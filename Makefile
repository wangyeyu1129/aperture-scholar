.PHONY: check format test schemas
check:
	python -m ruff check src tests scripts
	python -m ruff format --check src tests scripts
	python -m mypy
	python -m pytest --cov=aperture_scholar --cov-report=term-missing
	python scripts/export_schemas.py --check
format:
	python -m ruff check --fix src tests scripts
	python -m ruff format src tests scripts
test:
	python -m pytest
schemas:
	python scripts/export_schemas.py
