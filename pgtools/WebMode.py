import configparser

from CGRtools.CGRcore import CGRcore
from CGRtools.RDFread import RDFread
from CGRtools.SDFwrite import SDFwrite
from Fragmentation.Fragmentor import Fragmentor
from pgtools.GraphMatcher import GraphMatcher
from dbtools.models import PGdb
from pgtools.Web_Prediction import CatalystPrediction

PGdb = PGdb()

class WebMode():
    def __init__(self, args):
        self.userReaction=args.user_reaction#The program took user's reaction
        #self.userTags=args.user_tags
        self.catalysts=["Pd", "Ni", "Rh", "Pt", "Lindlar"]
        self.tags=[["Pd", "Lindlar"],["Ni","XXXXX"], ["Rh", "XXXXX"], ["Pt","XXXXX"], ["Lindlar", "XXXXX"]]
        self.predictionModule=CatalystPrediction(neighbors_number=args.kNN_neighbors, delta=args.kNN_delta)
        inputdata = RDFread(args.user_reaction)#The program read user's reaction
        self.__graphmatcher = GraphMatcher()
        self.__settings = configparser.RawConfigParser()#delimiters="<")
        self.__settings.optionxform = str
        self.__settings.read_file(args.configuration_file)
        self.__deep=args.reaction_center_deep
        self.fragmentor = Fragmentor(args.configuration_file, args.threads, settings=self.__settings)
        options = {}
        for option in self.__settings.options('Condenser'):
            options[option] = self.__settings.get('Condenser', option)
        self.__con = CGRcore(**options)
        for num, data in enumerate(inputdata.readdata()):
            CGR = self.__graphmatcher.LabelsCreation(self.createCGR(data))#Obtained a CGR from user's reaction and put labels

        self.user_PGs={}
        for gid in PGdb.getGroupIDs():
            skeys = self.__graphmatcher.substructure_search(CGR, gid)
            if skeys and (skeys[0] or skeys[1]):
                self.user_PGs[gid]=dict(CPG={}, RPG={})
                if skeys[0]:
                    for num, RC in enumerate(self.__graphmatcher.getReactionCenter(user_CGR=CGR, gid=gid, PGclass=1, deep=self.__deep)):
                        self.user_PGs[gid]['CPG'][num]=dict(reaction_center=self.cleanSubgraph(RC), fingerprint=None, catalysts={})
                if skeys[1]:
                    for num, RC in enumerate(self.__graphmatcher.getReactionCenter(user_CGR=CGR, gid=gid, PGclass=2, deep=self.__deep)):
                        self.user_PGs[gid]['RPG'][num]=dict(reaction_center=self.cleanSubgraph(RC), fingerprint=None, catalysts={})

        self.WriteRC('Fragmentation/temp_Users_CGR_RC.sdf')
        self.fragmentor.Fragmentation(file_in='Fragmentation/temp_Users_CGR_RC.sdf', file_out="temp_Users_RC")
        self.fingerprints_set = self.fragmentor.getFingerprints(name="temp_Users_RC")["temp_Users_RC"]
        #print(self.fingerprints_set)

        for number, value in self.fingerprints_set.items():
            self.user_PGs[int(number.split('_')[0])][number.split('_')[1]][int(number.split('_')[2])]['fingerprint']=value

        for i, catalyst in enumerate(self.catalysts):
            for PG in self.user_PGs:
                for PGclass in self.user_PGs[PG]:
                    for rc_num, data2 in self.user_PGs[PG][PGclass].items():
                        self.predictionModule.makePrediction(PG=PG, PGclass=PGclass, catalyst=catalyst, tags=self.tags[i], fingerprint=data2['fingerprint'])
                        print(catalyst, PG, PGclass, rc_num)


    def createCGR(self, data):
        CGR = self.__con.getCGR(data)
        return CGR

    def cleanSubgraph(self, subgraph=None):
        for g in subgraph.edges_iter():
            try:
                subgraph[g[0]][g[1]]['p_bond']=subgraph[g[0]][g[1]].get('s_bond')
            except:
                pass
            try:
                subgraph[g[0]][g[1]]['p_stereo']=subgraph[g[0]][g[1]]['s_stereo']
            except:
                pass
        for g in subgraph.nodes_iter():
            if 's_neighbors' in subgraph.node[g]:
                subgraph.node[g].pop('s_neighbors')
            if 'p_neighbors' in subgraph.node[g]:
                subgraph.node[g].pop('p_neighbors')
            if 's_hyb' in subgraph.node[g]:
                subgraph.node[g].pop('s_hyb')
            if 'p_hyb' in subgraph.node[g]:
                subgraph.node[g].pop('p_hyb')
            if 'isotop' in subgraph.node[g]:
                subgraph.node[g].pop('isotop')
            try:
                subgraph.node[g]['p_charge']=subgraph.node[g]['s_charge']
            except:
                pass
            try:
                subgraph.node[g]['p_stereo']=subgraph.node[g]['s_stereo']
            except:
                pass
        return subgraph

    def WriteRC(self, FileName):
        options = {}
        options['output'] = open(FileName,"w")
        self.__outputdata = SDFwrite(options['output'])
        for group, value1 in self.user_PGs.items():
            for PGclass, value2 in value1.items():
                for rc_num, value3 in value2.items():
                    rc=value3['reaction_center']
                    rc.graph['meta']={}
                    rc.graph['meta']['ReactID']=str(group)+'_'+str(PGclass)+'_'+str(rc_num)
                    self.__outputdata.writedata(rc)
        self.__outputdata.close()