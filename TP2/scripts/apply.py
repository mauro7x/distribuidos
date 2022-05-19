#!/usr/bin/python3

import os
import shutil
import json
import argparse

# Constants

DOCKER_COMPOSE_VERSION = 3
IMAGE_TAG = 'latest'
BROKER_NAME = 'broker'
DEFAULT_CONFIG_DIRPATH = './config'
PIPELINE_CONFIG_FILENAME = 'pipeline.json'
SCALE_CONFIG_FILENAME = 'scale.json'
COMMON_CONFIG_FILENAME = 'common.json'
CONFIG_MOUNTING_DIRPATH = '/config'
SERVICES_CONFIG_DIRNAME = '.services'
BASE_FILTER_CONFIG_NAME = 'filter'
MIDDLEWARE_CONFIG_NAME = 'middleware'

# Auxiliar functions


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate needed configuration for running the system.')
    parser.add_argument('-p', '--prefix', dest='prefix',
                        type=str, required=True,
                        help='prefix to apply to every image and container')
    parser.add_argument('-c', '--config-dirpath', dest='config_dirpath',
                        type=str, required=False,
                        default=DEFAULT_CONFIG_DIRPATH,
                        help='path to config directory (default: ./config)')
    args = parser.parse_args()

    return args


def read_json(filepath):
    with open(filepath) as file:
        data = json.load(file)
    return data


def find_by_msg_id(msgs, msg_id):
    idx, msg = list(
        filter(lambda x: x[1]['id'] == msg_id, enumerate(msgs)))[0]
    return idx, msg['data']

# Docker Compose generator class


class DockerComposeGenerator:
    TAB = '  '

    def __init__(self):
        args = parse_args()
        self.prefix = args.prefix

        # Config files
        pipeline = read_json(
            f'{args.config_dirpath}/{PIPELINE_CONFIG_FILENAME}')
        scale = read_json(f'{args.config_dirpath}/{SCALE_CONFIG_FILENAME}')
        common_config = read_json(
            f'{args.config_dirpath}/{COMMON_CONFIG_FILENAME}')
        self.pipeline = pipeline
        self.scale = scale
        self.common_config = common_config

        # Services config directory
        config_dirpath = f'{args.config_dirpath}/{SERVICES_CONFIG_DIRNAME}'
        shutil.rmtree(config_dirpath, ignore_errors=True)
        os.makedirs(config_dirpath)
        self.config_dirpath = config_dirpath

        # docker-compose file to write
        self.definition = []

        # Format: (service, filename, content)
        # e.g.: ('ingestion', 'server', { 'port': 3000 })
        self.svc_config_files = []

    def write(self, data, tabs=0):
        tabs = ''.join([DockerComposeGenerator.TAB for _ in range(tabs)])
        result = tabs + data
        self.definition.append(result)

    def pop(self):
        self.definition.pop()

    def flush(self):
        for service, filename, content in self.svc_config_files:
            json_content = json.dumps(content, indent=2)
            dirpath = f'{self.config_dirpath}/{service}'
            filepath = f'{dirpath}/{filename}.json'
            os.makedirs(dirpath, exist_ok=True)
            with open(filepath, 'w') as file:
                file.write(json_content)

        print(self)

    def __str__(self):
        return '\n'.join(self.definition)

    # Helpers

    def add_svc_file(self, svc_name, filename, content):
        self.svc_config_files.append((svc_name, filename, content))

    def add_broker_middleware_file(self, name, definition, count):
        middleware = {
            'common': self.common_config,
            'count': count
        }

        if 'affinity_key' in definition:
            middleware['input'] = definition['input']
            middleware['affinity_key'] = definition['affinity_key']

        self.add_svc_file(name, MIDDLEWARE_CONFIG_NAME, middleware)

    def add_svc_middleware_file(self, name, definition):
        middleware = {
            'common': self.common_config,
            'input': definition['input'],
            'output': []
        }

        for output_msg in definition['output']:
            to = output_msg['to']
            msg_id = output_msg['msg_id']
            msg_idx, data = find_by_msg_id(
                self.pipeline[to]['input'], msg_id)
            middleware['output'].append(
                {'to': to, 'msg_idx': msg_idx, 'data': data})

        self.add_svc_file(name, MIDDLEWARE_CONFIG_NAME, middleware)

    def mount_config_volume(self, name):
        svc_config_dirpath = f'{self.config_dirpath}/{name}'
        self.write('volumes:', 2)
        self.write(f'- {svc_config_dirpath}:{CONFIG_MOUNTING_DIRPATH}:ro', 3)

    def add_image(self, image):
        formatted_image = f'{self.prefix}{image}:{IMAGE_TAG}'
        self.write(f'image: {formatted_image}', 2)

    def add_container_name(self, name, i=None):
        suffix = f'_{i}' if i else ''
        container_name = f'{self.prefix}{name}{suffix}'
        self.write(f'container_name: {container_name}', 2)

    def add_group_broker(self, svc_name, definition, count):
        # Transparet behaviour to the outside: reachable at svc_name
        self.write(f'{svc_name}:', 1)

        name = f'{svc_name}_{BROKER_NAME}'
        self.add_image(BROKER_NAME)
        self.add_container_name(name)
        self.mount_config_volume(name)
        self.add_broker_middleware_file(name, definition, count)

    def add_svc_definition(self, name, definition, i=None):
        name_suffix = f'_{i}' if i else ''
        self.write(f'{name}{name_suffix}:', 1)

        if 'base' in definition:
            base_image = definition['base']['image']
            base_config = definition['base']['config']
            self.add_svc_file(name, BASE_FILTER_CONFIG_NAME, base_config)
            self.add_image(base_image)
        else:
            self.add_image(name)

        self.add_container_name(name, i)
        self.mount_config_volume(name)

    def add_svc_group(self, name, definition, count):
        self.add_group_broker(name, definition, count)

        self.add_svc_middleware_file(name, definition)
        for i in range(1, count + 1):
            self.write('')
            self.add_svc_definition(name, definition, i)

    def add_single_svc(self, name, definition):
        self.add_svc_middleware_file(name, definition)
        self.add_svc_definition(name, definition)

    def generate(self):
        self.write(f'version: \'{DOCKER_COMPOSE_VERSION}\'\n')
        self.write('services:')

        for svc_name, svc_definition in self.pipeline.items():
            count = self.scale[svc_name]
            assert(count > 0)

            if count == 1:
                self.add_single_svc(svc_name, svc_definition)
            elif count > 1:
                self.add_svc_group(svc_name, svc_definition, count)

            self.write('')

        # Remove extra \n
        self.pop()


# Main execution

def main():
    file = DockerComposeGenerator()
    file.generate()
    file.flush()


if __name__ == "__main__":
    main()
