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
