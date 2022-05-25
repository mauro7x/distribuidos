SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	VERBOSE="${VERBOSE}" ./scripts/build.sh
.PHONY: build

apply:
	LOG_LEVEL="${LOG_LEVEL}" python3 ./scripts/apply.py \
		-p "tp2_" \
		-c config \
		> docker-compose.yaml
.PHONY: apply

up:
	docker-compose up -d
.PHONY: up

down:
	docker-compose kill
	docker-compose down
.PHONY: down

logs:
	docker-compose logs
.PHONY: logs

run: down
	docker-compose up
	docker-compose down
.PHONY: run

clean:
	rm -rf ./.temp
	rm -rf ./docker-compose.yaml
	docker images --format '{{.Repository}}' | grep tp2_ | xargs docker rmi
.PHONY: clean
