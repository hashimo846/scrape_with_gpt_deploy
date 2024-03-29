from logging import getLogger, StreamHandler, Formatter, Logger


def init(name: str, level: int) -> Logger:
    """ ロガーの初期化 """
    logger = getLogger(name)
    formatter = Formatter('#%(levelname)s:%(message)s')
    streamhandler = StreamHandler()
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)
    logger.setLevel(level)
    return logger


def format(title: str, content: str = '') -> str:
    """ ログ出力のフォーマット """
    message = '【{}】'.format(title)
    if content is not None:
        message += str(content)
    return message
