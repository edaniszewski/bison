"""Unit tests for bison.utils"""

import pytest

from bison import errors, scheme, utils


@pytest.mark.parametrize(
    'option,value,expected', [
        (scheme.Option('foo'), 'foo', 'foo'),
        (scheme.Option('foo'), 1, 1),
        (scheme.Option('foo'), None, None),
        (scheme.Option('foo'), False, False),
        (scheme.Option('foo', field_type=str), 'foo', 'foo'),
        (scheme.Option('foo', field_type=str), 1, '1'),
        (scheme.Option('foo', field_type=int), '1', 1),
        (scheme.Option('foo', field_type=float), '1', 1.0),
        (scheme.Option('foo', field_type=float), '1.23', 1.23),
        (scheme.Option('foo', field_type=bool), 'false', False),
        (scheme.Option('foo', field_type=bool), 'False', False),
        (scheme.Option('foo', field_type=bool), 'FALSE', False),
        (scheme.Option('foo', field_type=bool), 'true', True),
        (scheme.Option('foo', field_type=bool), 'True', True),
        (scheme.Option('foo', field_type=bool), 'TRUE', True),
    ]
)
def test_cast(option, value, expected):
    """Cast values to the type set by the Option."""
    actual = utils.cast(option, value)
    assert actual == expected


@pytest.mark.parametrize(
    'option,value', [
        (scheme.Option('foo', field_type=int), 'foo'),
        (scheme.ListOption('foo'), 'foo'),
        (scheme.Option('foo', field_type=list), 'foo'),
        (scheme.Option('foo', field_type=tuple), 'foo'),
    ]
)
def test_cast_fail(option, value):
    """Cast values to the type set by the Option."""
    with pytest.raises(errors.BisonError):
        utils.cast(option, value)


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
