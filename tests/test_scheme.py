"""Unit tests for bison.scheme"""

import pytest

from bison import errors, scheme


def test_base_opt_validate():
    """Validate the base option, which should fail."""
    opt = scheme._BaseOpt()
    with pytest.raises(NotImplementedError):
        opt.validate('test-data')


def test_base_opt_parse_env():
    """Parse env from the base option, which should fail."""
    opt = scheme._BaseOpt()
    with pytest.raises(NotImplementedError):
        opt.parse_env()


class TestOption:
    """Tests for the `Option` class."""

    def test_init_simple(self):
        """Initialize an Option."""
        opt = scheme.Option('test-opt')

        assert opt.name == 'test-opt'
        assert type(opt.default) == scheme.NoDefault
        assert opt.type is None
        assert opt.choices is None
        assert opt.bind_env is None

    def test_init_full(self):
        """Initialize an Option."""
        opt = scheme.Option(
            name='test-opt',
            default='foo',
            field_type=str,
            choices=['foo', 'bar'],
            bind_env=True
        )

        assert opt.name == 'test-opt'
        assert type(opt.default) != scheme.NoDefault
        assert opt.default == 'foo'
        assert opt.type == str
        assert opt.choices == ['foo', 'bar']
        assert opt.bind_env is True

    @pytest.mark.parametrize(
        'field_type,value', [
            (str, 'test-value'),
            (str, ''),
            (int, 0),
            (int, 1000),
            (int, -1),
            (float, 0.0),
            (float, 1000.999),
            (float, -1.0),
            (bool, True),
            (bool, False),
            (list, []),
            (list, [1, 2, 3]),
            (list, ['a', 'b', 'c']),
            (tuple, tuple()),
            (tuple, (1,)),
            (tuple, ('a', 'b')),
            (dict, {}),
            (dict, {'a': 'b'}),
            (dict, {1: 2})
        ]
    )
    def test_validate_type_ok(self, field_type, value):
        """Validate an Option, where type validation succeeds"""
        opt = scheme.Option('test-option', field_type=field_type)
        opt.validate(value)

    @pytest.mark.parametrize(
        'field_type,value', [
            (str, None),
            (str, 1),
            (str, 1.8),
            (str, True),
            (str, ['a', 'b', 'c']),

            (int, None),
            (int, 'value'),
            (int, 1.8),
            (int, True),
            (int, ['a', 'b', 'c']),

            (float, None),
            (float, 'value'),
            (float, 1),
            (float, True),
            (float, ['a', 'b', 'c']),

            (bool, None),
            (bool, 'value'),
            (bool, 1),
            (bool, 1.8),
            (bool, ['a', 'b', 'c']),

            (list, None),
            (list, 'value'),
            (list, 1),
            (list, 1.8),
            (list, True),
        ]
    )
    def test_validate_type_failure(self, field_type, value):
        """Validate an Option, where type validation fails"""
        opt = scheme.Option('test-option', field_type=field_type)
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

    @pytest.mark.parametrize(
        'choices,value', [
            (['one', 'two'], 'one'),  # choices can be lists
            (('one', 'two'), 'one'),  # choices can be tuples
            ([1, 2, 3], 1),
            ((1, 2, 3), 1),
            ([None], None),
            ((None,), None),
            ([1.21, 1.22, 1.23], 1.23),
            ((1.21, 1.22, 1.23), 1.23),
            ([True, False], False),
            ((True, False), False)
        ]
    )
    def test_validate_choices_ok(self, choices, value):
        """Validate an Option, where choice validation succeeds"""
        opt = scheme.Option('test-option', choices=choices)
        opt.validate(value)

    @pytest.mark.parametrize(
        'choices,value', [
            (['one', 'two'], 'three'),
            ([1, 2, 3], 0),
            ([], None),
            ([0.2, 0.3, 0.4], 0.1),
            ([False], True)
        ]
    )
    def test_validate_choices_failure(self, choices, value):
        """Validate an Option, where choice validation succeeds"""
        opt = scheme.Option('test-option', choices=choices)
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

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
    def test_cast(self, option, value, expected):
        """Cast values to the type set by the Option."""
        actual = option.cast(value)
        assert actual == expected

    @pytest.mark.parametrize(
        'option,value', [
            (scheme.Option('foo', field_type=int), 'foo'),
            (scheme.Option('foo', field_type=list), 'foo'),
            (scheme.Option('foo', field_type=tuple), 'foo'),
        ]
    )
    def test_cast_fail(self, option, value):
        """Cast values to the type set by the Option."""
        with pytest.raises(errors.BisonError):
            option.cast(value)

    @pytest.mark.parametrize(
        'option,prefix,auto_env', [
            (scheme.Option('foo'), None, False),
            (scheme.Option('foo', bind_env=False), None, False),
            (scheme.Option('foo', bind_env=True), None, False),
            (scheme.Option('foo', bind_env=True), 'TEST_ENV_', False),

            (scheme.Option('foo', bind_env='TEST_KEY'), None, False),
            (scheme.Option('foo', bind_env='TEST_KEY'), 'TEST_ENV_', False),

            (scheme.Option('foo', bind_env=None), 'TEST_ENV_', False),
            (scheme.Option('foo', bind_env=None), 'TEST_ENV_', True),
            (scheme.Option('foo', bind_env=None), None, False),
            (scheme.Option('foo', bind_env=None), None, True),
        ]
    )
    def test_parse_env_none(self, option, prefix, auto_env):
        """Parse environment variables for the Option. All of theses tests
        should result in None being returned because no environment variables
        are actually set.
        """
        actual = option.parse_env(prefix=prefix, auto_env=auto_env)
        assert actual is None

    @pytest.mark.parametrize(
        'option,key,prefix,auto_env,expected', [
            (scheme.Option('foo', bind_env=True), 'foo', 'TEST_ENV_', False, 'bar'),
            (scheme.Option('foo', bind_env=True), 'foo', 'TEST_ENV_', True, 'bar'),

            (scheme.Option('foo', bind_env='TEST_ENV_FOO'), 'foo', 'TEST_ENV_', False, 'bar'),
            (scheme.Option('foo', bind_env='TEST_ENV_FOO'), 'foo', 'TEST_ENV_', True, 'bar'),
            (scheme.Option('foo', bind_env='TEST_ENV_FOO'), 'foo', None, False, 'bar'),
            (scheme.Option('foo', bind_env='TEST_ENV_FOO'), 'foo', None, True, 'bar'),

            (scheme.Option('foo', bind_env=None), 'foo', 'TEST_ENV_', True, 'bar'),
            (scheme.Option('foo', bind_env=None), 'nested.env.key', 'TEST_ENV_', True, 'test'),
        ]
    )
    def test_parse_env_ok(self, option, key, prefix, auto_env, expected, with_env):
        """Parse environment variables for the Option."""
        actual = option.parse_env(key=key, prefix=prefix, auto_env=auto_env)
        assert actual == expected


class TestDictOption:
    """Tests for the `DictOption` class."""

    def test_init_simple(self):
        """Initialize a DictOption."""
        opt = scheme.DictOption('test-opt', None)

        assert opt.name == 'test-opt'
        assert type(opt.default) == scheme.NoDefault
        assert opt.scheme is None
        assert opt.bind_env is False

    def test_init_full(self):
        """Initialize a DictOption."""
        opt = scheme.DictOption(
            name='test-opt',
            scheme=scheme.Scheme(),
            default='foo',
            bind_env=True
        )

        assert opt.name == 'test-opt'
        assert type(opt.default) != scheme.NoDefault
        assert opt.default == 'foo'
        assert isinstance(opt.scheme, scheme.Scheme)
        assert opt.bind_env is True

    @pytest.mark.parametrize(
        'value', [
            'foo',
            1,
            1.234,
            False,
            True,
            None,
            [1, 2, 3],
            ['a', 'b', 'c'],
            [{'a': 1}, {'b': 2}],
            ('foo', 'bar'),
            {1, 2, 3}
        ]
    )
    def test_validate_bad_data(self, value):
        """Validate a DictOption where the given value is not a dict"""
        opt = scheme.DictOption('test-opt', scheme.Scheme())
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

    def test_validate_no_scheme(self):
        """Validate a DictOption with no scheme"""
        opt = scheme.DictOption('test-opt', None)
        opt.validate({'foo': 'bar'})

    def test_validate_with_scheme(self):
        """Validate a DictOption with a scheme"""
        opt = scheme.DictOption('test-opt', scheme.Scheme(
            scheme.Option('foo', field_type=str)
        ))
        opt.validate({'foo': 'bar'})

    @pytest.mark.parametrize(
        'option,prefix,auto_env', [
            (scheme.DictOption('foo', scheme=None, bind_env=False), None, False),
            (scheme.DictOption('foo', scheme=None, bind_env=False), None, True),
            (scheme.DictOption('foo', scheme=None, bind_env=False), 'TEST_ENV', False),
            (scheme.DictOption('foo', scheme=None, bind_env=False), 'TEST_ENV', True),

            (scheme.DictOption('foo', scheme=None, bind_env=True), None, False),
            (scheme.DictOption('foo', scheme=None, bind_env=True), None, True),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'TEST_ENV', False),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'TEST_ENV', True),
        ]
    )
    def test_parse_env_none(self, option, prefix, auto_env):
        """Parse environment variables for the DictOption. All of theses tests
        should result in None being returned because no environment variables
        are actually set.
        """
        actual = option.parse_env(prefix=prefix, auto_env=auto_env)
        assert actual is None

    @pytest.mark.parametrize(
        'option,key,prefix,auto_env,expected', [
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'foo', 'TEST_ENV_', False, None),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'foo', 'TEST_ENV_', True, None),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'nested', 'TEST_ENV_', False, {'env': {'key': 'test'}}),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'nested', 'TEST_ENV_', True, {'env': {'key': 'test'}}),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'nested.env', 'TEST_ENV_', False, {'key': 'test'}),
            (scheme.DictOption('foo', scheme=None, bind_env=True), 'nested.env', 'TEST_ENV_', True, {'key': 'test'}),
        ]
    )
    def test_parse_env_ok(self, option, key, prefix, auto_env, expected, with_env):
        """Parse environment variables for the DictOption."""
        actual = option.parse_env(key=key, prefix=prefix, auto_env=auto_env)
        assert actual == expected


class TestListOption:
    """Tests for the `ListOption` class."""

    def test_init_simple(self):
        """Initialize a ListOption."""
        opt = scheme.ListOption('test-opt')

        assert opt.name == 'test-opt'
        assert type(opt.default) == scheme.NoDefault
        assert opt.member_type is None
        assert opt.member_scheme is None
        assert opt.bind_env is False

    def test_init_full(self):
        """Initialize a ListOption."""
        opt = scheme.ListOption(
            name='test-opt',
            default='foo',
            member_type=dict,
            member_scheme=scheme.Scheme(),
            bind_env=True
        )

        assert opt.name == 'test-opt'
        assert type(opt.default) != scheme.NoDefault
        assert opt.default == 'foo'
        assert opt.member_type == dict
        assert isinstance(opt.member_scheme, scheme.Scheme)
        assert opt.bind_env is True

    @pytest.mark.parametrize(
        'value', [
            'foo',
            1,
            1.234,
            False,
            True,
            None,
            {'a': 1, 'b': 2},
            ('foo', 'bar'),
            {1, 2, 3}
        ]
    )
    def test_validate_bad_data(self, value):
        """Validate when the value is not a list"""
        opt = scheme.ListOption('test-opt')
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

    def test_validate_member_type_scheme_conflict(self):
        """Validate the ListOption when both member_type and member_scheme are defined."""
        opt = scheme.ListOption(
            name='test-opt',
            member_type=int,
            member_scheme=scheme.Scheme()
        )
        with pytest.raises(errors.SchemeValidationError):
            opt.validate([1, 2, 3])

    @pytest.mark.parametrize(
        'member_type,value', [
            (str, ['a', 'b', 'c']),
            (int, [1, 2, 3]),
            (float, [1.0, 2.0, 3.0]),
            (bool, [False, False, True]),
            (tuple, [(1,), (2,), (3,)]),
            (list, [[1], [2], [3]]),
            (dict, [{'a': 1, 'b': 2}])
        ]
    )
    def test_validate_member_type_ok(self, member_type, value):
        """Validate the ListOption, where member_type validation succeeds."""
        opt = scheme.ListOption('test-opt', member_type=member_type)
        opt.validate(value)

    @pytest.mark.parametrize(
        'member_type,value', [
            (str, ['a', 1]),
            (str, [1, 2]),
            (int, [1, 2, '3']),
            (int, ['foo', 'bar']),
            (float, [1.0, '2.0', 3.0]),
            (float, ['foo', 'bar']),
            (bool, ['False', False, True]),
            (bool, ['foo', 'bar']),
            (tuple, [(1,), '(2,)', (3,)]),
            (tuple, ['']),
            (list, [[1], (2,), [3]]),
            (list, ['foo', 'bar']),
            (dict, [{'a': 1}, {1, 2, 3}]),
            (dict, ['foo', 'bar'])
        ]
    )
    def test_validate_member_type_failure(self, member_type, value):
        """Validate the ListOption, where member_type validation fails."""
        opt = scheme.ListOption('test-opt', member_type=member_type)
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

    @pytest.mark.parametrize(
        'member_scheme,value', [
            # an empty scheme will validate every dict as correct
            (scheme.Scheme(), [{'foo': 'bar'}]),
            (scheme.Scheme(), [{1: 3}]),
            (scheme.Scheme(), [{1.23: 2.31}]),
            (scheme.Scheme(), [{False: True}]),
            (scheme.Scheme(), [{None: None}]),
            (scheme.Scheme(), [{(1, 2): (2, 1)}]),

            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': 'bar'}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': 'baz'}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': 'baz'}, {'foo': 'bar'}])
        ]
    )
    def test_validate_member_scheme_ok(self, member_scheme, value):
        """Validate the ListOption, where member_scheme validation succeeds."""
        opt = scheme.ListOption('test-opt', member_scheme=member_scheme)
        opt.validate(value)

    @pytest.mark.parametrize(
        'member_scheme,value', [
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': 1}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': 1.23}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': False}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': True}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': None}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': (1, 2)}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': ['a', 'b']}]),
            (scheme.Scheme(scheme.Option('foo', field_type=str)), [{'foo': {'a', 'b'}}]),

            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': 'foo'}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': 1.23}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': False}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': True}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': None}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': (1, 2)}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': ['a', 'b']}]),
            (scheme.Scheme(scheme.Option('bar', field_type=int)), [{'bar': {'a', 'b'}}])
        ]
    )
    def test_validate_member_scheme_fail(self, member_scheme, value):
        """Validate the ListOption, where member_scheme validation fails."""
        opt = scheme.ListOption('test-opt', member_scheme=member_scheme)
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(value)

    def test_validate_member_scheme_not_a_scheme(self):
        """Validate the ListOption, where the member_scheme is not a Scheme."""
        opt = scheme.ListOption('test-opt', member_scheme='not-none-or-scheme')
        with pytest.raises(errors.SchemeValidationError):
            opt.validate(['a', 'b', 'c'])

    @pytest.mark.parametrize(
        'option,prefix,auto_env', [
            (scheme.ListOption('foo', bind_env=False), None, False),
            (scheme.ListOption('foo', bind_env=False), None, True),
            (scheme.ListOption('foo', bind_env=False), 'TEST_ENV', False),
            (scheme.ListOption('foo', bind_env=False), 'TEST_ENV', True),

            (scheme.ListOption('foo', bind_env=True), None, False),
            (scheme.ListOption('foo', bind_env=True), None, True),
            (scheme.ListOption('foo', bind_env=True), 'TEST_ENV', False),
            (scheme.ListOption('foo', bind_env=True), 'TEST_ENV', True),
        ]
    )
    def test_parse_env_none(self, option, prefix, auto_env):
        """Parse environment variables for the ListOption. All of theses tests
        should result in None being returned because no environment variables
        are actually set.
        """
        actual = option.parse_env(prefix=prefix, auto_env=auto_env)
        assert actual is None

    @pytest.mark.parametrize(
        'option,key,prefix,auto_env,expected', [
            (scheme.ListOption('foo', bind_env=True), 'foo', 'TEST_ENV_', False, ['bar']),
            (scheme.ListOption('foo', bind_env=True), 'foo', 'TEST_ENV_', True, ['bar']),
            (scheme.ListOption('foo', bind_env=True), 'bar.list', 'TEST_ENV_', False, ['a', 'b', 'c']),
            (scheme.ListOption('foo', bind_env=True), 'bar.list', 'TEST_ENV_', True, ['a', 'b', 'c']),
        ]
    )
    def test_parse_env_ok(self, option, key, prefix, auto_env, expected, with_env):
        """Parse environment variables for the ListOption."""
        actual = option.parse_env(key=key, prefix=prefix, auto_env=auto_env)
        assert actual == expected


class TestScheme:
    """Tests for the `Scheme` class."""

    def test_empty_init(self):
        """Initialize a Scheme with no arguments."""
        sch = scheme.Scheme()

        assert len(sch.args) == 0
        assert sch._flat is None

    def test_single_arg_init(self):
        """Initialize a Scheme with one argument."""
        sch = scheme.Scheme(
            'item'
        )

        assert len(sch.args) == 1
        assert sch._flat is None

    def test_multi_arg_init(self):
        """Initialize a Scheme with multiple arguments."""
        sch = scheme.Scheme(
            'item-1',
            'item-2',
            'item-3'
        )

        assert len(sch.args) == 3
        assert sch._flat is None

    @pytest.mark.parametrize(
        'args,expected', [
            (
                # args
                (scheme.Option('foo', default='bar'),),
                # expected
                {'foo': 'bar'}
            ),
            (
                # args
                (
                    scheme.Option('foo'),
                    scheme.Option('bar', default='baz'),
                    scheme.ListOption('list', default=['a', 'b'])
                ),
                # expected
                {
                    'bar': 'baz',
                    'list': ['a', 'b']
                }
            ),
            (
                # args
                (
                    scheme.Option('foo', default='bar'),
                    scheme.DictOption('bar', scheme=None)
                ),
                # expected
                {
                    'foo': 'bar'
                }
            ),
            (
                # args
                (
                    scheme.DictOption('foo', scheme=scheme.Scheme(), default={}),
                    scheme.DictOption('bar', scheme=scheme.Scheme(
                        scheme.Option('test', default=True),
                        scheme.Option('data', default=None),
                        scheme.Option('value', default=20),
                        scheme.Option('float', default=10.1010),
                        scheme.Option('no_default'),
                        scheme.DictOption('dct', scheme=scheme.Scheme(
                            scheme.Option('nested', default='here')
                        ))
                    ))
                ),
                # expected
                {
                    'foo': {},
                    'bar': {
                        'test': True,
                        'data': None,
                        'value': 20,
                        'float': 10.1010,
                        'dct': {
                            'nested': 'here'
                        }
                    }
                }
            ),
        ]
    )
    def test_build_defaults(self, args, expected):
        """Build a defaults dict from a Scheme."""
        sch = scheme.Scheme(*args)
        defaults = sch.build_defaults()

        assert defaults == expected

    @pytest.mark.parametrize(
        'args', [
            ('a', 'b'),  # not an instance of _BaseOpt
        ]
    )
    def test_build_defaults_failure(self, args):
        """Build a defaults dict from a Scheme with bad data."""
        sch = scheme.Scheme(*args)
        with pytest.raises(errors.InvalidSchemeError):
            sch.build_defaults()

    @pytest.mark.parametrize(
        'args,expected', [
            (
                (scheme.Option('foo'),),
                ['foo']
            ),
            (
                (scheme.Option('foo'), scheme.Option('bar')),
                ['foo', 'bar']
            ),
            (
                (scheme.Option('foo'), scheme.DictOption('bar', scheme=None)),
                ['foo', 'bar']
            ),
            (
                (
                    scheme.Option('foo'),
                    scheme.DictOption('bar', scheme=scheme.Scheme(
                        scheme.Option('test'),
                        scheme.DictOption('dct', scheme=scheme.Scheme(
                            scheme.Option('nested')
                        )),
                        scheme.ListOption('list')
                    ))
                ),
                ['foo', 'bar', 'bar.test', 'bar.dct', 'bar.list', 'bar.dct.nested']
            )
        ]
    )
    def test_flatten(self, args, expected):
        """Flatten a Scheme."""
        sch = scheme.Scheme(*args)
        flattened = sch.flatten()

        assert len(flattened) == len(expected)
        for key in expected:
            assert key in flattened

    @pytest.mark.parametrize(
        'args,value', [
            (
                # option exists in config
                (scheme.Option('foo', default='bar', field_type=str),),
                {'foo': 'baz'}
            ),
            (
                # option does not exist in config, but has default
                (scheme.Option('foo', default='bar', field_type=str),),
                {}
            ),
            (
                # multiple args
                (
                    scheme.Option('foo', field_type=str),
                    scheme.Option('bar', field_type=int),
                    scheme.Option('baz', choices=['test'])
                ),
                {'foo': 'a', 'bar': 1, 'baz': 'test'}
            )
        ]
    )
    def test_validate_ok(self, args, value):
        """Validate a Scheme successfully."""
        sch = scheme.Scheme(*args)
        sch.validate(value)

    @pytest.mark.parametrize(
        'args,value', [
            (
                # option does not exist in config, no default
                (scheme.Option('foo', field_type=str),),
                {}
            ),
            (
                # option exists in config, fails validation
                (scheme.Option('foo', default='bar', field_type=str),),
                {'foo': 1}
            ),
            (
                # multiple args, one fails validation
                (
                    scheme.Option('foo', field_type=str),
                    scheme.Option('bar', field_type=int),
                    scheme.Option('baz', choices=['test'])
                ),
                {'foo': 'a', 'bar': 1, 'baz': 'something'}
            )
        ]
    )
    def test_validate_failure(self, args, value):
        """Validate a Scheme unsuccessfully."""
        sch = scheme.Scheme(*args)
        with pytest.raises(errors.SchemeValidationError):
            sch.validate(value)

    @pytest.mark.parametrize(
        'value', [
            'foo',
            1,
            1.23,
            ['a', 'b', 'c'],
            {'a', 'b', 'c'},
            ('a', 'b', 'c'),
            None,
            False,
            True
        ]
    )
    def test_validate_failure_bad_config(self, value):
        """Validate a Scheme where the given config is not a dict."""
        sch = scheme.Scheme()
        with pytest.raises(errors.SchemeValidationError):
            sch.validate(value)
