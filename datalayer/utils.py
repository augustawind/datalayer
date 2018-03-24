from collections import OrderedDict
from collections.abc import MutableMapping


def typename(x):
    """Return the class name of a type or object."""
    try:
        return x.__name__
    except AttributeError:
        return type(x).__name__


class SubclassDict(MutableMapping):
    """Dict that uses a subclass check for lookups.

    Keys must all be 'type' objects.
    """

    def __init__(self, *args, **kwargs):
        self.data = OrderedDict()
        self.update(*args, **kwargs)

    @staticmethod
    def __validate_key(key: type):
        if not isinstance(key, type):
            raise TypeError(f"not a type: {repr(key)}")

    def __str__(self):
        return f'{typename(self)}({str(self.data)})'

    def __repr__(self):
        return f'{typename(self)}({repr(self.data)})'

    def __getitem__(self, item):
        self.__validate_key(item)

        # Find all keys that are subclasses of `item`
        matches = []
        for key in self.data:
            if issubclass(item, key):
                matches.append(key)

        # If only one match, return it
        if len(matches) == 1:
            return self.data[matches[0]]

        # If more than one match, find the nearest subclass in the MRO
        if len(matches) > 1:
            min_idx = None
            best_match = None
            mro = item.__mro__[:-1]
            for match in matches:
                try:
                    idx = mro.index(match)
                except ValueError:
                    continue
                if min_idx is None or idx < min_idx:
                    min_idx = idx
                    best_match = match
            return self.data[best_match]

        # If no matches, raise a KeyError
        raise KeyError(item)

    def __setitem__(self, key: type, value):
        self.__validate_key(key)
        self.data[key] = value

    def __delitem__(self, key: type):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def copy(self) -> 'SubclassDict':
        return SubclassDict(self.data)
