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
from collections import OrderedDict
from networkx.readwrite.json_graph import node_link_graph, node_link_data
from networkx import union_all
from bitstring import BitArray
from itertools import count
from pony.orm import Database, PrimaryKey, Optional, Required, Set, Json, db_session
from MWUI.models import data_tables
from MWUI.config import FP_SIZE, DATA_STEREO, DATA_ISOTOPE
from CGRtools.CGRreactor import CGRreactor
from CGRtools.files import MoleculeContainer
from CGRtools.CGRcore import CGRcore
from CGRtools.FEAR import FEAR
from .config import DEBUG, GroupStatus, DB_DATA, DB_MWUI_DATA, FP_DEEP


Molecule, Reaction, Conditions = data_tables[DB_MWUI_DATA]
db = Database()
cgr_core = CGRcore(extralabels=True)
cgr_core_query = CGRcore()
cgr_rctr = CGRreactor(stereo=DATA_STEREO, isotope=DATA_ISOTOPE, hyb=True, neighbors=True)
fear = FEAR(stereo=DATA_STEREO, deep=FP_DEEP)

_node_marks = ['sp_%s' % mark for mark in ('neighbors', 'hyb', 'stereo', 'charge')]
_edge_marks = ['sp_%s' % mark for mark in ('bond', 'stereo')]


class Group(db.Entity):
    _table_ = '%s_group' % DB_DATA if DEBUG else (DB_DATA, 'group')
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    function = Required(str)
    transform_data = Required(Json)
    group_data = Required(Json)
    last_reaction = Required(int, default=0)
    reactions = Set('GroupReaction')

    def __init__(self, name, function, transformation):
        sub = union_all(transformation.substrats)
        cgr = cgr_core_query.getCGR(transformation)
        for _, attr in cgr.nodes(data=True):
            for m in _node_marks:
                attr.pop(m, None)
        for *_, attr in cgr.edges(data=True):
            for m in _edge_marks:
                attr.pop(m, None)
        super(Group, self).__init__(name=name, function=function, transform_data=node_link_data(cgr),
                                    group_data=node_link_data(sub))

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
            cgr_core.update_sp_marks(g, copy=False)
            self.__cached_transform = g
        return self.__cached_transform

    @property
    def __center_atoms(self):
        if self.__cached_center is None:
            self.__cached_center = fear.get_center_atoms(self.transform)
        return self.__cached_center

    def analyse(self, reactions):
        results = []
        out = []
        for r in reactions:
            substrats_union = cgr_core.set_labels(union_all(r.substrats))
            uniq_groups = OrderedDict()
            gm = cgr_rctr.get_cgr_matcher(substrats_union, self.group)
            for m in gm.subgraph_isomorphisms_iter():
                group = tuple(sorted(m))
                if group not in uniq_groups:
                    uniq_groups[group] = fear.get_environment(substrats_union,
                                                              [x for x, y in m.items() if y in self.__center_atoms])
            results.append(uniq_groups)

        tmp = [x for g in results for x in g.values()]
        fingerprints = iter(Molecule.get_fingerprints(tmp) if tmp else [])

        for r, uniq_groups in zip(reactions, results):
            report = {GroupStatus.CLEAVAGE: [], GroupStatus.REMAIN: [], GroupStatus.TRANSFORM: []}
            if uniq_groups:
                cgr = cgr_core.getCGR(r)
                for m, fp in zip(uniq_groups, fingerprints):
                    cgrs = cgr.subgraph(m)
                    gm = cgr_rctr.get_cgr_matcher(cgrs, self.transform)
                    if gm.is_isomorphic():
                        report[GroupStatus.CLEAVAGE].append(fp)
                    else:
                        gm = cgr_rctr.get_cgr_matcher(cgrs, self.group)
                        if gm.is_isomorphic():
                            report[GroupStatus.REMAIN].append(fp)
                        else:
                            report[GroupStatus.TRANSFORM].append(fp)
            out.append(report)

        return out

    def analyse_db(self, reactions=None):
        if reactions is None:
            report = 0
            last_reaction = self.last_reaction
            for page in count(1):
                with db_session:
                    r = Reaction.select(lambda x: x.id > last_reaction).order_by(Reaction.id).page(page, pagesize=50)
                    if not r:
                        break

                    group = Group[self.id]
                    report += self.__populate(group, r, self.analyse([x.structure for x in r]))
                    last_reaction = r[-1].id
                    group.last_reaction = last_reaction
        else:
            with db_session:
                group = Group[self.id]
                report = self.__populate(group, reactions, self.analyse([x.structure for x in reactions]), check=True)
                max_id = max(x.id for x in reactions)

                if group.last_reaction < max_id:
                    group.last_reaction = max_id

        return report

    @staticmethod
    def __populate(group, reactions, results, check=False):
        report = count()
        for r, res in zip(reactions, results):
            for status, fps in res.items():
                for fp, _ in zip(fps, report):
                    if not check or not GroupReaction.exists(group=group, reaction=r.id, status_data=status.value,
                                                             fingerprint=fp.bin):
                        GroupReaction(r, group, fp, status=status)

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
    id = PrimaryKey(int, auto=True)
    group = Required('Group')
    reaction = Required(int)
    status_data = Required(int, default=0)
    fingerprint = Required(str) if DEBUG else Required(str, sql_type='bit(%s)' % (2 ** FP_SIZE))

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
