from threading import Lock, Event
from interpreter.debugger import Debug
from interpreter.interpreter import Interpreter
import settings
'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

class Controller():
    def __init__(self, debug: Debug, interp: Interpreter):
        self.debug = debug
        self.interp = interp

    def set_interp(self, interp: Interpreter) -> None:
        self.interp = interp
        self.debug = interp.debug

    def set_pause(self, pause: bool) -> None:
        if not pause:
            self.interp.pause_lock.clear()
        else:
            self.interp.pause_lock.set()

    def pause(self, pause: bool) -> None:
        self.debug.continueFlag = not pause
        if pause:
            self.interp.pause_lock.clear()
        else:
            self.interp.pause_lock.set()

    def get_byte(self, addr: int, signed: bool =False) -> int:
        return self.interp.mem.getByte(addr, signed=signed, admin=True)

    def add_breakpoint(self, cmd):
        self.debug.addBreakpoint(cmd, self.interp)

    def remove_breakpoint(self, cmd):
        self.debug.removeBreakpoint(cmd, self.interp)

    def reverse(self):
        self.debug.reverse(None, self.interp)

    def good(self) -> bool:
        return self.interp is not None

    def cont(self) -> bool:
        return self.debug.continueFlag

    def setSetting(self, key: str, val: bool) -> None:
        settings.settings[key] = val