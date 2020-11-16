.data
c: .float 4.80
.align 3
d: .double 42.42

.text
main:

la $t0, c
l.s $f0, 0($t0)
cvt.w.s $f12, $f0

mfc1 $a0, $f12
li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

la $t0, d
l.d $f0, 0($t0)
cvt.w.d $f12, $f0

mfc1 $a0, $f12
li $v0, 1
syscall