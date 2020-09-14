settings = {
    'data_min': 0x10010000,  # Lower bound of memory segment
    'data_max': 0x80000000,  # Upper bound of memory segment,

    # Initial register contents
    'initial_$0': 0,
    'initial_$gp': 0x10008000,
    'initial_$sp': 0x7FFFEFFC,
    'initial_$fp': 0,

    'initial_pc': 0x00400000,
    'initial_hi': 0,
    'initial_lo': 0,
    'initial_$ra': 0,

    'max_instructions': 1000000,  # Maximum instruction count
    'garbage_registers': False,  # Garbage values in registers / memory
    'garbage_memory': False,

    'pseudo_ops': {'R_FUNCT3': [
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
        'R_FUNCT2': [
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

    'enabled_syscalls': {1, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 30, 31, 32, 34, 35, 36, 40, 41}
}
