#!/usr/bin/env python3
import csv
import json
import logging
import os
import socket
import subprocess
import time

import common.cs_protocol
from common.constants import FINISH_PROCESSING_TYPE, STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE, POST_WITH_MAX_AVG_SENTIMENT_TYPE,  POST_AVG_SCORE_TYPE, BATCH_TYPE

BASE_CONFIG_FILE = "config.json"
POSTS_FILE = '/posts.csv'
COMMENTS_FILE = '/comments.csv'

POST_LINE_STARTER = 'post'
COMMENT_LINE_STARTER = 'comment'

RESULTS_FILE_PATH = '/results/results.txt'
IMG_FILE_PATH = '/results/meme_with_highest_avg_sentiment'

RETRY_SERVER_CONNECT_CADENCY = 5

PROGRESS_LOG_PERCENTAGE_STEP = 10

BATCH_SIZE = 200

class Client:

    def __count_lines_approx(self,filename,line_starter:str):
        grep = subprocess.Popen(('grep',line_starter, filename), stdout=subprocess.PIPE)
        output = int(subprocess.check_output(('wc', '-l'), stdin=grep.stdout).split()[0])
        return output

    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.info(f"Connecting to server {host}:{port}")

        connected = False
        self.post_avg_score = None
        self.send_buffer = []

        while not connected:
            try:
                self.s.connect((host, port))
                connected = True
            except:
                logging.warn(
                    f"Could not connect to server: server not ready. Retryin in {RETRY_SERVER_CONNECT_CADENCY} secs")
                time.sleep(RETRY_SERVER_CONNECT_CADENCY)
                continue
        
        logging.info("Connected successfully to server")
    
    def __flush_buffer(self):
        batch = {
            'type': BATCH_TYPE,
            'data': self.send_buffer
        }
        common.cs_protocol.send(self.s, batch)
        self.send_buffer = []

    def __send_row(self, row):
        self.send_buffer.append(row)
        if len(self.send_buffer) >= BATCH_SIZE:
            self.__flush_buffer()

    def __ingest_file(self, filename, line_starter):
        line_count_approx = self.__count_lines_approx(filename, line_starter)

        with open(filename, "r") as file:
            reader = csv.DictReader(file)

            lines_processed = 0
            log_step = int(line_count_approx * (PROGRESS_LOG_PERCENTAGE_STEP / 100))
            for row in reader:

                if lines_processed % log_step == 0:
                    logging.info(f" {lines_processed} / {line_count_approx} "
                    f"({round((lines_processed / line_count_approx) * 100)}%) elements sent.")

                self.__send_row(row)
                lines_processed += 1
            
            # Make sure no element is left in the buffer
            self.__flush_buffer()

        common.cs_protocol.send(self.s, {"type": FINISH_PROCESSING_TYPE})

    def __recv_results(self):
        with open(RESULTS_FILE_PATH, "w") as results_file:
            while True:
                result = common.cs_protocol.recv(self.s)
                if result["type"] == STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE:
                    results_file.write(json.dumps(result))
                    results_file.write("\n")
                    continue

                if result["type"] == POST_AVG_SCORE_TYPE: 
                    logging.debug("Received posts avg score")
                    self.post_avg_score = result["post_avg_score"]

                    results_file.write(json.dumps(result))
                    results_file.write("\n")
                    continue

                if result["type"] == POST_WITH_MAX_AVG_SENTIMENT_TYPE:
                    logging.debug("Received post with max avg sentiment")
                    if not result.get("file_length"):
                        logging.error(
                            "Server could not download post with max avg sentiment image")
                    else:
                        img_bytes = common.cs_protocol.recv_img(self.s)
                        with open("{}{}".format(IMG_FILE_PATH, result["ext"]), "wb") as img_file:
                            img_file.write(img_bytes)

                    results_file.write(json.dumps(result))
                    results_file.write("\n")
                    continue

                if result["type"] == FINISH_PROCESSING_TYPE:
                    break

                logging.error("Unknown result type recved: {}", result)
    
    def __log_results(self, start_time, end_time):
        logging.info(f"########### Results ###########")
        logging.info(f"Time elapsed: {end_time - start_time}")
        logging.info(f"Posts average score: {self.post_avg_score}")

    def run(self):
        start_time = time.time()
        self.__ingest_file(POSTS_FILE, POST_LINE_STARTER)
        self.__ingest_file(COMMENTS_FILE, COMMENT_LINE_STARTER)
        self.__recv_results()
        end_time = time.time()

        self.__log_results(start_time, end_time)

    def stop(self):
        self.s.close()


def parse_base_config():
    base_config = {}

    with open(BASE_CONFIG_FILE, 'r') as base_config_file:
        base_config = json.load(base_config_file)

    base_config["entity_name"] = os.environ["ENTITY_NAME"]
    return base_config


def initialize_log(logging_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging_level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def main():
    base_config = parse_base_config()
    initialize_log(base_config["logging_level"])

    client = Client(base_config["server_config"]["host"], int(
        base_config["server_config"]["port"]))
    
    try:
        client.run()
        client.stop()
    except:
        logging.error("Unexpected error. Exiting")


if __name__ == "__main__":
    main()
