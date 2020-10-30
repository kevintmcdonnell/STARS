.data
a: .float 8.3

.text
main:

la $t0, a

l.s $f14, 0($t0)
cvt.w.s $f12, $f14

li $v0, 2
syscall
