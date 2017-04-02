# -*- coding: utf-8 -*-

import pytest

from layeredconfig import Environment


def test_read_environment_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = Environment(prefix='MVP_')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}


def test_write_environment_fails(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    config = Environment(prefix='MVP_', readonly=True)

    with pytest.raises(TypeError) as exc_info:
        config.a = 10
    assert 'locked' in str(exc_info.value)


def test_write_environment_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = Environment(prefix='MVP_')

    config.a = 10
    config.b.c = '20'
    config.b['d'].e = '30'

    assert config.a == '10'  # looses typing information
    assert config.b.c == '20'
    assert config.b.d == {'e': '30'}
