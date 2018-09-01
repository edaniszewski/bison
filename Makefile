#
# bison - python application configuration
#

HAS_PIPENV := $(shell which pipenv)
PKG_VERSION := $(shell cat bison/__version__.py | grep __version__ | awk '{print $$3}')

requires-pipenv:
ifndef HAS_PIPENV
	@echo "pipenv required, but not found: run 'pip install pipenv --upgrade'"
	exit 1
endif

.PHONY: init
init: requires-pipenv  ## Initialize the project for development
	pipenv install --dev --skip-lock

.PHONY: test
test:  ## Run the bison unit tests
	pipenv run py.test -vv

.PHONY: ci
ci: coverage lint ## Run the ci pipeline (test w/ coverage, lint)

.PHONY: lint
lint: requires-pipenv  ## Run static analysis / linting on bison
	pipenv run flake8 --ignore=E501,E712 bison
	pipenv run isort bison tests -rc -c --diff

.PHONY: coverage
coverage: requires-pipenv  ## Show the coverage report for unit tests
	pipenv run py.test --cov-report term --cov-report html --cov=bison tests

.PHONY: publish
publish:  ## Publish bison to Pypi
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg bison.egg-info

.PHONY: version
version:  ## Print the current version of the package
	@echo $(PKG_VERSION)

.PHONY: help
help:  ## Print Make usage information
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.DEFAULT_GOAL := help