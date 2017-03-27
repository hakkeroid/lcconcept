# -*- coding: utf-8 -*-

import pytest
import requests

import mvp


@pytest.fixture(params=[{
    'a': 1,
    'b/c': 2,
    'b/d/e': 3,
}])
def etcd_store(request):
    url = "http://127.0.0.1:2379/v2"

    def loader(self):
        result = requests.get(self.url + '/keys',
                              params={'recursive': True,
                                      'sorted': True})
        return result.json()['node']

    def writer(self, data):
        for key, value in data.items():
            requests.put('/'.join([self.url, 'keys', key]),
                         data={'value': value})

    test_store = pytest.helpers.DAL(url=url, _load_data=loader,
                                    _write_data=writer)
    test_store.data = request.param
    yield test_store

    for key in ['a', 'b']:
        requests.delete('/'.join([url, 'keys', key]),
                        params={'recursive': True})


def test_etcd_connector(etcd_store, data):
    etcd = mvp.EtcdConnector(etcd_store.url)
    expected = {
        'a': '1',
        'b': {
            'c': '2',
            'd': {
                'e': '3',
            }
        },
        'x': {
            'y': '4'
        }
    }

    etcd.set({'x': {'y': 4}})
    assert etcd.get() == expected

    etcd.flush()
    assert not etcd.get()


def test_lazy_read_etcd_source(etcd_store):
    config = mvp.EtcdStore(etcd_store.url)
    config._connector._request = pytest.helpers.call_count(
        config._connector._request)

    # etc is untyped
    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}
    assert config._connector._request.calls == 1

    config._use_cache = False
    config.a

    assert config._connector._request.calls == 2


def test_write_etcd_source(etcd_store):
    config = mvp.EtcdStore(etcd_store.url)
    config._connector._request = pytest.helpers.call_count(
        config._connector._request)

    expected = etcd_store.data
    expected['a'] = 10
    expected['b/c'] = 20
    expected['b/d/e'] = 30

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}

    config.a = '10'
    config.b.c = '20'
    config.b.d.e = '30'
    config.save()

    data = etcd_store.data
    assert data['nodes'][0]['value'] == '10'
    assert data['nodes'][1]['nodes'][0]['value'] == '20'
    assert data['nodes'][1]['nodes'][1]['nodes'][0]['value'] == '30'
