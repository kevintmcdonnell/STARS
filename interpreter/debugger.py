import re

import constants as const
from interpreter.classes import *
from interpreter.exceptions import InvalidRegister
from settings import settings

'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


def print_usage_text() -> None:
    print("USAGE:  [b]reak <filename> <line_no>\n\
[d]elete\n\
[n]ext\n\
[c]ontinue\n\
[i]nfo b\n\
[p]rint <reg> <format>\n\
[p]rint <label> <data_type> <length> <format>\n\
kill\n\
[h]elp\n\
[r]everse\n")


def _print(cmd, interp):  # cmd = ['p', value, opts...]
    def str_value(val, base, bytes):
        # Return a string representation of a number as decimal, unsigned decimal, hex or binary
        # bytes: number of bytes to print (for hex, bin)
        if base == 'i':
            return str(val)

        elif base == 'u':
            unsigned_val = val if val >= 0 else val + const.WORD_SIZE
            return str(unsigned_val)

        elif base == 'h':
            return f'0x{val & 0xFFFFFFFF:0{2 * bytes}x}'

        elif base == 'b':
            return f'0b{val & 0xFFFFFFFF:0{8 * bytes}b}'

    if len(cmd) < 3:
        # Invalid form of input
        print_usage_text()
        return True

    if (cmd[1] in interp.reg or cmd[1] in interp.f_reg) and cmd[2] in ['i', 'u', 'h', 'b']:
        # Print contents of a register
        reg = cmd[1]
        base = cmd[2]

        if reg in interp.reg:
            value = interp.reg[reg]
        else:
            value = interp.get_reg_word(reg)

        print(f'{reg} {str_value(value, base, 4)}')
        return True

    elif cmd[1] in interp.f_reg and cmd[2] in ['f', 'd']:
        # Print contents of a floating point register
        reg = cmd[1]
        base = cmd[2]

        if base == 'f':
            print(f'{reg} {interp.get_reg_float(reg)}')
        else:
            try:
                print(f'{reg} {interp.get_reg_double(reg)}')
            except InvalidRegister:
                print('Not an even numbered register')

        return True

    elif len(cmd) >= 3 and cmd[1] in interp.mem.labels:
        # Print memory contents at a label
        label = cmd[1]
        data_type = cmd[2]

        if data_type == 's':  # print as string
            print(f'{label} {interp.mem.getString(label)}')
            return True

        elif len(cmd) == 5 and data_type in ['w', 'h', 'b']:
            base = cmd[4]

            if base not in ['d', 'u', 'h', 'b']:
                print_usage_text()
                return True

            # Get the number of words, halfs, bytes to print
            try:
                length = int(cmd[3])

                if length < 1:
                    print_usage_text()
                    return True

            except ValueError:
                print_usage_text()
                return True

            addr = interp.mem.getLabel(label)

            if data_type == 'w':
                bytes = 4

            elif data_type == 'h':
                bytes = 2

            else:
                bytes = 1

            for i in range(length):
                if data_type == 'w':
                    val = interp.mem.getWord(addr)

                elif data_type == 'h':
                    val = interp.mem.getHWord(addr)

                else:
                    val = interp.mem.getByte(addr)

                print(f'{str_value(val, base, bytes)}')
                addr += bytes

            return True

        elif len(cmd) >= 4 and data_type == 'c':  # Print as character
            try:
                length = int(cmd[3])

                if length < 1:
                    print_usage_text()
                    return True

            except ValueError:
                print_usage_text()
                return True

            addr = interp.mem.getLabel(label)
            print(f'{label}')

            for i in range(length):
                c = interp.mem.getByte(addr)

                if c in range(127):
                    if c == 0:  # Null
                        ret = "\\0"

                    elif c == 9:  # Tab
                        ret = "\\t"

                    elif c == 10:  # Newline
                        ret = "\\n"

                    elif c >= 32:  # Regular character
                        ret = chr(c)

                    else:  # Invalid character
                        ret = '.'

                else:  # Invalid character
                    ret = '.'

                print(f'\t{ret}')
                addr += 1

            return True

    print_usage_text()
    return True


def kill(cmd, interp) -> None:
    for i in range(3, len(interp.mem.fileTable)):
        interp.mem.fileTable[i].close()
    exit()


def next(cmd, interp) -> bool:
    return False


class Debug:
    def __init__(self):
        self.stack = []
        self.continueFlag = False
        self.breakpoints = []
        self.handle = {'b': self.addBreakpoint,
                       'break': self.addBreakpoint,
                       'n': next,
                       'next': next,
                       'c': self.cont,
                       'continue': self.cont,
                       'i': self.printBreakpoints,
                       'info': self.printBreakpoints,
                       'd': self.clearBreakpoints,
                       'delete': self.clearBreakpoints,
                       'p': _print,
                       'print': _print,
                       'kill': kill,
                       'r': self.reverse,
                       'reverse': self.reverse}

    def listen(self, interp):
        def strip_marker(instr):
            marker_idx = instr.find('\x81')

            if marker_idx >= 0:
                instr = instr[:marker_idx]

            return instr

        loop = True

        while loop and not settings['gui']:
            if type(interp.instr) is not str:
                if interp.instr.is_from_pseudoinstr:
                    instr_text = interp.instr.original_text.strip()
                    instr_text = strip_marker(instr_text)
                    print(f'{instr_text} ( {interp.instr.basic_instr()} )')

                else:
                    instr_text = interp.instr.original_text.strip()
                    instr_text = strip_marker(instr_text)
                    print(instr_text)

                print(' ' + interp.line_info)

            cmd = input('>')
            cmd = re.findall(r'\S+', cmd)

            if len(cmd) > 0 and cmd[0] in self.handle.keys():
                loop = self.handle[cmd[0]](cmd, interp)

            else:
                print_usage_text()

        if settings['gui']:
            interp.pause_lock.wait()
            if not self.continueFlag:
                interp.pause_lock.clear()

        # TODO: Fix this to work with floating point instructions
        # self.push(interp)

    def debug(self, instr) -> bool:
        # Returns whether to break execution and ask for input to debugger.
        # If continueFlag is true, then don't break execution.
        filename = instr.filetag.file_name
        lineno = instr.filetag.line_no

        if settings['debug'] and (filename, str(lineno)) in self.breakpoints:
            self.continueFlag = False
            return True

        if not self.continueFlag:
            return settings['debug']

    def push(self, interp) -> None:
        instr = interp.instr
        prev = None

        prev_pc = interp.reg['pc'] - 4

        if type(instr) is RType or type(instr) is IType:
            op = instr.operation

            if op in {'mult', 'multu', 'madd', 'maddu', 'msub', 'msubu', 'div', 'divu'}:
                prev = MChange(interp.reg['hi'], interp.reg['lo'], prev_pc)
            else:
                prev = RegChange(instr.regs[0], interp.reg[instr.regs[0]], prev_pc)

        elif type(instr) is LoadImm or type(instr) is Move:
            prev = RegChange(instr.reg, interp.reg[instr.reg], prev_pc)

        elif type(instr) is JType:
            op = instr.operation

            if 'l' in op:
                if type(instr.target) is Label:
                    prev = RegChange('$ra', interp.reg['$ra'], prev_pc)
                else:
                    prev = RegChange(instr.target, interp.reg[instr.target], prev_pc)

        elif type(instr) is LoadMem:
            op = instr.operation

            if op[0] == 'l':
                prev = RegChange(instr.reg, interp.reg[instr.reg], prev_pc)
            else:
                addr = interp.reg[instr.addr] + instr.imm

                if op[1] == 'w':
                    prev = MemChange(addr, interp.mem.getWord(addr), prev_pc, 'w')
                elif op[1] == 'h':
                    prev = MemChange(addr, interp.mem.getHWord(addr), prev_pc, 'h')
                else:
                    prev = MemChange(addr, interp.mem.getByte(addr), prev_pc, 'b')

        else:  # branches, nops, jr, j
            prev = Change(prev_pc)

        self.stack.append(prev)

    def reverse(self, cmd, interp) -> bool:
        if len(self.stack) > 0:
            prev = self.stack.pop()
            if type(prev) is RegChange:
                interp.reg[prev.reg] = prev.val

            elif type(prev) is MemChange:
                if prev.type == 'w':
                    interp.mem.addWord(prev.val, prev.addr)

                elif prev.type == 'h':
                    interp.mem.addHWord(prev.val, prev.addr)

                else:
                    interp.mem.addByte(prev.val, prev.addr)

            elif type(prev) is MChange:
                interp.reg['hi'] = prev.hi
                interp.reg['lo'] = prev.lo

            interp.reg['pc'] = prev.pc + 4
            interp.instr = interp.mem.text[str(prev.pc)]

        if settings['gui']:
            interp.step.emit()

        return True

    def cont(self, cmd, interp) -> bool:
        self.continueFlag = True
        return False

    def printBreakpoints(self, cmd, interp) -> bool:
        count = 1
        for b in self.breakpoints:
            print(f'{count} {b[0]} {b[1]}')
            count += 1
        return True

    def addBreakpoint(self, cmd: List[str], interp) -> bool:  # cmd = ['b', filename, lineno]
        if len(cmd) == 3 and str(cmd[2]).isdecimal():
            self.breakpoints.append((cmd[1], cmd[2]))  # filename, lineno
            return True

        print_usage_text()
        return True

    def clearBreakpoints(self, cmd: List[str], interp) -> bool:
        if len(cmd) == 1:
            self.breakpoints = []
        else:
            print_usage_text()
        return True

    def removeBreakpoint(self, cmd: List[str], interp) -> None:
        self.breakpoints.remove((cmd[0], cmd[1]))
