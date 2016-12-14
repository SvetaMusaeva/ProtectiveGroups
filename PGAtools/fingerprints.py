from bitstring import BitArray
from .config import FP_SIZE, FP_HEADER_STR, FP_HEADER_CGR

# пока общий для реакций и молекул
fp_header_str = {v: (int(k[:-1]) * 2 % FP_SIZE, int(k[:-1]) * 3 % FP_SIZE)
                 for k, v in (i.split() for i in open(FP_HEADER_STR))}
fp_header_cgr = {v: (int(k[:-1]) * 2 % FP_SIZE, int(k[:-1]) * 3 % FP_SIZE)
                 for k, v in (i.split() for i in open(FP_HEADER_CGR))}


def get_fingerprint(s, reaction=False):
    fp = BitArray(FP_SIZE)
    for k, v in s.items():
        if v:
            b1, b2 = fp_header_cgr[k] if reaction else fp_header_str[k]
            fp[b1] = fp[b2] = 1
    return fp
