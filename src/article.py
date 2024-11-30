import requests
from bs4 import BeautifulSoup
import time
import logging


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
