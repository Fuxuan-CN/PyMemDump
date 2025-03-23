import ctypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
""" This is the kernel32.dll library which is used to perform various operations on the system. """