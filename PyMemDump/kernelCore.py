""" any system-core library or API calls should be imported here """
import ctypes
import sys

if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
elif sys.platform == "linux":
    kernel32 = ctypes.CDLL("libc.so.6")
elif sys.platform == "darwin":
    kernel32 = ctypes.CDLL("libSystem.dylib")
else:
    raise OSError("Unsupported platform")