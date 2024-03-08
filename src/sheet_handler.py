from google.oauth2 import service_account
import google.auth.exceptions
import gspread
import json
from logging import DEBUG, INFO
import os
import log
from time import sleep
from typing import Dict, List, Tuple
import yaml

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# GCPサービスアカウント認証情報
GOOGLE_CREDENTIAL_PATH = os.getenv('GOOGLE_CREDENTIAL_PATH')

# スプレッドシートのインスタンスを保持して扱うクラス
class Spreadsheet:
    # ワークシート名
    MASTER_WORKSHEET_NAME = '項目_詳細情報'
    PRODUCT_WORKSHHET_NAME = 'リサーチシート'
    # スプシ上の固定カラム
    INPUT_COLUMNS_KEY = {
        'JAN': 'jan',
        '商品ID': 'id',
        'メーカー名': 'maker',
        '商品名': 'name',
        '参照URL(編集可能)': 'reference_url',
    }
    FEEDBACK_COLUMNS_KEY = {
        '実行': 'execute_button',
        '実行終了ログ': 'execute_status',
        '取得文': 'get_text',
        '要約文': 'summary_text',
        '抽出結果': 'extract_result',
    }
    MASTER_COLUMNS_KEY = {
        '項目/Feature': 'features',
        '説明/Description': 'descriptions',
        'リサーチャー向け説明/Description for researcher': 'research_descriptions',
        '形式/Format': 'formats',
        '単位/Units': 'units',
        '検索フィルタ名/Filter': 'filters',
    }
    # クラス内で保持する変数
    spreadsheet = None
    master_worksheet = None
    master_table = []
    product_worksheet = None
    product_table = []

    # コンストラクタ（スプシURL必須）
    def __init__(self, sheet_url: str) -> None:
        while True:
            try:
                # Google APIの認証
                gspread_client = self.__authorize_gspread()
                # スプレッドシート取得
                self.spreadsheet = gspread_client.open_by_url(sheet_url)
                # ワークシート取得
                self.master_worksheet = self.spreadsheet.worksheet(
                    self.MASTER_WORKSHEET_NAME)
                self.product_worksheet = self.spreadsheet.worksheet(
                    self.PRODUCT_WORKSHHET_NAME)
                # テーブル取得
                self.master_table = self.master_worksheet.get_all_values()
                self.product_table = self.product_worksheet.get_all_values()
            except Exception as e:
                logger.error(log.format('スプレッドシート取得失敗', e))
                sleep(1)
                logger.info(log.format('スプレッドシート再取得中'))
                continue
            else:
                break

    # スプレッドシートからマスタ情報の全項目を取得
    def get_master_items(self) -> Dict:
        try:
            # get master data from spreadsheet
            master = self.__get_master()
        except Exception as e:
            logger.error(log.format('マスタ情報取得失敗', e))
            return None
        try:
            # get each items
            boolean_items = self.__get_boolean_items(master)
            data_items = self.__get_data_items(master)
            option_items = self.__get_option_items(master)
            # to dict
            master_items = {
                'boolean': boolean_items,
                'data': data_items,
                'option': option_items,
            }
            return master_items
        except Exception as e:
            logger.error(log.format('マスタ情報解析失敗', e))
            return None

    # スプシの入力部分を取得（JANから参照URLまでのカラム）
    def get_inputs(self, target_row_idx: int, target_column_idx: int) -> Dict:
        try:
            # 各カラムのインデックスを特定
            input_header = self.product_table[0][:target_column_idx]
            input_columns_idx = dict()
            for idx, value in enumerate(input_header):
                if value in self.INPUT_COLUMNS_KEY.keys():
                    input_columns_idx[self.INPUT_COLUMNS_KEY[value]] = idx
            # 対象の行から情報を取得
            target_range = self.product_table[target_row_idx][:target_column_idx]
            inputs = dict()
            for key in input_columns_idx.keys():
                inputs[key] = target_range[input_columns_idx[key]]
            if inputs['jan'] == '':
                return None
            else:
                return inputs
        except Exception as e:
            logger.error(log.format('商品情報取得失敗', e))
            return None

    # スプシの出力部分を取得（実行ボタンから最後の抽出項目までのカラム）
    def get_outputs(self, target_row_idx: int, target_column_idx: int) -> Dict:
        # 各カラムのインデックスを特定
        output_header = self.product_table[0][target_column_idx:]
        output_columns_idx = dict()
        for idx, value in enumerate(output_header):
            if value in self.FEEDBACK_COLUMNS_KEY.keys():
                output_columns_idx[self.FEEDBACK_COLUMNS_KEY[value]] = idx
            else:
                output_columns_idx[value] = idx
        # 対象の行から情報を取得
        target_range = self.product_table[target_row_idx][target_column_idx:]
        outputs = dict()
        for key in output_columns_idx.keys():
            outputs[key] = target_range[output_columns_idx[key]]
        return outputs

    # スプシの出力部分を書き換え（実行ボタンから最後の抽出項目までのカラム）
    def set_outputs(self, target_row_idx: int, target_column_idx: int, outputs: Dict) -> None:
        # 各カラムのインデックスを特定
        output_header = self.product_table[0][target_column_idx:]
        output_columns_idx = dict()
        for idx, value in enumerate(output_header):
            if value in self.FEEDBACK_COLUMNS_KEY.keys():
                output_columns_idx[self.FEEDBACK_COLUMNS_KEY[value]] = idx
            else:
                output_columns_idx[value] = idx
        # 対象の行に情報を書き込み
        target_range = self.product_table[target_row_idx][target_column_idx:]
        for key in outputs.keys():
            if key in output_columns_idx.keys():
                target_range[output_columns_idx[key]] = str(outputs[key])
        start_cell = gspread.utils.rowcol_to_a1(
            target_row_idx+1, target_column_idx+1)
        end_cell = gspread.utils.rowcol_to_a1(
            target_row_idx+1, target_column_idx+len(target_range))
        self.product_worksheet.update([target_range], '{}:{}'.format(start_cell, end_cell), value_input_option='USER_ENTERED')

    # マスター情報を取得
    def __get_master(self) -> Dict:
        # get master table
        logger.info(log.format('スプレッドシートからマスタ情報取得中'))
        # get each column
        master = dict()
        for column_idx, column_name in enumerate(self.master_table[0]):
            if column_name in list(self.MASTER_COLUMNS_KEY.keys()):
                master[self.MASTER_COLUMNS_KEY[column_name]
                       ] = self.__get_column(self.master_table, column_idx)
        return master

    # 指定した列の全データをテーブルから取得
    def __get_column(self, table: List, idx: int) -> List:
        return [row[idx] for row in table]

    # マスタ情報から二値項目を取得
    def __get_boolean_items(self, master: Dict) -> List:
        items, i = [], 0
        while i < len(master['formats']):
            if master['formats'][i] == '二値':
                items.append({
                    'name': master['features'][i],
                    'description': master['descriptions'][i],
                    'research_description': master['research_descriptions'][i],
                    'unit': master['units'][i],
                })
            i += 1
        return items

    # マスタ情報からデータ項目を取得
    def __get_data_items(self, master: Dict) -> List:
        items, i = [], 0
        while i < len(master['formats']):
            if master['formats'][i] in ['小数', '整数', 'フリーワード']:
                items.append({
                    'name': master['features'][i],
                    'value_type': master['formats'][i],
                    'description': master['descriptions'][i],
                    'research_description': master['research_descriptions'][i],
                    'unit': master['units'][i],
                })
            i += 1
        return items

    # マスタ情報から選択項目を取得
    def __get_option_items(self, master: Dict) -> List:
        items, i = [], 0
        while i < len(master['formats']):
            count = 0
            if master['formats'][i] == '管理用の値':
                options = [master['filters'][i]]
                count += 1
                while i + count < len(master['formats']) and master['features'][i + count] == '':
                    options.append(master['filters'][i + count])
                    count += 1
                items.append({
                    'name': master['features'][i],
                    'description': master['descriptions'][i],
                    'research_description': master['research_descriptions'][i],
                    'unit': master['units'][i],
                    'options': options,
                })
                i += count
            else:
                i += 1
        return items

    # Google APIの認証
    def __authorize_gspread(self, credential_path: str = GOOGLE_CREDENTIAL_PATH) -> gspread.Client:
        credentials = service_account.Credentials.from_service_account_file(
            credential_path,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
            ]
        )
        gspread_client = gspread.authorize(credentials)
        return gspread_client

# ローカル実行時のプロセス
def main():
    # テスト用のシートを指定
    with open('test_sheet.yml') as file:
        test_sheet = yaml.safe_load(file)
    sheet_url = test_sheet['url']
    spreadsheet = Spreadsheet(sheet_url)
    logger.debug(log.format('マスタ', spreadsheet.get_master_items()))
    logger.debug(log.format('入力', spreadsheet.get_inputs(2, 5)))
    output = spreadsheet.get_outputs(2, 5)
    logger.debug(log.format('出力部分', output))
    output['execute_status'] = 'ok'
    output['execute_button'] = 'TRUE'
    spreadsheet.set_outputs(2, 5, output)

if __name__ == '__main__':
    main()
