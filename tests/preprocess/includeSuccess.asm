.include "toInclude.asm"
.text
li $a0, 24
li $v0, 4
syscall
li $v0, 10
syscall

.data
UvU: .asciiz "owo what's this?"