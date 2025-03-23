import psutil
import ctypes
from .structs import MEMORY_BASIC_INFORMATION
from typing import Literal
import threading
from .constants import (
    PAGE_READABLE, 
    PROCESS_QUERY_INFORMATION, 
    PROCESS_VM_READ, 
    MEM_COMMIT, 
    BLOCK_SIZE
)
from .kernalCore import kernel32
from .mem_progress import mem_progress
from .exceptions import DumpException, ProcessNotFound
from ._logger import logger
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os
from contextlib import contextmanager

@contextmanager
def open_process(pid, access):
    h_process = kernel32.OpenProcess(access, False, pid)
    if not h_process:
        raise DumpException(ctypes.WinError(ctypes.get_last_error()))
    try:
        yield h_process
    finally:
        kernel32.CloseHandle(h_process)

def get_pid_with_name(name: str) -> int:
    """ find the pid of a process with a given name """
    for proc in psutil.process_iter():
        if proc.name() == name:
            return proc.pid
    raise ProcessNotFound(f"进程 {name} 不存在")

def is_process_running(pid: int) -> bool:
    """ check if a process with a given pid is running """
    try:
        proc = psutil.Process(pid)
        return proc.is_running()
    except (psutil.NoSuchProcess , psutil.AccessDenied):
        return False
    
def get_total_memory_size(pid: int) -> int:
    """获取所有可读内存区域的总大小"""
    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        total_size = 0

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                total_size += mbi.RegionSize

            address += mbi.RegionSize

        kernel32.CloseHandle(h_process)
        return total_size

def get_all_memory_addr_range(pid: int) -> list[tuple[str, str]]:
    """获取所有可读内存区域的起始地址和结束地址"""
    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        memory_addr = []

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                memory_addr.append((address, address + mbi.RegionSize))

            address += mbi.RegionSize

        kernel32.CloseHandle(h_process)
        # 转换为16进制字符串
        memory_addr = [(hex(start), hex(end)) for start, end in memory_addr]
        return memory_addr
    
def content_by_fmt(content: bytes, content_fmt: Literal["hex", "bin", "ascii"] = "bin", encoding: str = "utf-8") -> bytes | str:
    """
    根据格式返回内容
    """
    if content_fmt == "hex":
        hex_data = " ".join(f"{b:02x}" for b in content)
        return hex_data.encode(encoding=encoding)
    elif content_fmt == "bin":
        byte_data = bytes((b + 256) % 256 for b in content)
        return byte_data
    elif content_fmt == "ascii":
        ascii_data = "".join(chr(b) if 32 <= b < 127 else "." for b in content)
        return ascii_data.encode(encoding=encoding)
    else:
        raise ValueError(f"未知格式: {content_fmt}")

def dump_memory(
    pid: int, 
    output_dir: str, 
    total_size: int, 
    ignore_read_error: bool = False, 
    content_fmt: Literal["hex", "bin", "ascii"] = "bin",
    encoding: str = "utf-8"
) -> None:
    """读取并导出内存"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:

        mbi = MEMORY_BASIC_INFORMATION()
        address = 0

        # 启动进度条
        mem_progress.start()

        # 总进度任务
        total_task = mem_progress.add_task("[bold cyan]导出内存", total=total_size, filename=f"进程: {pid}")

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                logger.debug(f"导出内存区域: {address:016x}-{address + mbi.RegionSize:016x} ({mbi.RegionSize} 字节)")
                filename = f"{address:016x}-{address + mbi.RegionSize:016x}.bin"
                output_path = os.path.join(output_dir, filename)

                with open(output_path, "wb") as f:
                    remaining_size = mbi.RegionSize
                    # 分块进度任务
                    chunk_task = mem_progress.add_task("[bold cyan]导出内存", total=mbi.RegionSize, filename=filename)

                    offset = 0

                    while remaining_size > 0:
                        chunk_size = min(remaining_size, BLOCK_SIZE)
                        buffer = (ctypes.c_byte * chunk_size)()
                        bytes_read = ctypes.c_size_t()

                        if kernel32.ReadProcessMemory(
                            h_process, ctypes.c_ulonglong(address + offset), buffer, chunk_size, ctypes.byref(bytes_read)
                        ):
                            # 将 ctypes.c_byte 数组转换为字节对象
                            data = content_by_fmt(buffer.raw[:bytes_read.value], content_fmt, encoding)
                            f.write(data)
                            
                            offset += chunk_size
                            remaining_size -= chunk_size
                            mem_progress.update(chunk_task, advance=chunk_size)  # 更新分块进度
                            mem_progress.update(total_task, advance=chunk_size)  # 更新总进度
                        else:
                            if not ignore_read_error:
                                raise DumpException(ctypes.WinError(ctypes.get_last_error()))
                            else:
                                logger.error(f"读取内存失败: {filename}")
                                break

                    mem_progress.remove_task(chunk_task)  # 移除完成的分块任务

                logger.info(f"导出成功: {filename}")

            address += mbi.RegionSize

        # 关闭进度条
        mem_progress.stop()
        kernel32.CloseHandle(h_process)

def dump_memory_by_address(
    pid: int, 
    output_dir: str,
    start_address: int, 
    end_address: int, 
    ignore_read_error: bool = False,
    content_fmt: Literal["hex", "bin", "ascii"] = "bin",
    encoding: str = "utf-8"
) -> None:
    """
    Dumps the memory of a process within a specified address range.

    This function reads the memory regions of a process within the specified start and end addresses,
    and writes their contents to separate files in the specified output directory.

    Args:
        pid (int): PID of the process.
        output_dir (str): Output directory for the memory dump files.
        start_address (int): Starting address of the memory range to dump.
        end_address (int): Ending address of the memory range to dump.
        ignore_read_error (bool): Flag to ignore read errors during memory dumping. Defaults to False.

    Returns:
        None

    Raises:
        DumpException: If an error occurs during memory dumping.
        ValueError: If start_address is greater than end_address.

    Example:
        >>> dump_memory_by_address(12345, "C:\\dumps", 0x10000000, 0x10010000)
        >>> # Dumps memory from address 0x10000000 to 0x10010000 of process 12345 to C:\\dumps

    Note:
        The specified address range must be within the process's memory address space.
        The output directory must exist and be writable.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:

        mbi = MEMORY_BASIC_INFORMATION()
        address = start_address

        # 启动进度条
        mem_progress.start()

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                if address + mbi.RegionSize > end_address:
                    mbi.RegionSize = end_address - address

                logger.debug(f"导出内存区域: {address:016x}-{address + mbi.RegionSize:016x} ({mbi.RegionSize} 字节)")
                filename = f"{address:016x}-{address + mbi.RegionSize:016x}.bin"
                output_path = os.path.join(output_dir, filename)

                with open(output_path, "wb") as f:
                    remaining_size = mbi.RegionSize
                    # 分块进度任务
                    chunk_task = mem_progress.add_task("[bold cyan]导出内存", total=mbi.RegionSize, filename=filename)

                    offset = 0

                    while remaining_size > 0:
                        chunk_size = min(remaining_size, BLOCK_SIZE)
                        buffer = (ctypes.c_byte * chunk_size)()
                        bytes_read = ctypes.c_size_t()

                        if kernel32.ReadProcessMemory(
                            h_process, ctypes.c_ulonglong(address + offset), buffer, chunk_size, ctypes.byref(bytes_read)
                        ):
                            # 将 ctypes.c_byte 数组转换为字节对象
                            data = content_by_fmt(buffer.raw[:bytes_read.value], content_fmt, encoding)
                            f.write(data)
                            offset += chunk_size
                            remaining_size -= chunk_size
                            mem_progress.update(chunk_task, advance=chunk_size)  # 更新分块进度
                        else:
                            if not ignore_read_error:
                                raise DumpException(ctypes.WinError(ctypes.get_last_error()))
                            else:
                                logger.error(f"读取内存失败: {filename}")
                                break

                    mem_progress.remove_task(chunk_task)  # 移除完成的分块任务

                logger.info(f"导出成功: {filename}")
                break

def read_memory_region(h_process, address, size):
    """读取指定内存区域"""
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    if not kernel32.ReadProcessMemory(h_process, ctypes.c_ulonglong(address), buffer, size, ctypes.byref(bytes_read)):
        raise DumpException(ctypes.WinError(ctypes.get_last_error()))
    return buffer.raw[:bytes_read.value]

def dump_memory_region(
    pid: int, 
    start_address: int, 
    end_address: int, 
    output_dir: str, 
    ignore_read_error: bool = False,
    content_fmt: Literal["hex", "bin", "ascii"] = "bin",
    encoding: str = "utf-8"
) -> None:
    """导出单个内存区域"""
    try:
        with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
            logger.info(f"导出内存区域: {start_address:016x}-{end_address:016x}")
            filename = f"{start_address:016x}-{end_address:016x}.bin"
            output_path = os.path.join(output_dir, filename)

            with threading.Lock():
                with open(output_path, "wb") as f:
                    remaining_size = end_address - start_address
                    while remaining_size > 0:
                        chunk_size = min(remaining_size, BLOCK_SIZE)
                        data = read_memory_region(h_process, start_address, chunk_size)
                        conv_data = content_by_fmt(data, content_fmt, encoding)
                        f.write(conv_data)
                        start_address += chunk_size
                        remaining_size -= chunk_size

            logger.info(f"导出成功: {filename}")
            kernel32.CloseHandle(h_process)
    except DumpException as e:
        if not ignore_read_error:
            raise
        logger.error(f"读取内存失败: {e}")

def concurrent_dump_memory(
    pid: int, 
    output_dir: str, 
    ignore_read_error: bool = False, 
    workers: int = None,
    content_fmt: Literal["hex", "bin", "ascii"] = "bin",
    encoding: str = "utf-8"
) -> None:
    """
    并发导出内存
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        regions = []

        # 获取所有可读内存区域
        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                regions.append((mbi.BaseAddress, mbi.BaseAddress + mbi.RegionSize))
            
            address += mbi.RegionSize

        if workers > len(regions):
            workers = len(regions)

        logger.info(f"开始导出内存: 进程: {pid}, 输出目录: {output_dir}, 工作进程数: {workers}, 任务总数: {len(regions)}")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for start_address, end_address in regions:
                futures.append(executor.submit(dump_memory_region, pid, start_address, end_address, output_dir, ignore_read_error, content_fmt, encoding))

            failed_tasks = 0
            for future in as_completed(futures):
                try:
                    future.result()
                except DumpException as e:
                    logger.error(f"内存导出失败: {e}")
                    failed_tasks += 1

        logger.info(f"内存导出完成，失败任务数: {failed_tasks}")

if __name__ == "__main__":
    pass