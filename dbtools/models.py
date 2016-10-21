#!/usr/bin/env python
# -*- coding: utf-8 -*-
from networkx.algorithms import isomorphism as gis

__author__ = 'arkadiy'

import json
from networkx.readwrite import json_graph
from pony.orm import *

db = Database("sqlite", "database.sqlite", create_db=True)

class Reactions(db.Entity):
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
    structures = Required('Structures')
    raw__medias = Set('Raw_Media')


class Groups(db.Entity):
    id = PrimaryKey(int, auto=True)
    group_name = Optional(str)
    structure_leave = Optional(LongStr)
    group_structures = Set('Group_Structure')
    structure_remain = Optional(LongStr)
    rcf = Set('Reaction_centers_Fingerprints')


class Structures(db.Entity):
    id = PrimaryKey(int, auto=True)
    smiles = Optional(str)
    CGR = Optional(LongStr)
    rs = Set(Reactions)
    group_structures = Set('Group_Structure')
    rcf = Set('Reaction_centers_Fingerprints')


class Tags(db.Entity):
    id = PrimaryKey(int, auto=True)
    tag = Optional(str)
    media = Set('Media')


class Media(db.Entity):
    id = PrimaryKey(int, auto=True)
    compound = Optional(str)
    tags = Set(Tags)
    raw__medias = Set('Raw_Media')


class Group_Structure(db.Entity):
    groups = Required(Groups)
    structures = Required(Structures)
    cleavage = Required(bool, default=False)
    remain = Required(bool, default=False)
    transform = Required(bool, default=False)
    PrimaryKey(groups, structures)


class Raw_Media(db.Entity):
    id = PrimaryKey(int, auto=True)
    reactionss = Set(Reactions)
    media = Optional(Media)
    component = Optional(str)


class Reaction_centers_Fingerprints(db.Entity):
    id = PrimaryKey(int, auto=True)
    structures = Required(Structures)
    groups = Required(Groups)
    class_transformation = Optional(str)
    fingerprint = Optional(str)


sql_debug(False)
db.generate_mapping(create_tables=True)


class PGdb:
    @db_session
    def addConditions(self, rx_id, cond_dict, sid, media):#Добавить условия проведения реакции
        structure = Structures.get(id=sid)
        Reactions(rx_id=rx_id, structures=structure, CL=cond_dict['CL'], LB=cond_dict['LB'], T=cond_dict['T'],
                  P=cond_dict['P'], TIM=cond_dict['TIM'], STP=cond_dict['STP'], YD=cond_dict['YD'], NYD=cond_dict['NYD'],
                  YPRO=cond_dict['YPRO'], CIT=cond_dict['citation'], TEXT=cond_dict['TXT'],
                  raw__medias = set(select(x for x in Raw_Media if x.component in media)))

    @db_session
    def addGroup(self, structure_l, structure_r, name):#Создает строчку в таблице групп с CGR
        Groups(group_name=name, structure_leave=json.dumps(json_graph.node_link_data(structure_l)),
               structure_remain = json.dumps(json_graph.node_link_data(structure_r)))

    @db_session
    def addFingerprint(self, sid=None, gid=None, classTransformation=None, fingerprint=None):
        structure = Structures.get(id=sid)
        group = Groups.get(id=gid)
        Reaction_centers_Fingerprints(groups=group, structures=structure, class_transformation=classTransformation, fingerprint=json.dumps(fingerprint))

    @db_session
    def addMedia(self, media):#Добавляет стандартные имена химического окружения
        Media(compound=media)

    @db_session
    def addRawMedia(self, component):#Добавляет сырые данные
        Raw_Media(component=component)

    @db_session
    def addStructure(self, smiles, CGR):#Добавляет новую структуру реакции
        Structures(smiles=smiles, CGR=json.dumps(json_graph.node_link_data(CGR)))

    @db_session
    def addStructureKey(self, sid, gid, key_list):#Добавить реляцию ЗГ и Структуры
        structure = Structures.get(id=sid)
        group = Groups.get(id=gid)
        Group_Structure(groups=group, structures=structure, cleavage=key_list[0], remain=key_list[1], transform=key_list[2])

    @db_session
    def addTag(self, tag):#Добавляет тэг в базу
        Tags(tag=tag)

    @db_session
    def addTag_to_Media(self, media, tag):#Делает связь между тэгом и стандартным именем
        tag_db = Tags.get(tag=tag)
        media_db = Media.get(compound=media)
        media_db.tags.add(tag_db)

    @db_session
    def checkStructureKey(self, sid):#Вытаскивает id групп для указанной id структуры
        return list(select(x.groups.id for x in Group_Structure if x.structures.id==sid))

    @db_session
    def getAllStructure(self):#Берет CGR структуры реакции
        for y in select(x.CGR for x in Structures if x.id==1):
            print((json_graph.node_link_graph(json.loads(y))).nodes())
        #return [json_graph.node_link_graph(json.loads(y)) for y in select(x.CGR for x in Structures)]

    @db_session
    def getCondition_id(self, sid):#Посмотрит, есть ли у структуры реляции к условиям
        return list(select(x.rs.id for x in Structures if x.id==sid))

    @db_session
    def get_Conditions(self, rid):#Вытаскивает условия для данной реакции
        conditions = list(select((x.CL, x.LB, x.T, x.P, x.TIM, x.STP, x.YD, x.NYD, x.YPRO, x.CIT, x.TEXT) for x in Reactions if x.id==rid).first())
        return dict(CL=conditions[0], LB=conditions[1], T=conditions[2], P=conditions[3], TIM=conditions[4], STP=conditions[5],
                    YD=conditions[6], NYD=conditions[7], YPRO=conditions[8], citation=conditions[9], TXT=conditions[10])

    @db_session
    def getGroup(self, gid):#Берет группу по данной id
        Group = select(x for x in Groups if x.id==gid).first()
        return [json_graph.node_link_graph(json.loads(Group.structure_leave)),
                json_graph.node_link_graph(json.loads(Group.structure_remain))]

    @db_session
    def getGroupIDs(self):#Берет все имеющиеся id групп
        return list(select(x.id for x in Groups))

    @db_session
    def getGroupID_byCGR(self, CGR):#Поиск ID группы по CGR группы
        self.__node_match=gis.generic_node_match(['element', 's_hyb', 'p_hyb', 's_neighbors', 'p_neighbors'],
                                                   [None]*5, [lambda a, b: b is None or (str(a)==str(b))]*5)
        self.__edge_match = gis.categorical_edge_match(['s_bond', 'p_bond'], [None]*2)
        for id in select(x.id for x in Groups):
            group_l = json_graph.node_link_graph(json.loads(Groups[id].structure_leave))
            GM_l = gis.GraphMatcher(group_l, CGR, node_match=self.__node_match, edge_match=self.__edge_match)
            if GM_l.is_isomorphic():
                return id
            else:
                group_r = json_graph.node_link_graph(json.loads(Groups[id].structure_remain))
                GM_r = gis.GraphMatcher(group_r, CGR, node_match=self.__node_match, edge_match=self.__edge_match)
                if GM_r.is_isomorphic():
                    return id
                else:
                    continue

    @db_session
    def getGroupID_byName(self, Name):#Поиск ID группы по имени группы
        return select(x.id for x in Groups if x.group_name==Name).first()

    @db_session
    def getGroupName_byID(self, id):#Поиск имени группы по ID группы
        return select(x.group_name for x in Groups if x.id==id).first()

    @db_session
    def getMediaID(self, media):#Взять ID компоненты стандартного имени
        return select(x.id for x in Media if x.compound==media).first()

    @db_session
    def getRawMediaID(self, raw_media):#Берет ID сырого имени по данному имени
        return select(x.id for x in Raw_Media if x.component==raw_media).first()

    @db_session
    def getAllRowMedia(self):#Берет все сырые имена для стандартизации
        return list(select(x.component for x in Raw_Media))

    @db_session
    def getAllRowMedia_byRID(self, rid):#Берет все сырые имена по id реакции
        return list(select(x.component for x in Raw_Media if rid in x.reactionss.id))

    @db_session
    def get_ReactionID_byStructureID(self, sid):#Вытаскивает id описаний условий для данной структуры
        return list(select(x.rs.id for x in Structures if x.id==sid))

    @db_session
    def getStructure(self, sid):#Берет CGR структуры реакции по данной ID
        return json_graph.node_link_graph(json.loads(select(x.CGR for x in Structures if x.id==sid).first()))

    @db_session
    def getStructureID(self, smiles):#Берет ID структуры реакции по данному smiles
        return select(x.id for x in Structures if x.smiles==smiles).first()

    @db_session
    def getStructureIDs(self):#Берет ID всех структур
        return list(select(x.id for x in Structures))

    @db_session
    def get_StructureIDs_forPG(self, group=None, cleavage=True, remaining=True, transforming=True):#Вытаскивает id структур,где интересующая группа уходит, остается и/или трансформируется
        return [list(select(x.structures.id for x in Group_Structure if (x.cleavage==cleavage and x.groups.id==self.getGroupID_byName(group)))),\
               list(select(x.structures.id for x in Group_Structure if (x.remain==remaining and x.groups.id==self.getGroupID_byName(group)))),\
                list(select(x.structures.id for x in Group_Structure if (x.transform==transforming and x.groups.id==self.getGroupID_byName(group))))]

    @db_session
    def getTagID(self, tag):#Вытаскивает ID тэга
        return select(x.id for x in Tags if x.tag==tag).first()

    @db_session
    def getTagsForReaction(self, rid):
        reaction = Reactions.get(id=rid)
        medias = []
        for r in reaction.raw__medias:
            if r.media:
                medias.append(r.media)
        tags=[]
        for media in medias:
            tags.append(list(media.tags.tag))
        return tags

    @db_session
    def StandardizeNames(self, raw_name, stand_name):#Стандартизирует сырые имена из базы
        raw_media = Raw_Media.get(component=raw_name)
        stand_media = Media.get(compound=stand_name)
        raw_media.media = stand_media

    @db_session
    def get_kid_number(self):#Смотрит количество реляций структура-группа
        return count(x for x in Group_Structure)

    @db_session
    def getPG_Statistic(self, gid, marker):#Берет статистику по номеру защитной группы
        if marker=="l":
            return count(x for x in Group_Structure if x.groups.id==gid and x.cleavage==True)
        if marker=="r":
            return count(x for x in Group_Structure if x.groups.id==gid and x.remain==True)
        if marker=="t":
            return count(x for x in Group_Structure if x.groups.id==gid and x.transform==True)
        else:
            return count(x for x in Group_Structure if x.groups.id==gid and x.cleavage==True), \
                    count(x for x in Group_Structure if x.groups.id==gid and x.remain==True), \
                    count(x for x in Group_Structure if x.groups.id==gid and x.transform==True)

    @db_session
    def get_ReactionRXID(self, gid=None, cleavage=True, remaining=True, transforming=True):
        structures_leave = select(x.structures for x in Group_Structure if x.groups.id==gid and x.cleavage==cleavage)
        structures_remain = select(x.structures for x in Group_Structure if x.groups.id==gid and x.remain==remaining)
        structures_transform = select(x.structures for x in Group_Structure if x.groups.id==gid and x.transform==transforming)
        return [select(y.rx_id for y in Reactions if y.structures==i).first() for i in structures_leave], \
               [select(y.rx_id for y in Reactions if y.structures==i).first() for i in structures_remain], \
               [select(y.rx_id for y in Reactions if y.structures==i).first() for i in structures_transform]

    @db_session
    def get_ReaxysID_by_ReactionID(self, rid):#Вытащить Reaxys id для заданной id реакции в базе
        return select(x.rx_id for x in Reactions if x.id==rid).first()

    @db_session
    def removePG(self,PGid):
        #delete(x for x in Group_Structure if x.groups==PGid)
        Groups[PGid].delete()

    @db_session
    def get_PGlist(self):#Выдает список защитных групп
        return list(select(x.group_name for x in Groups))

    @db_session
    def get_HightYield(self, Ryield):
        Rnumber=0
        for nyd in select(x.NYD for x in Reactions).without_distinct():
            if nyd:
                if "|" in nyd:
                    nyd = str(nyd).strip().split("|")[0].strip()
                if float(nyd)>=Ryield:
                    Rnumber+=1
        return Rnumber

    @db_session
    def get_StructureIDs_forPG_and_Cat(self, group=None, cleavage=True, remaining=True, transforming=True, tag=None):#Вытаскивает id структур,где интересующая группа уходит, остается и/или трансформируется
        return [list(select(m.id for m in Structures if m.id in select(k.structures.id for k in Group_Structure if (k.cleavage==cleavage and k.groups.id==self.getGroupID_byName(group)))
                            and tag[0] in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media)
               and tag[1] not in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media))),
                list(select(m.id for m in Structures if m.id in select(k.structures.id for k in Group_Structure if (k.remain==remaining and k.groups.id==self.getGroupID_byName(group)))
               and tag[0] in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media)
               and tag[1] not in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media))),
                list(select(m.id for m in Structures if m.id in select(k.structures.id for k in Group_Structure if (k.transform==transforming and k.groups.id==self.getGroupID_byName(group)))
               and tag[0] in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media)
               and tag[1] not in select(z.tag for x in m.rs for y in x.raw__medias for z in y.media.tags if y.media)))]

    @db_session
    def get_Fingerprints_forPG_and_Cat(self, group=None, PGclass=None, tag=None):#Вытаскивает fingerprint для структуры с интересующими тегами и где интересующая группа имеет интересующий класс
        return list(select((m.fingerprint, m.id) for m in Reaction_centers_Fingerprints if m.groups.id==group and m.class_transformation==PGclass
                            and tag[0] in select(z.tag for x in m.structures.rs for y in x.raw__medias for z in y.media.tags if y.media)
               and tag[1] not in select(z.tag for x in m.structures.rs for y in x.raw__medias for z in y.media.tags if y.media)))

    @db_session
    def get_Groups_for_Reaction(self, sid):#Берет id Защитных Групп, которые соответствуют данному sid
        return list(select(x.group_structures.groups.id for x in Structures if x.id==sid))
'''
    @db_session
    def checkNumber_of_RC(self, sid, gid):#Проверяет количество реакционных центров для данной sid и gid (структуры и группы)
        return count(x for x in Reaction_centers_Fingerprints if x.structures.id==sid and x.groups.id==gid)'''