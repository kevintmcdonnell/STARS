.text

main:

# Testing with positive and negative values
li $t0, 30000
li $t1, -30000

abs $a0, $t0
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

abs $a0, $t1
li $v0, 1
syscall