""" my module decorators """
from functools import wraps
from typing import Callable, Any
import warnings

class FutureFeature:
    """ Decorator for future implementation """

    def __init__(self, version_implemented: str, ignore: bool = False) -> None:
        self.version_implemented = version_implemented
        """ the version of the function that is implemented """
        self.ignore = ignore
        """ ignore the warning message """

    def __call__(self, func: Callable) -> Callable:
        """ decorator call """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn_msg = f"""
{func.__name__} is a future feature and is not implemented yet.
It will be implemented in version {self.version_implemented}.
excepted functionality: {func.__doc__}
"""
            if not self.ignore:
                warnings.warn(warn_msg, FutureWarning)
            return func(*args, **kwargs)
        return wrapper

    def __repr__(self) -> str:
        """ return the representation of the decorator """
        return f"<Future: {self.version_implemented}>"

    def __str__(self) -> str:
        """ return the string representation of the decorator """
        return f"Future: {self.version_implemented}"

# 示例用法
if __name__ == "__main__":
    @FutureFeature(version_implemented="0.1.0")
    def test_future() -> None:
        """ test future function """
        print("test future function")

    test_future()