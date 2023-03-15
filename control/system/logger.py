import logging

LOGGER_FILDER = "/var/log/tornado/"
LOGGER_NAME = "tornado"

class Logger:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(levelname)1.1s %(asctime)s %(filename)s %(module)s:%(lineno)d] %(message)s',
            datefmt='%Y%m%d %H:%M:%S')

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        fh = logging.FileHandler(LOGGER_FILDER+LOGGER_NAME+".log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)
