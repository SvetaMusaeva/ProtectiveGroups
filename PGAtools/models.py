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
from pony.orm import Database, PrimaryKey, Optional, Required, Set, Json
from MWUI.ORM import db as mwdb, main_tables as mt, data_tables as dt
from MWUI.config import FP_SIZE
from CGRtools.CGRreactor import CGRreactor
from CGRtools.CGRcore import CGRcore
from .config import DEBUG


User, *_ = mt
Molecule, Reaction, Conditions = dt
db = Database()
cgr_core = CGRcore()


class Group(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    protect = Required(str)
    transform_data = Required(Json)
    group_data = Required(Json)
    reactions = Set('GroupReaction')

    def __init__(self, name, protect, transformation):
        mr = cgr_core.merge_mols(transformation)

        transform_data = node_link_data(transform)
        group_data = node_link_data(mr['substrats'])
        super(Group, self).__init__(name=name, protect=protect,
                                    transform_data=transform_data, group_data=group_data)

    @property
    def group(self):
        if self.__cached_group is None:
            self.__cached_group = node_link_graph(self.group_data)
        return self.__cached_group

    @property
    def transform(self):
        if self.__cached_transform is None:
            self.__cached_transform = node_link_graph(self.transform_data)
        return self.__cached_transform

    __cached_group = None
    __cached_transform = None


class Reactions(db.Entity):
    id = PrimaryKey(int, auto=True)
    rx_id = Optional(int)
    fear = Required(str, unique=True)
    fingerprint = Required(str)  # , sql_type='bit(%s)' % (2 ** FP_SIZE))

    molecules = Set('MoleculeReaction')
    conditions = Set(Conditions, cascade_delete=True)
    groups = Set('GroupReaction')

    def analyse_groups(self, groups=None):
        if groups is None:
            groups = list(x for x in Groups)

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
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    fingerprint = Required(str) if DEBUG else Required(str, sql_type='bit(%s)' % (2 ** FP_SIZE))
    PrimaryKey(group, reaction)
