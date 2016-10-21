#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading

import time

from multiprocessing import Process
from multiprocessing.pool import Pool

from CGRtools.SDFwrite import SDFwrite
from Fragmentation.Fragmentor import Fragmentor
from pgtools.Prediction import Validation
from pgtools.GraphMatcher import GraphMatcher

__author__ = 'arkadiy'
from dbtools.models import PGdb
PGdb = PGdb()

class ValidationMode():
    def __init__(self, args):
        self.id_information={}
        self.__deep=args.reaction_center_deep
        self.__threads=args.threads
        PGList=PGdb.get_PGlist()
        self.catalysts=["Pd", "Ni", "Rh", "Pt", "Lindlar"]
        self.tags=[["Pd", "Lindlar"],["Ni","XXXXX"], ["Rh", "XXXXX"], ["Pt","XXXXX"], ["Lindlar", "XXXXX"]]
        d=self.PGchecking(PGList,5)
        print("Deleting marks..")
        self.killDynamicBonds(d)
        print("Writing file..")
        self.WriteCGR(d,"./SystemFiles/Reactions.sdf")
        print("Fragmentation..")
        fragmentor = Fragmentor(args.configuration_file, self.__threads)
        fragmentor.Fragmentation()
        print("Fingerprinting..")
        self.fingerprints_set = fragmentor.getFingerprints()#Набор фингерпринтов для разных фрагментаций
        bitstring_dict = {}#Словарь, в котором будут храниться только фингерпринты
        bitstring_dict=self.DictOfFingerprints(d)
        #Validation
        print("Validation..")
        statistic1={}
        fragnames=list(self.fingerprints_set.keys())

        with Pool(self.__threads) as pool:
            results=[pool.apply_async(Validation, (bitstring_dict, fragname)) for fragname in fragnames]
            for r in results:
                v=r.get()
                statistic1[v.frag_name]=v.predictions
        print("Creating statistics..")
        with open("./SystemFiles/Similarity_Statistics_2_BIG_2.csv", "w") as out:
            for frag_name in self.fingerprints_set:
                out.write(frag_name+'\n\nTcMax\n')
                a=[]
                b=[]
                c=[]
                d=[]
                for delta in sorted(statistic1[frag_name]['TcMax']):
                    if statistic1[frag_name]['TcMax'][delta]['P']>0 and statistic1[frag_name]['TcMax'][delta]['N']>0:
                        a.append(str(delta))
                        b.append(str(round(statistic1[frag_name]['TcMax'][delta]['TP']/statistic1[frag_name]['TcMax'][delta]['P'], 3)))
                        c.append(str(round(statistic1[frag_name]['TcMax'][delta]['FP']/statistic1[frag_name]['TcMax'][delta]['N'], 3)))
                        d.append(str(statistic1[frag_name]['TcMax'][delta]['Unpredictable']))
                out.write(';'.join(a)+'\n')
                out.write(';'.join(b)+'\n')
                out.write(';'.join(c)+'\n')
                out.write(';'.join(d)+'\n\n')
                for num_neighbors in sorted(statistic1[frag_name]['kNN']):
                    out.write('kNN '+str(num_neighbors)+' neighbors..\n')
                    a=[]
                    b=[]
                    c=[]
                    for delta in sorted(statistic1[frag_name]['kNN'][num_neighbors]):
                        a.append(str(delta))
                        b.append(str(round(statistic1[frag_name]['kNN'][num_neighbors][delta]['TP']/(statistic1[frag_name]['kNN'][num_neighbors][delta]['TP']+statistic1[frag_name]['kNN'][num_neighbors][delta]['FN']), 3)))
                        c.append(str(round(statistic1[frag_name]['kNN'][num_neighbors][delta]['FP']/(statistic1[frag_name]['kNN'][num_neighbors][delta]['FP']+statistic1[frag_name]['kNN'][num_neighbors][delta]['TN']), 3)))
                    out.write(';'.join(a)+'\n')
                    out.write(';'.join(b)+'\n')
                    out.write(';'.join(c)+'\n\n')
                for num_neighbors in sorted(statistic1[frag_name]['kNNw']):
                    out.write('kNN weighted '+str(num_neighbors)+' neighbors..\n')
                    a=[]
                    b=[]
                    c=[]
                    for delta in sorted(statistic1[frag_name]['kNNw'][num_neighbors]):
                        a.append(str(delta))
                        b.append(str(round(statistic1[frag_name]['kNNw'][num_neighbors][delta]['TP']/(statistic1[frag_name]['kNNw'][num_neighbors][delta]['TP']+statistic1[frag_name]['kNNw'][num_neighbors][delta]['FN']), 3)))
                        c.append(str(round(statistic1[frag_name]['kNNw'][num_neighbors][delta]['FP']/(statistic1[frag_name]['kNNw'][num_neighbors][delta]['FP']+statistic1[frag_name]['kNNw'][num_neighbors][delta]['TN']), 3)))
                    out.write(';'.join(a)+'\n')
                    out.write(';'.join(b)+'\n')
                    out.write(';'.join(c)+'\n\n')

    def PGchecking(self, PGList, MinNumOfReact):
        d={}
        self.GM=GraphMatcher()
        for j1, i in enumerate(PGList):
            '''
            if i=='Benzyl alcohol':
                print(j1)
                d[i]={}
                for j, cat in enumerate(self.catalysts):
                    ReactList=PGdb.get_StructureIDs_forPG_and_Cat(group=i, tag=self.tags[j])
                    n1=len(set(ReactList[0]))
                    n2=len(set(ReactList[1]))
                    if n1>MinNumOfReact and n2>MinNumOfReact:
                        print("cat=", cat)
                        d[i][cat]={}
                        d[i][cat]["CPG"]={}
                        d[i][cat]["RPG"]={}
                        for jj, id in enumerate(list(set(ReactList[0]))):
                            if jj%100==0 and jj>0:
                                break
                                    #print(jj, 1)
                            d[i][cat]["CPG"][id]={}
                            d[i][cat]["CPG"][id]["subgraph"]=self.GM.getReactionCenter(sid=id, gid=PGdb.getGroupID_byName(i), PGclass=1, deep=self.__deep)
                                #return
                        if jj<2:
                            print('No data for CPG! '+i+'-'+cat+'-')
                        for jj, id in enumerate(list(set(ReactList[1]))):
                            if jj%100==0 and jj>0:
                                break
                                    #print(jj, 2)
                            d[i][cat]["RPG"][id]={}
                            d[i][cat]["RPG"][id]["subgraph"]=self.GM.getReactionCenter(sid=id, gid=PGdb.getGroupID_byName(i), PGclass=2, deep=self.__deep)
                        if jj<2:
                            print('No data for RPG! '+i+'-'+cat+'-')

                if len(d[i])==0:
                    d.pop(i)
                else:
                        #return d
                    continue
            '''
            print(j1)
            d[i]={}
            for j, cat in enumerate(self.catalysts):
                ReactList=PGdb.get_StructureIDs_forPG_and_Cat(group=i, tag=self.tags[j])
                n1=len(set(ReactList[0]))
                n2=len(set(ReactList[1]))
                if n1>MinNumOfReact and n2>MinNumOfReact:
                    print("cat=", cat)
                    d[i][cat]={}
                    d[i][cat]["CPG"]={}
                    d[i][cat]["RPG"]={}
                    for jj, id in enumerate(list(set(ReactList[0]))):
                        #if jj%100==0 and jj>0:
                            #break
                                #print(jj, 1)
                        d[i][cat]["CPG"][id]={}
                        d[i][cat]["CPG"][id]["subgraph"]=self.GM.getReactionCenter(id, PGdb.getGroupID_byName(i), 1, self.__deep)
                            #return
                    if jj<2:
                        print('No data for CPG! '+i+'-'+cat+'-')
                    for jj, id in enumerate(list(set(ReactList[1]))):
                        #if jj%100==0 and jj>0:
                            #break
                                #print(jj, 2)
                        d[i][cat]["RPG"][id]={}
                        d[i][cat]["RPG"][id]["subgraph"]=self.GM.getReactionCenter(id, PGdb.getGroupID_byName(i), 2, self.__deep)
                    if jj<2:
                        print('No data for RPG! '+i+'-'+cat+'-')

            if len(d[i])==0:
                d.pop(i)
            else:
                    #return d
                continue

        return d

    def DictOfFingerprints(self,d):
        tmp={}
        for frag_name in self.fingerprints_set:
            for id in self.fingerprints_set[frag_name]:
                PG=self.id_information[id][0]
                cat=self.id_information[id][1]
                class1=self.id_information[id][2]
                if PG not in tmp:
                    tmp[PG]={}
                if cat not in tmp[PG]:
                    tmp[PG][cat]={}
                if class1 not in tmp[PG][cat]:
                    tmp[PG][cat][class1]={}
                if frag_name not in tmp[PG][cat][class1]:
                    tmp[PG][cat][class1][frag_name]={}
                tmp[PG][cat][class1][frag_name][id]=self.fingerprints_set[frag_name][id]
        return tmp

    def killDynamicBonds(self, graphDict):
        for i in graphDict:
            print("PG", i)
            for j, cat in enumerate(graphDict[i]):
                print("cat", cat)
                for class1 in graphDict[i][cat]:
                    print("Class", class1)
                    for id in graphDict[i][cat][class1]:
                        for num, subgraph in enumerate(graphDict[i][cat][class1][id]["subgraph"]):
                            for g in subgraph.edges_iter():
                                graphDict[i][cat][class1][id]["subgraph"][num][g[0]][g[1]]['p_bond']=graphDict[i][cat][class1][id]["subgraph"][num][g[0]][g[1]].get('s_bond')
                                graphDict[i][cat][class1][id]["subgraph"][num][g[0]][g[1]]['p_stereo']=graphDict[i][cat][class1][id]["subgraph"][num][g[0]][g[1]].get('s_stereo')
                            for g in subgraph.nodes_iter():
                                if 's_neighbors' in graphDict[i][cat][class1][id]["subgraph"][num].node[g]:
                                    graphDict[i][cat][class1][id]["subgraph"][num].node[g].pop('s_neighbors')
                                if 'p_neighbors' in graphDict[i][cat][class1][id]["subgraph"][num].node[g]:
                                    graphDict[i][cat][class1][id]["subgraph"][num].node[g].pop('p_neighbors')
                                if 's_hyb' in graphDict[i][cat][class1][id]["subgraph"][num].node[g]:
                                    graphDict[i][cat][class1][id]["subgraph"][num].node[g].pop('s_hyb')
                                if 'p_hyb' in graphDict[i][cat][class1][id]["subgraph"][num].node[g]:
                                    graphDict[i][cat][class1][id]["subgraph"][num].node[g].pop('p_hyb')
                                if 'isotop' in graphDict[i][cat][class1][id]["subgraph"][num].node[g]:
                                    graphDict[i][cat][class1][id]["subgraph"][num].node[g].pop('isotop')
                                graphDict[i][cat][class1][id]["subgraph"][num].node[g]['p_charge']=graphDict[i][cat][class1][id]["subgraph"][num].node[g].get('s_charge')
                                graphDict[i][cat][class1][id]["subgraph"][num].node[g]['p_stereo']=graphDict[i][cat][class1][id]["subgraph"][num].node[g].get('s_stereo')

    def WriteCGR(self,graphDict, FileName):
        options = {}
        options['output'] = open(FileName,"w")
        self.__outputdata = SDFwrite(options['output'])
        for i in graphDict:
            for j, cat in enumerate(graphDict[i]):
                for class1 in graphDict[i][cat]:
                    for id in graphDict[i][cat][class1]:
                        for k, subgraph in enumerate(graphDict[i][cat][class1][id]["subgraph"]):
                            subgraph.graph['meta']={}
                            subgraph.graph['meta']['ReactID']=i.replace(' ','_')+'_'+cat+'_'+str(id)+'_'+str(k)
                            self.id_information[i.replace(' ','_')+'_'+cat+'_'+str(id)+'_'+str(k)]=[i, cat, class1]
                            self.__outputdata.writedata(subgraph)
        self.__outputdata.close()
