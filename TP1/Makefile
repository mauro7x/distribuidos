SHELL := /bin/bash
PWD := $(shell pwd)

default: build

build:
	VERBOSE="${VERBOSE}" ./scripts/build.sh
.PHONY: build

up:
	docker compose up -d --scale app=0 --scale client=0
.PHONY: up

down:
	docker compose stop
	docker compose down
.PHONY: down

logs:
	docker compose logs -f
.PHONY: logs

manual-app:
	docker run -it \
		-e RUST_LOG=debug \
		-e SERVER_HOST=event_writer \
		--network tp1_external_apps \
		--entrypoint target/release/manual \
		tp1_app
.PHONY: manual-app

manual-client:
	docker run -it \
		-e RUST_LOG=debug \
		-e SERVER_HOST=public_aggregator \
		--network tp1_external_clients \
		--entrypoint target/release/manual \
		tp1_client
.PHONY: manual-client

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
