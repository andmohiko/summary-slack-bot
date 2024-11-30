from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import re

from src.env import get_env
from src.article import get_article_content

SLACK_BOT_TOKEN = get_env("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = get_env("SLACK_SIGNING_SECRET")

# Slack Appの初期化
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


# メンションに応答
@app.event("app_mention")
def handle_app_mention(event, say):
    text = event["text"]
    thread_ts = event.get("thread_ts", event["ts"])

    # SlackのURL形式（例: <https://example.com>）を処理する正規表現
    url_pattern = r"<(https?://[^>]+)>"
    match = re.search(url_pattern, text)

    if match:
        url = match.group(1)  # URL部分を抽出
        content = get_article_content(url)
        preview_length = 500  # プレビューとして返す文字数
        preview = content[:preview_length] + (
            "..." if len(content) > preview_length else ""
        )

        say(
            text=f"Here's the content preview for the URL:\n{preview}",
            thread_ts=thread_ts,  # スレッドタイムスタンプを指定
        )
    else:
        say(
            text="Please provide a valid URL.",
            thread_ts=thread_ts,  # スレッドタイムスタンプを指定
        )


# Flaskアプリの設定
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(port=3000)
