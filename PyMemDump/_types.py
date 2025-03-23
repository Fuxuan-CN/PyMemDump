from typing import Any

Process_Desc = str | int | None
""" Type of process description, such as process ID or name. """

class Process:
    """ process type caster"""

    def __call__(self, process_desc: Any) -> Process_Desc:
        """ cast process description to str or int"""
        return process_desc
    
class MemAddress:
    """Memory address type caster"""

    def __call__(self, address: Any) -> int:
        """Cast memory address to int"""
        if isinstance(address, str):
            try:
                if address.startswith("0x"):
                    address = int(address, 16)
                elif address.startswith("0b"):
                    address = int(address, 2)
                elif address.startswith("0o"):
                    address = int(address, 8)
                else:
                    address = int(address)
            except ValueError as e:
                raise ValueError(f"Invalid address format: {address}. Error: {e}")
        elif not isinstance(address, int):
            raise TypeError(f"Expected int or str, got {type(address).__name__}")
        return address