# Demonstrates traversing a 2D array of words, storing a value at each
# cell of the array.

.data
matrix: .word 1 4 7 10 12 2 5 8 11 14 3 6 9 12 15 
rows: .word 5
columns: .word 3

.text
.globl main
main:
la $t0, matrix
lw $t1, rows    # number of rows
lw $t2, columns # number of columns

li $t3, 0  # i, row counter

row_loop:
	li $t4, 0  # j, column counter
col_loop:
	# addr = base_addr + i * num_columns * elem_size_in_bytes + j * elem_size_in_bytes
	# addr = base_addr + elem_size_in_bytes * (i * num_columns + j)

	mul $t5, $t4, $t1 # j * num_rows
	add $t5, $t5, $t3 # j * num_rows + i
	sll $t5, $t5, 2   # 4*(j * num_rows + i)  Mult by 4 b/c we have an array of 4-byte words
	add $t5, $t5, $t0 # base_addr + 4*(j * num_rows + i)
	lw $a0, 0($t5)
	li $v0 1
	syscall
	li $a0, ' '
	li $v0, 11
	syscall

	addi $t4, $t4, 1  # j++
	blt $t4, $t2, col_loop
col_loop_done:

addi $t3, $t3, 1  # i++
blt $t3, $t1, row_loop

row_loop_done:

li $a0, '\n'
li $v0, 11
syscall
	
# Terminate the program
li $v0, 10
syscall
