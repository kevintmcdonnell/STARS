.data
c: .float 1.8733
a: .float 1.0

.text
main:

la $t0, c
l.s $f14, 0($t0)

la $t0, a
l.s $f10, 0($t0)

c.le.s 3, $f10, $f14

syscall