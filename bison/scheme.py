# -*- coding: utf-8 -*-
"""
bison.scheme
~~~~~~~~~~~~

This module defines the `Scheme`, which is used by `Bison`
in order to do configuration defaults and validation. A
`Scheme` is composed of various options, which are defined
here as well.
"""

from bison import errors


class NoDefault:
    """Defines a "no default" type.

    This is used in place of `None` in an options' `default` field, since
    `None` is a valid default value, so checking the presence/absence of
    a default value cannot be a NoneType check.
    """


# global _NoDefault instance to use as the default value for options.
_no_default = NoDefault()


class Scheme(object):
    """The `Scheme` specifies the expected options for a configuration.

    It provides the template for what is expected when parsing and building
    configuration state. Additionally, it allows the user to specify default
    values for various fields. The `Scheme` allows for validation across all
    specified options, to the extent that the constraints are specified on
    those options.
    """

    def __init__(self, *args):
        self.args = args
        self._flat = None

    def build_defaults(self):
        """Build a dictionary of default values from the `Scheme`.

        Returns:
            dict: The default configurations as set by the `Scheme`.

        Raises:
            errors.InvalidSchemeError: The `Scheme` does not contain
                valid options.
        """
        defaults = {}
        for arg in self.args:
            if not isinstance(arg, _BaseOpt):
                raise errors.InvalidSchemeError('')

            # if there is a default set, add it to the defaults dict
            if not isinstance(arg.default, NoDefault):
                defaults[arg.name] = arg.default

            # if we have a dict option, build the defaults for its scheme.
            # if any defaults exist, use them.
            if isinstance(arg, DictOption):
                b = arg.scheme.build_defaults()
                if b:
                    defaults[arg.name] = b
        return defaults

    def flatten(self):
        """Flatten the scheme into a dictionary where the keys are
        compound 'dot' notation keys, and the values are the corresponding
        options.

        Returns:
            dict: The flattened `Scheme`.
        """
        if self._flat is None:
            flat = {}
            for arg in self.args:
                if isinstance(arg, Option):
                    flat[arg.name] = arg

                elif isinstance(arg, ListOption):
                    flat[arg.name] = arg

                elif isinstance(arg, DictOption):
                    flat[arg.name] = DictOption
                    for k, v in arg.scheme.flatten().items():
                        flat[arg.name + '.' + k] = v

            self._flat = flat
        return self._flat

    def validate(self, config):
        """Validate the given config against the `Schema`.

        Args:
            config (dict): The configuration to validate.

        Raises:
            errors.SchemeValidationError: The configuration fails
                validation against the `Schema`.
        """
        if not isinstance(config, dict):
            raise errors.SchemeValidationError(
                'Scheme can only validate a dictionary config, but was given '
                '{} (type: {})'.format(config, type(config))
            )

        for arg in self.args:
            # the option exists in the config
            if arg.name in config:
                arg.validate(config[arg.name])

            # the option does not exist in the config
            else:
                # if the option has a default value, then it is
                # considered optional and is fine to omit, otherwise
                # it is considered to be required and its omission
                # is a validation error.
                if type(arg.default) == NoDefault:
                    raise errors.SchemeValidationError(
                        'Option "{}" is expected but not found.'.format(arg.name)
                    )


class _BaseOpt(object):
    """Base class for all scheme options"""

    def __init__(self):
        self.name = None
        self.default = NoDefault

    def validate(self, value):
        """Validate that the option constraints are met by the configuration.

        Args:
            value: The value corresponding with the option.

        Raises:
            errors.SchemeValidationError: The option failed validation.
        """
        raise NotImplementedError


class Option(_BaseOpt):
    """Option represents a configuration option with a singular value.

    For YAML, this would be a single k:v pair, e.g.

        debug: True

    The above could be represented by the following:

        Option('debug', field_type=bool)

    Args:
        name (str): The name of the option - this should correspond to the key
            for the option in a configuration file, e.g.
        default: The default value to use. By default, this is the internal
            `_NoDefault` type. If the value of this is anything other than
            `_NoDefault`, this option is considered optional, so validation will
            not fail if it is not present in the config. If this is left at its
            default value of `_NoDefault`, then this option is considered required
            and will fail validation if not present.
        field_type: The type that the option value should have.
        choices (list|tuple): The valid options for the field.
        bind_env (bool|str|None): Bind the option to an environment variable.
    """

    def __init__(self, name, default=_no_default, field_type=None, choices=None, bind_env=None):
        super(Option, self).__init__()
        self.name = name
        self.default = default
        self.type = field_type
        self.choices = choices
        self.bind_env = bind_env

    def validate(self, value):
        if (self.type is not None) and (type(value) != self.type):
            raise errors.SchemeValidationError(
                '{} is of type {}, but should be {}'.format(value, type(value), self.type)
            )
        if (self.choices is not None) and (value not in self.choices):
            raise errors.SchemeValidationError(
                '{} is not in the valid options: {}'.format(value, self.choices)
            )


class DictOption(_BaseOpt):
    """DictOption represents a configuration option with a dictionary value.

    For YAML, this would be a k:v pair where the value is a map, e.g.

        some_key:
          nested_key: value

    The above could be represented by the following:

        DictOption('some_key', scheme=Scheme(
            Option('nested_key')
        ))

    Args:
        name (str): The name of the option - this should correspond to the key
            for the option in a configuration file, e.g.
        scheme (Scheme|None): A Scheme that defines what the dictionary config should
            adhere to. This can be None if no validation is wanted on the option.
        default: The default value to use. By default, this is the internal
            `_NoDefault` type. If the value of this is anything other than
            `_NoDefault`, this option is considered optional, so validation will
            not fail if it is not present in the config. If this is left at its
            default value of `_NoDefault`, then this option is considered required
            and will fail validation if not present.
        bind_env (bool): Bind the option to an environment variable.
    """

    def __init__(self, name, scheme, default=_no_default, bind_env=False):
        super(DictOption, self).__init__()
        self.name = name
        self.default = default
        self.scheme = scheme
        self.bind_env = bind_env

    def validate(self, value):
        if not isinstance(value, dict):
            raise errors.SchemeValidationError('{} is not a dictionary'.format(value))

        if isinstance(self.scheme, Scheme):
            self.scheme.validate(value)


class ListOption(_BaseOpt):
    """ListOption represents a configuration option with a list value.

    For YAML, this would be a k:v pair where the value is a list, e.g.

        animals:
          - bison
          - buffalo

    The above could be represented by the following:

        ListOption('animals', member_type=str)

    Args:
        name (str): The name of the option - this should correspond to the key
            for the option in a configuration file, e.g.
        default: The default value to use. By default, this is the internal
            `_NoDefault` type. If the value of this is anything other than
            `_NoDefault`, this option is considered optional, so validation will
            not fail if it is not present in the config. If this is left at its
            default value of `_NoDefault`, then this option is considered required
            and will fail validation if not present.
        member_type: The type that all members of the list should have.
        member_scheme (Scheme): The `Scheme` that all members of the list should
            fulfil. This should be used when the list members are dictionaries/maps.
        bind_env (bool): Bind the option to an environment variable.
    """

    def __init__(self, name, default=_no_default, member_type=None, member_scheme=None, bind_env=False):
        super(ListOption, self).__init__()
        self.name = name
        self.default = default
        self.member_type = member_type
        self.member_scheme = member_scheme
        self.bind_env = bind_env

    def validate(self, value):
        if not isinstance(value, list):
            raise errors.SchemeValidationError('{} is not a list'.format(value))

        if self.member_scheme is not None and self.member_type is not None:
            raise errors.SchemeValidationError(
                'Cannot specify both a member_type and a member_scheme.'
            )

        if self.member_type is not None:
            for item in value:
                if type(item) != self.member_type:
                    raise errors.SchemeValidationError(
                        'Members in "{}" option are not of type {}'.format(self.name, self.member_type)
                    )

        if self.member_scheme is not None:
            if not isinstance(self.member_scheme, Scheme):
                raise errors.SchemeValidationError(
                    'Specified member scheme is not an instance of a Scheme.'
                )

            for item in value:
                self.member_scheme.validate(item)
