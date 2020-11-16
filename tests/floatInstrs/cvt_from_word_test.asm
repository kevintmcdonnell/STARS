.data
c: .word 1337
d: .word 1234567

.text
main:

lw $t0, c
mtc1 $t0, $f0

cvt.s.w $f12, $f0

li $v0, 2
syscall

li $a0, 32
li $v0, 11
syscall

lw $t0, d
mtc1 $t0, $f0

cvt.d.w $f12, $f0

li $v0, 3
syscall
