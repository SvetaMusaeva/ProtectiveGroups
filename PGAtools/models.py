from pony.orm import *
from collections import defaultdict
from networkx import relabel_nodes
from bitstring import BitArray
from networkx.readwrite.json_graph import node_link_graph, node_link_data
from CGRtools.FEAR import FEAR
from CGRtools.CGRreactor import CGRreactor
from CGRtools.CGRcore import CGRcore
from itertools import chain
from MODtools.descriptors.fragmentor import Fragmentor
from .fingerprints import get_fingerprint
from .config import (FRAGMENTOR_VERSION, FRAGMENT_TYPE_CGR, FRAGMENT_MIN_CGR,
                     FRAGMENT_MAX_CGR, FRAGMENT_TYPE_STR, FRAGMENT_MIN_STR, FRAGMENT_MAX_STR, FRAGMENT_DYNBOND_CGR)


db = Database()
fear = FEAR()
cgr_core = CGRcore()
cgr_reactor = CGRreactor()


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
    string = Required(str, unique=True)
    fingerprint = Required(bytes)
    reactions = Set('MoleculeReaction')

    def __init__(self, structure, fingerprint=None):
        structure_string = self.generate_string(structure)
        data = node_link_data(structure)

        if fingerprint is None:
            fingerprint = self.get_fingerprints([structure])[0]

        self.__cached_structure = structure
        super(Molecules, self).__init__(data=data, string=structure_string, fingerprint=fingerprint.bytes)

    @staticmethod
    def generate_string(structure):
        return fear.getreactionhash(structure)

    @staticmethod
    def get_fingerprints(structures):
        f = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_STR,
                       min_length=FRAGMENT_MIN_STR, max_length=FRAGMENT_MAX_STR,
                       useformalcharge=True).get(structures)['X']

        fingerprints = []
        for _, s in f.iterrows():
            fingerprints.append(get_fingerprint(s))

        return fingerprints

    @property
    def structure(self):
        if self.__cached_structure is None:
            self.__cached_structure = node_link_graph(self.data)
        return self.__cached_structure

    @property
    def bitstring_fingerprint(self):
        return BitArray(self.fingerprint)

    __cached_structure = None


class Reactions(db.Entity):
    id = PrimaryKey(int, auto=True)
    rx_id = Optional(int)
    string = Required(str, unique=True)
    fingerprint = Required(bytes)

    molecules = Set('MoleculeReaction')
    conditions_db = Set(Conditions, cascade_delete=True)
    groups = Set('GroupReaction')

    def __init__(self, reaction, conditions=None, fingerprint=None, **db_ids):
        cgr_string, cgr = self.generate_string(reaction, get_cgr=True)

        if fingerprint is None:
            fingerprint = self.get_fingerprints([cgr], is_cgr=True)[0]

        self.__cached_cgr = cgr
        self.__cached_structure = reaction
        super(Reactions, self).__init__(string=cgr_string, fingerprint=fingerprint.bytes,
                                        **{x: y for x, y in db_ids.items() if y})

        for i, is_p in (('substrats', False), ('products', True)):
            for x in reaction[i]:
                s = Molecules.get(string=fear.getreactionhash(x)) or Molecules(x)

                MoleculeReaction(reaction=self, molecule=s, product=is_p,
                                  mapping=next(cgr_reactor.spgraphmatcher(s.structure, x).isomorphisms_iter()))

        self.__set_conditions(conditions or [])

    def analyse_groups(self, groups=None):
        if groups is None:
            groups = list(x for x in Groups)


    @staticmethod
    def get_fingerprints(reactions, is_cgr=False):
        cgrs = reactions if is_cgr else [cgr_core.getCGR(x) for x in reactions]
        f = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_CGR,
                       min_length=FRAGMENT_MIN_CGR, max_length=FRAGMENT_MAX_CGR,
                       cgr_dynbonds=FRAGMENT_DYNBOND_CGR, useformalcharge=True).get(cgrs)['X']

        fingerprints = []
        for _, s in f.iterrows():
            fingerprints.append(get_fingerprint(s))

        return fingerprints

    def __set_conditions(self, conditions):
        for c in conditions:
            media = c.pop('media', [])
            cond = Conditions(reaction=self, **c)
            for m in media:
                cond.raw_medias.add(RawMedias.get(name=m) or RawMedias(name=m))

    def set_conditions(self, conditions):
        available_conditions = {x.id: x.to_dict(exclude='id') for x in self.conditions_db}
        raw_name = left_join((c.id, rm.name) for c in Conditions if c.reaction == self for rm in c.raw_medias)
        for i, name in raw_name:
            available_conditions[i].setdefault('media', set()).add(name)

        available_conditions = list(available_conditions.values())

        to_add = []
        for c in conditions:
            flag = False
            for ac in available_conditions:
                if all((ac[key] or None) == (c.get(key) or None)
                       for key in ('product_yield', 'temperature', 'time', 'citation', 'comment','conditions',
                                   'description', 'pressure', 'steps')) and ac['media'] == set(c.get('media', [])):
                    flag = True
                    break
            if not flag:
                to_add.append(c)

        self.__set_conditions(to_add)
        return len(to_add)

    @staticmethod
    def generate_string(reaction, get_cgr=False):
        cgr = cgr_core.getCGR(reaction)
        cgr_string = fear.getreactionhash(cgr)
        return (cgr_string, cgr) if get_cgr else cgr_string

    @property
    def cgr(self):
        if self.__cached_cgr is None:
            self.__cached_cgr = cgr_core.getCGR(self.structure)
        return self.__cached_cgr

    @property
    def structure(self):
        if self.__cached_structure is None:
            tmp = dict(substrats=[], products=[], meta={})

            for x in self.molecules.order_by(lambda x: x.id):  # potentially optimizable
                tmp['products' if x.product else 'substrats'].append(
                    relabel_nodes(x.molecule.structure, {int(k): v for k, v in x.mapping.items()}))
            self.__cached_structure = tmp
        return self.__cached_structure

    @property
    def bitstring_fingerprint(self):
        return BitArray(self.fingerprint)

    @property
    def conditions(self):
        if self.__cached_conditions is None:
            result = {}

            for condition in self.conditions_db:
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

    __cached_structure = None
    __cached_cgr = None
    __cached_conditions = None


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
        ns= set(tags)
        os = set(self.tag_names)

        self.tags.remove(x for x in self.tags if x.name in os.difference(ns))
        self.tags.add(Tags.get(name=x) or Tags(name=x) for x in ns.difference(os))


class GroupReaction(db.Entity):
    group = Required(Groups)
    reaction = Required(Reactions)
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    fingerprint = Optional(bytes)
    PrimaryKey(group, reaction)


class RawMedias(db.Entity):
    id = PrimaryKey(int, auto=True)
    conditions = Set(Conditions)
    name = Required(str, unique=True)
    media = Optional(Medias)

    def update_media(self, name):
        self.media = Medias.get(name=name) or Medias(name=name)


sql_debug(True)
db.bind("sqlite", "database.sqlite")
db.generate_mapping(create_tables=True)
