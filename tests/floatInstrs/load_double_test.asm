.data
small: .double 420.42
nan1: .word 0x7FFFFFFF
nan2: .word -1

.text
main:

# Small
la $t0, small
l.d $f12, 0($t0)

li $v0, 3
syscall

li $a0, 32
li $v0, 11
syscall

# Nan
la $t0, nan1
l.d $f12, 0($t0)

li $v0, 3
syscall
