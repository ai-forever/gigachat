.DEFAULT_GOAL := help

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'

.PHONY: .uv
.uv:
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .uv .pre-commit
	uv sync --group dev
	pre-commit install --install-hooks

.PHONY: clean  ## Clear local caches and build artifacts
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f .coverage.*
	rm -f coverage.*
	rm -f report.xml
	rm -rf dist

.PHONY: fmt  ## Auto-format python source files
fmt:
	uv run ruff format src tests
	uv run ruff check --fix src tests

.PHONY: lint  ## Lint python source files
lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

.PHONY: mypy  ## Perform type-checking
mypy:
	uv run mypy src tests

.PHONY: test  ## Run tests and generate a coverage report
test:
	uv run pytest -v --cov=src --cov-report=term-missing

.PHONY: htmlcov  ## Open html coverage report
htmlcov: test
	uv run coverage html
	open htmlcov/index.html
	#explorer "htmlcov\index.html" &

.PHONY: all  ## Run the standard set of checks performed in CI
all: lint mypy test

.PHONY: lock  ## Update lockfile
lock:
	uv lock

.PHONY: update  ## Update dependencies
update:
	uv lock --upgrade
	uv sync --group dev

.PHONY: pre  ## Run pre-commit on all the files in the repo
pre:
	pre-commit run --all-files
