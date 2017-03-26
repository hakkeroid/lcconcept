# -*- coding: utf-8 -*-
from collections import deque


class LayeredConfig:
    """Presenter"""

    def __init__(self, *sources, **kwargs):
        self._sources = sources
        self._root = kwargs.get('root', [])

    def __getattr__(self, name):
        queue = deque(self._sources)
        subqueue = deque()

        while queue:
            source = queue.popleft()

            # step down to key level
            iter_source = source
            for root in self._root:
                iter_source = iter_source[root]

            # lookup key and skip this source if not found
            try:
                value = iter_source[name]
            except KeyError:
                continue

            if isinstance(value, Source):
                # remember subtree for the next level of iteration
                subqueue.append(source)
            else:
                return value

        return LayeredConfig(*subqueue, root=self._root+[name])


class SourceMeta(type):
    def __call__(cls, *args, **kwargs):
        instance = super(SourceMeta, cls).__call__(*args, **kwargs)
        instance._initialized = True
        return instance


class Source(object):
    """Source object"""

    __metaclass__ = SourceMeta
    _initialized = False

    def __init__(self, **kwargs):
        self._root = kwargs.pop('root', None)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def setdefault(self, name, value):
        try:
            return self[name]
        except KeyError:
            self[name] = value
            return value

    def items(self):
        return self._read().items()

    def update(self, *others):
        data = self._read()
        for other in others:
            if isinstance(other, Source):
                data.update(other.dump())
            else:
                data.update(other)
        self._write(data)

    def dump(self):
        return self._read()

    def save(self):
        try:
            self._root[0].save()
        except AttributeError:
            pass

    def __getattr__(self, name):
        # although the key was accessed with attribute style
        # lets keep raising a KeyError to distinguish between
        # internal and user data.
        return self[name]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __getitem__(self, key):
        attr = self._read()[key]
        if isinstance(attr, dict):
            return Source(root=(self, key))
        return attr

    def __setitem__(self, key, value):
        if any([self._initialized is False,
                key == '_initialized',
                key in self.__dict__,
                key in self.__class__.__dict__]):
            super(Source, self).__setattr__(key, value)
        else:
            data = self._read()
            data[key] = value
            self._write(data)

    def __delattr__(self, name):
        del self[name]

    def __delitem__(self, key):
        data = self._read()
        del data[key]
        self._write(data)

    def __len__(self):
        return len(self._read().keys())

    def __iter__(self):
        return iter(self._read().keys())

    def _read(self):
        return self._root[0]._read()[self._root[1]]

    def _write(self, data):
        result = self._root[0]._read()
        result[self._root[1]] = data

        self._root[0]._write(result)

    def __eq__(self, other):
        return self._read() == other

    def __repr__(self):
        return repr(self._read())


class DictSource(Source):
    """Simple memory key-value source"""

    def __init__(self, data=None):
        super(DictSource, self).__init__()
        self._data = data or {}

    def _read(self):
        return self._data

    def _write(self, data):
        self._data = data

class YamlFile(Source):
    """Source for yaml files"""

    import yaml

    def __init__(self, source):
        super(YamlFile, self).__init__()
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return self.yaml.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            self.yaml.dump(data, fh)


class JsonFile(Source):
    """Source for json files"""

    import json

    def __init__(self, source):
        super(JsonFile, self).__init__()
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return self.json.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            self.json.dump(data, fh)


class INIFile(Source):
    """Source for json files"""

    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    def __init__(self, source, subsection_token=None):
        super(INIFile, self).__init__()
        self._source = source
        self._parser = self.configparser.ConfigParser()
        self._parser.readfp(source)
        self._token = subsection_token

    def _read(self):
        data = {}
        for section in self._parser.sections():
            subtree = dict(self._parser.items(section))
            if section == '__root__':
                data.update(subtree)
            elif self._token and self._token in section:
                subheaders = section.split('.')
                last = subheaders.pop()
                subdata = data
                for header in subheaders:
                    subdata = subdata.setdefault(header, {})
                subdata[last] = subtree
            else:
                data[section] = subtree
        return data

    def _write(self, data):
        return
        with open(self._source, 'w') as fh:
            self.json.dump(data, fh)


class EtcdStore(Source):
    """Source for etcd stores"""

    def __init__(self, baseurl="http://127.0.0.1:2379/v2", use_cache=True):
        super(EtcdStore, self).__init__()

        self._connector = EtcdConnector(baseurl)
        self._cache = None
        self._use_cache = use_cache

    def _read(self):
        if not self._use_cache or not self._cache:
            self._cache = self._connector.get()
        return self._cache

    def _write(self, data):
        self._cache = data

    def save(self):
        self._connector.set(self._cache)


class EtcdConnector:
    """Simple etcd connector"""

    import requests

    def __init__(self, url):
        self.url = url + '/keys'

    def set(self, data, root=None):
        for key, value in data.items():
            if isinstance(value, dict):
                key_parts = filter(None, [root, key])
                self.set(value, '/'.join(key_parts))
            else:
                key_parts = filter(None, [root, key])
                self._send('/'.join(key_parts), value)

    def get(self, path='/'):
        response = self._request(path, recursive=True)
        try:
            payload = response['node']['nodes']
        except KeyError:
            return {}
        return self._convert_payload(payload, root=path)

    def flush(self):
        response = self._request('/')
        try:
            payload = response['node']['nodes']
        except KeyError:
            return

        for node in payload:
            key = node['key'].lstrip('/')
            self.requests.delete('/'.join([self.url, key]),
                                 params={'recursive': True})

    def _convert_payload(self, nodes, root=None):
        root = root or '/'
        result = {}

        for node in nodes:
            if node.get('dir', False):
                key = node.get('key', root)
                nodes = node.get('nodes', [])
                result[key.lstrip(root)] = self._convert_payload(nodes, key)
            else:
                key = node['key']
                result[key.lstrip(root)] = node['value']
        return result

    def _request(self, path, recursive=False):
        # getting a single value is broken
        params = {'recursive': recursive}
        url = '/'.join([self.url, path])
        url.replace('//', '/')
        response = self.requests.get(url, params=params)
        return response.json()

    def _send(self, key, value):
        self.requests.put('/'.join([self.url, key]),
                          data={'value': value})
