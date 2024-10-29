import logging

from rich.logging import RichHandler
from rich.traceback import install

install(show_locals=True)

FORMAT = "%(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__package__)
