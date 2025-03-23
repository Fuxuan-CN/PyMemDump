"""
This is the main module of the PyMemDump package.
It exports the MemoryDumper class, which can be used to dump the memory of a process.
Example usage:

```python
from PyMemDump import MemoryDumper

dumper = MemoryDumper(process_desc=12345, save_path="./your/path")
dumper.dump()
```
"""
from .core import MemoryDumper

__all__ = ["MemoryDumper"]

