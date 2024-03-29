from extract_json import extract_json
import json
from logging import DEBUG, INFO
import openai_handler
import log
from typing import List, Dict
import yaml

# ロガーの初期化
logger = log.init(__name__, DEBUG)


def generate_prompts(input_text: str, product_name: str, item: Dict) -> List[Dict]:
    """ プロンプトを生成 """
    system_message = (
        'You will be provided with a check item, an item description, an expected output format and an excerpt texts about the product {product_name}. '
        'Your task is to refer to only the provided excerpt texts, then find out if the product meets the provided check item. '
        'Output \"True\" if the product meets the check item, \"False\" if not, or an empty string if it is impossible to find out it from only the provided excerpt texts. '
        'In addition, you MUST answer in JSON, the provided output format.'
    ).format(
        product_name=product_name
    )
    user_message = (
        'Check Item: {target}\n\n'
        'Item Description: {description}\n\n'
        'Output Format: {output_format}\n\n'
        'Excerpt texts: {input_text}'
    ).format(
        target=item['name'],
        description='\n'.join(
            [item['description'], item['research_description']]),
        output_format='{\"output\":\"\"}',
        input_text=input_text
    )
    prompts = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return prompts


def parse_answers(items: List[Dict], raw_answers: List[str], output_suffixes: Dict) -> List[Dict]:
    """ 回答をパース """
    answers = dict()
    for i in range(len(items)):
        json_str = extract_json(raw_answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format(
                '回答が読み取れないため空の値とします', '回答：' + raw_answers[i]))
            json_dict = {'output': ''}
        if json_dict['output'] == 'True':
            answers[items[i]['name'] +
                    output_suffixes['value_existence']] = 'あり'
            answers[items[i]['name'] + output_suffixes['for_search']] = '1'
            answers[items[i]['name'] + output_suffixes['for_display']] = '✓'
        elif json_dict['output'] == 'False':
            answers[items[i]['name'] +
                    output_suffixes['value_existence']] = 'あり'
            answers[items[i]['name'] + output_suffixes['for_search']] = '0'
            answers[items[i]['name'] + output_suffixes['for_display']] = '×'
        else:
            answers[items[i]['name'] +
                    output_suffixes['value_existence']] = '不明'
            answers[items[i]['name'] + output_suffixes['for_search']] = ''
            answers[items[i]['name'] + output_suffixes['for_display']] = ''
    return answers


def extract(input_text: str, product_name: str, items: List[Dict], output_suffixes: Dict) -> List[str]:
    """ 対象項目の情報を抽出 """
    raw_answers = []
    for item in items:
        messages = generate_prompts(input_text, product_name, item)
        logger.debug(log.format('二値項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers, output_suffixes)
    return answers, ', '.join(raw_answers)
