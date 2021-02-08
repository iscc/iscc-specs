import cython
from libc.stdint cimport uint64_t, uint32_t, uint8_t


cdef uint64_t MAXI64
cdef uint64_t MPRIME
cdef uint32_t MAXH
cdef uint64_t[64] MPA
cdef uint64_t[64] MPB

@cython.locals(a=uint64_t, b=uint64_t, f=uint64_t)
cpdef list minhash(list features)

cpdef bytes minhash_64(list features)

cpdef bytes minhash_256(list features)

@cython.locals(bits=str, bitpos=uint8_t, h=uint64_t)
cpdef bytes compress(list mhash, int lsb=*)
