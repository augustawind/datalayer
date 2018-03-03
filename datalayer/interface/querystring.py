from typing import Mapping, List

from datalayer import config
from datalayer.interface.datastructures import Query
from datalayer.specs import Spec


def parse_url_params(model: Spec, url_params: Mapping[str, str]) -> List[Query]:
    for key, val in url_params.items():
        parts = key.split(config.QUERYSTRING_SEP)
