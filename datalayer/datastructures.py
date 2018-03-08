from types import SimpleNamespace
from typing import (
    Any,
    NamedTuple,
    Tuple,
)

OPERATORS = SimpleNamespace(**{op: op for op in (
    'eq',
    'gt',
    'gte',
    'lt',
    'lte',
    'ne',
)})


class Query(NamedTuple):
    keys: Tuple[str]
    operator: str
    value: Any
