.text
main:

li $t0, 0x0f0f0f0f

not $a0, $t0
li $v0, 34
syscall

li $a0, ' '
li $v0, 11
syscall

li $t0, 0xf0f0f0f0

not $a0, $t0
li $v0, 34
syscall