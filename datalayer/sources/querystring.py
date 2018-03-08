from typing import Mapping, List

from datalayer import config
from datalayer.datastructures import Query
from datalayer.exceptions import SpecError
from datalayer.specs import CompoundSpec


def parse_url_params(spec: CompoundSpec, url_params: Mapping[str, str]) -> List[Query]:
    queries = []
    for key, val in url_params.items():
        parts = key.split(config.QUERYSTRING_SEP)
        for part in parts:
            try:
                sub_spec = spec.get(part)
            except SpecError:
                break
        queries.append(Query(parts, 'eq', sub_spec))
    return queries
