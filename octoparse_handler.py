from bs4 import BeautifulSoup
from logging import DEBUG, INFO
import requests
import log
import os
from typing import List, Dict

# ロガーの初期化
logger = log.init(__name__, DEBUG)

OCTOPARSE_USERNAME = os.getenv('OCTOPARSE_USERNAME')
OCTOPARSE_PASSWORD = os.getenv('OCTOPARSE_PASSWORD')
OCTOPARSE_API_BASE_URL = 'https://openapi.octoparse.com/'

# アクセストークンの取得
def get_access_token(username:str = OCTOPARSE_USERNAME, passward:str = OCTOPARSE_PASSWORD, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'token'
    header = {"Content-Type": "application/json"}
    body = {
        'username':username,
        'password':passward,
        'grant_type':'password'
    }
    return requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()

# アクセストークンの有効期限更新
def refresh_access_token(refresh_token:str, base_url:str = OCTOPARSE_API_BASE_URL, ) -> Dict:
    path = 'token'
    header = {"Content-Type": "application/json"}
    body = {
        'refresh_token':refresh_token,
        'grant_type':'refresh_token'
    }
    return requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()

# タスクグループの一覧を取得（タスクグループIDも取得できる）
def get_task_groups(access_token:str, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'taskGroup'
    header = {'Authorization': 'Bearer ' + access_token}
    return requests.get(base_url+path, headers=header, timeout = 3.0).json()

# グループ名を指定してタスクグループIDを取得
def get_task_group_id(access_token:str, task_name:str, base_url:str = OCTOPARSE_API_BASE_URL) -> int:
    task_groups = get_task_groups(access_token)
    for task_group in task_groups['data']:
        if task_group['taskGroupName'] == task_name:
            return task_group['taskGroupId']
    return None

# タスクグループIDを指定してタスク一覧を取得
def get_tasks(access_token:str, task_group_id:int, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'task/search'
    header = {'Authorization': 'Bearer ' + access_token}
    params = {'taskGroupId':task_group_id}
    return requests.get(base_url+path, headers=header, params=params, timeout = 3.0).json()

# タスクグループIDとタスク名を指定してタスクIDを取得
def get_task_id(access_token:str, task_group_id:int, task_name:str, base_url:str = OCTOPARSE_API_BASE_URL) -> str:
    tasks = get_tasks(access_token, task_group_id)
    for task in tasks['data']:
        if task['taskName'] == task_name:
            return task['taskId']
    return None

# タスクIDを指定してアクション一覧を取得
def get_actions(access_token:str, task_id:str, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'task/getActions'
    header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    body = {
        "taskIds": [task_id],
        "actionTypes": ["LoopAction","NavigateAction","EnterTextAction"]
    }
    return requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()['data'][0]['actions']

# タスクIDとアクション名を指定してアクションIDを取得
def get_action_id(access_token:str, task_id:str, action_name:str, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    actions = get_actions(access_token, task_id)
    for action in actions:
        if action['name'] == action_name:
            return action['actionId']
    return None

# タスクIDとアクションIDを指定してアクションのパラメータ(url)を更新
def update_action_url(access_token:str, task_id:str, action_id:str, url:str, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'task/updateActionProperties'
    header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    body = {
        "taskId": task_id,
        "actions": [{
            "actionType": "NavigateAction",
            "actionId": action_id,
            "properties": [{
                "name": "url",
                "value": url
            }]
        }]
    }
    response = requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()
    return response

def start_task(access_token:str, task_id:str, base_url:str = OCTOPARSE_API_BASE_URL) -> Dict:
    path = 'cloudextraction/start'
    header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
    body = {'taskId': task_id}
    response = requests.post(base_url+path, headers=header, json=body, timeout = 3.0).json()
    return response

def main():
    response = get_access_token()
    logger.debug(log.format('アクセストークン取得', response))
    task_groups = get_task_groups(response['data']['access_token'])
    logger.debug(log.format('タスクグループ一覧取得', task_groups))
    group_id = get_task_group_id(response['data']['access_token'], 'Scrape for LLM')
    logger.debug(log.format('タスクグループID取得', group_id))

    response = refresh_access_token(response['data']['refresh_token'])
    logger.debug(log.format('アクセストークン更新', response))
    tasks = get_tasks(response['data']['access_token'], group_id)
    logger.debug(log.format('タスク一覧取得', tasks))
    task_id = get_task_id(response['data']['access_token'], group_id, 'Scrape Amazon')
    logger.debug(log.format('タスクID取得', task_id))

    response = refresh_access_token(response['data']['refresh_token'])
    logger.debug(log.format('アクセストークン更新', response))
    actions = get_actions(response['data']['access_token'], task_id)
    logger.debug(log.format('アクション一覧取得', actions))
    action_id = get_action_id(response['data']['access_token'], task_id, 'open_page')
    logger.debug(log.format('アクションID取得', action_id))

    response = refresh_access_token(response['data']['refresh_token'])
    logger.debug(log.format('アクセストークン更新', response))
    sample_url = 'https://www.amazon.co.jp/gp/product/B0C2BV9TJK/ref=cg_2023MDE7_2b1_w?pf_rd_m=A3P5ROKL5A1OLE&pf_rd_s=slot-1&pf_rd_r=KP34WVW6TG2TK9QCV6RB&pf_rd_t=0&pf_rd_p=91028cb3-4575-4831-a249-d7d2182e667d&pf_rd_i=6946224a&th=1'
    status = update_action_url(response['data']['access_token'], task_id, action_id, sample_url)
    logger.debug(log.format('アクションのパラメータ更新', status))
    actions = get_actions(response['data']['access_token'], task_id)
    logger.debug(log.format('アクション一覧取得', actions))
    # TODO:以上のような処理を事前に実行し、得られたID群を定数として定義し、API呼び出し回数を減らす。
    # TODO:APIアクセス時にアクセストークンの期限が切れないように、API呼び出し前にアクセストークンの期限を更新する（or アクセストークンを発行する）。

if __name__ == "__main__":
    main()