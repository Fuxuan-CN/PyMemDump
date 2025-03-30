from typing import Any, TypeVar
from functools import wraps
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

T = TypeVar('T')

class WarningBaseDecorator:
    """ Base class for all warning decorators that can decorate both functions and classes """

    def __init__(self, message: str, category: type = UserWarning, ignore: bool = False, wait_for_look: bool = False):
        self.message = message
        self.category = category
        self.ignore = ignore
        self.wait_for_look = wait_for_look
        self.console = Console()

    def __call__(self, target: T) -> T:
        """ Decorator call """
        if callable(target):  # 如果是函数
            @wraps(target)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self._warn()
                return target(*args, **kwargs)
            return wrapper
        elif isinstance(target, type):  # 如果是类
            original_init = target.__init__

            @wraps(original_init)
            def new_init(self, *args: Any, **kwargs: Any) -> None:
                self._warn()
                original_init(self, *args, **kwargs)

            target.__init__ = new_init
            return target
        else:
            raise TypeError("Unsupported target type for decorator")

    def _warn(self) -> None:
        """ Issue the warning message """
        if not self.ignore:
            title = f"{self.category.__name__}"
            warn_msg = Text(self.message, style="bold red")
            panel = Panel(warn_msg, title=title, style=Style(bgcolor="yellow", color="black"))
            self.console.print(panel)
            
        if self.wait_for_look:
            input("Press Enter to continue or Ctrl+C to skip execution.")

    def __repr__(self) -> str:
        """ Return the representation of the decorator """
        return f"<{self.__class__.__name__}: {self.message}>"

    def __str__(self) -> str:
        """ Return the string representation of the decorator """
        return f"{self.__class__.__name__}: {self.message}"