# Implementation of selection sort.
# Kevin McDonnell
# 1/20/2016

# $s0: base address of array
# $s1: number of elements in the array
# $s2: address array[i]
# $s3: array[j]
# $s4: currentMin
# $s5: array[currentMinIndex]
# $t0: i
# $t1: j
# $t2: upper bound on outer loop
# $t3: value of array[i]
# $t4: value of array[j]

.data
array: .word 3, 4, 8, 2, 1
length: .word 5

.text
main:
	la $s0, array	# $s0: base address of array
	lw $s1, length	# number of elements in the array
	
	# initialize outer for-loop variables
	li $t0, 0		# $t0: i = 0	
	addi $t2, $s1, -1	# $t2 is upper bound on outer loop

outer_loop:
	bge $t0, $t2, end_outer_loop	# repeat until i >= length-1

	sll $s2, $t0, 2			# $s2 = 4*i
	add $s2, $s2, $s0		# $s2 is address of array[i]
	lw $s4, ($s2)			# $s4 is currentMin; currentMin = array[i]
	move $s5, $s2			# $s5 is address of currentMin
	
	addi $t1, $t0, 1		# j = i + 1
inner_loop:
	beq $t1, $s1, end_inner_loop	# repeat until j == length

	sll $s3, $t1, 2			# $s3 = 4*j
	add $s3, $s3, $s0		# $s3 is address of array[j]

	# do we have a new minimum?
	lw $t4, ($s3)		# $t4 is value at array[j]
	ble $s4, $t4, element_not_smaller # element not smaller than current minimum
	lw $s4, ($s3)		# we have a new minimum: currentMin = array[j];
	move $s5, $s3		# save address of new minimum
		
element_not_smaller:		

	addi $t1, $t1, 1	# j++
	j inner_loop
end_inner_loop:

	# swap array[i] with array[currentMinIndex] if necessary
	beq $s5, $s2, dont_swap # addr of minimum is still addr of array[i], so don't swap
	lw $t3, ($s2)		# $t3 = array[i]
	sw $t3, ($s5)		# array[currentMinIndex] = array[i]
	sw $s4, ($s2)		# array[i] = currentMin	 
dont_swap:

	addi $t0, $t0, 1	# i++
	j outer_loop
end_outer_loop:	

exit:
	# terminate program
	li $v0, 10
	syscall

