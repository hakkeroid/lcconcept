# -*- coding: utf-8 -*-

import pytest

import mvp


@pytest.fixture
def connector():
    class Connector:
        """Simple etcd connector"""

        def __init__(self):
            self.get_data = {}
            self.set_data = {}

        @pytest.helpers.inspector
        def get(self, *args, **kwargs):
            return self.get_data

        @pytest.helpers.inspector
        def set(self, *items):
            self.set_data.update(items)

    connector = Connector()
    connector.get_data = {
        'node': {
            'nodes': [{
                'key': 'a',
                'value': '1'
             }, {
                'key': 'b',
                'dir': True,
                'nodes': [{
                    'key': 'c',
                    'value': '2'
                }, {
                    'key': 'd',
                    'dir': True,
                    'nodes': [{
                        'key': 'e',
                        'value': '3'
                    }]
                }]
            }]
        }
    }
    return connector


@pytest.mark.parametrize('key', ['/', '/a'])
def test_etcd_connector_get_data(monkeypatch, key):
    url = 'http://fake-url:2379'
    connector = mvp.EtcdConnector(url)

    class Response(object):
        def json(self):
            return {}

    def get(*args, **kwargs):
        assert url + '/keys' + key == args[0]
        assert 'recursive' in kwargs['params']
        return Response()

    monkeypatch.setattr('mvp.EtcdConnector.requests.get', get)
    connector.get(key)


@pytest.mark.parametrize('key, value', [
    ('/a', 1),
    ('/b', 2),
])
def test_etcd_connector_set_data(monkeypatch, key, value):
    url = 'http://fake-url:2379'
    connector = mvp.EtcdConnector(url)

    def put(*args, **kwargs):
        assert url + '/keys' + key == args[0]
        assert value == kwargs['data']['value']

    monkeypatch.setattr('mvp.EtcdConnector.requests.put', put)
    connector.set((key, value))


def test_lazy_read_etcd_source(connector):
    config = mvp.EtcdStore('bogus-url')
    config._connector = connector

    # etcd is untyped
    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}
    assert config._connector.get.calls == 1

    config._use_cache = False
    config.a

    assert config._connector.get.calls == 2


def test_write_etcd_source(connector):
    config = mvp.EtcdStore('bogus-url')
    config._connector = connector

    config.a = '10'
    config.b.c = '20'
    config.b.d.e = '30'
    config.save()

    data = connector.set_data
    assert data['/a'] == '10'
    assert data['/b/c'] == '20'
    assert data['/b/d/e'] == '30'