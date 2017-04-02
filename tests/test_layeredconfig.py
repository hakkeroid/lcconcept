# -*- coding: utf-8 -*-

import io

import pytest

from layeredconfig import LayeredConfig
from layeredconfig import DictSource, Environment, INIFile
from layeredconfig import strategy


def test_raise_keyerrors_on_empty_multilayer_config():
    config = LayeredConfig()
    with pytest.raises(KeyError):
        assert config.a


def test_set_keychain():
    config = LayeredConfig(
        DictSource({'a': {'b': {'c': 2}}}),
        keychain=('a', 'b')
    )

    assert config.dump() == {'c': 2}


def test_properly_return_none_values():
    config = LayeredConfig(
        DictSource({'a': None})
    )

    assert config.a is None


def test_read_layered_sources():
    config = LayeredConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7

    assert config['a'] == 1
    assert config['b'].c == 2
    assert config.b['y'] == 7
    assert config.b.d.e == 8


def test_read_complex_layered_sources(monkeypatch):
    monkeypatch.setenv('MVP1_A', 1000)
    monkeypatch.setenv('MVP2_B_M_E', 4000)

    config = LayeredConfig(
        Environment('MVP1_'),  # untyped shadowing
        DictSource({'a': 1, 'b': {'c': 2, 'e': 400}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}}),
        DictSource({'a': 100, 'b': {'m': {'e': 800}}}),     # shadowing
        DictSource({'x': 'x', 'b': {'y': 0.7, 'd': 800}}),  # type changing
        Environment('MVP2_'),  # untyped shadowing
    )

    assert config.a == 100
    assert config.x == 'x'       # changes int to str
    assert config.b.c == 2
    assert config.b.y == 0.7     # changes int to float
    assert config.b.d == 800     # changes subsource (dict) to single value
    assert config.b.e == 400     # 'e' should not be shadowed by other 'e'
    assert config.b.m.e == 4000  # shadowed by untyped but casted to type

    with pytest.raises(AttributeError) as exc_info:
        config.b.d.e
    assert "no attribute 'e'" in str(exc_info.value)

    # config.b.d overrides a dict with a value
    with pytest.raises(ValueError) as exc_info:
        config.b.dump()
    assert "conflicts" in str(exc_info.value)


def test_layered_len():
    config = LayeredConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert len(config) == 3


def test_write_layered_source():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    config = LayeredConfig(source1, source2)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7

    config.a = 10
    config['x'] = 60
    config['b'].c = 20
    config.b['y'] = 70
    config.b['m'] = 'n'  # add new key
    config.b.d.e = 80

    assert config.a == 10
    assert config.x == 60
    assert config.b.c == 20
    assert config.b.y == 70
    assert config.b.m == 'n'
    assert config.b.d.e == 80

    assert source1.a == 10
    assert source1.b.c == 20

    assert source2.x == 60
    assert source2.b.y == 70
    assert source2.b.m == 'n'
    assert source2.b.d.e == 80


@pytest.mark.parametrize('key, message', (
    ('a', 'locked'),
    ('x', 'writable'),
))
def test_write_layered_source_fails(key, message):
    source1 = DictSource({'a': 1, 'b': {'c': 2}}, readonly=True)
    config = LayeredConfig(source1)

    with pytest.raises(TypeError) as exc_info:
        config[key] = 10

    assert message in str(exc_info.value)


def test_layered_get():
    config = LayeredConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert config.get('a') == 1
    assert config.get('x') == 6
    assert config.get('b').get('c') == 2
    assert config.get('b').get('y') == 7
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'
    assert 'nonexisting' not in config


def test_source_items(monkeypatch):
    monkeypatch.setenv('MVP_A', 10)
    config = LayeredConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        Environment('MVP_'),
        DictSource({'x': 6, 'b': {'y': 7}})
    )

    items = list(config.items())
    assert items == [('a', 10), ('b', config.b), ('x', 6)]

    items = list(config.b.items())
    assert items == [('c', 2), ('y', 7)]


@pytest.mark.parametrize('reverse', (1, -1))
def test_source_items_prevent_overriding_subsections_with_values(reverse):
    sources = [
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': 5})
    ]
    config = LayeredConfig(*sources[::reverse])

    with pytest.raises(ValueError) as exc_info:
        list(config.items())
    assert "conflicts" in str(exc_info.value)


def test_source_items_with_strategies_and_untyped_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 100)
    untyped_source = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1000
    """))

    config = LayeredConfig(
        Environment('MVP_'),  # last source still needs a typed source
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        INIFile(untyped_source),
        strategies={
            'a': strategy.add,
            'x': strategy.collect,  # keep lists intact
            'c': strategy.collect,  # collect values into list
            'd': strategy.merge,    # merge lists
        }
    )

    items = list(config.items())
    assert items == [('a', 1111),
                     ('b', config.b),
                     ('x', [[50, 60], [5, 6]])]

    items = list(config.b.items())
    assert items == [('c', [20, 2]),
                     ('d', [30, 40, 3, 4])]


def test_layered_dump():
    config = LayeredConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'a': '10'}),
        DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.dump() == {'a': '10', 'b': {'c': 2, 'y': 7}, 'x': 6}


def test_layered_setdefault():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7}})
    config = LayeredConfig(source1, source2)

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10
    assert 'nonexisting' in source2

    assert config.b.setdefault('nonexisting', 20) == 20
    assert config.b.nonexisting == 20
    assert 'nonexisting' in source2.b


@pytest.mark.parametrize('container', [
    dict, DictSource
])
def test_layered_simple_update(container):
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7}})
    config = LayeredConfig(source1, source2)

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
    typed_source1 = {'x': 5, 'b': {'y': 6}}
    typed_source2 = {'a': 1, 'b': {'c': 2}}
    untyped_source1 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=11
    """))
    untyped_source2 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=10
        x=50

        [b]
        c=20
        y=60

        [b.d]
        e=30
    """))
    typed1 = DictSource(typed_source1)
    typed2 = DictSource(typed_source2)
    untyped1 = INIFile(untyped_source1)
    untyped2 = INIFile(untyped_source2, subsection_token='.')
    config = LayeredConfig(typed1, typed2, untyped1, untyped2)

    assert typed1.x == 5
    assert typed1.b.y == 6

    assert typed2.a == 1
    assert typed2.b.c == 2
    with pytest.raises(KeyError):
        typed2.b.d.e

    assert untyped1.a == '11'

    assert untyped2.a == '10'
    assert untyped2.b.c == '20'
    assert untyped2.b.d.e == '30'

    assert config.a == 10    # found in first typed source
    assert config.x == 50    # found in second typed source
    assert config.b.c == 20
    assert config.b.y == 60
    assert config.b.d.e == '30'


def test_read_layered_sources_with_strategies():
    config = LayeredConfig(
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        strategies={
            'a': strategy.add,
            'x': strategy.collect,  # keep lists intact
            'c': strategy.collect,  # collect values into list
            'd': strategy.merge,    # merge lists
        }
    )

    assert config.a == 11
    assert config.x == [[50, 60], [5, 6]]
    assert config.b.c == [20, 2]
    assert config.b.d == [30, 40, 3, 4]


def test_read_layered_sources_with_strategies_and_untyped_sources(monkeypatch):
    monkeypatch.setenv('MVP_A', 100)
    untyped_source = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1000
    """))

    config = LayeredConfig(
        Environment('MVP_'),  # last source still needs a typed source
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        INIFile(untyped_source),
        strategies= {
            'a': strategy.add,
            'x': strategy.collect,  # keep lists intact
            'c': strategy.collect,  # collect values into list
            'd': strategy.merge,    # merge lists
        }
    )

    assert config.a == 1111
    assert config.x == [[50, 60], [5, 6]]
    assert config.b.c == [20, 2]
    assert config.b.d == [30, 40, 3, 4]
