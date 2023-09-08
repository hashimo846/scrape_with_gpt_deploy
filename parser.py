from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 明示的に特定の処理を行いたいサイトのドメイン一覧
DOMAIN_TYPES = {
    'amazon': ['www.amazon.co.jp', 'amazon.co.jp', 'amazon.jp'],
    'yahoo': ['shopping.yahoo.co.jp', 'store.shopping.yahoo.co.jp'],
    'rakuten': ['www.rakuten.co.jp', 'item.rakuten.co.jp']
}

# URLのドメインを判定
def judge_domain(url:str):
    # URLのドメイン部分を取得
    splitted_url = url.split('/')
    if len(splitted_url) < 2:
        logger.error(log.format('URLが不正です', url))
        return None
    else:
        domain = splitted_url[2]
    # ドメインがどのサイトであるか判別
    for key in DOMAIN_TYPES.keys():
        if domain in DOMAIN_TYPES[key]:
            return key
    # どのサイトでもない場合はothersを返す
    return 'others'

# 不要な文字を削除してテキストのみ抽出
def strip_text(text:str = ''):
    text = text.replace(' ', '').replace('　', '').replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    return text

# 不要な文字を削除してテキストのみ抽出
def weak_strip_text(text:str = ''):
    text = text.replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    return text

# URLから全てのテキストを取得
def parse_text(html_source:str):
    # HTMLソースを解析
    html = BeautifulSoup(html_source, 'html.parser')
    # テキストのみ抽出
    text = html.text
    # 不要な文字を削除
    text = strip_text(text)
    return text

def parse_amazon(html_source:str):
    # 抽出した情報を格納するDict
    extracted_texts = dict()

    # HTMLソースを解析
    html = BeautifulSoup(html_source, 'html.parser')
    # body部分を取得
    body = html.find('body')
    # <div id="dp">を抽出
    dp = body.find('div', id='dp')
    # <div id="dp-container">を抽出
    dp_container = dp.find('div', id='dp-container')

    # <div id="ppd">を抽出
    ppd = dp_container.find('div', id='ppd')
    # <div id="centerCol">を抽出
    centerCol = ppd.find('div', id='centerCol')
    # <div id="title_feature_div">を抽出（商品タイトル部分）
    title_feature_div = centerCol.find('div', id='title_feature_div')
    extracted_texts['title_feature_div'] = title_feature_div.text
    # <div id="productOverview_feature_div">を抽出（商品概要部分）
    productOverview_feature_div = centerCol.find('div', id='productOverview_feature_div')
    extracted_texts['productOverview_feature_div'] = productOverview_feature_div.text
    # <div id="featurebullets_feature_div">を抽出（商品詳細部分）
    featurebullets_feature_div = centerCol.find('div', id='featurebullets_feature_div')
    extracted_texts['featurebullets_feature_div'] = featurebullets_feature_div.text

    # dp_container内のdiv要素を全て週出
    dp_container_divs = dp_container.find_all('div', recursive = False)
    # dp_container_divs内の<div id="productDetails_feature_div">の次から<div id="similarities_feature_div">の前までのdiv要素を抽出
    start = False
    count = 0
    for div in dp_container_divs:
        if div.get('id') == 'productDetails_feature_div':
            start = True
            continue
        elif div.get('id') == 'similarities_feature_div' and div.find('div').get('id') == 'sims-consolidated-4_feature_div':
            break
        elif start and strip_text(div.text) != '':
            count += 1
            extracted_texts['product_description_sections_{}'.format(count)] = div.text    
        
    # 抽出したテキストを結合
    texts = []
    for key in extracted_texts.keys():
        text = extracted_texts[key]
        text = weak_strip_text(text)
        texts.append(text)
    text = '\n'.join(texts)
    return text