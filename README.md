# Layeredconfig

## What is it?

Layeredconfig is a python library that aggregates different configuration
sources into one simple configuration object with dot-notation and
dictionary-like access. It also allows to specify custom type conversion
and merging strategies when the same key was found multiple times.

```python
from layeredconfig import layeredconfigig, Environment, EtcdStore, INIFile

config = layeredconfigig(
	INIFile('/path/to/my/config.ini'),
    EtcdStore('https://my-etcd-host/'),
    Environment(prefix='MYAPP')
)

assert config.mykey == True
assert config['some'].nested.key == 100

assert config.dump() == {'mykey': True, 'some': {'nested': {'key': 100}}}
assert config.some.nested.dump() == {'key': 100}
```

Examples for type conversion and merging strategies are shown on the
[example page of the
documentation](http://layeredconfig.readthedocs.com/examples).

## Latest Version and History

Layeredconfig adheres to [Semantic Versioning](http://semver.org/).

The current version is 0.1.0 and layeredconfig is still in a planning phase.
As such it is *not meant for production use*.

Changes can be found in [CHANGELOG](CHANGELOG.md).

## Installation

Layeredconfig can be installed with pip and only requires
[`six`](https://pypi.python.org/pypi/six).

```
pip install layeredconfig
```

However, some of the configuration sources require additional packages
to be installed when used.

 * `YAMLFile` requires [`pyyaml`]()
 * `EtcdStore` requires [`requests`]()

## Documentation



## Licensing

Please see [LICENSE](LICENSE).

## Contribution

Contributions are very welcome. Please file any bugs or issues
