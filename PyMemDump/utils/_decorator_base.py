from typing import Any, TypeVar
from functools import wraps
import warnings

T = TypeVar('T')

class BaseDecorator:
    """ Base class for decorators that can decorate both functions and classes """

    def __init__(self, message: str, category: type = UserWarning, ignore: bool = False, wait_for_look: bool = False):
        self.message = message
        self.category = category
        self.ignore = ignore
        self.wait_for_look = wait_for_look

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
            warnings.warn(self.message, self.category, stacklevel=3)
        if self.wait_for_look:
            input("Press Enter to continue or Ctrl+C to skip execution.")

    def __repr__(self) -> str:
        """ Return the representation of the decorator """
        return f"<{self.__class__.__name__}: {self.message}>"

    def __str__(self) -> str:
        """ Return the string representation of the decorator """
        return f"{self.__class__.__name__}: {self.message}"