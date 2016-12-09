from pony.orm import *
from networkx.readwrite.json_graph import node_link_graph, node_link_data
from CGRtools.FEAR import FEAR
from CGRtools.CGRcore import CGRcore


db = Database()
fear = FEAR()
cgr_core = CGRcore()


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
    structure = Required('Structures')


class Groups(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    query_leave_data = Required(Json)
    query_remain_data = Required(Json)
    structures = Set('GroupStructure')

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
    structure_hash = Required(str)
    CGR_data = Required(Json)
    conditions = Set(Conditions, cascade_delete=True)
    groups = Set('GroupStructure')

    def __init__(self, reaction):
        tmp = reaction.copy()
        tmp['meta'] = {}

        cgr = cgr_core.getCGR(tmp)

        CGR_data = node_link_data(cgr)
        json_data = {'substrats': [node_link_data(x) for x in tmp['substrats']],
                     'products': [node_link_data(x) for x in tmp['products']], 'meta': {}}

        structure_hash = fear.getreactionhash(cgr)

        super(Structures, self).__init__(data=json_data, structure_hash=structure_hash, CGR_data=CGR_data)

    @property
    def reaction(self):
        return {'substrats': [node_link_graph(x) for x in self.data['substrats']],
                'products': [node_link_graph(x) for x in self.data['products']], 'meta': {}}

    @property
    def CGR(self):
        return node_link_graph(self.CGR_data)


class Tags(db.Entity):
    id = PrimaryKey(int, auto=True)
    tag = Optional(str)
    medias = Set('Media')


class Media(db.Entity):
    id = PrimaryKey(int, auto=True)
    compound = Optional(str)
    raw_medias = Set('RawMedia')
    tags = Set(Tags)


class GroupStructure(db.Entity):
    group = Required(Groups)
    structure = Required(Structures)
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    fingerprint = Optional(bytes)
    PrimaryKey(group, structure)


class RawMedia(db.Entity):
    id = PrimaryKey(int, auto=True)
    conditions = Set(Conditions)
    media = Optional(Media)
    component = Optional(str)


db.bind("sqlite", "database.sqlite")
db.generate_mapping(create_tables=True)
