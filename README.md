This program is a MIPS Assembly simulator made for the purpose of education.
## Dependencies
* PySide2 (v5.14 or newer)
* numpy (v1.19.3 or older for Windows)
* opengl

To download the dependecies run `./startup.sh` or `pip install -r requirements.txt`.
# How to run:
* `python sbumips.py [-a] [-h] [-d] [-g] [-n #] [-i] [-w] [-pa arg1, arg2, ...] filename`

# Positional arguments:
* `filename`       Input MIPS Assembly file.

# optional arguments:
* `-a`, `--assemble`    Assemble program without running it
* `-h`, `--help`     Shows help message and exits
* `-d`, `--debug`    Enables debugging mode
* `-g`, `--garbage`  Enables garbage data
* `-n`, `--max_instructions`  Sets max number of instructions
* `-i`, `--disp_instr_count`  Displays the total instruction count
* `-w`, `--warnings`  Enables warnings
* `-pa`  Program arguments for the MIPS program
    
# Example:
* `python sbumips.py tests/test2.asm -d`     Runs test2.asm with debugger on
* `python sbumips.py tests/test2.asm -g`     Runs test2.asm with garbage data on
* `python sbumips.py tests/test2.asm -d -g`     Runs test2.asm with debugger and garbage data on
* `python sbumips.py tests/test2.asm -pa A 30`     Runs test2.asm with program arguments "A" and "30"

# Troubleshooting
* If you are on Mac (especially Big Sur) and the gui mainwindow doesn't lauch, run `export QT_MAC_WANTS_LAYER=1` in the terminal.
