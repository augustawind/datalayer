from datalayer.utils import typename


class Error(Exception):
    """Base library error class."""

    def __init__(self, *parts):
        super().__init__(self.join(*parts))

    @staticmethod
    def join(*parts):
        return ': '.join(part for part in parts if part)


class SpecError(Error):

    def __init__(self, spec, *parts):
        self.spec = spec
        super().__init__(*parts)

    @classmethod
    def wrong_type(cls, spec, *parts, expected=None, actual=None):
        if expected:
            msg = f'expected {expected}'
            if actual:
                msg = f'{msg}, got {actual}'
            parts = [*parts, msg]
        return cls(spec, 'wrong type', *parts)


class SchemaError(SpecError):
    """Error raised when a Spec schema is invalid."""

    def __init__(self, spec, *parts):
        self.spec = spec
        super().__init__('invalid schema', typename(spec), *parts)


class ValidationError(SpecError):
    """Error raised when a value fails Spec validation."""

    def __init__(self, spec, *parts):
        self.spec = spec
        super().__init__(f'invalid value for {typename(spec)}', *parts)
