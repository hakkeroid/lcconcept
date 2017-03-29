# -*- coding: utf-8 -*-

import pytest

import mvp


def test_lazy_read_environment_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = mvp.Environment(prefix='MVP_')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}
