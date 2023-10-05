from logging import DEBUG, INFO
import log
import openai
import os
from time import sleep
from typing import List

# ロガーの初期化
logger = log.init(__name__, DEBUG)

#使用するAIモデル
MODEL = os.getenv("OPENAI_MODEL")

# OpenAI APIの認証
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")

# プロンプトを送信して回答を取得
def send(prompt:str) -> str:
    messages = [{'role':'user', 'content':prompt}]
    # send prompt
    while True:
        try:
            response = openai.ChatCompletion.create(model = MODEL,messages = messages, request_timeout = 60, temperature = 0, max_tokens = 1500)
        except Exception as e:
            logger.error(log.format('プロンプト送信失敗', 'ERROR_MESSAGE: {}'.format(e)))
            sleep(1)
            logger.info(log.format('プロンプト再送信中', 'SEND_PROMPT: {}'.format(messages)))
            continue
        else:
            break
    return response.choices[0]['message']['content'].strip()

# メッセージ群を送信して回答を取得
def send_messages(messages:List) -> str:
    # send prompt
    while True:
        try:
            logger.info(log.format('プロンプト送信中', 'SEND_PROMPT: {}'.format(messages)))
            response = openai.ChatCompletion.create(model = MODEL, messages = messages, request_timeout = 60, temperature = 0, max_tokens = 1500)
        except Exception as e:
            logger.error(log.format('プロンプト送信失敗', 'ERROR_MESSAGE: {}'.format(e)))
            sleep(1)
            logger.info(log.format('プロンプト再送信'))
            continue
        else:
            break
    logger.info(log.format('レスポンス内容', 'RECEIVE_RESPONSE: {}'.format(response.usage)))
    return response.choices[0]['message']['content'].strip()