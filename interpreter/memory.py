import random
import struct
import sys
from collections import OrderedDict
from typing import List, Union

from numpy import float32

from constants import WORD_MASK
from interpreter import exceptions as ex
from interpreter import utility
from interpreter.instructions import overflow_detect
from settings import settings


# Check for out of bounds
def check_bounds(addr: int) -> None:
    if addr < settings['data_min'] or addr > settings['data_max']:
        raise ex.MemoryOutOfBounds(f"{utility.format_hex(addr)} is not within the data section or heap/stack.")


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

    # Add an instruction to memory
    def addText(self, instr) -> None:
        self.text[str(self.textPtr)] = instr
        self.textPtr += 4  # PC += 4

    def setByte(self, addr: int, data: int, admin=True) -> None:
        # Addr : Address in memory (int)
        # Data = Contents of the byte (0 to 0xFF)
        if not admin:
            check_bounds(addr)
        self.data[str(addr)] = data

    # Add a word (4 bytes) to memory
    def addWord(self, data: int, addr: int) -> None:
        if addr % 4 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not word aligned.")

        for i in range(4):  # Set byte by byte starting from LSB
            self.setByte(addr + i, (data >> (8 * i)) & 0xFF)

    # Add a half word (2 bytes) to memory. Only looks at the least significant half-word of data.
    def addHWord(self, data: int, addr: int) -> None:
        if addr % 2 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not half-word aligned.")

        for i in range(2):  # Set byte by byte starting from LSB
            self.setByte(addr + i, (data >> (8 * i)) & 0xFF)

    def addByte(self, data: int, addr: int, admin=True) -> None:
        # Add a byte to memory. Only looks at the LSB of data.
        self.setByte(addr, data & 0xFF, admin=True)

    # Add a single precision floating point to memory
    def addFloat(self, data: float32, addr: int) -> None:
        data_int = int.from_bytes(struct.pack('>f', data), 'big', signed=True)
        self.addWord(data_int, addr)

    # Add a double precision floating point to memory
    def addDouble(self, data: float, addr: int) -> None:
        if addr % 8 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not double-word aligned.")

        data_int = int.from_bytes(struct.pack('>d', data), 'big', signed=True)

        self.addWord(data_int & WORD_MASK, addr)  # Lower 32 bits
        self.addWord(data_int >> 32, addr + 4)  # Upper 32 bits

    # Add a string to memory
    def addAscii(self, s: str, addr: int, null_terminate: bool = False) -> None:
        for c in s:
            self.setByte(addr, ord(c))
            addr += 1

        if null_terminate:
            self.setByte(addr, 0)  # Store null terminator

    # Add a null-terminated string to memory
    def addAsciiz(self, s: str, addr: int) -> None:
        self.addAscii(s, addr, null_terminate=True)

    # Add a label to the dictionary of labels
    def addLabel(self, l: str, addr: int) -> None:
        if l in self.labels:
            raise ex.InvalidLabel(l + " is already defined")

        self.labels[l] = addr

    def getByte(self, addr: Union[str, int], signed: bool = True, admin: bool = False) -> int:
        # Get a byte of memory from main memory
        # Returns an decimal integer representation of the byte (-128 ~ 127) if signed
        # Returns (0 ~ 255) if unsigned
        if not admin:
            check_bounds(int(addr))

        if str(addr) in self.data.keys():
            acc = self.data[str(addr)]

            if signed:  # Sign extend
                if acc & 0x80 > 0:
                    acc |= 0xFFFFFF00

            return overflow_detect(acc)

        else:
            # Randomly generate a byte
            if settings['warnings']:
                print(f'Warning: Reading from uninitialized byte {utility.format_hex(int(addr))}!', file=sys.stderr)

            if self.toggle_garbage:
                self.addByte(random.randint(0, 0xFF), addr, admin=True)
            else:
                self.addByte(0, addr, admin=True)

            return self.getByte(addr, signed=signed, admin=admin)

    # Get a word (4 bytes) of memory from main memory
    # Returns a decimal integer representation of the word
    def getWord(self, addr: int) -> int:
        if addr % 4 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not word aligned.")

        acc = 0  # Result

        for i in reversed(range(4)):  # Little Endian: Go from MSB to LSB
            check_bounds(addr + i)

            # Get the ith byte of the word
            byte = self.getByte(addr + i, signed=False)
            acc = acc << 8
            acc |= byte

        return overflow_detect(acc)

    # Get a half-word (2 bytes) of memory from main memory
    # Return a decimal integer representation of the word
    def getHWord(self, addr: int, signed: bool = True) -> int:
        if addr % 2 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not half-word aligned.")

        acc = 0  # Result

        for i in reversed(range(2)):  # Little Endian: Go from MSB to LSB
            check_bounds(addr + i)

            # Get the ith byte of the word
            byte = self.getByte(addr + i, signed=False)
            acc = acc << 8
            acc |= byte

        if signed:  # Sign extend
            if acc & 0x8000 > 0:
                acc |= 0xFFFF0000

        return overflow_detect(acc)

    def getFloat(self, addr: int) -> float32:
        data_int = self.getWord(addr)
        return struct.unpack('>f', data_int.to_bytes(4, 'big', signed=True))[0]

    def getDouble(self, addr: int) -> float:
        if addr % 8 != 0:
            raise ex.MemoryAlignmentError(f"{utility.format_hex(addr)} is not double-word aligned.")

        data_lower = self.getWord(addr)
        data_upper = self.getWord(addr + 4)
        data_int = (data_upper << 32) + data_lower

        return struct.unpack('>d', data_int.to_bytes(8, 'big', signed=True))[0]

    def getLabel(self, s: str) -> Union[int, None]:
        if s in self.labels:
            return self.labels[s]

        return None

    def getString(self, label: str, n: int = 100) -> Union[str, None]:
        addr = self.getLabel(label)

        if addr is None:
            return None

        count = 0
        ret = ''

        c = self.getByte(addr, signed=False)

        while c != 0 and count < n:
            if c < 128:
                if c == 9:  # Tab
                    ret += '\\t'
                elif c == 10:  # Newline
                    ret += '\\n'
                elif c == 13:  # Carriage return
                    ret += '\\r'
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

    # Dump the contents of memory
    def dump(self) -> None:
        print(self.stack)
        print(self.data)
        print(self.text)
        print(self.labels)
