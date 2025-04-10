from typing import Any, TypeVar
from functools import wraps
import rich
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

T = TypeVar('T')

class WarningBaseDecorator:
    """ Base class for all warning decorators that can decorate both functions and classes """

    def __init__(self, 
        message: str, 
        category: type = UserWarning, 
        ignore: bool = False, 
        wait_for_look: bool = False,
        style: str | Style | None = "bold yellow",
        title_warn_style: str | None = "bold yellow",
        panel_style: str | Style | None = "bold yellow"
    ) -> None:
        self.message = message
        self.category = category
        self.ignore = ignore
        self.wait_for_look = wait_for_look
        self.console = rich.get_console()
        self.style = style
        self.title_warn_style = title_warn_style
        self.panel_style = panel_style
        self._target = None

    def __call__(self, target: T) -> T:
        """ Decorator call """
        if callable(target):  # 如果是函数
            @wraps(target)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self._target = target
                skip = self._warn()
                if not skip:
                    return target(*args, **kwargs)
                return None
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

    def _warn(self) -> bool:
        """ Issue the warning message """
        if not self.ignore:
            title = f"[{self.title_warn_style}] {self.category.__name__} [{self.title_warn_style}]"
            name = self._target.__name__ if hasattr(self._target, "__name__") else self._target.__class__.__name__
            warn_msg = Text(f"{name} has a warning: \n {self.message}", style=self.style)
            panel = Panel(warn_msg, title=title, style=self.panel_style)
            self.console.print(panel)
            
        if self.wait_for_look:
            try:
                input("Press Enter to continue or Ctrl+C to skip execution.")
                return False
            except KeyboardInterrupt:
                print("\nSkipping execution...")
                return True
        return False

    def __repr__(self) -> str:
        """ Return the representation of the decorator """
        return f"<{self.__class__.__name__}: {self.message}>"

    def __str__(self) -> str:
        """ Return the string representation of the decorator """
        return f"{self.__class__.__name__}: {self.message}"
    
if __name__ == "__main__":

    @WarningBaseDecorator("This is a warning message", category=UserWarning, ignore=False, wait_for_look=False)
    def my_func():
        print("This is my function")

    my_func()