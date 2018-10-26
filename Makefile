#
# bison - python application configuration
#

PKG_VERSION := $(shell cat bison/__version__.py | grep __version__ | awk '{print $$3}')


.PHONY: test
test:  ## Run the bison unit tests
	tox tests

.PHONY: ci
ci: test lint  ## Run the ci pipeline (test w/ coverage, lint)

.PHONY: deps  ## Update pinned project dependencies (requirements.txt)
deps:
	tox -e deps

.PHONY: lint
lint:  ## Run static analysis / linting on bison
	tox -e lint

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