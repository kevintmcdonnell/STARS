.text

main:

# Testing with same values
li $t0, 10
li $t1, 10

# Should be 1
sle $a0, $t0, $t1
li $v0, 1
syscall

# Should be 1
sleu $a0, $t0, $t1
li $v0, 1
syscall

# Testing with diff values
li $t0, -10
li $t1, 10

# Should be 1
sle $a0, $t0, $t1
li $v0, 1
syscall

# Should be 0
sleu $a0, $t0, $t1
li $v0, 1
syscall