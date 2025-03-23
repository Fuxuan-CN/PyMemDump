
# PyMemDump - Python 内存转储工具

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Fuxuan-CN/PyMemDump/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Fuxuan-CN/PyMemDump.svg?style=social)](https://github.com/Fuxuan-CN/PyMemDump/stargazers)

PyMemDump 是一个用于转储系统进程内存的工具。它支持按进程名或PID指定目标进程，并将内存内容导出到指定的文件中。该工具还支持并发导出、指定地址范围导出、多种内容格式化选项等功能。

## 功能特点

- **多语言支持**：支持英文（`en_US`）和中文（`zh_CN`）。
- **灵活的目标进程指定**：可以通过进程名或PID指定目标进程。
- **并发导出**：支持多线程并发导出，提高导出效率。
- **指定地址范围导出**：可以指定内存地址范围进行导出。
- **多种内容格式**：支持`hex`、`bin`、`ascii`等多种内容格式。
- **详细的日志记录**：提供详细的日志信息，方便调试和问题追踪。

## 安装

### 通过`pip`安装

```bash
pip install PyMemDump
```

### 从源代码安装

1. 克隆仓库：

   ```bash
   git clone https://github.com/yourusername/PyMemDump.git
   ```

2. 进入目录并安装依赖：

   ```bash
   cd PyMemDump
   pip install -r requirements.txt
   ```

## 使用方法

### 命令行接口

PyMemDump 提供了命令行接口，用户可以通过命令行参数灵活配置导出选项。以下是一些常用的命令行参数：

```bash
python -m PyMemDump --help
```

#### 示例

- **全内存导出**：

  ```bash
  python -m PyMemDump --process notepad.exe --output ./dumps
  ```

- **并发导出**：

  ```bash
  python -m PyMemDump --process notepad.exe --output ./dumps --concurrent --workers 4
  ```

- **指定地址范围导出**：

  ```bash
  python -m PyMemDump --process notepad.exe --output ./dumps --by_addr --start-address 0x10000000 --end-address 0x10010000
  ```

- **扫描内存地址并保存到JSON文件**：

  ```bash
  python -m PyMemDump --process notepad.exe --scan_addr
  ```

### Python接口

你也可以通过Python代码直接使用PyMemDump的功能：

```python
from PyMemDump import MemoryDumper

dumper = MemoryDumper(process_desc="notepad.exe", save_path="./dumps")
dumper.dump()
```

## 国际化支持

- PyMemDump支持多语言，你可以如下操作切换语言：

```python
from PyMemDump import MemoryDumper

MemoryDumper.dump_with_args(language="zh_CN")
```

目前支持的语言有：

- 英文（`en_US`）
- 中文（`zh_CN`）
- 法语 (`fr_FR`)

- **想帮忙添加语言?**

查看下列文档来帮助你如何添加新语言；

- [i18n贡献文档](docs/I18NCONTROBUILTING.MD)

## 日志记录

PyMemDump 提供了详细的日志记录功能，帮助用户跟踪内存导出过程中的问题。日志信息会显示在控制台，并且可以通过配置文件保存到文件中。

## 注意事项

- 确保目标进程正在运行，否则会报错。
- 确保输出目录存在且可写。
- 在某些操作系统或环境中，可能需要管理员权限才能访问某些进程的内存。

## 贡献

欢迎贡献代码或报告问题！你可以通过以下方式参与：

- 提交Pull Request
- 提交Issue
- 编写lang.json文件翻译

## 许可证

PyMemDump 采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- GitHub: [Fuxuan-CN](https://github.com/Fuxuan-CN)
- Email: `fuxuan001@foxmail.com`
- QQ: 3072252442
- WeChat: Ricky-zhang1018
