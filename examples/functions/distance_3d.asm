.data
x1: .word 5
y1: .word -3
z1: .word 2
x2: .word 8
y2: .word -9
z2: .word 6
message: .asciiz "3D squared distance: "
space: .asciiz " "
endl: .asciiz "\n"

.text
main:
	lw $a0, x1
	lw $a1, y1
	lw $a2, z1
	lw $a3, x2
	lw $t6, y2
	lw $t7, z2

	addi $sp, $sp, -8
	sw $t6, 0($sp)	# y2
	sw $t7, 4($sp)	# z2

	jal distance_3D

	addi $sp, $sp, 8

	move $s0, $v0	# save distance returned by function

	li $v0, 4	# print string
	la $a0, message
	syscall

	li $v0, 1	# print integer
	move $a0, $s0
	syscall

	# terminate program
	li $v0, 10
	syscall

#-------------------------------------------------
# distance_3D - calculates the squared distance
# between two points (x1, y1, z1) and (x2, y2, z2)
#	$a0, $a1, $a2 = (x1, y1, z1)
#       a3 = x2
#	$sp of caller = y2
#	$sp+4 of caller = z2
#	$v0 = (x1-x2)^2 + (y1-y2)^2 + (z1-z2)^2
#-------------------------------------------------
distance_3D:
	lw $t0, 0($sp)
	lw $t1, 4($sp)

	sub $t2, $a0, $a3	# $t2 = x1 - x2
	sub $t3, $a1, $t0	# $t3 = y1 - y2
	sub $t4, $a2, $t1	# $t4 = z1 - z2

	mul $t2, $t2, $t2	# $t2 = (x1 - x2)^2
	mul $t3, $t3, $t3	# $t3 = (y1 - y2)^2
	mul $t4, $t4, $t4	# $t4 = (z1 - z2)^2

	add $v0, $t2, $t3	# result = (x1 - x2)^2 + (y1 - y2)^2
	add $v0, $v0, $t4	# result += (z1 - z2)^2

	jr $ra
