# This program takes a positive fraction and reduces it to lowest terms.
# $a0 = numerator
# $a1 = denominator
# $s0 = numerator after reducing
# $s1 = denominator after reduction

.data
numer: .word 310
denom: .word 1271
arrow: .asciiz " -> "

.text
main:
	lw $a0, numer
	li $v0, 1
	syscall
	
	li $a0, '/'
	li $v0, 11
	syscall
	
	lw $a0, denom
	li $v0, 1
	syscall
	
	la $a0, arrow
	li $v0, 4
	syscall

	lw $a0, numer
	lw $a1, denom				
	jal reduce

	move $s0, $v0
	move $s1, $v1

	move $a0, $s0
	li $v0, 1
	syscall
	
	li $a0, '/'
	li $v0, 11
	syscall
	
	move $a0, $s1
	li $v0, 1
	syscall
	
	li $a0, '\n'
	li $v0, 11
	syscall
	
	# terminate program
	li $v0, 10
	syscall

# Returns the GCD of a and b ($a0 and $a1).
# Pseudocode:
# function gcd(a, b)
#    while a != b 
#        if a > b
#           a := a - b; 
#        else
#           b := b - a; 
#    return a; 
gcd:
	move $v0, $a0  		# perhaps $a0 == $a1? 
	bne $a0, $a1, not_equal	# looks like they are not equal
	jr $ra			# $a0 == $a1, so just return $a0
	
not_equal:	
	addi $sp, $sp, -8
	sw $s0, 0($sp)
	sw $s1, 4($sp)

	move $s0, $a0
	move $s1, $a1
	
gcd_while:

	ble $s0, $s1, a_lte_b	# branch if a <= b
	sub $s0, $s0, $s1	# a > b so a := a - b
	j a_gt_b
a_lte_b:
	sub $s1, $s1, $s0	# a <= b, so b := b - a
a_gt_b:	
	bne $s0, $s1, gcd_while

	move $v0, $s0

	# return to caller
	lw $s0, 0($sp)
	lw $s1, 4($sp)
	addi $sp, $sp, 8

	jr $ra
	
# Returns the fraction a/b after reducing it to lowest terms:
#   (a / gcd(a,b)) / (b / gcd(a,b))
reduce:
	addi $sp, $sp, -12
	sw $a0, 0($sp)
	sw $a1, 4($sp)
	sw $ra, 8($sp)

	jal gcd

	lw $a0, 0($sp)
	lw $a1, 4($sp)
	lw $ra, 8($sp)
	addi $sp, $sp, 12
	
	move $t0, $v0
	div $a0, $t0	# a = a / gcd(a,b)
	mflo $v0
	div $a1, $t0	# b = b / gcd(a,b)
	mflo $v1

	jr $ra
