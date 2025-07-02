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
import os
import sys
import logging
import tempfile
import json
from argparse import ArgumentParser

from flask import Flask, request, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

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


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
app.logger.setLevel(logging.INFO)


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


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except ApiException as e:
        app.logger.warn("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@app.route("/push", methods=["POST"])
def pushMessage():
    # get request body as text
    body = request.form.get("res")
    user_id = request.form.get("user_id")
    shop = request.form.get("shop")
    action = request.form.get("action", "default")
    app.logger.info(user_id + " Request body: " + body)
    bubble = None
    # handle webhook body
    if action == "gift_cancel":
        detail = json.loads(body)
        bubble = gift_cancel_template(shop, detail)
    elif action == "business_data":
        body = json.loads(body)
        bubble = business_data_template(shop, body)
    elif action == "quota":
        body = json.loads(body)
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
            abort(400)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[
                        FlexMessage(
                            alt_text=shops,
                            contents=FlexContainer.from_json(json.dumps(bubble)),
                        )
                    ],
                )
            )
    except ApiException as e:
        app.logger.warn("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text
    if isinstance(event.source, UserSource):
        app.logger.info("user_id: " + event.source.user_id)
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


@handler.add(UnknownEvent)
def handle_unknown_left(event):
    app.logger.info(f"unknown event {event}")


@app.route("/static/<path:path>")
def send_static_content(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage="Usage: python " + __file__ + " [--port <port>] [--help]"
    )
    arg_parser.add_argument("-p", "--port", type=int, default=8000, help="port")
    arg_parser.add_argument("-d", "--debug", default=False, help="debug")
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    app.run(debug=options.debug, port=options.port)
