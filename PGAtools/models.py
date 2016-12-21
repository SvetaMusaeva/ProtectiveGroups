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
from .config import (FP_HEADER_STR, FP_HEADER_CGR, FRAGMENTOR_VERSION, FRAGMENT_TYPE_CGR, FRAGMENT_MIN_CGR,
                     FRAGMENT_MAX_CGR, FRAGMENT_TYPE_STR, FRAGMENT_MIN_STR, FRAGMENT_MAX_STR, FRAGMENT_DYNBOND_CGR)


db = Database()
fear = FEAR()
cgr_core = CGRcore()
cgr_reactor = CGRreactor()

# todo: set config
str_fragmentor = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_STR,
                            min_length=FRAGMENT_MIN_STR, max_length=FRAGMENT_MAX_STR,
                            useformalcharge=True, header=open(FP_HEADER_STR))
cgr_fragmentor = Fragmentor(workpath='.', version=FRAGMENTOR_VERSION, fragment_type=FRAGMENT_TYPE_CGR,
                            min_length=FRAGMENT_MIN_CGR, max_length=FRAGMENT_MAX_CGR,
                            cgr_dynbonds=FRAGMENT_DYNBOND_CGR, useformalcharge=True, header=open(FP_HEADER_CGR))


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
    query_leave_data = Required(Json)
    query_remain_data = Required(Json)
    reactions = Set('GroupReaction')

    def __init__(self, name, query_leave, query_remain):
        query_leave_data = node_link_data(query_leave)
        query_remain_data = node_link_data(query_remain)
        super(Groups, self).__init__(name=name, query_leave_data=query_leave_data, query_remain_data=query_remain_data)

    @property
    def query_leave(self):
        return node_link_graph(self.query_leave_data)

    @property
    def query_remain(self):
        return node_link_graph(self.query_remain_data)


class Structures(db.Entity):
    id = PrimaryKey(int, auto=True)
    data = Required(Json)
    string = Required(str, unique=True)
    fingerprint = Required(bytes)
    reactions = Set('StructureReaction')

    def __init__(self, structure, fingerprint=None):
        structure_string = fear.getreactionhash(structure)
        data = node_link_data(structure)
        if fingerprint is None:
            s = str_fragmentor.get([structure])['X'].loc[0]
            fingerprint = get_fingerprint(s)

        self.__cached_structure = structure
        super(Structures, self).__init__(data=data, string=structure_string, fingerprint=fingerprint.bytes)

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

    structures = Set('StructureReaction')
    conditions_db = Set(Conditions, cascade_delete=True)
    groups = Set('GroupReaction')

    def __init__(self, reaction, conditions=None, fingerprint=None, **db_ids):
        cgr_string, cgr = self.generate_string(reaction, get_cgr=True)

        if fingerprint is None:
            s = cgr_fragmentor.get([cgr])['X'].loc[0]
            fingerprint = get_fingerprint(s, reaction=True)

        self.__cached_cgr = cgr
        self.__cached_reaction = reaction
        super(Reactions, self).__init__(string=cgr_string, fingerprint=fingerprint.bytes,
                                        **{x: y for x, y in db_ids.items() if y})

        for i, is_p in (('substrats', False), ('products', True)):
            for x in reaction[i]:
                s = Structures.get(string=fear.getreactionhash(x)) or Structures(x)

                StructureReaction(reaction=self, structure=s, product=is_p,
                                  mapping=next(cgr_reactor.spgraphmatcher(s.structure, x).isomorphisms_iter()))

        self.__set_conditions(conditions or [])

    def __set_conditions(self, conditions):
        for c in conditions:
            media = c.pop('media')
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
                                   'description', 'pressure', 'steps')) and ac['media'] == set(c['media']):
                    flag = True
                    break
            if not flag:
                to_add.append(c)

        self.__set_conditions(to_add)

    @staticmethod
    def generate_string(reaction, get_cgr=False):
        cgr = cgr_core.getCGR(reaction)
        cgr_string = fear.getreactionhash(cgr)
        return (cgr_string, cgr) if get_cgr else cgr_string

    @property
    def cgr(self):
        if self.__cached_cgr is None:
            self.__cached_cgr = cgr_core.getCGR(self.reaction)
        return self.__cached_cgr

    @property
    def reaction(self):
        if self.__cached_reaction is None:
            tmp = dict(substrats=[], products=[], meta={})

            for x in self.structures.order_by(lambda x: x.id):  # potentially optimizable
                tmp['products' if x.product else 'substrats'].append(relabel_nodes(x.structure.structure, x.mapping,
                                                                                   copy=True))
            self.__cached_reaction = tmp
        return self.__cached_reaction

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
            clear_name = left_join((c.id, m.name, m.id) for c in Conditions if c.reaction == self for rm in c.raw_medias if rm.media for m in rm.media)
            for *id_name, mid in clear_name:
                mids.add(mid)
                clear_list.append(id_name)

            tags_list = defaultdict(list)
            tags_name = left_join((m.name, t.name) for m in Medias if m.id in mids for t in m.tags)
            for m, t in tags_name:
                tags_list[m].append(t)

            raw_name = left_join((c.id, rm.name) for c in Conditions if c.reaction == self for rm in c.raw_medias if not rm.media)
            for i, name in chain(clear_list, raw_name):
                result[i]['media'][name] = tags_list[name]
            self.__cached_conditions = list(result.values())

        return self.__cached_conditions

    __cached_reaction = None
    __cached_cgr = None
    __cached_conditions = None


class StructureReaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    reaction = Required(Reactions)
    structure = Required(Structures)
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


sql_debug(True)
db.bind("sqlite", "database.sqlite")
db.generate_mapping(create_tables=True)
