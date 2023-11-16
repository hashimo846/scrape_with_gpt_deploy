from extract_json import extract_json
import json
from langchain.text_splitter import TokenTextSplitter
from logging import DEBUG, INFO
import openai_handler
import log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトの生成


def messages_question_prompt(input_text: str, product_name: str, item: Dict) -> List[Dict]:
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
        description=item['description'],
        output_format='{\"' + 'output' + '\":\"\"}',
        input_text=input_text
    )

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return messages

# 回答をパース


def parse_answers(items: List[Dict], answers: List[str]) -> List[Dict]:
    answers_dict = dict()
    for i in range(len(items)):
        json_str = extract_json(answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format(
                '回答が読み取れないため空の値とします', '回答：' + answers[i]))
            json_dict = {'output': ''}
        if json_dict['output'] == 'True':
            answers_dict[items[i]['name']] = True
        elif json_dict['output'] == 'False':
            answers_dict[items[i]['name']] = False
        else:
            answers_dict[items[i]['name']] = ''
    return answers_dict

# 対象項目の情報を抽出


def extract(input_text: str, product_name: str, items: List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(input_text, product_name, item)
        logger.debug(log.format('二値項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)
