"""Unit tests for bison.utils"""

import pytest

from bison import utils


@pytest.mark.parametrize(
    'key,value,expected', [
        ('a',    'b',   ('a', 'b')),
        ('a.b',  'c',   ('a', {'b': 'c'})),
        ('a.b.c', None, ('a', {'b': {'c': None}})),
        ('a.b.c', 1,    ('a', {'b': {'c': 1}})),
        ('a.b.c', True, ('a', {'b': {'c': True}}))
    ]
)
def test_build_dot_value(key, value, expected):
    """Test building new dictionaries based off of a dot notation key"""
    res = utils.build_dot_value(key, value)
    assert res == expected


class TestDotDict:
    """Tests for the DotDict class."""

    @pytest.mark.parametrize(
        'param,expected', [
            (None, {}),
            ({}, {}),
            ({'a': 'b'}, {'a': 'b'}),
            ({'a': 1, 'b': {'c': None}}, {'a': 1, 'b': {'c': None}})
        ]
    )
    def test_init(self, param, expected):
        """Initialize a new DotDict."""
        dd = utils.DotDict(param)
        assert dd == expected

    @pytest.mark.parametrize(
        'key,expected', [
            ('z', None),
            ('x.y.z', None),
            ('c.d.g', None),
            ('', None),
            ('a', 1),
            ('b', None),
            ('c', {'f': 'bar', 'd': {'e': 'foo'}}),
            ('c.d', {'e': 'foo'}),
            ('c.d.e', 'foo'),
            ('c.f', 'bar'),
            ('g', False)
        ]
    )
    def test_get(self, key, expected):
        """Get values from the DotDict."""
        dd = utils.DotDict({
            'a': 1,
            'b': None,
            'c': {
                'd': {
                    'e': 'foo'
                },
                'f': 'bar'
            },
            'g': False
        })

        # test getting values via the .get() method
        value = dd.get(key)
        assert value == expected

        # test getting values via dictionary access methods
        value = dd[key]
        assert value == expected

    @pytest.mark.parametrize(
        'key', [
            'a',
            'c',
            'c.d',
            'c.d.e',
            'c.f'
        ]
    )
    def test_delete_1(self, key):
        """Delete values from the DotDict that exist."""
        dd = utils.DotDict({
            'a': 1,
            'c': {
                'd': {
                    'e': 'foo'
                },
                'f': 'bar'
            }
        })

        value = dd.get(key)
        assert value is not None

        # delete via the .delete() method
        dd.delete(key)

        value = dd.get(key)
        assert value is None

    @pytest.mark.parametrize(
        'key', [
            'a',
            'c'
        ]
    )
    def test_delete_2(self, key):
        """Delete values from the DotDict using del"""
        dd = utils.DotDict({
            'a': 1,
            'c': {
                'd': {
                    'e': 'foo'
                },
                'f': 'bar'
            }
        })

        value = dd[key]
        assert value is not None

        # delete via the del keyword. since we are testing
        # first order keys, they should all resolve, so they
        # can be deleted successfully.
        del dd[key]

        value = dd[key]
        assert value is None

    @pytest.mark.parametrize(
        'key', [
            'x',
            'x.y.z',
            '',
            'c.e',
            'c.d.e',
            'c.d.e.f'
        ]
    )
    def test_delete_3(self, key):
        """Delete values that do not exist from the DotDict."""
        dd = utils.DotDict({
            'a': 1,
            'b': None,
            'c': {
                'd': 'foo',
                'f': 'bar'
            }
        })

        # delete via the .delete() method
        with pytest.raises(KeyError):
            dd.delete(key)

    @pytest.mark.parametrize(
        'key', [
            'c.d',
            'c.d.e',
            'c.f'
        ]
    )
    def test_delete_4(self, key):
        """Delete values from the DotDict using del"""
        dd = utils.DotDict({
            'a': 1,
            'c': {
                'd': {
                    'e': 'foo'
                },
                'f': 'bar'
            }
        })

        # delete via the del keyword. dot notation keys
        # should fail resolution and raise a KeyError
        with pytest.raises(KeyError):
            del dd[key]

    @pytest.mark.parametrize(
        'key,value', [
            ('a', 'foo'),
            ('b', 'bar'),
            ('b.c', False),
            ('x', 1),
            ('x.y', [1, 2, 3]),
            ('x.y.z', 'baz'),
            ('x.y.z.q', {'a': 'foo', 'b': [1, 2, 3]})
        ]
    )
    def test_set(self, key, value):
        """Set an item in the DotDict"""
        dd = utils.DotDict({
            'a': 1,
            'b': {'c': True}
        })

        dd[key] = value
        assert dd.get(key) == value

    def test_set_multiple_nested(self):
        """Set multiple nested items"""
        dd = utils.DotDict()
        assert dd == {}

        dd['foo.bar.a'] = 'test'
        assert dd == {
            'foo': {
                'bar': {
                    'a': 'test'
                }
            }
        }

        dd['foo.bar.b'] = 'test'
        assert dd == {
            'foo': {
                'bar': {
                    'a': 'test',
                    'b': 'test'
                }
            }
        }

    def test_set_multiple_neste2(self):
        """Set multiple nested items"""
        dd = utils.DotDict()
        assert dd == {}

        dd['foo'] = 'test'
        assert dd == {
            'foo': 'test'
        }

        dd['bar.baz'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test'
            }
        }

        dd['bar.ball'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test'
            }
        }

        dd['bar.bits.a'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test',
                'bits': {
                    'a': 'test'
                }
            }
        }

        dd['bar.bits.b'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test',
                'bits': {
                    'a': 'test',
                    'b': 'test'
                }
            }
        }

        dd['bar.new.a'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test',
                'bits': {
                    'a': 'test',
                    'b': 'test'
                },
                'new': {
                    'a': 'test'
                }
            }
        }

        dd['bar.new.b.c.d'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test',
                'bits': {
                    'a': 'test',
                    'b': 'test'
                },
                'new': {
                    'a': 'test',
                    'b': {
                        'c': {
                            'd': 'test'
                        }
                    }
                }
            }
        }

        dd['bar.new.b'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': {
                'baz': 'test',
                'ball': 'test',
                'bits': {
                    'a': 'test',
                    'b': 'test'
                },
                'new': {
                    'a': 'test',
                    'b': 'test'
                }
            }
        }

        dd['bar'] = 'test'
        assert dd == {
            'foo': 'test',
            'bar': 'test'
        }

        dd['foo.bar.a'] = 'test'
        assert dd == {
            'foo': {
                'bar': {
                    'a': 'test'
                }
            },
            'bar': 'test'
        }

        dd['foo'] = ['a', 'b', 'c']
        assert dd == {
            'foo': ['a', 'b', 'c'],
            'bar': 'test'
        }

        dd['foo.bar.b'] = ['a', 'b', 'c']
        assert dd == {
            'foo': {
                'bar': {
                    'b': ['a', 'b', 'c']
                }
            },
            'bar': 'test'
        }

    @pytest.mark.parametrize(
        'key,expected', [
            ('a', True),
            ('a.b', False),
            ('a.b.c', False),
            ('b', True),
            ('b.c', True),
            ('b.c', True),
            ('b.a', False),
            ('b.c.d', True),
            ('b.c.d.e', False),
            ('b.c.d.e.f', False),
            ('g', False),
            ('g.e', False),
        ]
    )
    def test_inclusion(self, key, expected):
        """Check if a key exists in a DotDict"""
        dd = utils.DotDict({
            'a': 1,
            'b': {
                'c': {
                    'd': 'foo'
                }
            }
        })
        assert (key in dd) is expected

    @pytest.mark.parametrize(
        'source,expected', [
            ({}, {'foo': 'bar', 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': 'test'}, {'foo': 'test', 'bar': {'baz': {'key': 'value'}}}),
            ({'abc': '123'}, {'foo': 'bar', 'abc': '123', 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': 'test'}, {'foo': 'bar', 'bar': 'test'}),
            ({'bar': {'test': 'value'}}, {'foo': 'bar', 'bar': {'test': 'value'}}),
            ({'test': 123}, {'foo': 'bar', 'test': 123, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': 123}, {'foo': 123, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': 123}, {'foo': 'bar', 'bar': 123}),
            ({'test': [1, 2, 3]}, {'foo': 'bar', 'test': [1, 2, 3], 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': [1, 2, 3]}, {'foo': [1, 2, 3], 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': [1, 2, 3]}, {'foo': 'bar', 'bar': [1, 2, 3]}),
            ({'test': {'a': 1}}, {'foo': 'bar', 'test': {'a': 1}, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': {'a': 1}}, {'foo': {'a': 1}, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': {'a': 1}}, {'foo': 'bar', 'bar': {'a': 1}}),
            ({'test': False}, {'foo': 'bar', 'test': False, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': False}, {'foo': False, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': False}, {'foo': 'bar', 'bar': False}),
            ({'test': None}, {'foo': 'bar', 'test': None, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': None}, {'foo': None, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': None}, {'foo': 'bar', 'bar': None}),
        ]
    )
    def test_update(self, source, expected):
        """Update the DotDict"""
        dd = utils.DotDict({
            'foo': 'bar',
            'bar': {
                'baz': {
                    'key': 'value'
                }
            }
        })
        dd.update(source)
        assert dd == expected

    @pytest.mark.parametrize(
        'source,expected', [
            ({}, {'foo': 'bar', 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': 'test'}, {'foo': 'test', 'bar': {'baz': {'key': 'value'}}}),
            ({'abc': '123'}, {'foo': 'bar', 'abc': '123', 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': 'test'}, {'foo': 'bar', 'bar': 'test'}),
            ({'bar': {'test': 'value'}}, {'foo': 'bar', 'bar': {'baz': {'key': 'value'}, 'test': 'value'}}),
            ({'test': 123}, {'foo': 'bar', 'test': 123, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': 123}, {'foo': 123, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': 123}, {'foo': 'bar', 'bar': 123}),
            ({'test': [1, 2, 3]}, {'foo': 'bar', 'test': [1, 2, 3], 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': [1, 2, 3]}, {'foo': [1, 2, 3], 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': [1, 2, 3]}, {'foo': 'bar', 'bar': [1, 2, 3]}),
            ({'test': {'a': 1}}, {'foo': 'bar', 'test': {'a': 1}, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': {'a': 1}}, {'foo': {'a': 1}, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': {'a': 1}}, {'foo': 'bar', 'bar': {'a': 1, 'baz': {'key': 'value'}}}),
            ({'test': False}, {'foo': 'bar', 'test': False, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': False}, {'foo': False, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': False}, {'foo': 'bar', 'bar': False}),
            ({'test': None}, {'foo': 'bar', 'test': None, 'bar': {'baz': {'key': 'value'}}}),
            ({'foo': None}, {'foo': None, 'bar': {'baz': {'key': 'value'}}}),
            ({'bar': None}, {'foo': 'bar', 'bar': None}),
        ]
    )
    def test_merge(self, source, expected):
        """Update the DotDict"""
        dd = utils.DotDict({
            'foo': 'bar',
            'bar': {
                'baz': {
                    'key': 'value'
                }
            }
        })
        dd.merge(source)
        assert dd == expected

    def test_deep_merge(self):
        """Test merging through many nested dicts."""
        dd = utils.DotDict({
            'foo': {
                'bar': {
                    'baz': {
                        'bison': True
                    }
                }
            }
        })
        dd.merge({'foo': {
            'bar': {
                'baz': {
                    'birds': False
                }
            }
        }})

        assert dd == {
            'foo': {
                'bar': {
                    'baz': {
                        'bison': True,
                        'birds': False
                    }
                }
            }
        }
