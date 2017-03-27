# -*- coding: utf-8 -*-
from collections import deque
try:
    import urlparse
except ImportError:
    # py>3
    import urllib.parse as urlparse

import six

# optional dependencies
try:
    import yaml
except ImportError as err:
    pass


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

    def __new__(self, name, bases, dct):
        if not '_read' in dct:
            msg = '%s is missing to the required "_read" method' % name
            raise NotImplementedError(msg)
        if name != 'Source':
            dct['_source_name'] = name

        dct['_readonly'] = '_write' not in dct

        return super(SourceMeta, self).__new__(self, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        instance = super(SourceMeta, cls).__call__(*args, **kwargs)
        instance._initialized = True
        return instance


@six.add_metaclass(SourceMeta)
class Source(object):
    """Source object"""

    _initialized = False

    def __init__(self, **kwargs):
        self._root = kwargs.pop('root', None)

        # kwargs.get would override the metaclass settings
        # so only change if it's really given.
        if 'readonly' in kwargs:
            self._readonly = kwargs['readonly']
        if 'source_name' in kwargs:
            self._source_name = kwargs['source_name']

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
        return six.iteritems(self._read())

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

    def _read(self):
        return self._root[0]._read()[self._root[1]]

    def _write(self, data):
        if self._readonly:
            raise TypeError('%s is not writable' % self._source_name)

        result = self._root[0]._read()
        result[self._root[1]] = data

        self._root[0]._write(result)

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
            return Source(root=(self, key),
                          readonly=self._readonly,
                          source_name=self._source_name)
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


    def __init__(self, source):
        try:
            assert yaml
        except NameError:
            msg = 'You are missing the optional dependency "pyyaml"'
            raise ImportError(msg)

        super(YamlFile, self).__init__()
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return yaml.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            yaml.dump(data, fh)


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
                subheaders = section.split(self._token)
                last = subheaders.pop()
                subdata = data
                for header in subheaders:
                    subdata = subdata.setdefault(header, {})
                subdata[last] = subtree
            else:
                data.setdefault(section, {}).update(subtree)
        return data

    # def _write(self, data):
        # import ipdb; ipdb.set_trace()
        # return
        # with open(self._source, 'w') as fh:
            # self.json.dump(data, fh)


class EtcdStore(Source):
    """Source for etcd stores"""

    def __init__(self, baseurl="http://127.0.0.1:2379/v2", use_cache=True):
        super(EtcdStore, self).__init__()

        self._connector = EtcdConnector(baseurl)
        self._cache = None
        self._use_cache = use_cache

    def save(self):
        items = self._translate_dict_to_key_value_pairs(self._cache)
        self._connector.set(*items)

    def _read(self):
        if self._use_cache is False or not self._cache:
            # getting a single value is broken
            response = self._connector.get('/', recursive=True)
            payload = self._get_payload_from_response(response)
            self._cache = self._translate_payload_to_dict(payload)
        return self._cache

    def _write(self, data):
        self._cache = data

    def _translate_dict_to_key_value_pairs(self, data, root=None):
        for key, value in data.items():
            if isinstance(value, dict):
                key_parts = filter(None, [root, key])
                items = self._translate_dict_to_key_value_pairs(value, '/'.join(key_parts))
                for item in items:
                    yield item
            else:
                key_parts = filter(None, [root, key])
                yield '/' + '/'.join(key_parts), value

    def _get_payload_from_response(self, response):
        try:
            return response['node']['nodes']
        except KeyError:
            return {}
        return self._convert_payload(payload, root=path)

    def _translate_payload_to_dict(self, nodes, root=None):
        root = root or '/'
        result = {}

        for node in nodes:
            if node.get('dir', False):
                key = node.get('key', root)
                nodes = node.get('nodes', [])
                result[key.lstrip(root)] = self._translate_payload_to_dict(nodes, key)
            else:
                key = node['key']
                result[key.lstrip(root)] = node['value']
        return result


class EtcdConnector:
    """Simple etcd connector"""

    import requests

    def __init__(self, url):
        self.url = url + '/keys'

    def get(self, path, recursive=False):
        params = {'recursive': recursive}
        url = self._make_url(self.url, path)
        response = self.requests.get(url, params=params)
        return response.json()

    def set(self, *items):
        for key, value in items:
            url = self._make_url(self.url, key)
            self.requests.put(url, data={'value': value})

    def _make_url(self, *path_parts):
        full_url = '/'.join(path_parts)
        # not converting url_parts into a list leaves
        # us with a namedtuple which cannot be modified
        url_parts = list(urlparse.urlsplit(full_url))
        url_parts[2] = self._normalize_path(url_parts[2])
        return urlparse.urlunsplit(url_parts)

    def _normalize_path(self, path):
        parts = path.split('/')
        start, middle, end = parts[0], parts[1:-1], parts[-1]
        return '/'.join([start] + 
                        [part for part in middle if part] + 
                        [end])
