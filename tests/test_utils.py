import pytest

from datalayer import utils


@pytest.fixture
def parent():
    class Parent:
        pass
    return Parent


@pytest.fixture
def child1(parent):
    class Child1(parent):
        pass
    return Child1


@pytest.fixture
def child2(parent):
    class Child2(parent):
        pass
    return Child2


@pytest.fixture
def grandchild1(child1):
    class GrandChild1(child1):
        pass
    return GrandChild1


def test_typename(parent):
    assert utils.typename(str) == 'str'
    assert utils.typename('foo') == 'str'
    assert utils.typename(parent) == parent.__name__
    assert utils.typename(parent()) == parent.__name__


def test_subdict(parent, child1, grandchild1):
    d = utils.SubclassDict({int: 'x', str: 'y'})
    assert d[int] == 'x'
    assert d.get(int) == 'x'
    assert d.get(list) is None
    d[parent] = 3
    assert d[parent] == 3
    assert d[child1] == 3
    assert d[grandchild1] == 3
    d[child1] = 5
    assert d[grandchild1] == 5

    with pytest.raises(KeyError):
        _ = d[dict]
    with pytest.raises(TypeError):
        d.update({1: 2})
    with pytest.raises(TypeError):
        d.update(foo='bar')

    with pytest.raises(TypeError):
        utils.SubclassDict({'x': 5})
    with pytest.raises(TypeError):
        utils.SubclassDict({str: 5}, foo=6)
    with pytest.raises(TypeError):
        utils.SubclassDict(foo=6)
    with pytest.raises(TypeError):
        utils.SubclassDict(**{1: 2})
