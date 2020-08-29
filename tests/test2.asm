.text
f:
li $a0, 0x10400008
addi $a1, $a0, 12
li $v0, 30
syscall
li $v0, 10
syscall
.data
.space 8