def extract_json(input_text: str) -> str:
    """ 入力文からJSON形式のみ抽出（テキスト中の｛｝の前後を除去） """
    if input_text.find('{') > 0:
        input_text = '{' + '{'.join(input_text.split('{')[1:])
    if input_text[-1] != '}':
        input_text = '}'.join(input_text.split('}')[:-1]) + '}'
    return input_text
