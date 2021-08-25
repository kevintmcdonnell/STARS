from interpreter.interpreter import Interpreter
from sbumips import assemble
import sys
if __name__ == "__main__":
    sys.stderr = open('error.out', 'w')
    sys.stdout = sys.stderr
    for i in range(1, 30):
        if i == 26:
            continue
        sys.stderr.write(f'\nhw2-{i}-error.out:\n')

        try:
            result = assemble(f'sample-mips-progs/hw2-{i}/hw2.asm')
            inter = Interpreter(result, ['+'])
            inter.interpret()

        except Exception as e:
            sys.stderr.write(f"{type(e).__name__}: {str(e)}")
            continue

    sys.stderr.close()
