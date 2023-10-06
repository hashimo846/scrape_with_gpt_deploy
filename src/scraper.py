from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from typing import List, Dict
import os
import parser
from urllib.parse import urlencode

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# ScraperAPIのAPIのキー
SCRAPER_API_KEY = os.environ['SCRAPER_API_KEY']
SCRAPER_API_URL = 'http://api.scraperapi.com'

# 指定したURLのページソースを取得 (premiumオプションはスクレイピング対策回避のため)
def get_page_source(url:str = None, country_code = 'jp', premium = 'true', retry_max = 3) -> BeautifulSoup:
    logger.info(log.format('URLへアクセス中', url))
    payload = {'api_key': SCRAPER_API_KEY, 'url': url, 'country_code': country_code, 'premium': premium}
    retry_count = 0
    while True:
        try:
            response = requests.get(SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0))
            response.encoding = 'utf-8'
            source = BeautifulSoup(response.text, 'html.parser')
            break
        except Exception as e:
            logger.error(log.format('アクセス失敗','URL:{}\ERROR MESSAGE:{}'.format(url, e)))
            # リトライ回数の上限に達したらNoneを返して終了
            if retry_count >= retry_max:
                logger.error(log.format('アクセス失敗','URL:{}\nERROR MESSAGE:{}'.format(url, e)))
                return None
            # リトライ
            else:
                retry_count += 1
                continue
    logger.info(log.format('アクセス成功', 'URL:{}\nRETRY:{}'.format(url, retry_count)))
    return source

# 各URLのテキストを取得して結合
def scrape_all(url_list:List[str] = ['']) -> str:
    # 各URLから抽出したテキストを格納するリスト
    texts = []
    # 各URLが読み取りが出来たかのステータスを格納するリスト
    status = []
    # 各URLからテキストを取得
    for idx, url in enumerate(url_list):
        # ドメインによってURLのタイプを判定
        domain = parser.judge_domain(url)
        # ドメインによってURLにオプションを付与
        if domain == 'amazon':
            url += '&language=ja_JP'
        # ページソースを取得
        source = get_page_source(url)
        if source == None: continue
        # ドメインによってパーサを切り替えてテキストを取得
        if domain == 'amazon':
            text = parser.parse_amazon(source)
        else :
            text = parser.parse_text(source)
        # テキストが取得できなかった場合はスキップ
        if text == None:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得失敗')
        else:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得成功')
            texts.append(text)

    # テキストを結合して返す
    if len(texts) == 0:
        return None, '\n'.join(status)
    else:
        return '\n'.join(texts), '\n'.join(status)

# scraperのテスト
def main():
    # テスト用URL
    # url = 'https://www.amazon.co.jp/dp/B0B4R7PK1F'
    url = 'https://amzn.asia/d/iU4Y9Ys'
    # url = 'https://kakaku.com/item/K0001292315/spec/#tab'
    text = scrape_all([url])
    print(text)

if __name__ == "__main__":
    main()