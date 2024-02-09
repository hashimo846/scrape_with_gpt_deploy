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
def send_messages(messages: List, json_mode: bool) -> str:
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
        'トークン使用量', 'RESPONSE: {}'.format(response.usage)))
    logger.info(log.format(
        'レスポンス', 'RESPONSE: {}'.format(response.choices[0].message.content.strip())))

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # メッセージ群を送信して回答を取得
    messages = [
     {
        "role": "system",
        "content": "You will be provided with an extraction target, a target description and an output format. Your task is to refer to the websites about a product α7 III made by ソニー and extract the provided target. Please output the answer and the URL of the referenced website. If there is no information about the target on the referenced website, output the empty string ("") for the answer. You MUST answer in JSON, the provided output format. \n\nExtraction Target: 重量（バッテリー込み）\n\nTarget Description: バッテリーとSDカード込みの重量\n\n「カメラ本体・バッテリー・SDカードをすべて含めた重さ」を指します。SDカードの重さを含まない数値しか記載がない場合、SDカードは1枚2gとして計算してください。出力する値は「350g」のように余計な情報は取り除き、「g」で終わる形にしてください。\n\nOutput Format: {\"重量（バッテリー込み）\":\"\", \"URL\":[\"\"]}"
      }
    ]
    response = send_messages(messages, json_mode=True)
    print(response)