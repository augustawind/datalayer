from types import SimpleNamespace

import pytest

from datalayer import specs
from datalayer.exceptions import SchemaError, ValidationError


@pytest.fixture()
def custom_spec():
    class MySpec(specs.Spec):
        base_type = bool
    return MySpec


class TestAtom:

    def test_validate_spec(self, custom_spec):
        # Should not accept Spec classes or instances
        with pytest.raises(SchemaError):
            specs.Atom(specs.Atom)
        with pytest.raises(SchemaError):
            specs.Atom(specs.Model)
        with pytest.raises(SchemaError):
            specs.Atom(specs.Atom(int))
        with pytest.raises(SchemaError):
            specs.Atom(custom_spec(5))

        # Should not accept non-type values
        with pytest.raises(SchemaError):
            specs.Atom(5)
        with pytest.raises(SchemaError):
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


def spec_fields(fields=None):
    fields = fields or {}
    return {
        'name': str,
        'age': int,
        'height': specs.Atom(float),
        'verified': bool,
        **fields
    }


class TestModel:

    def test_validate_spec(self):
        # Should convert type values to Atoms
        spec = specs.Model(spec_fields())
        assert spec.spec['name'] == specs.Atom(str)
        assert spec.spec['height'] == specs.Atom(float)

        # Should accept mappings OR objects
        spec = specs.Model(SimpleNamespace(**spec_fields()))
        assert spec == specs.Model(spec_fields())

        # Should allow nested Specs
        kids = specs.Model({'name': str})
        spec = specs.Model(spec_fields({'kids': kids}))
        assert spec.spec['kids'] == kids
        assert spec.spec['kids'].spec['name'] == specs.Atom(str)

        # Should fail with non-str keys
        with pytest.raises(SchemaError):
            specs.Model(spec_fields({1: bool}))
        with pytest.raises(SchemaError):
            specs.Model(spec_fields({('x', 'y'): str}))

        # Should fail with non-type, non-Spec values
        with pytest.raises(SchemaError):
            specs.Model(spec_fields({'name': 'bob'}))

    def test_validate(self):
        spec = specs.Model(spec_fields())

        # Should fail if wrong number of items
        with pytest.raises(ValidationError):
            spec.validate({'name': 'bob', 'age': 13, 'height': 33.3})
        with pytest.raises(ValidationError):
            spec.validate({'name': 'bob', 'age': 13, 'height': 33.3,
                           'verified': True, 'greeting': 'hello'})

        # Should fail if field not present
        with pytest.raises(ValidationError):
            spec.validate({'name': 'bob', 'age': 13, 'height': 33.3,
                           'greeting': 'hello'})

        # Should fail if field has wrong type
        with pytest.raises(ValidationError):
            spec.validate({'name': 'bob', 'age': 13, 'height': 33.3,
                           'verified': 'yes'})

        # Happy path
        spec_value = {'name': 'bob', 'age': 13, 'height': 33.3,
                      'verified': True}
        value = spec.validate(spec_value)
        assert value == spec_value

    def test_inner(self):
        spec = specs.Model(spec_fields())

        # Should fail if item not found, unless default provided
        with pytest.raises(SchemaError):
            spec.inner(5)
        with pytest.raises(SchemaError):
            spec.inner('greeting')
        spec.inner(6.6, default='foo')
        assert spec.inner('greeting', default=str) is str

        # Should return whole dict if no item provided
        assert spec.inner() == {
            'name': specs.Atom(str),
            'age': specs.Atom(int),
            'height': specs.Atom(float),
            'verified': specs.Atom(bool),
        }

        # Happy path
        assert spec.inner('age').inner() is int
        assert spec.inner('name').inner() is str

        # Happy path, nested Specs
        spec = specs.Model(spec_fields({'colors': specs.Seq(str)}))
        innermost = spec.inner('colors').inner().inner()
        assert innermost is str

    def test_innermost(self):
        matrix_spec = specs.Seq(specs.Seq(int))
        schema = spec_fields({
            'name': str,
            'matrices': matrix_spec,
        })
        spec = specs.Model(schema)

        assert spec.innermost() == spec.spec
        assert spec.inner('matrices').innermost() is int
        assert spec.inner('name').innermost() is str


class TestMap:

    def test_validate_spec(self):
        # Should convert type values to Atoms
        spec = specs.Map((str, int))
        assert spec.spec == (specs.Atom(str), specs.Atom(int))
        spec = specs.Map([int, dict])
        assert spec.spec == (specs.Atom(int), specs.Atom(dict))

        # Should allow nested Specs
        seq_spec = specs.Seq(bool)
        spec = specs.Map((str, seq_spec))
        assert spec.spec == (specs.Atom(str), seq_spec)
        assert spec.spec.key == specs.Atom(str)
        assert spec.spec.value == seq_spec
        spec = specs.Map((seq_spec, int))
        assert spec.spec == (seq_spec, specs.Atom(int))
        assert spec.spec.key == seq_spec
        assert spec.spec.value == specs.Atom(int)

        # Should fail on non-sequence specs
        with pytest.raises(SchemaError):
            specs.Map(52)
        with pytest.raises(SchemaError):
            specs.Map('xo')
        with pytest.raises(SchemaError):
            specs.Map({'x': 3, 'y': 6})

        # Should fail on sequences with < or > 2 items
        with pytest.raises(SchemaError):
            specs.Map((int, str, bool))
        with pytest.raises(SchemaError):
            specs.Map((int,))

        # Should fail on unhashable keys
        with pytest.raises(SchemaError):
            specs.Map((dict, float))
        with pytest.raises(SchemaError):
            specs.Map((list, float))


class TestSeq:

    def test_validate_spec(self):
        # Should convert type values to Atoms
        spec = specs.Seq(str)
        assert spec.spec == specs.Atom(str)
        spec = specs.Seq(dict)
        assert spec.spec == specs.Atom(dict)

        # Should allow nested Specs
        kids = specs.Model({'name': str})
        spec = specs.Seq(kids)
        assert spec.spec == kids
        assert spec.spec.spec['name'] == specs.Atom(str)

    def test_validate(self):
        spec = specs.Seq(int)

        # Should fail on non-sequence type
        with pytest.raises(ValidationError):
            spec.validate(5)
        with pytest.raises(ValidationError):
            spec.validate({1: 2})

        # Should fail if item type doesn't match
        with pytest.raises(ValidationError):
            spec.validate(('foo', 'bar', 'baz'))
        with pytest.raises(ValidationError):
            spec.validate([1, 2, 3.3])

        # Happy path
        value = [1, 2, 3]
        assert spec.validate(value) == value

        # Should work with nested CompoundSpec
        spec = specs.Seq(specs.Model({'name': str, 'age': int}))
        value = [
            {'name': 'bob', 'age': 33},
            {'name': 'sue', 'age': 66},
        ]
        assert spec.validate(value) == value


def test_from_python():
    assert type(specs.from_python({'foo': str})) is specs.Model
    # assert type(specs.from_python([int])) is specs.Seq
