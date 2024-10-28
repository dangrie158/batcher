# slurmbatcher

Easily create sbatch scripts for running jobs on a cluster.

## Installation

```bash
pip install slurmbatcher
```

## Configuration
Create a configuration file in toml format. The configuration file must contain a `command_template` and a `matrix.parameters` section. The `command_template` is a string that will be used to generate the sbatch script. The `matrix.parameters` section contains the parameters that will be used to generate the cartesian product of all possible parameter combinations.
Additional parameters can be added to the `sbatch.parameters` section to specify sbatch parameters.

### command_template mini language
You can use placeholders in the `command_template` string to insert parameters from the `matrix.parameters` section. Placeholders are enclosed in curly braces that contain the name of the parameter to be inserted. You can also use the special `**parameters` placeholder to insert all parameters as keyword arguments. The `**parameters` placeholder will insert all parameters as keyword arguments in the form `--parameter-name value`.

You can use format specifiers to format the inserted values. The format specifier is a colon followed by a format string. The format string is passed to the python `format` method. For example, `{seed:04d}` will format the `seed` parameter as a zero-padded 4-digit integer. Additionally the following format specifiers are available:
- `:value`: gets replaced with the value of the parameter in the current matrix configuration (same as no format specifier)
- `:name`: gets replaced with the name of the parameter
- `:option`: gets replaces with a keyword argument in the form `--name value`

## Example:

running `slurmbatcher example.toml` with the following `example.toml`:

```toml
command_template="""\
    echo --cwd {workdir} \
    python $HOME/evoprompt/main.py --task {task} {evaluation-strategy:option} --{seed:name}={seed} {**parameters}\
"""
[sbatch.parameters]
partition = "gpu"
gpus = 1
mail-type = "END,FAIL"
mail-user = "griesshaber@hdm-stuttgart.de"
cpus-per-task = 4


[matrix.parameters]
task = ["sst2", "sst5"]
seed = 42
evaluation-strategy = ["simple", "fast"]
```

will generate the following sbatch script and submit it to the cluster (use `--dry-run` to only print the script):

```bash
#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=griesshaber@hdm-stuttgart.de
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=tars
#SBATCH --array=0-15

task=( 'sst2' 'sst5' )
workdir='$HOME/evoprompt'
rest=( '1' '2' )
seed='42'
evaluation_strategy=( 'simple' 'early-stopping' 'shortest-first' 'hardest-first' )

echo --cwd ${workdir} python $HOME/evoprompt/main.py --task ${task[$(( (SLURM_ARRAY_TASK_ID / 1) % 2 ))]} --evaluation-strategy ${evaluation_strategy[$(( (SLURM_ARRAY_TASK_ID / 4) % 4 ))]} --seed ${seed} --rest=${rest[$(( (SLURM_ARRAY_TASK_ID / 2) % 2 ))]}
```

which will run the following commands on the cluster:

```bash
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy simple --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy shortest-first --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy shortest-first --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy hardest-first --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy hardest-first --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy hardest-first --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy hardest-first --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy simple --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy simple --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy simple --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy early-stopping --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy early-stopping --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy early-stopping --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy early-stopping --seed 42 --rest=2
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst2 --evaluation-strategy shortest-first --seed 42 --rest=1
echo --cwd $HOME/evoprompt python /home/ma/g/griesshaber/evoprompt/main.py --task sst5 --evaluation-strategy shortest-first --seed 42 --rest=1
```
