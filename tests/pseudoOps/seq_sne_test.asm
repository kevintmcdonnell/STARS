.text

main:

# Testing with same values
li $t0, 30000
li $t1, 30000

# Should be 1
seq $a0, $t0, $t1
li $v0, 1
syscall

# Should be 0
sne $a0, $t0, $t1
li $v0, 1
syscall

# Testing with diff values
li $t0, 30000
li $t1, -30000

# Should be 0
seq $a0, $t0, $t1
li $v0, 1
syscall

# Should be 1
sne $a0, $t0, $t1
li $v0, 1
syscall