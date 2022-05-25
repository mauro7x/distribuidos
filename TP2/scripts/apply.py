#!/usr/bin/python3

import os
import shutil
import json
import argparse

# Constants

# Generated output
GENERATED_DIRPATH = './.temp'

# Docker compose
DOCKER_COMPOSE_VERSION = 3
IMAGE_TAG = 'latest'

# Names
BROKER_NAME = 'broker'
CLIENT_NAME = 'client'

# Filenames
FILTERS_CONFIG_FILENAME = 'filters.json'
SCALE_CONFIG_FILENAME = 'scale.json'
COMMON_CONFIG_FILENAME = 'common.json'
INGESTION_CONFIG_FILENAME = 'ingestion.json'
SINK_CONFIG_FILENAME = 'sink.json'

# Mounting dirpaths
CONFIG_MOUNTING_DIRPATH = '/config'
DATA_MOUNTING_DIRPATH = '/data'
OUT_MOUNTING_DIRPATH = '/out'

# Defaults
DEFAULT_CONFIG_DIRPATH = './config'
DEFAULT_DATA_DIRPATH = './data'

# Config
SERVICES_CONFIG_DIRNAME = '.services'
CLIENT_CONFIG_DIRNAME = '.client'
OUT_CONFIG_DIRNAME = '.out'
BASE_FILTER_CONFIG_NAME = 'filter'
MIDDLEWARE_CONFIG_NAME = 'middleware'
COMMON_CONFIG_NAME = 'common'

# Hash seed
HASH_SEED_KEY = 'PYTHONHASHSEED'
HASH_SEED_VALUE = 42

# Other
LOGGING_LEVEL_ENV_KEY = 'LOG_LEVEL'


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
                        help='path to config directory '
                        f'(default: {DEFAULT_CONFIG_DIRPATH})')
    parser.add_argument('-d', '--data-dirpath', dest='data_dirpath',
                        type=str, required=False,
                        default=DEFAULT_DATA_DIRPATH,
                        help='path to data directory '
                        f'(default: {DEFAULT_DATA_DIRPATH})')
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
        self.log_level = os.getenv(LOGGING_LEVEL_ENV_KEY)

        # Init temp directory
        shutil.rmtree(GENERATED_DIRPATH, ignore_errors=True)
        os.makedirs(GENERATED_DIRPATH)

        # Nested temp directories
        self.svc_config_dirpath = \
            f'{GENERATED_DIRPATH}/{SERVICES_CONFIG_DIRNAME}'
        self.client_config_dirpath = \
            f'{GENERATED_DIRPATH}/{CLIENT_CONFIG_DIRNAME}'
        self.out_dirpath = \
            f'{GENERATED_DIRPATH}/{OUT_CONFIG_DIRNAME}'
        os.makedirs(self.svc_config_dirpath)
        os.makedirs(self.client_config_dirpath)
        os.makedirs(self.out_dirpath)

        # Config files
        self.config_dirpath = args.config_dirpath
        filters = read_json(
            f'{self.config_dirpath}/{FILTERS_CONFIG_FILENAME}')
        scale = read_json(f'{self.config_dirpath}/{SCALE_CONFIG_FILENAME}')
        common_config = read_json(
            f'{self.config_dirpath}/{COMMON_CONFIG_FILENAME}')
        self.filters = filters
        self.scale = scale
        self.common_config = common_config

        # Input data
        self.data_dirpath = args.data_dirpath

        # docker-compose file to write
        self.definition = []

        # Format: (service, filename, content)
        # e.g.: ('ingestion', 'server', { 'port': 3000 })
        self.svc_config_files = []

        # Cache
        self.sources = {}

    def generate(self):
        self.write(f'version: \'{DOCKER_COMPOSE_VERSION}\'\n')
        self.write('services:')
        self.add_client()

        for svc_name, svc_definition in self.filters.items():
            if svc_definition.get('unique'):
                self.add_single_svc(svc_name, svc_definition)
            else:
                count = self.scale[svc_name]
                assert(count > 0)

                if count == 1:
                    self.add_single_svc(svc_name, svc_definition)
                elif count > 1:
                    self.add_svc_group(svc_name, svc_definition, count)

            self.write('')

        # Remove extra \n
        self.pop()

    def flush(self):
        for service, filename, content in self.svc_config_files:
            json_content = json.dumps(content, indent=2)
            dirpath = f'{self.svc_config_dirpath}/{service}'
            filepath = f'{dirpath}/{filename}.json'
            os.makedirs(dirpath, exist_ok=True)
            with open(filepath, 'w') as file:
                file.write(json_content)

        print(str(self))

    def __str__(self):
        return '\n'.join(self.definition)

    # Common helpers

    def write(self, data, tabs=0):
        tabs = ''.join([DockerComposeGenerator.TAB for _ in range(tabs)])
        result = tabs + data
        self.definition.append(result)

    def pop(self):
        self.definition.pop()

    # Sources
    def get_svc_sources(self, name, svc_name):
        if name in self.sources:
            return self.sources[name]

        count = self.scale.get(svc_name, 1)
        if count > 1 and name == svc_name:  # has broker
            self.sources[name] = 1
            return 1

        if self.filters[svc_name].get('entrypoint'):
            self.sources[name] = 1
            return 1

        sources = 0
        for src_name, src_definition in self.filters.items():
            outputs = src_definition['outputs']
            is_source = any(
                [output.get('to') == svc_name for output in outputs])
            if not is_source:
                continue

            if src_definition.get('unique'):
                sources += 1
                continue

            workers = self.scale[src_name]
            sources += workers

        self.sources[name] = sources
        return sources

    def get_client_sources(self):
        sources = 0
        for src_name, src_definition in self.filters.items():
            outputs = src_definition['outputs']
            is_source = any(
                [bool(output.get('sink', False)) for output in outputs])
            if not is_source:
                continue

            if src_definition.get('unique'):
                sources += 1
                continue

            workers = self.scale[src_name]
            sources += workers

        return sources

    # File helpers

    def add_svc_file(self, svc_name, filename, content):
        self.svc_config_files.append((svc_name, filename, content))

    def add_common_config_file(self, name, svc_name=None):
        if not svc_name:
            svc_name = name

        common = self.common_config.copy()
        common['sources'] = self.get_svc_sources(name, svc_name)
        self.add_svc_file(name, COMMON_CONFIG_NAME, common)

    def add_broker_middleware_file(self, name, definition, svc_name, count):
        middleware = {
            'base_hostname': svc_name,
            'count': count,
            'inputs': definition['inputs']
        }

        self.add_svc_file(name, MIDDLEWARE_CONFIG_NAME, middleware)

    def add_svc_middleware_file(self, name, definition):
        middleware = {
            'inputs': definition['inputs'],
            'outputs': []
        }

        for output_msg in definition['outputs']:
            if output_msg.get('sink'):
                output = {
                    'to': CLIENT_NAME,
                    'data': output_msg['data']
                }
                msg_idx = output_msg.get('msg_idx')
                if msg_idx is not None:
                    output['msg_idx'] = msg_idx
            else:
                to = output_msg['to']
                msg_id = output_msg['msg_id']
                msg_idx, data = find_by_msg_id(
                    self.filters[to]['inputs'], msg_id)
                output = {
                    'to': to,
                    'msg_idx': msg_idx,
                    'data': data
                }

            middleware['outputs'].append(output)

        self.add_svc_file(name, MIDDLEWARE_CONFIG_NAME, middleware)

    # Definitions

    def add_client_definition(self):
        log_level = self.log_level if self.log_level else 'info'
        self.write(f'{CLIENT_NAME}:', 1)
        self.add_image(CLIENT_NAME)
        self.add_container_name(CLIENT_NAME)
        self.add_env_vars(log_level)
        self.write('volumes:', 2)
        self.write(
            f'- {self.data_dirpath}:{DATA_MOUNTING_DIRPATH}:ro', 3)
        self.write(
            f'- {self.client_config_dirpath}:{CONFIG_MOUNTING_DIRPATH}:ro', 3)
        self.write(
            f'- {self.out_dirpath}:{OUT_MOUNTING_DIRPATH}:rw', 3)
        self.write('')

    def add_svc_definition(self, name, definition, i=None):
        name_suffix = f'_{i}' if i else ''
        self.write(f'{name}{name_suffix}:', 1)

        if 'config' in definition:
            config = definition['config']
            self.add_svc_file(name, BASE_FILTER_CONFIG_NAME, config)

        self.add_image(name)
        self.add_container_name(name, i)
        self.mount_config_volume(name)
        self.add_svc_env_vars(definition)

    # Docker compose sections

    def mount_config_volume(self, name):
        svc_config_dirpath = f'{self.svc_config_dirpath}/{name}'
        self.write('volumes:', 2)
        self.write(f'- {svc_config_dirpath}:{CONFIG_MOUNTING_DIRPATH}:ro', 3)

    def add_image(self, image):
        formatted_image = f'{self.prefix}{image}:{IMAGE_TAG}'
        self.write(f'image: {formatted_image}', 2)

    def add_container_name(self, name, i=None):
        suffix = f'_{i}' if i else ''
        container_name = f'{self.prefix}{name}{suffix}'
        self.write(f'container_name: {container_name}', 2)

    def add_svc_env_vars(self, definition):
        log_level = definition.get('log_level', self.log_level)
        self.add_env_vars(log_level)

    def add_env_vars(self, log_level):
        self.write('environment:', 2)
        self.write(f'- {HASH_SEED_KEY}={HASH_SEED_VALUE}', 3)

        if log_level:
            self.write(
                f'- {LOGGING_LEVEL_ENV_KEY}={log_level.upper()}', 3)

    # Service wrappers

    def add_client_files(self):
        # Common config
        shutil.copyfile(
            f'{self.config_dirpath}/{COMMON_CONFIG_FILENAME}',
            f'{self.client_config_dirpath}/{COMMON_CONFIG_FILENAME}'
        )

        # Ingestion config
        shutil.copyfile(
            f'{self.config_dirpath}/{INGESTION_CONFIG_FILENAME}',
            f'{self.client_config_dirpath}/{INGESTION_CONFIG_FILENAME}'
        )

        # Sink config
        sink = {
            "sources": self.get_client_sources()
        }
        json_content = json.dumps(sink, indent=2)
        sink_filepath = f'{self.client_config_dirpath}/{SINK_CONFIG_FILENAME}'
        with open(sink_filepath, 'w') as file:
            file.write(json_content)

    def add_client(self):
        self.add_client_definition()
        self.add_client_files()

    def add_group_broker(self, svc_name, definition, count):
        # Transparet behaviour to the outside: reachable at svc_name
        self.write(f'{svc_name}:', 1)

        name = f'{svc_name}_{BROKER_NAME}'
        self.add_image(BROKER_NAME)
        self.add_container_name(name)
        self.mount_config_volume(name)
        self.add_svc_env_vars(definition)
        self.add_broker_middleware_file(name, definition, svc_name, count)
        self.add_common_config_file(name, svc_name)

    def add_svc_group(self, name, definition, count):
        self.add_group_broker(name, definition, count)

        self.add_svc_middleware_file(name, definition)
        self.add_common_config_file(name)
        for i in range(1, count + 1):
            self.write('')
            self.add_svc_definition(name, definition, i)

    def add_single_svc(self, name, definition):
        self.add_svc_middleware_file(name, definition)
        self.add_common_config_file(name)
        self.add_svc_definition(name, definition)


# Main execution

def main():
    file = DockerComposeGenerator()
    file.generate()
    file.flush()


if __name__ == "__main__":
    main()
