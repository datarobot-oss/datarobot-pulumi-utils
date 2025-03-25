.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

SOURCE?=src
TESTS?=tests

.PHONY: lint
lint: ## Lint the codebase
	@echo "🧹 Ruff"
	@uv run ruff format $(SOURCE)
	@uv run ruff check --fix $(SOURCE)
	@echo "🧽 MyPy"
	@uv run mypy --pretty $(SOURCE)

.PHONY: lint-check
lint-check: ## Check whether the codebase is linted
	@echo "🧹 Ruff"
	@uv run ruff format --check $(SOURCE)
	@uv run ruff check $(SOURCE)
	@echo "🧽 MyPy"
	@uv run mypy --pretty $(SOURCE)

.PHONY: copyright
copyright: ## Apply copyrights to all files
	@echo "🧹 Applying license headers"
	docker run  --rm -v $(CURDIR):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:eb0e0b091ea41213f712f622797e37526ca1e5d6 -v info -c .licenserc.yaml header fix

.PHONY: copyright-check
copyright-check: ## Check if all files have the correct copyright
	@echo "👀 Checking for license headers"
	@docker run  --rm -v $(CURDIR):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:eb0e0b091ea41213f712f622797e37526ca1e5d6 -v info -c .licenserc.yaml header check

.PHONY: build
build: ## Build the package
	@echo "🏗️ Building the package"
	@uv build

.PHONY: clean
clean: ## Clean temporary files
	@echo "🧹 Cleaning temporary files.."
	@rm -rf dist
	@rm -rf .mypy_cache .pytest_cache .ruff_cache *.egg-info
	@rm -rf .coverage htmlcov coverage.xml
