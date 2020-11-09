.data
small: .float 420.42
big: .float 1.5e64
nan: .word 0x7FFFFFFF

.text
main:

# Small
la $t0, small
l.s $f12, 0($t0)

li $v0, 2
syscall

li $a0, 32
li $v0, 11
syscall

# Big
la $t0, big
l.s $f12, 0($t0)

li $v0, 2
syscall

li $a0, 32
li $v0, 11
syscall

# Nan
la $t0, nan
l.s $f12, 0($t0)

li $v0, 2
syscall
