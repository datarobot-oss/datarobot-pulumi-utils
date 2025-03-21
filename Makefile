.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

SOURCE?=src
TESTS?=tests

lint: ## Lint the codebase
	@echo "🧹 Ruff"
	@pdm run ruff check --fix $(SOURCE) $(TESTS)
	@echo "🧽 MyPy"
	@pdm run mypy --pretty $(SOURCE) $(TESTS)

lint-check: ## Check whether the codebase is linted
	@echo "🧹 Ruff"
	@pdm run ruff check $(SOURCE) $(TESTS)
	@pdm "🧽 MyPy"
	@poetry run mypy --pretty $(SOURCE) $(TESTS)

copyright: ## Apply copyrights to all files
	@echo "🧹 Applying license headers"
	docker run  --rm -v $(CURDIR):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:eb0e0b091ea41213f712f622797e37526ca1e5d6 -v info -c .licenserc.yaml header fix

copyright-check: ## Check if all files have the correct copyright
	@echo "👀 Checking for license headers"
	@docker run  --rm -v $(CURDIR):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:eb0e0b091ea41213f712f622797e37526ca1e5d6 -v info -c .licenserc.yaml header check