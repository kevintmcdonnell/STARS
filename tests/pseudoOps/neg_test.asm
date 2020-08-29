.text

main:

# Testing with positive and negative values and zero
li $t0, 30000
li $t1, -30000
li $t2, 0

neg $a0, $t0
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

neg $a0, $t1
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

neg $a0, $t2
li $v0, 1
syscall