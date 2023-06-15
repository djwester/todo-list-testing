.PHONY: install
install:
	poetry install

.PHONY: run-dev
run-dev:
	poetry run uvicorn main:app --reload
