""" any system-core library or API calls should be imported here """
import ctypes
import sys

if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

if sys.platform == "linux":
    LinuxKernelCore = ctypes.CDLL("libc.so.6")

if sys.platform == "darwin":
    MacOsKernelCore = ctypes.CDLL("libSystem.B.dylib")