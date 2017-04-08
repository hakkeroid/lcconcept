#!/usr/bin/env python3

try:
    import urlparse
except ImportError:
    # py>3
    import urllib.parse as urlparse

try:
    import requests
except ImportError:
    pass

from layeredconfig import source


class EtcdStore(source.Source):
    """Source for etcd stores"""

    _DEFAULT_URL = "http://127.0.0.1:2379/v2"

    def __init__(self, url, **kwargs):
        # enable caching by default
        kwargs['cached'] = kwargs.get('cached', True)

        super(EtcdStore, self).__init__(**kwargs)

        self._connector = EtcdConnector(url or self._DEFAULT_URL)

    def _read(self):
        # getting a single value is broken
        response = self._connector.get('/', recursive=True)
        payload = self._get_payload_from_response(response)
        return self._translate_payload_to_dict(payload)

    def _write(self, data):
        items = self._translate_dict_to_key_value_pairs(data)
        self._connector.set(*items)

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

    def __init__(self, url):
        self.url = url + '/keys'

        try:
            assert requests
        except NameError:
            raise ImportError('You are missing the optional'
                              ' dependency "requests"')

    def get(self, path, recursive=False):
        params = {'recursive': recursive}
        url = self._make_url(self.url, path)
        response = requests.get(url, params=params)
        return response.json()

    def set(self, *items):
        for key, value in items:
            url = self._make_url(self.url, key)
            requests.put(url, data={'value': value})

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
