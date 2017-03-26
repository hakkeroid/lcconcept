# -*- coding: utf-8 -*-

import io
import collections
import copy
import json
import yaml
import functools

import pytest
import mvp

def unindent(text):
    return '\n'.join([line.lstrip() for line in text.split('\n')])


def test_ini_source():
    inifile = io.StringIO(unindent(u"""
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

    config = mvp.INIFile(inifile)
    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_ini_source_subsections():
    inifile = io.StringIO(unindent(u"""
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

    config = mvp.INIFile(inifile, subsection_token='.')
    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d.e == '3'
    assert config['b/d/f'].g == '4'


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


def test_layered():
    config = mvp.LayeredConfig(
        mvp.DictSource({'a': 1, 'b': {'c': 2}}),
        mvp.DictSource({'x': 6, 'b': { 'y': 7}})
    )

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7


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


class DAL(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def data(self):
        return self._load_data(self)

    @data.setter
    def data(self, data):
        self._write_data(self, data)


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


@pytest.fixture
def json_file(tmpdir, data):
    path = tmpdir / 'config.json'

    def loader(self):
        return json.loads(self.path.read())

    def writer(self, data):
        self.path.write(json.dumps(data))

    test_file = DAL(path=path, _load_data=loader, _write_data=writer)
    test_file.data = data
    return test_file


@pytest.fixture
def yaml_file(tmpdir, data):
    path = tmpdir / 'config.yml'

    def loader(self):
        return yaml.load(self.path.read())

    def writer(self, data):
        self.path.write(yaml.dump(data))

    test_file = DAL(path=path, _load_data=loader, _write_data=writer)
    test_file.data = data
    return test_file


@pytest.fixture(params=[{
    'a': 1,
    'b/c': 2,
    'b/d/e': 3,
}])
def etcd_store(request):
    import requests
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

    test_store = DAL(url=url, _load_data=loader, _write_data=writer)
    test_store.data = request.param
    yield test_store

    for key in ['a', 'b']:
        requests.delete('/'.join([url, 'keys', key]),
                        params={'recursive': True})


def call_count(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return fn(*args, **kwargs)
    wrapper.calls = 0
    return wrapper


def test_etc(etcd_store, data):
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


def test_lazy_read_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = mvp.DictSource(data)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}


def test_source_get():
    config = mvp.DictSource({'a': 1})

    assert config.get('a') == 1
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'


def test_source_setdefault():
    config = mvp.DictSource({'a': 1})

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10


@pytest.mark.parametrize('container', [
    dict, mvp.DictSource
])
def test_source_update(container):
    source = {'a': {'b': 1}}
    config = mvp.DictSource(source)

    data1 = {'x': 4}
    data2 = container({'y': 5})
    expected = {'a': {'b': 1, 'x': 4, 'y': 5}}

    config.a.update(data1, data2)

    assert config == expected


def test_source_items():
    data = {'a': {'b': 1}}
    config = mvp.DictSource(data)

    assert config.a.items() == [('b', 1)]


def test_lazy_read_json_source(json_file):
    config = mvp.JsonFile(str(json_file.path))

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    before = config.b.c

    expected = json_file.data
    expected['b']['c'] = 20
    json_file.data = expected

    after = config.b.c

    assert before == 2
    assert after == 20


def test_lazy_read_yaml_source(yaml_file):
    config = mvp.YamlFile(str(yaml_file.path))

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    before = config.b.c

    expected = yaml_file.data
    expected['b']['c'] = 20
    yaml_file.data = expected

    after = config.b.c

    assert before == 2
    assert after == 20


def test_lazy_read_etcd_source(etcd_store):
    config = mvp.EtcdStore(etcd_store.url)
    config._connector._request = call_count(config._connector._request)

    # etc is untyped
    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}
    assert config._connector._request.calls == 1

    config._use_cache = False
    config.a

    assert config._connector._request.calls == 2


def test_write_json_source(json_file):
    config = mvp.JsonFile(str(json_file.path))
    expected = json_file.data
    expected['a'] = 10
    expected['b']['c'] = 20
    expected['b']['d']['e'] = 30

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.a = 10
    config.b.c = 20
    config.b.d.e = 30

    result = json.loads(json_file.path.read())
    assert result == expected


def test_write_yaml_source(yaml_file):
    config = mvp.YamlFile(str(yaml_file.path))
    expected = yaml_file.data
    expected['a'] = 10
    expected['b']['c'] = 20
    expected['b']['d']['e'] = 30

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.a = 10
    config.b.c = 20
    config.b.d.e = 30

    result = yaml.load(yaml_file.path.read())
    assert result == expected


def test_write_etcd_source(etcd_store):
    config = mvp.EtcdStore(etcd_store.url)
    config._connector._request = call_count(config._connector._request)

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
