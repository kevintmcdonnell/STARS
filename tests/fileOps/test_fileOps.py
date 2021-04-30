import unittest
from os import path as p

from interpreter import memory, syscalls, interpreter, classes

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


class TestFileOps(unittest.TestCase):
    # file operations
    def test_file_open_success(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        f = p.abspath('fileToOpen.txt')
        mem.addAsciiz(f, addr)
        reg = {'$a0': addr, '$a1': 0, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.openFile(i)
        self.assertEqual(reg['$v0'], 3, "Couldn't open valid file")
        self.assertEqual(len(mem.fileTable), 4)
        mem.fileTable[3].close()

    def test_file_open_nonexistent(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        mem.addAsciiz('file2Open.txt', addr)
        reg = {'$a0': addr, '$a1': 0, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.openFile(i)
        self.assertEqual(reg['$v0'], -1, "Opened invalid file")
        self.assertEqual(len(mem.fileTable), 3, "Opened invalid file")

    def test_file_open_invalid_char(self):
        mem = memory.Memory(False)
        addr = mem.dataPtr
        mem.addAsciiz('file' + chr(127) + 'Open.txt', addr)
        reg = {'$a0': addr, '$a1': 1, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.openFile(i)
        self.assertEqual(reg['$v0'], -1, "Opened an invalid character")
        self.assertEqual(len(mem.fileTable), 3, "Opened an invalid character")

    def test_file_read_success(self):
        file = p.abspath('fileToOpen.txt')
        f = open(file)
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        reg = {'$a0': 3, '$a1': addr, '$a2': 5, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.readFile(i)
        f.close()
        self.assertEqual(reg['$v0'], 5)
        self.assertEqual(syscalls.getString(reg['$a1'], mem, 5), 'hello')

    def test_file_read_overread(self):
        file = p.abspath('fileToOpen.txt')
        f = open(file)
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        reg = {'$a0': 3, '$a1': addr, '$a2': 20, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.readFile(i)
        f.close()
        self.assertEqual(reg['$v0'], 12)
        self.assertEqual(syscalls.getString(reg['$a1'], mem, 12), 'hello world!')

    def test_file_write_success(self):
        f = open('fileToWrite.txt', 'w')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        mem.addAsciiz("Good morning!", addr)
        reg = {'$a0': 3, '$a1': addr, '$a2': 4, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.writeFile(i)
        f.close()
        open('fileToWrite.txt', 'w').close()
        self.assertEqual(reg['$v0'], 4)
        self.assertEqual(syscalls.getString(reg['$a1'], mem, 4), 'Good')

    def test_file_write_overwrite(self):
        f = open('fileToWrite.txt', 'w')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        addr = mem.dataPtr
        mem.addAsciiz("Good morning!", addr)
        reg = {'$a0': 3, '$a1': addr, '$a2': 20, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.writeFile(i)
        f.close()
        open('fileToWrite.txt', 'w').close()
        self.assertEqual(reg['$v0'], 13)
        self.assertEqual(syscalls.getString(reg['$a1'], mem, 13), 'Good morning!')

    def test_file_close_success(self):
        f = open('fileToWrite.txt')
        mem = memory.Memory(False)
        mem.fileTable[3] = f
        reg = {'$a0': 3, '$v0': 0}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.closeFile(i)
        self.assertEqual(len(mem.fileTable), 3)

    def test_file_close_no_file(self):
        mem = memory.Memory(False)
        reg = {'$a0': 3}
        i = interpreter.Interpreter([classes.Label('main')], [])
        i.reg = reg
        i.mem = mem
        syscalls.closeFile(i)
        self.assertEqual(len(mem.fileTable), 3)


if __name__ == '__main__':
    unittest.main()
