# -*- coding: utf-8 -*-

import io

import pytest

import mvp


def test_layered_config():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7


def test_layered_config():
    typed_source = {'a': 1, 'b': {'c': 2}}
    untyped_source = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=10

        [b]
        c=20

        [b.d]
        e=30
    """))
    typed = mvp.DictSource(typed_source)
    untyped = mvp.INIFile(untyped_source, subsection_token='.')
    config = mvp.LayeredConfig(typed, untyped)

    assert typed.a == 1
    assert typed.b.c == 2
    with pytest.raises(KeyError):
        typed.b.d.e

    assert untyped.a == '10'
    assert untyped.b.c == '20'
    assert untyped.b.d.e == '30'

    assert config.a == 10
    assert config.b.c == 20
    assert config.b.d.e == '30'
