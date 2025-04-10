from .utils._types import Process_Desc
import json
import sys
from rich.panel import Panel
from typing import Literal
from .i18n import get_text
from .utils.constants import CPU_COUNT, __VERSION__, __AUTHOR__
from .utils.help_beautiful import RichHelpFormatter
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
    process_operation,
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
import rich
from .exec_hook import set_exechook

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
        set_exechook()
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
            logging.disable(logging.WARN) # disable logging if verbose is False
        logger.debug("MemoryDumper 初始化完成")

    def _print_logo(self) -> None:
        """ Prints the logo of the program """
        console = rich.get_console()
        console.highlighter = None
        console.print(art.text2art("PyMemDump", font="standard"), style="bold blue")
        console.print(f"Version: {__VERSION__}", style="bold cyan")
        console.print(f"Author: {__AUTHOR__}", style="bold magenta")
        console.print(f"{'=' * console.width}", style="bold")

    def __print_search_result(self, result: dict[str, list[str]]) -> None:
        """ Prints the search result """
        console = rich.get_console()
        info_str = """
[bold yellow]进程名[/bold yellow]: {process_name}
[bold yellow]进程PID[/bold yellow]: {pid}
[bold yellow]搜索字节串[/bold yellow]: {pattern}
[bold yellow]搜索时间[/bold yellow]: {time}
[bold yellow]搜索结果总数[/bold yellow]: {total_found}
[bold yellow]匹配结果[/bold yellow]: {matched_results}
"""
        console.print(Panel(info_str.format(
            process_name=result["process_name"],
            pid=result["pid"],
            pattern=result["pattern"],
            time=result["time"],
            total_found=result["total_found"],
            matched_results=result["matched_results"]
        ), title="[bold yellow]搜索结果[/bold yellow]"), highlight=True, style="green")

    def _is_process_running(self) -> bool:
        """ Checks if the process is running """
        if self.pid is None:
            logger.warning("pid没有设置")
            return False
        return is_process_running(self.pid)
    
    def get_all_addr_range(self, to_json: bool = False) -> dict[str, str | int | list[dict[str, str]]]:
        """
        Get all memory addresses of the target process.

        Returns:
            list[tuple[int, int]]: List of memory addresses of the target process.
        """
        with process_operation(self.pid):
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
            pids = get_pid_with_name(desc)
            self.process_name = desc
            if len(pids) > 1:
                logger.warning(f"存在多个进程名为 {desc} 的进程, 请输入其 PID 来指定目标进程.")
                if not self.verbose:
                    logger.warning("""
                    由于没有启用 verbose参数，再此日志提示进程选择后续将不在显示运行时日志。 \n
                    但是致命错误消息还是会显示在控制台，请注意查看。
                    """
                )
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

    def dump(self) -> None:
        """ Dumps the memory of the process """
        with process_operation(self.pid):
            if self.concurrent:
                self.dump_memory_concurrent(workers=self.workers)
            else:
                logger.info(f"Dumping memory of process {self.process_target} to {self.save_path}.")

                if not self._is_process_running():
                    raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
                
                # get the total memory chunk number of the process
                self.process_mem_size = get_total_memory_chunk_num(self.pid)

                dump_memory(
                    self.pid, 
                    self.save_path, 
                    self.process_mem_size, 
                    self.ignore_read_error,
                    self.data_fmt,
                    self.encoding
                )

    def dump_memory_by_address(self, start_address: int, end_address: int) -> None:
        """
        Dumps the memory of the target process within a specified address range.

        Args:
            start_address (int): Starting address of the memory range to dump.
            end_address (int): Ending address of the memory range to dump.
        """
        with process_operation(self.pid):
            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            dump_memory_by_address(
                self.pid, 
                self.save_path, 
                start_address, 
                end_address, 
                self.ignore_read_error, 
                content_fmt=self.data_fmt, 
                encoding=self.encoding
            )

    def dump_memory_concurrent(self, workers: int = CPU_COUNT) -> None:
        """ Dumps the memory of the target process concurrently """
        with process_operation(self.pid):
            logger.info(f"并发的转储进程 {self.process_target} ，并保存到： {self.save_path}")

            if not self._is_process_running():
                raise ProcessNotRunning(f"Process {self.process_name or self.pid} is not running.")
            
            concurrent_dump_memory(
                self.pid, self.save_path, 
                self.ignore_read_error, 
                workers=workers, 
                content_fmt=self.data_fmt, 
                encoding=self.encoding
            )

    def search(self, opt: bool, pattern: list[int] | bytes | bytearray | memoryview) -> dict[str, list[str]]:
        """
        Search for a pattern in the memory of the target process.

        Args:
            pattern (list[int] | bytes | bytearray | memoryview): Pattern to search for.

        Returns:
            dict[str, list[str]]: A dictionary containing the addresses of the pattern and its corresponding values.
        """
        with process_operation(self.pid):
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

    @classmethod
    def dump_with_args(cls, language: str = "zh_CN") -> None:
        """Dumps the memory of the process with command line arguments
        Args:
            language (str): language to use for the tool, default is zh_CN.
        """
        # 打印程序的 logo 和版本信息
        cls._print_logo(cls)

        # 创建参数解析器
        parser = argparse.ArgumentParser(
            prog=get_text(language, "tool_name"),
            description=get_text(language, "tool_desc"),
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "-p", "--process", type=Process(), help=get_text(language, "process"), required=True
        )
        parser.add_argument(
            "-o", "--output", type=str, help=get_text(language, "output"), default="MemDumped"
        )
        parser.add_argument(
            "--concurrent", action="store_true", help=get_text(language, "concurrent")
        )
        parser.add_argument(
            "-w", "--workers", type=int, help=get_text(language, "workers"), default=CPU_COUNT
        )
        parser.add_argument(
            "--by_addr", action="store_true", help=get_text(language, "by_addr")
        )
        parser.add_argument(
            "--scan_addr", action="store_true", help=get_text(language, "scan_addr")
        )
        parser.add_argument(
            "-i", "--ignore-read-error", action="store_true", help=get_text(language, "ignore-read-error")
        )
        parser.add_argument(
            "-start", "--start-address", type=MemAddress(), help=get_text(language, "start-address")
        )
        parser.add_argument(
            "-end", "--end-address", type=MemAddress(), help=get_text(language, "end-address")
        )
        parser.add_argument(
            "-format", "--content-fmt", type=str, choices=["hex", "bin", "ascii"], default="bin", help=get_text(language, "content-fmt")
        )
        parser.add_argument(
            "-enc", "--encoding", type=str, default="utf-8", help=get_text(language, "encoding")
        )
        parser.add_argument(
            "-vb", "--verbose", action="store_true", help=get_text(language, "verbose")
        )
        parser.add_argument(
            "-sch", "--search", type=MemAddress(), nargs="+", help=get_text(language, "search")
        )
        parser.add_argument(
            "-sch-opt", "--search-output", action="store_true", help=get_text(language, "search_opt")
        )

        # 解析命令行参数
        args = parser.parse_args()

        # 检查参数之间的逻辑关系
        if args.concurrent and args.by_addr:
            parser.error("concurrent and by_addr cannot be set at the same time.")
        if args.by_addr and (args.start_address is None or args.end_address is None):
            parser.error("start_address and end_address must be specified when by_addr is set.")
        if not args.by_addr and (args.start_address is not None or args.end_address is not None):
            parser.error("start_address and end_address can only be specified when by_addr is set.")

        # 根据参数创建 MemoryDumper 实例
        md = MemoryDumper(
            process_desc=args.process,
            save_path=args.output,
            concurrent=args.concurrent,
            workers=args.workers,
            ignore_read_error=args.ignore_read_error,
            content_fmt=args.content_fmt,
            encoding=args.encoding,
            verbose=args.verbose,
        )

        # 根据参数执行相应的操作
        try:
            if args.search:
                result = md.search(opt=args.search_output, pattern=args.search)
                if not args.search_output:
                    cls.__print_search_result(cls, result)
            elif args.scan_addr:
                md.get_all_addr_range(to_json=True)
            elif args.by_addr:
                md.dump_memory_by_address(args.start_address, args.end_address)
            else:
                md.dump()
        except KeyboardInterrupt:
            logger.critical("用户停止了操作")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"发生了致命错误: {e}")
            sys.exit(1)

if __name__ == "__main__":
    md = MemoryDumper(process_desc="notepad.exe", save_path="C:\\Users\\user\\Desktop\\notepad_dump")
    md.dump()