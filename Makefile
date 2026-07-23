PYTHON := python3.11
VENV := .venv
BIN := $(VENV)/bin
STAMP := $(VENV)/.installed

.DEFAULT_GOAL := install

.PHONY: install lint test run clean

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)

$(STAMP): $(BIN)/python pyproject.toml
	$(BIN)/pip install .
	touch $(STAMP)

install: $(STAMP)

lint: install
	$(BIN)/ruff check .

test: install
	$(BIN)/pytest

run: install
	$(BIN)/uvicorn main:app --reload

clean:
	rm -rf $(VENV) build *.egg-info .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
