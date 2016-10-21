#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from CGRtools.SDFwrite import SDFwrite
from Fragmentation.Fragmentor import Fragmentor

__author__ = 'arkadiy'

import configparser

from CGRtools.CGRcore import CGRcore
from dbtools.models import PGdb
from pgtools.GraphMatcher import GraphMatcher

PGdb = PGdb()

class Add_Reaction():
    def __init__(self, args):
        self.__graphmatcher = GraphMatcher()
        self.__deep=args.reaction_center_deep
        self.__settings = configparser.RawConfigParser(delimiters=":")
        self.__settings.optionxform = str
        self.__settings.read_file(args.configuration_file)
        options = {}
        for option in self.__settings.options('Condenser'):
            options[option] = self.__settings.get('Condenser', option)
        self.__con = CGRcore(**options)
        self.fragmentor = Fragmentor(args.configuration_file, args.threads, settings=self.__settings)

    def add_Structure(self, data):
        smiles = data['smiles']
        id = data['id']
        sid=PGdb.getStructureID(smiles)
        if sid:
            print("This structure has been already added!")
            if PGdb.checkStructureKey(sid):
                print("This reaction has already been indexed in substructure searching!")
            else:
                self.add_StructureKeys(sid)
        else:
            CGR = self.__graphmatcher.LabelsCreation(self.createCGR(data))
            PGdb.addStructure(smiles, CGR)
            sid = PGdb.getStructureID(smiles)
            self.add_StructureKeys(sid)
            print("This structure is added!")
        return sid

    def add_StructureKeys(self, sid):#sid - structure id; gid - group id
        CGR = PGdb.getStructure(sid)
        for gid in PGdb.getGroupIDs():
            skeys = self.__graphmatcher.substructure_search(CGR, gid)
            if skeys:
                PGdb.addStructureKey(sid, gid, skeys)
                if skeys[0] or skeys[1]:
                    print('Making fingerprints...')
                    self.addFingerprints(gid=gid, sid=sid, skeys=skeys)

    def createCGR(self, data):
        CGR = self.__con.getCGR(data)
        return CGR

    def addFingerprints(self, gid=None, sid=None, skeys=None):
        if skeys[0]:
            CPG_RC=self.__graphmatcher.getReactionCenter(sid=sid, gid=gid, PGclass=1, deep=self.__deep)
            for num, subgraph in enumerate(CPG_RC):
                for g in subgraph.edges_iter():
                    try:
                        CPG_RC[num][g[0]][g[1]]['p_bond']=CPG_RC[num][g[0]][g[1]].get('s_bond')
                    except:
                        pass
                    try:
                        CPG_RC[num][g[0]][g[1]]['p_stereo']=CPG_RC[num][g[0]][g[1]]['s_stereo']
                    except:
                        pass
                for g in subgraph.nodes_iter():
                    if 's_neighbors' in CPG_RC[num].node[g]:
                        CPG_RC[num].node[g].pop('s_neighbors')
                    if 'p_neighbors' in CPG_RC[num].node[g]:
                        CPG_RC[num].node[g].pop('p_neighbors')
                    if 's_hyb' in CPG_RC[num].node[g]:
                        CPG_RC[num].node[g].pop('s_hyb')
                    if 'p_hyb' in CPG_RC[num].node[g]:
                        CPG_RC[num].node[g].pop('p_hyb')
                    if 'isotop' in CPG_RC[num].node[g]:
                        CPG_RC[num].node[g].pop('isotop')
                    try:
                        CPG_RC[num].node[g]['p_charge']=CPG_RC[num].node[g]['s_charge']
                    except:
                        pass
                    try:
                        CPG_RC[num].node[g]['p_stereo']=CPG_RC[num].node[g]['s_stereo']
                    except:
                        pass
            self.WriteCGR(RC_list=CPG_RC, FileName='Fragmentation/temp_CGR_RC.sdf', sid=sid, gid=gid)

            self.fragmentor.Fragmentation(file_in='Fragmentation/temp_CGR_RC.sdf', file_out="temp_RC")
            self.fingerprints_set = self.fragmentor.getFingerprints(name="temp_RC")
            for f in self.fingerprints_set["temp_RC"].values():
                PGdb.addFingerprint(sid=sid, gid=gid,classTransformation='CPG', fingerprint=list(f))

        if skeys[1]:
            RPG_RC=self.__graphmatcher.getReactionCenter(sid=sid, gid=gid, PGclass=2, deep=self.__deep)
            for num, subgraph in enumerate(RPG_RC):
                for g in subgraph.edges_iter():
                    try:
                        RPG_RC[num][g[0]][g[1]]['p_bond']=RPG_RC[num][g[0]][g[1]].get('s_bond')
                    except:
                        pass
                    try:
                        RPG_RC[num][g[0]][g[1]]['p_stereo']=RPG_RC[num][g[0]][g[1]]['s_stereo']
                    except:
                        pass
                for g in subgraph.nodes_iter():
                    if 's_neighbors' in RPG_RC[num].node[g]:
                        RPG_RC[num].node[g].pop('s_neighbors')
                    if 'p_neighbors' in RPG_RC[num].node[g]:
                        RPG_RC[num].node[g].pop('p_neighbors')
                    if 's_hyb' in RPG_RC[num].node[g]:
                        RPG_RC[num].node[g].pop('s_hyb')
                    if 'p_hyb' in RPG_RC[num].node[g]:
                        RPG_RC[num].node[g].pop('p_hyb')
                    if 'isotop' in RPG_RC[num].node[g]:
                        RPG_RC[num].node[g].pop('isotop')
                    try:
                        RPG_RC[num].node[g]['p_charge']=RPG_RC[num].node[g]['s_charge']
                    except:
                        pass
                    try:
                        RPG_RC[num].node[g]['p_stereo']=RPG_RC[num].node[g]['s_stereo']
                    except:
                        pass
            self.WriteCGR(RC_list=RPG_RC, FileName='Fragmentation/temp_CGR_RC.sdf', sid=sid, gid=gid)

            self.fragmentor.Fragmentation(file_in='Fragmentation/temp_CGR_RC.sdf', file_out="temp_RC")
            self.fingerprints_set = self.fragmentor.getFingerprints(name="temp_RC")
            for f in self.fingerprints_set["temp_RC"].values():
                PGdb.addFingerprint(sid=sid, gid=gid,classTransformation='RPG', fingerprint=list(f))

    def WriteCGR(self,RC_list, FileName, sid=None, gid=None):
        options = {}
        options['output'] = open(FileName,"w")
        self.__outputdata = SDFwrite(options['output'])
        for k, subgraph in enumerate(RC_list):
            subgraph.graph['meta']={}
            subgraph.graph['meta']['ReactID']=str(sid)+'_'+str(gid)+'_'+str(k)
            self.__outputdata.writedata(subgraph)
        self.__outputdata.close()


class Add_Conditions():
    def __init__(self, field_list):
        self.__field_list = field_list

    def addConditions(self, data, sid):
        rids = PGdb.getCondition_id(sid)#reactions id
        if rids:#Проверяются дубликаты в условиях
            saved = False
            for num, elements in data['meta'].items():
                for num1, rid in enumerate(rids):
                    duplicate=True
                    conditions=PGdb.get_Conditions(rid)
                    for key, item in conditions.items():
                        if key in elements.keys() and elements[key].strip()!=str(item).strip():
                            duplicate=False
                            break
                    media = PGdb.getAllRowMedia_byRID(rid)
                    for component in elements['media']:
                        if component.strip() not in media:
                            duplicate = False
                            break

                    if duplicate:
                        break
                if duplicate:
                    continue
                else:
                    saved=True
                    self.saveConditions(sid, elements, data)
            if saved:
                return True
            else:
                return False
        else:
            for i in data['meta'].values():
                self.saveConditions(sid, i, data)
            return True

    #Проверяется, есть ли необходимый ключ в полученных данных. Если нет, то
    #создасться новый с пустым значением
    def checkFields(self, meta):
        for key in self.__field_list:
            if key not in meta.keys():
                meta[key]=''
        return meta

    def saveConditions(self, sid, i, data):
        i_checked = self.checkFields(i)
        for x in i['media']:
            if PGdb.getRawMediaID(x):
                continue
            else:
                PGdb.addRawMedia(x)
        PGdb.addConditions(data['id'], i_checked, sid, i['media'])
