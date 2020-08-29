import unittest
import subprocess
import os


class MyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MyTestCase, self).__init__(*args, **kwargs)

        # Get directory of files
        self.cwd = os.getcwd() + '/../..'

    def execute_file(self, op):
        # Method to execute test file by running the command line script
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
