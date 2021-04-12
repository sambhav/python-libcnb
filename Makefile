.PHONY: test
test:
	poetry run pytest

.PHONY: lint
lint:
	poetry run flake8 libcnb/
	poetry run black --check libcnb/ tests/
	poetry run isort --check libcnb/ tests/
	poetry run autoflake -c -r -i --remove-all-unused-imports --ignore-init-module-imports libcnb
	poetry run mypy libcnb/

.PHONY: fix-lint
fix-lint:
	poetry run black libcnb/ tests/
	poetry run isort libcnb/ tests/
	poetry run autoflake -r -i --remove-all-unused-imports --ignore-init-module-imports libcnb

.PHONY: docs-serve
docs-serve:
	poetry run mkdocs serve

.PHONY: prepare-for-pr
prepare-for-pr: fix-lint lint test
	@echo "========"
	@echo "It looks good! :)"
	@echo "Make sure to commit all changes!"
	@echo "========"