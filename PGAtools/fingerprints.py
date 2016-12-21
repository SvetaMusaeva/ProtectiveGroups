from bitstring import BitArray
from .config import FP_SIZE, FP_ACTIVE_BITS
from hashlib import md5


def get_fingerprint(s):
    fp = BitArray(2 ** FP_SIZE)
    for k, v in s.items():
        if v:
            b = BitArray(md5(k.encode()).digest())
            for r in range(FP_ACTIVE_BITS):
                fp[b[r * FP_SIZE: (r + 1) * FP_SIZE].uint] = True
    return fp
