from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from typing import List, Dict
import os
import webpage_parser
from urllib.parse import urlencode

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# ScraperAPIのAPIのキー
SCRAPER_API_KEY = os.environ['SCRAPER_API_KEY']
SCRAPER_API_URL = 'http://api.scraperapi.com'

# 指定したURLのページソースを取得 (premiumオプションはスクレイピング対策回避のため)
def get_page_source(url:str = None, country_code = 'jp', premium = 'true', retry_max = 5, keep_header = True, mode = 'GET') -> BeautifulSoup:
    payload = {'api_key': SCRAPER_API_KEY, 'url': url, 'country_code': country_code, 'premium': premium}
    retry_count = 0
    while True:
        try:
            logger.info(log.format('URLへアクセス中:{}'.format(mode), url))
            if mode == 'GET':
                response = requests.get(SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0))
            elif mode == 'POST':
                response = requests.post(SCRAPER_API_URL, params=payload, data={'language':'ja_JP'}, timeout=(10.0, 20.0))
            elif mode == 'PUT':
                response = requests.put(SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0))
            else:
                response = None
            print(response)
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
        domain = webpage_parser.judge_domain(url)
        source = get_page_source(url)
        # ドメインによってページソース取得処理を切り替え
        # if domain == 'amazon':
        #     # Amazonの場合は日本語で取得するオプションを付与
        #     url += '&language=ja_JP'
        #     # Amazonの場合POSTで取得
        #     source = get_page_source(url, mode='POST')
        # else:
        #     source = get_page_source(url)
        
        # ページソースが取得出来なかった場合スキップ
        if source == None:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得失敗')
            continue
        # ドメインによってパーサを切り替え
        if domain == 'amazon':
            text = webpage_parser.parse_amazon(source)
        else:
            text = webpage_parser.parse_text(source)
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
    url = 'https://www.amazon.co.jp/Xiaomi-%E7%A9%BA%E6%B0%97%E6%B8%85%E6%B5%84%E6%A9%9F-Purifier-3H%E3%80%90%E6%97%A5%E6%9C%AC%E6%AD%A3%E8%A6%8F%E4%BB%A3%E7%90%86%E5%BA%97%E5%93%81%E3%80%91-%E3%82%B7%E3%83%AB%E3%83%90%E3%83%BC/dp/B08L6P15VX/ref=sr_1_1?__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=25WKHOG3BRMNP&keywords=Mi+Air+Purifier+3H+AC-M6-SC&qid=1695948724&sprefix=mi+air+purifier+3h+ac-m6-sc%2Caps%2C166&sr=8-1'
    text = scrape_all([url])
    print(text)

if __name__ == "__main__":
    main()