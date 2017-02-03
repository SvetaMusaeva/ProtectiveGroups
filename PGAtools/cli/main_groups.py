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
from pony.orm import db_session, select
from ..models import Group, Reaction
from CGRtools.files.RDFrw import RDFread
from CGRtools.CGRcore import CGRcore
import networkx as nx

cgr_core = CGRcore()


def groups_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    groups = []
    with db_session:
        for r in inputdata:
            name = r.meta['name']
            r.meta.clear()
            if not Group.exists(name=name):
                g = Group(name, nx.union_all(r['substrats']), cgr_core.getCGR(r))
                # todo: indexation!
