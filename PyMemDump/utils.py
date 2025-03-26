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
from .kernelCore import kernel32
from .exceptions import DumpException, ProcessNotFound
from ._logger import logger
from contextlib import contextmanager

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

def get_all_memory_addr_range(pid: int) -> list[dict[str, str]]:
    """获取所有可读内存区域的起始地址和结束地址"""
    with open_process(pid, PROCESS_QUERY_INFORMATION | PROCESS_VM_READ) as h_process:
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        memory_addr = []

        while True:
            if not kernel32.VirtualQueryEx(h_process, ctypes.c_ulonglong(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                break

            if mbi.State == MEM_COMMIT and mbi.Protect in PAGE_READABLE:
                mem_permissions = get_permissions(mbi.Protect)
                memory_addr.append(
                    {
                        "start": hex(mbi.BaseAddress),
                        "end": hex(mbi.BaseAddress + mbi.RegionSize),
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

if __name__ == "__main__":
    pass