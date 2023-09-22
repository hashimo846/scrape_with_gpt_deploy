from langchain.text_splitter import TokenTextSplitter, CharacterTextSplitter
import openai
import os
import openai_handler
import log
from logging import DEBUG, INFO
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 1プロンプトに含むトークン数の上限
MAX_TOKEN = int(os.getenv("MAX_TOKEN"))
# 入力を分割する際の重複するトークン数
OVERLAP_TOKEN = int(os.getenv("OVERLAP_TOKEN"))
# 1プロンプトに含む入力の最大トークン数
MAX_INPUT_TOKEN = int(os.getenv("MAX_INPUT_TOKEN"))

# プロンプト中の質問部分の文字列を返す
def str_question(product:Dict) -> str:
    text = 'あなたの仕事は、与えられた文章から商品' + product['name'] + 'に関する情報を抽出することです。\n'
    text += '固有名詞や定量的な情報は、可能な限り出力に含めてください。\n'
    text += 'また、次の重要項目に関する情報が文章中にある場合は、必ず出力に含めてください。\n'
    return text

def str_refine_question(product:Dict, existing_answer:str) -> str:
    text = 'あなたの仕事は、与えられた文章から商品' + product['name'] + 'に関する情報を抽出することです。\n'
    text += '途中までの抽出結果があります： ' + existing_answer + '\n'
    text += '必要に応じて与えられた文章から情報を抽出し、途中までの抽出結果に加えてください。\n'
    text += '固有名詞や定量的な情報は、可能な限り出力に含めてください。\n'
    text += 'また、次の重要項目に関する情報が文章中にある場合は、必ず出力に含めてください。\n'
    return text

# プロンプト中の重要項目の文字列を返す
def str_important_items(master_items:Dict) -> str:
    item_names = []
    for key in master_items.keys():
        for item in master_items[key]:
            item_names.append(item['name'])
    text = '#重要項目\n'
    text += ', '.join(item_names) + '\n'
    return text

# プロンプト中の入力部分の文字列を返す
def str_input(input_text:str) -> str:
    text = '#文章\n'
    text += input_text + '\n'
    return text

# プロンプト中の出力部分の文字列を返す
def str_output() -> str:
    return '#要約文'

# プロンプトの文字列を返す
def str_summarize_prompt(input_text:str, product:Dict, master_items:Dict) -> str:
    prompt = '\n'.join([
        str_question(product), 
        str_important_items(master_items),
        str_input(input_text),
        str_output(),
    ])
    return prompt

# プロンプトのメッセージ群を返す
def messages_summarize_prompt(input_text:str, product:Dict, master_items:Dict) -> List:
    item_names = []
    for key in master_items.keys():
        for item in master_items[key]:
            item_names.append(item['name'])
    messages = [
        {'role':'system', 'content':'You will be provided with key words and a quote from web pages. Your job is to extract information about the product ' + product['name'] +' from the given quote. In addition, you must include as much information as possible about the key words provided if they are mentioned in the quote.'},
        {'role':'user', 'content':'Quote: ' + input_text + '\n\nKey words: ' + ', '.join(item_names)}
    ]

# refine用のプロンプトの文字列を返す
def str_refine_prompt(existing_answer:str, input_text:str, product:Dict, master_items:Dict) -> str:
    prompt = '\n'.join([
        str_refine_question(product, existing_answer), 
        str_important_items(master_items),
        str_input(input_text),
        str_output(),
    ])
    return prompt

# 決められたトークン数ごとに分割する
def split_by_token(input_text:str, max_token:int = MAX_INPUT_TOKEN, overlap_token:int = OVERLAP_TOKEN) -> List[str]:
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=overlap_token)
    texts = text_splitter.split_text(input_text)
    return texts

# 商品ページからテキストを取得してGPTに入力し、商品情報をスクレイピング
def summarize(input_text:str, product:Dict, master_items:Dict) -> str:
    # return map_reduce(input_text, product, master_items)
    return refine(input_text, product, master_items)

# map-reduceアルゴリズムで要約
def map_reduce(input_text:str, product:Dict, master_items:Dict) -> str:
    # 入力文が長い場合は分割
    split_texts = split_by_token(input_text)
    # 分割が不要なトークン長になるまで要約
    while len(split_texts) > 1:    
        # GPTに入力用のプロンプトを作成
        prompts = [str_summarize_prompt(text, product, master_items) for text in split_texts]
        # 要約のプロンプトをログ出力
        for i in range(len(prompts)):
            logger.debug(log.format('プロンプト'+str(i+1), prompts[i]))
        # GPTの回答を取得
        answer_texts = [openai_handler.send(prompt) for prompt in prompts]
        # 回答を結合
        answer_text = '\n'.join(answer_texts)
        # 入力が長い場合は再分割
        split_texts = split_by_token(answer_text)
    # 結合された要約文を最後に要約（はじめから分割無しの場合は最低1回の要約が保証される）
    prompt = str_summarize_prompt(split_texts[0], product, master_items)
    logger.debug(log.format('最終要約プロンプト', prompt))
    answer_text = openai_handler.send(prompt)
    return answer_text

# refineアルゴリズムで要約
def refine(input_text:str, product:Dict, master_items:Dict) -> str:
    # 入力文が長い場合は分割(反復して要約するたびにプロンプトが長くなるので、1000Token短めに区切る)
    split_texts = split_by_token(input_text = input_text, max_token = MAX_TOKEN - 1000)

    # 初めの分割の要約
    # prompt = str_summarize_prompt(split_texts[0], product, master_items)
    # answer_text = openai_handler.send(prompt)

    messages = messages_summarize_prompt(split_texts[0], product, master_items)
    answer_text = openai_handler.send(prompt)
    
    logger.debug(log.format('初回要約プロンプト', prompt))

    # 二個目以降の分割の要約
    for split_text in split_texts[1:]:
        # GPTに入力用のプロンプトを作成
        prompt = str_refine_prompt(answer_text, split_text, product, master_items)
        # 要約のプロンプトをログ出力
        logger.debug(log.format('二回目以降要約プロンプト', prompt))
        # GPTの回答を取得
        answer_text = openai_handler.send(prompt)
    return answer_text

# テスト用
def main():
    pass

if __name__ == '__main__':
    main()