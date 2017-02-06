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
from networkx.readwrite.json_graph import node_link_graph, node_link_data
from networkx import union_all
from bitstring import BitArray
from itertools import count
from pony.orm import Database, PrimaryKey, Optional, Required, Set, Json
from MWUI.ORM import main_tables as mt, data_tables as dt
from MWUI.config import FP_SIZE, DATA_STEREO, DATA_ISOTOPE
from CGRtools.CGRreactor import CGRreactor
from CGRtools.files import MoleculeContainer
from CGRtools.CGRcore import CGRcore
from CGRtools.FEAR import FEAR
from .config import DEBUG, GroupStatus, DB_DATA


User, *_ = mt
Molecule, Reaction, Conditions = dt
db = Database()
cgr_core = CGRcore()
cgr_rctr = CGRreactor(stereo=DATA_STEREO, isotope=DATA_ISOTOPE, hyb=True, neighbors=True)
fear = FEAR(stereo=DATA_STEREO)


class Group(db.Entity):
    _table_ = '%s_group' % DB_DATA if DEBUG else (DB_DATA, 'group')
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    function = Required(str)
    transform_data = Required(Json)
    group_data = Required(Json)
    reactions = Set('GroupReaction')

    def __init__(self, name, function, transformation):
        sub = union_all(transformation.substrats)
        cgr = cgr_core.getCGR(transformation)
        super(Group, self).__init__(name=name, function=function,
                                    transform_data=node_link_data(cgr), group_data=node_link_data(sub))

    @property
    def group(self):
        if self.__cached_group is None:
            g = node_link_graph(self.group_data)
            g.__class__ = MoleculeContainer
            self.__cached_group = g
        return self.__cached_group

    @property
    def transform(self):
        if self.__cached_transform is None:
            g = node_link_graph(self.transform_data)
            g.__class__ = MoleculeContainer
            self.__cached_transform = g
        return self.__cached_transform

    @property
    def __center_atoms(self):
        if self.__cached_center is None:
            self.__cached_center = fear.get_center_atoms(self.transform)
        return self.__cached_center

    def analyse(self, reactions):
        out = []
        batch = []
        for r in reactions:
            report = dict(cpg=0, rpg=0, tpg=0)
            gm = cgr_rctr.get_cgr_matcher(union_all(r.substrats), self.group)
            uniq_groups = {tuple(sorted(m)) for m in gm.subgraph_isomorphisms_iter()}

            if uniq_groups:
                cgr = cgr_core.getCGR(r)
                for m in uniq_groups:
                    cgrs = cgr.subgraph(m)
                    gm = cgr_rctr.get_cgr_matcher(cgrs, self.transform)
                    if gm.is_isomorphic():
                        batch.append(('cleavage', r.id, rrr))
                        report['cpg'] += 1
                    else:
                        gm = cgr_rctr.get_cgr_matcher(cgrs, self.group)
                        if gm.is_isomorphic():
                            batch.append(('remain', r.id, rrr))
                            report['rpg'] += 1
                        else:
                            batch.append(('transform', r.id, rrr))

                            report['tpg'] += 1

                out.append(report)
        return []

    def analyse_db(self, reactions=None):
        if reactions is None:
            result = []
            page = count(1)
            while True:
                reactions = Reaction.select().order_by(Reaction.id).page(next(page), pagesize=50)
                result.extend(self.analyse(reactions))
        else:
            result = self.analyse(reactions)

        report = count()
        for r, status, fprint in result:
            if not GroupReaction.exists(group=self, reaction=r.id, status_data=status.value, fingerprint=fprint.bin):
                GroupReaction(r, self, fprint, status=status)
                next(report)

        return next(report)

    __cached_group = None
    __cached_transform = None
    __cached_center = None


class RawMedia(db.Entity):
    _table_ = '%s_raw_media' % DB_DATA if DEBUG else (DB_DATA, 'raw_media')
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    media = Optional('Media')

    def update_media(self, name):
        self.media = Media.get(name=name) or Media(name=name)

    @staticmethod
    def get_media_mapping():

        return


class Media(db.Entity):
    _table_ = '%s_media' % DB_DATA if DEBUG else (DB_DATA, 'media')
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    raw = Set('RawMedia')
    tags = Set('Tag')

    @property
    def tag_names(self):
        return [x.name for x in self.tags]

    def update_tags(self, tags):
        new_tags = set(tags)
        old_tags = set(self.tag_names)

        self.tags.remove(x for x in self.tags if x.name in old_tags.difference(new_tags))
        self.tags.add(Tag.get(name=x) or Tag(name=x) for x in new_tags.difference(old_tags))


class Tag(db.Entity):
    _table_ = '%s_tag' % DB_DATA if DEBUG else (DB_DATA, 'tag')
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    medias = Set('Media', table='%s_media_tag' % DB_DATA if DEBUG else (DB_DATA, 'media_tag'))


class GroupReaction(db.Entity):
    _table_ = '%s_group_reaction' % DB_DATA if DEBUG else (DB_DATA, 'group_reaction')
    group = Required('Group')
    reaction = Required(int)
    status_data = Required(int, default=0)
    fingerprint = Required(str) if DEBUG else Required(str, sql_type='bit(%s)' % (2 ** FP_SIZE))
    PrimaryKey(group, reaction)

    def __init__(self, reaction, group, fingerprint, status=GroupStatus.CLEAVAGE):
        super(GroupReaction, self).__init__(reaction=reaction.id, group=group, status_data=status.value,
                                            fingerprint=fingerprint.bin)

    @property
    def bitstring_fingerprint(self):
        if self.__cached_bitstring is None:
            self.__cached_bitstring = BitArray(bin=self.fingerprint)
        return self.__cached_bitstring

    @property
    def status(self):
        return GroupStatus(self.status_data)

    __cached_bitstring = None
