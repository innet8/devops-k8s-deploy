# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import datetime
import errno
import mimetypes
import os
import sys
import logging
import tempfile
import json
from argparse import ArgumentParser

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from linebot.v3 import WebhookHandler
from linebot.v3.models import UnknownEvent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    LocationMessageContent,
    StickerMessageContent,
    ImageMessageContent,
    VideoMessageContent,
    AudioMessageContent,
    FileMessageContent,
    UserSource,
    RoomSource,
    GroupSource,
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    LeaveEvent,
    PostbackEvent,
    BeaconEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    MulticastRequest,
    BroadcastRequest,
    TextMessage,
    ApiException,
    LocationMessage,
    StickerMessage,
    ImageMessage,
    TemplateMessage,
    FlexMessage,
    Emoji,
    QuickReply,
    QuickReplyItem,
    ConfirmTemplate,
    ButtonsTemplate,
    CarouselTemplate,
    CarouselColumn,
    ImageCarouselTemplate,
    ImageCarouselColumn,
    FlexBubble,
    FlexImage,
    FlexBox,
    FlexText,
    FlexIcon,
    FlexButton,
    FlexSeparator,
    FlexContainer,
    MessageAction,
    URIAction,
    PostbackAction,
    DatetimePickerAction,
    CameraAction,
    CameraRollAction,
    LocationAction,
    ErrorResponse,
)

from linebot.v3.insight import ApiClient as InsightClient, Insight
import httpx
import asyncio


app = FastAPI()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None or channel_access_token is None:
    print(
        "Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables."
    )
    sys.exit(1)

handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), "static", "tmp")

configuration = Configuration(access_token=channel_access_token)


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


@app.post("/callback")
async def callback(request: Request):
    # get X-Line-Signature header value
    signature = request.headers.get("X-Line-Signature")

    # get request body as text
    body = await request.body()
    body_text = body.decode('utf-8')
    logger.info("Request body: " + body_text)

    # handle webhook body
    try:
        handler.handle(body_text, signature)
    except ApiException as e:
        logger.warning("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse("OK")


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
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{shop} 当前剩余短信额度:",
                        "weight": "bold",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": body.get("quota","0"),
                        "size": "lg",
                        "color": "#ee2f43",
                        "align": "end",
                        "weight": "bold"
                    }
                ]
            },
        }
    else:
        pass

    try:
        if not bubble:
            raise HTTPException(status_code=400, detail="Invalid action or data")
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
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


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text
    if isinstance(event.source, UserSource):
        logger.info("user_id: " + event.source.user_id)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if text == "profile":
            if isinstance(event.source, UserSource):
                profile = line_bot_api.get_profile(user_id=event.source.user_id)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text="Display name: " + profile.display_name),
                            TextMessage(
                                text="Status message: " + str(profile.status_message)
                            ),
                        ],
                    )
                )
            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(
                                text="Bot can't use profile API without user ID"
                            )
                        ],
                    )
                )
        elif text == "id":
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="Your USER_ID is: " + event.source.user_id)
                    ],
                )
            )


# Other Message Type
@handler.add(MessageEvent, message=(ImageMessageContent))
def handle_content_message(event):
    if isinstance(event.message, ImageMessageContent):
        ext = 'jpg'
    else:
        return

    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
        message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)
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

    response = httpx.post(init_url, headers=headers, json=payload)
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
    file_response = httpx.post(upload_url, headers=upload_headers, content=file_data)
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
    response = httpx.post(generation_url, headers=generation_headers, json=generation_payload)
    result = response.json()
    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[
                                TextMessage(text=part["text"])
                            ]
                        )
                    )
                return
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="Recognition failure")
                ]
            )
        )

@handler.add(UnknownEvent)
def handle_unknown_left(event):
    logger.info(f"unknown event {event}")


# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage="Usage: python " + __file__ + " [--port <port>] [--help]"
    )
    arg_parser.add_argument("-p", "--port", type=int, default=8000, help="port")
    arg_parser.add_argument("-d", "--debug", default=False, help="debug")
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    uvicorn.run(app, host="0.0.0.0", port=options.port, log_level="info" if not options.debug else "debug")
