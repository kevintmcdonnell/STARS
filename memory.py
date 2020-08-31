# TODO: check if saving/getting from data or stack (just check ranges of numbers, it's easy enough)

import random
import re
import sys
from collections import OrderedDict

from typing import List
import exceptions as ex

from constants import WORD_SIZE
from instructions import overflow_detect
from settings import settings
from typing import Union


def check_bounds(addr: int) -> None:
    # Checking for out of bounds for memory
    if int(addr) < settings['data_min'] or int(addr) > settings['data_max']:
        raise ex.MemoryOutOfBounds("0x%x is not within the data section or heap/stack." % int(addr))


class Memory:
    def __init__(self, toggle_garbage: bool = False):
        self.text = OrderedDict()  # Instructions
        self.data = OrderedDict()  # Main memory
        self.stack = OrderedDict()

        self.textPtr = settings['initial_pc']
        self.dataPtr = settings['data_min']
        self.labels = {}  # Dictionary to store the labels and their addresses

        self.toggle_garbage = toggle_garbage
        self.fileTable = OrderedDict([(0, sys.stdin),
                                      (1, sys.stdout),
                                      (2, sys.stderr)])
        self.heapPtr = 0x10040000

    def addText(self, instr) -> None:
        # Add an instruction to memory
        self.text[str(self.textPtr)] = instr
        self.textPtr += 4  # PC += 4

    def setByte(self, addr: int, data: int) -> None:
        # Addr : Address in memory (int)
        # Data = Contents of the byte (0 to 0xFF)
        check_bounds(addr)
        self.data[str(addr)] = data

    def addWord(self, data: int, addr: int) -> None:
        # Add a word (4 bytes) to memory
        if addr % 4 != 0:
            raise ex.MemoryAlignmentError(hex(addr) + " is not word aligned.")

        for i in range(4):  # Set byte by byte starting from LSB
            self.setByte(addr + i, (data >> (8 * i)) & 0xFF)

    def addHWord(self, data: int, addr: int) -> None:
        # Add a half word (2 bytes) to memory. Only looks at the least significant half-word of data.
        if addr % 2 != 0:
            raise ex.MemoryAlignmentError(hex(addr) + " is not half-word aligned.")

        for i in range(2):  # Set byte by byte starting from LSB
            self.setByte(addr + i, (data >> (8 * i)) & 0xFF)

    def addByte(self, data: int, addr: int) -> None:
        # Add a byte to memory. Only looks at the LSB of data.
        self.setByte(addr, data & 0xFF)

    def addAsciiz(self, s: str, addr: int) -> None:
        # Add a null-terminated string to memory
        self.addAscii(s, addr, null_terminate=True)

    def addLabel(self, l: str, addr: int) -> None:
        # Add a label to the dictionary of labels
        if l in self.labels:
            raise ex.InvalidLabel(l + " is already defined")

        self.labels[l] = addr

    def addAscii(self, s: str, addr: int, null_terminate: bool = False) -> None:
        # Add a string to memory
        for a in s:
            self.setByte(addr, ord(a))
            addr += 1

        if null_terminate:
            self.setByte(addr, 0)  # Store null terminator

    def getByte(self, addr: Union[str, int], signed: bool = True) -> int:
        # Get a byte of memory from main memory
        # Returns an decimal integer representation of the byte (-128 ~ 127) if signed
        # Returns (0 ~ 255) if unsigned
        check_bounds(addr)

        if str(addr) in self.data.keys():
            acc = self.data[str(addr)]

            if signed:  # Sign extend
                if acc & 0x80 > 0:
                    acc |= 0xFFFFFF00

            return overflow_detect(acc, WORD_SIZE)

        else:
            # Randomly generate a byte
            if settings['warnings']:
                print(f'Warning: Reading from uninitialized byte 0x{addr:08x}!', file=sys.stderr)

            if self.toggle_garbage:
                self.addByte(random.randint(0, 0xFF), addr)
            else:
                self.addByte(0, addr)

            return self.getByte(addr)

    def getWord(self, addr: int) -> int:
        # Get a word (4 bytes) of memory from main memory
        # Returns a decimal integer representation of the word
        if addr % 4 != 0:
            raise ex.MemoryAlignmentError(hex(addr) + " is not word aligned.")

        acc = 0  # Result

        for i in range(3, -1, -1):  # Little Endian: Go from MSB to LSB
            check_bounds(addr + i)

            # Get the ith byte of the word
            byte = self.getByte(addr + i, signed=False)
            acc = acc << 8
            acc |= byte

        return overflow_detect(acc, WORD_SIZE)

    def getHWord(self, addr: int, signed: bool = True) -> int:
        # Get a half-word (2 bytes) of memory from main memory
        # Returns a decimal integer representation of the word
        if addr % 2 != 0:
            raise ex.MemoryAlignmentError(hex(addr) + " is not half-word aligned.")

        acc = 0  # Result

        for i in range(1, -1, -1):  # Little Endian: Go from MSB to LSB
            check_bounds(addr + i)

            # Get the ith byte of the word
            byte = self.getByte(addr + i, signed=False)
            acc = acc << 8
            acc |= byte

        if signed:  # Sign extend
            if acc & 0x8000 > 0:
                acc |= 0xFFFF0000

        return overflow_detect(acc, WORD_SIZE)

    def getLabel(self, s: str) -> Union[int, None]:
        if s in self.labels:
            return self.labels[s]

        return None

    def getString(self, label: str, n: int = 100) -> Union[str, None]:
        addr = self.getLabel(label)
        if addr == None:
            return None

        count = 0
        ret = ''
        c = self.getByte(addr, signed=False)
        while c != 0 and count < n:
            if c in range(127):
                if c == 9:  # Tab
                    ret += "\\t"
                elif c == 10:  # Newline
                    ret += "\\n"
                elif c >= 32:  # Regular character
                    ret += chr(c)
                else:  # Invalid character
                    ret += '.'
            else:  # Invalid character
                ret += '.'
            count += 1
            addr += 1
            c = self.getByte(addr, signed=False)
        return ret

    def getBytes(self, label: str, n: int, signed: bool = True) -> Union[List[int], None]:
        addr = self.getLabel(label)
        if addr is None:
            return None

        ret = []
        for i in range(addr, addr + n):
            ret.append(self.getByte(i, signed=signed))
        return ret

    def dump(self) -> None:
        # Dump the contents of memory
        print(self.stack)
        print(self.data)
        print(self.text)
        print(self.labels)
