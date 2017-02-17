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
from itertools import count
from pony.orm import db_session
from ..models import Group
from CGRtools.files.RDFrw import RDFread


def groups_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    groups = count()
    found = 0
    with db_session:
        for r in inputdata:
            pg = r.meta['protective_group']
            fg = r.meta['functional_group']
            r.meta.clear()
            if not Group.exists(name=pg, function=fg):
                next(groups)
                g = Group(pg, fg, r)
                found += g.analyse_db()

    print('Groups processed\nNew: %d, Found match: %d' % (next(groups), found))
