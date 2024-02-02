from logging import DEBUG, INFO
import log
import openai
import os
from time import sleep
from typing import List

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# 使用するAIモデル
MODEL = os.getenv("OPENAI_MODEL")

# OpenAI APIの認証
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

# GPTの回答の最大トークン数
RESPONCE_MAX_TOKEN = int(os.getenv("RESPONCE_MAX_TOKEN"))

# メッセージ群を送信して回答を取得
def send_messages(messages: List, json_mode=False) -> str:
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
        'レスポンス', 'RESPONSE: {}'.format(response.usage)))

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # メッセージ群を送信して回答を取得
    messages = [
        {
            "role": "system",
            "content": (
              'You wil be provided with an extraction target,target descriptions and the output format. '
              'Your task is to research the extraction target about the product {} from web sites. '
              'Output the research result and the URL of the web site you referred to. '
              'In addition, you MUST answer in JSON, the provided output format.'
            ).format('EOS R10')
        },
        {
            "role": "user",
            "content": (
              'Extraction target: ファインダー形式\n'
              'Target descriptions: ここでのファイダー形式とは「カメラに搭載されているファインダーの種類」を指します。電子式（EVF）の場合は「電子ビューファインダー（EVF）」としてください。'
              'Output format: {\"ファインダー形式\":\"\", \"URL\":[\"\"]}'
            )
        }
    ]
    response = send_messages(messages, json_mode=True)
    print(response)