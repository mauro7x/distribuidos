#!/usr/bin/env python3
import json

COMMENTS_FILE = "comments.csv"
POSTS_FILE = "posts.csv"

PYTHONHASHSEED = 1

PIPELINE_CONFIG_PATH = "../config/pipeline.json"
CLIENT_CONFIG_PATH = "../config/client.json"
MONITOR_CONFIG_PATH = "../config/monitor.json"
DOCKER_COMPOSE_PATH = "../docker-compose.yaml"

DOCKER_COMPOSE_BASE = """# Generated automatically by generate_docker_compose.py

version: '3'
services:
  rabbitmq:
    container_name: rabbitmq
    image: rabbitmq:latest
    ports:
      - 15672:15672
    networks:
      - tp3-distribuidos-net

  <MONITORS>
  <CLIENTS>
  <INGESTOR>
  <POST_FILTERS>
  <COMMENT_FILTERS>
  <CALCULATOR_POST_AVG_SCORE>
  <JOINERS>
  <CALCULATORS_AVG_SENTIMENT_BY_POST>
  <POST_MAX_AVG_SENTIMENT_FILTER>
  <STUDENT_LIKED_POSTS_FILTER>

networks:
  tp3-distribuidos-net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

MONITOR = """
  monitor_%d:
    container_name: monitor_%d
    image: monitor:latest
    environment:
      - PYTHONUNBUFFERED=1
      - ENTITY_NAME=monitor
      - ENTITY_SUB_ID=%d
    volumes:
      - ./config/monitor.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - tp3-distribuidos-net
"""

CLIENT = """
  client_%d:
    container_name: client_%d
    image: client:latest
    entrypoint: python3 /client.py
    environment:
      - PYTHONUNBUFFERED=1
      - ENTITY_NAME=client
    volumes:
      - ./data/%s:/comments.csv
      - ./data/%s:/posts.csv
      - ./config/pipeline_entity.json:/config.json
      - ./results/:/results/
    depends_on:
      - rabbitmq
      - ingestor
    networks:
      - tp3-distribuidos-net
"""

INGESTOR = """
  ingestor:
    container_name: ingestor
    image: ingestor:latest
    environment:
      - PYTHONUNBUFFERED=1
      - ENTITY_NAME=ingestor
      - PYTHONHASHSEED=%d
    volumes:
      - ./data/%s:/comments.csv
      - ./data/%s:/posts.csv
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

POST_FILTER = """
  filter_posts_%d:
    container_name: filter_posts_%d
    image: filter_posts:latest
    environment:
      - ENTITY_NAME=filter_posts
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

COMMENT_FILTER = """
  filter_comments_%d:
    container_name: filter_comments_%d
    image: filter_comments:latest
    environment:
      - ENTITY_NAME=filter_comments
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

CALCULATOR_POST_AVG_SCORE = """
  calculator_post_avg_score:
    container_name: calculator_post_avg_score
    image: calculator_post_avg_score:latest
    environment:
      - ENTITY_NAME=calculator_post_avg_score
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

JOINER = """
  joiner_%d:
    container_name: joiner_%d
    image: joiner_post_comment_by_id:latest
    environment:
      - ENTITY_NAME=joiner
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

CALCULATOR_AVG_SENTIMENT_BY_POST = """
  calculator_avg_sentiment_by_post_%d:
    container_name: calculator_avg_sentiment_by_post_%d
    image: calculator_avg_sentiment_by_post:latest
    environment:
      - ENTITY_NAME=calculator_avg_sentiment_by_post
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

POST_MAX_AVG_SENTIMENT_FILTER = """
  filter_post_max_avg_sentiment:
    container_name: filter_post_max_avg_sentiment
    image: filter_post_max_avg_sentiment:latest
    environment:
      - ENTITY_NAME=filter_post_max_avg_sentiment
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""

STUDENT_LIKED_POSTS_FILTER = """
  filter_student_liked_posts_%d:
    container_name: filter_student_liked_posts_%d
    image: filter_student_liked_posts:latest
    environment:
      - ENTITY_NAME=filter_student_liked_posts
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/pipeline_entity.json:/config.json
      - ./config/pipeline.json:/pipeline.json
      - ./.data_backup/:/.data_backup/
    depends_on:
      - rabbitmq
    networks:
      - tp3-distribuidos-net
"""


def load_json(path):
    with open(path, 'r') as file:
        return json.load(file)


def generate_compose():
    pipeline_config = load_json(PIPELINE_CONFIG_PATH)
    monitor_config = load_json(MONITOR_CONFIG_PATH)
    client_config = load_json(CLIENT_CONFIG_PATH)

    n_post_filters = pipeline_config["filter_posts"]["scale"]

    post_filters = ""
    for i in range(n_post_filters):
        post_filters += POST_FILTER % (
            i, i, i, PYTHONHASHSEED)

    n_comment_filters = pipeline_config["filter_comments"]["scale"]

    comment_filters = ""
    for i in range(n_comment_filters):
        post_filters += COMMENT_FILTER % (
            i, i, i, PYTHONHASHSEED)

    calculator_post_avg_score = CALCULATOR_POST_AVG_SCORE % (PYTHONHASHSEED)

    n_joiners = pipeline_config["joiner"]["scale"]

    joiners = ""
    for i in range(n_joiners):
        joiners += JOINER % (i, i, i, PYTHONHASHSEED)

    n_calculators_avg_sentiment_by_post = pipeline_config[
        "calculator_avg_sentiment_by_post"]["scale"]

    calculators_avg_sentiment_by_post = ""
    for i in range(n_calculators_avg_sentiment_by_post):
        calculator_post_avg_score += CALCULATOR_AVG_SENTIMENT_BY_POST % (
            i, i, i, PYTHONHASHSEED)

    filter_post_max_avg_sentiment = POST_MAX_AVG_SENTIMENT_FILTER % (
        PYTHONHASHSEED)

    n_filters_student_liked_posts = pipeline_config["filter_student_liked_posts"]["scale"]

    filters_student_liked_posts = ''
    for i in range(n_filters_student_liked_posts):
        filters_student_liked_posts += STUDENT_LIKED_POSTS_FILTER % (
            i, i, i, PYTHONHASHSEED)

    ingestor = INGESTOR % (PYTHONHASHSEED, COMMENTS_FILE, POSTS_FILE)

    n_monitors = monitor_config["replicas"]
    monitors = ""
    for i in range(n_monitors):
        monitors += MONITOR % (i, i, i)

    n_clients = client_config["replicas"]
    clients = ""
    for i in range(n_clients):
        clients += CLIENT % (i, i, COMMENTS_FILE, POSTS_FILE)

    docker_compose = DOCKER_COMPOSE_BASE \
        .replace("<MONITORS>", monitors) \
        .replace("<CLIENTS>", clients) \
        .replace("<INGESTOR>", ingestor) \
        .replace("<POST_FILTERS>", post_filters) \
        .replace("<COMMENT_FILTERS>", comment_filters) \
        .replace("<CALCULATOR_POST_AVG_SCORE>", calculator_post_avg_score) \
        .replace("<JOINERS>", joiners) \
        .replace("<CALCULATORS_AVG_SENTIMENT_BY_POST>", calculators_avg_sentiment_by_post) \
        .replace("<POST_MAX_AVG_SENTIMENT_FILTER>", filter_post_max_avg_sentiment) \
        .replace("<STUDENT_LIKED_POSTS_FILTER>", filters_student_liked_posts)

    with open(DOCKER_COMPOSE_PATH, "w") as file:
        file.write(docker_compose)


def main():
    print("Generating docker-compose.yaml...")
    generate_compose()
    print("Docker compose generated successfully!")


if __name__ == "__main__":
    main()
