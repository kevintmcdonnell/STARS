"""
https://github.com/sbustars/STARS

Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

class MessageException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"{self.message}\n"

class InvalidImmediate(MessageException):
    pass
class MemoryOutOfBounds(MessageException):
    pass
class MemoryAlignmentError(MessageException):
    pass
class InvalidCharacter(MessageException):
    pass
class InvalidLabel(MessageException):
    pass
class InvalidSyscall(MessageException):
    pass
class InvalidRegister(MessageException):
    pass
class WritingToZeroRegister(MessageException):
    pass
class ArithmeticOverflow(MessageException):
    pass
class DivisionByZero(MessageException):
    pass
class InvalidInput(MessageException):
    pass
class InstrCountExceed(MessageException):
    pass
class BreakpointException(MessageException):
    pass
class FileAlreadyIncluded(MessageException):
    pass
class InvalidEQV(MessageException):
    pass
class InvalidArgument(MessageException):
    pass
class NoMainLabel(MessageException):
    pass