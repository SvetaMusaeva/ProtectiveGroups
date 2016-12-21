import sys
from itertools import zip_longest
from pony.orm import db_session
from CGRtools.files.RDFrw import RDFread
from ..utils.reaxys_data import Parser as ReaxysParser
from ..models import Reactions, Molecules


parsers = dict(reaxys=ReaxysParser)


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    data_parser = parsers[kwargs['parser']]()

    for nums, chunk in enumerate(zip_longest(*[inputdata.read()] * kwargs['chunk']), start=1):
        print("chunk: %d" % nums, file=sys.stderr)

        if None in chunk:
            chunk = [x for x in chunk if x is not None]

        molecules = []
        for x in chunk:
            for i in ('substrats', 'products'):
                molecules.extend(x[i])

        with db_session:
            for mol, m_fp in zip(molecules, Molecules.get_fingerprints(molecules)):
                if not Molecules.exists(string=Molecules.generate_string(mol)):
                    Molecules(mol, fingerprint=m_fp)

            for r, r_fp in zip(chunk, Reactions.get_fingerprints(chunk)):
                reaction = Reactions.get(string=Reactions.generate_string(r))
                meta = data_parser.parse(r['meta'])
                if not reaction:
                    Reactions(r, conditions=meta['rxd'], rx_id=meta['rx_id'], fingerprint=r_fp)
                else:
                    reaction.set_conditions(meta['rxd'])
