.data
.eqv word "hello"
.asciiz word
.asciiz " word " # word

.text
li $t0, 0

li $v0, 30
li $a0, 0x10000000
li $a1, 0x10000010
syscall