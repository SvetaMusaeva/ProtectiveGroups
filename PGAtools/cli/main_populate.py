# -*- coding: utf-8 -*-
#
#  Copyright 2016, 2017 Ramil Nugmanov <stsouko@live.ru>
#  Copyright 2016 Svetlana Musaeva <sveta_musaeva.95@mail.ru>
#  This file is part of PGAtools.
#
#  PGAtools is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
import sys
from itertools import zip_longest, count
from pony.orm import db_session, commit
from CGRtools.files.RDFrw import RDFread
from ..utils.reaxys_data import Parser as ReaxysParser
from ..models import Reaction, Molecule, Group, Conditions, User, RawMedia


parsers = dict(reaxys=ReaxysParser)


def populate_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    data_parser = parsers[kwargs['parser']]()

    raw_data = count()
    clean_data = count()
    added_data = count()
    upd_data = count()

    for nums, chunk in enumerate(zip_longest(*[inputdata] * kwargs['chunk']), start=1):
        print("chunk: %d" % nums, file=sys.stderr)

        cleaned = []
        molecules = []
        lrms = []
        for r in chunk:
            if r is None:
                break

            next(raw_data)
            try:
                rs, cgr = Reaction.get_fear(r, get_cgr=True)
                rms = dict(substrats=[], products=[])
                for i in ('substrats', 'products'):
                    for m in r[i]:
                        ms = Molecule.get_fear(m)
                        rms[i].append(ms)
                        molecules.append((m, ms))

                lrms.append(rms)
                cleaned.append((r, rs, cgr))
                next(clean_data)
            except:
                pass

        rfps = Reaction.get_fingerprints([x for *_, x in cleaned], is_cgr=True)
        mfps = Molecule.get_fingerprints([m for m, _ in molecules])

        with db_session:
            user = User[1]
            groups = list(Group.select())

            for (m, ms), mf in zip(molecules, mfps):
                if not Molecule.exists(fear=ms):
                    Molecule(m, user, fingerprint=mf, fear_string=ms)

            for (r, rs, cgr), r_fp, rms in zip(cleaned, rfps, lrms):
                reaction = Reaction.get(string=rs)
                meta = data_parser.parse(r['meta'])
                if not reaction:
                    next(added_data)
                    reaction = Reaction(r, user, special=dict(rx_id=meta['rx_id'], db_name='protective_groups'),
                                        fingerprint=r_fp, fear_string=rs, cgr=cgr,
                                        substrats_fears=rms['substrats'], products_fears=rms['products'])
                    commit()
                    for g in groups:
                        g.analyse(reaction)

                media = set()
                for c in meta['rxd']:
                    if not Conditions.exists(data=c, reaction=reaction):
                        Conditions(user=user, data=c, reaction=reaction)
                        media.update(c['media'])
                        next(upd_data)

                for m in media:
                    if not RawMedia.exists(name=m):
                        RawMedia(name=m)

    print('Data processed\nRaw: %d, Clean: %d, Added: %d, Conditions: %d' % next(zip(raw_data, clean_data,
                                                                                     added_data, upd_data)))
