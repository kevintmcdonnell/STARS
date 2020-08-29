LINE_MARKER = '\x81\x82'
FILE_MARKER = '\x81\x83'

WORD_SIZE = 1 << 32  # 2^32
HALF_SIZE = 1 << 16

# Registers
REGS = ['$0', '$at', '$v0', '$v1', '$a0', '$a1', '$a2', '$a3', '$t0', '$t1', '$t2', '$t3', '$t4', '$t5', '$t6', '$t7',
        '$s0', '$s1', '$s2', '$s3', '$s4', '$s5', '$s6', '$s7', '$t8', '$t9', '$k0', '$k1', '$gp', '$sp', '$fp', '$ra', 'pc', 'hi', 'lo']
