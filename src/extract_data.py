from langchain.text_splitter import TokenTextSplitter
from extract_json import extract_json
from logging import DEBUG, INFO
import openai_handler, log
from typing import List, Dict
import json

# 1プロンプトあたりの抽出項目数
ITEM_LIMIT = 4

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプト中の質問部分の文字列を返す
def str_question(product_name:str, items:List[Dict]) -> str:
    text = '今から入力と期待する出力形式を与えます。\n'
    text += '入力の情報のみを用いて、'
    if product_name != '': 
        text += '製品 ' + product_name + ' の'
    text += '、'.join([item['name'] for item in items])
    text += 'の情報を抜き出し、出力形式に従ってJSONで出力してください。\n'
    return text

# プロンプト中の出力形式部分の文字列を返す
def str_format(item_list:List[str]) -> str:
    text = '#出力形式\n'
    text += '{\"' + '\":\"\",\"'.join([item['name'] for item in item_list]) + '\":\"\"}' + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output() -> str:
    text = '#出力'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#入力\n'
    text += input_text + '\n'
    return text

# 生成したプロンプトのリスト返す
def str_prompt(product_name:str, input_text:str, item_list:List[str]) -> List[str]:
    # only one prompt
    prompt = '\n'.join([
        str_question(product_name, item_list), 
        str_format(item_list), 
        str_input(input_text),
        str_output(),
    ])
    return prompt

# 回答をパース
def parse_answers(items:List[str], answers:List[str]) -> List[Dict]:
    all_dict = dict()
    for answer in answers:
        json_str = extract_json(answer)
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format('回答が読み取れないため空の値とします', '回答：' + answer))
            json_dict = dict()
        all_dict |= json_dict
    answers_dict = dict()
    # 有効な項目のみを抽出
    for item in items:
        if item['name'] in all_dict.keys():
            answers_dict[item['name']] = all_dict[item['name']]
    return answers_dict

# 対象項目の情報を抽出
def extract(input_text:str, product_name:str, items:List[Dict]) -> List[str]:
    raw_answers = []
    item_idx = 0
    while item_idx < len(items):
        prompt = str_prompt(product_name, input_text, item_list = items[item_idx:item_idx+ITEM_LIMIT])
        raw_answers.append(openai_handler.send(prompt))
        item_idx += ITEM_LIMIT
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)