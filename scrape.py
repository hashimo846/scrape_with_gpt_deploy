from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
from time import sleep
from typing import List
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

# Octoparseの動作確認用
OCTOPARSE_USERNAME = os.getenv('OCTOPARSE_USERNAME')
OCTOPARSE_PASSWORD = os.getenv('OCTOPARSE_PASSWORD')
OCTOPARSE_API_BASE_URL = 'https://openapi.octoparse.com/'

# アクセストークンの取得
def get_access_token(username:str = OCTOPARSE_USERNAME, passward:str = OCTOPARSE_PASSWORD, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'token'
    header = {"Content-Type": "application/json"}
    body = {
        'username':username,
        'password':passward,
        'grant_type':'password'
    }
    return requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()

# アクセストークンの有効期限更新
def refresh_access_token(refresh_token:str, base_url:str = OCTOPARSE_API_BASE_URL, ) -> Dict:
    path = 'token'
    header = {"Content-Type": "application/json"}
    body = {
        'refresh_token':refresh_token,
        'grant_type':'refresh_token'
    }
    return requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()


def main():
    response = get_access_token()
    logger.debug(log.format('アクセストークン取得', response))
    sleep(1)
    response = refresh_access_token(response['data']['refresh_token'])
    logger.debug(log.format('アクセストークン更新', response))

if __name__ == "__main__":
    main()