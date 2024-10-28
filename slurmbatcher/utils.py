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


class ParameterFormatter(Formatter):

    def get_value(self, key: str | int, args, kwargs):
        if key not in kwargs:
            raise KeyError(key)
        else:
            return key, kwargs[key]

    def format_field(self, value_tuple: tuple[str, str], format_spec: str):
        name, value = value_tuple
        if name.startswith("**"):
            return value
        match format_spec:
            case "" | "value":
                return value
            case "option":
                return f"--{name} {value}"
            case "name":
                return name
            case _:
                return super().format_field(value, format_spec)
