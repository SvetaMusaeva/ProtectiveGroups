#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pgtools.Generate_fingerprints import Generate_fingerprints

__author__ = 'arkadiy'

import argparse
from pgtools.WebMode import WebMode
from pgtools.Media import Media
from pgtools.Protective_Group import Protective_Groups
from pgtools.Reactions import Reactions
from pgtools.Statistic_for_Green import Statistic
from pgtools.ValidationMode import ValidationMode
from pgtools.Standardize_names import StandardizeNames


def run():
    parser = arg_parser()
    args=parser.parse_args()
    if args.mode==0:#Добавить реакции
        reactions = Reactions(args)
    elif args.mode==1:#Добавить защитную(ые) группу(ы)
        groups = Protective_Groups(args)
    elif args.mode==2:#Добавить в базу стандартные имена, а также их теги
        media = Media(args.dictionary)
    elif args.mode==3:#Стандартизовать имена
        standardization = StandardizeNames(args.dictionary)
    elif args.mode==4:#Делать статистику
        statistic = Statistic(args)
    elif args.mode==5:#Валидация Similarity подхода
        validate = ValidationMode(args)
    elif args.mode==6:#Работа с сайтом
        web = WebMode(args)
    elif args.mode==7:#Сгенирировать фингерпринты
        fingerprints = Generate_fingerprints(args)

def arg_parser():
    parser = argparse.ArgumentParser(description="PGs tool", epilog="(c) Arkadiy Lin", prog='dbtools')
    parser.add_argument("--input", "-i", default="input.rdf", type=argparse.FileType('r'),
                        help="RDF inputfile")
    parser.add_argument("--output", "-o", default="output.txt", type=argparse.FileType('w'),
                        help="Statistic outputfile")
    parser.add_argument("--dictionary", "-d", default="SystemFiles/Synonyms.cfg", type=argparse.FileType('r'),
                        help="Media dictionary inputfile")
    parser.add_argument("--fields", "-f", default=['RX_ID', 'RX_NVAR', 'RX_RCT', 'RX_PRO', 'RX_SMILES',
                                                    'CL', 'LB', 'STP', 'TIM', 'COND', 'COM', 'YPRO', 'YD',
                                                    'NYD', 'RGT', 'CAT', 'SOL', 'citation', 'P', 'SUB',
                                                    'T', 'TXT', 'LCN'], action='append',
                        help="Typing of interested fields")
    parser.add_argument("--configuration_file", "-cf", default="SystemFiles/Settings.cfg", type=argparse.FileType('r'),
                        help="Configuration file for condenser, fragmentor and fingerprint preparing.")
    parser.add_argument("--query_file", "-qf", default="SystemFiles/MediaQueries.cfg", type=argparse.FileType('r'),
                        help="Query file where you can build your query. The form of this file is:\n"
                             "[<Name of query (i.e. Query1)>]\n"
                             "Names: <Names for table rows in single quotation marks('')(i.e. 'Pd/C catalyst')>\n"
                             "Groups: <Name(s) of PG(s) as it is(are) in DB in single quotation marks('')(i.e. 'Benzyl alcohols')>\n"
                             "Tags: <The list of tags' sets wrote in square brackets. All tags should be writen in "
                             "single quotation marks(''). Also you can use logical operands: !- does not contain, "
                             "N('tag')='value'- how many times the same tag should be in DB for each reaction."
                             "For example, ['Pd',!'acid',N('catalys')=1],['Pt','acid',N('catalyst')=1].>.")
    parser.add_argument("--mode", "-m", default=0, type=int,
                        help="Work mode: 0 - reactions addition to database; 1 - Protective Group(s) addition to database;"
                             "2 - standard names and their tags addition or updating in database; 3 - standardize media names;"
                             "4 - get statistic; 5 - similarity approach validation; 6 - web-mode; 7 - fingerprints generating.")
    parser.add_argument("--reaction_center_deep", "-rcd", default=2, type=int,
                        help="The number of atoms around the reaction center which should be added to subgraph of reaction center.")
    parser.add_argument("--user_reaction", "-ur", default=None, type=argparse.FileType('r'),
                        help="User's RDF file with reaction, obtained from the website.")
    parser.add_argument("--user_tags", "-ut", default=[['Pd'], ['Ni'], ['Pt'], ['Rh'], ['Lindlar']], action='append',
                        help="User's list of tags used for the results clustering. In turn, the each element in the list"
                             " is a python list with tags described each catalyst as user prefer.")
    parser.add_argument("--threads", "-th", default=2, type=int, help="Number of threads used in parallel computing.")
    parser.add_argument("--kNN_neighbors", "-k", default=8, type=int, help="Number of neighbors in kNN method.")
    parser.add_argument("--kNN_delta", "-kNNd", default=2, type=int, help="Value of delta which is needed to choose the class of transformation.")

    return parser


if __name__=="__main__":
    run()