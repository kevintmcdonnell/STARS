.data
c: .float 420.42

.text
main:

la $t0, c
l.s $f12, 2($t0)
