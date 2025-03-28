from ..utils.decorators import FutureFeature
from ..utils.mem_progress import mem_progress
from ..utils._logger import logger
from ..utils.utils import (
    get_total_memory_chunk_num,
    search_memory_region,
    kmp_search,
    open_process
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from ..structs import MEMORY_BASIC_INFORMATION
from ..kernelCore import kernel32
from ..utils.constants import (
    CPU_COUNT,
    MEM_COMMIT,
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_READ,
)

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
