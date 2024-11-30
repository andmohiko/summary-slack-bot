from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import re
import asyncio

from src.env import get_env
from src.article import get_article_content, summarize_article

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
        if content.startswith("Failed"):
            say(text=f"Error: {content}", thread_ts=thread_ts)
            return

        summary = asyncio.run(summarize_article(content))

        say(text=f"Here is the summarized content:\n{summary}", thread_ts=thread_ts)
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


@flask_app.route("/summarize", methods=["POST"])
def summarize_endpoint():
    data = request.get_json()
    if "article" not in data:
        return jsonify({"error": "Article content is required"}), 400

    article = data["article"]
    summary = asyncio.run(summarize_article(article))
    return jsonify({"summary": summary})


if __name__ == "__main__":
    flask_app.run(port=3000)
