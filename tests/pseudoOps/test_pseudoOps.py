import os
import subprocess
import unittest

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


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MyTestCase, self).__init__(*args, **kwargs)

        # Get directory of files
        self.cwd = os.getcwd() + '/../..'

    def execute_file(self, op):
        # Method to execute tests file by running the command line script
        output = subprocess.check_output(['python', 'sbumips.py', f'tests/pseudoOps/{op}_test.asm'], cwd=self.cwd).decode('ascii')
        return output

    def execute_test(self, op, expected_output):
        output = self.execute_file(op)
        self.assertEqual(expected_output, output)

    # The actual tests start here
    def test_abs(self):
        self.execute_test('abs', '30000 30000')

    def test_neg(self):
        self.execute_test('neg', '-30000 30000 0')

    def test_seq_sne(self):
        self.execute_test('seq_sne', '1001')

    def test_sge_sgeu(self):
        self.execute_test('sge_sgeu', '1101')

    def test_sgt_sgtu(self):
        self.execute_test('sgt_sgtu', '0001')

    def test_sle_sleu(self):
        self.execute_test('sle_sleu', '1110')

    def test_not(self):
        self.execute_test('not', '0xf0f0f0f0 0x0f0f0f0f')

    # I guess you could say we're on a 'rol'
    def test_rol_ror(self):
        self.execute_test('rol_ror', '0x4abcd123 0xbcd1234a')

    def test_rolv_rorv(self):
        self.execute_test('rolv_rorv', '0x4abcd123 0xbcd1234a')

    def test_move_li(self):
        self.execute_test('move_li', '300 -300 3000000 -3000000')

    def test_beqz_bnez(self):
        self.execute_test('beqz_bnez', '1001')

    def test_bgt_bgtu(self):
        self.execute_test('bgt_bgtu', '1110')

    def test_bge_bgeu(self):
        self.execute_test('bge_bgeu', '1110')

    def test_blt_bltu(self):
        self.execute_test('blt_bltu', '0001')

    def test_ble_bleu(self):
        self.execute_test('ble_bleu', '1011')

    def test_b(self):
        self.execute_test('b', '1')

    def test_load_store(self):
        self.execute_test('load_store', '42 11790 216220320')


if __name__ == '__main__':
    unittest.main()
