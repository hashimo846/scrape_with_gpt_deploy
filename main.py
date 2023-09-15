from logging import DEBUG, INFO
import extract_boolean, extract_data, extract_option
import sheet_handler, scraper, summarize, log
import functions_framework

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# メインプロセス
def main_process(sheet_url:str, target_row_idx:int, target_column_idx:int) -> str:
    # 入力情報をログ出力
    logger.debug(log.format('入力情報', 'ターゲット行/列:{}/{}\nスプレッドシートURL:{}'.format(target_row_idx, target_column_idx, sheet_url)))

    # マスタ情報を取得
    master_items = sheet_handler.get_master_items(sheet_url)
    if master_items == None: return 'マスタ情報の取得失敗'
    logger.debug(log.format('マスタ情報', master_items))

    # 商品情報を取得
    product = sheet_handler.get_product(sheet_url, target_row_idx)
    if product == None: return '商品情報の取得失敗'
    logger.debug(log.format('商品情報', product))

    # URLからページの全文を取得
    url_list = product['reference_url'].split('\n')
    logger.debug(log.format('WebページのURL', url_list))
    full_text = scraper.scrape_all(url_list)
    if full_text == None: return '参照URLへのアクセス失敗'
    logger.debug(log.format('Webページから取得した全文', full_text))
    
    # 全文から要約文を取得
    summarize_text = summarize.summarize(full_text, product, master_items)
    logger.debug(log.format('要約文', summarize_text))

    # 要約文から各項目を抽出
    answers = dict()
    answers['data'] = extract_data.extract(input_text = summarize_text, product_name = product['name'], items = master_items['data'])
    logger.debug(log.format('データ項目の抽出結果', answers['data']))
    answers['boolean'] = extract_boolean.extract(input_text = summarize_text, product_name = product['name'], items = master_items['boolean'])
    logger.debug(log.format('Boolean項目の抽出結果', answers['boolean']))
    answers['option'] = extract_option.extract(input_text = summarize_text, product_name = product['name'], items = master_items['option'])
    logger.debug(log.format('複数選択項目の抽出結果', answers['option']))

    # 各回答を出力
    status = sheet_handler.output_answers(sheet_url, target_row_idx, target_column_idx, answers)
    if status == 'error': return 'スプレッドシートへの書き込み失敗'   
    
    # 正常終了
    return '実行終了'

# HTTPリクエスト時のプロセス
@functions_framework.http
def on_http_trigger(request) -> str:
    # 入力を取得
    request_json = request.get_json()
    sheet_url = request_json['sheet_url']
    target_row_idx = int(request_json['row'])
    target_column_idx = int(request_json['column'])

    # メインプロセスを実行
    status = main_process(sheet_url, target_row_idx, target_column_idx)
    return status

# ローカル実行時のプロセス
def main() -> None:
    # 入力を取得
    sheet_url = 'https://docs.google.com/spreadsheets/d/1muIHw9Rolcjsi4KUW5XE45B0T3-5frBe1ZJK93LN9ZY/edit?usp=sharing'
    target_row_idx = 2
    target_column_idx = 7

    # メインプロセスを実行
    status = main_process(sheet_url, target_row_idx, target_column_idx)
    logger.info(log.format('終了ステータス', status))

if __name__ == "__main__":
    main()