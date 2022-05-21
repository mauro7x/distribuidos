SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	VERBOSE="${VERBOSE}" ./scripts/build.sh
.PHONY: build

apply:
	python3 ./scripts/apply.py -c ./config -p "tp2_" > docker-compose.yaml
.PHONY: apply

up: apply
	docker-compose up -d
.PHONY: up

down:
	docker-compose stop
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
