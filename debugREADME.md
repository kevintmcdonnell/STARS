This debugger is loosely based on the GDB debugger.

# How to run:

### Command line:
* see **README.md**

### Changing settings:
* navigate to **settings.py** and set the debug field to `True`
* now all programs will automatically run in debug mode

# Commands:
* `[h]elp`             Prints the usage for the debugger
* `[b]reak <filename> <line_no>`        Adds a breakpoint at line `<line_no>` in file `<filename>`
* `[n]ext`              Continues execution until the next line of code
* `[c]ontinue`          Continues execution until the next breakpoint or the end of execution
* `[i]nfo b`            Prints out all the breakpoints
* `[p]rint <reg> <format>`      Prints out the value of register `<reg>`
* `[p]rint <label> <data_type> <length> <format>`     Prints the memory at the address that `<label>` points to in memory
* `kill`                Terminates the program and debugger
* `[r]everse`           Takes one step back in the program

### Possible formats:
*  These are only relevant for data types `w`, `h`, and `b`.
*  `d`  decimal (signed)
*  `u`  decimal (unsigned)
*  `h`  hexadecimal
*  `b`  binary

### Possible data types:
*  `b`  byte
*  `h`  half word (2 bytes)
*  `w`  word (4 bytes)
*  `c`  character
*  `s`  string

### `print` examples:
*  Suppose the data section contains `.byte nums: 48, 49, 50, 0`.
*  `print nums c 3` would print `0, 1, 2`.
*  `print nums b 3 h` would print `0x30 0x31 0x32`.
*  `print nums s` would print `012`.