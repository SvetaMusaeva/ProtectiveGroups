from pony.orm import *
from networkx import relabel_nodes
from bitstring import BitArray
from networkx.readwrite.json_graph import node_link_graph, node_link_data
from CGRtools.FEAR import FEAR
from CGRtools.CGRreactor import CGRreactor
from CGRtools.CGRcore import CGRcore
from CGRtools.files.SDFrw import SDFwrite
from io import StringIO
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
    CL = Optional(str)
    LB = Optional(str)
    T = Optional(str)
    P = Optional(str)
    TIM = Optional(str)
    STP = Optional(str)
    YD = Optional(str)
    NYD = Optional(str)
    YPRO = Optional(str)
    CIT = Optional(LongStr)
    TEXT = Optional(LongStr)
    rx_id = Required(int)
    raw_medias = Set('RawMedia')
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
    string = Required(str)
    fingerprint = Required(bytes)
    reactions = Set('StructureReaction')

    def __init__(self, structure, fingerprint=None):
        structure_string = fear.getreactionhash(structure)
        data = node_link_data(structure)
        if fingerprint is None:
            with StringIO() as f:
                SDFwrite(f).write(structure)
                f.seek(0)
                s = str_fragmentor.get(f)['X'][0].loc[0]  # todo: remove [0] if fragmentor refactored
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
    string = Required(str)
    fingerprint = Required(bytes)

    structures = Set('StructureReaction')
    conditions = Set(Conditions, cascade_delete=True)
    groups = Set('GroupReaction')

    def __init__(self, reaction, fingerprint=None):
        cgr = cgr_core.getCGR(reaction)
        cgr_string = fear.getreactionhash(cgr)

        if fingerprint is None:
            with StringIO() as f:
                SDFwrite(f).write(cgr)
                f.seek(0)
                s = cgr_fragmentor.get(f)['X'][0].loc[0]  # todo: see below
                fingerprint = get_fingerprint(s, reaction=True)

        self.__cached_cgr = cgr
        self.__cached_reaction = reaction
        super(Reactions, self).__init__(string=cgr_string, fingerprint=fingerprint)

        for i, is_p in (('products', True), ('substrats', False)):
            for x in reaction[i]:
                s = Structures.get(string=fear.getreactionhash(x)) or Structures(x)

                StructureReaction(reaction=self, structure=s, product=is_p,
                                  mapping=next(cgr_reactor.spgraphmatcher(s.structure, x).isomorphisms_iter()))

    @property
    def cgr(self):
        if self.__cached_cgr is None:
            self.__cached_cgr = cgr_core.getCGR(self.reaction)
        return self.__cached_cgr

    @property
    def reaction(self):
        if self.__cached_reaction is None:
            tmp = dict(substrats=[], products=[], meta={})

            for x in self.structures:  # potentially optimizable
                tmp['products' if x.product else 'substrats'].append(relabel_nodes(x.structure.structure, x.mapping,
                                                                                   copy=True))
            self.__cached_reaction = tmp
        return self.__cached_reaction

    @property
    def bitstring_fingerprint(self):
        return BitArray(self.fingerprint)

    __cached_reaction = None
    __cached_cgr = None


class StructureReaction(db.Entity):
    id = PrimaryKey(int, auto=True)
    reaction = Required(Reactions)
    structure = Required(Structures)
    product = Required(bool, default=False)
    mapping = Required(Json)


class Tags(db.Entity):
    id = PrimaryKey(int, auto=True)
    tag = Optional(str)
    medias = Set('Media')


class Media(db.Entity):
    id = PrimaryKey(int, auto=True)
    compound = Optional(str)
    raw_medias = Set('RawMedia')
    tags = Set(Tags)


class GroupReaction(db.Entity):
    group = Required(Groups)
    reaction = Required(Reactions)
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    fingerprint = Optional(bytes)
    PrimaryKey(group, reaction)


class RawMedia(db.Entity):
    id = PrimaryKey(int, auto=True)
    conditions = Set(Conditions)
    media = Optional(Media)
    component = Optional(str)


db.bind("sqlite", "database.sqlite")
db.generate_mapping(create_tables=True)
