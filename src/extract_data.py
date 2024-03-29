from langchain.text_splitter import TokenTextSplitter
from extract_json import extract_json
from logging import DEBUG, INFO
import openai_handler
import log
from typing import List, Dict
import json

# 1プロンプトあたりの抽出項目数
ITEM_LIMIT = 4

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトを生成


def messages_question_prompt(input_text: str, product_name: str, items: List[Dict]) -> List[Dict]:
    system_message = (
        'You will be provided with extraction targets, descriptions of targets, an expected output format and an excerpt texts about the product {product_name}. '
        'Your task is to extract information about the provided extraction targets in Japanese from only the provided excerpt texts. '
        'In addition, you MUST answer in JSON, the provided output format.'
    ).format(
        product_name=product_name
    )

    user_message = (
        'Extraction Targets: {targets}\n\n'
        'Descriptions: {descriptions}\n\n'
        'Output Format: {output_format}\n\n'
        'Excerpt texts: {input_text}'
    ).format(
        targets=', '.join([item['name'] for item in items]),
        descriptions='\n' + '\n'.join(['- {name}: {description} {research_description}'.format(
            name=item['name'], description=item['description'], research_description=item['research_description']) for item in items]),
        output_format='{\"' +
        '\":\"\", \"'.join([item['name'] for item in items]) + '\":\"\"}',
        input_text=input_text
    )

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return messages

# 回答をパース


def parse_answers(items: List[str], answers: List[str]) -> List[Dict]:
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
    # ”不明”を空文字に変換
    for key in answers_dict.keys():
        if answers_dict[key] == '不明':
            answers_dict[key] = ''
    return answers_dict

# 対象項目の情報を抽出


def extract(input_text: str, product_name: str, items: List[Dict]) -> List[str]:
    raw_answers = []
    item_idx = 0
    while item_idx < len(items):
        messages = messages_question_prompt(
            input_text, product_name, items[item_idx:item_idx+ITEM_LIMIT])
        logger.debug(log.format('データ項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
        item_idx += ITEM_LIMIT
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)
