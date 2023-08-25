from bs4 import BeautifulSoup
from langchain.text_splitter import TokenTextSplitter
import openai
import os
import requests
import openai_handler
from typing import List, Dict

# 1プロンプトに含むトークン数の上限
MAX_TOKEN = int(os.getenv("MAX_TOKEN"))
# 入力を分割する際の重複するトークン数
OVERLAP_TOKEN = int(os.getenv("OVERLAP_TOKEN"))
# 1プロンプトに含む入力の最大トークン数
MAX_INPUT_TOKEN = int(os.getenv("MAX_INPUT_TOKEN"))

# プロンプトのテンプレート
def str_template(model_number:str, is_service = False):
    template = '今から与える入力のみを用いて、'
    if model_number != None: 
        template += '製品' + model_number + 'の'
    else:
        template += '商品の'
    template += '仕様や性能を示す情報を抽出してください。\n'
    template += 'ただし、定量的な数値情報や固有名詞は可能は限り出力に含めてください。\n\n'
    template += '#入力\n{}'
    return template

# 決められたトークン数ごとに分割する
def split_by_token(input_text, max_token = MAX_TOKEN, overlap_token = OVERLAP_TOKEN):
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=overlap_token)
    texts = text_splitter.split_text(input_text)
    return texts

# 商品ページからテキストを取得してGPTに入力し、商品情報をスクレイピング
def summarize(input_text:str, model_number:str = None) -> str:
    # 入力文が長い場合は複数に分割
    split_texts = split_by_token(input_text)
    # GPTに入力用のプロンプトを作成
    scrape_prompts = [str_template(model_number).format(text) for text in split_texts]
    # GPTの回答を取得
    extract_texts = [openai_handler.send([prompt]) for prompt in scrape_prompts]
    # 回答を結合
    extract_text = '\n'.join(extract_texts)
    return extract_text