# -*- coding: utf-8 -*-

import pytest

try:
    import yaml
    skip_yaml = True
except:
    skip_yaml = False


# make sure library does not break and informs user about
# missing dependency
@pytest.mark.skipif(skip_yaml, reason='Skip if dependencies are installed')
def test_missing_dependencies(monkeypatch):
    with pytest.raises(ImportError) as exc_info:
        import mvp
        mvp.YamlFile('/path')

    try:
        message = exc_info.value.message
    except AttributeError:
        # py33, py34 compatibility
        message = exc_info.value.msg

    assert 'optional dependency' in message
