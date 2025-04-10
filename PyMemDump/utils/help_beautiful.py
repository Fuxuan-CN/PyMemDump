""" make argparse help message beautiful """
import argparse
import rich
from rich.text import Text
from rich.panel import Panel
from rich.style import Style

class RichHelpFormatter(argparse.HelpFormatter):
    """
    使用 Rich 美化 argparse 的帮助信息。
    """
    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)
        self.console = rich.get_console()
        # 判断是否支持ANSI
        self.is_support_ansi = self.console.is_terminal and self.console.is_interactive
        if not self.is_support_ansi:
            self.console.no_color = True
            self.console.highlighter = None
            self.console.legacy_windows = True

    def _format_usage(self, usage, actions, groups, prefix):
        """
        美化使用方法部分。
        """
        usage_text = super()._format_usage(usage, actions, groups, prefix)
        return f"[bold green]{usage_text}[/bold green]"

    def _format_action(self, action):
        """
        美化动作（参数）部分。
        """
        help_text = super()._format_action(action)
        lines = help_text.split("\n")
        formatted_lines = []
        for line in lines:
            if line.startswith("  --"):
                # 美化参数名称
                parts = line.split(" ", 1)
                option = parts[0]
                description = parts[1] if len(parts) > 1 else ""
                formatted_lines.append(f"[bold cyan]{option}[/bold cyan] {description}")
            else:
                formatted_lines.append(line)
        return "\n".join(formatted_lines)

    def _format_text(self, text):
        """
        美化普通文本部分。
        """
        return f"[bold magenta]{text}[/bold magenta]"
    
    def __caught_panel(self, panel: Panel) -> str:
        """
        将 Rich Panel 输出到控制台并返回其内容。
        """
        with self.console.capture() as capture:
            self.console.print(panel)
        return capture.get()

    def format_help(self):
        """
        将美化后的帮助信息包装为 Rich 的 Panel。
        """
        help_text = super().format_help()
        title = f"[bold red]{self._prog if self._prog else 'Usage'}[/bold red]"
        panel = Panel(Text.from_markup(help_text), title=title, style=Style(color="blue"))
        return self.__caught_panel(panel)