import math
import os
import subprocess
import unittest

from numpy import float32

from interpreter import instructions as instrs

'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


class FloatTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FloatTest, self).__init__(*args, **kwargs)

        # Get directory of files
        self.cwd = os.getcwd() + '/../..'

    def execute_file(self, op):
        # Method to execute tests file by running the command line script
        output = subprocess.check_output(['python', 'sbumips.py', f'tests/floatInstrs/{op}_test.asm'], cwd=self.cwd, stderr=subprocess.STDOUT).decode('ascii')
        return output

    def execute_test(self, op, expected_output):
        output = self.execute_file(op)
        self.assertEqual(expected_output, output)

    def execute_error_test(self, op, ex):
        output = self.execute_file(op)
        self.assertIn(ex, output)

    # Arithmetic operations
    # Add
    # General case
    def test_add_general(self):
        ret = instrs.add_f(float32(5.38), float32(4.20))
        self.assertEqual(float32(9.58), ret)

    # Overflow
    def test_add_overflow(self):
        ret = instrs.add_f(float32(3e38), float32(3e38))
        self.assertEqual(float32('inf'), ret)

    # Nan
    def test_add_nan(self):
        ret = instrs.add_f(float32('inf'), float32('-inf'))
        self.assertTrue(math.isnan(ret))

    # Sub
    # General case
    def test_sub_general(self):
        ret = instrs.sub_f(float32(5.38), float32(9.58))
        self.assertEqual(float32(-4.20), ret)

    # Overflow
    def test_sub_overflow(self):
        ret = instrs.sub_f(float32(3e38), float32(-3e38))
        self.assertEqual(float32('inf'), ret)

    # Nan
    def test_sub_nan(self):
        ret = instrs.sub_f(float32('inf'), float32('inf'))
        self.assertTrue(math.isnan(ret))

    # Mul
    # General case
    def test_mul_general(self):
        ret = instrs.mul_f(float32(4.20), float32(5.38))
        self.assertEqual(float32(22.595999), ret)

    # Overflow
    def test_mul_overflow(self):
        ret = instrs.mul_f(float32(1e20), float32(1e20))
        self.assertEqual(float32('inf'), ret)

    # Nan
    def test_mul_nan(self):
        ret = instrs.mul_f(float32(0), float32('inf'))
        self.assertTrue(math.isnan(ret))

    # Div
    # Divide by 0
    def test_div_0_single(self):
        ret = instrs.div_f(float32(4.0), float32(0.0))
        self.assertEqual(float32('inf'), ret)

    def test_div_0_double(self):
        ret = instrs.div_f(4.0, 0.0)
        self.assertEqual(float('inf'), ret)

    # 0 / 0
    def test_div_nan_single(self):
        ret = instrs.div_f(float32(0.0), float32(0.0))
        self.assertTrue(math.isnan(ret))

    def test_div_nan_double(self):
        ret = instrs.div_f(0.0, 0.0)
        self.assertTrue(math.isnan(ret))

    # Abs
    # General case
    def test_abs_general(self):
        ret = instrs._abs(float32(-4.20))
        self.assertEqual(float32(4.20), ret)
        self.assertTrue(type(ret) is float32)

    # Infinity
    def test_abs_infinity(self):
        ret = instrs._abs(float32('-inf'))
        self.assertEqual(float32('inf'), ret)
        self.assertTrue(type(ret) is float32)

    # Sqrt
    # General case
    def test_sqrt_general(self):
        ret = instrs.sqrt(float32(9.0))
        self.assertEqual(float32(3.0), ret)
        self.assertTrue(type(ret) is float32)

    # Negative
    def test_sqrt_negative(self):
        ret = instrs.sqrt(float32(-9.0))
        self.assertTrue(math.isnan(ret))
        self.assertTrue(type(ret) is float32)

    # Ceil (round, floor, trunc have pretty much the same functionality)
    def test_ceil(self):
        self.execute_test('ceil', '2 2147483647 2147483647')

    # Load single
    def test_load_single(self):
        self.execute_test('load_single', '420.42 inf nan')

    # Address not aligned
    def test_load_err_single(self):
        self.execute_error_test('load_single_error', 'MemoryAlignmentError')

    # Load double
    def test_load_double(self):
        self.execute_test('load_double', '420.42 nan')

    # Address not aligned
    def test_load_err_double(self):
        self.execute_error_test('load_double_error', 'MemoryAlignmentError')
