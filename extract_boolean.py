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

# プロンプト中の質問部分の文字列を返す
def str_question(item:str) -> str:
    text = '今から入力、選択肢、期待する出力形式を与えます。\n'
    text += '入力のみを用いて、'
    text += '「' + item['name'] + '」に該当するかを調べ、その結果を選択肢の中から一つだけ選び、出力形式に従ってJSONで出力してください。\n'
    text += 'ただし、選択肢にないものは出力に含めないでください。\n'
    text += 'また、入力に' + item['name'] + 'に関する記載がない場合は、「不明」を出力してください。\n'
    return text

# プロンプト中の選択肢部分の文字列を返す
def str_option(option = OPTION) -> str:
    text = '#選択肢\n'
    text += '- '
    text += '\n- '.join(option) + '\n'
    return text

# プロンプト中の出力形式部分の文字列を返す
def str_format() -> str:
    text = '#出力形式\n'
    text += '{\"' + '出力' +'\":\"\"}' + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output() -> str:
    text = '#出力'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#入力\n'
    text += input_text + '\n'
    return text

# 生成したプロンプトのリスト返す
def str_prompt(item:Dict, input_text:str) -> List[str]:
    prompt = '\n'.join([
        str_question(item), 
        str_option(),
        str_format(), 
        str_input(input_text),
        str_output(),
    ])
    return prompt

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
            json_dict = {'出力': '不明'}
        if json_dict['出力'] == '該当する':
            answers_dict[items[i]['name']] = True
        elif json_dict['出力'] == '該当しない':
            answers_dict[items[i]['name']] = False
        else:
            answers_dict[items[i]['name']] = ''
    return answers_dict

# 対象項目の情報を抽出
def extract(input_text:str, product_name:str, items:List[Dict]) -> List[str]:
    answers = []
    for item in items:
        prompt = str_prompt(item, input_text)
        answers.append(openai_handler.send(prompt))
    answers = parse_answers(items, answers)
    return answers

def main():
    pass

if __name__ == '__main__':
    main()