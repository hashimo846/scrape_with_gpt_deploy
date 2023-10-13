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

# 初回要約プロンプト生成
def messages_summarize_prompt(input_text:str, product:Dict, master_items:Dict, max_char = 1000) -> List:
    item_names = []
    for key in master_items.keys():
        for item in master_items[key]:
            item_names.append(item['name'])
    system_message = 'You will be provided with key words and a web page excerpt about the product {}. '.format(product['name'])
    system_message += 'Your task is to extract as detailed information as possible of specification and features about the product from only the provided excerpt, then you answer it in Japanese. '
    system_message += 'In addition, if there are the information related to the key words in the provided excerpt, you MUST include it in your answer.'
    system_message += 'You MUST answer in {} characters or less.'.format(max_char)
    user_message = 'Key Words: {}\n\nExcerpt: {}'.format(', '.join(item_names), input_text)
    messages = [
        {'role':'system', 'content':system_message},
        {'role':'user', 'content':user_message},
    ]
    return messages

# Refine用プロンプト生成
def messages_refine_prompt(existing_answer:str, input_text:str, product:Dict, master_items:Dict, max_char = 800) -> List:
    item_names = []
    for key in master_items.keys():
        for item in master_items[key]:
            item_names.append(item['name'])
    system_message = 'You will be provided with key words, an unfinished summary and a web page excerpt about the product {}. '.format(product['name'])
    system_message += 'Your task is to add as detailed information as possible of specification and features about the product to the unfinished summary from only the provided excerpt, then you produce a more enriched summary in Japanese. '
    system_message += 'In addition, if there are the information related to the key words in the provided summary or excerpt, you MUST include it in your answer.'
    system_message += 'You MUST answer in {} characters or less.'.format(max_char)
    user_message = 'Key Words: {}\n\nUnfinished Summary: {}\n\nExcerpt: {}'.format(','.join(item_names), existing_answer, input_text)
    messages = [
        {'role':'system', 'content':system_message},
        {'role':'user', 'content':user_message}
    ]
    return messages

# 決められたトークン数ごとに分割する
def split_by_token(input_text:str, max_token:int = MAX_INPUT_TOKEN, overlap_token:int = OVERLAP_TOKEN) -> List[str]:
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=overlap_token)
    texts = text_splitter.split_text(input_text)
    return texts

# 商品詳細スペックの要約
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
    # 入力文が長い場合は分割(最大1000トークン)
    split_texts = split_by_token(input_text = input_text, max_token = 1000)
    first_split = split_texts[0]
    additional_split = split_texts[1:]

    # 初めの分割の要約
    messages = messages_summarize_prompt(first_split, product, master_items)
    answer_text = openai_handler.send_messages(messages)
    logger.debug(log.format('初回要約プロンプト', messages))

    # 二個目以降の分割の要約
    for split in additional_split:
        # GPTに入力用のプロンプトを作成
        messages = messages_refine_prompt(answer_text, split, product, master_items)
        # 要約のプロンプトをログ出力
        logger.debug(log.format('二回目以降要約プロンプト', messages))
        # GPTの回答を取得
        answer_text = openai_handler.send_messages(messages)
    return answer_text