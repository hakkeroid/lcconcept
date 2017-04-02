# -*- coding: utf-8 -*-

import io

import pytest

from layeredconfig import INIFile


def test_ini_source():
    inifile = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1

        [b]
        c=2

        [b.d]
        e=%(interpolated)s
        interpolated=3

        [b/d/f]
        g=4
    """))

    config = INIFile(inifile)
    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_ini_source_subsections():
    inifile = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1

        [b]
        c=2

        [b.d]
        e=%(interpolated)s
        interpolated=3

        [b/d/f]
        g=4
    """))

    config = INIFile(inifile, subsection_token='.')
    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d.e == '3'
    assert config['b/d/f'].g == '4'


