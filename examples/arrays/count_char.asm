## count.asm - count the occurences of a specific
## character in string "str".

.data
str:	.asciiz "abceebceebeebbacacc"
char:	.byte   'b'
ans:	.asciiz "Count is "

.text
.globl main
main:
	la $t0, str # address of character to check
	li $t1,0	# the loaded char
	li $t2,0	# counter
	lb $t3,char	# the char we are counting

loop:	
	lb $t1, 0($t0)	    # fetch next char
	beqz $t1, strEnd    # if it's a null, exit loop
	bne $t1, $t3, skip	# not null; same as char?
	addi $t2, $t2, 1	# yes, incrememt counter
skip:	
	addi $t0,$t0,1	# increase address pointer by 1
	j loop 			# and continue
strEnd:
	la $a0, ans	     
	li $v0, 4		
	syscall

	move $a0, $t2   # print out the count
	li $v0,1		
	syscall

	li $a0, '\n'
	li $v0, 11		
	syscall

	li $v0, 10
	syscall	
