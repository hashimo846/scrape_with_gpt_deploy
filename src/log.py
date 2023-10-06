from logging import getLogger, StreamHandler, Formatter, Logger, DEBUG, INFO

def init(name:str, level:int) -> Logger:
    # ロガーの初期化
    logger = getLogger(name)
    formatter = Formatter('#%(levelname)s:%(message)s')
    streamhandler = StreamHandler()
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)
    logger.setLevel(DEBUG)
    return logger

def format(title:str, content:any=None) -> str:
    message = '【' + title + '】' + '\n'
    if content is not None:
        message += str(content)
        message += '\n'
    return message