from tests.syscalls import test_syscalls
from tests.pseudoOps import test_pseudoOps
from tests.preprocess import test_preprocess
from tests.instructions import test
from tests.fileOps import test_fileOps

import unittest
from os import chdir

if __name__ == '__main__':
    chdir('tests/syscalls')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=test_syscalls.TestSyscalls)
    unittest.TextTestRunner().run(suite)

    chdir('../pseudoOps')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=test_pseudoOps.MyTestCase)
    unittest.TextTestRunner().run(suite)

    chdir('../preprocess')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=test_preprocess.TestPreprocess)
    unittest.TextTestRunner().run(suite)

    chdir('../instructions')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=test.TestSBUMips)
    unittest.TextTestRunner().run(suite)

    chdir('../fileOps')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCaseClass=test_fileOps.TestFileOps)
    unittest.TextTestRunner().run(suite)