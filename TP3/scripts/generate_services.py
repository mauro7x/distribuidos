#!/usr/bin/env python3

##################################################################
#                                                                #
# This script automatically generates the services, in .services #
# directory, with all the needed settings and files.             #
#                                                                #
##################################################################

import shutil

SERVICES_DIRECTORY = "../.services"
BASE_ENTITY_STRUCTURE_PATH = "../base/entity"
ENTITIES_BASE_PATH = "../entities"
ENTITY_IMPL_FILENAME = "entity.py"
ENTITY_FILE_CONTAINER_DIR = "common/"

# Relative from docker-compose.yaml
ENTITIES_BASE_PATH_FROM_COMPOSE = "entities"
SERVICES_BASE_PATH_FROM_COMPOSE = ".services"

ENTITY_RELATIVE_PATHS = [
    # (relative_path, entity_name)
    ("ingestor", "ingestor"),
    ("filters", "filter_posts"),
    ("filters", "filter_comments"),
    ("filters", "filter_post_max_avg_sentiment"),
    ("filters", "filter_student_liked_posts"),
    ("calculators", "calculator_post_avg_score"),
    ("calculators", "calculator_avg_sentiment_by_post"),
    ("joiner", "joiner_post_comment_by_id")
]

ENTITY_BASE_DOCKERFILE = """# Generated automaticaly by generate_services.py

FROM rabbitmq-python-base:0.0.1
COPY <ENTITY_PATH_FROM_COMPOSE> /
COPY ./common /common
COPY ./entities/common /common
ENTRYPOINT ["python3", "main.py"]
"""


class EntityParser:
    def __init__(self):
        self._build_commands = []

    def create_file(self, path, content):
        with open(path, "w") as file:
            file.write(content)

    def build_entities(self):
        self.remove_service_directory_if_exists()
        print(f"Building services into directory {SERVICES_DIRECTORY}")

        for (relative_path, entity_name) in ENTITY_RELATIVE_PATHS:
            self.build_service(relative_path, entity_name)

    def remove_service_directory_if_exists(self):
        print(f"Deleting old {SERVICES_DIRECTORY} directory if existent")

        try:
            shutil.rmtree(SERVICES_DIRECTORY,
                          ignore_errors=False, onerror=None)
        except:
            # directory did not exist
            pass

    def build_service(self, relative_path, entity_name):
        print(f"Creating entity {entity_name}...")

        entity_path = f"{SERVICES_DIRECTORY}/{entity_name}"

        # Copiar base entity structure
        shutil.copytree(BASE_ENTITY_STRUCTURE_PATH, entity_path)

        # Copy entity implementation
        src_path = ""
        src_path_from_compose = f"{SERVICES_BASE_PATH_FROM_COMPOSE}/{entity_name}"
        if relative_path != "":
            src_path = f"{ENTITIES_BASE_PATH}/{relative_path}/{entity_name}.py"
        else:
            src_path = f"{ENTITIES_BASE_PATH}/{entity_name}.py"

        dst_path = f"{entity_path}/{ENTITY_FILE_CONTAINER_DIR}/{ENTITY_IMPL_FILENAME}"

        shutil.copy2(src_path, dst_path)

        # Create entity Dockerfile
        entity_dockerfile = ENTITY_BASE_DOCKERFILE.replace(
            "<ENTITY_PATH_FROM_COMPOSE>", src_path_from_compose)

        entity_dockerfile_filename = f"{entity_path}/Dockerfile"
        self.create_file(entity_dockerfile_filename, entity_dockerfile)

        self._build_commands.append(
            f"docker build -f {src_path_from_compose}/Dockerfile -t \"{entity_name}:latest\" .\n	")

        print(f"Entity {entity_name} created successfully!")


def main():
    entity_parser = EntityParser()
    entity_parser.build_entities()


if __name__ == "__main__":
    main()
