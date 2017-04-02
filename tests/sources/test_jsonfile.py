# -*- coding: utf-8 -*-

import json

import pytest

from layeredconfig import JsonFile


@pytest.fixture
def json_file(tmpdir, data):
    path = tmpdir / 'config.json'

    def loader(self):
        return json.loads(self.path.read())

    def writer(self, data):
        self.path.write(json.dumps(data))

    test_file = pytest.helpers.DAL(path=path, _load_data=loader,
                                   _write_data=writer)
    test_file.data = data
    return test_file


def test_lazy_read_json_source(json_file):
    config = JsonFile(str(json_file.path))

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


def test_write_json_source(json_file):
    config = JsonFile(str(json_file.path))
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
