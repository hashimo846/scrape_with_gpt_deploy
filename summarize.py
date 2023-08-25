from bs4 import BeautifulSoup
from langchain.text_splitter import TokenTextSplitter
import openai
import os
import requests
import openai_handler
import log
from logging import DEBUG, INFO
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 1プロンプトに含むトークン数の上限
MAX_TOKEN = int(os.getenv("MAX_TOKEN"))
# 入力を分割する際の重複するトークン数
OVERLAP_TOKEN = int(os.getenv("OVERLAP_TOKEN"))
# 1プロンプトに含む入力の最大トークン数
MAX_INPUT_TOKEN = int(os.getenv("MAX_INPUT_TOKEN"))

# プロンプトのテンプレート
def str_template(product:Dict) -> str:
    template = '今から与える入力のみを用いて、'
    if product['name'] != '': 
        template += '製品' + product['name'] + 'の'
    else:
        template += '商品の'
    template += '仕様や性能を示す情報を抽出してください。\n'
    template += 'ただし、定量的な数値情報や固有名詞は可能は限り出力に含めてください。\n\n'
    template += '#入力\n{}'
    return template

# 決められたトークン数ごとに分割する
def split_by_token(input_text:str, max_token:int = MAX_INPUT_TOKEN, overlap_token:int = OVERLAP_TOKEN) -> List[str]:
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=overlap_token)
    texts = text_splitter.split_text(input_text)
    return texts

# 商品ページからテキストを取得してGPTに入力し、商品情報をスクレイピング
def summarize(input_text:str, product:Dict) -> str:
    # 入力文が長い場合は分割
    split_texts = split_by_token(input_text)
    # 分割が不要なトークン長になるまで要約
    while len(split_texts) > 1:    
        # GPTに入力用のプロンプトを作成
        scrape_prompts = [str_template(product).format(text) for text in split_texts]
        # GPTの回答を取得
        extract_texts = [openai_handler.send(prompt) for prompt in scrape_prompts]
        # 回答を結合
        extract_text = '\n'.join(extract_texts)
        # 入力が長い場合は再分割
        split_texts = split_by_token(extract_text)
    return split_texts[0]