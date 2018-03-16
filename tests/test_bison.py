"""Unit tests for bison.bison"""

import os

import pytest

import bison
from bison import errors
from bison.bison import YAML


class TestBison:
    """Test for the `Bison` class."""

    def test_simple_init(self):
        """Initialize a Bison object."""
        b = bison.Bison()

        assert b.scheme is None
        assert b.config_name == 'config'
        assert b.config_paths == []
        assert b.config_file is None
        assert b.env_prefix is None
        assert b.auto_env is False

        assert b._full_config is None
        assert isinstance(b._default, bison.DotDict)
        assert isinstance(b._config, bison.DotDict)
        assert isinstance(b._environment, bison.DotDict)
        assert isinstance(b._override, bison.DotDict)

        assert len(b._default) == 0
        assert len(b._config) == 0
        assert len(b._environment) == 0
        assert len(b._override) == 0

    def test_config_property_empty(self):
        """Get the full configuration when nothing is set."""
        b = bison.Bison()

        assert b._full_config is None
        c = b.config
        assert isinstance(c, bison.DotDict)
        assert len(c) == 0
        assert b._full_config == c

    @pytest.mark.parametrize(
        'key,expected,config', [
            ('foo', None, None),
            ('foo', None, bison.DotDict()),
            ('foo', None, bison.DotDict({'foo': None})),
            ('foo', 'bar', bison.DotDict({'foo': 'bar'})),
            ('foo.bar', 'baz', bison.DotDict({'foo': {'bar': 'baz'}})),
            ('foo.bar.baz', 1, bison.DotDict({'foo': {'bar': {'baz': 1}}})),
        ]
    )
    def test_get(self, key, expected, config):
        """Get configuration values from Bison."""
        b = bison.Bison()
        b._full_config = config  # for the test, set the config manually

        value = b.get(key)
        assert value == expected

    @pytest.mark.parametrize(
        'key,value', [
            ('foo', 'bar'),
            ('foo', 1),
            ('foo', False),
            ('foo', True),
            ('foo', None),
            ('foo.bar', 'baz'),
            ('foo.bar.baz', 1),
        ]
    )
    def test_set(self, key, value):
        """Set configuration overrides for a Bison instance."""
        b = bison.Bison()
        assert len(b._override) == 0
        assert b.get(key) is None

        b.set(key, value)

        assert len(b._override) == 1
        assert b.get(key) == value

    def test_set_multiple_nested(self):
        """Set overrides for multiple nested values"""
        b = bison.Bison()
        assert len(b._override) == 0
        assert len(b.config) == 0

        b.set('foo.bar.a', 'test')

        assert b.config == {
            'foo': {
                'bar': {
                    'a': 'test'
                }
            }
        }

        b.set('foo.bar.b', 'test')

        assert b.config == {
            'foo': {
                'bar': {
                    'a': 'test',
                    'b': 'test'
                }
            }
        }

    def test_set_multiple_nested_2(self):
        """Set overrides for multiple nested values when some already exist."""
        b = bison.Bison()
        assert len(b._override) == 0
        assert len(b.config) == 0

        # set the override config config to something to begin
        b._override = bison.DotDict({
            'foo': 'bar',
            'bar': {
                'bat': {
                    'a': 'test'
                },
                'bird': {
                    'b': 'test'
                }
            }
        })

        b.set('foo', 'baz')
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': 'test'
                },
                'bird': {
                    'b': 'test'
                }
            }
        }

        b.set('bar.bat.a', None)
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': None
                },
                'bird': {
                    'b': 'test'
                }
            }
        }

        b.set('bar.bird', 'warbler')
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': None
                },
                'bird': 'warbler'
            }
        }

    def test_set_multiple_nested_3(self):
        """Set overrides for multiple nested values when some already exist."""
        b = bison.Bison()
        assert len(b._override) == 0
        assert len(b.config) == 0

        # set a non override config config to something to begin
        b._config = bison.DotDict({
            'foo': 'bar',
            'bar': {
                'bat': {
                    'a': 'test'
                },
                'bird': {
                    'b': 'test'
                }
            }
        })

        b.set('foo', 'baz')
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': 'test'
                },
                'bird': {
                    'b': 'test'
                }
            }
        }

        b.set('bar.bat.a', None)
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': None
                },
                'bird': {
                    'b': 'test'
                }
            }
        }

        b.set('bar.bird', 'warbler')
        assert b.config == {
            'foo': 'baz',
            'bar': {
                'bat': {
                    'a': None
                },
                'bird': 'warbler'
            }
        }

    @pytest.mark.parametrize(
        'paths', [
            (),
            ('path1',),
            ('path1', 'path2'),
            ('path1', 'path2', 'path3')
        ]
    )
    def test_add_config_paths(self, paths):
        """Add configuration paths to the Bison instance."""
        b = bison.Bison()
        assert len(b.config_paths) == 0

        b.add_config_paths(*paths)
        assert len(b.config_paths) == len(paths)

    def test_validate_no_scheme(self):
        """Validate the Bison configuration when there is no Scheme to validate against."""
        b = bison.Bison()
        b.set('foo', 'bar')
        b.validate()

    def test_validate_ok(self):
        """Validate the Bison configuration successfully."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', field_type=str)
        ))

        # add 'foo' to the config
        b.set('foo', 'bar')

        # validation should succeed -- the value of 'foo' is a string
        b.validate()

    def test_validate_fail(self):
        """Validate the Bison configuration unsuccessfully."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', field_type=str)
        ))

        # add 'foo' to the config
        b.set('foo', 1)

        # validation should fail -- the value of 'foo' is not a string
        with pytest.raises(errors.SchemeValidationError):
            b.validate()

    def test_parse_no_sources(self):
        """Parse when there are no sources to parse from."""
        b = bison.Bison()
        b.parse()
        assert len(b.config) == 0

    def test_find_config(self, yaml_config):
        """Find a config file when it does exist"""
        b = bison.Bison()
        b.config_name = 'config'
        b.config_format = YAML
        b.config_paths = ['.', yaml_config.dirname]

        assert b.config_file is None

        b._find_config()

        assert b.config_file == os.path.join(yaml_config.dirname, yaml_config.basename)

    def test_find_config_nonexistent(self):
        """Find a config file when it does not exist"""
        b = bison.Bison()
        b.config_name = 'config'
        b.config_format = YAML
        b.config_paths = ['.']

        assert b.config_file is None

        with pytest.raises(errors.BisonError):
            b._find_config()

    def test_parse_config_no_paths(self):
        """Parse the file config when no paths are specified"""
        b = bison.Bison()

        assert b.config_file is None
        assert len(b._config) == 0

        b._parse_config()

        assert b.config_file is None
        assert len(b._config) == 0

    def test_parse_config_ok(self, yaml_config):
        """Parse the file config successfully."""
        b = bison.Bison()
        b.add_config_paths(yaml_config.dirname)

        assert b.config_file is None
        assert len(b._config) == 0

        b._parse_config()

        assert b.config_file == os.path.join(yaml_config.dirname, yaml_config.basename)
        assert len(b._config) == 2
        assert b.config == {
            'foo': True,
            'bar': {
                'baz': 1,
                'test': 'value'
            }
        }

    def test_parse_config_fail(self, bad_yaml_config):
        """Parse the file config unsuccessfully."""
        b = bison.Bison()
        b.add_config_paths(bad_yaml_config.dirname)

        assert b.config_file is None
        assert len(b._config) == 0

        with pytest.raises(errors.BisonError):
            b._parse_config()

        assert b.config_file == os.path.join(bad_yaml_config.dirname, bad_yaml_config.basename)
        assert len(b._config) == 0

    def test_parse_config_not_required_found(self, yaml_config):
        """Parse the file config when it isn't required."""
        b = bison.Bison()
        b.add_config_paths(yaml_config.dirname)

        assert b.config_file is None
        assert len(b._config) == 0

        b._parse_config(requires_cfg=False)

        assert b.config_file == os.path.join(yaml_config.dirname, yaml_config.basename)
        assert len(b._config) == 2
        assert b.config == {
            'foo': True,
            'bar': {
                'baz': 1,
                'test': 'value'
            }
        }

    def test_parse_config_not_required_not_found(self):
        """Parse the file config when it isn't required."""
        b = bison.Bison()
        b.add_config_paths('.')

        assert b.config_file is None
        assert len(b._config) == 0

        b._parse_config(requires_cfg=False)

        assert b.config_file is None
        assert len(b._config) == 0

    def test_parse_defaults_no_scheme(self):
        """Parse the defaults when there is no Scheme."""
        b = bison.Bison()

        assert len(b._default) == 0
        assert b._full_config is None

        b._parse_default()

        assert len(b._default) == 0
        assert b._full_config is None

    def test_parse_defaults_ok(self):
        """Parse the defaults successfully."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', default='bar')
        ))

        assert len(b._default) == 0
        assert len(b.config) == 0

        b._parse_default()

        assert len(b._default) == 1
        assert b.config == {'foo': 'bar'}

    def test_parse_env_env_prefix(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison()
        b.env_prefix = 'TEST_ENV_'
        b.auto_env = True

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # no scheme means nothing parsed.
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_env_prefix2(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison()
        # here, do not include the trailing '_', this should be added
        # on automatically if not there.
        b.env_prefix = 'TEST_ENV'
        b.auto_env = True

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # no scheme means nothing parsed.
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env='FOO')
        ))
        b.env_prefix = 'TEST_ENV'

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # we should get nothing back here -- env parsing will NOT
        # use the env_prefix when bind_env is specified manually.
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env_no_prefix(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env='TEST_ENV_FOO')
        ))

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 1
        assert b.config == {
            'foo': 'bar'
        }

    def test_parse_env_bind_env_auto(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            # this will autoenv to TEST_ENV_FOO, so we set to something
            # different here to test that it a.) works, b.) overrides autoenv
            bison.Option('foo', bind_env='TEST_OTHER_ENV_BAR'),
            bison.DictOption('nested', scheme=bison.Scheme(
                bison.DictOption('env', scheme=bison.Scheme(
                    bison.Option('key')
                ))
            ))
        ))
        b.env_prefix = 'TEST_ENV'
        b.auto_env = True

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 2
        assert b.config == {
            'foo': 'baz',
            'nested': {
                'env': {
                    'key': 'test'
                }
            }
        }

    def test_parse_env_bind_env_false(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=False)
        ))
        b.env_prefix = 'TEST_ENV'

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # we should get nothing back here -- nothing configured for
        # env parsing
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env_false_no_prefix(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=False)
        ))

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # we should get nothing back here -- nothing configured for
        # env parsing
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env_false_auto(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=False)
        ))
        b.env_prefix = 'TEST_ENV'
        b.auto_env = True

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # we should not get back the 'foo' key since its disabled,
        # even with auto-env
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env_true(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=True)
        ))
        b.env_prefix = 'TEST_ENV'

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 1
        assert b.config == {
            'foo': 'bar'
        }

    def test_parse_env_bind_env_true_no_prefix(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=True)
        ))

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        # we should not get anything back since we don't have a 'FOO' env variable
        assert len(b._environment) == 0
        assert len(b.config) == 0

    def test_parse_env_bind_env_true_auto(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env=True),
            bison.DictOption('nested', scheme=bison.Scheme(
                bison.DictOption('env', scheme=bison.Scheme(
                    bison.Option('key')
                ))
            ))
        ))
        b.env_prefix = 'TEST_ENV'
        b.auto_env = True

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 2
        assert b.config == {
            'foo': 'bar',
            'nested': {
                'env': {
                    'key': 'test'
                }
            }
        }

    def test_parse_env_int_value(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env='FOO_INT', field_type=int)
        ))

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 1
        assert b.config == {
            'foo': 1,
        }

    def test_parse_env_bool_value(self, with_env):
        """Parse the environment variable configuration."""
        b = bison.Bison(scheme=bison.Scheme(
            bison.Option('foo', bind_env='FOO_BOOL', field_type=bool)
        ))

        assert len(b._environment) == 0
        assert len(b.config) == 0

        b._parse_env()

        assert len(b._environment) == 1
        assert b.config == {
            'foo': False,
        }
