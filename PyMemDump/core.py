from .utils._types import Process_Desc
import json
from typing import Literal
from .i18n import get_text
from .utils.constants import CPU_COUNT, __VERSION__, __AUTHOR__
from .exceptions import ProcessNotRunning, ProcessNotFound
from .utils._logger import logger
import argparse
import logging
import art
from datetime import datetime
from .utils.utils import (
    get_pid_with_name, 
    is_process_running, 
    get_total_memory_chunk_num, 
    get_all_memory_addr_range,
    suspend_process,
    resume_process
)
from .functional.mem_operate import (
    dump_memory,
    dump_memory_by_address,
    concurrent_dump_memory,
    search_addr_by_bytes
)
from .utils._types import (
    Process,
    MemAddress
)
from rich.console import Console

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
        save_path: str = "MemDumped", 
        concurrent: bool = False, 
        workers: int = CPU_COUNT, 
        ignore_read_error: bool = False,
        content_fmt: Literal["hex", "bin", "ascii"] = "bin",
        encoding: str = "utf-8",
        verbose: bool = False
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
        self.verbose = verbose
        """ verbose flag """
        self.pid = self._extra_process_id(self.process_target)
        if not verbose:
            logging.disable() # disable logging if verbose is False
        logger.debug("MemoryDumper 初始化完成")

    def __print_logo(self) -> None:
        """ Prints the logo of the program """
        console = Console()
        console.print(art.text2art("PyMemDump", font="standard"), style="bold blue")
        console.print(f"Version: {__VERSION__}", style="bold cyan")
        console.print(f"Author: {__AUTHOR__}", style="bold magenta")
        console.print(f"{'=' * 100}", style="bold red")

    def _is_process_running(self) -> bool:
        """ Checks if the process is running """
        if self.pid is None:
            logger.warning("pid没有设置")
            return False
        return is_process_running(self.pid)
    
    def _stop_process(self) -> None:
        """ Stops the process """
        suspend_process(self.pid)

    def _resume_process(self) -> None:
        """ Resumes the process """
        resume_process(self.pid)
    
    def get_all_addr_range(self, to_json: bool = False) -> dict[str, str | int | list[dict[str, str]]]:
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
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "process_name": self.process_name,
            "pid": self.pid,
            "addresses": get_all_memory_addr_range(self.pid)
        }
        if to_json:
            with open(f"{self.process_name or self.pid}_all_addresses.json", "w") as f:
                json.dump(data_addrs, f, indent=4)
        logger.info(f"生成了进程为 {self.process_name or self.pid} 的全部内存地址信息。")
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
        try:
            if isinstance(desc, int):
                return desc
            elif isinstance(desc, str):
                pids = get_pid_with_name(desc)
                self.process_name = desc
                if len(pids) > 1:
                    logger.warning(f"存在多个进程名为 {desc} 的进程, 请输入其 PID 来指定目标进程.")
                    if not self.verbose:
                        logger.warning("由于 verbose 为 False，再此日志提示进程选择后续将不在显示运行时日志。")
                    logger.info(f"下列为所有进程名为 {desc} 的进程 PID: ")
                    for i, pid in enumerate(pids):
                        logger.info(f"{desc}({pid})")
                    while True:
                        usr_input = int(input("发现多个进程名，请输入指定的进程 PID: "))
                        if usr_input in pids:
                            return usr_input
                        else:
                            logger.error(f"输入的 PID {usr_input} 不是有效的进程 ID，请重新输入。")
                elif len(pids) == 1:
                    return pids[0]
                else:
                    raise ProcessNotFound(f"未找到进程名为 {desc} 的进程.")
            else:
                raise TypeError("expected int or str for process_desc, such as pid or process name.")
        except KeyboardInterrupt:
            print()  # 美观日志输出，避免日志挤在一起
            logger.critical("用户取消操作.")
            exit(0)

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
                
                # get the total memory chunk number of the process
                self.process_mem_size = get_total_memory_chunk_num(self.pid)

                dump_memory(self.pid, self.save_path, self.process_mem_size, self.ignore_read_error)
        except KeyboardInterrupt:
            logger.critical("用户停止了内存转储.")
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
            logger.critical("用户停止了内存转储.")
        finally:
            self._resume_process()

    def dump_memory_concurrent(self, workers: int = CPU_COUNT) -> None:
        """ Dumps the memory of the target process concurrently """
        try:
            self._stop_process()
            logger.info(f"并发的转储进程 {self.process_target} ，并保存到： {self.save_path}")

            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            concurrent_dump_memory(self.pid, self.save_path, self.ignore_read_error, workers=workers, content_fmt=self.data_fmt, encoding=self.encoding)
        except KeyboardInterrupt:
            logger.critical("用户停止了内存转储.")
        finally:
            self._resume_process()

    def search(self, opt: bool, pattern: list[int] | bytes | bytearray | memoryview) -> dict[str, list[str]]:
        """
        Search for a pattern in the memory of the target process.

        Args:
            pattern (list[int] | bytes | bytearray | memoryview): Pattern to search for.

        Returns:
            dict[str, list[str]]: A dictionary containing the addresses of the pattern and its corresponding values.
        """
        self._stop_process()
        try:
            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            found_addrs = search_addr_by_bytes(self.pid, pattern, self.concurrent, self.workers)
            result = {
                "pid": self.pid,
                "process_name": self.process_name,
                "pattern": [hex(i) for i in pattern],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_found": len(found_addrs),
                "matched_results": found_addrs
            }
            if opt:
                with open(f"{self.pid}_search_result.json", "w") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
            return result
        except KeyboardInterrupt:
            logger.critical("用户停止了内存地址搜索")
        finally:
            self._resume_process()

    @classmethod
    def dump_with_args(cls, language: str = "zh_CN") -> None:
        """ Dumps the memory of the process with command line arguments 
        Args:
            language (str): language to use for the tool, default is zh_CN.
        """
        cls.__print_logo(cls)
        parser = argparse.ArgumentParser(description=get_text(language, "tool_desc"))
        parser.add_argument("-scan", "--scan_addr", action="store_true", help=get_text(language, "scan_addr"))
        parser.add_argument("--concurrent", action="store_true", help=get_text(language, "concurrent"))
        parser.add_argument("-w", "--workers", type=int, help=get_text(language, "workers"), default=CPU_COUNT)
        parser.add_argument("-p", "--process", type=Process(), help=get_text(language, "process"), required=True)
        parser.add_argument("--by_addr", action="store_true", help=get_text(language, "by_addr"))
        parser.add_argument("-o", "--output", type=str, help=get_text(language, "output"), default="MemDumped")
        parser.add_argument("-i", "--ignore-read-error", action="store_true", help=get_text(language, "ignore-read-error"))
        parser.add_argument("-start", "--start-address", type=MemAddress(), help=get_text(language, "start-address"))
        parser.add_argument("-end", "--end-address", type=MemAddress(), help=get_text(language, "end-address"))
        parser.add_argument("-format", "--content-fmt", type=str, choices=["hex", "bin", "ascii"], default="bin", help=get_text(language, "content-fmt"))
        parser.add_argument("-enc", "--encoding", type=str, default="utf-8", help=get_text(language, "encoding"))
        parser.add_argument("-vb", "--verbose", action="store_true", help=get_text(language, "verbose"))
        # 为什么用 MemAddress() ? ，是因为要考虑到用户想输入16进制的数值，但是呢，MemAddress这个已经实现了转换，没有必要继续实现了
        parser.add_argument("-sch", "--search", type=MemAddress(), nargs="+", help=get_text(language, "search"))
        parser.add_argument("-sch-opt", "--search-output", action="store_true", help=get_text(language, "search_opt"))
        args = parser.parse_args()

        if args.search is not None:
            md = MemoryDumper(process_desc=args.process, save_path=args.output, verbose=args.verbose)
            result = md.search(opt=args.search_output, pattern=args.search)
            if not args.search_output:
                print(f"Search pattern: {result['pattern']}")
                print(f"Search time: {result['time']}")
                print(f"Search result: {result['matched_results']}")
            return

        if args.scan_addr:
            # 扫描不需要指定格式，导出的时候再指定
            md = MemoryDumper(process_desc=args.process, save_path=args.output, verbose=args.verbose)
            md.get_all_addr_range(to_json=True)
            return

        if args.concurrent and args.by_addr:
            raise ValueError("concurrent and by_addr cannot be set at the same time.")

        if args.concurrent:
            md = MemoryDumper(
                process_desc=args.process, 
                save_path=args.output, 
                concurrent=True, 
                workers=args.workers, 
                ignore_read_error=args.ignore_read_error, 
                content_fmt=args.content_fmt, 
                encoding=args.encoding,
                verbose=args.verbose
            )
            md.dump()
            return
        
        if not args.by_addr and (args.start_address is not None or args.end_address is not None):
            raise ValueError("start_address and end_address can only be specified when by_addr is set.")

        if args.by_addr:
            if args.start_address is None or args.end_address is None:
                raise ValueError("start_address and end_address must be specified when by_addr is set.")
            md = MemoryDumper(
                 process_desc=args.process, 
                 save_path=args.output, 
                 ignore_read_error=args.ignore_read_error, 
                 content_fmt=args.content_fmt, 
                 encoding=args.encoding,
                 verbose=args.verbose
                )
            md.dump_memory_by_address(args.start_address, args.end_address)
            return
        else:
            md = MemoryDumper(
                 process_desc=args.process, 
                 save_path=args.output, 
                 ignore_read_error=args.ignore_read_error, 
                 content_fmt=args.content_fmt, 
                 encoding=args.encoding,
                 verbose=args.verbose
                )
            md.dump()
            return

if __name__ == "__main__":
    md = MemoryDumper(process_desc="notepad.exe", save_path="C:\\Users\\user\\Desktop\\notepad_dump")
    md.dump()