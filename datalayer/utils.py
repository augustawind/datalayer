from collections.abc import MutableMapping


class _DEFAULT:
    pass


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
    def __validate_key(key: type):
        if not isinstance(key, type):
            raise TypeError(f"not a type: {repr(key)}")

    def __str__(self):
        return f'{typename(self)}({str(self.data)})'

    def __repr__(self):
        return f'{typename(self)}({repr(self.data)})'

    def __getitem__(self, item: type):
        self.__validate_key(item)
        min_idx = None
        best_match = _DEFAULT
        mro = item.__mro__
        for key, value in self.data.items():
            try:
                idx = mro.index(key)
            except ValueError:
                continue
            if min_idx is None or idx < min_idx:
                min_idx = idx
                best_match = value
        if best_match is _DEFAULT:
            raise KeyError(item)
        return best_match

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
