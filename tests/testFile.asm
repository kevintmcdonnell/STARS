.data
msg: .asciiz "Hello world\n"

.text
.globl main	# This comment with \n has no problem

main:
	jal func

.include "test2.asm"