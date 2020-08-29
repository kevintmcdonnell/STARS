.text
main:
li $a0, 1
li $a1, 2
addi $t0, $a0, 3
add $t1, $a0, $a1
jal lab
sw $a0, w
lw $s0, w
li $v0, 10
syscall

lab:
beq $t1, $t0 l1
addi $t1, $t1, 1
l1:
beq $t1, $a0, lab
jr $ra

.data
w: .word 24