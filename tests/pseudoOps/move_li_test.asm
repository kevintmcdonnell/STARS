.text
main:

# 16 bit values
li $t0, 300
move $a0, $t0
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

li $t0, -300
move $a0, $t0
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

# 32 bit values
li $t0, 3000000
move $a0, $t0
li $v0, 1
syscall

li $a0, ' '
li $v0, 11
syscall

li $t0, -3000000
move $a0, $t0
li $v0, 1
syscall