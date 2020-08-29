# Hello world program
.data
Greeting: .asciiz "Hello world!\n"

.text
main:
	# Prints a string on the screen
	li $v0, 4
	la $a0, Greeting
	syscall
	
	# Terminates the program
	li $v0, 10
	syscall


