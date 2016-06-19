import logging
import logging.handlers
from datetime import datetime

import pytz

DATE_FORMAT = '%Y/%m/%d %I:%M:%S %p'


def get_logger(name: str):

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    file = logging.handlers.RotatingFileHandler(
              '/var/log/home/' + name + '.log', maxBytes=1 * 1024 * 1024, backupCount=3)
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

    return logger


def converter(timestamp):
    local_time = datetime.fromtimestamp(timestamp, tz=pytz.timezone('America/Los_Angeles'))
    return local_time.timetuple()
