from logging import DEBUG, INFO
import extract_boolean, extract_data, extract_option
import io_handler, scrape, summarize, log
import functions_framework

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# メインプロセス
@functions_framework.http
def main(request) -> None:
    # 入力を取得
    request_json = request.get_json()
    sheet_url = request_json['sheet_url']
    target_row_idx = int(request_json['row'])
    target_column_idx = int(request_json['column'])
    logger.debug(log.format('入力情報', 'ターゲット行:{}\nスプレッドシートURL:{}'.format(target_row_idx, sheet_url)))

    # マスタ情報を取得
    master_items = io_handler.get_master_items(sheet_url)
    if master_items == None: return 'マスタ情報の取得失敗'
    logger.debug(log.format('マスタ情報', master_items))

    # 商品情報を取得
    product = io_handler.get_product(sheet_url, target_row_idx)
    if product == None: return '商品情報の取得失敗'
    logger.debug(log.format('商品情報', product))

    # URLからページの全文を取得
    full_text = scrape.scrape_all_text(url = product['reference_url'], input_text=None)
    if full_text == None: return '参照URLへのアクセス失敗'
    logger.debug(log.format('Webページから取得した全文', full_text))
    
    # 全文から要約文を取得
    summarize_text = summarize.summarize(input_text = full_text)
    logger.debug(log.format('要約文', summarize_text))

    # 要約文を分割
    split_inputs = summarize.split_input(input_text = summarize_text)

    # 要約文から各項目を抽出
    answers = dict()
    answers['data'] = extract_data.extract(split_inputs = split_inputs, product_name = product['name'], items = master_items['data'])
    logger.debug(log.format('データ項目の抽出結果', answers['data']))
    answers['boolean'] = extract_boolean.extract(split_inputs = split_inputs, product_name = product['name'], items = master_items['boolean'])
    logger.debug(log.format('Boolean項目の抽出結果', answers['boolean']))
    answers['option'] = extract_option.extract(split_inputs = split_inputs, product_name = product['name'], items = master_items['option'])
    logger.debug(log.format('複数選択項目の抽出結果', answers['option']))

    # 各回答を出力
    status = io_handler.output_answers(sheet_url, target_row_idx, target_column_idx, answers)
    if status == 'error': return 'スプレッドシートへの書き込み失敗'   
    
    # 正常終了
    return '実行終了'