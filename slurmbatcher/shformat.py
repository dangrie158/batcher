SHEBANG = "#!/bin/bash"


def sbatch_parameter(name: str, value: str) -> str:
    return f"#SBATCH --{name}={value}"


def safe_variable_name(name: str) -> str:
    return name.replace("-", "_")


def array(values: list[str]) -> str:
    return f"""( {" ".join(f"'{value}'" for value in values)} )"""


def variable(value: str) -> str:
    return f"'{value}'"


def variable_getter(variable_name: str) -> str:
    return f"${{{variable_name}}}"


def array_getter(variable_name: str, index_expression: str) -> str:
    return f"${{{variable_name}[{index_expression}]}}"


def calculate(expression: str) -> str:
    return f"$(({expression}))"
