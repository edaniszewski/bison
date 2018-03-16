# -*- coding: utf-8 -*-
"""
bison.utils
~~~~~~~~~~~

Utilities for `bison`.
"""

import collections


def build_dot_value(key, value):
    """Build new dictionaries based off of the dot notation key.

    For example, if a key were 'x.y.z' and the value was 'foo',
    we would expect a return value of: ('x', {'y': {'z': 'foo'}})

    Args:
        key (str): The key to build a dictionary off of.
        value: The value associated with the dot notation key.

    Returns:
        tuple: A 2-tuple where the first element is the key of
            the outermost scope (e.g. left-most in the dot
            notation key) and the value is the constructed value
            for that key (e.g. a dictionary)
    """
    # if there is no nesting in the key (as specified by the
    # presence of dot notation), then the key/value pair here
    # are the final key value pair.
    if key.count('.') == 0:
        return key, value

    # otherwise, we will need to construct as many dictionaries
    # as there are dot components to hold the value.
    final_value = value
    reverse_split = key.split('.')[::-1]
    end = len(reverse_split) - 1
    for idx, k in enumerate(reverse_split):
        if idx == end:
            return k, final_value
        final_value = {k: final_value}


class DotDict(dict):
    """A dictionary which supports getting and setting with dot notation keys."""

    def __init__(self, dct=None):
        if dct is None:
            dct = {}
        super(DotDict, self).__init__(dct)

    def __getitem__(self, item):
        # x.__getitem__(y) <==> x[y], so this makes x[y] and x.get(y) go
        # through the same code path (e.g. __getattribute__)
        return self.get(item, None)

    def __setitem__(self, key, value):
        # if there are no dots in the key, its a normal set
        if key.count('.') == 0:
            super(DotDict, self).__setitem__(key, value)
            return

        # otherwise, traverse the key components to set the value
        first, remainder = key.split('.', 1)
        if first in self:
            elem = super(DotDict, self).__getitem__(first)
            if isinstance(elem, dict):
                dd = DotDict(elem)
                dd.__setitem__(remainder, value)
                elem.update(dd)
            else:
                k, v = build_dot_value(key, value)
                super(DotDict, self).__setitem__(k, v)

        else:
            k, v = build_dot_value(key, value)
            super(DotDict, self).__setitem__(k, v)

    def __contains__(self, item):
        # if there are no dots in the key, it is a normal contains
        if item.count('.') == 0:
            return super(DotDict, self).__contains__(item)

        # otherwise, traverse the key components to check contains
        first, remainder = item.split('.', 1)
        if first in self:
            v = super(DotDict, self).__getitem__(first)
            if isinstance(v, (dict, DotDict)):
                return DotDict(v).__contains__(remainder)
            return False
        return False

    # ---------------------------------------
    # Public Facing Methods
    # ---------------------------------------

    def get(self, key, default=None):
        """Get a value from the `DotDict`.

        The `key` parameter can either be a regular string key,
        e.g. "foo", or it can be a string key with dot notation,
        e.g. "foo.bar.baz", to signify a nested lookup.

        The default value is returned if any level of the key's
        components are not found.

        Args:
            key (str): The key to get the value for.
            default: The return value should the given key
                not exist in the `DotDict`.
        """
        # if there are no dots in the key, its a normal get
        if key.count('.') == 0:
            return super(DotDict, self).get(key, default)

        # set the return value to the default
        value = default

        # split the key into the first component and the rest of
        # the components. the first component corresponds to this
        # DotDict. the remainder components correspond to any nested
        # DotDicts.
        first, remainder = key.split('.', 1)
        if first in self:
            value = super(DotDict, self).get(first)

            # if the value for the key at this level is a dictionary,
            # then pass the remainder to that DotDict.
            if isinstance(value, (dict, DotDict)):
                return DotDict(value).get(remainder)

            # TODO: support lists

        return value

    def delete(self, key):
        """Remove a value from the `DotDict`.

        The `key` parameter can either be a regular string key,
        e.g. "foo", or it can be a string key with dot notation,
        e.g. "foo.bar.baz", to signify a nested element.

        If the key does not exist in the `DotDict`, it will continue
        silently.

        Args:
            key (str): The key to remove.
        """
        dct = self
        keys = key.split('.')
        last_key = keys[-1]
        for k in keys:
            # if the key is the last one, e.g. 'z' in 'x.y.z', try
            # to delete it from its dict.
            if k == last_key:
                del dct[k]
                break

            # if the dct is a DotDict, get the value for the key `k` from it.
            if isinstance(dct, DotDict):
                dct = super(DotDict, dct).__getitem__(k)

            # otherwise, just get the value from the default __getitem__
            # implementation.
            else:
                dct = dct.__getitem__(k)
                if not isinstance(dct, (DotDict, dict)):
                    raise KeyError(
                        'Subkey "{}" in "{}" invalid for deletion'.format(k, key)
                    )

    def merge(self, source):
        """Merge the dictionary with the values from another dictionary
        (or other DotDict).

        This is preferable to using `update` in some cases. Merging will recursively
        update a dictionary, while updating will just overwrite. As an example, if
        we have the DotDict with the values

            >>> d = DotDict({
            ...   'foo': {
            ...     'bar': True
            ...   }
            ... })
            >>> d
            {'foo': {'bar': True}}

        Then for update, we would get:

            >>> d.update({'foo': {'baz': False}})
            >>> d
            {'foo': {'baz': False}}

        For a merge, we would get:

            >>> d.merge({'foo': {'baz': False}})
            >>> d
            {'foo': {'bar': True, 'baz': False}}

        So, an `update` will replace the specified dictionary, but a `merge` will
        combine the values.

        Args:
            source: The dict/iterable which will be used to update the DotDict.
        """
        _merge(self, source)


def _merge(d, u):
    """Merge two dictionaries (or DotDicts) together.

    Args:
          d: The dictionary/DotDict to merge into.
          u: The source of the data to merge.
    """
    for k, v in u.items():
        # if we have a mapping, recursively merge the values
        if isinstance(v, collections.Mapping):
            d[k] = _merge(d.get(k, {}), v)

        # if d (the dict to merge into) is a dict, just add the
        # value to the dict.
        elif isinstance(d, collections.MutableMapping):
            d[k] = v

        # otherwise if d (the dict to merge into) is not a dict (e.g. when
        # recursing into it, `d.get(k, {})` may not be a dict), then do what
        # `update` does and prefer the new value.
        #
        # this means that something like `{'foo': 1}` when updated with
        # `{'foo': {'bar': 1}}` would have the original value (`1`) overwritten
        # and would become: `{'foo': {'bar': 1}}`
        else:
            d = {k: v}

    return d
