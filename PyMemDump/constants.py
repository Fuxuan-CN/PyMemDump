import os
# 常量定义
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x00001000
PAGE_READABLE = (0x02, 0x04, 0x08, 0x20, 0x40)  # 可读的内存保护标志
BLOCK_SIZE = 1024 * 1024  # 每次读取 1 MB

CPU_COUNT = os.cpu_count()  # CPU 数量
""" CPU 数量 """