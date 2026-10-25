.PHONY: install install-dev run test coverage lint type format quality init-db docker-up clean

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

run:
	flask --app app run --debug

test:
	pytest

coverage:
	pytest --cov=app --cov=detector --cov-report=term-missing --cov-fail-under=70

lint:
	ruff check app.py detector.py tests

type:
	mypy detector.py

format:
	ruff format app.py detector.py tests

quality: lint type coverage

init-db:
	flask --app app init-db

docker-up:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f emergency.db .coverage coverage.xml
