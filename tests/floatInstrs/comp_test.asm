.data
c: .float 4.20
d: .float 42.0

.text
main:

la $t0, c
l.s $f0, 0($t0)

la $t0, d
l.s $f1, 0($t0)

c.le.s $f0, $f1
bc1t branch

li $a0, 0
li $v0, 1
syscall

branch:
li $a0, 1
li $v0, 1
syscall