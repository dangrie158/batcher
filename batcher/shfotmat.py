def safe_variable_name(name: str) -> str:
    return name.replace("-", "_")


def array(name: str, values: list[str]) -> str:
    safe_name = safe_variable_name(name)
    return f"""{safe_name}=( {" ".join(f"'{value}'" for value in values)} )\n"""


def variable(name: str, value: str) -> str:
    safe_name = safe_variable_name(name)
    return f"{safe_name}='{value}'\n"
