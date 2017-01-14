import sys
from itertools import zip_longest, count
from pony.orm import db_session
from CGRtools.files.RDFrw import RDFread
from ..utils.reaxys_data import Parser as ReaxysParser
from ..models import Reactions, Molecules, Groups


parsers = dict(reaxys=ReaxysParser)


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    data_parser = parsers[kwargs['parser']]()

    raw_data = count()
    clean_data = count()
    added_data = count()
    upd_data = count()

    with db_session:
        groups = list(x for x in Groups)

    for nums, chunk in enumerate(zip_longest(*[inputdata] * kwargs['chunk']), start=1):
        print("chunk: %d" % nums, file=sys.stderr)

        cleaned = []
        for r in chunk:
            if r is not None:
                next(raw_data)
                try:
                    rs, cgr = Reactions.get_fear(r, get_cgr=True)
                    cleaned.append((r, rs, cgr))
                except:
                    pass

        rfps = Reactions.get_fingerprints([x for *_, x in cleaned], is_cgr=True)

        molecules = []
        with db_session:
            for r, _ in cleaned:
                next(clean_data)
                for i in ('substrats', 'products'):
                    for m in r[i]:
                        ms = Molecules.get_fear(m)
                        if not Molecules.exists(string=ms):
                            molecules.append((m, ms))

        mfps = Molecules.get_fingerprints([m for m, _ in molecules])

        with db_session:
            for (m, ms), mf in zip(molecules, mfps):
                Molecules(m, fingerprint=mf, fear_string=ms)

            for (r, rs, cgr), r_fp in zip(cleaned, rfps):
                reaction = Reactions.get(string=rs)
                meta = data_parser.parse(r['meta'])
                if not reaction:
                    next(added_data)
                    reaction = Reactions(r, conditions=meta['rxd'], rx_id=meta['rx_id'], fingerprint=r_fp,
                                         fear_string=rs, cgr=cgr)
                    reaction.analyse_groups(groups=groups)
                else:
                    if reaction.set_conditions(meta['rxd']):
                        next(upd_data)

    print('Data processed\nRaw: %d, Clean: %d, Added: %d, Updated: %d' % next(zip(raw_data, clean_data,
                                                                                  added_data, upd_data)))
