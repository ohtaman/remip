.PHONY: help install test test-cpython test-pyodide test-all build clean lint format

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd remip && uv sync --dev
	cd remip-client && uv sync --dev
	cd remip-client/tests/node && npm install

build: ## Build remip-client wheel
	cd remip-client && uv build

test-remip-server: ## Run remip server tests
	cd remip && uv run pytest tests/ -v

test-remip-client-python: ## Run remip-client Python tests
	cd remip-client && uv run pytest tests/ -v

test-remip-client-pyodide: ## Run remip-client Pyodide tests (requires build)
	./scripts/test-pyodide.sh

test-cpython: test-remip-server test-remip-client-python ## Run all CPython tests

test-pyodide: test-remip-client-pyodide ## Alias for test-remip-client-pyodide

test-all: ## Run all tests
	./scripts/run-all-tests.sh

test: test-all ## Alias for test-all

clean: ## Clean build artifacts
	cd remip && rm -rf dist/ build/ *.egg-info/
	cd remip-client && rm -rf dist/ build/ *.egg-info/
	cd remip-client/tests/node && rm -rf node_modules/

lint: ## Run linting
	cd remip && uv run ruff check .
	cd remip-client && uv run ruff check .

format: ## Format code
	cd remip && uv run ruff format .
	cd remip-client && uv run ruff format .

dev-server: ## Start development server
	cd remip && uv run python -m remip.main

dev-test: ## Quick test for development
	cd remip-client && uv build
	cd remip-client/tests/node && npm run test-only

pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type pre-push

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

test-changed: ## Test only changed files
	./scripts/test-changed-files.sh
