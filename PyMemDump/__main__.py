""" module for command line interface """
from PyMemDump import MemoryDumper
from .utils._auto_language import auto_language

if __name__ == "__main__":
    MemoryDumper.dump_with_args(language=auto_language())