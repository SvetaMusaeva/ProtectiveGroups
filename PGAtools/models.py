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
from MWUI.ORM import db, main_tables as mt, save_tables as st, data_tables as dt

User, Subscription, Model, Destination, Additive, Post, BlogPost, TeamPost, Meeting, Thesis, Email, Attachment = mt
Task, Structure, Result, Additiveset = st
Molecule, Reaction = dt



class Conditions(db.Entity):
    id = PrimaryKey(int, auto=True)
    citation = Optional(LongStr, lazy=False)
    comment = Optional(str)
    conditions = Optional(str)
    description = Optional(LongStr, lazy=False)
    pressure = Optional(str)
    product_yield = Optional(str)
    steps = Optional(str)
    temperature = Optional(str)
    time = Optional(str)
    raw_medias = Set('RawMedias')
    reaction = Required('Reactions')


class Groups(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    transform_data = Required(Json)
    group_data = Required(Json)
    reactions = Set('GroupReaction')

    def __init__(self, name, group, transform):
        transform_data = node_link_data(transform)
        group_data = node_link_data(group)
        super(Groups, self).__init__(name=name, query_leave_data=transform_data, query_remain_data=group_data)

    @property
    def group(self):
        return node_link_graph(self.group_data)

    @property
    def transform(self):
        return node_link_graph(self.transform_data)


class Molecules(db.Entity):
    id = PrimaryKey(int, auto=True)
    data = Required(Json)
    fear = Required(str, unique=True)
    fingerprint = Required(str)  # , sql_type='bit(%s)' % (2 ** FP_SIZE))
    reactions = Set('MoleculeReaction')

    def __init__(self, molecule, fingerprint=None, fear_string=None):
        data = node_link_data(molecule)

        if fear_string is None:
            fear_string = self.get_fear(molecule)
        if fingerprint is None:
            fingerprint = self.get_fingerprints([molecule])[0]

        self.__cached_structure = molecule
        self.__cached_bitstring = fingerprint
        super(Molecules, self).__init__(data=data, fear=fear_string, fingerprint=fingerprint.bin)

    @staticmethod
    def get_fear(molecule):
        return fear.get_cgr_string(molecule)

    @staticmethod
    def get_fingerprints(structures):
        f = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_STR,
                       min_length=FRAGMENT_MIN_STR, max_length=FRAGMENT_MAX_STR,
                       useformalcharge=True).get(structures)['X']

        return get_fingerprints(f)

    @property
    def structure(self):
        if self.__cached_structure is None:
            g = node_link_graph(self.data)
            g.__class__ = MoleculeContainer
            self.__cached_structure = g
        return self.__cached_structure

    @property
    def bitstring_fingerprint(self):
        if self.__cached_bitstring is None:
            self.__cached_bitstring = BitArray(bin=self.fingerprint)
        return self.__cached_bitstring

    @staticmethod
    def get_molecule(molecule):
        return Molecules.get(fear=fear.get_cgr_string(molecule))

    __cached_structure = None
    __cached_bitstring = None


class Reactions(db.Entity):
    id = PrimaryKey(int, auto=True)
    rx_id = Optional(int)
    fear = Required(str, unique=True)
    fingerprint = Required(str)  # , sql_type='bit(%s)' % (2 ** FP_SIZE))

    molecules = Set('MoleculeReaction')
    conditions = Set(Conditions, cascade_delete=True)
    groups = Set('GroupReaction')

    def __init__(self, reaction, conditions=None, fingerprint=None, fear_string=None, cgr=None,
                 substrats_fears=None, products_fears=None, **db_ids):
        if fear_string is None:
            fear_string, cgr = self.get_fear(reaction, get_cgr=True)
        elif cgr is None:
            cgr = cgr_core.getCGR(reaction)

        if fingerprint is None:
            fingerprint = self.get_fingerprints([cgr], is_cgr=True)[0]

        self.__cached_cgr = cgr
        self.__cached_structure = reaction
        self.__cached_bitstring = fingerprint
        super(Reactions, self).__init__(fear=fear_string, fingerprint=fingerprint.bin,
                                        **{x: y for x, y in db_ids.items() if y})

        new_mols = []
        batch = []
        fears = dict(substrats=iter(substrats_fears or []), products=iter(products_fears or []))
        for i, is_p in (('substrats', False), ('products', True)):
            for x in reaction[i]:
                m_fear_string = next(fears[i], fear.get_cgr_string(x))
                m = Molecules.get(fear=m_fear_string)
                if m:
                    mapping = list(next(cgr_reactor.get_cgr_matcher(m.structure, x).isomorphisms_iter()).items())
                    batch.append((m, is_p, mapping))
                else:
                    new_mols.append((x, is_p, m_fear_string))

        if new_mols:
            for fp, (x, is_p, m_fear_string) in zip(Molecules.get_fingerprints([x for x, *_ in new_mols]), new_mols):
                m = Molecules(x, fear_string=m_fear_string, fingerprint=fp)
                batch.append((m, is_p, None))

        for m, is_p, mapping in batch:
            MoleculeReaction(reaction=self, molecule=m, product=is_p, mapping=mapping)

        if conditions:
            self.__set_conditions(conditions)

    def analyse_groups(self, groups=None):
        if groups is None:
            groups = list(x for x in Groups)

    @staticmethod
    def get_fingerprints(reactions, is_cgr=False):
        cgrs = reactions if is_cgr else [cgr_core.getCGR(x) for x in reactions]
        f = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_CGR,
                       min_length=FRAGMENT_MIN_CGR, max_length=FRAGMENT_MAX_CGR,
                       cgr_dynbonds=FRAGMENT_DYNBOND_CGR, useformalcharge=True).get(cgrs)['X']

        return get_fingerprints(f)

    def __set_conditions(self, conditions):
        for c in conditions:
            media = c.pop('media', [])
            cond = Conditions(reaction=self, **c)
            for m in media:
                cond.raw_medias.add(RawMedias.get(name=m) or RawMedias(name=m))

    def set_conditions(self, conditions):
        tmp = {c.id: c.to_dict(exclude='id') for c in self.conditions}
        raw_name = left_join((c.id, rm.name) for c in Conditions if c.reaction == self for rm in c.raw_medias)
        for i, name in raw_name:
            tmp[i].setdefault('media', set()).add(name)

        available_conditions = list(tmp.values())
        to_add = []
        keys = ('product_yield', 'temperature', 'time', 'citation', 'comment',
                'conditions', 'description', 'pressure', 'steps')
        for c in conditions:
            if not any(all((ac[key] or None) == (c.get(key) or None) for key in keys)
                       and ac['media'] == set(c.get('media', [])) for ac in available_conditions):
                to_add.append(c)

        self.__set_conditions(to_add)
        return len(to_add)

    @staticmethod
    def get_fear(reaction, get_cgr=False):
        cgr = cgr_core.getCGR(reaction)
        cgr_string = fear.get_cgr_string(cgr)
        return (cgr_string, cgr) if get_cgr else cgr_string

    @property
    def cgr(self):
        if self.__cached_cgr is None:
            self.__cached_cgr = cgr_core.getCGR(self.structure)
        return self.__cached_cgr

    @property
    def structure(self):
        if self.__cached_structure is None:
            r = ReactionContainer()
            for m in self.molecules.order_by(lambda x: x.id):
                r['products' if m.product else 'substrats'].append(
                    relabel_nodes(m.molecule.structure, dict(m.mapping)) if m.mapping else m.molecule.structure)
            self.__cached_structure = r
        return self.__cached_structure

    @property
    def bitstring_fingerprint(self):
        if self.__cached_bitstring is None:
            self.__cached_bitstring = BitArray(bin=self.fingerprint)
        return self.__cached_bitstring

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

    @staticmethod
    def get_reaction(reaction):
        cgr = cgr_core.getCGR(reaction)
        return Reactions.get(fear=fear.get_cgr_string(cgr))

    @staticmethod
    def get_reactions_with_molecule(molecule, product=None):
        if product is None:
            q = left_join(r for m in Molecules if m.fear == fear.get_cgr_string(molecule) for rs in m.reactions
                          for r in rs.reactions)
        else:
            q = left_join(r for m in Molecules if m.fear == fear.get_cgr_string(molecule) for rs in m.reactions if
                          rs.product == product for r in rs.reactions)
        return list(q)

    @staticmethod
    def get_reactions_with_components(products=None, substrats=None):
        collector = {}
        if products is not None:
            p_fear = [fear.get_cgr_string(x) for x in products]
            for x in p_fear:
                collector[x] = set()

            for m, r in left_join((m.fear, r) for m in Molecules if m.fear in p_fear
                                  for rs in m.reactions if rs.product for r in rs.reactions):
                collector[m].add(r)

        if substrats is not None:
            s_fear = [fear.get_cgr_string(x) for x in substrats]
            for x in s_fear:
                collector[fear.get_cgr_string(x)] = set()

            for m, r in left_join((m.fear, r) for m in Molecules if m.fear in s_fear
                                  for rs in m.reactions if not rs.product for r in rs.reactions):
                collector[m].add(r)

        return list(reduce(set.intersection, collector.values()))

    __cached_structure = None
    __cached_cgr = None
    __cached_conditions = None
    __cached_bitstring = None


class MoleculeReaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    reaction = Required(Reactions)
    molecule = Required(Molecules)
    product = Required(bool, default=False)
    mapping = Required(Json)


class Tags(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    medias = Set('Medias')


class Medias(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    raw_medias = Set('RawMedias')
    tags = Set(Tags)

    @property
    def tag_names(self):
        return [x.name for x in self.tags]

    def update_tags(self, tags):
        ns = set(tags)
        os = set(self.tag_names)

        self.tags.remove(x for x in self.tags if x.name in os.difference(ns))
        self.tags.add(Tags.get(name=x) or Tags(name=x) for x in ns.difference(os))


class RawMedias(db.Entity):
    id = PrimaryKey(int, auto=True)
    conditions = Set(Conditions)
    name = Required(str, unique=True)
    media = Optional(Medias)

    def update_media(self, name):
        self.media = Medias.get(name=name) or Medias(name=name)


class GroupReaction(db.Entity):
    group = Required(Groups)
    reaction = Required(Reactions)
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    fingerprint = Optional(str)  # , sql_type='bit(%s)' % (2 ** FP_SIZE))
    PrimaryKey(group, reaction)


sql_debug(DEBUG)
db.bind("sqlite", "database.sqlite")  # 'postgres', user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)
db.generate_mapping(create_tables=CREATE_TABLES)
