.data
small: .double 0.0
nan: .double 0.0

.text
main:

# Small
li $t0, 0x51EB851F
mtc1 $t0, $f14

li $t0, 0x407A46B8
mtc1 $t0, $f15

la $t1, small
s.d $f14, 0($t1)
l.d $f12, 0($t1)

li $v0, 3
syscall

li $a0, 32
li $v0, 11
syscall

# Nan
li $t0, -1
mtc1 $t0, $f14

li $t0, 0x7FFFFFFF
mtc1 $t0, $f15

la $t1, nan
s.d $f14, 0($t1)
l.d $f12, 0($t1)

li $v0, 3
syscall

