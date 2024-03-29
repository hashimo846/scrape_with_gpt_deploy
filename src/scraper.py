from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from typing import List, Dict, Tuple
import os
import webpage_parser
from urllib.parse import urlencode

logger = log.init(__name__, DEBUG)

# ScraperAPI認証用
SCRAPER_API_KEY = os.environ['SCRAPER_API_KEY']
SCRAPER_API_URL = 'http://api.scraperapi.com'


def get_page_source(url: str = None, country_code='jp', premium='true', retry_max=5, keep_header=True, mode='GET', render='true') -> BeautifulSoup:
    """ 指定したURLのページソースを取得 (premiumオプションはスクレイピング対策回避のため) """
    payload = {'api_key': SCRAPER_API_KEY, 'url': url, 'render': render,
               'country_code': country_code, 'premium': premium}
    retry_count = 0
    while True:
        try:
            logger.info(log.format('URLへアクセス中:{}'.format(mode), url))
            if mode == 'GET':
                response = requests.get(
                    SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0))
            elif mode == 'POST':
                response = requests.post(SCRAPER_API_URL, params=payload, data={
                                         'language': 'ja_JP'}, timeout=(10.0, 20.0))
            elif mode == 'PUT':
                response = requests.put(
                    SCRAPER_API_URL, params=payload, timeout=(10.0, 20.0))
            else:
                response = None
            print(response)
            response.encoding = 'utf-8'
            source = BeautifulSoup(response.text, 'html.parser')
            break
        except Exception as e:
            logger.error(log.format(
                'アクセス失敗', 'URL:{}\ERROR MESSAGE:{}'.format(url, e)))
            # NOTE: リトライ回数の上限に達したらNoneを返して終了
            if retry_count >= retry_max:
                logger.error(log.format(
                    'アクセス失敗', 'URL:{}\nERROR MESSAGE:{}'.format(url, e)))
                return None
            # リトライ
            else:
                retry_count += 1
                continue
    logger.info(log.format(
        'アクセス成功', 'URL:{}\nRETRY:{}'.format(url, retry_count)))
    return source


def scrape_all(url_list: List[str] = ['']) -> Tuple[str, str]:
    """ 各URLのテキストを取得して結合 """
    texts, status = [], []
    for idx, url in enumerate(url_list):
        source = get_page_source(url)
        if source == None:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得失敗')
            continue
        # NOTE: ドメインによってパーサを切り替え
        domain = webpage_parser.judge_domain(url)
        if domain == 'amazon':
            text = webpage_parser.parse_amazon(source)
        else:
            text = webpage_parser.parse_text(source)
        if text == None:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得失敗')
        else:
            status.append('[URL{}:type={}] '.format(idx+1, domain)+'取得成功')
            texts.append(text)
    if len(texts) == 0:
        return None, '\n'.join(status)
    else:
        return '\n'.join(texts), '\n'.join(status)


def main():
    """ テスト用のメイン関数 """
    pass


if __name__ == "__main__":
    main()
