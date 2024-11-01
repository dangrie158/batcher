# slurmbatcher

Easily create sbatch scripts for running jobs on a cluster.

## Installation

```bash
pip install slurmbatcher
```

## Usage

```bash
usage: slurmbatcher [-h] [--dry-run] config

create sbatch configs easily

positional arguments:
  config      path to the config file

options:
  -h, --help  show this help message and exit
  --dry-run   print sbatch script instead of running it
```

## Configuration
Create a configuration file in toml format. The configuration file must contain a `command_template` and a `matrix.parameters` section. The `command_template` is a string that will be used to generate the sbatch script. The `matrix.parameters` section contains the parameters that will be used to generate the cartesian product of all possible parameter combinations.
Additional parameters can be added to the `sbatch.parameters` section to specify sbatch parameters.

### `command_template`
The `command_template` is a string that will be used to generate the commands that are run on the cluster.
You can use placeholders in the `command_template` string to insert parameters from the `matrix.parameters` section. Placeholders are enclosed in curly braces that contain the name of the parameter to be inserted. You can also use the special `**parameters` placeholder to insert all parameters as keyword arguments. The `**parameters` placeholder will insert all parameters as keyword arguments in the form `--parameter-name value`.

The command template can contain arbitrary bash code and span multiple lines. The command template will be written to the sbatch script as is. The placeholders will be replaced with the corresponding values from the matrix configuration.

#### command_template mini language
You can use format specifiers to format the inserted values. The format specifier is a colon followed by a format string. The format string is passed to the python `format` method. For example, `{seed:04d}` will format the `seed` parameter as a zero-padded 4-digit integer. Additionally the following format specifiers are available:
- `:value`: gets replaced with the value of the parameter in the current matrix configuration (same as no format specifier)
- `:name`: gets replaced with the name of the parameter
- `:option`: gets replaces with a keyword argument in the form `--name value`

### `sbatch.parameters` section
You can specify additional parameters for the sbatch script in the `sbatch.parameters` section. The parameters are written as `#SBATCH --parameter-name=value` lines in the generated sbatch script. You can use all [parameters available](https://slurm.schedmd.com/sbatch.html) in the sbatch command, except for `array` as this is automatically generated.

### `matrix.parameters` section
The `matrix.parameters` section contains the parameters that will be used to generate the cartesian product of all possible parameter combinations. Each parameter is specified as a list of values or a scalar. The cartesian product of all parameter values will be generated and each combination will be used to generate a task in the array job.

### `matrix.jobs` section
If you specify parameters in the `matrix.jobs` section instead of the `matrix.parameters` section, the cartesian product of all parameter values will be generated and each combination will be used to generate a **seperate** job. This can be used if you want to split the array into different jobs for a better overview (e.g. to send emails for each job separately). Technically this will create multiple sbatch scripts that will be submitted to the cluster for each combination in the cartesian product of the parameters.

## Example:

running `slurmbatcher example.toml` with the following `example.toml`:

```toml
command_template="""\
    echo --cwd {workdir} \
    python $HOME/evoprompt/main.py --task {task} {evaluation-strategy:option} --{seed:name} {seed} {**parameters}\
"""
[sbatch.parameters]
partition = "gpu"
gpus = 1
mail-type = "END,FAIL"
mail-user = "griesshaber@hdm-stuttgart.de"
cpus-per-task = 4
nodelist = "tars"


[matrix.parameters]
workdir="$HOME/evoprompt"
seed = 42
evaluation-strategy = ["shortest-first", "hardest-first"]
rest=["1", 2]

[matrix.jobs]
task = ["sst2", "sst5"]
```

will generate 2 sbatch scripts and submit it to the cluster. The generated sbatch scripts will look like this:

```bash
 1 #!/bin/bash
 #SBATCH --partition=gpu
 #SBATCH --gpus=1
 #SBATCH --mail-type=END,FAIL
 #SBATCH --mail-user=griesshaber@hdm-stuttgart.de
 #SBATCH --cpus-per-task=4
 #SBATCH --nodelist=tars
 #SBATCH --array=0-3

task='sst5'
workdir='$HOME/evoprompt'

seed='42'

rest_list=( '1' '2' )
rest=${rest_list[$(((SLURM_ARRAY_TASK_ID / 1) % 1))]}

evaluation_strategy_list=( 'simple' 'early-stopping' 'shortest-first' 'hardest-first' )
evaluation_strategy=${evaluation_strategy_list[$(((SLURM_ARRAY_TASK_ID / 2) % 2))]}

python ${workdir}/train.py --task ${task} --evaluation-strategy ${evaluation_strategy} --seed ${seed} --rest=${rest}```
```
which will run the following commands on the cluster in 2 separate jobs:

```bash
# commands in Job 1
python $HOME/evoprompt/train.py --task sst2 --evaluation-strategy shortest-first --seed 42 --rest=2
python $HOME/evoprompt/train.py --task sst2 --evaluation-strategy hardest-first --seed 42 --rest=1
python $HOME/evoprompt/train.py --task sst2 --evaluation-strategy hardest-first --seed 42 --rest=2
python $HOME/evoprompt/train.py --task sst2 --evaluation-strategy shortest-first --seed 42 --rest=1

# commands in Job 2
python $HOME/evoprompt/train.py --task sst5 --evaluation-strategy shortest-first --seed 42 --rest=2
python $HOME/evoprompt/train.py --task sst5 --evaluation-strategy hardest-first --seed 42 --rest=1
python $HOME/evoprompt/train.py --task sst5 --evaluation-strategy hardest-first --seed 42 --rest=2
python $HOME/evoprompt/train.py --task sst5 --evaluation-strategy shortest-first --seed 42 --rest=1
```
