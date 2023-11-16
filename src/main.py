from logging import DEBUG, INFO
import extract_boolean, extract_data, extract_option
import sheet_handler, scraper, summarize, log
import functions_framework
import yaml

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# メインプロセス
def main_process(sheet_url:str, target_row_idx:int, target_column_idx:int) -> None:
    # 入力情報をログ出力
    logger.debug(log.format('入力情報', 'ターゲット行/列:{}/{}\nスプレッドシートURL:{}'.format(target_row_idx, target_column_idx, sheet_url)))
    # スプシを取得
    spreadsheet = sheet_handler.Spreadsheet(sheet_url)
    # スプシ出力用の辞書
    outputs = {
        'execute_button':'FALSE',
        'execute_status':'',
        'get_text':'',
        'summary_text':'',
        'extract_result':'',
    }

    # マスタ情報を取得
    master_items = spreadsheet.get_master_items()
    if master_items == None:
        outputs['execute_status'] += 'マスタ情報の取得失敗\n'
        status = spreadsheet.set_outputs(target_row_idx, target_column_idx, outputs)
        return
    else: 
        logger.debug(log.format('マスタ情報', master_items))

    # 商品情報を取得
    product = spreadsheet.get_inputs(target_row_idx, target_column_idx)
    if product == None:
        outputs['execute_status'] += '商品情報の取得失敗\n'
        status = spreadsheet.set_outputs(target_row_idx, target_column_idx, outputs)
        return
    else:
        logger.debug(log.format('商品情報', product))

    # URLからページの全文を取得
    url_list = product['reference_url'].split('\n')
    logger.debug(log.format('WebページのURL', url_list))
    full_text, scrape_status = scraper.scrape_all(url_list)
    if full_text == None:
        outputs['execute_status'] += '参照URLへのアクセス失敗\n'
        outputs['execute_status'] += scrape_status + '\n'
        status = spreadsheet.set_outputs(target_row_idx, target_column_idx, outputs)
        return
    else:
        outputs['execute_status'] += scrape_status + '\n'
        outputs['get_text'] = full_text
        logger.debug(log.format('Webページから取得した全文', full_text))

    # 要約文から各項目を抽出
    answers = dict()
    raw_answers = dict()
    answers['data'], raw_answers['data'] = extract_data.extract(input_text = full_text, product_name = product['name'], items = master_items['data'])
    logger.debug(log.format('データ項目の抽出結果', answers['data']))
    answers['boolean'], raw_answers['boolean'] = extract_boolean.extract(input_text = full_text, product_name = product['name'], items = master_items['boolean'])
    logger.debug(log.format('Boolean項目の抽出結果', answers['boolean']))
    answers['option'], raw_answers['option'] = extract_option.extract(input_text = full_text, product_name = product['name'], items = master_items['option'])
    logger.debug(log.format('複数選択項目の抽出結果', answers['option']))
    outputs |= answers['data'] | answers['boolean'] | answers['option']
    outputs['extract_result'] += str(raw_answers)

    # 各回答を出力
    outputs['execute_status'] += '実行終了\n'
    status = spreadsheet.set_outputs(target_row_idx, target_column_idx, outputs)
    if status == 'error': return

    # 正常終了
    logger.info('正常終了')
    return

# HTTPリクエスト時のプロセス
@functions_framework.http
def on_http_trigger(request) -> None:
    # 入力を取得
    request_json = request.get_json()
    sheet_url = request_json['sheet_url']
    target_row_idx = int(request_json['target_row_idx'])
    target_column_idx = int(request_json['target_column_idx'])

    # メインプロセスを実行
    main_process(sheet_url, target_row_idx, target_column_idx)
    return

# ローカル実行時のプロセス
def main() -> None:
    # テスト用のシートを指定
    with open('test_sheet.yml') as file:
        test_sheet = yaml.safe_load(file)
    # シートの各行を処理
    for target_row_idx in range(test_sheet['start_row'], test_sheet['end_row']):
        # 入力を取得
        sheet_url = test_sheet['url']
        target_column_idx = 5
        # メインプロセスを実行
        main_process(sheet_url, target_row_idx, target_column_idx)
    return

if __name__ == "__main__":
    main()