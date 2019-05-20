import logging
import logging.handlers
from datetime import datetime

import pytz
import sys

DATE_FORMAT = '%Y/%m/%d %I:%M:%S %p'


def get_logger(name):

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    file = logging.handlers.RotatingFileHandler(
              '/var/log/home/' + name + '.log', maxBytes=512 * 1024, backupCount=1)
    file.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                       datefmt=DATE_FORMAT)
    file_formatter.converter = converter
    file.setFormatter(file_formatter)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s %(name)-12s: %(message)s',
                                          datefmt=DATE_FORMAT)
    console_formatter.converter = converter
    console.setFormatter(console_formatter)

    logger.addHandler(console)
    logger.addHandler(file)

    # Setup uncaught exception logging
    catch_excep = lambda typ, value, traceback: _handle_exception(logger, typ, value, traceback)
    sys.excepthook = catch_excep

    return logger


def converter(timestamp):
    local_time = datetime.fromtimestamp(timestamp, tz=pytz.timezone('America/Los_Angeles'))
    return local_time.timetuple()


def _handle_exception(logger, exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
