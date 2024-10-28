import argparse
from pathlib import Path

cli = argparse.ArgumentParser(
    prog="slurmbatcher", description="create sbatch configs easily"
)
cli.add_argument("config", type=Path, help="path to the config file")
cli.add_argument(
    "--dry-run", action="store_true", help="print sbatch script instead of running it"
)
