
.text
main:
#comment

	li	$v0, 0x4	# comment
	la	$a0, msg1
	syscall

    la $t0, w
    lw $t0, 0($t0)
	li	$v0,5
	syscall
	move	$t0,$v0

	li	$v0,4
	la	$a0, msg2
	syscall

	li	$v0,5
	syscall
	move	$t1,$v0

    li $t7 4
    li $t8 4

	add $t0, $t0, $t1

	li	$v0, 4
	la	$a0, msg3
	syscall


	li	$v0,1
	move	$a0, $t0
	syscall

	li	$v0, 4
	la	$a0, newline
	syscall

    addi $t1, $t0, 1
    beq $t0, $t1, yeet
    la $a0, test
    li $v0, 4
    syscall

    li $v0, 11
    li $a0, 10
    syscall

yeet:
    li $a0, 0x10010000
    addi $a1, $a0, 28
    li	$v0,30
	syscall

    li $v0,10
    syscall
.include "test2.asm"
	.data
w: .word 2157882611
msg1:	.asciiz	"Enter A:   "
msg2:	.asciiz	"Enter B:   "
msg3:	.asciiz	"A + B = "
test:   .asciiz "Not branched"
newline: .asciiz "\n"
.asciiz "ajsdf"
nums: .byte 1, 2, 'c', 4