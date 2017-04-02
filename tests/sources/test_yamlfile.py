# -*- coding: utf-8 -*-

import pytest

from layeredconfig import YamlFile

try:
    import yaml
except:
    # skip all tests when yaml is not installed
    pytestmark = pytest.mark.skip(reason='Missing optional dependencies')


@pytest.fixture
def yaml_file(tmpdir, data):
    import yaml

    path = tmpdir / 'config.yml'

    def loader(self):
        return yaml.load(self.path.read())

    def writer(self, data):
        self.path.write(yaml.dump(data))

    test_file = pytest.helpers.DAL(path=path, _load_data=loader,
                                   _write_data=writer)
    test_file.data = data
    return test_file


def test_lazy_read_yaml_source(yaml_file):
    config = YamlFile(str(yaml_file.path))

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


def test_write_yaml_source(yaml_file):
    config = YamlFile(str(yaml_file.path))
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

    assert yaml_file.data == expected
