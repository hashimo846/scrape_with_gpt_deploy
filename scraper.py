from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from typing import List, Dict
import os
import parser

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# HTTPリクエスト時のユーザーエージェント
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}

# ScraperAPIのAPIのキー
SCRAPER_API_KEY = os.environ['SCRAPER_API_KEY']

# 指定したURLのページソースを取得
def get_page_source(url:str = None):
    logger.info(log.format('URLへアクセス中', url))
    try:
        with requests.get(url, timeout=(3.0, 7.5), headers = HEADERS) as r:
            source = r.content
    except Exception as e:
        logger.error(log.format('アクセス失敗','URL:{}\nerror message:{}'.format(url, e)))
        return None
    return source

# 各URLのテキストを取得して結合
def scrape_all(url_list:List[str] = ['']) -> str:
    # 各URLから抽出したテキストを格納するリスト
    texts = []
    # 各URLからテキストを取得
    for url in url_list:
        # ページソースを取得
        source = get_page_source(url)
        # ドメインによってパーサを切り替えてテキストを取得
        domain = parser.judge_domain(url)
        if domain == 'amazon':
            text = parser.parse_amazon(source)
        elif domain == 'others':
            text = parser.parse_text(source)
        # テキストが取得できなかった場合はスキップ
        if text != None:
            texts.append(text)
    # テキストを結合して返す
    if len(texts) == 0:
        return None
    else:
        return ''.join(texts)

def main():
    # テスト用URL
    url = 'https://www.amazon.co.jp/dp/B08BP6894V?th=1'
    text = scrape_all([url])
    print(text)

if __name__ == "__main__":
    main()