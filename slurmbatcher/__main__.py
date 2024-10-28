import logging
import subprocess
import tempfile
import tomllib
from math import prod
from pathlib import Path

from slurmbatcher import shfotmat
from slurmbatcher.cli import cli
from slurmbatcher.types import Configuration
from slurmbatcher.utils import dict_product, get_fstring_parameters

logger = logging.getLogger(__name__)


def create_sbatch_scripts(config: Configuration):
    sbatch_script = f"""#!/bin/bash\n"""
    for key, value in config.sbatch.parameters.items():
        sbatch_script += f"#SBATCH --{key}={value}\n"

    command_parameters = get_fstring_parameters(config.command_template)
    parameter_arities = [len(mapping) for mapping in config.matrix.parameters.values()]
    num_steps = prod(parameter_arities)
    sbatch_script += f"#SBATCH --array=0-{num_steps-1}\n\n"

    parameter_getters = {}
    for parameter_index, parameter in enumerate(config.matrix.parameters.items()):
        (parameter_name, parameter_values) = parameter
        if (
            parameter_name not in command_parameters
            and "**parameters" not in command_parameters
        ):
            logger.warning(
                f"Parameter '{parameter_name}' is not present in the command template. Add it to the template or use the rest placeholder '{{**parameters}}'"
            )
            continue

        safe_parameter_name = shfotmat.safe_variable_name(parameter_name)

        arity = parameter_arities[parameter_index]
        sbatch_script += (
            shfotmat.array(safe_parameter_name, parameter_values)
            if arity > 1
            else shfotmat.variable(safe_parameter_name, parameter_values[0])
        )
        combinations_so_far = prod(parameter_arities[:parameter_index])
        parameter_getters[parameter_name] = (
            f"${{{safe_parameter_name}[$(( (SLURM_ARRAY_TASK_ID / {combinations_so_far}) % {arity} ))]}}"
            if arity > 1
            else f"${{{safe_parameter_name}}}"
        )

    explicit_params = set(
        parameter_name
        for parameter_name in parameter_getters.keys()
        if parameter_name in command_parameters
    )
    rest_params = parameter_getters.keys() - explicit_params

    for placeholder in command_parameters:
        if placeholder == "**parameters":
            if len(rest_params) == 0:
                logger.warning(
                    "No parameters left to be filled into the rest placeholder {{**parameters}}"
                )
        elif not placeholder in parameter_getters:
            logger.warning(f"parameter {placeholder} not found in matrix")
            parameter_getters[placeholder] = ""

    rest_params_string = " ".join(
        f"--{parameter_name}={parameter_getters[parameter_name]}"
        for parameter_name in rest_params
    )

    final_command = config.command_template.format_map(
        {**parameter_getters, "**parameters": rest_params_string}
    )

    sbatch_script += f"\n{final_command}\n"

    return sbatch_script


def main():
    args = cli.parse_args()
    cwd = Path.cwd()

    if not args.config.exists():
        print(f"config file {args.config} does not exist")
        exit(1)

    with open(args.config, "rb") as config_file:
        config = tomllib.load(config_file)

    parsed = Configuration.model_validate(config)
    script = create_sbatch_scripts(parsed)

    if args.dry_run:
        print(script)
        exit(0)

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as script_file:
        script_file.write(script)
        script_file.flush()

        subprocess.run(["sbatch", "--chdir", cwd.absolute(), script_file.name])


if __name__ == "__main__":
    main()
