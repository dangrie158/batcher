from itertools import chain, product
from string import Formatter
from typing import Any, Generator, Iterable


def flatten(container: Iterable) -> Iterable:
    for i in container:
        if isinstance(i, (list, tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i


def dict_product(dict_) -> Generator[dict, Any, None]:
    keys = dict_.keys()
    for values in product(*dict_.values()):
        yield dict(zip(keys, values))


def to_string_list(input_: Any) -> Iterable[str]:
    return map(str, flatten([input_]))


def get_fstring_parameters(string: str) -> Iterable[str]:
    return [
        field_name
        for _, field_name, _, _ in Formatter().parse(string)
        if field_name is not None
    ]
