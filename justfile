# Justfile for Windows and cross-platform use

install:
    poetry install

run-dev:
    poetry run uvicorn main:app --reload
