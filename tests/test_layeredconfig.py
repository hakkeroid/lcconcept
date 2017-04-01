# -*- coding: utf-8 -*-

import io

import pytest

import mvp


def test_raise_keyerrors_on_empty_multilayer_config():
    config = mvp.LayeredConfig()
    with pytest.raises(KeyError):
        assert config.a

def test_properly_return_none_values():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': None})
    )

    assert config.a is None


def test_read_layered_sources():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7

    assert config['a'] == 1
    assert config['b'].c == 2
    assert config.b['y'] == 7


def test_layered_len():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert len(config) == 3


def test_write_layered_source():
    source1 = mvp.DictSource({'a': 1, 'b': {'c': 2}})
    source2 = mvp.DictSource({'x': 6, 'b': {'y': 7}})
    config = mvp.LayeredConfig(source1, source2)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7

    config.a = 10
    config['x'] = 60
    config['b'].c = 20
    config.b['y'] = 70

    assert config.a == 10
    assert config.x == 60
    assert config.b.c == 20
    assert config.b.y == 70

    assert source1.a == 10
    assert source1.b.c == 20

    assert source2.x == 60
    assert source2.b.y == 70


def test_layered_get():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.get('a') == 1
    assert config.get('x') == 6
    assert config.get('b').get('c') == 2
    assert config.get('b').get('y') == 7
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'
    assert 'nonexisting' not in config


def test_source_items():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'a': '10'}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    items = list(config.items())
    assert items == [('a', '10'), ('b', config.b), ('x', 6)]

    items = list(config.b.items())
    assert items == [('c', 2), ('y', 7)]


def test_layered_dump():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'a': '10'}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.dump() == {'a': '10', 'b': {'c': 2, 'y': 7}, 'x': 6}


def test_layered_setdefault():
    source1 = mvp.DictSource({'a': 1, 'b': {'c': 2}})
    source2 = mvp.DictSource({'x': 6, 'b': {'y': 7}})
    config = mvp.LayeredConfig(source1, source2)

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10
    assert 'nonexisting' in source2

    assert config.b.setdefault('nonexisting', 20) == 20
    assert config.b.nonexisting == 20
    assert 'nonexisting' in source2.b


@pytest.mark.parametrize('container', [
    dict, mvp.DictSource
])
def test_layered_simple_update(container):
    source1 = mvp.DictSource({'a': 1, 'b': {'c': 2}})
    source2 = mvp.DictSource({'x': 6, 'b': {'y': 7}})
    config = mvp.LayeredConfig(source1, source2)

    data1 = container({'a': 10, 'x': 60})
    data2 = container({'c': 20})
    data3 = container({'y': 70})

    config.update(data1)
    config.b.update(data2, data3)

    assert config.a == 10
    assert config.x == 60
    assert config.b.c == 20
    assert config.b.y == 70

    assert source1.a == 10
    assert source1.b.c == 20

    assert source2.x == 60
    assert source2.b.y == 70


def test_layered_config_with_untyped_source():
    typed_source = {'a': 1, 'b': {'c': 2}}
    untyped_source1 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=11
    """))
    untyped_source2 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=10

        [b]
        c=20

        [b.d]
        e=30
    """))
    typed = mvp.DictSource(typed_source)
    untyped1 = mvp.INIFile(untyped_source1)
    untyped2 = mvp.INIFile(untyped_source2, subsection_token='.')
    config = mvp.LayeredConfig(typed, untyped1, untyped2)

    assert typed.a == 1
    assert typed.b.c == 2
    with pytest.raises(KeyError):
        typed.b.d.e

    assert untyped1.a == '11'

    assert untyped2.a == '10'
    assert untyped2.b.c == '20'
    assert untyped2.b.d.e == '30'

    assert config.a == 10
    assert config.b.c == 20
    assert config.b.d.e == '30'

    # assert config.dump()
