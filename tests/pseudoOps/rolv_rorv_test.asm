.text

main:

li $t0, 0x1234abcd
li $t1, 12

# Should be 0x4abcd123
rolv $a0, $t0, $t1
li $v0, 34
syscall

li $a0, ' '
li $v0, 11
syscall

# Should be 0xbcd1234a
rorv $a0, $t0, $t1
li $v0, 34
syscall