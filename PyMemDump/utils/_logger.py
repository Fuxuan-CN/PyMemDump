
from rich.logging import RichHandler
import logging

# 配置日志
logging.basicConfig(
    level="DEBUG",
    format="| %(threadName)-10s ===>> %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("MemoryDump")
""" Memory dump logger """

def test_log():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

if __name__ == "__main__":
    test_log()