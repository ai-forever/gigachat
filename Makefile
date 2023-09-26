.DEFAULT_GOAL := help

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'

.PHONY: .poetry
.poetry:
	@poetry -V || echo 'Please install Poetry: https://python-poetry.org/docs/#installing-with-the-official-installer'

.PHONY: .pre-commit
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .poetry .pre-commit
	poetry install
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
	poetry run black src tests
	poetry run ruff --fix src tests

.PHONY: lint  ## Lint python source files
lint:
	poetry run ruff src tests
	poetry run black --check --diff src tests

.PHONY: mypy  ## Perform type-checking
mypy:
	poetry run mypy src

.PHONY: test  ## Run tests and generate a coverage report
test:
	poetry run coverage run -m pytest -v
	poetry run coverage report

.PHONY: htmlcov  ## Open html coverage report
htmlcov: test
	poetry run coverage html
	open htmlcov/index.html
	#explorer "htmlcov\index.html" &

.PHONY: all  ## Run the standard set of checks performed in CI
all: lint mypy test

.PHONY: pre  ## Run pre-commit on all the files in the repo
pre:
	pre-commit run --all-files
