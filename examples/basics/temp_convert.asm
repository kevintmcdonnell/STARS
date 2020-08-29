# Converts Celsius temperature to Fahrenheit
.data
prompt:	.asciiz "Enter temperature (Celsius): "
ans1:	.asciiz "The temperature in Fahrenheit is "
end1:	.asciiz "\n"
	
.text
main:
	la $a0,prompt	#print prompt on terminal
	li $v0,4
	syscall
	
	li $v0,5	#syscall 5 reads an integer
	syscall
	
	li $t1, 9
	mul $t0,$v0, $t1	#to convert, multiply by 9,
	li $t1, 5
	div $t0,$t1	#divide by 5, then
	mflo $t0
	addi $t0,$t0,32	#add 32

	la $a0,ans1	#print string before result
	li $v0,4
	syscall

	move $a0,$t0	#print result
	li $v0,1
	syscall

	la $a0,end1	#system call to print
	li $v0,4	#out a newline
	syscall

	li $v0,10
	syscall		
