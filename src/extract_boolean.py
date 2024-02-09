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
def messages_question_prompt(product: Dict, item: Dict) -> List[Dict]:
    system_message = (
        'You wil be provided with an check target, a target description and an output format. '
        'Your task is to extract the provided target information from an online website about a product {product_name} made by {product_maker}. '
        'Output the answer, \"True\" if the product meets the check target, \"False\" if not, or an empty string if it is not sure. '
        'In addition, please output the URL of the referenced website. '
        'You MUST answer in JSON, the provided output format.'
    ).format(
        product_name = product['name'], 
        product_maker = product['maker']
    )

    user_message = (
        'Check Target: {target}\n\n'
        'Description: {description}\n\n'
        'Output Format: {output_format}'
    ).format(
        target = item['name'],
        description = '\n'.join(
            [item['description'], item['research_description']]),
        output_format = '{\"answer\":\"\", \"URL\":[\"\"]}',
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
            json_dict = {'answer': ''}
        if json_dict['answer'] == 'True':
            answers_dict[items[i]['name']] = True
        elif json_dict['answer'] == 'False':
            answers_dict[items[i]['name']] = False
        else:
            answers_dict[items[i]['name']] = ''
    return answers_dict

# 対象項目の情報を抽出
def extract(product: Dict, items: List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(product, item)
        logger.debug(log.format('二値項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)
