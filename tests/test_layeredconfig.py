# -*- coding: utf-8 -*-

import mvp


def test_layered_config():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7
