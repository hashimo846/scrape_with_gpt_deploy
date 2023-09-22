from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 明示的に特定の処理を行いたいサイトのドメイン一覧
DOMAIN_TYPES = {
    'amazon': ['amazon.co.jp', 'amazon.jp', 'amzn.asia'],
    'yahoo': ['shopping.yahoo.co.jp', 'store.shopping.yahoo.co.jp'],
    'rakuten': ['www.rakuten.co.jp', 'item.rakuten.co.jp']
}

# URLのドメインを判定
def judge_domain(url:str) -> str:
    # ドメインがどのサイトであるか判別
    for key in DOMAIN_TYPES.keys():
        # ドメインがURL内に含まれているか判定
        for domain in DOMAIN_TYPES[key]:
            if domain in url:
                return key
    # どのサイトでもない場合はothersを返す
    return 'others'

# 不要な文字を削除してテキストのみ抽出
def strip_text(text:str = '') -> str:
    # 不要な文字を削除
    text = text.replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    # 複数個連続するスペースを一つにする
    valid_texts = []
    for word in text.split(' '):
        if word != '':
            valid_texts.append(word)
    text = ' '.join(valid_texts)
    return text

# BeautifulSoupオブジェクトから指定したこのタグからテキストを抽出（タグが見つからない場合はNoneを返す）
def extract_text(parent:BeautifulSoup, tag:str, id:str = None) -> str:
    child = parent.find(tag, id=id)
    if child != None:
        return child.text
    else:
        return None

# 指定された要素の中身を削除
def remove_content(parent:BeautifulSoup, tag:str, id:str = None) -> None:
    child = parent.find(tag, id=id)
    if child != None:
        child.clear()

# URLから全てのテキストを取得
def parse_text(html_source:BeautifulSoup) -> str:
    # テキストのみ抽出
    text = html_source.text
    # 不要な文字を削除
    text = strip_text(text)
    return text

def parse_amazon(html_source:BeautifulSoup) -> str:
    # 抽出した情報を格納するDict
    extracted_texts = dict()

    # <html> → <body> → <div id="dp"> → <div id="dp-container"> のオブジェクトを取得
    body = html_source.find('body')
    dp = body.find('div', id='dp')
    dp_container = dp.find('div', id='dp-container')
    # <div id="dp_container"> → <div id="ppd"> → <div id="centerCol"> のオブジェクトを取得
    ppd = dp_container.find('div', id='ppd')
    centerCol = ppd.find('div', id='centerCol')

    # 必要な部分からテキストを抽出
    extracted_texts['title'] = extract_text(parent = centerCol, tag = 'div', id = 'title_feature_div')
    overview = centerCol.find('div', id = 'productOverview_feature_div')
    if overview != None:
        remove_content(parent = overview, tag = 'div', id = 'poToggleButton')
    extracted_texts['overview'] = extract_text(parent = centerCol, tag = 'div', id = 'productOverview_feature_div')
    feature = centerCol.find('div', id = 'featurebullets_feature_div')
    if feature != None:
        remove_content(parent = feature, tag = 'a', id = 'seeMoreDetailsLink')
    extracted_texts['feature'] = extract_text(parent= centerCol, tag = 'div', id = 'featurebullets_feature_div')
    extracted_texts['description'] = extract_text(parent = dp_container, tag = 'div', id = 'productDescription_feature_div')
    # A+コンテンツのテキストを抽出
    for div in dp_container.find_all('div', recursive = False):
        if 'aplus' in div.get('id'):
            extracted_texts[div.get('id')] = extract_text(parent = dp_container, tag = 'div', id = div.get('id'))
        
    # 抽出したテキストを結合
    log_text = output_text = ''
    for key in extracted_texts.keys():
        # ログ出力用のテキスト生成
        log_text += '--- {} ---\n'.format(key)
        log_text += strip_text(str(extracted_texts[key])) + '\n'
        # 抽出したテキストがNoneの場合はスキップ
        if extracted_texts[key] == None:
            continue
        # 不要な文字を削除
        text = strip_text(extracted_texts[key])
        # 関数の出力用のテキスト生成
        output_text += text + '\n'
    return output_text

def main():
    pass

if __name__ == '__main__':
    main()