from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from time import sleep
import sys
import io
import os
import shutil
import stat
from pathlib import Path
import selenium
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# HTTPリクエスト時のユーザーエージェント
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}

# URLからテキストを取得
def scrape(url:str = None):
    logger.info(log.format('URLからテキストを取得中', url))        
    try:
        with requests.get(url, timeout=(3.0, 7.5), headers = HEADERS) as r:
            html = BeautifulSoup(r.content, 'html.parser')
            text = html.text
    except Exception as e:
        logger.error(log.format('アクセス失敗','URL:{}\nerror message:{}'.format(url, e)))
        return None
    # テキストのみ抽出
    text = text.replace(' ', '').replace('　', '').replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    return text

# URLからページのソースを取得
def scrape_page_source(url:str = None):
    logger.info(log.format('URLからテキストを取得中', url))        
    try:
        with requests.get(url, timeout=(3.0, 7.5), headers = HEADERS) as r:
            html = BeautifulSoup(r.content, 'html.parser')
    except Exception as e:
        logger.error(log.format('アクセス失敗','URL:{}\nerror message:{}'.format(url, e)))
        return None
    return html

# 各URLのテキストを取得して結合
def scrape_all(url_list:List[str] = ['']) -> str:
    # 各URLからテキストを取得
    texts = []
    for url in url_list:
        text = scrape(url)
        if text != None:
            texts.append(text)
    # テキストを結合して返す
    if len(texts) == 0:
        return None
    else:
        return ''.join(texts)

def main():
    url = 'https://www.amazon.co.jp/dp/B08BP6894V?th=1'
    page_source = scrape_page_source(url)
    print(page_source)

if __name__ == "__main__":
    main()