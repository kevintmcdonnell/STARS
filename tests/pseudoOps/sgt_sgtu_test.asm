.text

main:

# Testing with same values
li $t0, 10
li $t1, 10

# Should be 0
sgt $a0, $t0, $t1
li $v0, 1
syscall

# Should be 0
sgtu $a0, $t0, $t1
li $v0, 1
syscall

# Testing with diff values
li $t0, -10
li $t1, 10

# Should be 0
sgt $a0, $t0, $t1
li $v0, 1
syscall

# Should be 1
sgtu $a0, $t0, $t1
li $v0, 1
syscall