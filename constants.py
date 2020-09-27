LINE_MARKER = '\x81\x82'
FILE_MARKER = '\x81\x83'

WORD_SIZE = 1 << 32  # 2^32
HALF_SIZE = 1 << 16

WORD_MASK = 0xFFFFFFFF

FLOAT_MIN = 1.175494351E-38
FLOAT_MAX = 3.402823466E38

# Registers
REGS = ['$0', '$at', '$v0', '$v1', '$a0', '$a1', '$a2', '$a3', '$k0', '$k1', '$gp', '$sp', '$fp', '$ra', 'pc', 'hi', 'lo']
REGS += [f'$t{i}' for i in range(10)]
REGS += [f'$s{i}' for i in range(8)]

F_REGS = [f'$f{i}' for i in range(32)]