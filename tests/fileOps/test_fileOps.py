import unittest
import interpreter
import memory
import syscalls
from os import path as p


class TestFileOps(unittest.TestCase):
    # file operations
    def test_file_open_success(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        f = p.abspath('fileToOpen.txt')
        mem.addAsciiz(f, addr)
        reg = {'$a0': addr, '$a1': 1, '$v0': 0}
        syscalls.openFile(reg, mem)
        self.assertEqual(reg['$v0'], 3, "Couldn't open valid file")
        self.assertEqual(len(mem.fileTable), 4)
        mem.fileTable[3].close()

    def test_file_open_nonexistent(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        mem.addAsciiz('file2Open.txt', addr)
        reg = {'$a0': addr, '$a1': 1, '$v0': 0}
        self.assertRaises(FileNotFoundError, syscalls.openFile, reg, mem)
        self.assertEqual(reg['$v0'], 0, "Opened invalid file")
        self.assertEqual(len(mem.fileTable), 3, "Opened invalid file")

    def test_file_open_invalid_char(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        mem.addAsciiz('file' + chr(127) + 'Open.txt', addr)
        reg = {'$a0': addr, '$a1': 1, '$v0': 0}
        syscalls.openFile(reg, mem)
        self.assertEqual(reg['$v0'], -1, "Opened an invalid character")
        self.assertEqual(len(mem.fileTable), 3, "Opened an invalid character")

    def test_file_read_success(self):
        file = p.abspath('fileToOpen.txt')
        f = open(file)
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        reg = {'$a0': 3, '$a1': addr, '$a2': 5, '$v0': 0}
        syscalls.readFile(reg, mem)
        f.close()
        self.assertEqual(reg['$v0'], 5)
        self.assertEqual(syscalls.getString(addr, mem, 5), 'hello')

    def test_file_read_overread(self):
        file = p.abspath('fileToOpen.txt')
        f = open(file)
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        reg = {'$a0': 3, '$a1': addr, '$a2': 20, '$v0': 0}
        syscalls.readFile(reg, mem)
        f.close()
        self.assertEqual(reg['$v0'], 0)
        self.assertEqual(syscalls.getString(addr, mem, 12), 'hello world!')

    def test_file_write_success(self):
        f = open('fileToWrite.txt', 'w')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        mem.addAsciiz("Good morning!", addr)
        reg = {'$a0': 3, '$a1': addr, '$a2': 4, '$v0': 0}
        syscalls.writeFile(reg, mem)
        f.close()
        open('fileToWrite.txt', 'w').close()
        self.assertEqual(reg['$v0'], 4)
        self.assertEqual(syscalls.getString(addr, mem, 4), 'Good')

    def test_file_write_overwrite(self):
        f = open('fileToWrite.txt', 'w')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        mem.addAsciiz("Good morning!", addr)
        reg = {'$a0': 3, '$a1': addr, '$a2': 20, '$v0': 0}
        syscalls.writeFile(reg, mem)
        f.close()
        open('fileToWrite.txt', 'w').close()
        self.assertEqual(reg['$v0'], 13)
        self.assertEqual(syscalls.getString(addr, mem, 13), 'Good morning!')

    def test_file_close_success(self):
        f = open('fileToWrite.txt')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        reg = {'$a0': 3, '$v0': 0}
        syscalls.closeFile(reg, mem)
        self.assertEqual(len(mem.fileTable), 3)

    def test_file_close_no_file(self):
        mem = memory.Memory(False)
        reg = {'$a0': 3}
        syscalls.closeFile(reg, mem)
        self.assertEqual(len(mem.fileTable), 3)


if __name__ == '__main__':
    unittest.main()
