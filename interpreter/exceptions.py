class InvalidImmediate(Exception):
    def __init__(self, message: str):
        self.message = message


class MemoryOutOfBounds(Exception):
    def __init__(self, message: str):
        self.message = message


class MemoryAlignmentError(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidCharacter(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidLabel(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidSyscall(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidRegister(Exception):
    def __init__(self, message: str):
        self.message = message


class WritingToZeroRegister(Exception):
    def __init__(self, message: str):
        self.message = message


class ArithmeticOverflow(Exception):
    def __init__(self, message: str):
        self.message = message


class DivisionByZero(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidInput(Exception):
    def __init__(self, message: str):
        self.message = message


class InstrCountExceed(Exception):
    def __init__(self, message: str):
        self.message = message


class BreakpointException(Exception):
    def __init__(self, message: str):
        self.message = message


class FileAlreadyIncluded(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidEQV(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidArgument(Exception):
    def __init__(self, message: str):
        self.message = message


class NoMainLabel(Exception):
    def __init__(self, message: str):
        self.message = message