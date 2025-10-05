# Makefile for with-keepass (uses .venv)
# Common targets:
#   make dev       # full development pipeline (deps → lint → test → coverage → cc → bandit → build)
#   make venv      # create/upgrade virtualenv and install -e .[dev]
#   make lint      # flake8
#   make test      # unittest discovery
#   make coverage  # coverage run + report + badge
#   make cc        # radon cyclomatic complexity
#   make bandit    # security scan
#   make build     # build wheel
#   make clean     # remove build/test artifacts
#   make deepclean # clean + remove .venv

SHELL := /bin/bash
VENV ?= .venv
PKG  ?= with_keepass

# Cross-platform venv bin paths
ifeq ($(OS),Windows_NT)
  BIN := $(VENV)/Scripts
else
  BIN := $(VENV)/bin
endif

PY  := $(BIN)/python3
PIP := $(BIN)/pip

.PHONY: dev venv lint test coverage cc bandit build clean deepclean

dev: venv lint test coverage cc bandit build
	@echo "✅ Development pipeline complete."

# Rebuild the venv only when pyproject.toml changes
venv: $(VENV)/.stamp

$(VENV)/.stamp: pyproject.toml
	@echo ">> Ensuring virtual environment exists at $(VENV)"
	@python3 -m venv $(VENV)
	@echo ">> Upgrading pip"
	@$(PIP) install --upgrade pip
	@echo ">> Installing project in editable mode with dev extras"
	@$(PIP) install -e .[dev]
	@# Touch the stamp file to record the last successful build time
	@touch $@

lint:
	$(PY) -m flake8 -v $(PKG)/ --max-line-length 100 --ignore=E302,E305

test:
	$(PY) -m unittest discover tests/ -v

coverage:
	$(PY) -m coverage run -m unittest discover tests/
	$(PY) -m coverage report -m
	mkdir -p badges
	$(BIN)/coverage-badge -o badges/coverage.svg -f

cc:
	$(PY) -m radon cc -s $(PKG)/

bandit:
	$(PY) -m bandit -r $(PKG)/ --skip B606

build:
	$(PY) -m build

clean:
	@echo "Cleaning build and test artifacts…"
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info badges/coverage.svg
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

deepclean: clean
	@echo "Removing virtual environment…"
	rm -rf $(VENV)
