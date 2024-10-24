VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
TEST = pytest

# Self documenting commands
.DEFAULT_GOAL := help
.PHONY: help
help: ## show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%s\033[0m|%s\n", $$1, $$2}' \
	| column -t -s '|'

$(BIN)/activate: requirements.txt
	uv venv
	uv pip install -U pip
	uv pip install -r requirements.txt

init: ## Initialize the project environment (venv & pre-commit)
	@$(MAKE) $(BIN)/activate
	@$(MAKE) update
	@$(MAKE) clean

clean: ## Remove temporary files
	@rm -rf .ipynb_checkpoints
	@rm -rf **/.ipynb_checkpoints
	@rm -rf __pycache__
	@rm -rf **/__pycache__
	@rm -rf **/**/__pycache__
	@rm -rf .pytest_cache
	@rm -rf **/.pytest_cache
	@rm -rf .ruff_cache
	@rm -rf .coverage
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf site/
	@rm -rf .mypy_cache
	@rm -rf **/*.egg-info

bump: ## Show the next version
	@bump-my-version show-bump

bump-patch: $(VENV)/bin/activate ## Bump patch version
	@printf "Applying patch bump\n"
	@$(BIN)/bump-my-version bump patch
	@$(MAKE) bump

bump-minor: $(VENV)/bin/activate ## Bump minor version
	@printf "Applying minor bump\n"
	@$(BIN)/bump-my-version bump minor
	@$(MAKE) bump

bump-major: $(VENV)/bin/activate ## Bump major version
	@printf "Applying major bump\n"
	@$(BIN)/bump-my-version bump major
	@$(MAKE) bump

update: $(VENV)/bin/activate ## Update pre-commit
	$(PYTHON) -m pre_commit install --install-hooks
	$(PYTHON) -m pre_commit autoupdate

test: $(VENV)/bin/activate ## Run unit tests
	$(PYTHON) -m $(TEST)
	$(MAKE) clean

lint: $(VENV)/bin/activate ## Run pre-commit hooks
	$(PYTHON) -m pre_commit install --install-hooks
	$(PYTHON) -m pre_commit run --all-files
	$(MAKE) clean

build-dist: $(VENV)/bin/activate ## Generate distribution packages
	$(PYTHON) -m build

build-docker: ## Build the docker image
	@docker build -t crossdb-query .

publish: $(VENV)/bin/activate ## Publish to PyPI
	$(MAKE) lint
	$(MAKE) build-dist
	$(PYTHON) -m twine upload --repository pypi dist/*
	$(MAKE) clean

build: $(VENV)/bin/activate ## Build the project, docs, and docker image
	$(MAKE) lint
	$(MAKE) build-dist
	$(MAKE) build-docker
