import json
from langchain.text_splitter import TokenTextSplitter
from logging import DEBUG, INFO
from extract_json import extract_json
import openai_handler, log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプトを生成
def messages_question_prompt(input_text:str, product_name:str, item:Dict) -> List[Dict]:
    output_format = '{\"' + item['name'] +'\":[\"\", \"\"]}'
    system_message = 'You will be provided with a key word, available options, an expected output format and an overview text about the product {}. '.format(product_name)
    system_message += 'Your task is to refer to only the provided overview, then select appropriate options for the key word from only the provided options. '
    system_message += 'If there is no appropriate option, output empty string (""). '
    system_message += 'In addition, you MUST answer in JSON, the provided output format. '
    system_message += 'Do NOT output anything that is not included in the provided options.'
    user_message = 'Key Word: {}\n\nOptions: {}\n\nOutput Format: {}\n\nOverview: {}'.format(item['name'], ', '.join(item['options']), output_format, input_text)
    messages = [
        {'role':'system', 'content':system_message},
        {'role':'user', 'content':user_message}
    ]
    return messages

# 回答をパース
def parse_answers(items:List[Dict], answers:List[str]) -> List[Dict]:
    answers_dict = dict()
    item_names = [item['name'] for item in items]
    for i in range(len(items)):
        json_str = extract_json(answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format('回答が読み取れないため空の値とします', '回答：' + answers[i]))
            json_dict = {'':''}
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
                        logger.debug(log.format('選択肢にないものが含まれています', str(key_list[0]) + ':' + str(option)))
            except Exception as e:
                logger.warning(log.format('項目が抽出できませんでした', e))
                continue
            answers_dict[key_list[0]] = ', '.join(valid_answers)
    return answers_dict

# 対象項目の情報を抽出
def extract(input_text:str, product_name:str, items:List[Dict]) -> List[str]:
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(input_text, product_name, item)
        logger.debug(log.format('選択項目抽出プロンプト', messages))
        raw_answers.append(openai_handler.send_messages(messages))
    answers = parse_answers(items, raw_answers)
    return answers, ', '.join(raw_answers)