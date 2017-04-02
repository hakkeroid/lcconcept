# -*- coding: utf-8 -*-

import json

from layeredconfig import source


class JsonFile(source.Source):
    """Source for json files"""

    def __init__(self, source, **kwargs):
        super(JsonFile, self).__init__(**kwargs)
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return json.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            json.dump(data, fh)
