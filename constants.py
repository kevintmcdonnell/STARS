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

LINE_MARKER = '\x81\x82'
FILE_MARKER = '\x81\x83'

WORD_SIZE = 1 << 32  # 2^32
HALF_SIZE = 1 << 16

WORD_MASK = 0xFFFFFFFF
WORD_MAX = (1 << 31) - 1
WORD_MIN = -(1 << 31)

FLOAT_MIN = 1.175494351E-38
FLOAT_MAX = 3.402823466E38

# Registers
CONST_REGS = ['$zero', '$at', '$k0', '$k1', '$gp', '$sp', '$fp', '$ra',
              'pc', 'hi', 'lo']
REGS = ['$zero', '$at', '$v0', '$v1', '$a0', '$a1', '$a2', '$a3',
        '$t0', '$t1', '$t2', '$t3', '$t4', '$t5', '$t6', '$t7',
        '$s0', '$s1', '$s2', '$s3', '$s4', '$s5', '$s6', '$s7',
        '$t8', '$t9', '$k0', '$k1', '$gp', '$sp', '$fp', '$ra',
        'pc', 'hi', 'lo']

F_REGS = [f'$f{i}' for i in range(32)]

# For syscalls that require user input.
# The index of the type is used to resolve the input type in GUI
USER_INPUT_TYPE = ["str", "int"] 

# For save prompt
SAVE_SINGLE = "Changes to {} will be lost unless you save. Do you wish to save all changes now?"
SAVE_MULTIPLE = "Changes to one or more files will be lost unless you save. Do you wish to save all changes now?"

# For memory byte representation 
MEMORY_REPR = {
    "Hexadecimal":"0x{:02x}", 
    "Decimal":"{:3}",
    "ASCII":"{:2}"
}
MEMORY_REPR_DEFAULT = 'Hexadecimal'

# Size of memory show in table
MEMORY_WIDTH = 4 # bytes per column
MEMORY_ROW_COUNT = 16
MEMORY_COLUMN_COUNT = 4
MEMORY_SIZE = MEMORY_ROW_COUNT * MEMORY_COLUMN_COUNT * 4 # 256
MEMORY_TABLE_HEADER = ["Address"] + [f"+{MEMORY_WIDTH*i:x}" for i in range(MEMORY_COLUMN_COUNT)]
MEMORY_SECTION = ['Kernel', '.data', 'stack', 'MMIO'] # Memory Section Dropdown

WORD_HEX_FORMAT = "0x{:08x}"

# Table Headers
LABEL_HEADER = ['', 'Label', 'Address']
INSTR_HEADER = ["Bkpt", f"{'Address': ^14}", f"{'Instruction': ^40}", "Source"]
REGISTER_HEADER = ["Name", "Value"]
COPROC_FLAGS_HEADER = ["Condition", "Flags"]

# PRESET MESSAGES
PROGRAM_FINISHED = "\n-- program is finished running --\n\n"
OPEN_FILE_FAILED = 'Could not open file\n'
INSTRUCTION_COUNT = "Instruction Count: {}\t\t"

# For message in dialog for syscalls that require user input
INPUT_MESSAGE = {
    "int": "Enter an integer",
    "str": "Enter a string" 
}
INPUT_LABEL = "Value"

WINDOW_TITLE = "STARS"
WORDLIST_PATH = r"gui/wordslist.txt"
PREFERNCES_PATH = "preferences.json"

MENU_BAR = {
    'File': {
        'New': {
            'Shortcut':'Ctrl+N',
            'Action':'self.new_tab'
        },
        'Open': {
            'Shortcut':'Ctrl+O',
            'Action':'self.open_file'
        },
        'Close': {
            'Shortcut':'Ctrl+W',
            'Action':'self.close_tab',
            'Tag':'close',
            'Start':False
        },
        'Save': {
            'Shortcut':'Ctrl+S',
            'Action':'self.save_file',
            'Tag':'save',
            'Start':False
        }
    },
    'Run': {
        'Assemble': {
            'Shortcut':'F3',
            'Action':'self.assemble',
            'Tag':'assemble',
            'Start':False
        },
        'Start': {
            'Shortcut':'F5',
            'Action':'self.start',
            'Tag':'start',
            'Start':False
        },
        'Step': {
            'Shortcut':'F7',
            'Action':'self.step',
            'Tag':'step',
            'Start':False
        },
        'Backstep': {
            'Shortcut':'F8',
            'Action':'self.reverse',
            'Tag':'backstep',
            'Start':False
        },
        'Pause': {
            'Shortcut':'F9',
            'Action':'self.pause',
            'Tag':'pause',
            'Start':False
        }
    },
    'Settings': {
        'Garbage Memory': {
            'Checkbox': 'garbage_memory'
        },
        'Garbage Registers': {
            'Checkbox': 'garbage_registers'
        },
        'Instruction Count': {
            'Checkbox': 'disp_instr_count'
        },
        'Warnings': {
            'Checkbox': 'warnings'
        }
    },
    'Tools': {
        'Change Theme': {
            'Action': "self.change_theme",
            'Shortcut':"F2"
        },
        'MMIO Display': {
            'Action': "self.launch_vt100"
        }
    },
    'Help': {
        'Help': {}
    }    
}