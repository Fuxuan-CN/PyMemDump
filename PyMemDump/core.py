from ._types import Process_Desc
import json
from typing import Literal
from .i18n import get_text
from .utils import (
    dump_memory, 
    get_pid_with_name, 
    is_process_running, 
    get_total_memory_size, 
    dump_memory_by_address,
    concurrent_dump_memory,
    get_all_memory_addr_range,
    suspend_process,
    resume_process
)
from .constants import CPU_COUNT
from ._types import (
    Process,
    MemAddress
)
from .exceptions import ProcessNotRunning
from ._logger import logger
import argparse

class MemoryDumper:
    """
    Main class for dumping the memory of a process.

    This class provides a simple interface for dumping the memory of a running process.
    It supports specifying the target process by either its name or PID, and allows
    users to choose the output directory for the memory dump files.

    Attributes:
        process_target (Process_Desc): Description of the target process (PID or name).
        pid (int): Process ID of the target process.
        process_name (str): Name of the target process.
        save_path (str): Output directory for the memory dump files.
        process_mem_size (int): Total memory size of the target process.
        ignore_read_error (bool): Flag to ignore read errors during memory dumping.

    Methods:
        dump(): Dumps the memory of the target process.
        dump_with_args(): Dumps the memory of the target process using command line arguments.

    Example:
        ```python
            dumper = MemoryDumper(process_desc="notepad.exe", save_path="C:\\dumps")
            dumper.dump()
        ```

    Note:
        The target process must be running when calling the dump method.
        The output directory must exist and be writable.
    """

    def __init__(self, 
        process_desc: Process_Desc = None, 
        save_path: str = None, 
        concurrent: bool = False, 
        workers: int = CPU_COUNT, 
        ignore_read_error: bool = False,
        content_fmt: Literal["hex", "bin", "ascii"] = "bin",
        encoding: str = "utf-8"
    ) -> None:
        self.process_target = process_desc
        """ user input process description, can be pid or process name """
        self.pid: int = None
        """ process id """
        self.process_name: str = None
        """ process name """
        self.save_path: str = save_path
        """ output directory to save the memory dump """
        self.process_mem_size: int = None
        """ total memory size of the process """
        self.ignore_read_error: bool = ignore_read_error
        """ ignore read errors when dumping memory """
        self.concurrent: bool = concurrent
        """ concurrent dumping flag """
        self.workers: int = workers
        """ number of workers to use for concurrent dumping """
        self.data_fmt = content_fmt
        """ content format to save the memory dump """
        self.encoding = encoding
        """ encoding to save the memory dump """
        logger.info("MemoryDumper initialized.")
        self.pid = self._extra_process_id(self.process_target)

    def _is_process_running(self) -> bool:
        """ Checks if the process is running """
        if self.pid is None:
            logger.warning("Process ID is not set.")
            return False
        return is_process_running(self.pid)
    
    def _stop_process(self) -> None:
        """ Stops the process """
        suspend_process(self.pid)

    def _resume_process(self) -> None:
        """ Resumes the process """
        resume_process(self.pid)
    
    def get_all_addr_range(self, to_json: bool = False) -> dict[str, str | int | list[tuple[str, str]]:]:
        """
        Get all memory addresses of the target process.

        Returns:
            list[tuple[int, int]]: List of memory addresses of the target process.
        """
        self._stop_process()
        logger.info(f"Getting all memory addresses of process {self.process_target}.")
        if not self._is_process_running():
            raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
        data_addrs = {
            "process_name": self.process_name,
            "pid": self.pid,
            "addresses": get_all_memory_addr_range(self.pid)
        }
        if to_json:
            with open(f"{self.process_name or self.pid}_all_addresses.json", "w") as f:
                json.dump(data_addrs, f, indent=4)
        logger.info(f"Memory addresses of process {self.process_target} generated.")
        self._resume_process()
        return data_addrs
    
    def _extra_process_id(self, desc: Process_Desc) -> int:
        """
        Get the process id from the process description.

        Args:
            desc (Process_Desc): Description of the target process (PID or name).

        Returns:
            int: Process ID of the target process.
        """
        if isinstance(desc, int):
            return desc
        elif isinstance(desc, str):
            pid = get_pid_with_name(desc)
            self.process_name = desc
            logger.info(f"Process name: {desc}, PID: {pid}")
            return pid
        else:
            raise TypeError("expected int or str for process_desc, such as pid or process name.")

    def dump(self) -> None:
        """ Dumps the memory of the process """
        self._stop_process()
        try:
            if self.concurrent:
                self.dump_memory_concurrent(workers=self.workers)
            else:
                logger.info(f"Dumping memory of process {self.process_target} to {self.save_path}.")

                if not self._is_process_running():
                    raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
                
                # get the total memory size of the process
                self.process_mem_size = get_total_memory_size(self.pid)

                dump_memory(self.pid, self.save_path, self.process_mem_size, self.ignore_read_error)
        except KeyboardInterrupt:
            logger.critical("Memory dumping interrupted by user.")
        finally:
            self._resume_process()

    def dump_memory_by_address(self, start_address: int, end_address: int) -> None:
        """
        Dumps the memory of the target process within a specified address range.

        Args:
            start_address (int): Starting address of the memory range to dump.
            end_address (int): Ending address of the memory range to dump.
        """
        self._stop_process()
        try:
            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            dump_memory_by_address(self.pid, self.save_path, start_address, end_address, self.ignore_read_error, content_fmt=self.data_fmt, encoding=self.encoding)
        except KeyboardInterrupt:
            logger.critical("Memory dumping interrupted by user.")
        finally:
            self._resume_process()

    def dump_memory_concurrent(self, workers: int = CPU_COUNT) -> None:
        """ Dumps the memory of the target process concurrently """
        try:
            self._stop_process()
            logger.info(f"Dumping memory of process {self.process_target} to {self.save_path} concurrently.")

            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            concurrent_dump_memory(self.pid, self.save_path, self.ignore_read_error, workers=workers, content_fmt=self.data_fmt, encoding=self.encoding)
        except KeyboardInterrupt:
            logger.critical("Memory dumping interrupted by user.")
        finally:
            self._resume_process()

    @staticmethod
    def dump_with_args(language: Literal["en_US", "zh_CN"] = "zh_CN") -> None:
        """ Dumps the memory of the process with command line arguments 
        Args:
            language (str): language to use for the tool, default is zh_CN.
        """
        parser = argparse.ArgumentParser(description=get_text(language, "tool_desc"))
        parser.add_argument("--scan_addr", action="store_true", help=get_text(language, "scan_addr"))
        parser.add_argument("--concurrent", action="store_true", help=get_text(language, "concurrent"))
        parser.add_argument("-w", "--workers", type=int, help=get_text(language, "workers"), default=CPU_COUNT)
        parser.add_argument("-p", "--process", type=Process(), help=get_text(language, "process"), required=True)
        parser.add_argument("--by_addr", action="store_true", help=get_text(language, "by_addr"))
        parser.add_argument("-o", "--output", type=str, help=get_text(language, "output"), default="MemDumped")
        parser.add_argument("-i", "--ignore-read-error", action="store_true", help=get_text(language, "ignore-read-error"))
        parser.add_argument("-s", "--start-address", type=MemAddress(), help=get_text(language, "start-address"))
        parser.add_argument("-e", "--end-address", type=MemAddress(), help=get_text(language, "end-address"))
        parser.add_argument("-f", "--content-fmt", type=str, choices=["hex", "bin", "ascii"], default="bin", help=get_text(language, "content-fmt"))
        parser.add_argument("-c", "--encoding", type=str, default="utf-8", help=get_text(language, "encoding"))
        args = parser.parse_args()

        if args.scan_addr:
            # 扫描不需要指定格式，导出的时候再指定
            md = MemoryDumper(process_desc=args.process, save_path=args.output)
            md.get_all_addr_range(to_json=True)
            return

        if args.concurrent and args.by_addr:
            raise ValueError("concurrent and by_addr cannot be set at the same time.")

        if args.concurrent:
            md = MemoryDumper(process_desc=args.process, save_path=args.output, concurrent=True, workers=args.workers, ignore_read_error=args.ignore_read_error, content_fmt=args.content_fmt, encoding=args.encoding)
            md.dump()
            return
        
        if not args.by_addr and (args.start_address is not None or args.end_address is not None):
            raise ValueError("start_address and end_address can only be specified when by_addr is set.")

        if args.by_addr:
            if args.start_address is None or args.end_address is None:
                raise ValueError("start_address and end_address must be specified when by_addr is set.")
            md = MemoryDumper(process_desc=args.process, save_path=args.output, ignore_read_error=args.ignore_read_error, content_fmt=args.content_fmt, encoding=args.encoding)
            if (isinstance(args.start_address, str) and args.start_address.startswith("0x")) \
                and (isinstance(args.end_address, str) and args.end_address.startswith("0x")):
                addr_16_start = int(args.start_address, 16)
                addr_16_end = int(args.end_address, 16)
            else:
                addr_16_start = args.start_address
                addr_16_end = args.end_address
            md.dump_memory_by_address(addr_16_start, addr_16_end)
            return
        else:
            md = MemoryDumper(process_desc=args.process, save_path=args.output, ignore_read_error=args.ignore_read_error, content_fmt=args.content_fmt, encoding=args.encoding)
            md.dump()
            return

if __name__ == "__main__":
    md = MemoryDumper(process_desc="notepad.exe", save_path="C:\\Users\\user\\Desktop\\notepad_dump")
    md.dump()