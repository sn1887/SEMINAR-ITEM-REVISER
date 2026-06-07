.PHONY: install install-dev test lint format smoke eval clean

install:
	pip install -e .

install-dev:
	pip install -e '.[dev]'

install-hf:
	pip install -e '.[dev,hf]'

test:
	pytest -q

lint:
	ruff check src scripts tests

format:
	ruff format src scripts tests

smoke:
	python scripts/run_item_reviser.py item.question="Don’t you agree that stricter environmental regulations are necessary?"

eval:
	python scripts/evaluate.py experiment=item_reviser_eval model=mock

clean:
	rm -rf outputs multirun .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
