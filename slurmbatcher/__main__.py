import subprocess
import tomllib
from math import prod
from typing import Generator, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from slurmbatcher import shformat
from slurmbatcher.cli import cli
from slurmbatcher.logging import logger
from slurmbatcher.types import Configuration, JobScript
from slurmbatcher.utils import ParameterFormatter, dict_product, get_fstring_parameters


def sanity_check(config: Configuration):
    if not config.command_template:
        logger.error("No command template found")
        exit(1)

    if not config.matrix.parameters:
        logger.warning("No parameters found in matrix")

    for parameter_name, values in config.matrix.parameters.items():
        if not values:
            logger.warning(f"No values found for parameter '{parameter_name}'")

    duplicate_parameters = set(config.matrix.parameters.keys()) & set(config.matrix.jobs.keys())
    if len(duplicate_parameters) > 0:
        logger.error("matrix.parameters and matrix.tasks must not have any keys in common")
        logger.info(f"Duplicate parameters: {duplicate_parameters}")
        exit(1)

    command_parameters = get_fstring_parameters(config.command_template)
    # Check if all parameters in the command template are present in the matrix
    for parameter in command_parameters:
        if (
            parameter != "**parameters"
            and parameter not in config.matrix.parameters
            and parameter not in config.matrix.jobs
        ):
            logger.error(f"Parameter '{parameter}' not found in matrix")
            exit(1)

    # Check if all parameters in the matrix are used in the command template
    if "**parameters" not in command_parameters:
        for parameter in config.matrix.parameters.keys():
            if parameter not in command_parameters:
                logger.warning(
                    f"Parameter '{parameter}' is not used in the command template and no '**parameters' placeholder found"
                )
                logger.info(
                    "Consider adding it to the command template, removing it from the matrix or add a '**parameters' placeholder"
                )


def create_sbatch_scripts(config: Configuration) -> Iterable[JobScript]:
    for job_config in dict_product(config.matrix.jobs):
        sbatch_script = create_sbatch_script(job_config, config)
        yield sbatch_script


def create_sbatch_script(job_config: dict[str, str], config: Configuration) -> JobScript:
    sbatch_script = shformat.SHEBANG + "\n"
    for key, value in config.sbatch.parameters.items():
        sbatch_script += f"{shformat.sbatch_parameter(key, value)}\n"

    command_parameters = get_fstring_parameters(config.command_template)
    parameter_arities = [len(mapping) for mapping in config.matrix.parameters.values()]
    num_steps = prod(parameter_arities)
    sbatch_script += f"#SBATCH --array=0-{num_steps-1}\n\n"

    parameter_getters = {}

    for job_parameter_name, job_parameter_value in job_config.items():
        safe_parameter_name = shformat.safe_variable_name(job_parameter_name)
        sbatch_script += f"{safe_parameter_name}={shformat.variable(job_parameter_value)}\n"
        parameter_getters[job_parameter_name] = f"${{{safe_parameter_name}}}"

    for parameter_index, parameter in enumerate(config.matrix.parameters.items()):
        (parameter_name, parameter_values) = parameter

        safe_parameter_name = shformat.safe_variable_name(parameter_name)
        arity = parameter_arities[parameter_index]
        combinations_so_far = prod(parameter_arities[:parameter_index])
        if arity > 1:
            serialized_parameter_value = shformat.array(parameter_values)
            index_expression = shformat.calculate(f"(SLURM_ARRAY_TASK_ID / {combinations_so_far}) % {arity}")
            safe_parameter_list_name = f"{safe_parameter_name}_list"
            sbatch_script += f"{safe_parameter_list_name}={serialized_parameter_value}\n"
            sbatch_script += (
                f"{safe_parameter_name}={shformat.array_getter(safe_parameter_list_name, index_expression)}\n"
            )
            parameter_getters[parameter_name] = shformat.variable_getter(safe_parameter_name)
        else:
            serialized_parameter_value = shformat.variable(parameter_values[0])
            sbatch_script += f"{safe_parameter_name}={serialized_parameter_value}\n"
            parameter_getters[parameter_name] = shformat.variable_getter(safe_parameter_name)
        sbatch_script += "\n"

    explicit_params = set(
        parameter_name for parameter_name in parameter_getters.keys() if parameter_name in command_parameters
    )
    rest_params = parameter_getters.keys() - explicit_params

    rest_params_string = " ".join(
        f"--{parameter_name}={parameter_getters[parameter_name]}" for parameter_name in rest_params
    )

    final_command = ParameterFormatter().format(
        config.command_template,
        **{**parameter_getters, "**parameters": rest_params_string},
    )

    sbatch_script += f"\n{final_command}"
    return JobScript(job_config, sbatch_script)


def main():
    args = cli.parse_args()
    console = Console()

    if not args.config.exists():
        console.print(f"config file {args.config} does not exist")
        exit(1)

    with open(args.config, "rb") as config_file:
        config_contents = tomllib.load(config_file)

    config = Configuration.model_validate(config_contents)
    sanity_check(config)
    job_scripts = create_sbatch_scripts(config)

    if args.dry_run:
        for job_config, script in job_scripts:
            formatted_script = Syntax(script, "bash", line_numbers=True)
            console.print(Panel.fit(formatted_script, title=str(job_config)))
        exit(0)

    for job_config, script in job_scripts:
        # srteam the script to sbatch stdin
        process = subprocess.Popen(
            ["sbatch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process.stdin.write(script)
        process.stdin.close()
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            console.print(f"Error submitting job: {stderr}")
            exit(1)
        job_id = stdout.split()[-1].strip()
        console.print(f"Submitted job {job_config} as job {job_id}")


if __name__ == "__main__":
    main()
