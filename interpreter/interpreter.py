import os
import random
import re
import struct
import sys
from collections import OrderedDict

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget
from numpy import float32

import constants as const
from interpreter import exceptions as ex, instructions as instrs
from interpreter.classes import *
from interpreter.debugger import Debug
from interpreter.memory import Memory
from interpreter.syscalls import syscalls
from settings import settings


class Interpreter(QWidget):
    step = Signal()
    console_out = Signal(str)
    end = Signal(bool)

    def out(self, s: str, end='', file=sys.stdout) -> None:
        if settings['gui']:
            self.console_out.emit(f'{s}{end}')
        else:
            print(s, end=end, file=file)

    def __init__(self, code: List, args: List[str]):
        if settings['gui']:
            super().__init__()

        self.reg_initialized = set()
        self.reg = OrderedDict()
        self.f_reg = dict()

        self.init_registers(settings['garbage_registers'])
        self.mem = Memory(settings['garbage_memory'])

        self.instruction_count = 0
        self.line_info = ''
        self.debug = Debug()
        self.instr = None

        self.has_main = False
        self.initialize_memory(code, args)

    def initialize_memory(self, code: List, args: List[str]):
        if len(args) > 0:
            self.handleArgs(args)

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

                elif data_type == 'float':
                    mod = self.mem.dataPtr % 4
                    if mod != 0:
                        self.mem.dataPtr += (4 - mod)
                    for data in line.data:
                        self.mem.addFloat(data, self.mem.dataPtr)
                        self.mem.dataPtr += 4

                elif data_type == 'double':
                    mod = self.mem.dataPtr % 8
                    if mod != 0:
                        self.mem.dataPtr += (8 - mod)
                    for data in line.data:
                        self.mem.addDouble(data, self.mem.dataPtr)
                        self.mem.dataPtr += 8

                elif data_type == 'space':
                    for data in line.data:
                        for j in range(data):
                            if settings['garbage_memory']:
                                self.mem.addByte(random.randint(0, 0xFF), self.mem.dataPtr)
                            else:
                                self.mem.addByte(0, self.mem.dataPtr)

                            self.mem.dataPtr += 1

                elif data_type == 'align':
                    if not 0 <= line.data <= 3:
                        raise ex.InvalidImmediate('Value for .align is invalid')

                    align = 2 ** line.data

                    mod = self.mem.dataPtr % align

                    if mod != 0:
                        self.mem.dataPtr += (align - mod)

            elif type(line) == Label:
                if line.name == 'main':
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

        comp = re.compile(r'(lb[u]?|lh[u]?|lw[lr]|lw|la|s[bhw]|sw[lr])')

        for line in code:  # Replace the labels in load/store instructions by the actual address
            if type(line) == PseudoInstr and comp.match(line.operation):
                addr = self.mem.getLabel(line.label.name)

                if addr:
                    line.instrs[0].imm = (addr >> 16) & 0xFFFF
                    line.instrs[1].imm = addr & 0xFFFF
                else:
                    raise ex.InvalidLabel(f'{line.label.name} is not a valid label. {self.line_info}')

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
            if f'initial_{r}' in settings.keys():
                self.reg[r] = settings[f'initial_{r}']

            elif randomize:
                self.reg[r] = random.randint(0, 2 ** 32 - 1)

            else:
                self.reg[r] = 0

        for r in const.F_REGS:
            if randomize:
                random_bytes = os.urandom(4)
                self.f_reg[r] = float32(struct.unpack('>f', random_bytes)[0])

            else:
                self.f_reg[r] = float32(0.0)

    def get_register(self, reg: str) -> int:
        key = reg

        if reg[1:].isnumeric():
            x = int(reg[1:])
            key = list(self.reg.keys())[x]

        if settings['warnings'] and key[1] in {'s', 't', 'a', 'v'} and key not in {'$at', '$sp'} and key not in self.reg_initialized:
            print(f'Reading from uninitialized register {key}!', file=sys.stderr)

        return instrs.overflow_detect(self.reg[key])

    def set_register(self, reg: str, data: int) -> None:
        if reg == '$0':
            raise ex.WritingToZeroRegister(f' {self.line_info}')

        key = reg

        if reg[1:].isnumeric():
            x = int(reg[1:])
            key = list(self.reg.keys())[x]

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

            if op in {'mult', 'multu', 'madd', 'maddu', 'msub', 'msubu'}:
                signed = op[-1] == 'u'
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
                signed = op[-1] == 'u'
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

        # Load or store from memory
        elif type(instr) == LoadMem:
            op = instr.operation
            reg = instr.reg
            addr = self.get_register(instr.addr) + instr.imm

            if op in ['lwr', 'lwl']:
                result = instrs.table[op](addr, self.mem, self.get_register(reg))
                self.set_register(reg, result)

            elif op[0] == 'l':  # lw, lh, lb
                result = instrs.table[op](addr, self.mem)
                self.set_register(reg, result)

            else:  # Store instructions
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
                syscalls[str(code)](self.reg, self.mem, self)

            else:
                raise ex.InvalidSyscall('Not a valid syscall code:')

        # Branches
        elif type(instr) == Branch:
            op = instr.operation
            rs = self.get_register(instr.rs)
            rt = self.get_register(instr.rt)

            if 'z' in op:
                result = instrs.table[op[:-1]](rs)
            else:
                result = instrs.table[op](rs, rt)

            if result:
                label = instr.label.name
                addr = self.mem.getLabel(label)

                if addr is None:
                    raise ex.InvalidLabel(f'{label} is not a valid label.')

                if 'al' in op:
                    instrs.jal(self.reg, self.mem, label)
                else:
                    self.set_register('pc', addr)

        elif type(instr) == Nop:
            pass

        elif type(instr) == Breakpoint:
            raise ex.BreakpointException(f'code = {instr.code}')

    def interpret(self) -> None:
        try:
            while True:
                # Get the next instruction and increment pc
                pc = self.reg['pc']

                if str(pc) not in self.mem.text:
                    raise ex.MemoryOutOfBounds(f'{pc} is not a valid address')

                if self.instruction_count > settings['max_instructions']:
                    raise ex.InstrCountExceed(f'Exceeded maximum instruction count: {settings["max_instructions"]}')

                self.instr = self.mem.text[str(pc)]
                self.reg['pc'] += 4
                self.instruction_count += 1

                try:
                    self.line_info = f' ({self.instr.filetag.file_name}, {self.instr.filetag.line_no})'
                except AttributeError:
                    self.line_info = ''

                if self.instr == 'TERMINATE_EXECUTION':
                    if settings['debug']:
                        print()
                        self.debug.listen(self)

                    if settings['gui']:
                        self.end.emit(False)

                    break

                elif self.debug.debug(self.instr):
                    self.debug.listen(self)

                self.execute_instr(self.instr)

                if settings['gui']:
                    self.step.emit()

        except Exception as e:
            if hasattr(e, 'message'):
                e.message += ' ' + self.line_info

                if settings['gui']:
                    self.end.emit(False)

            raise e

    def dump(self) -> None:
        # Dump the contents in registers and memory
        print('Registers:')

        for name, val in self.reg.items():
            print(f'{name}: {val}')

        print('Memory:')
        self.mem.dump()
