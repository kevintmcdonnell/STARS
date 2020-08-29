class InvalidImmediateException(Exception):
    def __init__(self, message: str):
        self.message = message


class MemoryOutOfBoundsException(Exception):
    def __init__(self, message: str):
        self.message = message


class MemoryAlignmentException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidCharacterException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidLabelException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidSyscallException(Exception):
    def __init__(self, message: str):
        self.message = message


class WritingToZeroRegisterException(Exception):
    def __init__(self, message: str):
        self.message = message


class ArithmeticOverflowException(Exception):
    def __init__(self, message: str):
        self.message = message


class DivisionByZeroException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidInputException(Exception):
    def __init__(self, message: str):
        self.message = message


class InstrCountExceedException(Exception):
    def __init__(self, message: str):
        self.message = message


class BreakpointException(Exception):
    def __init__(self, message: str):
        self.message = message


class HoustonWeHaveAProblemException(Exception):
    def __init__(self, message: str):
        self.message = message


class FileAlreadyIncludedException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidEQVException(Exception):
    def __init__(self, message: str):
        self.message = message


class InvalidArgumentException(Exception):
    def __init__(self, message: str):
        self.message = message


class NoMainLabelException(Exception):
    def __init__(self, message: str):
        self.message = message