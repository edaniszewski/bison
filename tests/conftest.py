"""Test fixtures for Bison unit tests."""

import os

import pytest


@pytest.fixture()
def yaml_config(tmpdir):
    """Create a YAML config file."""
    cfg = tmpdir.join('config.yml')
    cfg.write("""
    foo: True
    bar:
      baz: 1
      test: value
    """)

    yield cfg

    cfg.remove()


@pytest.fixture()
def bad_yaml_config(tmpdir):
    """Create a bad YAML config file."""
    cfg = tmpdir.join('config.yml')
    cfg.write("""
    field:\n::>:!~-:
    """)

    yield cfg

    cfg.remove()


@pytest.fixture()
def with_env():
    """Set and cleanup environment variables for tests."""
    os.environ['TEST_ENV_FOO'] = 'bar'
    os.environ['TEST_ENV_NESTED_ENV_KEY'] = 'test'
    os.environ['TEST_ENV_BAR_LIST'] = 'a,b,c'
    os.environ['TEST_OTHER_ENV_BAR'] = 'baz'
    os.environ['FOO_INT'] = '1'
    os.environ['FOO_BOOL'] = 'False'

    yield

    del os.environ['TEST_ENV_FOO']
    del os.environ['TEST_ENV_NESTED_ENV_KEY']
    del os.environ['TEST_ENV_BAR_LIST']
    del os.environ['TEST_OTHER_ENV_BAR']
    del os.environ['FOO_INT']
    del os.environ['FOO_BOOL']
