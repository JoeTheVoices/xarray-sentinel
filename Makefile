ENVIRONMENT := XARRAY-SENTINEL
COV_REPORT := html
CONDA := conda
CONDAOPTS := -n $(ENVIRONMENT)

default: fix-code-style unit-test code-quality

fix-code-style:
	black .
	isort .
	mdformat .

test: unit-test doc-test

unit-test:
	python -m pytest -v --cov=. --cov-report=$(COV_REPORT) tests/

doc-test:
	python -m pytest -v README.md

code-quality:
	flake8 . --max-complexity=10 --max-line-length=127 --extend-ignore E203
	mypy --strict .

code-style:
	black --check .
	isort --check .
	mdformat --check .

# deploy

conda-env-create:
	$(CONDA) env create $(CONDAOPTS) -f environment-ci.yml

conda-env-update:
	$(CONDA) env update $(CONDAOPTS) -f environment-ci.yml
	pip install git+https://github.com/rasterio/rasterio  # need rasterio >= 1.3a3 for fsspec support

conda-env-update-all: conda-env-update
	$(CONDA) env update $(CONDAOPTS) -f environment-dev.yml
