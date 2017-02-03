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
from pony.orm import Database, PrimaryKey, Optional, Required, Set, Json
from MWUI.ORM import db as mwdb, main_tables as mt, data_tables as dt
from MWUI.config import FP_SIZE
from CGRtools.CGRreactor import CGRreactor
from CGRtools.files import MoleculeContainer, ReactionContainer
from CGRtools.CGRcore import CGRcore
from .config import DEBUG, GroupStatus

User, *_ = mt
Molecule, Reaction, Conditions = dt
db = Database()
cgr_core = CGRcore()
cgr_rctr = CGRreactor()


class Group(db.Entity):
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

    def analyse(self, reactions):
        out = []
        batch = []
        for r in reactions:
            report = dict(cpg=0, rpg=0, tpg=0)
            gm = cgr_rctr.get_cgr_matcher(union_all(r.structure.substrats), self.group)
            uniq_groups = {tuple(sorted(m)) for m in gm.subgraph_isomorphisms_iter()}

            if uniq_groups:
                cgr = cgr_core.getCGR(r.structure)
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
                            GroupReaction(group=self, remain=True, reaction=reaction.id, fingerprint=)
                            report['rpg'] += 1
                        else:
                            batch.append(('transform', r.id, rrr))

                            report['tpg'] += 1

                out.append(report)
        for g in batch:
            GroupReaction(group=self, transform=True, reaction=reaction.id, fingerprint=)
        return out

    __cached_group = None
    __cached_transform = None


class Reactions(db.Entity):
    def get_conditions(self):
        if self.__cached_conditions is None:
            result = {}

            for condition in self.conditions:
                data = condition.to_dict(exclude='id')
                data['media'] = {}
                result[condition.id] = data

            clear_list = []
            mids = set()
            clear_name = left_join((c.id, m.name, m.id) for c in Conditions if c.reaction == self
                                   for rm in c.raw_medias if rm.media for m in rm.media)
            for *id_name, mid in clear_name:
                mids.add(mid)
                clear_list.append(id_name)

            tags_list = defaultdict(list)
            tags_name = left_join((m.name, t.name) for m in Medias if m.id in mids for t in m.tags)
            for m, t in tags_name:
                tags_list[m].append(t)

            raw_name = left_join((c.id, rm.name) for c in Conditions if c.reaction == self
                                 for rm in c.raw_medias if not rm.media)
            for i, name in chain(clear_list, raw_name):
                result[i]['media'][name] = tags_list[name]
            self.__cached_conditions = list(result.values())

        return self.__cached_conditions


class RawMedia(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    media = Optional('Media')

    def update_media(self, name):
        self.media = Media.get(name=name) or Media(name=name)

    @staticmethod
    def get_media_mapping():

        return


class Media(db.Entity):
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
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    medias = Set('Media')


class GroupReaction(db.Entity):
    group = Required('Group')
    reaction = Required(int)
    status_data = Required(int, default=0)
    fingerprint = Required(str) if DEBUG else Required(str, sql_type='bit(%s)' % (2 ** FP_SIZE))
    PrimaryKey(group, reaction)

    def __init__(self, reaction, group, status=GroupStatus.CLEAVAGE, fingerprint=None):
        if fingerprint is None:
            fingerprint =

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
