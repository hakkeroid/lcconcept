# -*- coding: utf-8 -*-

import io

import pytest

import mvp


@pytest.fixture
def defaults():
    return {
        'home': 'mydata',
        'processes': 4,
        'force': True,
        'extra': ['foo', 'bar'],
        'mymodule': {
            'force': False,
            'extra': ['foo', 'baz'],
            'arbitrary': {
                'nesting': {
                    'depth': 'works'
                }
            }
        },
        'extramodule': {
            'unique': True
        }
    }


@pytest.mark.xfail
def test_read(defaults):
    additional = {
        'home': 'thisdata',
        'mymodule': {
            'force': True,
            'arbitrary': {
                'my_data': True
            }
        },
    }
    inifile = io.BytesIO(unindent("""
        [__root__]
        force=True
        home=/some/path
        other=test

        [mymodule]
        more=stuff
    """))
    defaults['home'] = 'thisdata'
    defaults['mymodule']['force'] = True
    defaults['mymodule']['arbitrary']['my_data'] = True

    config = mvp.Config(
        mvp.Source(defaults),
        mvp.INISource(inifile),
        mvp.Source(additional)
    )

    assert config.mymodule.arbitrary.nesting.depth
    assert defaults == config.dump()


@pytest.mark.xfail
def test_write(defaults):
    source = mvp.Source(defaults)
    config = mvp.Config(source)

    config.home = 'otherdata'
    config.write()
