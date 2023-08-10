from google.oauth2 import service_account
import google.auth.exceptions
import gspread
import json
from logging import DEBUG, INFO
import os
import log
from time import sleep
from typing import Dict, List, Tuple

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# パラメータ
GOOGLE_CREDENTIAL_PATH = os.getenv('GOOGLE_CREDENTIAL_PATH')
MASTER_WORKSHEET = '項目_詳細情報'
PRODUCT_WORKSHHET = '商品_詳細情報'
OUTPUT_COLUMN = 7

# Jsonファイルの読み込み
def read_json(file_path:str) -> Dict:
    with open(file_path, 'r') as f:
        return json.load(f)

# Google APIの認証
def authorize_gspread(credential_path:str = GOOGLE_CREDENTIAL_PATH) -> gspread.Client:
    credentials =  service_account.Credentials.from_service_account_file(
        credential_path, 
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ]
    )
    gspread_client = gspread.authorize(credentials)
    return gspread_client

# URLからスプレッドシートを取得
def get_spreadsheet(sheet_url:str) -> gspread.Spreadsheet:
    gspread_client = authorize_gspread()
    spreadsheet = gspread_client.open_by_url(sheet_url)
    return spreadsheet

# URLとシート名からテーブルを取得（List）
def get_table(sheet_url:str, worksheet_name:str) -> List:
    while True:
        try:
            spreadsheet = get_spreadsheet(sheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)
            table = worksheet.get_all_values()
        except google.auth.exceptions.TransportError as e:
            logger.error(log.format('スプレッドシート取得失敗', e))
            sleep(1)
            logger.info(log.format('スプレッドシート再取得中'))
            continue
        else:
            break
    return table

# 指定した列の全データをテーブルから取得
def get_column(table:List, idx:int) -> List:
    return [row[idx] for row in table]

# スプレッドシートのURLからマスタ情報を取得
def get_master(sheet_url:str) -> Dict:
    # get master table
    logger.info(log.format('スプレッドシートからマスタ情報取得中'))
    master_table = get_table(sheet_url, MASTER_WORKSHEET)
    # get each column
    master = {
        'features': get_column(master_table, 0),
        'descriptions': get_column(master_table, 1),
        'formats': get_column(master_table, 2),
        'units': get_column(master_table, 3),
        'filters': get_column(master_table, 4),
    }
    return master
    

# マスタ情報から二値項目を取得
def get_boolean_items(master:Dict) -> List:
    items, i = [], 0
    while i < len(master['formats']):
        if master['formats'][i] == '二値':
            items.append(master['features'][i])
        i += 1
    return items

# マスタ情報からデータ項目を取得
def get_data_items(master:Dict) -> List:
    items, i = [], 0
    while i < len(master['formats']):
        if master['formats'][i] in ['小数','整数','フリーワード']:
            name = master['features'][i]
            value_type = master['formats'][i]
            unit = master['units'][i] if master['units'][i] != '' else None
            items.append({'name':name, 'value_type':value_type, 'unit':unit})
        i += 1
    return items

# マスタ情報から選択項目を取得
def get_option_items(master:Dict) -> List:
    items, i = [], 0
    while i < len(master['formats']):
        if master['formats'][i] == '管理用の値':
            name = master['features'][i]
            options = [master['filters'][i]]
            i += 1
            while i < len(master['formats']) and master['features'][i] == '':
                options.append(master['filters'][i])
                i += 1
            items.append({'name':name, 'options':options})
        else:
            i += 1
    return items

# スプレッドシートからマスタ情報の全項目を取得
def get_master_items(sheet_url:str) -> Dict:
    try:
        # get master data from spreadsheet
        master = get_master(sheet_url)
        # get each items
        boolean_items = get_boolean_items(master)
        data_items = get_data_items(master)
        option_items = get_option_items(master)
        # to dict
        master_items = {
            'boolean':boolean_items, 
            'data':data_items,
            'option':option_items,
        }
        return master_items
    except Exception as e:
        logger.error(log.format('マスタ情報取得失敗', e))
        return None

# extract valid columns from product table
def extract_valid_columns(target_row:List) -> Dict:
    important_keys = {'JAN(変更不可)':'jan', 'メーカー名(変更不可)':'maker', '商品名(変更不可)':'name', '型番(変更不可)':'model_number', '参照URL(編集可能)':'reference_url', '実行ボタン':'execute_button'}
    valid_columns = {}
    for idx, value in enumerate(target_row):
        if value in important_keys:
            key = important_keys[value]
        elif value == '':
            continue
        else:
            key = (value)
        # valid_columns = {key:idx}
        valid_columns[key] = idx
    return valid_columns

def get_product_table(sheet_url:str) -> List:
    logger.info(log.format('スプレッドシートから商品情報取得中'))
    product_table = get_table(sheet_url, PRODUCT_WORKSHHET)
    return product_table

# 商品情報を取得（janが空の場合はNoneを返す）
def get_product(sheet_url:str, target_row_idx:int) -> Dict:
    try:
        product_table = get_product_table(sheet_url)
        valid_columns = extract_valid_columns(product_table[0])
        target_row = product_table[target_row_idx]
        product = dict()
        for key in valid_columns.keys():
            product[key] = target_row[valid_columns[key]]
        if product['jan'] == '':
            return None
        else:
            return product
    except Exception as e:
        logger.error(log.format('商品情報取得失敗', e))
        return None

# get all products from product sheet
def get_all_products() -> List:
    # read input from json
    input_data = read_json(INPUT_PATH)
    
    # extract valid columns
    valid_columns = extract_valid_columns(product_table[0])
    # get products list
    products = []
    for target_row in product_table[1:]:
        product = extract_product(valid_columns, target_row)
        if product is not None:
            products.append(product)
    return products, valid_columns

# set values
def set_answers(sheet_url:str, target_row_idx, values) -> None:
    while True:
        try:
            spreadsheet = get_spreadsheet(sheet_url)
            worksheet = spreadsheet.worksheet(PRODUCT_WORKSHHET)
            values_size = len(values[0])
            start_cell = gspread.utils.rowcol_to_a1(target_row_idx+1, OUTPUT_COLUMN)
            end_cell = gspread.utils.rowcol_to_a1(target_row_idx+1, OUTPUT_COLUMN+values_size-1)
            worksheet.update('{}:{}'.format(start_cell, end_cell), values)
            '''spreadのバージョン6になると、引数の順番が逆になる
            UserWarning: [Deprecated][in version 6.0.0]: method signature will change to: 'Worksheet.update(value = [[]], range_name=)' arguments 'range_name' and 'values' will swap, values will be mandatory of type: 'list(list(...))'
            '''
        except Exception as e:
            logger.error(log.format('スプレッドシートへの書き出し失敗', e))
            sleep(1)
            logger.info(log.format('スプレッドシートへ再書き出し中'))
            break
        else:
            break

# 出力先のカラムのヘッダとインデックスを取得
def get_output_columns(sheet_url:str) -> Dict:
    table = get_product_table(sheet_url)
    output_header = table[0][OUTPUT_COLUMN-1:]
    output_columns = dict()
    for i in range(len(output_header)):
        output_columns[output_header[i]] = i
    return output_columns, len(output_header)

def output_answers(sheet_url:str, target_row_idx:int, answers:Dict) -> None :
    output_columns, output_size = get_output_columns(sheet_url)
    # make output data
    outputs = ['' for i in range(output_size)]
    # for data items
    for key in answers['data'].keys():
        outputs[output_columns[key]] = str(answers['data'][key])
    # for boolean items
    for key in answers['boolean'].keys():
        outputs[output_columns[key]] = str(answers['boolean'][key])
    # for option items
    for key in answers['option'].keys():
        outputs[output_columns[key]] = ', '.join(answers['option'][key])
    # set values
    set_answers(sheet_url, target_row_idx, [outputs])
    logger.info(log.format('スプレッドシートへの書き出し完了'))

def main():
    pass

if __name__ == '__main__':
    main()