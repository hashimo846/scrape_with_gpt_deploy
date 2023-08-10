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
def str_question(item:str, is_multi_prompt:bool) -> str:
    text = '今から入力、選択肢、期待する出力形式を与えます。\n'
    text += '入力のみを用いて、'
    text += '「' + item + '」に該当するかを調べ、その結果を選択肢の中から一つだけ選び、出力形式に従ってJSONで出力してください。\n'
    text += 'ただし、選択肢にないものは出力に含めないでください。\n'
    text += 'また、入力に' + item + 'に関する記載がない場合は、「不明」を出力してください。\n'
    if is_multi_prompt:
        text += 'また、入力の文が長いのため、<end>というまで出力を生成しないでください。\n'
        text += '<end>というまでは<ok>とだけ返答してください。\n'
    return text

# プロンプト中の選択肢部分の文字列を返す
def str_option(option = OPTION) -> str:
    text = '#選択肢\n'
    text += '- '
    text += '\n- '.join(option) + '\n'
    return text

# プロンプト中の出力形式部分の文字列を返す
def str_format(item:str) -> str:
    text = '#出力形式\n'
    text += '{\"' + '出力' +'\":\"\"}' + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output(is_multi_prompt:bool) -> str:
    text = '#出力'
    if is_multi_prompt:
        text += '\n<end>'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#入力\n'
    text += input_text + '\n'
    return text

# 生成したプロンプトのリスト返す
def str_prompts(item:str, input_texts:List[str]) -> List[str]:
    is_multi_prompt = 1 < len(input_texts)
    prompts_list = []
    
    if is_multi_prompt:
        # first prompt
        prompt_text = '\n'.join([
            str_question(item, is_multi_prompt), 
            str_option(),
            str_format(item), 
            str_input(input_texts[0]),
        ])
        prompts_list.append(prompt_text)
        # intermediate prompts
        for input_text in input_texts[1:-1]:
            prompts_list.append(input_text)
        # last prompt
        prompt_text = '\n'.join([
            input_texts[-1] + '\n',
            str_output(is_multi_prompt),
        ])
        prompts_list.append(prompt_text)
    else:
        # only one prompt
        prompt_text = '\n'.join([
            str_question(item, is_multi_prompt), 
            str_option(),
            str_format(item), 
            str_input(input_texts[0]),
            str_output(is_multi_prompt),
        ])
        prompts_list.append(prompt_text)
    return prompts_list

# 回答をパース
def parse_answers(items:List[str], answers:List[str]) -> List[Dict]:
    answers_dict = dict()
    for i in range(len(items)):
        json_str = extract_json(answers[i])
        try:
            json_dict = json.loads(json_str)
        except Exception as e:
            logger.warning(log.format('JSON形式で出力されていません', e))
            json_dict = {'出力': '不明'}
        if json_dict['出力'] == '該当する':
            answers_dict[items[i]] = True
        elif json_dict['出力'] == '該当しない':
            answers_dict[items[i]] = False
        else:
            answers_dict[items[i]] = None
    return answers_dict

# 対象項目の情報を抽出
def extract(split_inputs:List[str], product_name:str, items:List[Dict]) -> List[str]:
    answers = []
    for item in items:
        prompts = str_prompts(item, split_inputs)
        answers.append(openai_handler.send(prompts))
    answers = parse_answers(items, answers)
    return answers

def main():
    pass

if __name__ == '__main__':
    main()