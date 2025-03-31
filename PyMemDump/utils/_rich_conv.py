""" This module provides rich text conversion functions. """
from rich.console import RenderableType

def to_printable(rich_content: RenderableType) -> str:
    """ Convert rich content to a printable string. """
    return str(rich_content)