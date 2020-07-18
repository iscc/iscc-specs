import cython
from libc.stdint cimport uint8_t, uint32_t


cdef uint32_t READ_SIZE
cdef uint32_t MIN
cdef uint32_t AVG
cdef uint32_t MAX
cdef uint32_t CENTER_SIZE
cdef uint32_t MASK_S
cdef uint32_t MASK_L
cdef uint32_t[256] GEAR


@cython.locals(pattern=uint32_t, i=uint32_t, size=uint32_t, barrier=uint32_t)
cdef uint32_t cdc_offset(const uint8_t[:])
