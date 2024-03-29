from logging import DEBUG, INFO
import log
import openai
import os
from time import sleep
from typing import List

logger = log.init(__name__, DEBUG)

# NOTE: 使用するAIモデル
MODEL = os.getenv("OPENAI_MODEL")

# NOTE: OpenAI APIの認証
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

# NOTE: GPTの回答の最大トークン数
RESPONCE_MAX_TOKEN = int(os.getenv("RESPONCE_MAX_TOKEN"))


def send_messages(messages: List, json_mode=False) -> str:
    """ メッセージ群を送信して回答を取得 """
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                timeout=60,
                temperature=0,
                max_tokens=RESPONCE_MAX_TOKEN,
                response_format={
                    'type': 'json_object' if json_mode else 'text'}
            )
        except Exception as e:
            logger.error(log.format(
                'プロンプト送信失敗', 'ERROR_MESSAGE: {}'.format(e)))
            sleep(1)
            logger.info(log.format('プロンプト再送信'))
            continue
        else:
            break
    logger.info(log.format(
        'レスポンス', 'RESPONSE: {}'.format(response.choices[0].message.content.strip())))

    return response.choices[0].message.content.strip()
