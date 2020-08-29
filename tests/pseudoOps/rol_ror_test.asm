.text

main:

li $t0, 0x1234abcd

# Should be 0x4abcd123
rol $a0, $t0, 12
li $v0, 34
syscall

li $a0, ' '
li $v0, 11
syscall

# Should be 0xbcd1234a
ror $a0, $t0, 12
li $v0, 34
syscall