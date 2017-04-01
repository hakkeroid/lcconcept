# -*- coding: utf-8 -*-

import pytest

import mvp


def test_read_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = mvp.DictSource(data)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}


def test_source_get():
    config = mvp.DictSource({'a': 1})

    assert config.get('a') == 1
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'


def test_source_setdefault():
    config = mvp.DictSource({'a': 1})

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10


@pytest.mark.parametrize('container', [
    dict, mvp.DictSource
])
def test_source_update(container):
    source = {'a': {'b': 1}}
    config = mvp.DictSource(source)

    data1 = {'x': 4}
    data2 = container({'y': 5})
    expected = {'a': {'b': 1, 'x': 4, 'y': 5}}

    config.a.update(data1, data2)

    assert config == expected


def test_source_items():
    data = {'a': {'b': 1}}
    config = mvp.DictSource(data)

    items = [i for i in config.a.items()]
    assert items == [('b', 1)]


def test_source_with_custom_types():
    data = {'a': 1, 'b': {'c': 2}}
    types = {
        'a': mvp.CustomType(customize=str, reset=int),
        'c': mvp.CustomType(lambda v: 2*v, lambda v: v/2)
    }
    config = mvp.DictSource(data, type_map=types)

    assert config.a == '1'
    assert config.b.c == 4

    assert config.dump() == data
    assert config.dump(with_custom_types=True) == {'a': '1', 'b': {'c': 4}}
