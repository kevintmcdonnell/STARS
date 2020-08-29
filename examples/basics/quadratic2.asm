########## Evaluates Ax^2 + Bx + C ##########
# Version 2
# Values of x, A, B, C are entered by user


.data
promptX: .asciiz "Enter x: "
promptA: .asciiz "Enter A: "
promptB: .asciiz "Enter B: "
promptC: .asciiz "Enter C: "
ans:  .asciiz "Answer: "
endl: .asciiz "\n"

.text
main:
	########## Prompts ##########
	la $a0, promptX # load address into argument register $a0
	li $v0, 4 	# syscall 4 is print_string
	syscall
	
	li $v0, 5	# syscall 5 is read_int
	syscall
	move $t0, $v0	# $t0 = x
	
	la $a0, promptA # load address into argument register $a0
	li $v0, 4 	# syscall 4 is print_string
	syscall
	
	li $v0, 5	# syscall 5 is read_int
	syscall
	move $t1, $v0	# $t1 = A
	
	la $a0, promptB # load address into argument register $a0
	li $v0, 4 	# syscall 4 is print_string
	syscall
	
	li $v0, 5	# syscall 5 is read_int
	syscall
	move $t2, $v0	# $t2 = B

	la $a0, promptC # load address into argument register $a0
	li $v0, 4 	# syscall 4 is print_string
	syscall
	
	li $v0, 5	# syscall 5 is read_int
	syscall
	move $t3, $v0	# $t3 = C

	########## Calculations ##########
	mul $t4, $t0, $t0  # $t4 = x^2	
	mul $t5, $t4, $t1  # $t5 = A*x^2
	mul $t2, $t2, $t0  # $t2 = B*x
 	add $t0, $t5, $t2  # $t0 = A*x^2 + B*x	
	add $t0, $t0, $t3  # $t0 = A*x^2 + B*x + C

	########## Output ##########
	la $a0, ans	# load address into argument register $a0
	li $v0, 4	# syscall 4 is print_string
	syscall	

	move $a0, $t0   # move result value into reg $a0
	li $v0, 1	# syscall 1 is print_integer
	syscall

	la $a0, endl 	# load address in arg reg $a0
	li $v0, 4	# syscall 4 is print_string
	syscall
	
	li $v0, 10	# syscall 10 is terminate program
	syscall		


