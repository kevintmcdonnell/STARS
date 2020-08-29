.data
ages: .word 19, 25, 20, 22, 24, 23
target_msg: .asciiz "Target element: "
target_elem: .word 22
index_msg: .asciiz "Index: "
space: .asciiz " "
endl: .ascii "\n"

.text
.globl main
main:
	la $s0, ages
	li $s1, 6	# size of array
	li $t1, 0	# i = 0

	# Algorithm 1: print contents of the array
loop1:
	beq $t1, $s1, done1	# repeat until counter == size
	sll $t0, $t1, 2		# $t0 = 4*i
	add $t0, $t0, $s0	# $t0 holds address of ages[i]
	lw $a0, 0($t0)		# get ages[i]
	li $v0, 1		# syscall 1 is print_integer
	syscall
	
	la $a0, space 	
	li $v0, 4		# syscall 4 is print_string
	syscall

	addi $t1, $t1, 1	# i++
	
	j loop1

done1:
	la $a0, endl 	
	li $v0, 4		# syscall 4 is print_string
	syscall

	
	# Algorithm 2: sequentially search for a value in the array
	# if successful, store index in $t4
	# otherwise, store -1 in $t4
	move $t0, $s0		# t1 = starting address of array
	li $t1, 0		# i = 0
	lw $t2, target_elem	# target element
	
	la $a0, target_msg 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	lw $a0, target_elem
	li $v0, 1		# syscall 1 is print_int
	syscall
	
	la $a0, endl 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	li $t4, -1		# pessimistic search!
loop2:
	beq $t1, $s1, done2	# repeat until counter == size
	sll $t0, $t1, 2	
	add $t0, $t0, $s0	# $t0 holds address of ages[i]
	lw $t3, 0($t0)		# get ages[i]
	bne $t3, $t2, no_match	# didn't match
	move $t4, $t1		# we found a match
	j done2
		
no_match:
	addi $t1, $t1, 1	# i++
	j loop2
done2:
	la $a0, index_msg 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	move $a0, $t4		# get ages[i]
	li $v0, 1		# syscall 1 is print_integer
	syscall
	
	la $a0, endl 	
	li $v0, 4		# syscall 4 is print_string
	syscall

exit:
	# terminate program
	li $v0, 10
	syscall
