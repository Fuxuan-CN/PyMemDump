from ._decorator_base import BaseDecorator

class Issue(BaseDecorator):
    """ Decorator for function or class issues """

    def __init__(self, issue_desc: str, github_issue_link: str = None, ignore: bool = False, plan_to_fix_version: str = None, wait_for_look: bool = False):
        message = f"{issue_desc}\n"
        if plan_to_fix_version:
            message += f"Plan to fix in version {plan_to_fix_version}.\n"
        if github_issue_link:
            message += f"For more information, see {github_issue_link}.\n"
        super().__init__(message, UserWarning, ignore, wait_for_look)

class FutureFeature(BaseDecorator):
    """ Decorator for future implementation of functions or classes """

    def __init__(self, version_implemented: str, available_now: bool = False, is_a_idea: bool = False, ignore: bool = False, wait_for_look: bool = False):
        message = f"This feature is not fully implemented yet and will be available in version {version_implemented}.\n"
        if not available_now:
            message += "This function or class is not available yet.\n"
        if is_a_idea:
            message += "This function or class is just an idea and may not be implemented as described.\n"
        super().__init__(message, FutureWarning, ignore, wait_for_look)

# 示例用法
if __name__ == "__main__":
    @FutureFeature(version_implemented="0.1.0")
    def test_future_function() -> None:
        """ test future function """
        pass

    @FutureFeature(version_implemented="0.1.0")
    class TestFutureClass:
        """ test future class """
        def __init__(self):
            pass

    test_future_function()
    TestFutureClass()