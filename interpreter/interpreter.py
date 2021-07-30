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
    step = Signal(int) # use to signal program counter increment
    end = Signal(bool) # use to signal program termination
    console_out = Signal(str) # use by out for printing to console
    user_input = Signal(int) # use by input/set_input for user input syscalls

    def __init__(self, code: List[Instruction], args: List[str]) -> None:
        if settings['gui']:
            super().__init__()
        # For user input syscalls
        self.pause_lock = Event()
        self.input_lock = Event()
        self.lock_input = Lock()
        self.input_str = None
        # Registers
        self.reg_initialized = set()
        self.reg = OrderedDict()
        self.f_reg = dict()
        self.condition_flags = [False] * 8
        self.init_registers(settings['garbage_registers'])
        # Memory and program arguments
        self.mem = Memory(settings['garbage_memory'])
        self.handleArgs(args)
        self.initialize_memory(code)
        # For error messages
        self.line_info = ''

    def initialize_memory(self, code: List[Instruction]) -> None:
        '''Initialize memory by adding instructions the data/text section 
        and then replacing the labels with the correct address'''
        # Function control variables
        has_main = False
        INSERT_MEMORY_FUNCTIONS = {
            'byte': self.mem.addByte,
            'half': self.mem.addHWord,
            'word': self.mem.addWord,
            'float': self.mem.addFloat,
            'double': self.mem.addDouble,
            'space': self.mem.addByte
        }
        comp = re.compile(r'(lb[u]?|lh[u]?|lw[lr]|lw|la|s[bhw]|sw[lr])')
        for line in code:  # Go through the source code line by line, adding declarations first
            if type(line) is Declaration:
                # Data declaration
                data_type, data = line.type, line.data

                # Special formatting for data
                if data_type == 'float':
                    data = [utility.create_float32(d) for d in data]
                elif data_type == 'space':
                    data = [random.randint(0, 0xFF) if settings['garbage_memory'] else 0
                            for i in range(data)]
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
                
                elif data_type in INSERT_MEMORY_FUNCTIONS:
                    for info in data:
                        INSERT_MEMORY_FUNCTIONS[data_type](info, self.mem.dataPtr)
                        self.mem.dataPtr += const.ALIGNMENT_CONVERSION.get(data_type, 1)

                elif data_type == 'align':
                    if not 0 <= line.data <= 3:
                        raise ex.InvalidImmediate(f'Value({line.data}) for .align is invalid')
                    self.mem.dataPtr = utility.align_address(self.mem.dataPtr, 2 ** line.data)

            elif type(line) is Label:
                if line.name == 'main':
                    has_main, self.reg['pc'] = True, self.mem.textPtr
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
        key = reg if reg != '$0' else '$zero'
        if settings['warnings'] and key[1] in {'s', 't', 'a', 'v'} and key not in {'$at', '$sp'} and key not in self.reg_initialized:
            print(f'Reading from uninitialized register {key}!', file=sys.stderr)

        return instrs.overflow_detect(self.reg[key])

    def set_register(self, reg: str, data: int) -> None:
        if reg == '$0' or reg == '$zero':
            raise ex.WritingToZeroRegister(f' {self.line_info}')
        self.reg_initialized.add(reg)
        self.reg[reg] = instrs.overflow_detect(data)

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
        double_bytes = struct.pack('>f', self.f_reg[next_reg]) + struct.pack('>f', self.f_reg[reg])

        return struct.unpack('>d', double_bytes)[0]

    def set_reg_double(self, reg: str, data: float) -> None:
        reg_number = int(reg[2:])
        if reg_number & 1:
            raise ex.InvalidRegister('Double-precision instructions can only be done'
                                     ' with even numbered registers')
        next_reg = f'$f{reg_number + 1}'
        double_bytes = struct.pack('>d', data)
        self.f_reg[reg] = struct.unpack('>f', double_bytes[4:])[0]
        self.f_reg[next_reg] = struct.unpack('>f', double_bytes[:4])[0]

    def get_reg_word(self, reg: str) -> int:
        bytes = struct.pack('>f', self.f_reg[reg])
        return struct.unpack('>i', bytes)[0]

    def set_reg_word(self, reg: str, data: int) -> None:
        bytes = struct.pack('>i', data)
        self.f_reg[reg] = struct.unpack('>f', bytes)[0]

    def execute_instr(self, instr) -> None:
        '''Execute the given MIPS instruction object.'''
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
        # Function control variables
        op = instr.operation
        # Instruction with 3 registers
        if type(instr) is RType and hasattr(instr, "rd"):
            if is_float_single(op):
                result = instrs.table[op[:-2] + '_f'](self.get_reg_float(instr.rs), self.get_reg_float(instr.rt))
                self.set_reg_float(instr.rd, result)
            elif is_float_double(op):
                result = instrs.table[op[:-2] + '_f'](self.get_reg_double(instr.rs), self.get_reg_double(instr.rt))
                self.set_reg_double(instr.rd, result)
            else:
                result = instrs.table[op](self.get_register(instr.rs), self.get_register(instr.rt))
                if (op == 'movz' and rt == 0) or (op == 'movn' and rt != 0):
                    self.set_register(instr.rd, result)
                else:
                    self.set_register(instr.rd, result)

        # Instruction with 2 registers
        elif type(instr) is RType: # Note: rs and rt are flipped for certain conditionals
            if is_conversion_to_int(op):
                if is_float_single(op):
                    result = instrs.table[op[:-4]](self.get_reg_float(instr.rt))
                else:
                    result = instrs.table[op[:-4]](self.get_reg_double(instr.rt))
                self.set_reg_float(instr.rs, interpret_as_float(result))

            elif is_float_single(op):
                result = instrs.table[op[:-2]](self.get_reg_float(instr.rt))
                self.set_reg_float(instr.rs, result)

            elif is_float_double(op):
                result = instrs.table[op[:-2]](self.get_reg_double(instr.rt))
                self.set_reg_double(instr.rs, result)

            elif op in {'mult', 'multu', 'madd', 'maddu', 'msub', 'msubu'}:
                signed = op[-1] != 'u'
                low, high = instrs.mul(self.get_register(instr.rs), self.get_register(instr.rt), 
                        thirty_two_bits=False, signed=signed)  # A 64 bit integer
                if 'mult' not in op:
                    lo_reg, hi_reg = self.get_register('lo'), self.get_register('hi')
                    if 'add' in op:
                        low, high = instrs.addu(lo_reg, low), instrs.addu(hi_reg, high)
                    else:
                        low, high = instrs.subu(lo_reg, low), instrs.subu(hi_reg, high)
                # Set lo to lower 32 bits, and hi to upper 32 bits
                self.set_register('lo', low)
                self.set_register('hi', high)

            elif op == 'div' or op == 'divu':
                signed = op[-1] != 'u'
                result, remainder = instrs.div(self.get_register(instr.rs),
                                    self.get_register(instr.rt), signed=signed)
                # Set lo to quotient, and hi to remainder
                self.set_register('lo', result)
                self.set_register('hi', remainder)
            else:
                result = instrs.table[op](self.get_register(instr.rt))
                self.set_register(instr.rs, result)

        # j type instructions (Label)
        elif type(instr) is JType and type(instr.target) is Label:
            instrs.table[op](self.reg, self.mem, instr.target.name)

        # j type instructions (Return)
        elif type(instr) is JType:
            instrs.table[op](self.reg, instr.target)

        # i-type isntructions
        elif type(instr) is IType:
            result = instrs.table[op](self.get_register(instr.rs), instr.imm)
            self.set_register(instr.rt, result)

        # Load immediate
        elif type(instr) is LoadImm: # always 'lui'
            self.set_register(instr.rt, instrs.lui(instr.imm))

        # Load or store from memory
        elif type(instr) is LoadMem:
            addr = self.get_register(instr.rs) + instr.imm
            if op in {'lwr', 'lwl'}:
                result = instrs.table[op](addr, self.mem, self.get_register(instr.rt))
                self.set_register(instr.rt, result)
            elif op in {'lw', 'lh', 'lb', 'lhu', 'lbu'}:
                self.set_register(instr.rt, instrs.table[op](addr, self.mem))
            elif op == 'l.s':
                self.set_reg_float(instr.rt, self.mem.getFloat(addr))
            elif op == 'l.d':
                self.set_reg_double(instr.rt, self.mem.getDouble(addr))
            elif op == 's.s':
                self.mem.addFloat(self.get_reg_float(instr.rt), addr)
            elif op == 's.d':
                self.mem.addDouble(self.get_reg_double(instr.rt), addr)
            else:  # Other store instructions
                instrs.table[op](addr, self.mem, self.get_register(instr.rt))

        # Mfhi, mflo, mthi, mtlo
        elif type(instr) is Move:
            self.set_register(instr.rd, self.get_register(instr.rs))

        # Floating point move instructions
        elif type(instr) is MoveFloat:
            if op == 'mfc1': # rs and rt are intentionally swapped here
                self.set_register(instr.rs, interpret_as_int(self.get_reg_float(instr.rt)))
            elif op == 'mtc1': 
                self.set_reg_float(instr.rt, interpret_as_float(self.get_register(instr.rs)))

            elif op[:4] in ['movn', 'movz']:
                conditional = self.get_register(instr.rt)
                if (op[3] == 'z' and conditional == 0) or (op[3] == 'n' and conditional != 0):
                    if is_float_single(op):
                        self.set_reg_float(instr.rd, self.get_reg_float(instr.rs))
                    else:
                        self.set_reg_double(instr.rd, self.get_reg_double(instr.rs))

        elif type(instr) is MoveCond:
            flag = self.condition_flags[instr.imm]
            if not 0 <= flag <= 7:
                raise ex.InvalidArgument('Condition flag number must be between 0 - 7')
            if (op[3] == 't' and flag) or (op[3] == 'f' and not flag):
                if is_float_single(op):
                    self.set_reg_float(instr.rt, self.get_reg_float(instr.rs))
                elif is_float_double(op):
                    self.set_reg_double(instr.rt, self.get_reg_double(instr.rs))
                else:
                    self.set_register(instr.rt, self.get_register(instr.rs))

        # syscall
        elif type(instr) is Syscall:
            code = self.get_register('$v0')
            if code in syscalls and code in settings['enabled_syscalls']:
                syscalls[code](self)
            else:
                raise ex.InvalidSyscall('Not a valid syscall code:')

        # Compare float
        elif type(instr) is Compare:
            if is_float_single(op):
                rs, rt = self.get_reg_float(instr.rs), self.get_reg_float(instr.rt)
            else:
                rs, rt = self.get_reg_double(instr.rs), self.get_reg_double(instr.rt)
            compare_op, flag = op[2:4], instr.imm

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
            if instr.format_from == 'w':
                data = self.get_reg_word(instr.rs)
            elif instr.format_from == 's':
                data = self.get_reg_float(instr.rs)
            else:
                data = self.get_reg_double(instr.rs)

            if instr.format_to == 'w':
                self.set_reg_word(instr.rt, int(data))
            elif instr.format_to == 's':
                self.set_reg_float(instr.rt, float32(data))
            else:
                self.set_reg_double(instr.rt, float(data))

        # Branches
        elif type(instr) is Branch:
            if 'z' in op:
                result = instrs.table[op](self.get_register(instr.rs))
            else:
                result = instrs.table[op](self.get_register(instr.rs), self.get_register(instr.rt))
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
            flag = instr.flag
            if not 0 <= flag <= 7:
                raise ex.InvalidArgument('Condition flag number must be between 0 - 7')
            if (self.condition_flags[flag] and op == 'bc1t') or (not self.condition_flags[flag] and op == 'bc1f'):
                label = instr.label.name
                addr = self.mem.getLabel(label)
                if addr is None:
                    raise ex.InvalidLabel(f'{label} is not a valid label.')
                self.set_register('pc', addr)

        elif type(instr) is Breakpoint:
            raise ex.BreakpointException(f'code = {instr.code}')

    def interpret(self) -> None:
        '''Goes through the text segment and executes each instruction.'''
        first = True
        debug = Debug()
        instruction_count = 0
        instr = None
        try:
            while True: # Get the next instruction and increment pc
                pc = self.reg['pc']
                if str(pc) not in self.mem.text:
                    raise ex.MemoryOutOfBounds(f'{pc} is not a valid address')
                if instruction_count > settings['max_instructions']:
                    raise ex.InstrCountExceed(f'Exceeded maximum instruction count: {settings["max_instructions"]}')

                instr = self.mem.text[str(pc)]
                if instr == 'TERMINATE_EXECUTION':
                    if settings['debug']:
                        print()
                        debug.listen(self)
                    if settings['gui']:
                        self.end.emit(False)
                    break
                self.reg['pc'] += 4
                instruction_count += 1
                self.line_info = str(instr.filetag)
                if settings['gui']:
                    self.step.emit(pc)

                if debug.debug(instr):
                    if not debug.continueFlag:
                        self.pause_lock.clear()
                    if settings['gui']:
                        debug.listen(self)
                    elif not settings['gui'] and settings['debug']:
                        debug.listen(self)
                    else:
                        first = False
                elif settings['gui'] and type(instr) is Syscall and self.reg['$v0'] in [10, 17]:
                    if settings['disp_instr_count']:
                        self.out(f'\nInstruction count: {instruction_count}')
                    self.end.emit(False)
                    break

                if settings['gui']:
                    debug.push(self)
                self.execute_instr(instr) # execute
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
