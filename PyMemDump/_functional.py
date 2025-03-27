""" all functionally of PyMemDump , just `in module` invoke"""
import os
import ctypes
from typing import Literal
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from .utils import (
    open_process,
    content_by_fmt, 
    bytes_num_to_unit,
    kmp_search,
    search_memory_region,
    get_total_memory_chunk_num
)
from .constants import (
    PAGE_READABLE, 
    PROCESS_QUERY_INFORMATION, 
    PROCESS_VM_READ, 
    MEM_COMMIT, 
    BLOCK_SIZE,
    CPU_COUNT
)
from .structs import (
    MEMORY_BASIC_INFORMATION
)
from .kernelCore import kernel32
from .mem_progress import mem_progress
from .exceptions import DumpException
from ._logger import logger
from .decorators import FutureFeature

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
                logger.info(f"导出内存区域: {address:016x}-{address + mbi.RegionSize:016x} (大小: {bytes_num_to_unit(mbi.RegionSize)})")
                filename = f"{pid}_{address:016x}-{address + mbi.RegionSize:016x}.bin"
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
                            data = content_by_fmt(ctypes.string_at(ctypes.addressof(buffer), bytes_read.value), content_fmt, encoding)
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
    if start_address > end_address:
        raise ValueError("Start address must be less than or equal to end address.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = start_address

        # 验证地址范围是否在进程内存地址空间内
        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                if address + mbi.RegionSize > end_address:
                    mbi.RegionSize = end_address - address

                if address >= start_address and address + mbi.RegionSize <= end_address:
                    logger.info(f"导出内存区域: {address:016x}-{address + mbi.RegionSize:016x} (大小: {bytes_num_to_unit(mbi.RegionSize)})")
                    filename = f"{pid}_{address:016x}-{address + mbi.RegionSize:016x}.bin"
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
                                data = content_by_fmt(ctypes.string_at(ctypes.addressof(buffer), bytes_read.value), content_fmt, encoding)
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
                else:
                    logger.warning(f"内存区域 {address:016x}-{address + mbi.RegionSize:016x} 不在指定范围内，跳过。")
            else:
                logger.warning(f"内存区域 {address:016x}-{address + mbi.RegionSize:016x} 不可读，跳过。")
                
            address += mbi.RegionSize

        # 关闭进度条
        mem_progress.stop()

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
            filename = f"{pid}_{start_address:016x}-{end_address:016x}.bin"
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

@FutureFeature("v0.2.0", available_now=True, ignore=True)
def search_addr_by_bytes(pid: int, pattern: list[int] | bytes | bytearray | memoryview, concurrent: bool = False, workers: int = None) -> list[str]:
    """
    搜索指定字节序列的内存地址
    """
    if concurrent:
        return search_addr_by_bytes_concurrent(pid, pattern, workers)
    
    mem_progress.start()
    # 添加搜索任务
    total_memory_size = get_total_memory_chunk_num(pid) 
    total_task = mem_progress.add_task("[bold yellow]搜索内存", total=total_memory_size, filename=f"进程: {pid}")

    logger.info(f"搜索内存: 进程: {pid}, 字节序列: {pattern}")

    if isinstance(pattern, list):
        pattern = bytes(pattern)
    elif isinstance(pattern, (bytearray, memoryview)):
        pattern = bytes(pattern)

    found_addresses = []

    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT:
                region_size = mbi.RegionSize
                buffer = ctypes.create_string_buffer(region_size)
                bytes_read = ctypes.c_size_t()

                if kernel32.ReadProcessMemory(h_process, ctypes.c_ulonglong(mbi.BaseAddress), buffer, region_size, ctypes.byref(bytes_read)):
                    region_data = ctypes.string_at(ctypes.addressof(buffer), bytes_read.value)
                    positions = kmp_search(region_data, pattern)
                    for pos in positions:
                        found_addresses.append(hex(mbi.BaseAddress + pos))
                        logger.debug(f"找到内存地址: {hex(mbi.BaseAddress + pos)}")
                else:
                    logger.warning(f"读取内存失败: {hex(mbi.BaseAddress)}-{hex(mbi.BaseAddress + mbi.RegionSize)}")

                # 更新进度条
                mem_progress.update(total_task, advance=region_size)

            address += mbi.RegionSize

        mem_progress.stop()  # 关闭进度条

    return found_addresses

def search_addr_by_bytes_concurrent(pid: int, pattern: list[int] | bytes | bytearray | memoryview, workers: int = CPU_COUNT) -> list[str]:
    """
    并发的搜索指定字节序列的内存地址
    """
    mem_progress.start()
    total_memory_size = get_total_memory_chunk_num(pid)
    total_task = mem_progress.add_task("[bold yellow]搜索内存", total=total_memory_size, filename=f"进程: {pid}")

    logger.info(f"并发搜索内存: 进程: {pid}, 字节序列: {pattern}")

    if isinstance(pattern, list):
        pattern = bytes(pattern)
    elif isinstance(pattern, (bytearray, memoryview)):
        pattern = bytes(pattern)

    found_addresses = []

    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        regions = []

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT:
                regions.append((mbi.BaseAddress, mbi.RegionSize))
            address += mbi.RegionSize

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(search_memory_region, h_process, base, size, pattern, mem_progress, total_task) for base, size in regions]
            for future in as_completed(futures):
                found_addresses.extend(future.result())

    mem_progress.stop()
    return [hex(addr) for addr in found_addresses]
