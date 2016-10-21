from dbtools.models import PGdb
from pgtools.GraphMatcher import GraphMatcher

PGdb = PGdb()

class Generate_fingerprints():
    def __init__(self, args):
        self.__deep=4
        self.GM=GraphMatcher()
        '''
        for sid in PGdb.getStructureIDs():
            for gid in PGdb.get_Groups_for_Reaction(sid):
                if PGdb.checkNumber_of_RC(sid, gid):
                    pass
                else:
                    rc_list=self.GM.getReactionCenter(sid, gid, 1, self.__deep)'''
