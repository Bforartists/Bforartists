# This code tests bug reported in T50703

import numpy

a = numpy.array([[3, 2, 0], [3, 1, 0]], dtype=numpy.int32)
a[0]
