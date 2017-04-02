# -*- coding: utf-8 -*-

import os

from layeredconfig import source


class Environment(source.Source):
    """Reads environment variables"""

    _is_typed = False

    def __init__(self, prefix=None, token='_', **kwargs):
        super(Environment, self).__init__(**kwargs)
        self.prefix = prefix
        self.token = token

    def _read(self):
        data = {}
        for key, value in os.environ.items():
            if not key.startswith(self.prefix):
                continue

            subheaders = key.lower().split(self.token)[1:]
            subdata = data
            last = subheaders.pop()
            for header in subheaders:
                subdata = subdata.setdefault(header, {})
            subdata[last] = value

        return data

    def _write(self, data):
        def _write(section, keychain=None):
            if keychain is None:
                keychain = []

            for key, value in section.items():
                if isinstance(value, dict):
                    _write(value, keychain + [key])
                else:
                    full_key = '_'.join(keychain + [key]).upper()
                    os.environ[self.prefix + full_key] = str(value)

        _write(data)
