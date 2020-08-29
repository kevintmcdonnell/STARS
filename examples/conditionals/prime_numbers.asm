.data
start_msg: .asciiz "The first 50 prime numbers are \n"
space: .asciiz " "
endl: .ascii "\n"

.text
main:
	li $s0, 50	# NUMBER_OF_PRIMES: number of primes to display total
	li $s1, 7	# NUMBER_OF_PRIMES_PER_LINE: number of primes to display per line
	li $t0, 0	# count: the number of prime numbers
	li $t1, 2	# number: a number to be tested for primality
	
	la $a0, start_msg
	li $v0, 4
	syscall

while_loop:
	# top of while-loop
	beq $t0, $s0, exit	# repeat until count == # of primes to display

	# initialization of for-loop
	li $t2, 2	# divisor: for-loop counter variable
	move $t3, $t1	# upper bound of loop = number
	li $t4, 2	# declare constant to perform a division
	div $t3, $t4	#    divide number by by 2
	mflo $t3	# upper bound of divisor = number / 2

for_loop:
	bgt $t2, $t3, end_for_loop	# repeat until divisor > number / 2
	div $t1, $t2			# number / divisor
	mfhi $t4			# $t4 = number  divisor
	beqz $t4, end_for_loop		# it's not a prime #; break out of for-loop

	addi $t2, $t2, 1		# it still might be prime, so divisor++
	j for_loop
end_for_loop:

	beqz $t4, dont_print_number	# isPrime is false, so don't print the number
	addi $t0, $t0, 1		# isPrime is true; count++ and...
	li $v0, 1			# ...print the number
	move $a0, $t1
	syscall
	li $a0, ' '
	li $v0, 11
	syscall

	# do we need to print a newline? Let's find out
	div $t0, $s1			# count / NUMBER_OF_PRIMES_PER_LINE
	mfhi $t4			# t5 = count  NUMBER_OF_PRIMES_PER_LINE
	bnez $t4, dont_print_number	# we actually did print number, just don't print newline
	li $a0, '\n'
	li $v0, 11
	syscall

dont_print_number:
	addi $t1, $t1, 1	# number++: set up next number to test for primality
	j while_loop

exit:
	li $a0, '\n'
	li $v0, 11
	syscall

	# terminate program
	li $v0, 10
	syscall


