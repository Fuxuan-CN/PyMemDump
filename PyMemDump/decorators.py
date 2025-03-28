""" my module decorators """
from typing import Callable, Any
from functools import wraps
import warnings

class Issue:
    """ Decorator for function issues """

    def __init__(self, issue_desc: str, github_issue_link: str = None, ignore: bool = False, plan_to_fix_version: str = None, wait_for_look: bool = False) -> None:
        self.issue_desc = issue_desc
        """ the description of the issue """
        self.ignore = ignore
        """ ignore the warning message """
        self.plan_to_fix_version = plan_to_fix_version
        """ the version to fix the issue """
        self.wait_for_look = wait_for_look
        """ wait the user to look at the warning message """
        self.github_issue_link = github_issue_link
        """ the link to the github issue """

    def __call__(self, func: Callable) -> Callable:
        """ decorator call """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn_msg = f"""
{func.__name__} has an issue: {self.issue_desc}
"""
            if self.plan_to_fix_version:
                warn_msg += f"Plan to fix in version {self.plan_to_fix_version}.\n"
            if self.github_issue_link:
                warn_msg += f"For more information, see {self.github_issue_link}.\n"
            if not self.ignore:
                warnings.warn(warn_msg, UserWarning)
            if self.wait_for_look:
                input("Press Enter to continue or Ctrl+C to skip execution.")
            return func(*args, **kwargs)
        return wrapper

    def __repr__(self) -> str:
        """ return the representation of the decorator """
        return f"<Issue: {self.issue_desc}, plan_to_fix_version={self.plan_to_fix_version}>"

    def __str__(self) -> str:
        """ return the string representation of the decorator """
        return f"Issue: {self.issue_desc}, plan_to_fix_version={self.plan_to_fix_version}"

class FutureFeature:
    """ Decorator for future implementation """

    def __init__(self, version_implemented: str, available_now: bool = False, is_a_idea: bool = False, ignore: bool = False) -> None:
        self.version_implemented = version_implemented
        """ the version of the function that is implemented """
        self.available_now = available_now
        """ whether the function is partially available now """
        self.is_a_idea = is_a_idea
        """ whether the function is just an idea """
        self.ignore = ignore
        """ ignore the warning message """

    def __call__(self, func: Callable) -> Callable:
        """ decorator call """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn_msg = f"""
{func.__name__} is a future feature and is not fully implemented yet.
It will be implemented in version {self.version_implemented}.
Expected functionality: {func.__doc__}
"""
            if not self.available_now:
                warn_msg += "This function is not available yet.\n"
            if self.is_a_idea:
                warn_msg += "This function is just an idea and may not be implemented as described.\n"
            if not self.ignore:
                warnings.warn(warn_msg, FutureWarning)
            return func(*args, **kwargs)
        return wrapper

    def __repr__(self) -> str:
        """ return the representation of the decorator """
        return f"<Future: {self.version_implemented}, available_now={self.available_now}, is_a_idea={self.is_a_idea}>"

    def __str__(self) -> str:
        """ return the string representation of the decorator """
        return f"Future: {self.version_implemented}, available_now={self.available_now}, is_a_idea={self.is_a_idea}"

# 示例用法
if __name__ == "__main__":
    @FutureFeature(version_implemented="0.1.0")
    def test_future() -> None:
        """ test future function """
        print("test future function")

    test_future()