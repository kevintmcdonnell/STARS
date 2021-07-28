from typing import List, Union

from interpreter import utility

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


class Label:
    def __init__(self, name: str):
        self.name = name

class Declaration(Label):
    def __init__(self, name: str, type: str, data: Union[int, List[int], str, List[str]]):
        super().__init__(name)
        self.type = type
        self.data = data

class FileTag:
    def __init__(self, file_name: str, line_no: int):
        self.file_name = file_name
        self.line_no = line_no

class Instruction:
    def __init__(self, op):
        self.operation = op

    def __str__(self):
        return f"{self.operation}"

class Breakpoint(Instruction):
    def __init__(self, code: int = 0):
        super().__init__("breakpoint")
        self.code = code

class Nop(Instruction):
    def __init__(self):
        super().__init__("nop")

class Syscall(Instruction):
    def __init__(self):
        super().__init__("syscall")

# RType Instructions
class RType(Instruction):
    # Two or Three registers
    def __init__(self, op: str, regs: List[str]):
        super().__init__(op)
        if len(regs) == 2:
            self.rs, self.rt = regs
        else:
            self.rd, self.rs, self.rt = regs

    def __str__(self) -> str:
        return f"{super().__str__()} {f'{self.rd}, ' if hasattr(self, 'rd') else ''}{self.rs}, {self.rt}"

class Move:
    def __init__(self, op: str, reg: str):
        self.operation = op
        self.reg = reg

    def basic_instr(self) -> str:
        return f'{self.operation} {self.reg}'

class MoveFloat:
    def __init__(self, op: str, rs: str, rt: str, rd: str = ''):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.rd = rd

    def basic_instr(self) -> str:
        if len(self.rd) > 0:
            return f'{self.operation} {self.rs} {self.rt}'
        else:
            return f'{self.operation} {self.rs} {self.rt} {self.rd}'

class MoveCond:
    def __init__(self, op: str, rs: str, rt: str, flag: int):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.flag = flag

    def basic_instr(self) -> str:
        return f'{self.operation} {self.rs} {self.rt} {self.flag}'

# IType Instructions
class IType:
    # Two registers and an immediate
    def __init__(self, op: str, regs: List[str], imm: int):
        self.operation = op
        self.regs = regs
        self.imm = imm

    def basic_instr(self) -> str:
        if self.operation in ['or', 'ori', 'and', 'andi', 'xor', 'xori']:
            imm = utility.format_hex(self.imm)
        else:
            imm = self.imm

        return f'{self.operation} {self.regs[0]} {self.regs[1]} {imm}'

class Compare:
    def __init__(self, op: str, rs: str, rt: str, flag: int):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.flag = flag

    def basic_instr(self) -> str:
        return f'{self.operation} {self.rs} {self.rt} {self.flag}'

class Convert:
    def __init__(self, format_from: str, format_to: str, rs: str, rt: str):
        self.format_from = format_from
        self.format_to = format_to
        self.rs = rs
        self.rt = rt

    def basic_instr(self) -> str:
        return f'cvt.{self.format_from}.{self.format_to} {self.rs} {self.rt}'

class Branch:
    def __init__(self, op: str, rs: str, rt: str, label: Label):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.label = label

    def basic_instr(self) -> str:
        return f'{self.operation} {self.rs} {self.rt} {self.label.name}'

class BranchFloat:
    def __init__(self, op: str, label: Label, flag: int):
        self.operation = op
        self.label = label
        self.flag = flag

    def basic_instr(self) -> str:
        return f'{self.operation} {self.flag} {self.label.name}'

class LoadImm:
    def __init__(self, op: str, reg: str, imm: int):
        self.operation = op
        self.reg = reg
        self.imm = imm

    def basic_instr(self) -> str:
        imm_hex = utility.format_hex(self.imm)
        return f'{self.operation} {self.reg}, {imm_hex}'

class LoadMem:
    def __init__(self, op: str, reg: str, addr: str, imm: int):
        self.operation = op
        self.reg = reg
        self.addr = addr
        self.imm = imm

    def basic_instr(self) -> str:
        imm_hex = utility.format_hex(self.imm)
        return f'{self.operation} {self.reg}, {imm_hex}({self.addr})'

# JType Instructions
class JType:
    # A label or a register as a target
    def __init__(self, op: str, target: Union[str, Label]):
        self.operation = op
        self.target = target

    def basic_instr(self) -> str:
        if type(self.target) is Label:
            return f'{self.operation} {self.target.name}'
        return f'{self.operation} {self.target}'

class PseudoInstr:
    def __init__(self, op: str, instrs: List):
        self.operation = op
        self.instrs = instrs

    def original(self) -> str:
        return self.operation

# Change classes for putting instructions on the stack
class Change:
    def __init__(self, pc: int):
        self.pc = pc

class FlagChange:
    def __init__(self, flag: int, value: bool, pc: int):
        self.flag = flag
        self.value = value
        self.pc = pc

class MChange:
    def __init__(self, hi: int, lo: int, pc: int):
        self.pc = pc
        self.hi = hi
        self.lo = lo

# type can be 'w', 'h', or 'b' to indicate word, halfword, and byte respectively
class MemChange:
    def __init__(self, addr: int, val: int, pc: int, type: str):
        self.addr = addr
        self.val = val
        self.pc = pc
        self.type = type

class RegChange:
    def __init__(self, reg: str, val: int, pc: int, is_double: bool = False):
        self.reg = reg
        self.val = val
        self.pc = pc
        self.is_double = is_double