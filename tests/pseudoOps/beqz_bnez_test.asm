.text
main:

# Zero test
li $t0, 0

beqz $t0, branch

li $a0, 0
li $v0, 1
syscall
j next

branch:
li $a0, 1
li $v0, 1
syscall

next:

li $t0, 1

beqz $t0, branch_2

li $a0, 0
li $v0, 1
syscall
j next_2

branch_2:
li $a0, 1
li $v0, 1
syscall

next_2:

# Zero test
li $t0, 0

bnez $t0, branch_3

li $a0, 0
li $v0, 1
syscall
j next_3

branch_3:
li $a0, 1
li $v0, 1
syscall

next_3:

li $t0, 1

bnez $t0, branch_4

li $a0, 0
li $v0, 1
syscall
j next_4

branch_4:
li $a0, 1
li $v0, 1
syscall

next_4: