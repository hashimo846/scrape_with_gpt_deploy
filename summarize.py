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

# プロンプト中の質問部分の文字列を返す
def str_question(product:Dict) -> str:
    text = 'これから与える入力のみを用いて、'
    if product['name'] != '': 
        text += '製品' + product['name'] + 'の'
    else:
        text += '商品の'
    text += '性能や特徴を示す情報を、定量的な数値情報や固有名詞は可能な限り含めて抽出してください。\n'
    text += '特に、以下に示す重要項目に関する情報がある場合は可能な限り出力に含めてください。\n'
    return text

# プロンプト中の重要項目の文字列を返す
def str_important_items(master_items:Dict) -> str:
    item_names = []
    for key in master_items.keys():
        for item in master_items[key]:
            item_names.append(item['name'])
    text = '#重要項目\n'
    text += ','.join(item_names) + '\n'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#入力\n'
    text += input_text + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output() -> str:
    return '#出力'

# プロンプトの文字列を返す
def str_prompt(input_text:str, product:Dict, master_items:Dict) -> str:
    prompt = '\n'.join([
        str_question(product), 
        str_important_items(master_items),
        str_input(input_text),
        str_output(),
    ])
    return prompt

# 決められたトークン数ごとに分割する
def split_by_token(input_text:str, max_token:int = MAX_INPUT_TOKEN, overlap_token:int = OVERLAP_TOKEN) -> List[str]:
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=overlap_token)
    texts = text_splitter.split_text(input_text)
    return texts

# 商品ページからテキストを取得してGPTに入力し、商品情報をスクレイピング
def summarize(input_text:str, product:Dict, master_items:Dict) -> str:
    # 入力文が長い場合は分割
    split_texts = split_by_token(input_text)
    # 最低一回は要約する
    first_time = True
    # 分割が不要なトークン長になるまで要約
    while len(split_texts) > 1 or first_time:    
        # GPTに入力用のプロンプトを作成
        scrape_prompts = [str_prompt(text, product, master_items) for text in split_texts]
        '''
        for i in range(len(scrape_prompts)):
            logger.debug(log.format('プロンプト'+str(i+1), scrape_prompts[i]))
        '''
        # GPTの回答を取得
        extract_texts = [openai_handler.send(prompt) for prompt in scrape_prompts]
        # 回答を結合
        extract_text = '\n'.join(extract_texts)
        # 入力が長い場合は再分割
        split_texts = split_by_token(extract_text)
        # 2回目以降フラグ
        first_time = False
    return split_texts[0]