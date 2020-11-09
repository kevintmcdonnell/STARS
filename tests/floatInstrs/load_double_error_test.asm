.data
c: .double 420.42
d: .double 1337.420

.text
main:

la $t0, c
l.d $f12, 4($t0)
