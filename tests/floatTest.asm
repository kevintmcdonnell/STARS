.data
a: .float 3.44
c: .float 5.44

.text
main:

la $t0, a
la $t1, c

l.s $f13, 0($t0)
l.s $f12, 0($t1)

li $v0, 3
syscall
