########## Evaluates Ax^2 + Bx + C ##########
# Version 1
# Values of x, A, B, C are hard-coded

.data
ans:  .asciiz "Answer: "
endl: .asciiz "\n"
x:  .word 6
A:  .word 3
B:  .word 4
C:  .word 5

.text

main:
	lw $t0, x 	# load word at the address of x into $t0
	lw $t1, A
	lw $t2, B
	lw $t3, C

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


