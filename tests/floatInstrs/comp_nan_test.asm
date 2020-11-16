.data
zero: .float 0.0

.text
main:

la $t0, zero
l.s $f0, 0($t0)

div.s $f0, $f0, $f0
mov.s $f1, $f0

c.le.s 5, $f0, $f1
bc1t 5, branch

li $a0, 0
li $v0, 1
syscall

branch:
li $a0, 1
li $v0, 1
syscall