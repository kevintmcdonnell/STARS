.data
small: .float 0.0
nan: .float 0.0

.text
main:

# Small
li $t0, 0x43D235C3
mtc1 $t0, $f14

la $t1, small
s.s $f14, 0($t1)
l.s $f12, 0($t1)

li $v0, 2
syscall

li $a0, 32
li $v0, 11
syscall

# Nan
li $t0, 0x7FFFFFFF
mtc1 $t0, $f14

la $t1, nan
s.s $f14, 0($t1)
l.s $f12, 0($t1)

li $v0, 2
syscall

