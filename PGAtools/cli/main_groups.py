from pony.orm import db_session, select
from ..models import Groups, Reactions
from CGRtools.files.RDFrw import RDFread
from CGRtools.CGRcore import CGRcore
import networkx as nx

cgr_core = CGRcore()


def groups_core(**kwargs):
    inputdata = RDFread(kwargs['input'])
    groups = []
    with db_session:
        for r in inputdata.read():
            name = r['meta']['name']
            r['meta'] = {}
            if not Groups.exists(name=name):
                g = Groups(name, nx.union_all(r['substrats']), cgr_core.getCGR(r))
                # todo: indexation!