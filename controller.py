from threading import Lock, Event
from interpreter.debugger import Debug
from interpreter.interpreter import Interpreter

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