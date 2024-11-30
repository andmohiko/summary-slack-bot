import requests
from bs4 import BeautifulSoup
import time
import logging
from openai import AsyncOpenAI

from src.env import get_env

client = AsyncOpenAI(api_key=get_env("OPENAI_API_KEY"))


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


# HTML本文を取得する関数
def get_article_content(url):
    """
    指定されたURLのHTML本文を取得します。

    Args:
        url (str): 対象のURL。

    Returns:
        str: 記事の本文またはエラー情報。
    """
    try:
        time.sleep(1)  # サーバーに負担をかけないための遅延
        response = requests.get(url, timeout=20)  # タイムアウトを設定
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # articleタグまたはbodyタグを探す
        article_body = soup.find("article") or soup.find("body")
        if article_body:
            # 不要な要素を削除
            for element in article_body.find_all(
                ["header", "footer", "aside", "nav", "script", "style"]
            ):
                element.decompose()
            return article_body.get_text(strip=True, separator="\n")
        else:
            return "Content could not be extracted. Returning raw HTML."
    except requests.exceptions.RequestException as e:
        logging.warning(f"Error fetching URL {url}: {e}")
        return f"Failed to fetch content from {url}. Please check the URL."


# OpenAI APIを使って記事を要約する関数
async def summarize_article(article):
    prompt = f"""あなたは、要約のスペシャリストです。
下に示す記事を要約してください。なお、長くても500文字以内に収めてください。
要約した内容は、次の書式設定を効果的に使い、見やすい形でまとめてください。
太字: 半角スペース*テキスト*半角スペース
番号付きリスト: 1. アイテム1\n2. アイテム2
箇条書きリスト: • アイテム1\n• アイテム2
引用: > 引用文

記事内容はこちら
----------------------------------------
{article}
----------------------------------------
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは有能な記事要約者です。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )
        response_dict = response.model_dump()
        summary = response_dict["choices"][0]["message"]["content"]
        return summary
    except Exception as e:
        logging.warning(f"OpenAI API error: {e}")
        return "Failed to generate a summary using OpenAI."
