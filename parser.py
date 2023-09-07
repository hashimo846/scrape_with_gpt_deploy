from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 不要な文字を削除してテキストのみ抽出
def strip_text(text:str = ''):
    text = text.replace(' ', '').replace('　', '').replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    return text

# URLから全てのテキストを取得
def parse_text(html_source:str):
    # テキストのみ抽出
    html = BeautifulSoup(html_source, 'html.parser')
    text = html.text
    # 不要な文字を削除
    text = strip_text(text)
    return text

def parse_amazon():
    pass
