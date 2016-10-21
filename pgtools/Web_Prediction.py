import json

from dbtools.models import PGdb


PGdb = PGdb()

class CatalystPrediction():
    def __init__(self, neighbors_number=9, delta=0.5):
        self.neighbors_number=neighbors_number
        self.delta=delta

    def makePrediction(self, PG=None, PGclass=None, fingerprint=None, catalyst=None, tags=None):
        a=fingerprint
        a_len=len(fingerprint)
        Tanimoto_vector_CPG={}
        for fingerprintDB_1, fing_id1 in PGdb.get_Fingerprints_forPG_and_Cat(group=PG, PGclass='CPG', tag=tags):
            #print(fingerprintDB_1, type(json.loads(fingerprintDB_1)))
            fing1=set(json.loads(fingerprintDB_1))
            b=len(fing1)
            c=len(a&fing1)
            Tc=c/(a_len+b-c)
            print(round(Tc, 4))
            Tanimoto_vector_CPG[fing_id1]=round(Tc, 4)

        Tanimoto_vector_RPG={}
        for fingerprintDB_2, fing_id2 in PGdb.get_Fingerprints_forPG_and_Cat(group=PG, PGclass='RPG', tag=tags):
            #print(fing_id2, fingerprintDB_2)
            fing2=set(fingerprintDB_2)
            b=len(fing2)
            c=len(a&fing2)
            Tc=c/(a_len+b-c)
            Tanimoto_vector_RPG[fing_id2]=round(Tc, 4)

        CPG=[]
        for key, value in sorted(Tanimoto_vector_CPG.items(), key = lambda x: x[1], reverse=True):
            if value not in CPG:
                CPG.append(value)

        RPG=[]
        for key, value in sorted(Tanimoto_vector_RPG.items(), key = lambda x: x[1], reverse=True):
            if value not in RPG:
                RPG.append(value)

        weight_CPG=0
        total_weight=0
        #print(Tanimoto_vector_CPG, Tanimoto_vector_RPG)
        #for n in range(self.neighbors_number):
