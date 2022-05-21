import json
import logging


def read_json(filepath):
    with open(filepath) as file:
        data = json.load(file)
    return data


def init_log(logging_level: str = 'INFO'):
    level = logging._nameToLevel.get(logging_level.upper(), logging.WARN)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )
