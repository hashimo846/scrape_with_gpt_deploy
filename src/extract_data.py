from langchain.text_splitter import TokenTextSplitter
from extract_json import extract_json
from logging import DEBUG, INFO
import openai_handler
import log
from typing import List, Dict
import json

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトを生成
def messages_question_prompt(product: Dict, item: Dict, language = 'Japanese') -> List[Dict]:
    system_message = (
        'You will be provided with an extraction target, a target description and an output format. '
        'Your task is to refer to the websites about a product {product_name} made by {product_maker} and extract the provided target. '
        'Please output the answer and the URL of the referenced website. '
        'If there is no information about the target on the referenced website, output the empty string ("") for the answer. '
        'You MUST answer in JSON, the provided output format. '
    ).format(
        product_name=product['name'],
        product_maker=product['maker']
    )

    user_message = (
        'Extraction Target: {target}\n\n'
        'Target Description: {description}\n\n'
        'Output Format: {output_format}'
    ).format(
        target = item['name'],
        description = '\n'.join(
            [item['description'], item['research_description']]),
        output_format = '{\"' + item['name'] + '\":\"\", \"URL\":[\"\"]}',
    )

    messages = [
        {'role': 'system', 'content': system_message + '\n\n' + user_message}
        # {'role': 'user', 'content': user_message}
    ]
    return messages

# 回答をパース
def parse_answers(items: Dict, answers: List[str]) -> List[Dict]:
    all_dict = dict()
    for answer in answers:
        json_str = extract_json(answer)
        try:
            json_dict = json.loads(json_str)
            json_dict.pop('URL', None)
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
def extract(product: Dict, items: List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(
            product, item)
        logger.debug(log.format('データ項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)
