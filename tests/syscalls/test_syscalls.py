import unittest
import unittest.mock as mock
from io import StringIO

import exceptions as ex
import memory
import settings
import syscalls


class TestSyscalls(unittest.TestCase):
    # syscall 1
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0}
        syscalls.printInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -1}
        syscalls.printInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(-1))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0x7FFFFFFF}
        syscalls.printInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0x7FFFFFFF))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -2147483648}
        syscalls.printInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(-2147483648))

    # syscall 4
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printString(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('words', mem.dataPtr)
        syscalls.printString(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), 'words')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidString(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAscii('words', mem.dataPtr)
        mem.dataPtr += 5
        mem.addByte(255, mem.dataPtr)
        mem.dataPtr += 1
        mem.addAsciiz('words', mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.printString, reg, mem)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidString2(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAscii('words', mem.dataPtr)
        mem.dataPtr += 5
        mem.addByte(8, mem.dataPtr)
        mem.dataPtr += 1
        mem.addAsciiz('words', mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.printString, reg, mem)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printEmptyString(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addByte(0, mem.dataPtr)
        syscalls.printString(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '')

    # sycall 5
    @mock.patch('builtins.input', side_effect=['0'])
    def test_readInt(self, input):
        mem = memory.Memory()
        reg = {'$v0': 8}
        syscalls.readInteger(reg, mem)
        self.assertEqual(0, reg['$v0'])

    @mock.patch('builtins.input', side_effect=['-1'])
    def test_readNegInt(self, input):
        mem = memory.Memory()
        reg = {'$v0': 8}
        syscalls.readInteger(reg, mem)
        self.assertEqual(-1, reg['$v0'])

    @mock.patch('builtins.input', side_effect=['A'])
    def test_readInvalidInt(self, input):
        mem = memory.Memory()
        reg = {'$v0': 8}
        self.assertRaises(ex.InvalidInput, syscalls.readInteger, reg, mem)

    # syscall 6
    def test_atoi(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('02113', mem.dataPtr)
        syscalls.atoi(reg, mem)
        self.assertEqual(2113, reg['$v0'])

    def test_atoi_zero(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('0', mem.dataPtr)
        syscalls.atoi(reg, mem)
        self.assertEqual(0, reg['$v0'])

    def test_atoi_neg(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('-12345', mem.dataPtr)
        syscalls.atoi(reg, mem)
        self.assertEqual(-12345, reg['$v0'])

    def test_atoi_bad1(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('--12345', mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, reg, mem)

    def test_atoi_bad2(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('123e45', mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, reg, mem)

    def test_atoi_bad_empty(self):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr}
        mem.addAsciiz('', mem.dataPtr)
        self.assertRaises(ex.InvalidCharacter, syscalls.atoi, reg, mem)

    # syscall 8
    @mock.patch('builtins.input', side_effect=['uwu'])
    def test_readString(self, input):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr, '$a1': 3}
        syscalls.readString(reg, mem)
        s = syscalls.getString(mem.dataPtr, mem, num=3)
        self.assertEqual('uwu', s)

    @mock.patch('builtins.input', side_effect=['uwu uwu'])
    def test_underReadString(self, input):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr, '$a1': 3}
        syscalls.readString(reg, mem)
        s = syscalls.getString(mem.dataPtr, mem, num=3)
        self.assertEqual('uwu', s)

    @mock.patch('builtins.input', side_effect=['uwu uwu'])
    def test_overReadString(self, input):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr, '$a1': 9}
        syscalls.readString(reg, mem)
        s = syscalls.getString(mem.dataPtr, mem, num=9)
        self.assertEqual('uwu uwu', s)

    @mock.patch('builtins.input', side_effect=[str(chr(0xFF))])
    def test_readWeirdString(self, input):
        mem = memory.Memory()
        reg = {'$a0': mem.dataPtr, '$a1': 9}
        syscalls.readString(reg, mem)
        s = mem.getByte(mem.dataPtr, signed=False)
        self.assertEqual(str(chr(0xFF)), str(chr(0xFF)))

    # syscall 9
    def test_sbrk(self):
        mem = memory.Memory()
        reg = {'$a0': 5, '$v0': 0}
        out = mem.heapPtr
        syscalls.sbrk(reg, mem)
        self.assertEqual(out, reg['$v0'])
        self.assertEqual(out + reg['$a0'] + (4 - (reg['$a0'] % 4)), mem.heapPtr)

    def test_Negsbrk(self):
        mem = memory.Memory()
        reg = {'$a0': -1, '$v0': 0}
        self.assertRaises(ex.InvalidArgument, syscalls.sbrk, reg, mem)

    def test_Negsbrk2(self):
        mem = memory.Memory()
        reg = {'$a0': 0xFFFFFFFF, '$v0': 0}
        syscalls.sbrk(reg, mem)
        self.assertRaises(ex.MemoryOutOfBounds, syscalls.sbrk, reg, mem)

    def test_0sbrk(self):
        mem = memory.Memory()
        reg = {'$a0': 0, '$v0': 0}
        out = mem.heapPtr
        syscalls.sbrk(reg, mem)
        self.assertEqual(out, reg['$v0'])
        self.assertEqual(out, mem.heapPtr)

    def test_Maxsbrk(self):
        mem = memory.Memory()
        reg = {'$a0': settings.settings['initial_$sp'] - mem.heapPtr, '$v0': 0}
        out = mem.heapPtr
        syscalls.sbrk(reg, mem)
        self.assertEqual(out, reg['$v0'])
        heap = out + reg['$a0']
        if heap % 4 != 0:
            heap += 4 - (heap % 4)
        self.assertEqual(out + reg['$a0'], mem.heapPtr)

    # syscall 11
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printChar(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': ord('A')}
        syscalls.printChar(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), 'A')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidChar(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 8}
        self.assertRaises(ex.InvalidCharacter, syscalls.printChar, reg, mem)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printInvalidChar2(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 255}
        self.assertRaises(ex.InvalidCharacter, syscalls.printChar, reg, mem)

    # syscall 30
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMem(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hewwo worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  77  77  65  68  w  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemBadChar(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hew' + str(chr(255)) + 'o worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  ff  77  65  68  .  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemBadChar2(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hew' + str(chr(20)) + 'o worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  14  77  65  68  .  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemNull(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hew' + str(chr(0)) + 'o worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  00  77  65  68  \\0 w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemTab(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hew' + str(chr(9)) + 'o worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  09  77  65  68  \\t w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemNewline(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hew' + str(chr(10)) + 'o worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 12}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  0a  77  65  68  \\n w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpMemRound(self, mock_stdout):
        mem = memory.Memory()
        mem.addAsciiz('uwu hewwo worwd >.<', mem.dataPtr)
        reg = {'$a0': mem.dataPtr, '$a1': mem.dataPtr + 10}
        syscalls.memDump(reg, mem)
        self.assertEqual('''addr        hex             ascii       
0x10010000  20  75  77  75     u  w  u  
0x10010004  77  77  65  68  w  w  e  h  
0x10010008  6f  77  20  6f  o  w     o  
''', mock_stdout.getvalue())

    # syscall 31
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpReg(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0}
        syscalls.regDump(reg, mem)
        self.assertEqual('''reg  hex        dec
$a0  0x00000000 0
''', mock_stdout.getvalue())

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpRegNeg(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0x80000000}
        syscalls.regDump(reg, mem)
        self.assertEqual('''reg  hex        dec
$a0  0x80000000 -2147483648
''', mock_stdout.getvalue())

    # syscall 32
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_dumpFiles(self, mock_stdout):
        mem = memory.Memory()
        reg = {}
        f = open('dummytest.txt')
        mem.fileTable[3] = f
        syscalls.dumpFiles(reg, mem)
        f.close()
        self.assertEqual('''0	stdin
1	stdout
2	stderr
3	dummytest.txt
''', mock_stdout.getvalue())

    # syscall 34
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printHex(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0}
        syscalls.printHex(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0x00000000')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegHex(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -1}
        syscalls.printHex(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0xffffffff')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeHex(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0x7FFFFFFF}
        syscalls.printHex(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0x7fffffff')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegHex(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -2147483648}
        syscalls.printHex(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0x80000000')

    # syscall 35
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printBin(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0}
        syscalls.printBin(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0b00000000000000000000000000000000')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegBin(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -1}
        syscalls.printBin(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0b11111111111111111111111111111111')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeBin(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0x7FFFFFFF}
        syscalls.printBin(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0b01111111111111111111111111111111')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegBin(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -2147483648}
        syscalls.printBin(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), '0b10000000000000000000000000000000')

    # syscall 36
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printUInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0}
        syscalls.printUnsignedInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printNegval(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -1}
        syscalls.printUnsignedInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0xffffffff))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeUInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': 0x7FFFFFFF}
        syscalls.printUnsignedInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0x7fffffff))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_printLargeNegUInt(self, mock_stdout):
        mem = memory.Memory()
        reg = {'$a0': -2147483648}
        syscalls.printUnsignedInt(reg, mem)
        self.assertEqual(mock_stdout.getvalue(), str(0x80000000))


if __name__ == '__main__':
    unittest.main()
