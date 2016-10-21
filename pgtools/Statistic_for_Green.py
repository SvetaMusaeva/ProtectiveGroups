#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'arkadiy'

from dbtools.models import PGdb
import configparser
import re

PGdb = PGdb()

class Statistic():
    def __init__(self,args):
        self.__args = args
        self.__queries = configparser.RawConfigParser(delimiters="<")
        self.__queries.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
        self.__queries.optionxform = str
        self.__queries.read_file(self.__args.query_file)
        self.__out = [str(len(self.__queries.sections())) + ' queries(y) have(s) been found in Query file..']
        for query in self.__queries.sections():
            self.__out.append('{0}{1}{0}\n'.format('-'*50, query))
            self.__out.append(query + " is performing..")
            for group in self.__queries.get(query, 'Groups').split('|'):
                if PGdb.getGroupID_byName(group):
                    tags = self.__queries.get(query, 'Tags').split('|')
                    self.statistic_table(self.__queries.get(query, 'Names').strip().split('|'), group, tags)
                else:
                    self.__out.append("For query " + query + " group " + group + " has not been found in the DB!")

        self.writeResult()


    def statistic_table(self, row_names, group, tags):
        self.__out.append('\n{0}\n{2}{1:129}{2}\n{0}\n{2}{3:30}{2}{4:32}{2}{5:32}{2}{6:32}{2}\n{2}{7}{2}{8:20}{2}{9:11}{2}{8:20}{2}{9:11}{2}{8:20}{2}{9:11}{2}\n{0}'.format(
            '-'*131, (group + " Protection").center(129),'|','Row name'.center(30),'Group leaves'.center(32),'Group remains'.center(32),
            'Group transforms'.center(32), ' '*30, 'N'.center(20), 'N, %'.center(11)))
        structures = PGdb.get_StructureIDs_forPG(group=group)
        conditions_l = self.getReactionID(structures[0])
        conditions_r = self.getReactionID(structures[1])
        conditions_t = self.getReactionID(structures[2])
        r_ids = []
        for i, row in enumerate(row_names):
            r_ids.append([])
            conditions_filtered = [self.TagFiltering(conditions_l, tags[i]), self.TagFiltering(conditions_r, tags[i]), self.TagFiltering(conditions_t, tags[i])]#Списки id реакций для ушедшей и оставшейся группы, прошедших фильтрацию по тэгам
            len_l = len(conditions_filtered[0])
            len_r = len(conditions_filtered[1])
            len_t = len(conditions_filtered[2])
            len_summ = len_l+len_r+len_t
            if len_summ:
                self.__out.append('{0}{1:30}{0}{2:20}{0}{5:11}{0}{3:20}{0}{6:11}{0}{4:20}{0}{7:11}{0}'.format('|',row.ljust(30),
                                    str(len_l).center(20), str(len_r).center(20),
                                    str(len_t).center(20), str(round(len_l*100/len_summ, 2)).center(11),
                                    str(round(len_r*100/len_summ, 2)).center(11), str(round(len_t*100/len_summ, 2)).center(11)))
                r_ids[i].append([str(PGdb.get_ReaxysID_by_ReactionID(x)) for x in conditions_filtered[0]])
                r_ids[i].append([str(PGdb.get_ReaxysID_by_ReactionID(x)) for x in conditions_filtered[1]])
                r_ids[i].append([str(PGdb.get_ReaxysID_by_ReactionID(x)) for x in conditions_filtered[2]])

        self.__out.append('-'*131)
        self.__out.append('\n')
        reactions_l = set()
        reactions_r = set()
        reactions_t = set()
        for i, row in enumerate(row_names):
            if r_ids[i]:
                self.__out.append('Reaction IDs for ' + group + ' (' + row + '):')
                self.__out.append('Group leaves - ' + ','.join(r_ids[i][0]))
                self.__out.append('Group remains - ' + ','.join(r_ids[i][1]))
                self.__out.append('Group transforms - ' + ','.join(r_ids[i][2]))
                self.__out.append('\n')
                reactions_l |= set(r_ids[i][0])
                reactions_r |= set(r_ids[i][1])
                reactions_t |= set(r_ids[i][2])
        self.__out.append('\n')
        self.__out.append('Selective reactions with several ' + group + ' groups from CPG and RPG:\n')
        self.__out.append(','.join(list(reactions_l & reactions_r)) + '\n')
        self.__out.append('Selective reactions with several ' + group + ' groups from CPG and TPG:\n')
        self.__out.append(','.join(list(reactions_l & reactions_t)) + '\n')
        self.__out.append('Selective reactions with several ' + group + ' groups from RPG and TPG:\n')
        self.__out.append(','.join(list(reactions_r & reactions_t)) + '\n')
        self.__out.append('Selective reactions with several ' + group + ' groups from all classes:\n')
        self.__out.append(','.join(list((reactions_l & reactions_r) & reactions_t)) + '\n')
        self.__out.append('{0}{1}{0}'.format('*'*50, group + ' PG analysis is finished'))
        self.__out.append('\n')

    def writeResult(self):
        self.__args.output.write('\n'.join(self.__out))
        self.__args.output.close()

    def getReactionID(self, structures):
        tmp = []
        for id in structures:
            tmp+=PGdb.get_ReactionID_byStructureID(id)
        return tmp

    def TagFiltering(self, allid, tags):
        tmp = allid
        tmp_bad = []
        for id in tmp:
            tags_db = PGdb.getTagsForReaction(id)#Выдал список списков (список веществ, для каждого из них список тэгов)
            tags_db_conc = []
            for x in tags_db:#Формирование единого списка тэгов
                tags_db_conc+=x
            for tag_not_stripped in tags.lstrip("[").rstrip("]").split(","):#Фильтрация по тэгам
                tag=tag_not_stripped.strip()
                if '!' in tag:#Следит за присутствием не желательного тэга
                    if id not in tmp_bad and tag.replace("!", "") in tags_db_conc:
                        tmp_bad.append(id)
                        break
                elif re.findall(r'N\(.+\)=\d+', tag):#Следит за количеством тэгов
                    if id not in tmp_bad and tags_db_conc.count(tag.lstrip("N(").rstrip(')=' + tag.split('=')[-1]))!=int(tag.split('=')[-1].strip()):
                        tmp_bad.append(id)
                        break
                elif re.findall(r'(.+) is (.+)', tag):#Отслеживает конструкции something IS something
                    if id not in tmp_bad:
                        tag_existance = False
                        for y in tags_db:
                            if tag.split()[0].strip() in y and tag.split()[-1].strip() in y:
                                tag_existance=True
                                break
                        if tag_existance==False:
                            tmp_bad.append(id)
                            break
                elif re.findall(r'(.+) or (.+)', tag):#Отслеживает конструкции something OR something
                    if id not in tmp_bad:
                        tag_existance = False
                        for or_tags in tag.split(" or "):
                            if or_tags in tags_db_conc:
                                tag_existance=True
                                break
                        if tag_existance==False:
                            tmp_bad.append(id)
                            break
                else:#Определяет наличие интересующего тэга
                    if id not in tmp_bad and tag.strip() not in tags_db_conc:
                        tmp_bad.append(id)
                        break
        return list(set(tmp)-set(tmp_bad))