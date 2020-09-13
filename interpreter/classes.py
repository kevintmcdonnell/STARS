from typing import List, Union
from interpreter import utility


class Label:
    def __init__(self, name: str):
        self.name = name


class RType:
    # Two or Three registers
    def __init__(self, operation: str, regs: List[str]):
        self.operation = operation
        self.regs = regs

    def basic_instr(self) -> str:
        if len(self.regs) == 2:
            return f'{self.operation} {self.regs[0]}, {self.regs[1]}'

        else:
            return f'{self.operation} {self.regs[0]}, {self.regs[1]}, {self.regs[2]}'


class IType:
    # Two registers and an immediate
    def __init__(self, operation: str, regs: List[str], imm: int):
        self.operation = operation
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
    def __init__(self, operation: str, target: Union[str, Label]):
        self.operation = operation
        self.target = target


class Branch:
    def __init__(self, op: str, rs: str, rt: str, label: Label):
        self.operation = op
        self.rs = rs
        self.rt = rt
        self.label = label

    def basic_instr(self) -> str:
        return f'{self.operation} {self.rs}, {self.rt}, {self.label.name}'


class LoadImm:
    def __init__(self, op: str, reg: str, imm: int):
        self.operation = op
        self.reg = reg
        self.imm = imm

    def basic_instr(self) -> str:
        imm_hex = utility.format_hex(self.imm)
        return f'{self.operation} {self.reg}, {imm_hex}'


class LoadMem:
    def __init__(self, operation: str, reg: str, addr: str, imm: int, label: Label = None):
        self.operation = operation
        self.reg = reg
        self.addr = addr
        self.imm = imm
        self.label = label

    def basic_instr(self) -> str:
        imm_hex = utility.format_hex(self.imm)
        return f'{self.operation} {self.reg}, {imm_hex}({self.addr})'


class Move:
    def __init__(self, operation: str, reg: str):
        self.operation = operation
        self.reg = reg


class Nop:
    def __init__(self):
        pass


class Breakpoint:
    def __init__(self, code: int = 0):
        self.code = code


class Declaration:
    def __init__(self, label: Label, type: str, data: Union[int, List[int], str, List[str]]):
        self.label = label
        self.type = type
        self.data = data


class PseudoInstr:
    def __init__(self, operation: str, instrs: List):
        self.operation = operation
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