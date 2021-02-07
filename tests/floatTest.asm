.data
c: .double 1.8733
a: .double 1.0

.text
main:

la $t0, c
l.d $f14, 0($t0)

la $t0, a
s.d $f14, 0($t0)

syscall