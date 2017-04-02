# -*- coding: utf-8 -*-

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from layeredconfig import source


class INIFile(source.Source):
    """Source for ini files"""

    _is_typed = False

    def __init__(self, source, subsection_token=None, **kwargs):
        super(INIFile, self).__init__(**kwargs)
        self._source = source
        self._parser = configparser.ConfigParser()
        self._parser.readfp(source)
        self._token = subsection_token

    def _read(self):
        data = {}
        for section in self._parser.sections():
            sublevel = dict(self._parser.items(section))
            if section == '__root__':
                data.update(sublevel)
            elif self._token and self._token in section:
                subheaders = section.split(self._token)
                last = subheaders.pop()
                subdata = data
                for header in subheaders:
                    subdata = subdata.setdefault(header, {})
                subdata[last] = sublevel
            else:
                data.setdefault(section, {}).update(sublevel)
        return data
