#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'arkadiy'
from CGRtools.RDFread import RDFread
from pgtools.rdf_parser import rdf_parser
from pgtools.reaction_treatment import Add_Reaction
from pgtools.reaction_treatment import Add_Conditions

class Reactions():
    def __init__(self, args):
        inputdata = RDFread(args.input)
        stand = rdf_parser()
        reactions = Add_Reaction(args)
        conditions = Add_Conditions(args.fields)
        for num, data in enumerate(inputdata.readdata()):
            if num % 1000==0:
                print("reaction: %d" % (num + 1))
            fixed_data = stand.get_standardized(data, args.fields)
            structure_id = reactions.add_Structure(fixed_data)
            if conditions.addConditions(fixed_data, structure_id):
                print("Conditions have been added successfuly!")
            else:
                print("There is an error in conditions addition!")
