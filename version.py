import re
from itertools import zip_longest


class Version(object):
    def __init__(self, ver_str: str):
        if not re.match(r'\d+(\.\d+)+', ver_str):
            raise ValueError(f'{ver_str} is not a valid version')
        self.version = tuple(ver_str.split('.'))

    def __repr__(self):
        return 'Version: {}'.format('.'.join(self.version))

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        else:
            return all([a == b for a,b in zip_longest(self.version, other.version, fillvalue='')])

    def __gt__(self, other):
        for a, b in zip_longest(self.version, other.version, fillvalue=''):
            if a > b:
                return True
        return False

    def __lt__(self, other):
        for a, b in zip_longest(self.version, other.version, fillvalue=''):
            if a < b:
                return True
        return False

    def __ne__(self, other):
        for a, b in zip_longest(self.version, other.version, fillvalue=''):
            if a != b:
                return True
        return False

    def __hash__(self):
        return id(self.version)
