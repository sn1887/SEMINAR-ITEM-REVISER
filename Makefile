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
	python scripts/smoke_test.py

eval:
	test -n "$(MODEL_PATH)" || (echo "Set MODEL_PATH=/path/to/local/hf/model" && exit 1)
	python scripts/evaluate.py experiment=item_reviser_eval model=hf_local model.model_path="$(MODEL_PATH)"

clean:
	rm -rf outputs multirun .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
