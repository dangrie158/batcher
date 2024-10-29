from typing import Annotated, NamedTuple

from pydantic import BaseModel, BeforeValidator

from slurmbatcher.utils import to_string_list

String = Annotated[str, BeforeValidator(str)]
StringList = Annotated[list[str], BeforeValidator(to_string_list)]


class Matrix(BaseModel):
    jobs: dict[str, StringList] = {}
    parameters: dict[str, StringList]


class SBatchSettings(BaseModel):
    parameters: dict[str, String] = {}


class Configuration(BaseModel):
    command_template: str
    sbatch: SBatchSettings
    matrix: Matrix


class JobScript(NamedTuple):
    job_config: dict[str, str]
    sbatch_script: str
