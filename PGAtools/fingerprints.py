from bitstring import BitArray


fp_size = 2048
# пока общий для реакций и молекул
fp_header = {v: (int(k[:-1]) * 2 % fp_size, int(k[:-1]) * 3 % fp_size) for k, v in (i.split() for i in open(header))}


def get_fingerprint(s):
    fp = BitArray(fp_size)
    for k, v in s:
        if v:
            b1, b2 = fp_header[k]
            fp[b1] = fp[b2] = 1
    return fp
