import sys
import traceback
from CGRtools.files.RDFrw import RDFread
from ..utils.reaxys_data import Parser as ReaxysParser


parsers = dict(reaxys=ReaxysParser)


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    data_parser = parsers[kwargs['parser']]

    err = 0
    num = 0
    for num, data in enumerate(inputdata.read(), start=1):
        if num % 100 == 1:
            print("reaction: %d" % num, file=sys.stderr)
        try:
            meta = data_parser.parse(data['meta'])
        except Exception:
            err += 1
            print('reaction %d consist errors: %s' % (num, traceback.format_exc()), file=sys.stderr)
    print('%d from %d reactions processed' % (num - err, num), file=sys.stderr)

    return 0 if num and not err else 1 if num - err else 2
