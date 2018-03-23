import pytest

from datalayer import utils


@pytest.fixture
def base_cls():
    class BaseCls:
        pass
    return BaseCls


@pytest.fixture
def child_cls1(base_cls):
    class ChildCls1(base_cls):
        pass
    return ChildCls1


@pytest.fixture
def child_cls2(child_cls1):
    class ChildCls2(child_cls1):
        pass
    return ChildCls2


def test_typename(base_cls):
    assert utils.typename(str) == 'str'
    assert utils.typename('foo') == 'str'
    assert utils.typename(base_cls) == 'BaseCls'
    assert utils.typename(base_cls()) == 'BaseCls'


def test_subclassdict(base_cls, child_cls1, child_cls2):
    d = utils.SubclassDict({int: 'x', str: 'y'})
    assert d[int] == 'x'
    assert d.get(int) == 'x'
    assert d.get(list) is None
    d[base_cls] = 3
    assert d[base_cls] == 3
    assert d[child_cls1] == 3
    assert d[child_cls2] == 3

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
