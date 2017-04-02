# -*- coding: utf-8 -*-

try:
    import yaml
except ImportError:
    pass

from layeredconfig import source


class YamlFile(source.Source):
    """Source for yaml files"""

    def __init__(self, source, **kwargs):
        try:
            assert yaml
        except NameError:
            raise ImportError('You are missing the optional'
                              ' dependency "pyyaml"')

        super(YamlFile, self).__init__(**kwargs)
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return yaml.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            yaml.dump(data, fh)
