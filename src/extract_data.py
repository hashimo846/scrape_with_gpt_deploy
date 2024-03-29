from extract_json import extract_json
from logging import DEBUG, INFO
import openai_handler
import log
from typing import List, Dict
import json

# ロガーの初期化
logger = log.init(__name__, DEBUG)


def messages_question_prompt(input_text: str, product_name: str, item: Dict) -> List[Dict]:
    """ プロンプトを生成 """
    system_message = (
        'You will be provided with an extraction target, descriptions of target, an expected output format and an excerpt texts about the product {product_name}. '
        'Your task is to extract information about the provided extraction target in Japanese from only the provided excerpt texts. '
        'In addition, you MUST answer in JSON, the provided output format. '
    ).format(
        product_name=product_name
    )
    if item['value_type'] != 'text':
        system_message += 'Use \"' + \
            item['unit'] + '\" as the unit and output only the value.'
    user_message = (
        'Extraction Target: {target}\n\n'
        'Descriptions: {descriptions}\n\n'
        'Output Format: {output_format}\n\n'
        'Excerpt texts: {input_text}'
    ).format(
        target=item['name'],
        descriptions=item['description'] + ' ' + item['research_description'],
        output_format='{\"' + item['name'] + '\":\"\"}',
        input_text=input_text
    )
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return messages


def parse_answers(items: List[Dict], raw_answers: List[str], output_suffixes: Dict) -> List[Dict]:
    """ 回答をパース """
    all_dict = dict()
    for raw_answer in raw_answers:
        json_str = extract_json(raw_answer)
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            logger.warning(log.format(
                '回答が読み取れないため空の値とします', '回答：' + raw_answer))
            json_dict = dict()
        all_dict |= json_dict
    # アドミンインポート用の出力を生成
    answers = dict()
    for item in items:
        # 有効な回答がある場合のみ出力
        if item['name'] not in all_dict.keys():
            continue
        try:
            # 指定された型に変換
            if item['value_type'] == 'integer':
                answer = int(all_dict[item['name']])
            elif item['value_type'] == 'float':
                answer = float(all_dict[item['name']])
            elif item['value_type'] == 'text':
                answer = all_dict[item['name']]
            # 値の有無をチェック
            if answer == '':
                answers[item['name']+output_suffixes['value_existence']] = '不明'
                answers[item['name']+output_suffixes['for_search']] = ''
                answers[item['name']+output_suffixes['for_display']] = ''
            else:
                answers[item['name']+output_suffixes['value_existence']] = 'あり'
                answers[item['name']+output_suffixes['for_search']] = answer
                answers[item['name']+output_suffixes['for_display']
                        ] = str(answer) + item['unit']
        except Exception as e:
            answers[item['name'] + output_suffixes['value_existence']] = '不明'
            answers[item['name']+output_suffixes['for_search']] = ''
            answers[item['name']+output_suffixes['for_display']] = ''
    return answers


def extract(input_text: str, product_name: str, items: List[Dict], output_suffixes: Dict) -> List[str]:
    """ 対象項目の情報を抽出 """
    raw_answers = []
    for item in items:
        messages = messages_question_prompt(input_text, product_name, item)
        logger.debug(log.format('データ項目抽出プロンプト', '\n'.join(['---[role: {role}]---\n{content}'.format(
            role=message['role'], content=message['content']) for message in messages])))
        raw_answers.append(openai_handler.send_messages(
            messages, json_mode=True))
    answers = parse_answers(items, raw_answers, output_suffixes)
    return answers, raw_answers
