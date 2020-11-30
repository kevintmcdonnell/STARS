import struct
import unittest
import unittest.mock as mock
from io import StringIO

from numpy import float32

import settings
from interpreter import exceptions as ex
from interpreter import memory, syscalls
from interpreter.classes import Label
from interpreter.interpreter import Interpreter

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


def out(s, end=''):
    print(s, end=end)


class TestSyscalls(unittest.TestCase):
    # syscall 1
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0}
        syscalls.printInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -1}
        syscalls.printInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(-1))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0x7FFFFFFF}
        syscalls.printInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0x7FFFFFFF))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -2147483648}
        syscalls.printInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(-2147483648))

    # syscall 2
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printFloat(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.f_reg = {'$f12': float32(420.42)}
        syscalls.printFloat(inter)
        self.assertEqual(mock_stdout.getvalue(), '420.42')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printFloatBig(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.f_reg = {'$f12': float32(42.0E17)}
        syscalls.printFloat(inter)
        self.assertEqual(mock_stdout.getvalue(), '4.2e+18')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printFloatInf(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.f_reg = {'$f12': float32('inf')}
        syscalls.printFloat(inter)
        self.assertEqual(mock_stdout.getvalue(), 'inf')

    # syscall 3
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printDouble(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.f_reg = {'$f12': float32(1.26443839488E11), '$f13': float32(3.9105663299560546875E0)}
        syscalls.printDouble(inter)
        self.assertEqual(mock_stdout.getvalue(), '420.42')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printDoubleBig(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.f_reg = {'$f12': float32(-2.4833974245227757568E19), '$f13': float32(4.1028668212890625E2)}
        syscalls.printDouble(inter)
        self.assertEqual(mock_stdout.getvalue(), '4.2e+18')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printDoubleInf(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()

        inf_int = 0x7FF00000
        inf_bytes = struct.pack('>i', inf_int)
        inf_float = struct.unpack('>f', inf_bytes)[0]

        inter.f_reg = {'$f12': float32(0), '$f13': inf_float}
        syscalls.printDouble(inter)
        self.assertEqual(mock_stdout.getvalue(), 'inf')

    # syscall 4
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printString(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('words', inter.mem.dataPtr)
        syscalls.printString(inter)
        self.assertEqual(mock_stdout.getvalue(), 'words')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidString(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAscii('words', inter.mem.dataPtr)
        inter.mem.dataPtr += 5
        inter.mem.addByte(255, inter.mem.dataPtr)
        inter.mem.dataPtr += 1
        inter.mem.addAsciiz('words', inter.mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.printString, inter)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidString2(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAscii('words', inter.mem.dataPtr)
        inter.mem.dataPtr += 5
        inter.mem.addByte(8, inter.mem.dataPtr)
        inter.mem.dataPtr += 1
        inter.mem.addAsciiz('words', inter.mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.printString, inter)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printEmptyString(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addByte(0, inter.mem.dataPtr)
        syscalls.printString(inter)
        self.assertEqual(mock_stdout.getvalue(), '')

    # sycall 5
    @mock.patch('builtins.input', side_effect=['0'])
    def test_readInt(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$v0': 8}
        syscalls.readInteger(inter)
        self.assertEqual(0, inter.reg['$v0'])

    @mock.patch('builtins.input', side_effect=['-1'])
    def test_readNegInt(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$v0': 8}
        syscalls.readInteger(inter)
        self.assertEqual(-1, inter.reg['$v0'])

    @mock.patch('builtins.input', side_effect=['A'])
    def test_readInvalidInt(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$v0': 8}
        self.assertRaises(ex.InvalidInput, syscalls.readInteger, inter)

    # syscall 6
    def test_atoi(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('02113', inter.mem.dataPtr)
        syscalls.atoi(inter)
        self.assertEqual(2113, inter.reg['$v0'])

    def test_atoi_zero(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('0', inter.mem.dataPtr)
        syscalls.atoi(inter)
        self.assertEqual(0, inter.reg['$v0'])

    def test_atoi_neg(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('-12345', inter.mem.dataPtr)
        syscalls.atoi(inter)
        self.assertEqual(-12345, inter.reg['$v0'])

    def test_atoi_bad1(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('--12345', inter.mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, inter)

    def test_atoi_bad2(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('123e45', inter.mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, inter)

    def test_atoi_bad_empty(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr}
        inter.mem.addAsciiz('', inter.mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, inter)

    # syscall 8
    @mock.patch('builtins.input', side_effect=['uwu'])
    def test_readString(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': 3}
        syscalls.readString(inter)
        s = syscalls.getString(inter.mem.dataPtr, inter.mem, num_chars=3)
        self.assertEqual('uwu', s)

    @mock.patch('builtins.input', side_effect=['uwu uwu'])
    def test_underReadString(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': 3}
        syscalls.readString(inter)
        s = syscalls.getString(inter.mem.dataPtr, inter.mem, num_chars=3)
        self.assertEqual('uwu', s)

    @mock.patch('builtins.input', side_effect=['uwu uwu'])
    def test_overReadString(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': 9}
        syscalls.readString(inter)
        s = syscalls.getString(inter.mem.dataPtr, inter.mem, num_chars=9)
        self.assertEqual('uwu uwu', s)

    @mock.patch('builtins.input', side_effect=[str(chr(0xFF))])
    def test_readWeirdString(self, input):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': 9}
        syscalls.readString(inter)
        s = inter.mem.getByte(inter.mem.dataPtr, signed=False)
        self.assertEqual(str(chr(0xFF)), str(chr(0xFF)))

    # syscall 9
    def test_sbrk(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 5, '$v0': 0}
        out = inter.mem.heapPtr
        syscalls.sbrk(inter)
        self.assertEqual(out, inter.reg['$v0'])
        self.assertEqual(out + inter.reg['$a0'] + (4 - (inter.reg['$a0'] % 4)), inter.mem.heapPtr)

    def test_Negsbrk(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -1, '$v0': 0}
        self.assertRaises(ex.InvalidArgument, syscalls.sbrk, inter)

    def test_Negsbrk2(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0xFFFFFFFF, '$v0': 0}
        self.assertRaises(ex.InvalidArgument, syscalls.sbrk, inter)

    def test_0sbrk(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0, '$v0': 0}
        out = inter.mem.heapPtr
        syscalls.sbrk(inter)
        self.assertEqual(out, inter.reg['$v0'])
        self.assertEqual(out, inter.mem.heapPtr)

    def test_Maxsbrk(self):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': settings.settings['initial_$sp'] - inter.mem.heapPtr, '$v0': 0}
        out = inter.mem.heapPtr
        syscalls.sbrk(inter)
        self.assertEqual(out, inter.reg['$v0'])
        heap = out + inter.reg['$a0']
        if heap % 4 != 0:
            heap += 4 - (heap % 4)
        self.assertEqual(out + inter.reg['$a0'], inter.mem.heapPtr)

    # syscall 11
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printChar(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': ord('A')}
        syscalls.printChar(inter)
        self.assertEqual(mock_stdout.getvalue(), 'A')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidChar(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 8}
        self.assertRaises(ex.InvalidCharacter, syscalls.printChar, inter)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidChar2(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 255}
        self.assertRaises(ex.InvalidCharacter, syscalls.printChar, inter)

    # syscall 30
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMem(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hewwo worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  77  77  65  68  w  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemBadChar(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hew' + str(chr(255)) + 'o worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  ff  77  65  68  .  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemBadChar2(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hew' + str(chr(20)) + 'o worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  14  77  65  68  .  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemNull(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hew' + str(chr(0)) + 'o worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  00  77  65  68  \\0 w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemTab(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hew' + str(chr(9)) + 'o worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  09  77  65  68  \\t w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemNewline(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hew' + str(chr(10)) + 'o worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 12}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  0a  77  65  68  \\n w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemRound(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.mem.addAsciiz('uwu hewwo worwd >.<', inter.mem.dataPtr)
        inter.reg = {'$a0': inter.mem.dataPtr, '$a1': inter.mem.dataPtr + 10}
        syscalls.memDump(inter)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  77  77  65  68  w  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    # syscall 31
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpReg(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0}
        syscalls.regDump(inter)
        self.assertEqual('''reg  hex        dec
$a0  0x00000000 0
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpRegNeg(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0x80000000}
        syscalls.regDump(inter)
        self.assertEqual('''reg  hex        dec
$a0  0x80000000 -2147483648
''', mock_stdout.getvalue())

    # syscall 32
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpFiles(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {}
        f = open('dummytest.txt')
        inter.mem.fileTable[3] = f
        syscalls.dumpFiles(inter)
        f.close()
        self.assertEqual('''0	stdin
1	stdinter.out
2	stderr
3	dummytest.txt
''', mock_stdout.getvalue())

    # syscall 34
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printHex(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0}
        syscalls.printHex(inter)
        self.assertEqual(mock_stdout.getvalue(), '0x00000000')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegHex(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -1}
        syscalls.printHex(inter)
        self.assertEqual(mock_stdout.getvalue(), '0xffffffff')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeHex(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0x7FFFFFFF}
        syscalls.printHex(inter)
        self.assertEqual(mock_stdout.getvalue(), '0x7fffffff')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegHex(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -2147483648}
        syscalls.printHex(inter)
        self.assertEqual(mock_stdout.getvalue(), '0x80000000')

    # syscall 35
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printBin(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0}
        syscalls.printBin(inter)
        self.assertEqual(mock_stdout.getvalue(), '0b00000000000000000000000000000000')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegBin(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -1}
        syscalls.printBin(inter)
        self.assertEqual(mock_stdout.getvalue(), '0b11111111111111111111111111111111')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeBin(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0x7FFFFFFF}
        syscalls.printBin(inter)
        self.assertEqual(mock_stdout.getvalue(), '0b01111111111111111111111111111111')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegBin(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -2147483648}
        syscalls.printBin(inter)
        self.assertEqual(mock_stdout.getvalue(), '0b10000000000000000000000000000000')

    # syscall 36
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printUInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0}
        syscalls.printUnsignedInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegval(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -1}
        syscalls.printUnsignedInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0xffffffff))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeUInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': 0x7FFFFFFF}
        syscalls.printUnsignedInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0x7fffffff))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegUInt(self, mock_stdout):
        inter = Interpreter([Label('main')], [])
        inter.mem = memory.Memory()
        inter.reg = {'$a0': -2147483648}
        syscalls.printUnsignedInt(inter)
        self.assertEqual(mock_stdout.getvalue(), str(0x80000000))


if __name__ == '__main__':
    unittest.main()
