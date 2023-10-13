from extract_json import extract_json
import json
from langchain.text_splitter import TokenTextSplitter
from logging import DEBUG, INFO
import openai_handler, log
from typing import List, Dict

# OPTION
OPTION = ['該当する', '該当しない', '不明']

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトの生成
def messages_question_prompt(input_text:str, product_name:str, item:Dict) -> List[Dict]:
    output_format = '{\"' + 'output' +'\":\"\"}'
    system_message = 'You will be provided with a check item, an expected output format and an overview text about the product {}. '.format(product_name)
    system_message += 'Your task is to refer to only the provided overview, then find out if the product meets the provided check item. '
    system_message += 'Output \"True\" if the product meets the check item, \"False\" if not, or an empty string if it is impossible to find out it from only the provided overview. '
    system_message += 'In addition, you MUST answer in JSON, the provided output format.'
    user_message = 'Check Item: {}\n\nOutput Format: {}\n\nOverview: {}'.format(item['name'], output_format, input_text)
    messages = [
        {'role':'system', 'content':system_message},
        {'role':'user', 'content':user_message}
    ]
    return messages

# 回答をパース
def parse_answers(items:List[Dict], answers:List[str]) -> List[Dict]:
    answers_dict = dict()
    for i in range(len(items)):
        json_str = extract_json(answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format('回答が読み取れないため空の値とします', '回答：' + answers[i]))
            json_dict = {'output': ''}
        if json_dict['output'] == 'True':
            answers_dict[items[i]['name']] = True
        elif json_dict['output'] == 'False':
            answers_dict[items[i]['name']] = False
        else:
            answers_dict[items[i]['name']] = ''
    return answers_dict

# 対象項目の情報を抽出
def extract(input_text:str, product_name:str, items:List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(input_text, product_name, item)
        logger.debug(log.format('二値項目抽出プロンプト', messages))
        raw_answers.append(openai_handler.send_messages(messages))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)