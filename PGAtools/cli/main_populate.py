import sys
import traceback
from CGRtools.files.RDFrw import RDFread
from CGRtools.files.SDFrw import SDFwrite
from CGRtools.CGRpreparer import CGRcombo


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    outputdata = SDFwrite(kwargs['output'], extralabels=kwargs['save_extralabels'])

    worker = CGRcombo(cgr_type=kwargs['cgr_type'], extralabels=kwargs['extralabels'], speed=kwargs['speed'],
                      b_templates=kwargs['b_templates'], m_templates=kwargs['m_templates'],
                      stereo=kwargs['stereo'], isotop=kwargs['isotop'], element=kwargs['element'], deep=kwargs['deep'])

    err = 0
    num = 0
    for num, data in enumerate(inputdata.read(), start=1):
        if num % 100 == 1:
            print("reaction: %d" % num, file=sys.stderr)
        try:
            a = worker.getCGR(data)
            outputdata.write(a)
        except Exception:
            err += 1
            print('reaction %d consist errors: %s' % (num, traceback.format_exc()), file=sys.stderr)
    print('%d from %d reactions condensed' % (num - err, num), file=sys.stderr)

    return 0 if num and not err else 1 if num - err else 2