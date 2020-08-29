# Hello world program
.data
greeting: .asciiz "Hello world!\n"
prompt1: .asciiz "Enter your age: "
output1: .asciiz "Your age in 5 years: "

.text
main:
	# print greeting
	li $v0, 4
	la $a0, greeting
	syscall
	
	# display prompt
	li $v0, 4
	la $a0, prompt1
	syscall
	
	# read integer
	li $v0, 5
	syscall
	
	# compute new age
	move $t1, $v0
	addi $t1, $t1, 5
	
	# print output
	li $v0, 4
	la $a0, output1
	syscall
	li $v0, 1
	move $a0, $t1
	syscall
	
	# terminate program
	li $v0, 10
	syscall


