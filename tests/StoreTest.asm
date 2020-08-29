.globl main
.text
main:

li $t0, 0
addi $t1, $t0, 5

move $a0, $t1
li $v0, 1
syscall

.data
a: .byte 48, 49, 50, 0