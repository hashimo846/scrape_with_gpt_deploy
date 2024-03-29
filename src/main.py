from logging import DEBUG, INFO
import extract_boolean
import extract_data
import extract_option
import sheet_handler
import scraper
import log
import functions_framework
import yaml

logger = log.init(__name__, DEBUG)


def main_process(sheet_url: str, target_row_idx: int) -> None:
    # 入力情報をログ出力
    logger.debug(log.format(
        '入力情報', 'ターゲット行:{}\nシートURL:{}'.format(target_row_idx, sheet_url)))

    # スプシを取得
    MAX_RETRY = 3
    for retry_count in range(MAX_RETRY):
        try:
            spreadsheet = sheet_handler.Spreadsheet(sheet_url)
        except Exception as e:
            logger.error(log.format('スプシの取得失敗({})'.format(retry_count+1), e))
            if retry_count+1 == MAX_RETRY:
                return
        else:
            break

    # スプシへのフィードバック(sheet_info.ymlのoutput_columnsに対応)
    feedback = {'execute_button': 'FALSE'}

    # マスタ情報を取得
    master_items = spreadsheet.get_master_items()
    if master_items == None:
        feedback['execute_status'] = 'マスタ情報の取得失敗\n'
        spreadsheet.set_feedback(target_row_idx, feedback)
        return
    else:
        logger.debug(log.format('マスタ情報', master_items))

    # 商品情報を取得
    product = spreadsheet.get_inputs(target_row_idx)
    if product == None:
        feedback['execute_status'] = '商品情報の取得失敗\n'
        spreadsheet.set_feedback(target_row_idx, feedback)
        return
    else:
        logger.debug(log.format('商品情報', product))

    # URLからページの全文を取得
    url_list = product['reference_url'].split('\n')
    while '' in url_list:
        url_list.remove('')
    logger.debug(log.format('WebページのURL', url_list))
    full_text, scrape_status = scraper.scrape_all(url_list)
    if full_text == None:
        feedback['execute_status'] = '参照URLへのアクセス失敗\n'
        feedback['execute_status'] += scrape_status + '\n'
        status = spreadsheet.set_feedback(target_row_idx, feedback)
        return
    else:
        feedback['execute_status'] = scrape_status + '\n'
        feedback['get_text'] = full_text
        logger.debug(log.format('Webページから取得した全文', full_text))
    # with open('test_sheet.yml') as file:
    #     test_sheet = yaml.safe_load(file)
    #     full_text = test_sheet['sample_text']
    #     feedback['execute_status'] = '\n'

    # 取得文から各項目を抽出
    answers = dict()
    raw_answers = dict()
    output = dict()
    answers['data'], raw_answers['data'] = extract_data.extract(
        input_text=full_text, product_name=product['name'], items=master_items['data'], output_suffixes=spreadsheet.get_output_suffixes())
    logger.debug(log.format('データ項目の抽出結果', answers['data']))
    answers['boolean'], raw_answers['boolean'] = extract_boolean.extract(
        input_text=full_text, product_name=product['name'], items=master_items['boolean'], output_suffixes=spreadsheet.get_output_suffixes())
    logger.debug(log.format('Boolean項目の抽出結果', answers['boolean']))
    answers['option'], raw_answers['option'] = extract_option.extract(
        input_text=full_text, product_name=product['name'], items=master_items['option'],  output_suffixes=spreadsheet.get_output_suffixes())
    logger.debug(log.format('複数選択項目の抽出結果', answers['option']))
    output |= answers['data'] | answers['boolean'] | answers['option']
    feedback['extract_result'] = str(raw_answers)

    # 実行結果を出力
    item_names = []
    for item_type in master_items.keys():
        for item in master_items[item_type]:
            item_names.append(item['name'])
    output_headers = spreadsheet.generate_output_headers(item_names)
    spreadsheet.set_output_header(output_headers)
    spreadsheet.set_output(target_row_idx, output)
    feedback['execute_status'] += '実行終了\n'
    spreadsheet.set_feedback(target_row_idx, feedback)

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
    main_process(sheet_url, target_row_idx)
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
        # メインプロセスを実行
        main_process(sheet_url, target_row_idx)
    return


if __name__ == "__main__":
    main()
