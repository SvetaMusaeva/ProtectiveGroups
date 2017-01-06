from bitstring import BitArray
from sklearn.neighbors.ball_tree import BallTree
from sklearn.neighbors.dist_metrics import PyFuncDistance
from .config import FP_SIZE, FP_ACTIVE_BITS
from hashlib import md5


def get_fingerprint(s):
    active_bits = set()
    for k, v in s.items():
        if v:
            b = BitArray(md5(k.encode()).digest())
            for r in range(FP_ACTIVE_BITS):
                active_bits.add(b[r * FP_SIZE: (r + 1) * FP_SIZE].uint)

    fp = BitArray(2 ** FP_SIZE)
    fp.set(True, active_bits)
    return fp
