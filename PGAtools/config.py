from os import path

# dynamic
FP_SIZE = 2048
FP_HEADER_STR = ''
FP_HEADER_CGR = ''
FRAGMENTOR_VERSION = '15.36'
FRAGMENT_TYPE_STR = 3
FRAGMENT_MIN_STR = 2
FRAGMENT_MAX_STR = 10
FRAGMENT_TYPE_CGR = 3
FRAGMENT_MIN_CGR = 2
FRAGMENT_MAX_CGR = 10
FRAGMENT_DYNBOND_CGR = 1


params = ('FP_SIZE','FP_HEADER_STR', 'FP_HEADER_CGR', 'FRAGMENTOR_VERSION','FRAGMENT_TYPE_STR', 'FRAGMENT_MIN_STR',
          'FRAGMENT_MAX_STR', 'FRAGMENT_TYPE_CGR', 'FRAGMENT_MIN_CGR', 'FRAGMENT_MAX_CGR', 'FRAGMENT_DYNBOND_CGR')

if not path.exists(path.join(path.dirname(__file__), "config.ini")):
    with open(path.join(path.dirname(__file__), "config.ini"), 'w') as f:
        f.write('\n'.join('%s = %s' % (x, y) for x, y in globals().items()
                          if x in params))

with open(path.join(path.dirname(__file__), "config.ini")) as f:
    for line in f:
        try:
            k, v = line.split('=')
            k = k.strip()
            v = v.strip()
            if k in params:
                globals()[k] = int(v) if v.isdigit() else v
        except:
            pass
