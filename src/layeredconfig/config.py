# -*- coding: utf-8 -*-

from collections import defaultdict, deque

from .source import Source


class LayeredConfig(object):
    """Multi layer config object"""

    _initialized = False

    def __init__(self, *sources, **kwargs):
        self._source_list = sources
        self._strategy_map = kwargs.get('strategies', {})

        # _keychain is a list of keys that led from the root
        # config to this (sub)config
        self._keychain = kwargs.get('keychain', [])
        self._initialized = True

    @property
    def _sources(self):
        """Return the sublevels of the sources according to the keychain"""
        for source in reversed(self._source_list):
            traversed_source = source
            for key in self._keychain:
                traversed_source = traversed_source[key]
            yield source, traversed_source

    @property
    def _typed_sources(self):
        for source in reversed(self._source_list):
            if not source.is_typed():
                continue
            traversed_source = source
            for key in self._keychain:
                traversed_source = traversed_source[key]
            yield source, traversed_source

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def items(self):
        def _items():
            subqueues = defaultdict(deque)

            yielded = set()
            results = {}

            for root_source, source in self._sources:
                for key, value in source.items():
                    # identical keys from different sources that have
                    # dicts as values needs to be merged
                    if isinstance(value, dict):
                        # higher prio sources might override keys with
                        # simple values that otherwise point to subsections
                        if key in yielded:
                            msg = ("The key '%s' from '%s' specifies a"
                                   " subsection as value which conflicts"
                                   " with a higher prioritized source"
                                   " that wants the same value to be a"
                                   " non-sectional instead")
                            raise ValueError(msg % (key,
                                root_source._meta.source_name))
                        subqueues[key].appendleft(root_source)
                        continue

                    if key in subqueues:
                        msg = ("The key '%s' from '%s' specifies a"
                               " non-sectional value which conflicts"
                               " with a higher prioritized source"
                               " that wants the same value to be a"
                               " subsection instead.")
                        raise ValueError(msg % (key,
                            root_source._meta.source_name))

                    if not source.is_typed():
                        value = self._get_typed_value(key, value)

                    # all other identical keys will shadow
                    # subsequent keys
                    if key in self._strategy_map:
                        strategy = self._strategy_map[key]
                        results[key] = strategy(value, results.get(key))
                    elif key in yielded:
                        continue
                    else:
                        yield key, value
                        yielded.add(key)

            for key, value in results.items():
                yield key, value

            for key, subqueue in subqueues.items():
                yield key, self._make_subconfig(subqueue, key)

        return sorted(_items())

    def setdefault(self, name, value):
        try:
            return self[name]
        except KeyError:
            self[name] = value
            return value

    def update(self, *others):
        for other in others:
            for key, value in other.items():
                self[key] = value

    def dump(self):
        def _dump(obj):
            for key, value in obj.items():
                if isinstance(value, LayeredConfig):
                    yield key, dict(_dump(value))
                else:
                    yield key, value

        return dict(_dump(self))

    def _get_typed_value(self, key, value):
        for root_source, source in self._typed_sources:
            try:
                typed_value = source[key]
            except KeyError:
                continue

            type_info = self._get_type_info(typed_value)
            return self._convert_value_to_type(value, type_info)
        return value

    def _get_type_info(self, value):
        return type(value)

    def _convert_value_to_type(self, value, type_info):
        return type_info(value)

    def _make_subconfig(self, sources, key):
        return LayeredConfig(*sources,
                             keychain=self._keychain+[key],
                             strategies=self._strategy_map
                             )

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        # will be used as input for a new sublevel config with the
        # key added to the keychain.
        subqueue = deque()

        strategy = self._strategy_map.get(key)
        result = None

        for root_source, source in self._sources:
            try:
                value = source[key]
            except KeyError:
                continue

            if isinstance(value, Source):
                subqueue.appendleft(root_source)
                continue

            if not source.is_typed():
                value = self._get_typed_value(key, value)

            if strategy:
                result = strategy(value, result)
            else:
                return value

        # in the while loop we always ended up in any of the continue
        # statements which means either the key was not found or the key
        # is a sublevel source or it is untyped.
        if result:
            return result
        elif subqueue:
            return self._make_subconfig(subqueue, key)
        else:
            raise KeyError("Key '%s' was not found" % key)

    def __setattr__(self, attr, value):
        self[attr] = value

    def __setitem__(self, key, value):
        if any([self._initialized is False,
                key == '_initialized',
                key in self.__dict__,
                key in LayeredConfig.__dict__]):
            super(LayeredConfig, self).__setattr__(key, value)
        else:
            # will be used if the key could not be found in any source
            # which means that a new key/value shall be added to the
            # config.
            writable_source = None

            for root_source, source in self._sources:
                if writable_source is None and root_source._writable:
                    writable_source = source

                if key in source:
                    source[key] = value
                    return

            # no source was found so write it to first writable source
            if writable_source:
                writable_source[key] = value
            else:
                raise TypeError('No writable sources found')

    def __eq__(self, other):
        return self.dump() == other.dump()

    def __len__(self):
        return len(list(iter(self)))

    def __iter__(self):
        yielded = set()

        for root_source, source in self._sources:
            for key in source:
                if key not in yielded:
                    yielded.add(key)
                    yield key

    def __repr__(self):
        return repr(self.dump())
