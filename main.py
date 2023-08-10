from logging import DEBUG, INFO
import extract_boolean, extract_data, extract_option
import io_handler, scrape, summarize, log

# ロガーの初期化
logger = log.init(__name__, DEBUG)

# メインプロセス
def main() -> None:
    # 入力を取得
    target_row_idx = 2
    sheet_url = 'https://docs.google.com/spreadsheets/d/1l5Vo_Yz7Gh_s3M-2tDq-wnWLdAkD0rKylxw9IKYQ7M8/edit?usp=sharing'
    logger.debug(log.format('入力情報', 'ターゲット行:{}\nスプレッドシートURL:{}'.format(target_row_idx, sheet_url)))

    # マスタ情報を取得
    master_items = io_handler.get_master_items(sheet_url)
    if master_items == None: return
    logger.debug(log.format('マスタ情報', master_items))

    # 商品情報を取得
    product = io_handler.get_product(sheet_url, target_row_idx)
    if product == None: return
    logger.debug(log.format('商品情報', product))

    # URLからページの全文を取得
    full_text = scrape.scrape_all_text(url = product['reference_url'], input_text=None)
    logger.debug(log.format('Webページから取得した全文', full_text))
    if full_text == None: return
    
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
    io_handler.output_answers(sheet_url, target_row_idx, answers)
    
if __name__ == '__main__':
    main()