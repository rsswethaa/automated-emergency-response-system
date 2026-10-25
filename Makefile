.PHONY: install run test init-db clean

install:
	python -m pip install -r requirements.txt

run:
	flask --app app run --debug

test:
	python -m unittest discover -s tests -v

init-db:
	flask --app app init-db

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f emergency.db
