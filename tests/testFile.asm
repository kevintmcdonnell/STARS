
.text
main:
#comment

	li $a0, 0xF0
	li $a1, 1
	srlv $a0, $a0, $a1
	li $v0, 1
	syscall

    li $v0,10
    syscall

	.data
w: .word 2157882611
msg1:	.asciiz	"Enter A:   "
msg2:	.asciiz	"Enter B:   "
msg3:	.asciiz	"A + B = "
test:   .asciiz "Not branched"
newline: .asciiz "\n"
.asciiz "ajsdf"
nums: .byte 1, 2, 'c', 4