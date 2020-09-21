import random
from collections import OrderedDict
from typing import Dict, Union

import settings
from constants import WORD_SIZE, WORD_MASK
from interpreter import exceptions as ex
from interpreter import utility
from interpreter.instructions import overflow_detect
from interpreter.memory import Memory


# Given an ASCII code, Check if a character is not printable.
def isInvalidChar(c: int) -> bool:
    return (c < 32 and (c != 10 and c != 9 and c != 13)) or c >= 127


# Get a string starting from a specified address until null terminator is hit or
# a certain number of chars are read
def getString(addr: int, mem: Memory, num_chars: int = -1) -> Union[str, None]:
    name = ""
    c = mem.getByte(addr, signed=False)

    while c != 0 and num_chars != 0:
        if isInvalidChar(c):
            return None

        name += chr(c)
        addr += 1

        c = mem.getByte(addr, signed=False)
        num_chars -= 1

    return name


def printInt(reg: Dict[str, int], mem, out) -> None:
    out(overflow_detect(int(reg['$a0'])), end='')


def printHex(reg: Dict[str, int], mem, out) -> None:
    value = int(reg['$a0'])
    out(utility.format_hex(value), end='')


def printBin(reg: Dict[str, int], mem, out) -> None:
    value = int(reg['$a0'])
    out(f'0b{value & WORD_MASK:032b}', end='')


def printUnsignedInt(reg: Dict[str, int], mem, out) -> None:
    value = int(reg['$a0'])
    if value < 0:
        value += WORD_SIZE

    out(value, end='')


def printString(reg: Dict[str, int], mem: Memory, out) -> None:
    # Get the first byte of the string
    addr = reg['$a0']  # Starting address of the string
    c = mem.getByte(str(addr), signed=False)

    while c != 0:  # Keep printing until we hit a null terminator
        if isInvalidChar(c):
            raise ex.InvalidCharacter(f'Character with ASCII code {c} can\'t be printed.')

        out(chr(c), end='')

        addr += 1  # Increment address
        c = mem.getByte(addr, signed=False)


def atoi(reg: Dict[str, int], mem: Memory, out=None) -> None:
    # Converts string to integer
    # a0: address of null-terminated string
    # result: $v0 contains integer converted from string

    # Get the first byte of the string
    addr = reg['$a0']
    sign = 1

    # First, check if the number is negative
    if mem.getByte(str(addr), signed=False) == ord('-'):
        sign = -1
        addr += 1

    result = 0
    c = mem.getByte(str(addr), signed=False)

    # Then, check if the string is empty
    if c == 0:
        raise ex.InvalidCharacter('Empty string passed to atoi syscall')

    while c != 0:  # Keep going until null terminator
        if c < ord('0') or c > ord('9'):
            raise ex.InvalidCharacter(f'Character with ASCII code {c} is not a number')

        result *= 10
        result += c - ord('0')

        addr += 1  # Increment address
        c = mem.getByte(str(addr), signed=False)

    result *= sign
    reg['$v0'] = overflow_detect(result)


def readInteger(reg: Dict[str, int], mem, out=None) -> None:
    read = input()

    try:
        reg['$v0'] = overflow_detect(int(read))

    except ValueError:
        raise ex.InvalidInput(read)


def readString(reg: Dict[str, int], mem: Memory, out=None) -> None:
    s = input()

    s = utility.handle_escapes(s)
    s = s[:int(reg['$a1'])]

    mem.addAsciiz(s, int(reg['$a0']))


def sbrk(reg: Dict[str, int], mem: Memory, out=None) -> None:
    if mem.heapPtr > settings.settings['initial_$sp']:
        raise ex.MemoryOutOfBounds('Heap has exceeded the upper limit of ' + str(settings.settings['initial_$sp']))

    if reg['$a0'] < 0:
        raise ex.InvalidArgument('$a0 must be a non-negative number.')

    reg['$v0'] = mem.heapPtr
    mem.heapPtr += reg['$a0']

    if mem.heapPtr % 4 != 0:
        mem.heapPtr += 4 - (mem.heapPtr % 4)


def _exit(reg, mem, out=None) -> None:
    exit()


def printChar(reg: Dict[str, int], mem, out) -> None:
    c = reg['$a0']

    if isInvalidChar(c):
        raise ex.InvalidCharacter(f'Character with ASCII code {c} can\'t be printed.')

    out(chr(c), end='')


def memDump(reg: Dict[str, int], mem: Memory, out) -> None:
    # Set lower and upper bounds for addresses to dump memory contents
    low = reg['$a0']
    high = reg['$a1']

    if low % 4 != 0:
        low -= (low % 4)

    if high % 4 != 0:
        high += (4 - (high % 4))

    i = low  # Address
    out(f'{"addr":12s}{"hex":16s}{"ascii":12s}\n')

    while i < high:
        out(hex(i), end='  ')  # out address

        # Printing in LITTLE ENDIAN
        for step in reversed(range(4)):  # out memory contents in hex
            w = mem.getByte(i + step, signed=False)
            byte = hex(w)[2:]  # Get rid of the "0x"

            if len(byte) == 1:  # Pad with zero if it is one character
                byte = "0" + byte

            out(byte, end='  ')

        for step in reversed(range(4)):  # out memory contents in ASCII
            c = mem.getByte(i + step, signed=False)

            if c in range(127):
                if c == 0:  # Null terminator
                    out("\\0", end=' ')

                elif c == 9:  # Tab
                    out("\\t", end=' ')

                elif c == 10:  # Newline
                    out("\\n", end=' ')

                elif c >= 32:  # Regular character
                    out(chr(c), end='  ')

                else:  # Invalid character
                    out('.', end='  ')

            else:  # Invalid character
                out('.', end='  ')

        out("\n")
        i += 4  # Go to next word


def regDump(reg: Dict[str, int], mem, out) -> None:
    out(f'{"reg":4} {"hex":10} {"dec"}\n')

    for k, value in reg.items():
        out(f'{k:4} {utility.format_hex(value)} {overflow_detect(value):d}\n')


def openFile(reg: Dict[str, int], mem: Memory, out=None) -> None:
    # searches through to find the lowest unused value for a file descriptor
    fd = 0

    while True:
        if fd not in mem.fileTable:
            break

        fd += 1

    # get the string from memory
    name = getString(reg['$a0'], mem)

    if name is None:
        reg['$v0'] = -1
        return

    # set flags
    flags = {
        0: 'w',
        1: 'r',
        9: 'a'
    }

    if reg['$a1'] not in flags:
        reg['$v0'] = -1
        return

    flag = flags[reg['$a1']]

    # open the file
    f = open(name, flag)
    mem.fileTable[fd] = f

    reg['$v0'] = fd


def readFile(reg: Dict[str, int], mem: Memory, out=None) -> None:
    fd = reg['$a0']
    addr = reg['$a1']
    num_chars = reg['$a2']

    if fd not in mem.fileTable:
        reg['$v0'] = -1
        return

    s = mem.fileTable[fd].read(num_chars)
    mem.addAscii(s, addr)

    reg['$v0'] = len(s)


def writeFile(reg: Dict[str, int], mem: Memory, out=None) -> None:
    fd = reg['$a0']

    if fd not in mem.fileTable:
        reg['$v0'] = -1
        return

    s = getString(reg['$a1'], mem, num_chars=reg['$a2'])

    mem.fileTable[fd].write(s)
    reg['$v0'] = len(s)


def closeFile(reg: Dict[str, int], mem: Memory, out=None) -> None:
    fd = reg['$a0']

    if fd in mem.fileTable and fd >= 3:
        f = mem.fileTable.pop(fd)
        f.close()


# this can be expanded to print more info about the individual files if we so want to
def dumpFiles(reg, mem: Memory, out) -> None:
    for k, i in mem.fileTable.items():
        s = ''
        if k == 0:
            s = 'stdin'
        elif k == 1:
            s = 'stdout'
        elif k == 2:
            s = 'stderr'
        else:
            s = i.name
        out(str(k) + '\t' + s + '\n')


def _exit2(reg: Dict[str, int], mem, out=None) -> None:
    exit(reg['$a0'])


# For random integer generation
def setSeed(reg: Dict[str, int], mem, out=None) -> None:
    # a0: seed
    random.seed(reg['$a0'])


def randInt(reg: Dict[str, int], mem, out=None) -> None:
    # Generates a random integer in range [0, a0] (inclusive)
    # Puts result in $v0
    upper = reg['$a0']

    if upper < 0:
        raise ex.InvalidArgument('Upper value for randInt must be nonnegative')

    reg['$v0'] = random.randint(0, upper)


syscalls = OrderedDict([('1', printInt),
                        ('4', printString),
                        ('5', readInteger),
                        ('6', atoi),
                        ('8', readString),
                        ('9', sbrk),
                        ('10', _exit),
                        ('11', printChar),
                        ('13', openFile),
                        ('14', readFile),
                        ('15', writeFile),
                        ('16', closeFile),
                        ('17', _exit2),
                        ('30', memDump),
                        ('31', regDump),
                        ('32', dumpFiles),
                        ('34', printHex),
                        ('35', printBin),
                        ('36', printUnsignedInt),
                        ('40', setSeed),
                        ('41', randInt)])
