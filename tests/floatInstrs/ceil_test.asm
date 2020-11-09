.data
c: .float 1.8
big: .float 1.5e20
zero: .float 0.0

.text
main:

# Small
la $t0, c
l.s $f12, 0($t0)

ceil.w.s $f1, $f12
mfc1 $a0, $f1

li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

# Big
la $t0, big
l.s $f12, 0($t0)

ceil.w.s $f1, $f12
mfc1 $a0, $f1

li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

# Infinity
la $t0, zero
l.s $f13, 0($t0)
div.s $f12, $f12, $f13

ceil.w.s $f1, $f12
mfc1 $a0, $f1

li $v0, 1
syscall
