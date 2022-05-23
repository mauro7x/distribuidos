SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	VERBOSE="${VERBOSE}" ./scripts/build.sh
.PHONY: build

build-client:
	docker build \
        -t tp2_client:latest \
        -f ./Dockerfile \
        --build-arg MAIN_PATH=src/client.py \
        --build-arg COMMON_PATH=src/common \
        .
.PHONY: build-client

apply:
	LOG_LEVEL="${LOG_LEVEL}" python3 ./scripts/apply.py \
		-c ./config \
		-p "tp2_" \
		> docker-compose.yaml
.PHONY: apply

up:
	docker-compose up -d
.PHONY: up

down:
	# docker-compose stop
	docker-compose kill
	docker-compose down
.PHONY: down

logs:
	docker-compose logs -f
.PHONY: logs

run: build apply
	docker-compose up
	docker-compose down
.PHONY: run

clean:
	rm -rf ./config/.services
	rm -rf ./docker-compose.yaml
	docker images --format '{{.Repository}}' | grep tp2_ | xargs docker rmi
.PHONY: clean
