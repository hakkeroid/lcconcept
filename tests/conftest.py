# -*- coding: utf-8 -*-

pytest_plugins = ['helpers_namespace']

import functools

import pytest


@pytest.fixture
def data():
    return {
        'a': 1,
        'b': {
            'c': 2,
            'd': {
                'e': 3
            }
        }
    }


@pytest.helpers.register
class DAL(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def data(self):
        return self._load_data(self)

    @data.setter
    def data(self, data):
        self._write_data(self, data)


@pytest.helpers.register
def inspector(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        #wrapper.args = args
        #wrapper.kwargs = kwargs
        return fn(*args, **kwargs)
    wrapper.calls = 0
    wrapper.args = None
    wrapper.kwargs = None
    return wrapper


@pytest.helpers.register
def unindent(text):
    return '\n'.join([line.lstrip() for line in text.split('\n')])
