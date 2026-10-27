PYTHON := .venv/bin/python

.PHONY: setup validate generate verify test all

setup:
	bash setup.sh

validate:
	$(PYTHON) validate_data.py

generate: validate
	$(PYTHON) generate.py

verify:
	$(PYTHON) verify_ats.py

test:
	$(PYTHON) -m pytest -q

all: generate verify
