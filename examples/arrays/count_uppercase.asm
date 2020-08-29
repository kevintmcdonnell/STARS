.data
input: .asciiz "Computer Science @ Stony Brook University"
count_msg: .asciiz "Number of uppercase letters: "
space: .asciiz " "
endl: .ascii "\n"

.text
.globl main
main:
	# counts number of uppercase letters: ASCII values in the range 65-90
	li $t0, 0	# count of uppercase letters
	la $t1, input	# address of string
	
loop1:
	lb $t2, 0($t1)		# string[i]
	beqz $t2, done1		# hit NULL character at end of string
	li $t3, 'A'             # minimum ASCII value
	blt $t2, $t3, not_uppercase_letter 
	li $t3, 'Z'             # maximum ASCII value
	bgt $t2, $t3, not_uppercase_letter 
	addi $t0, $t0, 1	# add 1 to count of uppercase letters

not_uppercase_letter:		
	addi $t1, $t1, 1	# advance to next character of string
	j loop1

done1:
	la $a0, count_msg 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	move $a0, $t0		# get count
	li $v0, 1		# syscall 1 is print_integer
	syscall
	
	la $a0, endl 	
	li $v0, 4		# syscall 4 is print_string
	syscall

exit:
	# terminate program
	li $v0, 10
	syscall

