#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import chain

from CGRtools.SDFwrite import SDFwrite

__author__ = 'arkadiy'

from networkx.algorithms import isomorphism as gis, nx
from dbtools.models import PGdb
import operator

PGdb = PGdb()

class GraphMatcher():
    def __init__(self):

        self.__node_match=gis.generic_node_match(['element', 's_hyb', 'p_hyb', 's_neighbors', 'p_neighbors'],
                                                   [None]*5, [lambda a, b: b is None or a is None or (str(a)==str(b))]*5)
        self.__edge_match = gis.categorical_edge_match(['s_bond', 'p_bond'], [None]*2)

        self.__node_match_sub=gis.generic_node_match(['element', 's_hyb', 's_neighbors'], [None]*3,
                                                   [lambda a, b: b is None or (str(a)==str(b))]*3)
        self.__edge_match_sub = gis.categorical_edge_match(['s_bond'], [None])


    def substructure_search(self, CGR, gid):#sid - structure id; gid - group id
        PG = PGdb.getGroup(gid)
        tmp = []
        GM = gis.GraphMatcher(CGR, PG[0], node_match=self.__node_match_sub, edge_match=self.__edge_match_sub)
        GM_number = self.NUniqueMapping(GM)
        if GM_number:
            tmp = [False, False, False]
            GM_leave = gis.GraphMatcher(CGR, PG[0], node_match=self.__node_match, edge_match=self.__edge_match)
            GM_l_number = self.NUniqueMapping(GM_leave)
            if GM_l_number == GM_number:
                tmp[0] = True
            else:
                GM_remain = gis.GraphMatcher(CGR, PG[1], node_match=self.__node_match, edge_match=self.__edge_match)
                GM_r_number = self.NUniqueMapping(GM_remain)
                if GM_l_number:
                    tmp[0] = True
                if GM_r_number:
                    tmp[1] = True
                if GM_l_number + GM_r_number != GM_number:
                    tmp[2] = True
        return tmp

    def getReactionCenter(self, sid=None, gid=None, PGclass=1, deep=4, user_CGR=None):#PGclass = 1 or 2 or 3 (CPG, RPG or TPG)
        if sid:
            CGR = PGdb.getStructure(sid)
        else:
            CGR=user_CGR
        PG = PGdb.getGroup(gid)
        tmp = []
        if PGclass==1:
            #Searching left groups
            GM_leave = gis.GraphMatcher(CGR, PG[0], node_match=self.__node_match, edge_match=self.__edge_match)
            return self.NUniqueMapping(GM_leave, mode='map', deep=deep, Graph=CGR)
        elif PGclass==2:
            #Searching remaining groups
            GM_remain = gis.GraphMatcher(CGR, PG[1], node_match=self.__node_match, edge_match=self.__edge_match)
            return self.NUniqueMapping(GM_remain, mode='map', deep=deep, Graph=CGR)

    def detectDynamicBond(self):
        pass

    def NUniqueMapping(self, GM, mode=None, deep=None, Graph=None):#Вытаскивает количество уникальных маппов, тем самым решая проблему автоморфизма. mode=map если нужны сами вложения
        number = set()
        for gm in GM.subgraph_isomorphisms_iter():
            number.add(tuple(sorted(list(gm.keys()))))
        if mode is not None and deep is not None:#Getting reaction center
            centers = []
            for subset in list(number):
                nodes = set(subset)
                for i in range(deep):
                    nodes=set(chain.from_iterable(Graph.edges(nodes)))

                centers.append(nx.Graph(Graph.subgraph(nodes)))
            return centers
        else:
            return len(number)

    def LabelsCreation(self, Graph):
        tmp = Graph
        for i in tmp.nodes():
            label = {'s_hyb': 1, 'p_hyb': 1, 's_neighbors': 0, 'p_neighbors': 0}#1- sp3; 2- sp2; 3- sp1; 4- aromatic
            for k, h, n in (('s_bond', 's_hyb', 's_neighbors'), ('p_bond', 'p_hyb', 'p_neighbors')):
                for node, bond in tmp[i].items():
                #Блок неводородных соседей
                    if tmp.node[node]['element']!='H' and bond.get(k):
                            label[n]+=1
                #Блок закончился
                #Блок гибридизации
                    if bond.get(k) in (1, None):
                        pass
                    elif bond.get(k)==4:#Если есть ароматическая связь, то гибридизация принимает значение 4 (ароматика)
                        label[h] = 4
                    elif bond.get(k)==3 or (bond.get(k)==2 and label[h]==2):#Если есть 3-я или две 2-х связи, то sp1
                        label[h] = 3
                    elif bond.get(k)==2:#Если есть 2-я связь, но до этого не было найдено другой 2-й, 3-й, или аром.
                        label[h] = 2
                #Блок закончился
            tmp.node[i].update(label)
            #print(tmp.node[i])

        return tmp

    def WriteCGR2(self, FileName, CGR, PG):
        options = {}
        options['output'] = open(FileName,"w")
        self.__outputdata = SDFwrite(options['output'])
        self.__outputdata.writedata(CGR)
        self.__outputdata.writedata(PG)
        self.__outputdata.close()
