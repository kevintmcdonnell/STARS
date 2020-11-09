from tests.syscalls.test_syscalls import TestSyscalls
from tests.pseudoOps.test_pseudoOps import MyTestCase
from tests.preprocess.test_preprocess import TestPreprocess
from tests.instructions.test import TestSBUMips
from tests.fileOps.test_fileOps import TestFileOps
from tests.floatInstrs.test import FloatTest
import unittest
from os import chdir

if __name__ == '__main__':
    chdir('tests/syscalls')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=TestSyscalls)
    unittest.TextTestRunner().run(suite)

    chdir('../pseudoOps')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=MyTestCase)
    unittest.TextTestRunner().run(suite)

    chdir('../preprocess')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=TestPreprocess)
    unittest.TextTestRunner().run(suite)

    chdir('../instructions')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=TestSBUMips)
    unittest.TextTestRunner().run(suite)

    chdir('../fileOps')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=TestFileOps)
    unittest.TextTestRunner().run(suite)

    chdir('../floatInstrs')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=FloatTest)
    unittest.TextTestRunner().run(suite)