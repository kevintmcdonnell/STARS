# Check for leap year. Keep prompting for years until the user enters a leap year.
# In Gregorian Calendar: "A year is a leap year if it is divisible by 4 with 
# the exception of century years that are not divisible by 400" 
# Also, this calendar was adopted in 1582, so the entered year must be >= 1582.
# That is:  if (year % 4 != 0) then ordinary_year
#           else if (year % 100 == 0) and (year  400 != 0) then ordinary_year
#           else leap_year

.data 
year:    	.word 0 
prompt:  	.asciiz "Enter year: " 
leap_msg: 	.asciiz " is a leap year\n" 
ord_msg:	.asciiz " is an ordinary year\n" 
err_msg:	.asciiz "You must enter a year after 1582.\n"

.text
start: 
	li $v0, 4 
	la $a0, prompt 
	syscall                # print a prompt

	li $v0, 5
	syscall                # read an integer 
	sw $v0, year           # and store it in year

	# if (year < 1582) then go to err_msg
	lw $t0, year 	
	li $t1, 1582
	blt $t0, $t1, error

	# if (year mod 4 != 0) then go to ordinary_year
	li $t1, 4 
	div $t0, $t1            	# hi = year mod 4 
	mfhi $t1                	# $t1 = hi, which is the remainder
	bne $t1, $0, ordinary_year   	# if $t1 != 0 go to ordinary_year

	# if (year  100 != 0) then go to leap_year
        li $t1, 100 
        div $t0, $t1            # hi = year  100
        mfhi $t1               	# $t1 = hi 
        bne $t1, $0, leap_year	# if $t1 != 0 go to leap_year

	# if (year  400 != 0) then go to ordinary_year
	li $t1, 400 
	div $t0, $t1           		# hi = year  400
	mfhi $t1               		# $t1 = hi 
	bne $t1, $0, ordinary_year  	# if $t1 != 0 go to ordinary_year

leap_year: 
	lw $a0, year           	# it's a leap year
	li $v0, 1 
	syscall               	# print the year 
	li $v0, 4 
	la $a0, leap_msg 
	syscall                	# print " is a leap year\n" 
	j done                  # go to done

ordinary_year: 
	lw $a0, year           # the input was not a leap year
	li $v0, 1 
	syscall                # print the year 
	li $v0, 4 
	la $a0, ord_msg 
	syscall                # print " is an ordinary year\n"
	
	j start              	# go to start (read another year)

error:
	li $v0, 4 
	la $a0, err_msg 
	syscall                # print "You must enter a year after 1582.\n"
	
	j start              	# go to start (read another year)

done:      
	# terminate program
	li $v0, 10
	syscall


