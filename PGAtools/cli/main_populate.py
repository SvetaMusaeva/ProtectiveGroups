import sys
from itertools import zip_longest, count
from pony.orm import db_session
from CGRtools.files.RDFrw import RDFread
from ..utils.reaxys_data import Parser as ReaxysParser
from ..models import Reactions, Molecules


parsers = dict(reaxys=ReaxysParser)


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    data_parser = parsers[kwargs['parser']]()

    raw_data = count()
    clean_data = count()
    added_data = count()
    upd_data = count()
    for nums, chunk in enumerate(zip_longest(*[inputdata.read()] * kwargs['chunk']), start=1):
        print("chunk: %d" % nums, file=sys.stderr)

        cleaned = []
        for r in chunk:
            if r is not None:
                next(raw_data)
                try:
                    rs = Reactions.generate_string(r)
                    cleaned.append((r, rs))
                except:
                    pass

        molecules = []
        for x, _ in cleaned:
            next(clean_data)
            for i in ('substrats', 'products'):
                molecules.extend(x[i])

        with db_session:
            for mol, m_fp in zip(molecules, Molecules.get_fingerprints(molecules)):
                if not Molecules.exists(string=Molecules.generate_string(mol)):
                    Molecules(mol, fingerprint=m_fp)

            for (r, rs), r_fp in zip(cleaned, Reactions.get_fingerprints(x for x, _ in cleaned)):
                reaction = Reactions.get(string=rs)
                meta = data_parser.parse(r['meta'])
                if not reaction:
                    next(added_data)
                    Reactions(r, conditions=meta['rxd'], rx_id=meta['rx_id'], fingerprint=r_fp)
                else:
                    if reaction.set_conditions(meta['rxd']):
                        next(upd_data)

    print('Data processed\nRaw: %d, Clean: %d, Added: %d, Updated: %d' % next(zip(raw_data, clean_data,
                                                                                  added_data, upd_data)))
