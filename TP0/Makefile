SHELL := /bin/bash
PWD := $(shell pwd)

GIT_REMOTE = github.com/7574-sistemas-distribuidos/docker-compose-init

default: build

all:

deps:
	go mod tidy
	go mod vendor

build: deps
	GOOS=linux go build -o bin/client github.com/7574-sistemas-distribuidos/docker-compose-init/client
.PHONY: build

docker-image:
	docker build -t "server:latest" ./server
	docker build -f ./client/Dockerfile -t "client:latest" .
	# Execute this command from time to time to clean up intermediate stages generated 
	# during client build (your hard drive will like this :) ). Don't left uncommented if you 
	# want to avoid rebuilding client image every time the docker-compose-up command 
	# is executed, even when client code has not changed
	# docker rmi `docker images --filter label=intermediateStageToBeDeleted=true -q`
.PHONY: docker-image

docker-compose-up: docker-image
	docker-compose -f docker-compose-dev.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker-compose -f docker-compose-dev.yaml stop -t 1
	docker-compose -f docker-compose-dev.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker-compose -f docker-compose-dev.yaml logs -f
.PHONY: docker-compose-logs

gen-docker-compose-n-clients:
	docker build -t "n_clients_compose_script:latest" scripts/n_clients_compose
	rm -rf tmp && mkdir tmp
	cp docker-compose.template.yaml ./tmp/input
	docker run -e N_CLIENTS=${N_CLIENTS} -v "$(PWD)"/tmp:/usr/app/src/files -it n_clients_compose_script
	cp ./tmp/output docker-compose-dev.yaml
	rm -rf tmp
.PHONY: gen-docker-compose-n-clients

netcat-test:
	docker build -t "test:latest" ./scripts/test
	docker run -e HOST=server -e PORT=12345 --network=tp0_testing_net test
.PHONY: netcat-test

test: docker-compose-up netcat-test docker-compose-down
.PHONY: test
