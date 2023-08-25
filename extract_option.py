import json
from langchain.text_splitter import TokenTextSplitter
from logging import DEBUG, INFO
from extract_json import extract_json
import openai_handler, log
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# プロンプト中の質問部分の文字列を返す
def str_question(product_name:str, item:Dict) -> str:
    text = '今から入力、選択肢、期待する出力形式を与えます。\n'
    text += '入力のみを用いて、' + product_name + 'について、'
    text += item['name'] + 'を選択肢の中から複数選択し、出力形式に従ってJSONで出力してください。\n'
    text += 'もし選択肢の中に該当するものがない場合は、出力形式に従って空の文字列を出力してください。\n'
    text += 'また、選択肢にないものは出力に含めないでください。\n'
    return text

# プロンプト中の選択肢部分の文字列を返す
def str_option(item:Dict) -> str:
    text = '#選択肢\n'
    text += '- '
    text += '\n- '.join(item['options']) + '\n'
    return text

# プロンプト中の出力形式部分の文字列を返す
def str_format(item:Dict) -> str:
    text = '#出力形式\n'
    text += '{\"' + item['name'] +'\":[\"\",\"\"]}' + '\n'
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
def str_prompt(product_name:str, item:Dict, input_text:str) -> List[str]:
    prompt = '\n'.join([
        str_question(product_name, item), 
        str_option(item),
        str_format(item), 
        str_input(input_text),
        str_output(),
    ])
    return prompt

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
        # 有効な項目名のみ抽出
        if key_list[0] in item_names:
            answers_dict[key_list[0]] = []
            # 有効な選択肢のみ抽出
            try:
                for option in json_dict[key_list[0]]:
                    if option in items[i]['options']:
                        answers_dict[key_list[0]].append(option)
                    elif option == '':
                        continue
                    else:
                        logger.debug(log.format('選択肢にないものが含まれています', str(key_list[0]) + ':' + str(option)))
            except Exception as e:
                logger.warning(log.format('項目が抽出できませんでした', e))
                continue
    return answers_dict

# 対象項目の情報を抽出
def extract(input_text:str, product_name:str, items:List[Dict]) -> List[str]:
    answers = []
    for item in items:
        prompt = str_prompt(product_name, item, input_text)
        answers.append(openai_handler.send(prompt))
    answers = parse_answers(items, answers)
    return answers
