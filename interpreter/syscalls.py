import random
from typing import Dict, Union

from settings import settings
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


def printInt(inter) -> None:
    inter.out(inter.get_register('$a0'), end='')


def printHex(inter) -> None:
    value = inter.get_register('$a0')
    inter.out(utility.format_hex(value), end='')


def printBin(inter) -> None:
    value = inter.get_register('$a0')
    inter.out(f'0b{value & WORD_MASK:032b}', end='')


def printUnsignedInt(inter) -> None:
    value = inter.get_register('$a0')
    if value < 0:
        value += WORD_SIZE

    inter.out(value, end='')


def printFloat(inter) -> None:
    value = inter.get_reg_float('$f12')
    inter.out(value, end='')


def printDouble(inter) -> None:
    value = inter.get_reg_double('$f12')
    inter.out(value, end='')


def printString(inter) -> None:
    # Get the first byte of the string
    addr = inter.get_register('$a0')  # Starting address of the string
    c = inter.mem.getByte(str(addr), signed=False)

    while c != 0:  # Keep printing until we hit a null terminator
        if isInvalidChar(c):
            raise ex.InvalidCharacter(f'Character with ASCII code {c} can\'t be printed.')

        inter.out(chr(c), end='')

        addr += 1  # Increment address
        c = inter.mem.getByte(addr, signed=False)


def atoi(inter) -> None:
    # Converts string to integer
    # a0: address of null-terminated string
    # result: $v0 contains integer converted from string

    # Get the first byte of the string
    addr = inter.get_register('$a0')
    sign = 1

    # First, check if the number is negative
    if inter.mem.getByte(str(addr), signed=False) == ord('-'):
        sign = -1
        addr += 1

    result = 0
    c = inter.mem.getByte(str(addr), signed=False)

    # Then, check if the string is empty
    if c == 0:
        raise ex.InvalidCharacter('Empty string passed to atoi syscall')

    while c != 0:  # Keep going until null terminator
        if c < ord('0') or c > ord('9'):
            raise ex.InvalidCharacter(f'Character with ASCII code {c} is not a number')

        result *= 10
        result += c - ord('0')

        addr += 1  # Increment address
        c = inter.mem.getByte(str(addr), signed=False)

    result *= sign
    inter.set_register('$v0', result)


def readInteger(inter) -> None:
    read = inter.input()

    try:
        inter.set_register('$v0', int(read))

    except ValueError:
        raise ex.InvalidInput(read)


def readString(inter) -> None:
    s = inter.input()

    s = utility.handle_escapes(s)
    s = s[:inter.get_register('$a1')]

    inter.mem.addAsciiz(s, inter.get_register('$a0'))


def sbrk(inter) -> None:
    if inter.mem.heapPtr > settings['initial_$sp']:
        raise ex.MemoryOutOfBounds('Heap has exceeded the upper limit of ' + str(settings['initial_$sp']))

    size = inter.get_register('$a0')

    if size < 0:
        raise ex.InvalidArgument('$a0 must be a non-negative number.')

    inter.set_register('$v0', inter.mem.heapPtr)
    inter.mem.heapPtr += size

    if inter.mem.heapPtr % 4 != 0:
        inter.mem.heapPtr += 4 - (inter.mem.heapPtr % 4)


def _exit(inter) -> None:
    if settings['gui']:
        inter.end.emit(False)
    exit()


def printChar(inter) -> None:
    c = inter.get_register('$a0')

    if isInvalidChar(c):
        raise ex.InvalidCharacter(f'Character with ASCII code {c} can\'t be printed.')

    inter.out(chr(c), end='')


def memDump(inter) -> None:
    # Set lower and upper bounds for addresses to dump memory contents
    low = inter.get_register('$a0')
    high = inter.get_register('$a1')

    if low % 4 != 0:
        low -= (low % 4)

    if high % 4 != 0:
        high += (4 - (high % 4))

    i = low  # Address
    inter.out(f'{"addr":12s}{"hex":16s}{"ascii":12s}\n')

    while i < high:
        inter.out(hex(i), end='  ')  # inter.out address

        # Printing in LITTLE ENDIAN
        for step in reversed(range(4)):  # inter.out memory contents in hex
            w = inter.mem.getByte(i + step, signed=False)
            byte = hex(w)[2:]  # Get rid of the "0x"

            if len(byte) == 1:  # Pad with zero if it is one character
                byte = "0" + byte

            inter.out(byte, end='  ')

        for step in reversed(range(4)):  # inter.out memory contents in ASCII
            c = inter.mem.getByte(i + step, signed=False)

            if c in range(127):
                if c == 0:  # Null terminator
                    inter.out("\\0", end=' ')

                elif c == 9:  # Tab
                    inter.out("\\t", end=' ')

                elif c == 10:  # Newline
                    inter.out("\\n", end=' ')

                elif c >= 32:  # Regular character
                    inter.out(chr(c), end='  ')

                else:  # Invalid character
                    inter.out('.', end='  ')

            else:  # Invalid character
                inter.out('.', end='  ')

        inter.out("\n")
        i += 4  # Go to next word


def regDump(inter) -> None:
    inter.out(f'{"reg":4} {"hex":10} {"dec"}\n')

    for k, value in inter.reg.items():
        inter.out(f'{k:4} {utility.format_hex(value)} {overflow_detect(value):d}\n')


def openFile(inter) -> None:
    # searches through to find the lowest unused value for a file descriptor
    fd = 0

    while True:
        if fd not in inter.mem.fileTable:
            break

        fd += 1

    # get the string from memory
    name = getString(inter.get_register('$a0'), inter.mem)

    if name is None:
        inter.set_register('$v0', -1)
        return

    # set flags
    flags = {
        0: 'w',
        1: 'r',
        9: 'a'
    }

    mode = inter.get_register('$a1')

    if mode not in flags:
        inter.set_register('$v0', -1)
        return

    flag = flags[mode]

    # open the file
    f = open(name, flag)
    inter.mem.fileTable[fd] = f

    inter.set_register('$v0', fd)


def readFile(inter) -> None:
    fd = inter.get_register('$a0')
    addr = inter.get_register('$a1')
    num_chars = inter.get_register('$a2')

    if fd not in inter.mem.fileTable:
        inter.set_register('$v0', -1)
        return

    s = inter.mem.fileTable[fd].read(num_chars)
    inter.mem.addAscii(s, addr)

    inter.set_register('$v0', len(s))


def writeFile(inter) -> None:
    fd = inter.get_register('$a0')

    if fd not in inter.mem.fileTable:
        inter.set_register('$v0', -1)
        return

    s = getString(inter.get_register('$a1'), inter.mem, num_chars=inter.get_register('$a2'))

    inter.mem.fileTable[fd].write(s)
    inter.set_register('$v0', len(s))


def closeFile(inter) -> None:
    fd = inter.get_register('$a0')

    if fd in inter.mem.fileTable and fd >= 3:
        f = inter.mem.fileTable.pop(fd)
        f.close()


# this can be expanded to print more info abinter.out the individual files if we so want to
def dumpFiles(inter) -> None:
    for k, i in inter.mem.fileTable.items():
        if k == 0:
            s = 'stdin'
        elif k == 1:
            s = 'stdinter.out'
        elif k == 2:
            s = 'stderr'
        else:
            s = i.name

        inter.out(str(k) + '\t' + s + '\n')


def _exit2(inter) -> None:
    if settings['gui']:
        inter.end.emit(False)
    exit(inter.get_register('$a0'))


# For random integer generation
def setSeed(inter) -> None:
    # a0: seed
    random.seed(inter.get_register('$a0'))


def randInt(inter) -> None:
    # Generates a random integer in range [0, a0] (inclusive)
    # Puts result in $v0
    upper = inter.get_register('$a0')

    if upper < 0:
        raise ex.InvalidArgument('Upper value for randInt must be nonnegative')

    inter.set_register('$v0', random.randint(0, upper))


syscalls = {1: printInt,
            2: printFloat,
            3: printDouble,
            4: printString,
            5: readInteger,
            6: atoi,
            8: readString,
            9: sbrk,
            10: _exit,
            11: printChar,
            13: openFile,
            14: readFile,
            15: writeFile,
            16: closeFile,
            17: _exit2,
            30: memDump,
            31: regDump,
            32: dumpFiles,
            34: printHex,
            35: printBin,
            36: printUnsignedInt,
            40: setSeed,
            41: randInt}
