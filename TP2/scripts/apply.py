#!/usr/bin/python3

import json
import argparse

# Constants

DOCKER_COMPOSE_VERSION = 3
PREFIX = 'tp2_'
IMAGE_TAG = 'latest'
BROKER_IMAGE = 'broker'

# File wrapper


class BufferedFile:
    TAB = '  '

    def __init__(self):
        self.buffer = []

    def write(self, data, tabs=0):
        result = ''.join([BufferedFile.TAB for _ in range(tabs)]
                         ) + data
        self.buffer.append(result)

    def pop(self):
        self.buffer.pop()

    def flush(self):
        print(self)

    def __str__(self):
        return '\n'.join(self.buffer)


# Helpers


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate needed configuration for running the system.')
    parser.add_argument('-p', dest='pipeline', type=str, required=True,
                        help='path to pipeline definition file (JSON)')
    parser.add_argument('-s', dest='scale', type=str,
                        required=True, help='path to scaling definition file (JSON)')
    args = parser.parse_args()

    return args


def read_json(filepath):
    with open(filepath) as file:
        data = json.load(file)
    return data


def write_image(file, image):
    formatted_image = f'{PREFIX}{image}:{IMAGE_TAG}'
    file.write(f'image: {formatted_image}', 2)


def write_container_name(file, name, i=None):
    suffix = f'_{i}' if i else ''
    container_name = f'{PREFIX}{name}{suffix}'
    file.write(f'container_name: {container_name}', 2)


def write_svc_definition(file, pipeline, name, definition, i=None):
    if 'base' in definition:
        base_image = definition['base']['image']
        base_config = definition['base']['config']
        write_image(file, base_image)
    else:
        write_image(file, name)

    write_container_name(file, name, i)


def write_group_broker(file, pipeline, name, definition):
    file.write(f'{name}:', 1)
    write_image(file, BROKER_IMAGE)
    write_container_name(file, name)


def write_svc_group(file, pipeline, name, definition, count):
    write_group_broker(file, pipeline, name, definition)

    for i in range(1, count + 1):
        file.write('')
        file.write(f'{name}_{i}:', 1)
        write_svc_definition(file, pipeline, name, definition, i)


def write_svc(file, pipeline, name, definition, count):
    if count <= 0:
        raise Exception(f'Invalid scale count for service {name}: {count}')

    if count == 1:
        file.write(f'{name}:', 1)
        write_svc_definition(file, pipeline, name, definition)
    else:
        write_svc_group(file, pipeline, name, definition, count)


def write(file, pipeline, scale):
    file.write(f'version: \'{DOCKER_COMPOSE_VERSION}\'\n')
    file.write('services:')

    for svc_name, svc_definition in pipeline.items():
        try:
            count = scale[svc_name]
        except:
            raise Exception(f'Scale number not found for service {svc_name}')

        write_svc(file, pipeline, svc_name, svc_definition, count)
        file.write('')

    # Remove extra \n
    file.pop()


# Main execution


def main():
    args = parse_args()
    pipeline = read_json(args.pipeline)
    scale = read_json(args.scale)
    file = BufferedFile()
    write(file, pipeline, scale)

    file.flush()


if __name__ == "__main__":
    main()
