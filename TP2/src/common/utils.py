import json
import logging
import os

LOGGING_LEVEL_ENV_KEY = 'LOG_LEVEL'


def read_json(filepath: str):
    with open(filepath) as file:
        data = json.load(file)
    return data


def init_log():
    level_name = os.getenv(LOGGING_LEVEL_ENV_KEY, '')
    level = logging._nameToLevel.get(level_name.upper(), logging.WARNING)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )
