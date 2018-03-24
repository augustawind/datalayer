import abc
from collections.abc import Container, Mapping, Sequence
from typing import Any

from datalayer.exceptions import SpecError, ValidationError
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
        """Validate the spec, raising a SpecError if invalid."""
        return spec

    def validate(self, value: Any) -> Any:
        """Validate the given value, raising a ValidationError if invalid."""
        if not isinstance(value, self.base_type):
            raise ValidationError(
                self,
                f'wrong type: expected {typename(self.base_type)},'
                f' got {typename(value)} instead')
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
        is_type = issubclass(type(spec), type)
        if isinstance(spec, Spec) or is_type and issubclass(spec, Spec):
            raise SpecError(self, 'cannot be a Spec')
        if not is_type:
            raise SpecError(
                self, f'expected a type object, got {typename(spec)}')
        return spec


class CompoundSpec(Spec):

    base_type = Container

    def _validate_spec_or_type(self, value):
        """Assert the value is a Spec, converting type objects to Atoms."""
        if isinstance(value, type):
            value = Atom(value)
        elif not isinstance(value, Spec):
            raise SpecError(self, 'values must be Specs or type objects')
        return value


class Model(CompoundSpec):

    base_type = Mapping

    def validate_spec(self, spec: Any) -> Mapping:
        for key, val in spec.items():
            if not isinstance(key, str):
                raise SpecError(self, 'keys must be str')
            spec[key] = self._validate_spec_or_type(val)
        return spec

    def validate(self, value: Mapping) -> Mapping:
        value = super().validate(value)
        if len(value) > len(self.spec):
            raise ValidationError(
                self,
                f'too many items: expected {len(self.spec)}, got {len(value)}')
        if len(value) < len(self.spec):
            raise ValidationError(
                self,
                f'too few items: expected {len(self.spec)}, got {len(value)}')

        for field, field_spec in self.spec.items():
            if field not in value:
                raise ValidationError(self, f'field {field} not found')
            value[field] = field_spec.validate(value[field])

        return value

    def inner(self, item=_DEFAULT, default=_DEFAULT):
        if item is _DEFAULT:
            return self.spec

        if not isinstance(item, str):
            raise SpecError(self, 'item must be a str')

        try:
            return self.spec[item]
        except KeyError:
            if default is _DEFAULT:
                raise SpecError(self, f'key "{item}" not found')
            return default


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
    }))
})
