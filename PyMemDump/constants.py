""" all constants of PyMemDump """

import os
# 常量定义
PROCESS_QUERY_INFORMATION = 0x0400
""" 进程权限：查询信息 """
PROCESS_VM_READ = 0x0010
""" 进程权限：读取内存 """
MEM_COMMIT = 0x00001000
""" 内存权限：提交 """
PAGE_READABLE = (0x02, 0x04, 0x08, 0x20, 0x40)  # 可读的内存保护标志
""" 内存权限：可读 """
PAGE_WRITEABLE = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80)  # 可写的内存保护标志
""" 内存权限：可写 """
PAGE_EXECUTE = 0x00000010  # 可执行的内存保护标志
""" 内存权限：可执行 """
BLOCK_SIZE = 1024 * 1024  # 每次读取 1 MB
""" 内存块大小 """

CPU_COUNT = os.cpu_count()  # CPU 数量
""" CPU 数量 """