import abc
from collections import namedtuple
from collections.abc import Container, Mapping, Sequence
from typing import Any

from datalayer.exceptions import SchemaError, ValidationError
from datalayer.utils import SubclassDict, typename


class _DEFAULT:
    """Generic default value for when None doesn't cut it."""


class Spec(abc.ABC):

    def __init__(self, spec: Any):
        self.spec = self.validate_spec(spec)

    def __eq__(self, other):
        return self.spec == other.spec

    @property
    @abc.abstractmethod
    def base_type(self):
        """Python data type this Spec represents."""

    def validate_spec(self, spec: Any) -> Any:
        """Validate the spec, raising a SchemaError if invalid."""
        return spec

    def validate(self, value: Any) -> Any:
        """Validate the given value, raising a ValidationError if invalid."""
        if not isinstance(value, self.base_type):
            raise ValidationError.wrong_type(
                self,
                expected=f"'{typename(self.base_type)}'",
                actual=f"'{typename(value)}'")
        return value

    def inner(self) -> Any:
        """Return the inner object wrapped by this Spec."""
        return self.spec

    def innermost(self) -> Any:
        """Unwrap inner Specs, returning the first non-Spec."""
        inner = self.inner()
        while isinstance(inner, Spec):
            inner = inner.inner()
        return inner


class Atom(Spec):

    @property
    def base_type(self):
        return self.spec

    def validate_spec(self, spec: Any) -> Any:
        spec = super().validate_spec(spec)
        is_type = issubclass(type(spec), type)
        if is_type:
            is_spec = issubclass(spec, Spec)
        else:
            is_spec = isinstance(spec, Spec)
        if is_spec:
            raise SchemaError(self, 'cannot be a Spec')
        if not is_type:
            raise SchemaError.wrong_type(
                self,
                expected="'type'",
                actual=f"'{typename(spec)}'")
        return spec


class CompoundSpec(Spec):
    base_type = Container

    def _validate_spec_or_type(self, value):
        """Assert the value is a Spec, converting type objects to Atoms."""
        if isinstance(value, type):
            value = Atom(value)
        elif not isinstance(value, Spec):
            raise SchemaError.wrong_type(
                self,
                expected="Spec or type",
                actual=f"'{typename(value)}'")
        return value


class Model(CompoundSpec):
    base_type = Mapping

    def validate_spec(self, spec: Any) -> Mapping:
        spec = super().validate_spec(spec)
        if isinstance(spec, type):
            raise SchemaError.wrong_type(
                self,
                expected='Mapping or object',
                actual=f"'{typename(spec)}'")

        # If spec isn't a Mapping, grab attrs from its __dict__
        if not isinstance(spec, Mapping):
            spec = spec.__dict__

        validated_spec = {}
        for key, val in spec.items():
            if type(key) is not str:
                raise SchemaError(self, 'keys must be str')
            validated_spec[key] = self._validate_spec_or_type(val)
        return validated_spec

    def validate(self, value: Mapping) -> Mapping:
        value = super().validate(value)
        if len(value) > len(self.spec):
            raise ValidationError(
                self,
                'too many items'
                f'expected {len(self.spec)}, got {len(value)}')
        if len(value) < len(self.spec):
            raise ValidationError(
                self,
                'too few items',
                f'expected {len(self.spec)}, got {len(value)}')

        for field, field_spec in self.spec.items():
            if field not in value:
                raise ValidationError(self, f"field '{field}' not found")
            value[field] = field_spec.validate(value[field])

        return value

    def inner(self, item=_DEFAULT, default=_DEFAULT):
        if item is _DEFAULT:
            return self.spec

        try:
            return self.spec[item]
        except KeyError:
            if default is _DEFAULT:
                raise SchemaError(self, f'key {repr(item)} not found')
            return default


class Map(CompoundSpec):
    base_type = Mapping
    Spec = namedtuple('MapSpec', ('key', 'value'))

    def validate_spec(self, spec: Any) -> Spec:
        spec = super().validate_spec(spec)
        if not (isinstance(spec, Sequence) and len(spec) == 2):
            raise SchemaError.wrong_type(
                self,
                expected='sequence with 2 items',
                actual=f"'{typename(spec)}'")

        key_spec, val_spec = spec
        key_spec = self._validate_spec_or_type(key_spec)
        val_spec = self._validate_spec_or_type(val_spec)

        if key_spec.base_type.__hash__ is None:
            raise SchemaError(
                self, 'unhashable Spec for key', f"'{typename(key_spec)}'")

        return self.Spec(key_spec, val_spec)


class Seq(CompoundSpec):
    base_type = Sequence

    def validate_spec(self, spec: Any) -> Spec:
        spec = self._validate_spec_or_type(spec)
        return spec

    def validate(self, value: Sequence) -> Sequence:
        value = super().validate(value)
        cls = type(value)
        value = cls(self.spec.validate(item) for item in value)
        return value


"""A mapping of Python types to their corresponding Spec classes."""
TYPE_TO_SPEC = SubclassDict({spec.base_type: spec for spec in (
    Model,
    Seq,
)})


def from_python(data: Any) -> Spec:
    spec_cls = TYPE_TO_SPEC.get(type(data), Atom)
    return spec_cls(data)


example = Model({
    'valid': bool,
    'tally': int,
    'records': Seq(Model({
        'name': str,
        'age': int,
        'colors': Seq(str),
        'kids': Atom(list),
    })),
    'attributes': Map((str, int)),
})
