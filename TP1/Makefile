SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	docker build -t "tp1_server:latest" ./services/server
	docker build -t "tp1_client:latest" ./services/client
	docker build -t "tp1_app:latest" ./services/app
.PHONY: build

up:
	docker-compose up -d
.PHONY: up

down:
	docker-compose stop
	docker-compose down
.PHONY: down

logs:
	docker-compose logs -f
.PHONY: logs

cargo-check:
	./scripts/run_for_services.sh "cargo check --color always"
.PHONY: cargo-check

cargo-clippy:
	./scripts/run_for_services.sh "cargo clippy --color always -- -D warnings"
.PHONY: cargo-clippy

cargo-fmt:
	./scripts/run_for_services.sh "cargo fmt --check"
.PHONY: cargo-fmt

cargo-clean:
	./scripts/run_for_services.sh cargo clean
.PHONY: cargo-clean

lint: cargo-check cargo-clippy cargo-fmt
.PHONY: lint
