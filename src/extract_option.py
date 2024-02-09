import json
from langchain.text_splitter import TokenTextSplitter
from logging import DEBUG, INFO
from extract_json import extract_json
import openai_handler
import log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトを生成
def messages_question_prompt(product: Dict, item: Dict) -> List[Dict]:
    system_message = (
        'You wil be provided with an extraction target, a target description, available options and an output format. '
        'Your task is to select the appropriate options for the provided target from an online website about the product {product_name} made by {product_maker}. '
        'Output the answer and the URL of the referenced website. If the answer is not sure, output an empty string. '
        'Do NOT output anything that is not included in the provided options. '
        'You MUST answer in JSON, the provided output format.'
    ).format(
      product_name = product['name'],
      product_maker = product['maker']
    )

    user_message = (
        'Extraction Target: {keyword}\n\n'
        'Description: {description}\n\n'
        'Options: {options}\n\n'
        'Output Format: {output_format}'
    ).format(
        keyword=item['name'],
        description = '\n'.join(
            [item['description'], item['research_description']]),
        options = ', '.join(item['options']),
        output_format = '{\"' + item['name'] + '\":[\"\", \"\"], \"URL\":[\"\"]}'
    )

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return messages

# 回答をパース


def parse_answers(items: List[Dict], answers: List[str]) -> List[Dict]:
    answers_dict = dict()
    item_names = [item['name'] for item in items]
    for i in range(len(items)):
        json_str = extract_json(answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format(
                '回答が読み取れないため空の値とします', '回答：' + answers[i]))
            json_dict = {'': ''}
        key_list = list(json_dict.keys())
        if len(key_list) == 0:
            continue
        # 有効な項目名のみ抽出
        if key_list[0] in item_names:
            valid_answers = []
            # 有効な選択肢のみ抽出
            try:
                for option in json_dict[key_list[0]]:
                    if option in items[i]['options']:
                        valid_answers.append(option)
                    elif option == '':
                        continue
                    else:
                        logger.debug(log.format('選択肢にないものが含まれています', str(
                            key_list[0]) + ':' + str(option)))
            except Exception as e:
                logger.warning(log.format('項目が抽出できませんでした', e))
                continue
            answers_dict[key_list[0]] = ', '.join(valid_answers)
    return answers_dict

# 対象項目の情報を抽出


def extract(product: Dict, items: List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(product, item)
        logger.debug(log.format('選択項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)
