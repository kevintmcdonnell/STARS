.text
main:

li $t0, 42
sb $t0, a

li $t0, 11790
sh $t0, bb

li $t0, 216220320
sw $t0, c

lbu $a0, a
li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

lhu $a0, bb
li $v0, 1
syscall

li $a0, 32
li $v0, 11
syscall

lw $a0, c
li $v0, 1
syscall

.data
c: .word 0
bb: .half 0
a: .byte 0