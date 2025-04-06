
from rich.logging import RichHandler
from rich.theme import Theme
import logging
from rich.console import Console
from ..exec_hook import ExtractException

my_log_theme = Theme(
    {
        "logging.level.debug": "bold green",
        "logging.level.info": "bold cyan",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold magenta"
    }
)

# 配置日志
logging.basicConfig(
    level="DEBUG",
    format="| %(name)s | %(threadName)-10s ===>> %(message)s",
    datefmt="%X",
    handlers=[RichHandler(console=Console(theme=my_log_theme), rich_tracebacks=True, markup=True)]
)

logger = logging.getLogger("MemoryDump")
""" Memory dump logger """

def test_log():
    logger.debug("这是一条debug信息")
    logger.info("这是一条info信息")
    logger.warning("这是一条warning信息")
    logger.error("这是一条error信息")
    logger.critical("这是一条critical信息")

    try:
        1 / 0
    except Exception as e:
        err_msg = ExtractException(type(e), e, e.__traceback__, panel=False)
        logger.error(err_msg)

if __name__ == "__main__":
    test_log()