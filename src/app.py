from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import requests
from bs4 import BeautifulSoup

# Slack Appの初期化
app = App(token="xoxb-your-slack-bot-token", signing_secret="your-signing-secret")


# URLのタイトルを取得する関数
def get_page_title(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else "No Title Found"
            return title
        else:
            return f"Error: Received status code {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


# メンションに応答
@app.event("app_mention")
def handle_app_mention(event, say):
    text = event["text"]
    user = event["user"]

    # テキスト内のURLを抽出
    words = text.split()
    url = next((word for word in words if word.startswith("http")), None)

    if url:
        title = get_page_title(url)
        say(f"<@{user}> The title of the page is: {title}")
    else:
        say(f"<@{user}> Please provide a valid URL.")


# Flaskアプリの設定
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(port=3000)
