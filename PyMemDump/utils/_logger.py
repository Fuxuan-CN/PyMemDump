
from rich.logging import RichHandler
import logging

# 配置日志
logging.basicConfig(
    level="DEBUG",
    format="| %(name)s | %(threadName)-10s ===>> %(message)s",
    datefmt="%X",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("MemoryDump")
""" Memory dump logger """

def test_log():
    logger.debug("这是一条debug信息")
    logger.info("这是一条info信息")
    logger.warning("这是一条warning信息")
    logger.error("这是一条error信息")
    logger.critical("这是一条critical信息")

if __name__ == "__main__":
    test_log()