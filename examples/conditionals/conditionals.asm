.data
test: .word 0

.text

main:
	########## if-statement Example #1 ##########
	# if (i == j)
	#    f = g + h;
	# f = f - i;
	
	# $s0 = f, $s1 = g, $s2 = h, $s3 = i, $s4 = j

	li $s0, 10 # f
	li $s1, 6  # g
	li $s2, 3  # h
	li $s3, 1  # i
	li $s4, 2  # j
	
	bne $s3, $s4, L1   	# i != j
	add $s0, $s1, $s2	# f = g + h	
L1:
	sub $s0, $s0, $s3

	########## if-statement Example #2 ##########
	# if (a > b)
	#    if (a > c)
	#       max = a;
	#    else
	#       max = c;
	# else
	#    if (b > c)
	#       max = b;
	#    else
	#       max = c;
	
	# s0 = a, $s1 = b, $s2 = c, $s3 = max
	li $s0, 255	# a
	li $s1, 11 	# b
	li $s2, 9  	# c
	
	ble $s0, $s1, a_LTE_b 	# a <= b, so either b or c is biggest
	ble $s0, $s2, maxC 		# a > b but a <= c, so max = c
	move $s3, $s0 			# a > b and a > c, so max = a
	j done
a_LTE_b:
	ble $s1, $s2,  maxC 	# a <= b and b <= c, so max = c
	move $s3, $s1			# a <= b and b > c, so max = b
	j done

maxC:
	move $s3, $s2			# max = c
	
done:	

	########## while-loop Example #1 ##########
	# determines power of n such that 2^n = 128
	
	# $s0 = pow, $s1 = n
	addi $s0, $0, 1		 	# pow = 1
	add  $s1, $0, $0	 	# n = 0
	addi $t0, $0, 128	 	# t0 = 128
while: 
	beq  $s0, $t0, end_while # leave loop if pow == 128
	sll  $s0, $s0, 1	 	# pow = pow * 2	
	addi $s1, $s1, 1	 	# n = n + 1
	j    while
end_while:

	########## for-loop Example #1 ##########
	# computes sum of 0 through 9 (inclusive)

	# $s0 = i, $s1 = sum
	add  $s1, $0, $0 			# sum = 0
       	add  $s0, $0, $0		# i = 0
       	addi $t0, $0, 10		# $t0 = 10
for:   	beq  $s0, $t0, end_for	# leave loop if i == 10
       	add  $s1, $s1, $s0		# sum = sum + i
       	addi $s0, $s0, 1		# i = i + 1
       	j    for
end_for:

	########## for-loop Example #2 ##########
	# sums the powers of 2 from 1 to 256

	# $s0 = i, $s1 = sum
      	add  $s1, $0, $0		# sum = 0
      	addi $s0, $0, 1			# i = 1
      	addi $t0, $0, 257		# $t0 = 257
for2: 	slt  $t1, $s0, $t0		# $t1 = 1 if i < 257
      	beq  $t1, $0, end_for2	# i >= 257, so leave loop
      	add  $s1, $s1, $s0		# sum = sum + i
      	sll  $s0, $s0, 1		# i = i * 2
      	j    for2
end_for2:

	########## switch-statement Example #1 ##########
	# switch (amount)
	#    case 20:  fee = 2; break;
	#    case 50:  fee = 3; break;
	#    case 100: fee = 5; break;
	#    default:  fee = 7;

	# $s0 = amount, $s1 = fee
	li $s0, 200 			# amount = initial value
case20:
	li $t0, 20
	bne $s0, $t0, case50	# if amount != 20, branch to case50
	li $s1, 2
	j end_switch

case50:
	li $t0, 50
	bne $s0, $t0, case100	# if amount != 50, branch to case100
	li $s1, 3
	j end_switch
	
case100:
	li $t0, 100
	bne $s0, $t0, default	# if amount != 100, branch to default
	li $s1, 5
	j end_switch	

default:
	li $s1, 7

end_switch:

	# playing with lb instruction
	li $s6, 0xAABBCC33
	sw $s6, test
	lb $s7, test
	
	# terminate program
	li $v0, 10
	syscall


