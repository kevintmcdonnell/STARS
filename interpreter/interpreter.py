import random
import re
import sys
from collections import OrderedDict

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget

import constants as const
from interpreter import exceptions as ex, instructions as instrs
from interpreter.classes import *
from interpreter.memory import Memory
from interpreter.syscalls import syscalls
from settings import settings


class Interpreter(QWidget):
    step = Signal()
    console_out = Signal(str)

    def out(self, s: str, end="") -> None:
        if settings['gui']:
            self.console_out.emit(f'{s}{end}')
        else:
            print(s, end=end)

    def __init__(self, code: List, args: List[str]):
        if settings['gui']:
            super().__init__()
        self.reg = OrderedDict()
        self.reg_initialized = set()

        self.init_registers(settings['garbage_registers'])
        self.mem = Memory(settings['garbage_memory'])

        self.instruction_count = 0
        self.line_info = ""
        self.debug = self.Debug()
        self.instr = None

        if len(args) > 0:
            self.handleArgs(args)

        self.has_main = False

        for line in code:  # Go through the source code line by line, adding declarations first
            if type(line) == Declaration:
                # Data declaration
                data_type = line.type[1:]

                # If a label is specified, add the label to memory
                if line.label:
                    self.mem.addLabel(line.label.name, self.mem.dataPtr)

                if data_type == 'asciiz':
                    # A null-terminated string
                    # There could be multiple strings separated by commas
                    # Add the string to memory and increment address in memory
                    s = line.data[1: -1]  # Remove quotation marks
                    s = utility.handle_escapes(s)

                    self.mem.addAsciiz(s, self.mem.dataPtr)
                    self.mem.dataPtr += len(s) + 1

                elif data_type == 'ascii':
                    # A regular string
                    s = line.data[1: -1]
                    s = utility.handle_escapes(s)

                    self.mem.addAscii(s, self.mem.dataPtr)
                    self.mem.dataPtr += len(s)

                elif data_type == 'byte':
                    for data in line.data:
                        self.mem.addByte(data, self.mem.dataPtr)
                        self.mem.dataPtr += 1

                elif data_type == 'word':
                    mod = self.mem.dataPtr % 4
                    if mod != 0:
                        self.mem.dataPtr += (4 - mod)
                    for data in line.data:
                        self.mem.addWord(data, self.mem.dataPtr)
                        self.mem.dataPtr += 4

                elif data_type == 'half':
                    mod = self.mem.dataPtr % 2
                    if mod != 0:
                        self.mem.dataPtr += (2 - mod)
                    for data in line.data:
                        self.mem.addHWord(data, self.mem.dataPtr)
                        self.mem.dataPtr += 2

                elif data_type == 'space':
                    for data in line.data:
                        for j in range(data):
                            if settings['garbage_memory']:
                                self.mem.addByte(random.randint(0, 0xFF), self.mem.dataPtr)
                            else:
                                self.mem.addByte(0, self.mem.dataPtr)
                            self.mem.dataPtr += 1

                elif data_type == 'align':
                    if line.data > 3 or line.data < 0:
                        raise ex.InvalidImmediate('Value for .align is invalid')

                    align = 2 ** line.data

                    mod = self.mem.dataPtr % align

                    if mod != 0:
                        self.mem.dataPtr += (align - mod)

            elif type(line) == Label:
                if line.name == "main":
                    self.has_main = True
                    self.reg['pc'] = self.mem.textPtr

                self.mem.addLabel(line.name, self.mem.textPtr)

            elif type(line) == PseudoInstr:
                for instr in line.instrs:
                    self.mem.addText(instr)

            else:
                self.mem.addText(line)

        if not self.has_main:
            raise ex.NoMainLabel('Could not find main label')

        comp = re.compile(r'((lb[u]?)|(lh[u]?)|(lw[lr])|(lw)|(la)|(s[bhw])|(sw[lr]))')

        for line in code:  # Now add the instructions
            if type(line) == PseudoInstr:
                if comp.match(line.operation):
                    addr = self.mem.getLabel(line.label.name)

                    if addr:
                        line.instrs[0].imm = (addr >> 16) & 0xFFFF
                        line.instrs[1].imm = addr & 0xFFFF
                    else:
                        raise ex.InvalidLabel(line.label.name + ' is not a valid label.' + self.line_info)

        # Special instruction to terminate execution after every instruction has been executed
        self.mem.addText('TERMINATE_EXECUTION')

    def handleArgs(self, args: List[str]) -> None:
        saveAddr = settings['data_max'] - 3
        stack = settings['initial_$sp']

        for arg in args:
            saveAddr -= (len(arg) + 1)
            self.mem.addAsciiz(arg, saveAddr)
            self.mem.addWord(saveAddr, stack)
            stack -= 4

        self.mem.addWord(len(args), stack)
        self.reg['$sp'] = stack
        self.reg['$a0'] = len(args)
        self.reg['$a1'] = stack + 4

    def init_registers(self, randomize: bool) -> None:
        for r in const.REGS:
            if 'initial_' + r in settings.keys():
                self.reg[r] = settings['initial_' + r]

            elif randomize:
                self.reg[r] = random.randint(0, 2 ** 32 - 1)

            else:
                self.reg[r] = 0

    def get_register(self, reg: str) -> int:
        key = reg
        try:
            x = int(reg[1:])
            key = list(self.reg.items())[x][0]
        except ValueError:
            pass

        if settings['warnings'] and key[1] in ['s', 't', 'a', 'v'] and key not in ['$at', '$sp'] and key not in self.reg_initialized:
            print(f'Reading from uninitialized register {key}!', file=sys.stderr)

        return instrs.overflow_detect(self.reg[key])

    def set_register(self, reg: str, data: int) -> None:
        if reg == '$0':
            raise ex.WritingToZeroRegister(" " + self.line_info)

        key = reg
        try:
            x = int(reg[1:])
            key = list(self.reg.items())[x][0]

        except ValueError:
            pass

        self.reg_initialized.add(key)
        self.reg[key] = instrs.overflow_detect(data)

    def execute_instr(self, instr) -> None:
        # Instruction with 3 registers
        if type(instr) == RType and len(instr.regs) == 3:
            op = instr.operation
            rd = instr.regs[0]
            rs = self.get_register(instr.regs[1])
            rt = self.get_register(instr.regs[2])

            result = instrs.table[op](rs, rt)

            if op == 'movz':
                if rt == 0:
                    self.set_register(rd, result)

            elif op == 'movn':
                if rt != 0:
                    self.set_register(rd, result)

            else:
                self.set_register(rd, result)

        # Instruction with 2 registers
        elif type(instr) == RType and len(instr.regs) == 2:
            op = instr.operation
            r1 = instr.regs[0]
            r2 = instr.regs[1]

            if op in ['mult', 'multu', 'madd', 'maddu', 'msub', 'msubu']:
                signed = len(op) == 4
                r1_data = self.get_register(r1)
                r2_data = self.get_register(r2)

                low, high = instrs.mul(r1_data, r2_data, thirty_two_bits=False, signed=signed)  # A 64 bit integer

                if 'mult' not in op:
                    lo_reg = self.get_register('lo')
                    hi_reg = self.get_register('hi')

                    if 'add' in op:
                        low = instrs.addu(lo_reg, low)
                        high = instrs.addu(hi_reg, high)
                    else:
                        low = instrs.subu(lo_reg, low)
                        high = instrs.subu(hi_reg, high)

                # Set lo to lower 32 bits, and hi to upper 32 bits
                self.set_register('lo', low)
                self.set_register('hi', high)

            elif op == 'div' or op == 'divu':
                signed = len(op) == 3
                result, remainder = instrs.div(self.get_register(r1), self.get_register(r2), signed=signed)

                # Set lo to quotient, and hi to remainder
                self.set_register('lo', result)
                self.set_register('hi', remainder)

            else:
                result = instrs.table[op](self.get_register(r2))
                self.set_register(r1, result)

        # j type instructions (Label)
        elif type(instr) == JType and type(instr.target) == Label:
            instrs.table[instr.operation](self.reg, self.mem, instr.target.name)

        # j type instructions (Return)
        elif type(instr) == JType:
            instrs.table[instr.operation](self.reg, instr.target)

        # i-type isntructions
        elif type(instr) == IType:
            op = instr.operation
            rd = instr.regs[0]
            rs = self.get_register(instr.regs[1])
            imm = instr.imm

            result = instrs.table[op](rs, imm)
            self.set_register(rd, result)

        # Load immediate
        elif type(instr) == LoadImm:
            if instr.operation == 'lui':
                upper = instrs.lui(instr.imm)
                self.set_register(instr.reg, upper)

        # Load from memory
        elif type(instr) == LoadMem:
            op = instr.operation
            reg = instr.reg
            addr = self.get_register(instr.addr) + instr.imm

            if op in ['lwr', 'lwl']:
                result = instrs.table[op](addr, self.mem, self.get_register(reg))
                self.set_register(reg, result)

            elif op in ['swr', 'swl']:
                pass

            elif op[0] == 'l':  # lw, lh, lb
                result = instrs.table[op](addr, self.mem)
                self.set_register(reg, result)

            else:  # sw, sh, sb
                instrs.table[op](addr, self.mem, self.get_register(reg))

        # Mfhi, mflo, mthi, mtlo
        elif type(instr) == Move:
            op = instr.operation

            if 'f' in op:
                src = op[2:]
                dest = instr.reg

            else:
                src = instr.reg
                dest = op[2:]

            self.set_register(dest, self.get_register(src))

        # syscall
        elif type(instr) == Syscall:
            code = self.get_register('$v0')

            if str(code) in syscalls.keys() and code in settings['enabled_syscalls']:
                syscalls[str(code)](self.reg, self.mem, self.out)

            else:
                raise ex.InvalidSyscall('Not a valid syscall code:')

        # Branches
        elif type(instr) == Branch:
            op = instr.operation
            rs = self.get_register(instr.rs)
            rt = self.get_register(instr.rt)

            if 'z' in op:
                result = instrs.table[op[:4]](rs)
            else:
                result = instrs.table[op](rs, rt)

            if result:
                label = instr.label.name
                addr = self.mem.getLabel(label)

                if addr is None:
                    raise ex.InvalidLabel(label + ' is not a valid label.')

                if 'al' in op:
                    instrs.jal(self.reg, self.mem, label)
                else:
                    self.set_register('pc', addr)

        elif type(instr) == Nop:
            pass

        elif type(instr) == Breakpoint:
            raise ex.BreakpointException("code = %d" % instr.code)

        else:
            raise ex.HoustonWeHaveAProblemException('oh no.')

    def interpret(self) -> None:
        try:
            while True:
                # Get the next instruction and increment pc
                if str(self.reg['pc']) not in self.mem.text:
                    raise ex.MemoryOutOfBounds(str(self.reg['pc']) + " is not a valid address")

                self.instr = self.mem.text[str(self.reg['pc'])]

                if self.instr != "TERMINATE_EXECUTION":
                    self.reg['pc'] += 4
                    self.instruction_count += 1

                if self.instruction_count > settings['max_instructions']:
                    raise ex.InstrCountExceed('Exceeded maximum instruction count: ' + str(settings['max_instructions']))

                try:
                    self.line_info = f' ({self.instr.filetag.file_name}, {self.instr.filetag.line_no})'

                except AttributeError:
                    self.line_info = ""

                if self.instr == 'TERMINATE_EXECUTION':
                    if settings['debug']:
                        print()
                        self.debug.listen(self)
                    break

                elif self.debug.debug(self.instr):

                    self.debug.listen(self)

                self.execute_instr(self.instr)
                if settings['gui']:
                    self.step.emit()

        except Exception as e:
            if hasattr(e, 'message'):
                e.message += " " + self.line_info
            raise e

    def dump(self) -> None:
        # Dump the contents in registers and memory
        print("Registers:")
        for s in self.reg:
            print(f'{s}: {self.reg[s]}')

        print("Memory:")
        self.mem.dump()

    class Debug():
        def __init__(self):
            self.stack = []
            self.continueFlag = False
            self.breakpoints = []
            self.handle = {'b': self.addBreakpoint,
                           'break': self.addBreakpoint,
                           'n': self.next,
                           'next': self.next,
                           'c': self.cont,
                           'continue': self.cont,
                           'i': self.printBreakpoints,
                           'info': self.printBreakpoints,
                           'd': self.clearBreakpoints,
                           'delete': self.clearBreakpoints,
                           'p': self.print,
                           'print': self.print,
                           'kill': self.kill,
                           'r': self.reverse,
                           'reverse': self.reverse}

        def listen(self, interp):
            loop = True

            while loop:
                if type(interp.instr) is not str:
                    if interp.instr.is_from_pseudoinstr:
                        print(f'{interp.instr.original_text.strip()} ( {interp.instr.basic_instr()} )')

                    else:
                        print(interp.instr.original_text.strip())

                    print(' ' + interp.line_info)

                cmd = input('>')
                cmd = re.findall('\S+', cmd)

                if len(cmd) > 0 and cmd[0] in self.handle.keys():
                    loop = self.handle[cmd[0]](cmd, interp)

                else:
                    self.print_usage_text()
            self.push(interp)

        def debug(self, instr) -> bool:
            # Returns whether to break execution and ask for input to debugger.
            # If continueFlag is true, then don't break execution.
            filename = instr.filetag.file_name
            lineno = instr.filetag.line_no

            if not self.continueFlag:
                return settings['debug']

            # If we encounter a breakpoint while executing, then break
            elif settings['debug'] and ((filename, str(lineno)) in self.breakpoints):
                self.continueFlag = False
                return True

        def print_usage_text(self) -> None:
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

        def push(self, interp) -> None:
            instr = interp.instr
            prev = None
            if type(instr) == RType or type(instr) == IType:
                op = instr.operation
                if op in ['mult', 'multu', 'madd', 'maddu', 'msub', 'msubu', 'div', 'divu']:
                    prev = MChange(interp.reg['hi'], interp.reg['lo'], interp.reg['pc'] - 4)
                else:
                    prev = RegChange(instr.regs[0], interp.reg[instr.regs[0]], interp.reg['pc'] - 4)
            elif type(instr) == LoadImm or type(instr) == Move:
                prev = RegChange(instr.reg, interp.reg[instr.reg], interp.reg['pc'] - 4)
            elif type(instr) == JType:
                op = instr.operation
                if 'l' in op:
                    if type(instr.target) == Label:
                        prev = RegChange('$ra', interp.reg['$ra'], interp.reg['pc'] - 4)
                    else:
                        prev = RegChange(instr.target, interp.reg[instr.target], interp.reg['pc'] - 4)
            elif type(instr) == LoadMem:
                op = instr.operation
                if op[0] == 'l':
                    prev = RegChange(instr.reg, interp.reg[instr.reg], interp.reg['pc'] - 4)
                else:
                    addr = interp.reg[instr.addr] + instr.imm
                    if instr.label:
                        addr = interp.mem.getLabel(instr.Label)
                    if op[1] == 'w':
                        prev = MemChange(addr, interp.mem.getWord(addr), interp.reg['pc'] - 4, 'w')
                    elif op[1] == 'h':
                        prev = MemChange(addr, interp.mem.getHWord(addr), interp.reg['pc'] - 4, 'h')
                    else:
                        prev = MemChange(addr, interp.mem.getByte(addr), interp.reg['pc'] - 4, 'b')
            else:  # branches, nops, jr, j
                prev = Change(interp.reg['pc'] - 4)

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

            return True

        def kill(self, cmd, interp) -> None:
            for i in range(3, len(interp.mem.fileTable)):
                interp.mem.fileTable[i].close()
            exit()

        def next(self, cmd, interp) -> bool:
            return False

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

            self.print_usage_text()
            return True

        def clearBreakpoints(self, cmd: List[str], interp) -> bool:
            if len(cmd) == 1:
                self.breakpoints = []
            else:
                self.print_usage_text()
            return True

        def print(self, cmd, interp):  # cmd = ['p', value, opts...]
            def str_value(val, base, bytes):
                # Return a string representation of a number as decimal, unsigned decimal, hex or binary
                # bytes: number of bytes to print (for hex, bin)
                if base == 'd':
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
                self.print_usage_text()
                return True

            if cmd[1] in interp.reg:
                # Print contents of a register
                reg = cmd[1]
                base = cmd[2]

                if base not in ['d', 'u', 'h', 'b']:
                    self.print_usage_text()
                    return True

                # Base is either d, u, h, b
                print(f'{reg} {str_value(interp.reg[reg], base, 4)}')
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
                        self.print_usage_text()
                        return True

                    # Get the number of words, halfs, bytes to print
                    try:
                        length = int(cmd[3])

                        if length < 1:
                            self.print_usage_text()
                            return True

                    except ValueError:
                        self.print_usage_text()
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
                            self.print_usage_text()
                            return True

                    except ValueError:
                        self.print_usage_text()
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

            self.print_usage_text()
            return True
