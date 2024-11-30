from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request, jsonify
import re
import logging
import asyncio

from src.env import get_env
from src.article import get_article_content, summarize_article

SLACK_BOT_TOKEN = get_env("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = get_env("SLACK_SIGNING_SECRET")

# Slack Appの初期化
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


# メンションに応答
@app.event("app_mention")
def handle_app_mention(event, say, client):
    thread_ts = event.get("thread_ts", event["ts"])
    channel = event["channel"]

    # 異常系は早期リターン
    if thread_ts == event["ts"]:
        say(
            text="Please provide a valid URL or mention me in a thread that contains a URL.",
            thread_ts=thread_ts,  # スレッドタイムスタンプを指定
        )
        return

    # スレッドの親メッセージを取得
    try:
        response = client.conversations_replies(channel=channel, ts=thread_ts)
        if not response["ok"] or len(response["messages"]) == 0:
            say(text="Failed to retrieve the parent message.", thread_ts=thread_ts)
            return

        parent_message = response["messages"][0]["text"]
        url_pattern = r"<(https?://[^>]+)>"
        match = re.search(url_pattern, parent_message)

        if not match:
            say(
                text="Parent message does not contain a valid URL.",
                thread_ts=thread_ts,
            )
            return

        url = match.group(1)  # URL部分を抽出
        content = get_article_content(url)
        if content.startswith("Failed"):
            say(text=f"Error: {content}", thread_ts=thread_ts)
            return

        summary = asyncio.run(summarize_article(content))
        say(text=f"{summary}", thread_ts=thread_ts)
    except Exception as e:
        logging.warning(f"Slack API error: {e}")
        say(text=f"Error: {str(e)}", thread_ts=thread_ts)


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
