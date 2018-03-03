import pytest

from datalayer import specs
from datalayer.exceptions import Error, SpecError, ValidationError


@pytest.fixture()
def custom_spec():
    class MySpec(specs.Spec):
        base_type = bool
    return MySpec


class TestAtom:

    def test_validate_spec(self, custom_spec):
        # Should not accept Specs
        with pytest.raises(SpecError):
            specs.Atom(specs.Atom(int))
        with pytest.raises(SpecError):
            specs.Atom(custom_spec(5))

        # Should not accept non-type values
        with pytest.raises(SpecError):
            specs.Atom(5)
        with pytest.raises(SpecError):
            specs.Atom(True)

        # Should accept types
        assert specs.Atom(int).spec is int
        assert specs.Atom(list).spec is list

    def test_validate(self):
        spec = specs.Atom(int)

        # Should not pass on wrong type
        with pytest.raises(ValidationError):
            spec.validate('foo')
        with pytest.raises(ValidationError):
            spec.validate(None)
        with pytest.raises(ValidationError):
            spec.validate([1, 2, 3])

        # Should pass on correct type
        assert spec.validate(5) == 5


class TestMap:

    @staticmethod
    def spec_fields(fields=None):
        fields = fields or {}
        return {
            'name': str,
            'age': int,
            'height': specs.Atom(float),
            'verified': bool,
            **fields
        }

    def test_validate_spec(self):
        # Should convert type values to Specs
        spec = specs.Map(self.spec_fields())
        assert spec.spec['name'] == specs.Atom(str)
        assert spec.spec['height'] == specs.Atom(float)

        # Should allow nested Specs
        kids = specs.Map({'name': str})
        spec = specs.Map(self.spec_fields({'kids': kids}))
        assert spec.spec['kids'] == kids
        assert spec.spec['kids'].spec['name'] == specs.Atom(str)

        # Should fail with non-str keys
        with pytest.raises(SpecError):
            specs.Map(self.spec_fields({1: bool}))
        with pytest.raises(SpecError):
            specs.Map(self.spec_fields({('x', 'y'): str}))

        # Should fail with non-type, non-Spec values
        with pytest.raises(SpecError):
            specs.Map(self.spec_fields({'name': 'bob'}))
