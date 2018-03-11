def typename(x):
    """Return the class name of a type or object."""
    try:
        return x.__name__
    except AttributeError:
        return type(x).__name__
