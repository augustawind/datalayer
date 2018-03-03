from datalayer.utils import typename


class Error(Exception):
    """Base library error class."""


class SpecError(Error):
    """Error raised when a Spec is invalid."""

    def __init__(self, spec, msg=''):
        self.spec = spec
        super().__init__(f'invalid spec: {typename(spec)}: {msg}')


class ValidationError(Error):
    """Error raised when a value fails Spec validation."""

    def __init__(self, spec, msg=''):
        self.spec = spec
        super().__init__(f'invalid value: {typename(spec)}: {msg}')
