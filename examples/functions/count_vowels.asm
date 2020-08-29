##
## vowel.asm - prints out number of lower case vowels in
##	     - the string str
##
##	  a0 - points to the string
##

.data
str:	.asciiz "long time ago in a galaxy far away"
endl:	.asciiz "\n"

.text
main:			# execution starts here
	la $a0,str
	jal count_vowels	# call count_vowels

	move $a0,$v0
	li $v0,1
	syscall		# print answer

	la $a0,endl
	li $v0,4
	syscall		# print newline

	li $v0,10
	syscall		# au revoir...

#----------------------------------------------
# is_vowel - takes a single character as a
# parameter and returns 1 if the character
# is a (lower case) vowel; otherwise, returns 0.
# 	a0 - holds character
#	v0 - returns 0 or 1
#----------------------------------------------

is_vowel: 
	li $v0,0
	li $t0, 'a'
	beq $a0, $t0, yes
	li $t0, 'e'
	beq $a0, $t0, yes
	li $t0, 'i'
	beq $a0, $t0, yes
	li $t0, 'o'
	beq $a0, $t0, yes
	li $t0, 'u'
	beq $a0, $t0, yes
	jr $ra
yes:	
	li $v0,1
	jr $ra

#----------------------------------------------
# count_vowels - use is_vowel to count the vowels in a
# string.
# 	a0 - holds string address
#	s0 - holds number of vowels
#	v0 - returns number of vowels
#----------------------------------------------

count_vowels:
	addi $sp, $sp, -12	# save registers on stack
	sw $s0, 0($sp)
	sw $s1, 4($sp)
	sw $ra, 8($sp)

	li $s0, 0		# count of vowels
	move $s1, $a0		# address of string

nextc:	
	lb $a0, ($s1)		# get each character
	beqz $a0, done		# zero marks end
	jal is_vowel		# call is_vowel
	add $s0, $s0, $v0 	# add 0 or 1 to count
	addi $s1, $s1, 1	# move along string
	b nextc
done:	
	move $v0, $s0		# use $v0 for result

	lw $s0, 0($sp)		# restore registers
	lw $s1, 4($sp)
	lw $ra, 8($sp)
	addi $sp, $sp, 12
	jr $ra



