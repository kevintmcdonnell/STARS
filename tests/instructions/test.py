import unittest

from interpreter import instructions
from interpreter.exceptions import *
from interpreter.instructions import overflow_detect
from interpreter.interpreter import *

'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

class TestSBUMips(unittest.TestCase):
    # Arithmetic operations
    # Add
    # General case
    def test_add_1(self):
        ret = instructions.add(2113, 420)
        self.assertEqual(2113 + 420, ret)

    # Positive overflow
    def test_add_2(self):
        self.assertRaises(ArithmeticOverflow, instructions.add, 0x7FF284AB, 0x6FA3B583)

    # Negative overflow
    def test_add_3(self):
        self.assertRaises(ArithmeticOverflow, instructions.add, -0x7FF284AB, -0x6FA3B583)

    # Addu
    # Positive Overflow
    def test_addu_1(self):
        ret = instructions.addu(0x7FFFFFFF, 0x7FFFFFFF)
        ret = instructions.overflow_detect(ret)
        self.assertEqual(-2, ret)

    # Negative Overflow
    def test_addu_2(self):
        ret = instructions.addu(0x80000000, 0x80000000)
        ret = instructions.overflow_detect(ret)
        self.assertEqual(0, ret)

    # Addi
    # General case
    def test_addi_1(self):
        ret = instructions.addi(30000, 420)
        self.assertEqual(30420, ret)

    # Invalid immediate value
    def test_addi_2(self):
        self.assertRaises(InvalidImmediate, instructions.addi, 30000, 60000)

    # Mul
    # General case: Positive * positive
    def test_mul_1(self):
        ret = instructions.mul(200, 300)
        self.assertEqual(60000, ret)

    # General case: Positive * negative
    def test_mul_2(self):
        ret = instructions.mul(200, -300)
        self.assertEqual(-60000, ret)

    # General case: Negative * negative
    def test_mul_3(self):
        ret = instructions.mul(-200, -300)
        self.assertEqual(60000, ret)

    # Edge case: more than 32 bits
    def test_mul_4(self):
        ret = instructions.mul(0x7F000FFF, 0x7F000FFF)
        ret = overflow_detect(ret)

        self.assertEqual(50323457, ret)

    # Mult
    # General case: positive
    def test_mult_1(self):
        ret = instructions.mul(0x7F000FFF, 0x7F000FFF, thirty_two_bits=False)
        self.assertEqual((50323457, 1057034207), ret)

    # General case: negative
    def test_mult_2(self):
        low, high = instructions.mul(0x7F000FFF, -200, thirty_two_bits=False)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((-940343096, -100), (low, high))

    # Multu
    # General case
    def test_multu(self):
        low, high = instructions.mul(300, -200, thirty_two_bits=False, signed=False)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((-60000, 299), (low, high))

    # Div
    # General case: pos / pos
    def test_div_1(self):
        low, high = instructions.div(30000, 59)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((508, 28), (low, high))

    # General case: pos / neg
    def test_div_2(self):
        low, high = instructions.div(30000, -59)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((-508, 28), (low, high))

    # General case: neg / pos
    def test_div_3(self):
        low, high = instructions.div(-30000, 59)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((-508, -28), (low, high))

    # General case: pos / neg
    def test_div_4(self):
        low, high = instructions.div(-30000, -59)
        low = overflow_detect(low)
        high = overflow_detect(high)
        self.assertEqual((508, -28), (low, high))

    # Division by 0
    def test_div_5(self):
        self.assertRaises(DivisionByZero, instructions.div, 5, 0)

    # Divu
    def test_divu(self):
        low, high = instructions.div(-30000, 59, signed=False)
        self.assertEqual((72795547, 23), (low, high))

    # Clo
    # Positive
    def test_clo_1(self):
        ret = instructions.clo(200000)
        self.assertEqual(0, ret)

    # Negative
    def test_clo_2(self):
        ret = instructions.clo(-200000)
        self.assertEqual(14, ret)

    # -1
    def test_clo_3(self):
        ret = instructions.clo(-1)
        self.assertEqual(32, ret)

    # Clz
    # Positive
    def test_clz_1(self):
        ret = instructions.clz(200000)
        self.assertEqual(14, ret)

    # Negative
    def test_clz_2(self):
        ret = instructions.clz(-200000)
        self.assertEqual(0, ret)

    # 0
    def test_clz_3(self):
        ret = instructions.clz(0)
        self.assertEqual(32, ret)

    # Slt
    # General case 1
    def test_slt_1(self):
        ret = instructions.slt(-3, 5)
        self.assertEqual(1, ret)

    # General case 2
    def test_slt_2(self):
        ret = instructions.slt(5, -3)
        self.assertEqual(0, ret)

    # Sltu
    # General case 1
    def test_sltu_1(self):
        ret = instructions.sltu(5, -3)
        self.assertEqual(1, ret)

    # General case 2
    def test_sltu_2(self):
        ret = instructions.sltu(-3, 5)
        self.assertEqual(0, ret)

    # General case 3
    def test_sltu_3(self):
        ret = instructions.sltu(-5, -3)
        self.assertEqual(1, ret)

    # Slti
    # Invalid immediate
    def test_slti(self):
        self.assertRaises(InvalidImmediate, instructions.slti, 3, 60000)

    # Sltiu
    # Invalid immediate
    def test_sltiu(self):
        self.assertRaises(InvalidImmediate, instructions.sltiu, 3, -60000)

    # Shifting
    # Sll
    # General case
    def test_sll_1(self):
        ret = instructions.sll(1, 5)
        self.assertEqual(2 ** 5, ret)

    # Invalid shift amount
    def test_sll_2(self):
        self.assertRaises(InvalidImmediate, instructions.sll, 1, 32)

    # Sllv
    # shamt out of range 0-31
    def test_sllv(self):
        ret = instructions.sllv(1, -1)
        ret = instructions.overflow_detect(ret)
        self.assertEqual(-2 ** 31, ret)

    # Sra
    def test_sra(self):
        ret = instructions.sra(-2 ** 31, 24)
        ret = instructions.overflow_detect(ret)
        self.assertEqual(-128, ret)

    # Srl
    # positive
    def test_srl_1(self):
        ret = instructions.srl(2 ** 30, 24)
        self.assertEqual(64, ret)

    # Negative
    def test_srl_2(self):
        ret = instructions.srl(-2 ** 31, 24)
        self.assertEqual(128, ret)

    # Jump operations
    # j
    # Valid case
    def test_j_1(self):
        mem = Memory(False)
        mem.addLabel('label', 0x12345678)
        reg = {}
        instructions.j(reg, mem, 'label')
        self.assertEqual(0x12345678, reg['pc'])

    # Invalid case
    def test_j_2(self):
        mem = Memory(False)
        mem.addLabel('label', 0x12345678)
        reg = {}
        self.assertRaises(InvalidLabel, instructions.j, reg, mem, 'wack')

    # jal
    # Valid case
    def test_jal_1(self):
        mem = Memory(False)
        mem.addLabel('label', 0x12345678)
        reg = {'pc': 0x400000}
        instructions.jal(reg, mem, 'label')
        self.assertEqual(0x12345678, reg['pc'])
        self.assertEqual(0x400000, reg['$ra'])

    # Invalid case
    def test_jal_2(self):
        mem = Memory(False)
        mem.addLabel('label', 0x12345678)
        reg = {'pc': 0x400000}
        self.assertRaises(InvalidLabel, instructions.jal, reg, mem, 'wack')

    # jalr
    def test_jalr(self):
        reg = {'pc': 0x400000, '$t0': 0x1234}
        instructions.jalr(reg, '$t0')
        self.assertEqual(0x400000, reg['$ra'])
        self.assertEqual(0x1234, reg['pc'])

    # Lui
    # Positive
    def test_lui_1(self):
        ret = instructions.lui(0xFFF)
        self.assertEqual(0xFFF0000, ret)

    # Negative
    def test_lui_2(self):
        ret = instructions.lui(0xFFFF)
        self.assertEqual(-2 ** 16, overflow_detect(ret))

    # Invalid
    def test_lui_3(self):
        self.assertRaises(InvalidImmediate, instructions.lui, -1)
        self.assertRaises(InvalidImmediate, instructions.lui, 65536)

    # Logical operations
    def test_and(self):
        ret = instructions._and(0x5d9d128d, 0x30be0a88)
        self.assertEqual(0x109c0288, ret)

    def test_or(self):
        ret = instructions._or(0x5d9d128d, 0x30be0a88)
        self.assertEqual(0x7dbf1a8d, ret)

    def test_xor(self):
        ret = instructions.xor(0x5d9d128d, 0x30be0a88)
        self.assertEqual(0x6d231805, ret)

    def test_nor(self):
        ret = instructions.nor(0x5d9d128d, 0x30be0a88)
        self.assertEqual(-2109676174, overflow_detect(ret))

    # Load operations
    # Lb
    # Positive
    def test_lb_1(self):
        mem = Memory(False)
        mem.addByte(30, 0x10010005)
        ret = instructions.lb(0x10010005, mem)
        self.assertEqual(30, ret)

    # Sign extend
    def test_lb_2(self):
        mem = Memory(False)
        mem.addByte(0xF0, 0x10010005)
        ret = instructions.lb(0x10010005, mem)
        self.assertEqual(-16, ret)

    # Address out of range
    def test_lb_3(self):
        mem = Memory(False)
        self.assertRaises(MemoryOutOfBounds, instructions.lb, 0x10000005, mem)

    # Nothing there
    def test_lb_4(self):
        mem = Memory(False)
        ret = instructions.lb(0x10010002, mem)
        self.assertEqual(0, ret)

    # Lbu
    # General case
    def test_lbu_1(self):
        mem = Memory(False)
        mem.addByte(0xF0, 0x10010005)
        ret = instructions.lbu(0x10010005, mem)
        self.assertEqual(0xF0, ret)

    # More than one byte
    def test_lbu_2(self):
        mem = Memory(False)
        mem.addByte(0xFFF0, 0x10010005)
        ret = instructions.lbu(0x10010005, mem)
        self.assertEqual(0xF0, ret)

    # Lh
    # General case
    def test_lh_1(self):
        mem = Memory(False)
        mem.addHWord(3000, 0x10010006)
        ret = instructions.lh(0x10010006, mem)
        self.assertEqual(3000, ret)

    # Sign extend
    def test_lh_2(self):
        mem = Memory(False)
        mem.addHWord(0xFFFF, 0x10010006)
        ret = instructions.lh(0x10010006, mem)
        self.assertEqual(-1, ret)

    # Address unaligned
    def test_lh_3(self):
        mem = Memory(False)
        self.assertRaises(MemoryAlignmentError, instructions.lh, 0x10010005, mem)

    # Nothing there
    def test_lh_4(self):
        mem = Memory(False)
        ret = instructions.lh(0x10010002, mem)
        self.assertEqual(0, ret)

    # More than one byte
    def test_lh_5(self):
        mem = Memory(False)
        mem.addHWord(0x7F000F, 0x10010006)
        ret = instructions.lh(0x10010006, mem)
        self.assertEqual(0xF, ret)

    # Lhu
    # Zero extend
    def test_lhu(self):
        mem = Memory(False)
        mem.addHWord(0xFFFF, 0x10010006)
        ret = instructions.lhu(0x10010006, mem)
        self.assertEqual(0xFFFF, ret)

    # Lw
    # General case
    def test_lw_1(self):
        mem = Memory(False)
        mem.addWord(0x1234abcd, 0x10010008)
        ret = instructions.lw(0x10010008, mem)
        self.assertEqual(0x1234abcd, ret)

    # Address unaligned
    def test_lw_2(self):
        mem = Memory(False)
        mem.addWord(0x1234abcd, 0x10010008)
        self.assertRaises(MemoryAlignmentError, instructions.lw, 0x10010007, mem)

    # Nothing there
    def test_lw_3(self):
        mem = Memory(False)
        mem.addByte(0xFF, 0x10010002)
        ret = instructions.lw(0x10010000, mem)
        self.assertEqual(0x00FF0000, ret)

    # sb
    # General case
    def test_sb_1(self):
        mem = Memory(False)
        instructions.sb(0x10010005, mem, 0xF4)
        self.assertEqual(0xF4, mem.data[str(0x10010005)])

    # Address out of range
    def test_sb_2(self):
        mem = Memory(False)
        self.assertRaises(MemoryOutOfBounds, instructions.sb, 0x1001005, mem, 0xF4)

    # More than one byte
    def test_sb_3(self):
        mem = Memory(False)
        instructions.sb(0x10010005, mem, 0x12345678)
        self.assertEqual(0x78, mem.data[str(0x10010005)])

    # sh
    # General case
    def test_sh_1(self):
        mem = Memory(False)
        instructions.sh(0x10010006, mem, 0xabcd)
        self.assertEqual(0xcd, mem.data[str(0x10010006)])
        self.assertEqual(0xab, mem.data[str(0x10010007)])

    # Address unaligned
    def test_sh_2(self):
        mem = Memory(False)
        self.assertRaises(MemoryAlignmentError, instructions.sh, 0x10010007, mem, 0xabcd)

    # sw
    # General case
    def test_sw_1(self):
        mem = Memory(False)
        instructions.sw(0x10010004, mem, 0x1234abcd)
        self.assertEqual(0xcd, mem.data[str(0x10010004)])
        self.assertEqual(0xab, mem.data[str(0x10010005)])
        self.assertEqual(0x34, mem.data[str(0x10010006)])
        self.assertEqual(0x12, mem.data[str(0x10010007)])

    # Address unaligned
    def test_sw_2(self):
        mem = Memory(False)
        self.assertRaises(MemoryAlignmentError, instructions.sw, 0x10010006, mem, 0x1234abcd)

    # Lwl
    # Test with different alignment
    def test_lwl_0(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwl(0x10010000, mem, reg)
        self.assertEqual(0x7868abcd, ret)

    def test_lwl_1(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwl(0x10010001, mem, reg)
        self.assertEqual(0x5678abcd, ret)

    def test_lwl_2(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwl(0x10010002, mem, reg)
        self.assertEqual(0x345678cd, ret)

    def test_lwl_3(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwl(0x10010003, mem, reg)
        self.assertEqual(0x12345678, ret)

    # Lwr
    # Test with different alignment
    def test_lwr_0(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwr(0x10010000, mem, reg)
        self.assertEqual(0x12345678, ret)

    def test_lwr_1(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwr(0x10010001, mem, reg)
        self.assertEqual(0x24123456, ret)

    def test_lwr_2(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwr(0x10010002, mem, reg)
        self.assertEqual(0x24681234, ret)

    def test_lwr_3(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        ret = instructions.lwr(0x10010003, mem, reg)
        self.assertEqual(0x2468ab12, ret)

    # swl
    def test_swl_0(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swl(0x10010000, mem, reg)
        self.assertEqual(0x24, mem.data[str(0x10010000)])
        self.assertEqual(0x56, mem.data[str(0x10010001)])
        self.assertEqual(0x34, mem.data[str(0x10010002)])
        self.assertEqual(0x12, mem.data[str(0x10010003)])

    def test_swl_1(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swl(0x10010001, mem, reg)
        self.assertEqual(0x68, mem.data[str(0x10010000)])
        self.assertEqual(0x24, mem.data[str(0x10010001)])
        self.assertEqual(0x34, mem.data[str(0x10010002)])
        self.assertEqual(0x12, mem.data[str(0x10010003)])

    def test_swl_2(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swl(0x10010002, mem, reg)
        self.assertEqual(0xab, mem.data[str(0x10010000)])
        self.assertEqual(0x68, mem.data[str(0x10010001)])
        self.assertEqual(0x24, mem.data[str(0x10010002)])
        self.assertEqual(0x12, mem.data[str(0x10010003)])

    def test_swl_3(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swl(0x10010003, mem, reg)
        self.assertEqual(0xcd, mem.data[str(0x10010000)])
        self.assertEqual(0xab, mem.data[str(0x10010001)])
        self.assertEqual(0x68, mem.data[str(0x10010002)])
        self.assertEqual(0x24, mem.data[str(0x10010003)])

    # swr
    def test_swr_0(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swr(0x10010000, mem, reg)
        self.assertEqual(0xcd, mem.data[str(0x10010000)])
        self.assertEqual(0xab, mem.data[str(0x10010001)])
        self.assertEqual(0x68, mem.data[str(0x10010002)])
        self.assertEqual(0x24, mem.data[str(0x10010003)])

    def test_swr_1(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swr(0x10010001, mem, reg)
        self.assertEqual(0x78, mem.data[str(0x10010000)])
        self.assertEqual(0xcd, mem.data[str(0x10010001)])
        self.assertEqual(0xab, mem.data[str(0x10010002)])
        self.assertEqual(0x68, mem.data[str(0x10010003)])

    def test_swr_2(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swr(0x10010002, mem, reg)
        self.assertEqual(0x78, mem.data[str(0x10010000)])
        self.assertEqual(0x56, mem.data[str(0x10010001)])
        self.assertEqual(0xcd, mem.data[str(0x10010002)])
        self.assertEqual(0xab, mem.data[str(0x10010003)])

    def test_swr_3(self):
        mem = Memory(False)
        mem.addWord(0x12345678, 0x10010000)
        reg = 0x2468abcd
        instructions.swr(0x10010003, mem, reg)
        self.assertEqual(0x78, mem.data[str(0x10010000)])
        self.assertEqual(0x56, mem.data[str(0x10010001)])
        self.assertEqual(0x34, mem.data[str(0x10010002)])
        self.assertEqual(0xcd, mem.data[str(0x10010003)])


if __name__ == '__main__':
    unittest.main()
