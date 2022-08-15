default: build

build:
	VERBOSE="${VERBOSE}" PRETTY="${PRETTY}" ./scripts/build.sh
.PHONY: build

up: pre_run
	docker-compose up -d
.PHONY: up

down:
	docker-compose stop
	docker-compose down
.PHONY: down

logs:
	docker-compose logs -f
.PHONY: logs

pre_run:
	rm -rf ./.data_backup
	docker-compose kill >/dev/null 2>&1
	docker-compose down >/dev/null 2>&1
.PHONY: pre_run

run: build pre_run
	docker-compose up
	docker-compose down
.PHONY: run
