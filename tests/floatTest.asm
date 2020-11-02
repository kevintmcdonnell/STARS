.data
a: .float 1.0
c: .float 1.8733

.text
main:

la $t0, c
l.s $f14, 0($t0)

la $t0, a
l.s $f10, 0($t0)

c.le.s $f10, $f14

li $t1, 5

movf $a0, $t1
li $v0, 1
syscall