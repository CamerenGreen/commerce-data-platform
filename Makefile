.PHONY: up down reset seed test lint logs

up:
	docker compose up --build -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build -d

seed:
	python scripts/seed.py

test:
	pytest -q

lint:
	ruff check .

logs:
	docker compose logs -f api

