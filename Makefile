.PHONY: setup test test-fail lint up down smoke

setup:
	pip install -r requirements-dev.txt
	test -f .env || cp .env.example .env

lint:
	ruff check .

test:
	pytest --cov=app --cov-report=term-missing

test-fail:
	DEMO_FAIL=1 pytest

up:
	docker compose up -d --build

down:
	docker compose down

smoke:
	scripts/smoke.sh
