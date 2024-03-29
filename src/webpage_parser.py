from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import log
from typing import List, Dict

logger = log.init(__name__, DEBUG)

# 明示的に特定の処理を行いたいサイトのドメイン一覧
DOMAIN_TYPES = {
    'amazon': ['amazon.co.jp', 'amazon.jp', 'amzn.asia'],
    'yahoo': ['shopping.yahoo.co.jp', 'store.shopping.yahoo.co.jp'],
    'rakuten': ['www.rakuten.co.jp', 'item.rakuten.co.jp']
}


def judge_domain(url: str) -> str:
    """ URLのドメインを判定 (どのサイトでもない場合はothersを返す) """
    for key in DOMAIN_TYPES.keys():
        for domain in DOMAIN_TYPES[key]:
            if domain in url:
                return key
    return 'others'

#


def strip_text(text: str = '') -> str:
    """ 不要な文字を削除してテキストのみ抽出 """
    text = text.replace('\n', '').replace('\t', '')
    text = text.replace('\r', '').replace('\v', '').replace('\f', '')
    # NOTE: 複数個連続するスペースを一つにする
    valid_texts = []
    for word in text.split(' '):
        if word != '':
            valid_texts.append(word)
    text = ' '.join(valid_texts)
    return text


def extract_text(parent: BeautifulSoup, tag: str, id: str = None) -> str:
    """ BeautifulSoupオブジェクトから指定したこのタグからテキストを抽出（タグが見つからない場合はNoneを返す）"""
    child = parent.find(tag, id=id)
    if child != None:
        return child.text
    else:
        return None


def remove_content(parent: BeautifulSoup, tag: str, id: str = None) -> None:
    """ 指定された要素の中身を削除 """
    child = parent.find(tag, id=id)
    if child != None:
        child.clear()


def parse_text(html_source: BeautifulSoup) -> str:
    """ URLから全てのテキストを取得 """
    try:
        text = html_source.text
        text = strip_text(text)
        return text
    except Exception as e:
        logger.error(log.format('Webページの解析失敗', e))
        return None


def parse_amazon(html_source: BeautifulSoup) -> str:
    """ Amazonのページから必要なテキストを抽出 """
    try:
        extracted_texts = dict()

        # NOTE: <html> → <body> → <div id="dp"> → <div id="dp-container"> のオブジェクトを取得
        body = html_source.find('body')
        dp = body.find('div', id='dp')
        dp_container = dp.find('div', id='dp-container')
        # NOTE: <div id="dp_container"> → <div id="ppd"> → <div id="centerCol"> のオブジェクトを取得
        ppd = dp_container.find('div', id='ppd')
        centerCol = ppd.find('div', id='centerCol')

        extracted_texts['title'] = extract_text(
            parent=centerCol, tag='div', id='title_feature_div')
        overview = centerCol.find('div', id='productOverview_feature_div')
        if overview != None:
            remove_content(parent=overview, tag='div', id='poToggleButton')
        extracted_texts['overview'] = extract_text(
            parent=centerCol, tag='div', id='productOverview_feature_div')
        feature = centerCol.find('div', id='featurebullets_feature_div')
        if feature != None:
            remove_content(parent=feature, tag='a', id='seeMoreDetailsLink')
        extracted_texts['feature'] = extract_text(
            parent=centerCol, tag='div', id='featurebullets_feature_div')
        extracted_texts['description'] = extract_text(
            parent=dp_container, tag='div', id='productDescription_feature_div')
        # NOTE: A+コンテンツのテキストを抽出
        for div in dp_container.find_all('div', recursive=False):
            if 'aplus' in div.get('id'):
                extracted_texts[div.get('id')] = extract_text(
                    parent=dp_container, tag='div', id=div.get('id'))

        # NOTE: 抽出したテキストを結合
        output_text = ''
        for key in extracted_texts.keys():
            # 抽出したテキストがNoneの場合はスキップ
            if extracted_texts[key] == None:
                continue
            # 不要な文字を削除
            text = strip_text(extracted_texts[key])
            # 関数の出力用のテキスト生成
            output_text += text + '\n'
        return output_text
    except Exception as e:
        logger.error(log.format('Amazonのページ解析失敗', e))
        return None


def main():
    """ テスト用のメイン関数 """
    pass


if __name__ == '__main__':
    main()
