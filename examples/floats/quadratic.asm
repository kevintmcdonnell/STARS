########## Evaluates Ax^2 + Bx + C ##########
# Values of x, A, B, C are hard-coded

.data
err:  .asciiz "Error: root(s) are imaginary"

.align 2
A:  .float 2.0
B:  .float -6.0
C:  .float -3.0

four: .float 4.0
zero: .float 0.0

.text

main:
	la $t0, A 	# load word at the address of x into $t0
	l.s $f1, 0($t0)
	l.s $f2, 4($t0)
	l.s $f3, 8($t0)
	l.s $f14, 12($t0)
	l.s $f0, 16($t0)

	########## Calculations ##########
    neg.s $f4, $f2  # f4 = -b
    mul.s $f5, $f4, $f4  # f5 = b^2

    mul.s $f6, $f1, $f3  # f6 = ac
    mul.s $f6, $f6, $f14  # f6 = 4ac

    sub.s $f5, $f5, $f6  # f5 = b^2 - 4ac

    # Check if determinant is negative
    c.lt.s $f5, $f0   # b^2 - 4ac < 0?
    bc1t error

    sqrt.s $f5, $f5  # f5 = sqrt(b^2 - 4ac)

    add.s $f10, $f4, $f5  # numerator (plus)
    sub.s $f11, $f4, $f5  # numerator (minus)

    add.s $f1, $f1, $f1   # f1 = 2a

    # Divide by 2a
    div.s $f10, $f10, $f1
    div.s $f11, $f11, $f1

	########## Output ##########
    # Print the roots
	mov.s $f12, $f10
	li $v0, 2
	syscall

	li $a0, '\n'  # Print newline
	li $v0, 11
	syscall

	mov.s $f12, $f11
	li $v0, 2
	syscall

	li $v0, 10	# syscall 10 is terminate program
	syscall

error:
    la $a0, err
    li $v0, 4
    syscall

    li $v0, 10
    syscall

