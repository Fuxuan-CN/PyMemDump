""" the abstract interface for all extensions """
from abc import ABC, abstractmethod
from ..core import MemoryDumper
from ..utils.decorators import FutureFeature

@FutureFeature("v0.2.5", is_a_idea=True)
class BaseExtension(ABC):
    """ base interface for all extensions """

    @abstractmethod
    def __init__(self, dumper: MemoryDumper) -> None:
        """ initialize the extension with the dumper """
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs) -> None:
        """ execute the extension """
        pass