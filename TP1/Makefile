SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	docker build -t "tp1_client:latest" ./services/client
	docker build -t "tp1_app:latest" ./services/app
	docker build -t "tp1_alert_service:latest" ./services/alert_service
	docker build -t "tp1_db_aggregator:latest" ./services/db_aggregator
	docker build -t "tp1_db_event_writer:latest" ./services/db_event_writer
	docker build -t "tp1_event_receiver:latest" ./services/event_receiver
	docker build -t "tp1_logging_service:latest" ./services/logging_service
	docker build -t "tp1_query_receiver:latest" ./services/query_receiver
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
