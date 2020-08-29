.text
main:
    li $a0, 0
    li $a1, 0xffff
    label:
        bgeu $a0, $a1, label1
        addi $a0, $a0, 1
        b label
    label1:
        li $v0, 10
        syscall