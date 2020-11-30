"""
https://github.com/sbustars/STARS

Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

settings = {
    'data_min': 0x10010000,  # Lower bound of memory segment
    'data_max': 0x80000000,  # Upper bound of memory segment,
    'mmio_base': 0xffff0000,  # Start of the mmio region of memory
    # Initial register contents
    'initial_$0': 0,
    'initial_$gp': 0x10008000,
    'initial_$sp': 0x7FFFEFFC,
    'initial_$fp': 0,

    'initial_pc': 0x00400000,
    'initial_hi': 0,
    'initial_lo': 0,
    'initial_$ra': 0,

    'max_instructions': 1_000_000,  # Maximum instruction count
    'garbage_registers': False,  # Garbage values in registers / memory
    'garbage_memory': False,

    'pseudo_ops': {'R_TYPE3': [
        'seq',
        'sne',
        'sge',
        'sgeu',
        'sgt',
        'sgtu',
        'sle',
        'sleu',
        'rolv',
        'rorv'
    ],
        'R_TYPE2': [
            'move',
            'neg',
            'not',
            'abs'
        ],
        'I_TYPE': [
            'rol',
            'ror'
        ],
        'LOADS_I': [
            'li'
        ],
        'PS_LOADS_A': [
            'la'
        ],
        'BRANCH': [
            'bge',
            'bgeu',
            'bgt',
            'bgtu',
            'ble',
            'bleu',
            'blt',
            'bltu',
            'b'
        ],
        'ZERO_BRANCH': [
            'beqz',
            'bnez'
        ]},

    # Command line flags
    'assemble': False,
    'debug': False,
    'disp_instr_count': False,
    'warnings': False,
    'gui': False,

    'enabled_syscalls': {1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 30, 31, 32, 34, 35, 36, 40, 41}
}
