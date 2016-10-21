#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'arkadiy'

from CGRtools.RDFread import RDFread
from dbtools.models import PGdb
from pgtools.GraphMatcher import GraphMatcher
from pgtools.reaction_treatment import Add_Reaction

PGdb = PGdb()
# Добавление защитных групп происходит по принципу:
# Каждая группа в базе характеризуется названием, id и двумя CGR для отрыва и сохранения группы от определенного
# фрагмента. Все группы перед добавлением в базу должны храниться в RDF формате, экспортированном из базы
# InstantJChem. При добавлении новой ЗГ программа сначала пытается проверить добавляли ли уже эту группу ранее.
# Она делает CGR для данной реакции и потом ищет строчку в базе, содержащей эту CGR. Если такой id уже есть,
# значит база уже содержит такую CGR.В противном случае она пытается добавить нашу группу в базу в виде двух CGR:
# отрыв и сохранение группы.


class Protective_Groups():
    def __init__(self, args):
        inputdata = RDFread(args.input)
        self.group = Add_Reaction(args)
        self.graphmatcher = GraphMatcher()
        for num, data in enumerate(inputdata.readdata()):
            self.CGR_l = self.group.createCGR(data)
            group_id = PGdb.getGroupID_byCGR(self.CGR_l)
            if group_id:
                print("Group #" + str(num+1) + " with name " + PGdb.getGroupName_byID(group_id) + " has been already added to DB..")
            else:
                print("Group #" + str(num+1) + " is not known to DB..")
                CGR_r = self.group.createCGR(self.createRemainingGroup(data))
                PGdb.addGroup(self.CGR_l, CGR_r, data['meta']['NAME'].strip())
                self.reindexDB(PGdb.getGroupID_byCGR(self.CGR_l))
            if num % 10==0:
                print("reaction: %d" % (num + 1))


    def createRemainingGroup(self, data):
        return dict(substrats = data['substrats'], products = data['substrats'], meta = data['meta'])

    def reindexDB(self, gid):
        sid_list = PGdb.getStructureIDs()
        if sid_list:
            for sid in sid_list:
                CGR = PGdb.getStructure(sid)
                skeys = self.graphmatcher.substructure_search(CGR, gid)
                if skeys:
                    PGdb.addStructureKey(sid, gid, skeys)
                    if skeys[0] or skeys[1]:
                        self.group.addFingerprints(gid=gid, sid=sid, skeys=skeys)

