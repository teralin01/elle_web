import logging
from logging import DEBUG, INFO, ERROR, WARN
from sys import stdout

LOGGER_FILDER = "/var/log/tornado/"
LOGGER_NAME = "tornado"

class Logger(logging.Logger):
    def __init__(self):
        logger = logging.getLogger(LOGGER_NAME)
        self.logger = logger  
        
        if not len(logger.handlers):
            logger.propagate = False   
            logger.setLevel(logging.DEBUG)
            logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
            fileHandler = logging.FileHandler("{0}/{1}.log".format(LOGGER_FILDER,LOGGER_NAME ))
            fileHandler.setFormatter(logFormatter)
            logger.addHandler(fileHandler)

            consoleHandler = logging.StreamHandler(stdout)
            consoleHandler.setFormatter(logFormatter)
            logger.addHandler(consoleHandler)
               

    def info(self, msg, extra=None):
        self.logger.info(msg, extra=extra)

    def error(self, msg, extra=None):
        self.logger.error(msg, extra=extra)

    def debug(self, msg, extra=None):
        self.logger.debug(msg, extra=extra)

    def warn(self, msg, extra=None):
        self.logger.warn(msg, extra=extra)        