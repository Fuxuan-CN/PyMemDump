from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.traceback import install

# 启用 rich 的 traceback
install()

# 定义进度条
mem_progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.0f}%",
    "•",
    TimeElapsedColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    console=None,
)