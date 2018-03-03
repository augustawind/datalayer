def typename(x):
    """Return the class name of a type or object."""
    if type(x) is not type:
        x = type(x)
    return x.__name__
