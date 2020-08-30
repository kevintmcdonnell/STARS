import random
from collections import OrderedDict
from typing import Dict, Union

import exceptions as ex
import settings
import utility
from constants import WORD_SIZE
from instructions import overflow_detect
from memory import Memory


def getString(addr: int, mem: Memory, num: int = -1) -> Union[None, str]:
    name = ""
    c = mem.getByte(addr, signed=False)

    while c != 0 and num != 0:
        if (c < 32 and (c != 10 and c != 9)) or c >= 127:
            return None

        name += chr(c)
        addr += 1
        c = mem.getByte(addr, signed=False)
        num -= 1

    return name


def printInt(reg: Dict[str, int], mem) -> None:
    print(overflow_detect(int(reg['$a0']), WORD_SIZE), end='')


def printHex(reg: Dict[str, int], mem) -> None:
    value = int(reg['$a0'])
    print(utility.format_hex(value), end='')


def printBin(reg: Dict[str, int], mem) -> None:
    value = int(reg['$a0'])
    print(f'0b{value & 0xFFFFFFFF:032b}', end='')


def printUnsignedInt(reg: Dict[str, int], mem) -> None:
    value = int(reg['$a0'])
    if value < 0:
        value += WORD_SIZE

    print(value, end='')


def printString(reg: Dict[str, int], mem: Memory) -> None:
    # Get the first byte of the string
    c = mem.getByte(str(reg['$a0']), signed=False)
    addr = OrderedDict(reg)['$a0']  # Starting address of the string

    while c != 0:  # Keep printing until we hit a null terminator
        if (c < 32 and (c != 10 and c != 9)) or c >= 127:
            raise ex.InvalidCharacterException(f'Character with ASCII code {c} can\'t be printed.')

        a = chr(c)
        print(a, end='')

        addr += 1  # Increment address
        c = mem.getByte(str(addr), signed=False)


def atoi(reg: Dict[str, int], mem: Memory) -> None:
    # Converts string to integer
    # a0: address of null-terminated string
    # result: $v0 contains integer converted from string

    # Get the first byte of the string
    addr = OrderedDict(reg)['$a0']  # Starting address of the string
    sign = 1

    # First, check if the number is negative
    if mem.getByte(str(addr), signed=False) == ord('-'):
        sign = -1
        addr = addr + 1

    result = 0
    c = mem.getByte(str(addr), signed=False)

    # Then, check if the string is empty
    if mem.getByte(str(addr), signed=False) == 0:
        raise ex.InvalidCharacterException('Empty string passed to atoi syscall')

    while c != 0:  # Keep going until null terminator
        if c < 48 or c > 57:
            raise ex.InvalidCharacterException(f'Character with ASCII code {c} is not a number')

        result *= 10
        result += c - 48

        addr += 1  # Increment address
        c = mem.getByte(str(addr), signed=False)

    result *= sign
    reg['$v0'] = overflow_detect(result, WORD_SIZE)


def readInteger(reg: Dict[str, int], mem) -> None:
    read = input()

    try:
        reg['$v0'] = overflow_detect(int(read), WORD_SIZE)

    except ValueError:
        raise ex.InvalidInputException(read)


def readString(reg: Dict[str, int], mem: Memory) -> None:
    s = input()
    s = s[:int(reg['$a1'])]
    mem.addAsciiz(s, int(reg['$a0']))


def sbrk(reg: Dict[str, int], mem: Memory) -> None:
    if mem.heapPtr > settings.settings['initial_$sp']:
        raise ex.MemoryOutOfBoundsException('Heap has exceeded the upper limit of ' + str(settings.settings['initial_$sp']))

    if reg['$a0'] < 0:
        raise ex.InvalidArgumentException('$a0 must be a non-negative number.')

    reg['$v0'] = mem.heapPtr
    mem.heapPtr += reg['$a0']

    if mem.heapPtr % 4 != 0:
        mem.heapPtr += 4 - (mem.heapPtr % 4)


def _exit(reg, mem) -> None:
    exit()


def printChar(reg: Dict[str, int], mem) -> None:
    c = reg['$a0']

    if (c < 32 and (c != 10 and c != 9)) or c >= 127:
        raise ex.InvalidCharacterException('Character with ASCII code ' + str(c) + ' can\'t be printed.')

    print(chr(c), end='')


def memDump(reg: Dict[str, int], mem: Memory) -> None:
    # Set lower and upper bounds for addresses to dump memory contents
    low = reg['$a0']
    high = reg['$a1']

    if low % 4 != 0:
        low -= (low % 4)

    if high % 4 != 0:
        high += (4 - (high % 4))

    i = low  # Address
    print(f'{"addr":12s}{"hex":16s}{"ascii":12s}')

    while i < high:
        print(hex(i), end='  ')  # Print address

        # Printing in LITTLE ENDIAN
        for step in range(3, -1, -1):  # Print memory contents in hex
            w = mem.getByte(i + step, signed=False)
            byte = hex(w)[2:]  # Get rid of the "0x"

            if len(byte) == 1:  # Pad with zero if it is one character
                byte = "0" + byte

            print(byte, end='  ')

        for step in range(3, -1, -1):  # Print memory contents in ASCII
            c = mem.getByte(i + step, signed=False)

            if c in range(127):
                if c == 0:  # Null terminator
                    print("\\0", end=' ')

                elif c == 9:  # Tab
                    print("\\t", end=' ')

                elif c == 10:  # Newline
                    print("\\n", end=' ')

                elif c >= 32:  # Regular character
                    print(chr(c), end='  ')

                else:  # Invalid character
                    print('.', end='  ')

            else:  # Invalid character
                print('.', end='  ')

        print('\n', end='')
        i += 4  # Go to next word


def regDump(reg: Dict[str, int], mem) -> None:
    print(f'{"reg":4} {"hex":10} {"dec"}')

    for k in reg.keys():
        print(f'{k:4} {utility.format_hex(reg[k])} {overflow_detect(reg[k], WORD_SIZE):d}')


def openFile(reg: Dict[str, int], mem: Memory) -> None:
    # searches through to find the lowest unused value for a file descriptor
    fd = 0
    for f in mem.fileTable:
        if fd == f:
            fd += 1

    # get the string from memory
    name = getString(reg['$a0'], mem)
    if name is None:
        reg['$v0'] = -1
        return

    # set flags
    flags = ""
    if reg['$a1'] == 0:
        flags = 'w'
    elif reg['$a1'] == 1:
        flags = 'r'
    elif reg['$a1'] == 9:
        flags = 'a'
    else:
        reg["$v0"] = -1

    # open the file
    f = open(name, flags)
    mem.fileTable[fd] = f

    reg['$v0'] = fd


# TODO: see how MARS determines when EOF occurs, bc python has basically no method for EOF
def readFile(reg: Dict[str, int], mem: Memory) -> None:
    if reg['$a0'] not in mem.fileTable.keys():
        reg['$v0'] = -1
        return
    s = mem.fileTable[reg['$a0']].read(reg['$a2'])
    mem.addAsciiz(s, reg['$a1'])

    if len(s) < reg['$a2']:
        reg['$v0'] = 0
    else:
        reg['$v0'] = len(s)


def writeFile(reg: Dict[str, int], mem: Memory) -> None:
    if reg['$a0'] not in mem.fileTable.keys():
        reg['$v0'] = -1
        return
    s = getString(reg['$a1'], mem, num=reg['$a2'])

    mem.fileTable[reg['$a0']].write(s)
    reg['$v0'] = len(s)


def closeFile(reg: Dict[str, int], mem: Memory) -> None:
    if reg['$a0'] in mem.fileTable.keys() and reg['$a0'] not in [0, 1, 2]:
        f = mem.fileTable.pop(reg['$a0'])
        f.close()


# this can be expanded to print more info about the individual files if we so want to
def dumpFiles(reg, mem: Memory) -> None:
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
        print(str(k) + '\t' + s)


def _exit2(reg: Dict[str, int], mem) -> None:
    exit(reg['$a0'])


# For random integer generation
def setSeed(reg: Dict[str, int], mem) -> None:
    # a0: seed
    random.seed(reg['$a0'])


def randInt(reg: Dict[str, int], mem) -> None:
    # Generates a random integer in range [0, a0] (inclusive)
    # Puts result in $v0
    upper = reg['$a0']

    if upper < 0:
        raise ex.InvalidArgumentException('Upper value for randInt must be nonnegative')

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
