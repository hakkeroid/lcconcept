# -*- coding: utf-8 -*-

import copy

from layeredconfig import source


class DictSource(source.Source):
    """Simple memory key-value source"""

    def __init__(self, data=None, **kwargs):
        super(DictSource, self).__init__(**kwargs)
        self._data = data or {}

    def _read(self):
        # use deepcopy to prevent uncontrolled changes
        # to self._data from outside of this class
        return copy.deepcopy(self._data)

    def _write(self, data):
        self._data = data
