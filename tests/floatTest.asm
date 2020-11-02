.data
c: .float 1.8733

.text
main:

la $t0, c
l.s $f14, 0($t0)

li $t1, 1

movn.s $f12, $f14, $t1
li $v0, 2
syscall
