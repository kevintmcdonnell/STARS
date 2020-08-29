## hex.asm ask user for decimal number,
##  convert to hex, print the result.

.data
result:	.space 8
.asciiz "\n"
prompt: .asciiz "Enter decimal number: "
ans1:	.asciiz "Hexadecimal is "

.text
.globl main
main:
	la $a0,prompt	# print prompt on terminal
	li $v0,4
	syscall

	li $v0,5		# sycall 5 reads an integer
	syscall
	move $t2,$v0	# $t2 holds hex number

	la $a0,ans1		# print string before result
	li $v0,4
	syscall

	li $t0,8		# eight hex digits in word
	la $t3,result 	# answer string set up here

loop:	
	rol $t2,$t2,4		# start with leftmost digit
	andi $t1,$t2,0xF	# mask one digit
	li $t4, 9
	ble $t1, $t4, print	# check if 0 to 9
	addi $t1,$t1,7		# 7 chars between '9' and 'A'
print:	
	addi $t1,$t1,48	# ASCII '0' is 48
	sb $t1,($t3)	# save in string
	addi $t3,$t3,1	# advance destination pointer
	addi $t0,$t0,-1	# decrement counter
	bnez $t0,loop	# and continue if counter>0
	
	la $a0,result	# print result on terminal
	li $v0,4
	syscall

	li $v0,10
	syscall		
