from google.oauth2 import service_account
import gspread
from logging import DEBUG, INFO
import os
import log
from typing import Dict, List, Tuple
import yaml

logger = log.init(__name__, DEBUG)
GOOGLE_CREDENTIAL_PATH = os.getenv('GOOGLE_CREDENTIAL_PATH')
SHEET_INFO_PATH = os.getenv('SHEET_INFO_PATH')


class Spreadsheet:
    """ スプレッドシートを保持・操作するクラス """

    def __init__(self, sheet_url: str) -> None:
        """ コンストラクトにて認証とシートの取得をする """
        # NOTE: gspreadの認証
        gspread_client = self.__authorize_gspread()
        with open(SHEET_INFO_PATH) as file:
            self.sheet_info = yaml.safe_load(file)
        # NOTE: シートを取得
        self.spreadsheet = gspread_client.open_by_url(sheet_url)
        self.sheets, self.tables = dict(), dict()
        for sheet_key in ['master', 'research', 'output']:
            self.__get_sheet_table(sheet_key)

    def __get_sheet_table(self, sheet_key: str) -> Tuple[gspread.Worksheet, List]:
        """ シートとテーブルを取得 """
        self.sheets[sheet_key] = self.spreadsheet.worksheet(
            self.sheet_info[sheet_key]['name'])
        self.tables[sheet_key] = self.sheets[sheet_key].get_all_values()

    def get_master_items(self) -> Dict:
        """ シートから全項目情報を取得 """
        try:
            master_columns = self.__get_master_columns()
        except Exception as e:
            logger.error(log.format('マスタ情報取得失敗', e))
            return None
        try:
            boolean_items = self.__get_boolean_items(master_columns)
            data_items = self.__get_data_items(master_columns)
            option_items = self.__get_option_items(master_columns)
            master_items = {
                'boolean': boolean_items,
                'data': data_items,
                'option': option_items,
            }
            return master_items
        except Exception as e:
            logger.error(log.format('マスタ情報解析失敗', e))
            return None

    def get_inputs(self, target_row_idx: int, sheet_key: str = 'research') -> Dict:
        """ スプシの入力部分を取得 """
        try:
            # NOTE: 入力となるカラムのインデックスを特定
            header_row_idx = self.sheet_info[sheet_key]['header_row'] - 1
            header_row = self.tables[sheet_key][header_row_idx]
            input_columns_idx = dict()
            input_columns = self.sheet_info['research']['input_columns']
            for header_idx, header_value in enumerate(header_row):
                for column_key, column_value in input_columns.items():
                    if header_value == column_value:
                        input_columns_idx[column_key] = header_idx
                        break
            # NOTE: 対象の行から情報を取得
            target_row = self.tables[sheet_key][target_row_idx]
            inputs = dict()
            for key in input_columns_idx.keys():
                inputs[key] = target_row[input_columns_idx[key]]
            return inputs
        except Exception as e:
            logger.error(log.format('商品情報取得失敗', e))
            return None

    def get_feedback(self, target_row_idx: int, sheet_key: str = 'research') -> Dict:
        """ 実行フィードバックの出力部分を取得 """
        try:
            # NOTE: 対象の列を特定
            target_columns = self.sheet_info[sheet_key]['output_columns']
            target_columns_idx = self.__get_target_columns_idx(
                sheet_key, target_columns.values())
            # NOTE: 対象の行から情報を取得
            target_row = self.tables[sheet_key][target_row_idx]
            output = dict()
            for key in target_columns_idx.keys():
                output[key] = target_row[target_columns_idx[key]]
            return output
        except Exception as e:
            logger.error(log.format('出力情報取得失敗', e))
            return None

    def __get_target_columns_idx(self, sheet_key: str, target_columns: List) -> Dict:
        """ 対象カラムのインデックスをValueから取得 """
        header_row_idx = self.sheet_info[sheet_key]['header_row'] - 1
        header_row = self.tables[sheet_key][header_row_idx]
        columns_idx = dict()
        for header_idx, header_value in enumerate(header_row):
            if header_value in target_columns:
                columns_idx[header_value] = header_idx
        return columns_idx

    def set_feedback(self, target_row_idx: int, feedback: Dict, sheet_key: str = 'research') -> None:
        """ 実行フィードバックの出力部分の書き換え """
        target_columns = self.sheet_info[sheet_key]['output_columns']
        target_columns_idx = self.__get_target_columns_idx(
            sheet_key, target_columns.values())
        target_row = self.tables[sheet_key][target_row_idx]
        print(feedback)
        print(target_columns_idx)
        for key in feedback.keys():
            target_idx = target_columns_idx[target_columns[key]]
            target_row[target_idx] = str(feedback[key])
        start_cell = gspread.utils.rowcol_to_a1(target_row_idx+1, 1)
        end_cell = gspread.utils.rowcol_to_a1(
            target_row_idx+1, len(target_row))
        self.sheets[sheet_key].update([target_row], '{}:{}'.format(start_cell, end_cell),
                                      value_input_option='USER_ENTERED')

    def generate_output_headers(self, item_names: List[str], sheet_key: str = 'output') -> List[str]:
        """ 出力部分のヘッダーを生成 """
        output_headers = []
        for item_name in item_names:
            for suffix in self.sheet_info[sheet_key]['output_header_suffixes'].values():
                output_headers.append(item_name + suffix)
        return output_headers

    def set_output_header(self, output_headers: List[str], sheet_key: str = 'output') -> None:
        """ 抽出結果出力のためのヘッダーを出力(すでにヘッダー内に存在するものは項目は無視) """
        header_row_idx = self.sheet_info[sheet_key]['header_row'] - 1
        header_row = self.tables[sheet_key][header_row_idx]
        for output_header in output_headers:
            if output_header not in header_row:
                header_row.append(output_header)
        start_cell = gspread.utils.rowcol_to_a1(header_row_idx+1, 1)
        end_cell = gspread.utils.rowcol_to_a1(
            header_row_idx+1, len(header_row))
        self.sheets[sheet_key].update([header_row], '{}:{}'.format(start_cell, end_cell),
                                      value_input_option='USER_ENTERED')
        self.__get_sheet_table(sheet_key='output')

    def set_output(self, target_row_idx: int, output: Dict, sheet_key: str = 'output') -> None:
        """ スプシの出力部分を書き換え """
        target_columns_idx = self.__get_target_columns_idx(
            sheet_key='output', target_columns=output.keys())
        if len(target_columns_idx) == 0:
            return
        target_row = self.tables['output'][target_row_idx]
        output_start_column = self.sheet_info['output']['output_start_column']
        output_end_column = max(target_columns_idx.values()) + 1
        for key in output.keys():
            if key in target_columns_idx.keys():
                target_row[target_columns_idx[key]] = str(output[key])
        start_cell = gspread.utils.rowcol_to_a1(
            target_row_idx+1, output_start_column)
        end_cell = gspread.utils.rowcol_to_a1(
            target_row_idx+1, output_end_column)
        self.sheets[sheet_key].update([target_row[output_start_column-1:output_end_column]],
                                      '{}:{}'.format(start_cell, end_cell),
                                      value_input_option='USER_ENTERED')

    def get_output_suffixes(self) -> Dict:
        """ 出力部分のサフィックスを取得 """
        return self.sheet_info['output']['output_header_suffixes']

    def __get_master_columns(self, sheet_key: str = 'master') -> Dict:
        """ 項目情報シートの各カラムの情報を取得 """
        logger.info(log.format('スプレッドシートからマスタ情報取得中'))
        master_columns = dict()
        header_row_idx = self.sheet_info[sheet_key]['header_row'] - 1
        header_columns = self.sheet_info[sheet_key]['header_columns']
        for column_idx, column_value in enumerate(self.tables[sheet_key][header_row_idx]):
            for header_key, header_value in header_columns.items():
                if column_value == header_value:
                    master_columns[header_key] = self.__get_column(
                        self.tables[sheet_key], column_idx)
                    break
        return master_columns

    def __get_column(self, table: List, idx: int) -> List:
        """ 指定したカラムの情報を取得 """
        return [row[idx] for row in table]

    def __get_boolean_items(self, master_columns: Dict) -> List:
        """ 二値項目を取得 """
        items, i = [], 0
        target_type_name = self.sheet_info['master']['data_types']['boolean']
        while i < len(master_columns['formats']):
            if master_columns['formats'][i] == target_type_name:
                items.append({
                    'name': master_columns['features'][i],
                    'description': master_columns['descriptions'][i],
                    'research_description': master_columns['research_descriptions'][i],
                    'unit': master_columns['units'][i],
                })
            i += 1
        return items

    def __get_data_items(self, master_columns: Dict) -> List:
        """ データ項目を取得 """
        items, i = [], 0
        target_types = ['text', 'integer', 'float']
        data_types = self.sheet_info['master']['data_types']
        target_types_key = {data_types[key]: key for key in target_types}
        while i < len(master_columns['formats']):
            if master_columns['formats'][i] in target_types_key.keys():
                items.append({
                    'name': master_columns['features'][i],
                    'value_type': target_types_key[master_columns['formats'][i]],
                    'description': master_columns['descriptions'][i],
                    'research_description': master_columns['research_descriptions'][i],
                    'unit': master_columns['units'][i],
                })
            i += 1
        return items

    def __get_option_items(self, master_columns: Dict) -> List:
        """ 選択項目を取得 """
        items, i = [], 0
        target_type_name = self.sheet_info['master']['data_types']['option']
        while i < len(master_columns['formats']):
            count = 0
            if master_columns['formats'][i] == '管理用の値':
                options = [master_columns['filters'][i]]
                count += 1
                while i + count < len(master_columns['formats']) and master_columns['features'][i + count] == '':
                    options.append(master_columns['filters'][i + count])
                    count += 1
                items.append({
                    'name': master_columns['features'][i],
                    'description': master_columns['descriptions'][i],
                    'research_description': master_columns['research_descriptions'][i],
                    'unit': master_columns['units'][i],
                    'options': options,
                })
                i += count
            else:
                i += 1
        return items

    def __authorize_gspread(self, credential_path: str = GOOGLE_CREDENTIAL_PATH) -> gspread.Client:
        """ gspreadの認証 """
        credentials = service_account.Credentials.from_service_account_file(
            credential_path,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
            ]
        )
        gspread_client = gspread.authorize(credentials)
        return gspread_client


def main():
    """ テスト用のメイン関数 """
    pass


if __name__ == '__main__':
    main()
