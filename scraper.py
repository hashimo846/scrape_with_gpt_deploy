from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from typing import List, Dict
import os
import parser

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# ScraperAPIのAPIのキー
SCRAPER_API_KEY = os.environ['SCRAPER_API_KEY']
SCRAPER_API_URL = 'http://api.scraperapi.com'

# 指定したURLのページソースを取得
def get_page_source(url:str = None):
    logger.info(log.format('URLへアクセス中', url))
    payload = {'api_key': SCRAPER_API_KEY, 'url': url}
    try:
        with requests.get(SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0)) as r:
            source = r.text
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
        if source == None: continue
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
    # url = 'https://www.amazon.co.jp/dp/B0B4R7PK1F'
    url = 'https://www.amazon.co.jp/dp/B08BP6894V?th=1'
    text = scrape_all([url])
    print(text)

if __name__ == "__main__":
    main()