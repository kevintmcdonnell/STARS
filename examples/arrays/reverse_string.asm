### reverse_string.asm - reverse the character
## string "str"

.data
str:	.asciiz "hello world"
end1:	.asciiz "\n"

.text
.globl main
main:			# execution starts here
	la $t1,str	# t1 points to the string
nextCh:	
	lb $t0,($t1)	# get a byte from string
	beqz $t0,strEnd	# zero means end of string
	addi $sp,$sp,-4	# adjust stack pointer
	sw $t0,($sp)	# PUSH the t0 register
	addi $t1,$t1,1	# move pointer one character
	j nextCh		# go round the loop again
strEnd:	
	la $t1,str		# t1 points to the string
store:	
	lb $t0,($t1)	# get a byte from string
	beqz $t0,done	# zero means end of string
	lw $t0,($sp)	# POP a value from the stack
	addi $sp,$sp,4	# end adjust the pointer
	sb $t0,($t1)	# store in string
	addi $t1, $t1,1	# move pointer one character
	j store

done:	
	la $a0,str	# system call to print
	li $v0,4	# out a message
	syscall

	la $a0,end1	# system call to print
	li $v0,4	# out a newline
	syscall

	li $v0,10
	syscall	

