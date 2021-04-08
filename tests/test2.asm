.text

func:
	addi $v0, $0, 4	# This comment is fine
	la $a0, msg		# This is a comment with \n that breaks stuff
	syscall