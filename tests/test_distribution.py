# -*- coding: utf-8 -*-

import pytest

DEPENDENCIES = {
    'yaml': ['yaml'],
    'etcd': ['requests'],
}
SKIP = []

# make sure library does not break and informs user about
# missing dependency. Those tests are only in the minimal
# test environment relevant. So skip them if dependencies
# are importable.
for source, deps in DEPENDENCIES.items():
    for dep in deps:
        try:
            __import__(dep)
            SKIP.append(source)
        except:
            pass


@pytest.mark.skipif('yaml' in SKIP, reason='Skip if dependencies are installed')
def test_missing_yaml_dependencies(monkeypatch):
    with pytest.raises(ImportError) as exc_info:
        import layeredconfig
        layeredconfig.YamlFile('/path')

    try:
        message = exc_info.value.message
    except AttributeError:
        # py33, py34 compatibility
        message = exc_info.value.msg

    assert 'optional dependency' in message


@pytest.mark.skipif('etcd' in SKIP, reason='Skip if dependencies are installed')
def test_missing_etcd_dependencies(monkeypatch):
    with pytest.raises(ImportError) as exc_info:
        import layeredconfig
        layeredconfig.YamlFile('/path')

    try:
        message = exc_info.value.message
    except AttributeError:
        # py33, py34 compatibility
        message = exc_info.value.msg

    assert 'optional dependency' in message
