.data
c: .float 3.4

.text
main:

li $t0, 2

la $t1, c
l.s $f0, 0($t1)

movz.s $f12, $f0, $t0
li $v0, 2
syscall

li $a0, 32
li $v0, 11
syscall

movn.s $f12, $f0, $t0
li $v0, 2
syscall