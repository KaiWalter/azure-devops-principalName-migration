# logging

import logging

LOG_FILENAME = 'migration.log'

def printInfo(message: str):
    print(message)
    logging.info(message)


def printWarning(message: str):
    print(message)
    logging.warning(message)


def printException(message: str):
    logging.exception(message)
    raise Exception(message)
