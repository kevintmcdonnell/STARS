.data
pumpkin:	.ascii "    )\\\n"
		.ascii " .'`--`'.\n"
		.ascii "/  ^  ^  \\\n"
		.ascii "\\ \\/\\/\\/ /\n"
		.asciiz " '------' "

.text
main:
li $a1, 0xffff0000  # base addr of the mmio
li $t0, 0xffff0fa0  # upper addr
la $t1, pumpkin
li $t3, 0 # row
li $t4, 0 # col
li $t5, 80
loop1:
    lbu $t2, 0($t1)
    beqz $t2, exit
    li $t6, '\n'
    bne $t6, $t2, next
        addi $t3, $t3, 1
        li $t4, 0
        addi $t1, $t1, 1
        b loop1
next:
    mul $t7, $t5, $t3
    add $t7, $t7, $t4
    li $t6, 2
    mul $t7, $t7, $t6
    add $t7, $t7, $a1
    sb $t2, 0($t7)
    li $t2, 0x3d
    sb $t2, 1($t7)
    addi $t4, $t4, 1
    addi $t1, $t1, 1
    b loop1
exit:
    la $a0, pumpkin
    li $v0, 4
    syscall
    li $v0, 5
    syscall
    li $v0, 10
    syscall