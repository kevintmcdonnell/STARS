.data
c: .float 4.20
d: .float 42.0

.text
main:

la $t0, c
l.s $f0, 0($t0)

la $t0, d
l.s $f1, 0($t0)

c.le.s 5, $f0, $f1

li $t2, 42
movt $a0, $t2, 5
li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

li $a0, 0
movt $a0, $t2, 4
li $v0, 1
syscall