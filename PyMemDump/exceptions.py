""" all exceptions will be defined here """

class DumpException(Exception):
    """ Base class for all exceptions raised by MemDump """
    pass

class ProcessNotRunning(DumpException):
    """ Raised when trying to dump a process that is not running """
    pass

class ProcessNotFound(DumpException):
    """ Raised when trying to dump a process that cannot be found """
    pass