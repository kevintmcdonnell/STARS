# Counts the number of 1s in a 32-bit word
# num = 35;
# counter = 0;
# position = 1;
# for (i = 0; i < 32; i++) {
# 	bit = num & position;
# 	if (bit != 0)
# 		counter++;
# 	position = position << 1;
# }
# print(counter);

.text
	# $s0 = num, $s1 = counter, $s2 = bit, $t0 = position, $t1 = i
	li $s0, 0xf1f0f0f0 	# num = input value
	li $s1, 0 		# counter = 0
	li $t0, 1 		# position = 1
	li $t1, 0 		# i = 0

loop:
	and $s2, $s0, $t0 	# bit = num & position
	beqz $s2, end_if	# bit == 0, so leave if-statement
	addi $s1, $s1, 1	# bit == 1, so add 1 to counter
end_if:

	sll $t0, $t0, 1		# position = position << 1
	addi $t1, $t1, 1	# i++
	li $t2, 32
	blt $t1, $t2, loop	# if i < 32 then iterate again	
			
done:
	# print result
	li $v0, 1
	move $a0, $s1
	syscall
	
	# terminate program
	li $v0, 10
	syscall
