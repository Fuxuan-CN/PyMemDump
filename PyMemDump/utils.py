import psutil
import ctypes
from .structs import (
    MEMORY_BASIC_INFORMATION,
    THREADENTRY32
)
from .constants import (
    PAGE_READABLE,
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_READ,
    MEM_COMMIT,
    PAGE_EXECUTE,
    PAGE_WRITEABLE
)
from typing import Literal
from rich.progress import Progress
from rich.progress import TaskID
from .kernelCore import kernel32
from .exceptions import DumpException
from ._logger import logger
from .decorators import FutureFeature
from contextlib import contextmanager

@FutureFeature("v0.2.5")
def get_pid_by_window_title(title: str) -> int:
    """
    根据窗口标题获取进程ID
    """
    pass

def build_partial_match_table(pattern: bytes) -> list[int]:
    """
    构建KMP算法的部分匹配表
    """
    table = [0] * len(pattern)
    j = 0  # 表示前缀的长度
    for i in range(1, len(pattern)):
        while j > 0 and pattern[i] != pattern[j]:
            j = table[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        table[i] = j
    return table

def kmp_search(data: bytes, pattern: bytes) -> list[int]:
    """
    使用KMP算法在数据中搜索模式串
    """
    if not pattern:
        return []

    table = build_partial_match_table(pattern)
    positions = []
    j = 0  # 表示模式串的当前匹配位置

    for i in range(len(data)):
        while j > 0 and data[i] != pattern[j]:
            j = table[j - 1]
        if data[i] == pattern[j]:
            j += 1
        if j == len(pattern):
            positions.append(i - j + 1)
            j = table[j - 1]

    return positions

def bytes_num_to_unit(num: int) -> str:
    """将字节数转换为可读的单位"""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_idx = 0
    while num >= 1024 and unit_idx < len(units) - 1:
        num /= 1024
        unit_idx += 1
    return f"{num:.2f} {units[unit_idx]}"

def get_permissions(protect: int) -> str:
    """Convert protection flags to readable permissions"""
    permissions = []
    if protect in PAGE_READABLE:
        permissions.append("readable")
    if protect in PAGE_WRITEABLE:
        permissions.append("writeable")
    if protect == PAGE_EXECUTE:
        permissions.append("executable")
    return ", ".join(permissions) if permissions else "none"

def suspend_process(pid: int):
    """ 暂停目标进程中的所有线程 """
    logger.info(f"暂停进程 {pid} 中的所有线程")
    h_snapshot = kernel32.CreateToolhelp32Snapshot(0x00000004, pid)
    if h_snapshot == -1:
        raise DumpException(ctypes.WinError(ctypes.get_last_error()))

    try:
        te32 = THREADENTRY32()
        te32.dwSize = ctypes.sizeof(THREADENTRY32)  # 确保 dwSize 被正确设置
        if not kernel32.Thread32First(h_snapshot, ctypes.byref(te32)):
            raise DumpException(ctypes.WinError(ctypes.get_last_error()))

        while True:
            if te32.th32OwnerProcessID == pid:
                h_thread = kernel32.OpenThread(0x0002, False, te32.th32ThreadID)  # THREAD_SUSPEND_RESUME
                if h_thread:
                    kernel32.SuspendThread(h_thread)
                    kernel32.CloseHandle(h_thread)
            if not kernel32.Thread32Next(h_snapshot, ctypes.byref(te32)):
                break
    finally:
        kernel32.CloseHandle(h_snapshot)

def resume_process(pid: int):
    """ 恢复目标进程中的所有线程 """
    logger.info(f"恢复进程 {pid} 中的所有线程")
    h_snapshot = kernel32.CreateToolhelp32Snapshot(0x00000004, pid)  # TH32CS_SNAPTHREAD
    if h_snapshot == -1:
        raise DumpException(ctypes.WinError(ctypes.get_last_error()))

    try:
        te32 = THREADENTRY32()
        te32.dwSize = ctypes.sizeof(THREADENTRY32)  # 确保 dwSize 被正确设置
        if not kernel32.Thread32First(h_snapshot, ctypes.byref(te32)):
            raise DumpException(ctypes.WinError(ctypes.get_last_error()))

        while True:
            if te32.th32OwnerProcessID == pid:
                h_thread = kernel32.OpenThread(0x0002, False, te32.th32ThreadID)  # THREAD_SUSPEND_RESUME
                if h_thread:
                    kernel32.ResumeThread(h_thread)
                    kernel32.CloseHandle(h_thread)
            if not kernel32.Thread32Next(h_snapshot, ctypes.byref(te32)):
                break
    finally:
        kernel32.CloseHandle(h_snapshot)

@contextmanager
def open_process(pid, access):
    h_process = kernel32.OpenProcess(access, False, pid)
    if not h_process:
        raise DumpException(ctypes.WinError(ctypes.get_last_error()))
    try:
        yield h_process
    finally:
        kernel32.CloseHandle(h_process)

def get_pid_with_name(name: str) -> list[int]:
    """ find the pid of a process with a given name """
    result = []
    for proc in psutil.process_iter():
        if proc.name() == name:
            result.append(proc.pid)
    return result

def is_process_running(pid: int) -> bool:
    """ check if a process with a given pid is running """
    try:
        proc = psutil.Process(pid)
        return proc.is_running()
    except (psutil.NoSuchProcess , psutil.AccessDenied):
        return False
    
def get_total_memory_chunk_num(pid: int) -> int:
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

        return total_size

def get_all_memory_addr_range(pid: int) -> list[dict[str, str]]:
    """获取所有可读内存区域的起始地址和结束地址"""
    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        memory_addr = []

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT: # 确保只扫描已提交的内存区域
                mem_permissions = get_permissions(mbi.Protect)
                memory_addr.append(
                    {
                        "start": hex(mbi.BaseAddress),
                        "end": hex(mbi.BaseAddress + mbi.RegionSize),
                        "size": bytes_num_to_unit(mbi.RegionSize),
                        "permissions": mem_permissions
                    }
                )

            address += mbi.RegionSize
            
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
    
def search_memory_region(h_process: int, base_address: int, region_size: int, pattern: bytes, progress: Progress, task: TaskID) -> list[int]:
    """搜索单个内存区域"""
    buffer = ctypes.create_string_buffer(region_size)
    bytes_read = ctypes.c_size_t()
    if kernel32.ReadProcessMemory(h_process, ctypes.c_ulonglong(base_address), buffer, region_size, ctypes.byref(bytes_read)):
        region_data = ctypes.string_at(ctypes.addressof(buffer), bytes_read.value)
        positions = kmp_search(region_data, pattern)
        progress.update(task, advance=region_size)
        return [(base_address + pos) for pos in positions]
    else:
        progress.update(task, advance=region_size)
        return []

if __name__ == "__main__":
    pass