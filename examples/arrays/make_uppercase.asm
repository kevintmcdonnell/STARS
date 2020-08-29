# Converts lowercase letters to uppercase, leaving all other symbols unchanged.

.data
input: .asciiz "Computer Science @ Stony Brook University"
output_msg: .asciiz "Input to all uppercase: "
space: .asciiz " "
endl: .ascii "\n"

.text
.globl main
main:
	li $t0, 0	# count of uppercase letters
	la $t1, input	# address of string
	
loop1:
	lb $t2, 0($t1)		# read string[i]
	beqz $t2, done1		# hit NULL character at end of string
	li $t3, 'a'
	blt $t2, $t3, not_lowercase_letter  # minimum ASCII value
	li $t3, 'z'
	bgt $t2, $t3, not_lowercase_letter # maximum ASCII value
	addi $t2, $t2, -32	# convert to uppercase letter
	sb $t2, 0($t1)		# write back string[i] 

not_lowercase_letter:		
						
	addi $t1, $t1, 1	# advance to next character of string
	j loop1

done1:
	la $a0, output_msg 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	la $a0, input 	
	li $v0, 4		# syscall 4 is print_string
	syscall
	
	la $a0, endl 	
	li $v0, 4		# syscall 4 is print_string
	syscall

exit:
	# terminate program
	li $v0, 10
	syscall


