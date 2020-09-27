.text
main:

la $t0, a
la $t1, c

l.s $f1, 0($t0)
l.s $f0, 0($t1)

.data
a: .float 3.44
c: .float 5.44