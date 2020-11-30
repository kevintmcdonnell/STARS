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


class RType:
    # Two or Three registers
    def __init__(self, op: str, regs: List[str]):
        self.operation = op
        self.regs = regs

    def basic_instr(self) -> str:
        if len(self.regs) == 2:
            return f'{self.operation} {self.regs[0]}, {self.regs[1]}'

        else:
            return f'{self.operation} {self.regs[0]}, {self.regs[1]}, {self.regs[2]}'


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

        return f'{self.operation} {self.regs[0]}, {self.regs[1]}, {imm}'


class JType:
    # A label or a register as a target
    def __init__(self, op: str, target: Union[str, Label]):
        self.operation = op
        self.target = target


class Convert:
    def __init__(self, format_from: str, format_to: str, rs: str, rt: str):
        self.format_from = format_from
        self.format_to = format_to
        self.rs = rs
        self.rt = rt


class Compare:
    def __init__(self, op: str, rs: str, rt: str, flag: int):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.flag = flag


class Branch:
    def __init__(self, op: str, rs: str, rt: str, label: Label):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.label = label

    def basic_instr(self) -> str:
        return f'{self.operation} {self.rs}, {self.rt}, {self.label.name}'


class BranchFloat:
    def __init__(self, op: str, label: Label, flag: int):
        self.operation = op
        self.label = label
        self.flag = flag


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


class Move:
    def __init__(self, op: str, reg: str):
        self.operation = op
        self.reg = reg


class MoveFloat:
    def __init__(self, op: str, rs: str, rt: str, rd: str = ''):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.rd = rd


class MoveCond:
    def __init__(self, op: str, rs: str, rt: str, flag: int):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.flag = flag


class Nop:
    def __init__(self):
        pass


class Breakpoint:
    def __init__(self, code: int = 0):
        self.code = code


class Declaration:
    def __init__(self, label: Union[Label, None], type: str, data: Union[int, List[int], str, List[str]]):
        self.label = label
        self.type = type
        self.data = data


class PseudoInstr:
    def __init__(self, op: str, instrs: List):
        self.operation = op
        self.instrs = instrs


class FileTag:
    def __init__(self, file_name: str, line_no: int):
        self.file_name = file_name
        self.line_no = line_no


class Syscall:
    def __init__(self):
        pass


class RegChange:
    def __init__(self, reg: str, val: int, pc: int):
        self.reg = reg
        self.val = val
        self.pc = pc


# type can be 'w', 'h', or 'b' to indicate word, halfword, and byte respectively
class MemChange:
    def __init__(self, addr: int, val: int, pc: int, type: str):
        self.addr = addr
        self.val = val
        self.pc = pc
        self.type = type


class Change:
    def __init__(self, pc: int):
        self.pc = pc


class MChange:
    def __init__(self, hi: int, lo: int, pc: int):
        self.pc = pc
        self.hi = hi
        self.lo = lo
