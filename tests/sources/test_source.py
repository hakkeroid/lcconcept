# -*- coding: utf-8 -*-

import pytest

from layeredconfig import DictSource, CustomType
from layeredconfig.source import Source


def test_enforce_read_method():
    with pytest.raises(NotImplementedError) as exc_info:
        class MySource(Source):
            pass

    assert 'required "_read"' in str(exc_info.value)


def test_read_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    assert config['a'] == 1
    assert config['b'].c == 2
    assert config.b['d'] == {'e': 3}

    # test lazy read
    data['a'] = 10
    data['b']['c'] = 20
    data['b']['d']['e'] = 30

    assert config.a == 10
    assert config.b.c == 20
    assert config.b.d == {'e': 30}


def test_write_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.a = 10
    config.b.c = 20
    del config.b.d.e

    assert config.a == 10
    assert config.b.c == 20
    with pytest.raises(KeyError):
        config.b.d.e


def test_prevent_writing_to_readonly_source():
    class ReadonlySource(Source):
        def _read(self):
            return {}

    config = ReadonlySource()

    with pytest.raises(TypeError) as exc_info:
        config.a = 10

    assert 'read-only source' in str(exc_info.value)


def test_prevent_writing_to_locked_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data, readonly=True)

    with pytest.raises(TypeError) as exc_info:
        config.a = 10

    assert 'locked' in str(exc_info.value)


def test_source_get():
    config = DictSource({'a': 1})

    assert config.get('a') == 1
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'
    assert 'nonexisting' not in config


def test_source_items():
    data = {'a': {'b': 1}}
    config = DictSource(data)

    items = [i for i in config.a.items()]
    assert items == [('b', 1)]


def test_source_setdefault():
    config = DictSource({'a': 1})

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10


@pytest.mark.parametrize('container', [
    dict, DictSource
])
def test_source_update(container):
    source = {'a': {'b': 1}}
    config = DictSource(source)

    data1 = {'x': 4}
    data2 = container({'y': 5})
    expected = {'a': {'b': 1, 'x': 4, 'y': 5}}

    config.a.update(data1, data2)

    assert config == expected


def test_source_with_custom_types():
    data = {'a': 1, 'b': {'c': 2}}
    types = {
        'a': CustomType(customize=str, reset=int),
        'c': CustomType(lambda v: 2*v, lambda v: v/2)
    }
    config = DictSource(data, type_map=types)

    assert config.a == '1'
    assert config.b.c == 4

    assert config.dump() == data
    assert config.dump(with_custom_types=True) == {'a': '1', 'b': {'c': 4}}


def test_read_cached_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data, cached=True)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    # test cached access
    data['a'] = 10
    data['b']['c'] = 20
    data['b']['d']['e'] = 30

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}


def test_write_cached_dict_source():
    config = DictSource({}, cached=True)

    config.a = 1
    config.b = {}
    config.b.c = 2
    config.b.d = {}
    config.b.d.e = 3

    assert config._data == {}

    config.write_cache()

    assert config._data == {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
