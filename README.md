# batcher

Easily create sbatch scripts for running jobs on a cluster.

## Example:

running `python -m batcher example.toml` with the following `example.toml`:

```toml
command_template="""\
    echo --cwd {workdir} \
    python $HOME/evoprompt/main.py --task {task} --evaluation-strategy {evaluation-strategy} --seed {seed} {**parameters}\
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
