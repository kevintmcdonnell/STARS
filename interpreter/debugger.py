import re

import constants as const
from interpreter.classes import *
from interpreter.exceptions import InvalidRegister
from settings import settings

'''
https://github.com/sbustars/STARS

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
[d]elete: Clear all breakpoints\n\
[n]ext: Step to the next instruction\n\
[c]ontinue: Run until the next breakpoint\n\
[i]nfo b: Print information about the breakpoints\n\
[p]rint <flag>\
[p]rint <reg> <format>\n\
[p]rint <label> <data_type> <length> <format>\n\
[q]uit: Terminate the program\n\
[h]elp: Print this usage text\n\
[r]everse: Step back to the previous instruction\n")


def _print(cmd, interp):  # cmd = ['p', value, opts...]
    def str_value(val, base, bytes):
        # Return a string representation of a number as decimal, unsigned decimal, hex or binary
        # bytes: number of bytes to print (for hex, bin)
        if base == 'i':
            return str(val)

        elif base == 'u':
            unsigned_val = val if val >= 0 else val + const.WORD_SIZE
            return str(unsigned_val)

        elif base == 'x':
            return f'0x{val & 0xFFFFFFFF:0{2 * bytes}x}'

        elif base == 'b':
            return f'0b{val & 0xFFFFFFFF:0{8 * bytes}b}'

    # Print condition flag
    if len(cmd) == 2:
        try:
            flag = int(cmd[1])

            if 0 <= flag <= 7:
                print(interp.condition_flags[flag])
            else:
                print_usage_text()

        except ValueError:
            print_usage_text()

        return True

    # Invalid
    elif len(cmd) < 3:
        # Invalid form of input
        print_usage_text()
        return True

    # Integer register
    elif (cmd[1] in interp.reg or cmd[1] in interp.f_reg) and cmd[2] in ['i', 'u', 'x', 'b']:
        # Print contents of a register
        reg = cmd[1]
        base = cmd[2]

        if reg in interp.reg:
            value = interp.reg[reg]
        else:
            value = interp.get_reg_word(reg)

        print(f'{reg} {str_value(value, base, 4)}')
        return True

    # Floating point register
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

    # Data section
    elif len(cmd) >= 3 and cmd[1] in interp.mem.labels:
        # Print memory contents at a label
        label = cmd[1]
        data_type = cmd[2]

        if data_type == 's':  # print as string
            print(f'{label} {interp.mem.getString(label)}')
            return True

        elif len(cmd) == 5 and data_type in ['w', 'h', 'b']:
            base = cmd[4]

            if base not in ['i', 'u', 'x', 'b']:
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

        elif len(cmd) >= 4 and data_type in ['f', 'd']:
            # Get the number of floats/doubles to print
            try:
                length = int(cmd[3])

                if length < 1:
                    print_usage_text()
                    return True

            except ValueError:
                print_usage_text()
                return True

            addr = interp.mem.getLabel(label)

            if data_type == 'f':
                bytes = 4

            else:
                bytes = 8

            for i in range(length):
                if data_type == 'f':
                    val = interp.mem.getFloat(addr)

                else:
                    val = interp.mem.getDouble(addr)

                print(val)
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

                    elif c == 13:  # Carriage return
                        ret = "\\r"

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


def quit(cmd, interp) -> None:
    for i in range(3, len(interp.mem.fileTable)):
        interp.mem.fileTable[i].close()
    exit()


def next(cmd, interp) -> bool:
    return False


class Debug:
    def __init__(self):
        self.stack = []
        self.continueFlag = False
        self.breakpoints = set()
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
                       'q': quit,
                       'quit': quit,
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

        self.push(interp)

    def debug(self, instr) -> bool:
        # Returns whether to break execution and ask for input to debugger.
        # If continueFlag is true, then don't break execution.
        current = instr.filetag.file_name, str(instr.filetag.line_no)
        
        if settings['debug'] and current in self.breakpoints:
            self.continueFlag = False
            return True

        if not self.continueFlag:
            return settings['debug']

    def push(self, interp) -> None:
        def is_float_single(x):
            return '.s' in x

        def is_float_double(x):
            return '.d' in x

        instr = interp.instr
        prev = None

        prev_pc = interp.reg['pc'] - 4

        if type(instr) in {RType, IType}:
            op = instr.operation

            if op in {'mult', 'multu', 'madd', 'maddu', 'msub', 'msubu', 'div', 'divu'}:
                prev = MChange(interp.reg['hi'], interp.reg['lo'], prev_pc)

            else:
                dest_reg = instr.rd if type(instr) is RType else instr.rt

                if is_float_single(op):
                    prev = RegChange(dest_reg, interp.f_reg[dest_reg], prev_pc)
                elif is_float_double(op):
                    prev = RegChange(dest_reg, interp.f_reg[dest_reg], prev_pc, is_double=True)
                else:
                    prev = RegChange(dest_reg, interp.reg[dest_reg], prev_pc)

        elif type(instr) is Move:
            reg = instr.rd if 'f' in instr.operation else instr.rs
            prev = RegChange(reg, interp.reg[reg], prev_pc)

        elif type(instr) is LoadImm:
            prev = RegChange(instr.rt, interp.reg[instr.rt], prev_pc)

        elif type(instr) is JType:
            op = instr.operation

            # jal, jalr
            if 'l' in op:
                if type(instr.target) is Label:
                    prev = RegChange('$ra', interp.reg['$ra'], prev_pc)
                else:
                    prev = RegChange(instr.target, interp.reg[instr.target], prev_pc)

        elif type(instr) is LoadMem:
            op = instr.operation

            # Loads
            if op[0] == 'l':
                if is_float_single(op):
                    prev = RegChange(instr.rt, interp.f_reg[instr.rt], prev_pc)
                elif is_float_double(op):
                    prev = RegChange(instr.rt, interp.f_reg[instr.rt], prev_pc, is_double=True)
                else:
                    prev = RegChange(instr.rt, interp.reg[instr.rt], prev_pc)

            # Stores
            else:
                addr = interp.reg[instr.rs] + instr.imm

                if is_float_single(op):
                    prev = MemChange(addr, interp.mem.getFloat(addr), prev_pc, 'f')
                elif is_float_double(op):
                    prev = MemChange(addr, interp.mem.getDouble(addr), prev_pc, 'd')
                elif op[1] == 'w':
                    prev = MemChange(addr, interp.mem.getWord(addr), prev_pc, 'w')
                elif op[1] == 'h':
                    prev = MemChange(addr, interp.mem.getHWord(addr), prev_pc, 'h')
                else:
                    prev = MemChange(addr, interp.mem.getByte(addr), prev_pc, 'b')

        elif type(instr) is Compare:
            flag = instr.imm
            prev = FlagChange(flag, interp.condition_flags[flag], prev_pc)

        elif type(instr) is Convert:
            dest_reg = instr.rs

            if instr.format_to == 'd':
                prev = RegChange(dest_reg, interp.f_reg[dest_reg], prev_pc, is_double=True)
            else:
                prev = RegChange(dest_reg, interp.f_reg[dest_reg], prev_pc)

        elif type(instr) is MoveFloat or type(instr) is MoveCond:
            op = instr.operation

            if op == 'mtc1':
                prev = RegChange(instr.rt, interp.f_reg[instr.rt], prev_pc)
            elif op == 'mfc1':
                prev = RegChange(instr.rs, interp.reg[instr.rs], prev_pc)
            elif is_float_single(op):
                prev = RegChange(instr.rs, interp.f_reg[instr.rs], prev_pc)
            else:
                prev = RegChange(instr.rs, interp.f_reg[instr.rs], prev_pc, is_double=True)

        else:  # branches, nops, jr, j
            prev = Change(prev_pc)

        self.stack.append(prev)

    def reverse(self, cmd, interp) -> bool:
        def is_float_reg(reg):
            return reg in const.F_REGS

        prev = None
        if len(self.stack) > 0:
            prev = self.stack.pop()

            if type(prev) is RegChange:
                if is_float_reg(prev.reg):
                    if prev.is_double:
                        interp.set_reg_double(prev.reg, prev.val)
                    else:
                        interp.set_reg_float(prev.reg, prev.val)

                else:
                    interp.reg[prev.reg] = prev.val

            elif type(prev) is MemChange:
                if prev.type == 'f':
                    interp.mem.addFloat(prev.val, prev.addr)
                elif prev.type == 'd':
                    interp.mem.addDouble(prev.val, prev.addr)
                elif prev.type == 'w':
                    interp.mem.addWord(prev.val, prev.addr)
                elif prev.type == 'h':
                    interp.mem.addHWord(prev.val, prev.addr)
                else:
                    interp.mem.addByte(prev.val, prev.addr)

            elif type(prev) is MChange:
                interp.reg['hi'] = prev.hi
                interp.reg['lo'] = prev.lo

            elif type(prev) is FlagChange:
                interp.condition_flags[prev.flag] = prev.value

            interp.reg['pc'] = prev.pc + 4
            interp.instr = interp.mem.text[str(prev.pc)]

        if settings['gui']:
            print(interp.reg['pc'])
            if prev != None:
                interp.step.emit(prev.pc)
            else:
                interp.step.emit(settings['initial_pc'])

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
            self.breakpoints.add((f'"{cmd[1]}"', cmd[2]))  # filename, lineno
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
