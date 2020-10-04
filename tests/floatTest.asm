.data
a: .word -8388608

.text
main:

la $t0, a

l.s $f12, 0($t0)

li $v0, 2
syscall
