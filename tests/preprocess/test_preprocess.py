import unittest
from os import path as p
from preprocess import *
from exceptions import *
from sbumips import MipsLexer


class TestPreprocess(unittest.TestCase):

    def test_eqv_success(self):
        lexer = MipsLexer()
        data = preprocess('eqvTest.asm', lexer)
        self.assertEqual(data, '''.data \x81\x82 "eqvTest.asm" 1
.eqv word "hello" \x81\x83 "eqvTest.asm" 2
.asciiz word \x81\x83 "eqvTest.asm" 3
.asciiz " word " # word \x81\x83 "eqvTest.asm" 4

.text \x81\x83 "eqvTest.asm" 6
li $t0, 0 \x81\x83 "eqvTest.asm" 7

li $v0, 30 \x81\x83 "eqvTest.asm" 9
li $a0, 0x10000000 \x81\x83 "eqvTest.asm" 10
li $a1, 0x10000010 \x81\x83 "eqvTest.asm" 11
syscall \x81\x83 "eqvTest.asm" 12''')

    def test_file_include_success(self):
        lexer = MipsLexer()
        data = preprocess('includeSuccess.asm', lexer)
        self.assertEqual(data, '''.text \x81\x82 "toInclude.asm" 1
li $v0, 10 \x81\x83 "toInclude.asm" 2
syscall \x81\x83 "toInclude.asm" 3

.data \x81\x83 "toInclude.asm" 5
jello: .word 4 \x81\x83 "toInclude.asm" 6
.text \x81\x83 "includeSuccess.asm" 2
li $a0, 24 \x81\x83 "includeSuccess.asm" 3
li $v0, 4 \x81\x83 "includeSuccess.asm" 4
syscall \x81\x83 "includeSuccess.asm" 5
li $v0, 10 \x81\x83 "includeSuccess.asm" 6
syscall \x81\x83 "includeSuccess.asm" 7

.data \x81\x83 "includeSuccess.asm" 9
UvU: .asciiz "owo what's this?" \x81\x83 "includeSuccess.asm" 10''')

    def test_file_not_found(self):
        lexer = MipsLexer()
        self.assertRaises(FileNotFoundError, preprocess, 'invalidFile.asm', lexer)

    def test_file_already_included(self):
        lexer = MipsLexer()
        self.assertRaises(FileAlreadyIncludedException, preprocess, 'alreadyIncluded.asm', lexer)

    def test_eqv_restricted_token(self):
        lexer = MipsLexer()
        self.assertRaises(InvalidEQVException, preprocess, 'eqvRestricted.asm', lexer)
