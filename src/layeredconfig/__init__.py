# -*- coding: utf-8 -*-

from .config import LayeredConfig
from .source import CustomType
from .sources.dictsource import DictSource
from .sources.environment import Environment
from .sources.etcdstore import EtcdStore
from .sources.inifile import INIFile
from .sources.jsonfile import JsonFile
from .sources.yamlfile import YamlFile
from .strategy import add, collect, merge
