## length.asm - prints out the length of character
## string "str"

.data
str:    .asciiz "hello world"
ans:    .asciiz "Length is "
end1:   .asciiz "\n"

.text
.globl main
main:                   # execution starts here
        la $t2,str      # t2 points to the strint
        li $t1,0        # t1 holds the count
nextCh: lb $t0,($t2)    # get a bye from string
        beqz $t0,strEnd # zero means end of string
        addi $t1,$t1,1  # increment count
        addi $t2,$t2,1  # move pointer one character
        j nextCh        # go round the loop again

strEnd: la $a0,ans      # system call to print
        li $v0,4        # out a message
        syscall

        move $a0,$t1    # system call to print
        li $v0,1        # out the lenghth worked out
        syscall

        la $a0,end1     # system call to print
        li $v0,4        # out a newline
        syscall

        li $v0,10
        syscall         

