import os
import random
import re
import struct
import sys
from collections import OrderedDict
from threading import Event, Lock

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


class Interpreter(QWidget):
    start = Signal()
    step = Signal(int)
    end = Signal(bool)
    console_out = Signal(str) # use by out for printing to console
    user_input = Signal(int) # use by input/set_input for user input syscalls
    mem_access = Signal()

    def __init__(self, code: List, args: List[str]):
        if settings['gui']:
            super().__init__()

        self.reg_initialized = set()
        self.reg = OrderedDict()
        self.f_reg = dict()
        self.condition_flags = [False] * 8

        self.pause_lock = Event()
        self.input_lock = Event()
        self.lock_input = Lock()
        self.input_str = None

        self.init_registers(settings['garbage_registers'])
        self.mem = Memory(settings['garbage_memory'])

        self.instruction_count = 0
        self.line_info = ''
        self.debug = Debug()
        self.instr = None

        self.handleArgs(args)
        self.initialize_memory(code)

    def initialize_memory(self, code: List):
        '''Initialize memory by adding instructions the data/text section 
        and then replacing the labels with the correct address'''
        # Function control variables
        has_main = False
        comp = re.compile(r'(lb[u]?|lh[u]?|lw[lr]|lw|la|s[bhw]|sw[lr])')
        for line in code:  # Go through the source code line by line, adding declarations first
            if type(line) is Declaration:
                # Data declaration
                data_type = line.type

                # If a label is specified, add the label to memory
                if line.name:
                    self.mem.addLabel(line.name, self.mem.dataPtr)

                # Align the dataPtr to the proper alignment
                if data_type in const.ALIGNMENT_CONVERSION:
                    self.mem.dataPtr = utility.align_address(self.mem.dataPtr, const.ALIGNMENT_CONVERSION[data_type])

                if 'ascii' in data_type: # ascii/asciiz
                    # There could be multiple strings separated by commas
                    # Add the string to memory and increment address in memory
                    s = line.data[1: -1] # Remove quotation marks
                    s = utility.handle_escapes(s)
                    null_terminate = 'z' in data_type
                    self.mem.addAscii(s, self.mem.dataPtr, null_terminate=null_terminate)
                    self.mem.dataPtr += len(s) + int(null_terminate) # T/F -> 1/0

                elif data_type == 'byte':
                    for data in line.data:
                        self.mem.addByte(data, self.mem.dataPtr)
                        self.mem.dataPtr += 1

                elif data_type == 'word':
                    for data in line.data:
                        self.mem.addWord(data, self.mem.dataPtr)
                        self.mem.dataPtr += 4

                elif data_type == 'half':
                    for data in line.data:
                        self.mem.addHWord(data, self.mem.dataPtr)
                        self.mem.dataPtr += 2

                elif data_type == 'float':
                    for data in line.data:
                        data_f32 = 0.0

                        if abs(data) < const.FLOAT_MIN:
                            data_f32 = float32(0)
                        elif data > const.FLOAT_MAX:
                            data_f32 = float32('inf')
                        elif data < -const.FLOAT_MAX:
                            data_f32 = float32('-inf')
                        else:
                            data_f32 = float32(data)

                        self.mem.addFloat(data_f32, self.mem.dataPtr)
                        self.mem.dataPtr += 4

                elif data_type == 'double':
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
                    self.mem.dataPtr = utility.align_address(self.mem.dataPtr, 2 ** line.data)

            elif type(line) is Label:
                if line.name == 'main':
                    has_main = True
                    self.reg['pc'] = self.mem.textPtr

                self.mem.addLabel(line.name, self.mem.textPtr)

            elif type(line) is PseudoInstr:
                for instr in line.instrs:
                    self.mem.addText(instr)

            else:
                self.mem.addText(line)

        if not has_main:
            raise ex.NoMainLabel('Could not find main label')

        for line in code:  # Replace the labels in load/store instructions by the actual address
            if type(line) is PseudoInstr and comp.match(line.operation):
                addr = self.mem.getLabel(line.label.name)

                if addr:
                    line.instrs[0].imm = (addr >> 16) & 0xFFFF
                    line.instrs[1].imm = addr & 0xFFFF
                else:
                    raise ex.InvalidLabel(f'{line.label.name} is not a valid label. {self.line_info}')

        # Special instruction to terminate execution after every instruction has been executed
        self.mem.addText('TERMINATE_EXECUTION')

    def handleArgs(self, args: List[str]) -> None:
        '''Add program arguments to the run time stack.'''
        if len(args) > 0:
            saveAddr = settings['data_max'] - 3
            temp = settings['initial_$sp'] - 4 - (4 * len(args))
            # args.reverse()
            stack = temp
            self.mem.addWord(len(args), stack)
            stack += 4
            for arg in args:
                saveAddr -= (len(arg) + 1)
                self.mem.addAsciiz(arg, saveAddr)
                self.mem.addWord(saveAddr, stack)
                stack += 4

            self.reg['$sp'] = temp
            self.reg['$a0'] = len(args)
            self.reg['$a1'] = temp + 4

    def init_registers(self, randomize: bool) -> None:
        for r in const.REGS:
            if f'initial_{r}' in settings.keys():
                self.reg[r] = settings[f'initial_{r}']

            elif randomize and r not in const.CONST_REGS:
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
        if reg == '$0' or reg == '$zero':
            raise ex.WritingToZeroRegister(f' {self.line_info}')

        key = reg

        if reg[1:].isnumeric():
            x = int(reg[1:])
            key = list(self.reg.keys())[x]

        self.reg_initialized.add(key)
        self.reg[key] = instrs.overflow_detect(data)

    def get_reg_float(self, reg: str) -> float32:
        return self.f_reg[reg]

    def set_reg_float(self, reg: str, data: float32) -> None:
        self.f_reg[reg] = data

    def get_reg_double(self, reg: str) -> float:
        reg_number = int(reg[2:])

        if reg_number & 1:
            raise ex.InvalidRegister('Double-precision instructions can only be done'
                                     ' with even numbered registers')

        next_reg = f'$f{reg_number + 1}'

        lower_bytes = struct.pack('>f', self.f_reg[reg])
        upper_bytes = struct.pack('>f', self.f_reg[next_reg])
        double_bytes = upper_bytes + lower_bytes

        return struct.unpack('>d', double_bytes)[0]

    def set_reg_double(self, reg: str, data: float) -> None:
        reg_number = int(reg[2:])

        if reg_number & 1:
            raise ex.InvalidRegister('Double-precision instructions can only be done'
                                     ' with even numbered registers')

        next_reg = f'$f{reg_number + 1}'

        double_bytes = struct.pack('>d', data)
        upper = struct.unpack('>f', double_bytes[:4])[0]
        lower = struct.unpack('>f', double_bytes[4:])[0]

        self.f_reg[reg] = lower
        self.f_reg[next_reg] = upper

    def get_reg_word(self, reg: str) -> int:
        bytes = struct.pack('>f', self.f_reg[reg])
        return struct.unpack('>i', bytes)[0]

    def set_reg_word(self, reg: str, data: int) -> None:
        bytes = struct.pack('>i', data)
        self.f_reg[reg] = struct.unpack('>f', bytes)[0]

    def execute_instr(self, instr) -> None:
        def is_float_single(op: str) -> bool:
            return op[-2:] == '.s'

        def is_float_double(op: str) -> bool:
            return op[-2:] == '.d'

        def is_conversion_to_int(op: str) -> bool:
            return op[-4:-2] == '.w'

        def interpret_as_float(x: int) -> float32:
            x_bytes = struct.pack('>i', x)
            return struct.unpack('>f', x_bytes)[0]

        def interpret_as_int(x: float32) -> int:
            x_bytes = struct.pack('>f', x)
            return struct.unpack('>i', x_bytes)[0]

        # Instruction with 3 registers
        if type(instr) is RType and hasattr(instr, "rd"):
            op = instr.operation
            rd = instr.rd

            if is_float_single(op):
                rs = self.get_reg_float(instr.rs)
                rt = self.get_reg_float(instr.rt)
                result = instrs.table[op[:-2] + '_f'](rs, rt)
                self.set_reg_float(rd, result)

            elif is_float_double(op):
                rs = self.get_reg_double(instr.rs)
                rt = self.get_reg_double(instr.rt)
                result = instrs.table[op[:-2] + '_f'](rs, rt)
                self.set_reg_double(rd, result)

            else:
                rs = self.get_register(instr.rs)
                rt = self.get_register(instr.rt)
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
        elif type(instr) is RType:
            op = instr.operation
            r1 = instr.rs
            r2 = instr.rt

            if is_conversion_to_int(op):
                if is_float_single(op):
                    result = instrs.table[op[:-4]](self.get_reg_float(r2))
                else:
                    result = instrs.table[op[:-4]](self.get_reg_double(r2))

                self.set_reg_float(r1, interpret_as_float(result))

            elif is_float_single(op):
                result = instrs.table[op[:-2]](self.get_reg_float(r2))
                self.set_reg_float(r1, result)

            elif is_float_double(op):
                result = instrs.table[op[:-2]](self.get_reg_double(r2))
                self.set_reg_double(r1, result)

            elif op in {'mult', 'multu', 'madd', 'maddu', 'msub', 'msubu'}:
                signed = op[-1] != 'u'
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
                signed = op[-1] != 'u'
                result, remainder = instrs.div(self.get_register(r1), self.get_register(r2), signed=signed)

                # Set lo to quotient, and hi to remainder
                self.set_register('lo', result)
                self.set_register('hi', remainder)

            else:
                result = instrs.table[op](self.get_register(r2))
                self.set_register(r1, result)

        # j type instructions (Label)
        elif type(instr) is JType and type(instr.target) is Label:
            instrs.table[instr.operation](self.reg, self.mem, instr.target.name)

        # j type instructions (Return)
        elif type(instr) is JType:
            instrs.table[instr.operation](self.reg, instr.target)

        # i-type isntructions
        elif type(instr) is IType:
            result = instrs.table[instr.operation](self.get_register(instr.rs), instr.imm)
            self.set_register(instr.rt, result)

        # Load immediate
        elif type(instr) is LoadImm:
            if instr.operation == 'lui':
                upper = instrs.lui(instr.imm)
                self.set_register(instr.rt, upper)

        # Load or store from memory
        elif type(instr) is LoadMem:
            op = instr.operation
            reg = instr.rt
            addr = self.get_register(instr.rs) + instr.imm

            if op in {'lwr', 'lwl'}:
                result = instrs.table[op](addr, self.mem, self.get_register(reg))
                self.set_register(reg, result)

            elif op in {'lw', 'lh', 'lb', 'lhu', 'lbu'}:
                result = instrs.table[op](addr, self.mem)
                self.set_register(reg, result)

            elif op == 'l.s':
                result = self.mem.getFloat(addr)
                self.set_reg_float(reg, result)

            elif op == 'l.d':
                result = self.mem.getDouble(addr)
                self.set_reg_double(reg, result)

            elif op == 's.s':
                self.mem.addFloat(self.get_reg_float(reg), addr)

            elif op == 's.d':
                self.mem.addDouble(self.get_reg_double(reg), addr)

            else:  # Other store instructions
                instrs.table[op](addr, self.mem, self.get_register(reg))
            if settings['gui']:
                self.mem_access.emit()

        # Mfhi, mflo, mthi, mtlo
        elif type(instr) is Move:
            self.set_register(instr.rd, self.get_register(instr.rs))

        # Floating point move instructions
        elif type(instr) is MoveFloat:
            op = instr.operation
            rs = instr.rs
            rt = instr.rt

            if op == 'mfc1':
                rt_float = self.get_reg_float(rt)
                rt_int = interpret_as_int(rt_float)
                self.set_register(rs, rt_int)

            elif op == 'mtc1':
                rs_int = self.get_register(rs)
                rs_float = interpret_as_float(rs_int)
                self.set_reg_float(rt, rs_float)

            elif op[:4] in ['movn', 'movz']:
                rd_data = self.get_register(instr.rd)

                if (op[3] == 'z' and rd_data == 0) or (op[3] == 'n' and rd_data != 0):
                    if is_float_single(op):
                        rt_data = self.get_reg_float(rt)
                        self.set_reg_float(rs, rt_data)
                    else:
                        rt_data = self.get_reg_double(rt)
                        self.set_reg_double(rs, rt_data)

        elif type(instr) is MoveCond:
            op = instr.operation
            flag = self.condition_flags[instr.flag]

            rs = instr.rs
            rt = instr.rt

            if (op[3] == 't' and flag) or (op[3] == 'f' and not flag):
                if is_float_single(op):
                    rt_data = self.get_reg_float(rt)
                    self.set_reg_float(rs, rt_data)

                elif is_float_double(op):
                    rt_data = self.get_reg_double(rt)
                    self.set_reg_double(rs, rt_data)

                else:
                    rt_data = self.get_register(rt)
                    self.set_register(rs, rt_data)

        # syscall
        elif type(instr) is Syscall:
            code = self.get_register('$v0')

            if code in syscalls and code in settings['enabled_syscalls']:
                syscalls[code](self)
            else:
                raise ex.InvalidSyscall('Not a valid syscall code:')

        # Compare float
        elif type(instr) is Compare:
            op = instr.operation

            if is_float_single(op):
                rs = self.get_reg_float(instr.rs)
                rt = self.get_reg_float(instr.rt)
            else:
                rs = self.get_reg_double(instr.rs)
                rt = self.get_reg_double(instr.rt)

            compare_op = op[2:4]
            flag = instr.imm

            if not 0 <= flag <= 7:
                raise ex.InvalidArgument('Condition flag number must be between 0 - 7')

            if compare_op == 'eq':
                self.condition_flags[flag] = rs == rt
            elif compare_op == 'le':
                self.condition_flags[flag] = rs <= rt
            elif compare_op == 'lt':
                self.condition_flags[flag] = rs < rt

        # Convert float
        elif type(instr) is Convert:
            format_from = instr.format_from
            format_to = instr.format_to

            if format_from == 'w':
                data = self.get_reg_word(instr.rs)
            elif format_from == 's':
                data = self.get_reg_float(instr.rs)
            else:
                data = self.get_reg_double(instr.rs)

            if format_to == 'w':
                self.set_reg_word(instr.rt, int(data))
            elif format_to == 's':
                self.set_reg_float(instr.rt, float32(data))
            else:
                self.set_reg_double(instr.rt, float(data))

        # Branches
        elif type(instr) is Branch:
            op = instr.operation
            rs = self.get_register(instr.rs)
            rt = self.get_register(instr.rt)

            if 'z' in op:
                result = instrs.table[op](rs)
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

        # Branches (float)
        elif type(instr) is BranchFloat:
            op = instr.operation
            flag = instr.flag

            if (self.condition_flags[flag] and op == 'bc1t') or (not self.condition_flags[flag] and op == 'bc1f'):
                label = instr.label.name
                addr = self.mem.getLabel(label)

                if addr is None:
                    raise ex.InvalidLabel(f'{label} is not a valid label.')

                self.set_register('pc', addr)

        elif type(instr) is Nop:
            pass

        elif type(instr) is Breakpoint:
            raise ex.BreakpointException(f'code = {instr.code}')

    def interpret(self) -> None:
        first = True
        if settings['gui']:
            self.start.emit()
        try:
            while True:
                # Get the next instruction and increment pc
                pc = self.reg['pc']

                if str(pc) not in self.mem.text:
                    raise ex.MemoryOutOfBounds(f'{pc} is not a valid address')

                if self.instruction_count > settings['max_instructions']:
                    raise ex.InstrCountExceed(f'Exceeded maximum instruction count: {settings["max_instructions"]}')

                self.instr = self.mem.text[str(pc)]
                if self.instr == 'TERMINATE_EXECUTION':
                    if settings['debug']:
                        print()
                        self.debug.listen(self)

                    if settings['gui']:
                        self.end.emit(False)

                    break

                self.reg['pc'] += 4
                self.instruction_count += 1

                if settings['gui']:
                    self.step.emit(pc)


                try:
                    self.line_info = f' ({self.instr.filetag.file_name}, {self.instr.filetag.line_no})'
                except AttributeError:
                    self.line_info = ''

                if self.debug.debug(self.instr):
                    if not self.debug.continueFlag:
                        self.pause_lock.clear()
                    if settings['gui']:
                        self.debug.listen(self)
                    elif not settings['gui'] and settings['debug']:
                        self.debug.listen(self)
                    else:
                        first = False

                elif settings['gui'] and type(self.instr) is Syscall and (self.reg['$v0'] == 10 or self.reg['$v0'] == 17):
                    if settings['disp_instr_count']:
                        self.out(f'\nInstruction count: {self.instruction_count}')
                    self.end.emit(False)
                    break

                if settings['gui']:
                    self.debug.push(self)

                self.execute_instr(self.instr)

        except Exception as e:
            if hasattr(e, 'message'):
                e.message += ' ' + self.line_info
                if settings['gui']:
                    self.end.emit(False)
            raise e

    def dump(self) -> None:
        '''Dump the contents in registers and memory.'''
        print('Registers:')

        for name, val in self.reg.items():
            print(f'{name}: {val}')

        print('Memory:')
        self.mem.dump()

    def out(self, s: str, end='') -> None:
        '''Prints to terminal or the console in the GUI'''
        if settings['gui']:
            self.console_out.emit(f'{s}{end}')
        else:
            print(s, end=end)

    def get_input(self, input_type: str) -> str:
        '''Prompts the user for an input value.'''
        if settings['gui']:
            self.input_lock.clear()
            self.user_input.emit(const.USER_INPUT_TYPE.index(input_type))
            self.input_lock.wait()
            return self.input_str
        else:
            return input()

    def set_input(self, string: str) -> None:
        '''Set input string to the provided string'''
        self.lock_input.acquire()
        if not self.input_lock.isSet():
            self.input_str = string
            self.input_lock.set()
        self.lock_input.release()
