PYTHON := .venv/bin/python

.PHONY: setup validate generate verify test all variant

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

variant:
	@test -n "$(V)" || { echo "ERROR: V is required - make variant V=<tag>"; exit 2; }
	$(PYTHON) validate_data.py --variant $(V)
	$(PYTHON) generate.py --variant $(V)
	$(PYTHON) verify_ats.py --variant $(V)
