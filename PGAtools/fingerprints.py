from bitstring import BitArray
from sklearn.neighbors.ball_tree import BallTree
from .config import FP_SIZE, FP_ACTIVE_BITS
from hashlib import md5


def get_fingerprints(df):
    bits_map = {}
    for fragment in df.columns:
        b = BitArray(md5(fragment.encode()).digest())
        bits_map[fragment] = [b[r * FP_SIZE: (r + 1) * FP_SIZE].uint for r in range(FP_ACTIVE_BITS)]

    result = []
    for _, s in df.iterrows():
        active_bits = set()
        for k, v in s.items():
            if v:
                active_bits.update(bits_map[k])

        fp = BitArray(2 ** FP_SIZE)
        fp.set(True, active_bits)
        result.append(fp)

    return result

