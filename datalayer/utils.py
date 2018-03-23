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
        self.data = {}
        self.update(*args, **kwargs)

    @staticmethod
    def __validate_key(key):
        if type(key) is not type:
            raise TypeError(f"not a type: {repr(key)}")

    def __str__(self):
        return f'{typename(self)}({str(self.data)})'

    def __repr__(self):
        return f'{typename(self)}({repr(self.data)})'

    def __getitem__(self, item):
        self.__validate_key(item)
        for key, value in self.data.items():
            if issubclass(item, key):
                return value
        raise KeyError(item)

    def __setitem__(self, key, value):
        self.__validate_key(key)
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
