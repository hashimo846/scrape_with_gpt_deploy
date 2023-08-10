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
def str_question(product_name:str, items:List[Dict], is_multi_prompt:bool) -> str:
    text = '今から入力と期待する出力形式を与えます。\n'
    text += '入力の情報のみを用いて、'
    if product_name != '': 
        text += '製品 ' + product_name + ' の'
    text += '、'.join([item['name'] for item in items])
    text += 'の情報を抜き出し、出力形式に従ってJSONで出力してください。\n'
    if is_multi_prompt:
        text += 'また、入力の文が長いのため、<end>というまで出力を生成しないでください。\n'
        text += '<end>というまでは<ok>とだけ返答してください。\n'
    return text

# プロンプト中の出力形式部分の文字列を返す
def str_format(item_list:List[str]) -> str:
    text = '#出力形式\n'
    text += '{\"' + '\":\"\",\"'.join([item['name'] for item in item_list]) + '\":\"\"}' + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output(is_multi_prompt:bool) -> str:
    text = '#出力'
    if is_multi_prompt:
        text += '\n<end>'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#入力\n'
    text += input_text + '\n'
    return text

# 生成したプロンプトのリスト返す
def str_prompts(product_name:str, input_texts:List[str], item_list:List[str]) -> List[str]:
    is_multi_prompt = 1 < len(input_texts)
    prompts_list = []

    if is_multi_prompt:
        # first prompt
        prompt_text = '\n'.join([
            str_question(product_name, item_list, is_multi_prompt), 
            str_format(item_list), 
            str_input(input_texts[0]),
        ])
        prompts_list.append(prompt_text)
        # intermediate prompts
        for input_text in input_texts[1:-1]:
            prompts_list.append(input_text)
        # last prompt
        prompt_text = '\n'.join([
            input_texts[-1] + '\n',
            str_output(is_multi_prompt),
        ])
        prompts_list.append(prompt_text)
    else:
        # only one prompt
        prompt_text = '\n'.join([
            str_question(product_name, item_list, is_multi_prompt), 
            str_format(item_list), 
            str_input(input_texts[0]),
            str_output(is_multi_prompt),
        ])
        prompts_list.append(prompt_text)
    return prompts_list

# 回答をパース
def parse_answers(items:List[str], answers:List[str]) -> List[Dict]:
    all_dict = dict()
    for answer in answers:
        json_str = extract_json(answer)
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません'), e)
            json_dict = dict()
        all_dict |= json_dict
    answers_dict = dict()
    # 有効な項目のみを抽出
    for item in items:
        if item['name'] in all_dict.keys():
            answers_dict[item['name']] = all_dict[item['name']]
    return answers_dict

# 対象項目の情報を抽出
def extract(split_inputs:List[str], product_name:str, items:List[Dict]) -> List[str]:
    answers = []
    item_idx = 0
    while item_idx < len(items):
        prompts = str_prompts(product_name, split_inputs, item_list = items[item_idx:item_idx+ITEM_LIMIT])
        answers.append(openai_handler.send(prompts))
        item_idx += ITEM_LIMIT
    answers = parse_answers(items, answers)
    return answers