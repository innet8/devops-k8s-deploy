# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import errno
import logging
import mimetypes
import os
import sys
import tempfile

from fastapi import Request, FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import redis
import json
import httpx

from linebot.v3.webhook import WebhookParser,UserSource
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    AsyncMessagingApiBlob,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage,
    PushMessageRequest,
    FlexMessage,
    FlexContainer,
    ApiException
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
USER_STATE_PREFIX = "line_bot_user_state:"

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用的生命周期管理。
    在应用启动时连接 Redis，在应用关闭时断开 Redis。
    """
    # 连接 Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    await redis_client.ping()
    logger.info("Connected to Redis successfully!")
    app.state.redis_client = redis_client

    yield # 应用在此处启动并处理请求
    # 应用关闭时执行的代码
    if hasattr(app.state, 'redis_client') and app.state.redis_client:
        await app.state.redis_client.close()
        logger.info("Redis connection closed.")

# 将 lifespan 传递给 FastAPI 实例
app = FastAPI(lifespan=lifespan)

configuration = Configuration(
    access_token=channel_access_token
)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


static_tmp_path = os.path.join(os.path.dirname(__file__), "static", "tmp")
# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

# 营业数据
def business_data_template(shop_name, body):
    business_data = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": shop_name,
                    "weight": "bold",
                    "size": "xl",
                    "margin": "md",
                },
                {"type": "separator", "margin": "xl"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "xxl",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "总销售额：",
                                    "size": "sm",
                                    "color": "#555555",
                                },
                                {
                                    "type": "text",
                                    "text": body.get("receivable_price") + "",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end",
                                },
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "实收金额：",
                                    "size": "sm",
                                    "color": "#555555",
                                },
                                {
                                    "type": "text",
                                    "text": body.get("received_price") + "",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end",
                                },
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "营业收入：",
                                    "size": "sm",
                                    "color": "#555555",
                                },
                                {
                                    "type": "text",
                                    "text": body.get("business_price") + "",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end",
                                },
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "size": "sm",
                                    "color": "#555555",
                                    "text": "总订单数：",
                                },
                                {
                                    "type": "text",
                                    "text": body.get("total_order_num") + "",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end",
                                },
                            ],
                        },
                    ],
                },
                {"type": "separator", "margin": "xxl"},
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "时间：",
                            "size": "xs",
                            "color": "#aaaaaa",
                            "flex": 0,
                        },
                        {
                            "type": "text",
                            "text": body.get("time_range"),
                            "color": "#aaaaaa",
                            "size": "xs",
                            "align": "end",
                        },
                    ],
                },
            ],
        },
        "styles": {"footer": {"separator": True}},
    }
    return business_data

def gift_cancel_template(shop_name, detail):
    result = {
        "time_range": detail.get("time_range"),
        "summary": detail.get("summary"),
        "gift_records": detail.get("gift_records"),
        "cancel_records": detail.get("cancel_records"),
    }
    shop = shop_name

    def build_records_section(records, title, color):
        if not records:
            return []
        # print(f"[DEBUG] Building section: {title} | {len(records)} records")
        section = [
            {
                "type": "text",
                "text": title,
                "weight": "bold",
                "size": "md",
                "color": color,
                "margin": "md",
            }
        ]

        for i, rec in enumerate(records):
            section.append({"type": "text", "text": rec, "wrap": True, "size": "sm"})
            if i < len(records) - 1:
                section.append({"type": "separator", "margin": "md"})

        return section

    body_contents = [
        {
            "type": "text",
            "text": f"{shop}赠退菜记录",
            "weight": "bold",
            "size": "xl",
            "color": "#222222",
        },
        {
            "type": "text",
            "text": f"{result['time_range']}",
            "size": "sm",
            "wrap": True,
            "color": "#666666",
        },
        {
            "type": "text",
            "text": result["summary"],
            "size": "sm",
            "color": "#666666",
            "margin": "sm",
        },
        {"type": "separator", "margin": "md"},
    ]
    print(result["gift_records"])
    # 添加赠菜记录
    gift_section = build_records_section(
        result["gift_records"], "🎁 赠菜记录", "#1DB446"
    )
    if gift_section:
        body_contents += gift_section
        body_contents.append({"type": "separator", "margin": "lg"})

    # 添加退菜记录
    cancel_section = build_records_section(
        result["cancel_records"], "🔁 退菜记录", "#FF6B6B"
    )
    if cancel_section:
        body_contents += cancel_section

    # 生成完整 bubble
    flex_message = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": body_contents,
        },
    }

    return flex_message

def quota_template(shop,body):
    return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "paddingAll": "20px",
                "contents": [
                {
                    "type": "text",
                    "text": f"{shop}",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1DB446"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#F8F8F8",
                    "cornerRadius": "lg",
                    "paddingAll": "12px",
                    "margin": "md",
                    "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "contents": [
                        {
                            "type": "text",
                            "text": "当前短信额度",
                            "weight": "bold",
                            "size": "md",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": body.get("quota","0"),
                            "size": "xl",
                            "color": "#ee2f43",
                            "weight": "bold",
                            "align": "end"
                        }
                        ]
                    }
                    ]
                }
                ]
            }
        }
        
async def handle_TextMessage(event):
    text = event.message.text
    user_id = event.source.user_id
    received_text = event.message.text
    user_state_key = f"{USER_STATE_PREFIX}{user_id}"
    logger.info(f"文本消息: {text}, Userid: {user_id}")
    # 从 app.state 获取 Redis 客户端
    redis_client = app.state.redis_client
    if text == "id":
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="Your USER_ID is: " + event.source.user_id)
                ],
            )
        )
    elif text == "识别图片": # 假设这是你的特定指令
        await redis_client.set(user_state_key, "waiting_for_image", ex=120) # 设置状态并设置 120 秒过期时间
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="好的，请现在发送您的图片。")
                ],
            )
        )
    elif received_text == "取消":
        if await redis_client.exists(user_state_key):
            await redis_client.delete(user_state_key)
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="操作已取消。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="当前没有需要取消的操作。")
            )

async def handle_ImageMessage(event):
    user_id = event.source.user_id
    user_state_key = f"{USER_STATE_PREFIX}{user_id}"

    # 从 app.state 获取 Redis 客户端
    redis_client = app.state.redis_client
    current_state = await redis_client.get(user_state_key)
    if current_state != "waiting_for_image":
        logger.info(f"未收到指令后的图片消息 ID: {event.message.id}")
        return
    logger.info(f"图片消息 ID: {event.message.id}, Userid: {user_id}")
    ext = 'jpg'
    line_bot_blob_api = AsyncMessagingApiBlob(async_api_client)
    thread = line_bot_blob_api.get_message_content_with_http_info(event.message.id, async_req=True)
    message_content = thread.get()
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        tf.write(message_content)
        tempfile_path = tf.name


    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    IMAGE_PATH = f"static/tmp/{dist_name}"
    DISPLAY_NAME = "IMAGE"

    # Step 1: 获取 MIME 类型和文件大小
    mime_type, _ = mimetypes.guess_type(IMAGE_PATH)
    num_bytes = os.path.getsize(IMAGE_PATH)
    init_url = "https://generativelanguage.googleapis.com/upload/v1beta/files"
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(num_bytes),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json"
    }
    payload = {
        "file": {
            "display_name": DISPLAY_NAME
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(init_url, headers=headers, json=payload)

    upload_url = response.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("Failed to get resumable upload URL")
    
    with open(IMAGE_PATH, "rb") as f:
        file_data = f.read()

    upload_headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Length": str(num_bytes),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize"
    }
    async with httpx.AsyncClient() as client:
        file_response = await client.post(upload_url, headers=upload_headers, content=file_data)
    file_info = file_response.json()
    file_uri = file_info.get("file", {}).get("uri")

    if not file_uri:
        raise RuntimeError("Upload succeeded but no file URI found")
    generation_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    generation_headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    generation_payload = {
        "contents": [{
            "parts": [
                {
                    "file_data": {
                        "mime_type": mime_type,
                        "file_uri": file_uri
                    }
                },
                {
                    "text": "This image contains a screenshot of a conversation. Please extract all messages with their respective senders. Return the result in the format:\n\n- Sender: Message\n\nIgnore any irrelevant UI elements or system messages."
                }
            ]
        }],
        "generationConfig": {
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(generation_url, headers=generation_headers, json=generation_payload)
    result = response.json()
    temp = json.dumps(result)
    logger.info(f"识别结果: {temp}, Userid: {user_id}")
    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                await line_bot_api.reply_message(
                        ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=part["text"])
                        ]
                    )
                )
                return
    
    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="Recognition failure")
            ]
        )
    )

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue

        if isinstance(event.source, UserSource):
            logger.info("user_id: " + event.source.user_id)
        if isinstance(event.message, TextMessageContent):
            await handle_TextMessage(event)
        elif isinstance(event.message, ImageMessageContent):
            await handle_ImageMessage(event)

    return 'OK'


@app.post("/push")
async def pushMessage(
    res: str = Form(...),
    user_id: str = Form(...),
    shop: str = Form(...),
    action: str = Form("default")
):
    logger.info(f"{user_id} Request body: {res}")
    bubble = None
    # handle webhook body
    if action == "gift_cancel":
        detail = json.loads(res)
        bubble = gift_cancel_template(shop, detail)
    elif action == "business_data":
        body = json.loads(res)
        bubble = business_data_template(shop, body)
    elif action == "quota":
        body = json.loads(res)
        bubble = quota_template(shop,body)
    else:
        pass

    try:
        if not bubble:
            raise HTTPException(status_code=400, detail="Invalid action or data")
        await line_bot_api.reply_message(
            PushMessageRequest(
                to=user_id,
                messages=[
                    FlexMessage(
                        alt_text=shop,
                        contents=FlexContainer.from_json(json.dumps(bubble)),
                    )
                ],
            )
        )
    except ApiException as e:
        logger.warning("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse("OK")