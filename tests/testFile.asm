.text
.globl main
main:
li $t0,-3
li $t1,2
div $t0,$t1

mflo $a0
li $v0,1
syscall
mfhi $a0
li $v0,1
syscall