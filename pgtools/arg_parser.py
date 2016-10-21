#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'arkadiy'

import argparse

class arguments_parser:
    def arg_parser(self):
        parser = argparse.ArgumentParser(description="PGs tool", epilog="(c) Arkadiy Lin", prog='dbtools')
        parser.add_argument("--input", "-i", default="None", type=argparse.FileType('r'),
                            help="RDF inputfile")
        parser.add_argument("--output", "-o", default="output.sdf", type=argparse.FileType('w'),
                            help="SDF outputfile")
        parser.add_argument("--synonyms", "-s", default="Synonyms.cfg", type=argparse.FileType('r'),
                            help="Synonyms inputfile")
        parser.add_argument("--fields", "-f", default=['RX_ID', 'RX_NVAR', 'RX_RCT', 'RX_PRO', 'RX_SMILES',
                                                       'CL', 'LB', 'STP', 'TIM', 'COND', 'COM', 'YPRO', 'YD',
                                                       'NYD', 'RGT', 'CAT', 'SOL', 'citation', 'P', 'SUB',
                                                       'T', 'TXT', 'LCN'], action='append',
                            help="Typing of interested fields")
        parser.add_argument("--configuration_file", "-cf", default="Settings.cfg", type=argparse.FileType('r'),
                            help="Configuration file for condenser, fragmentor and fingerprint preparing.")
        parser.add_argument("--mode", "-m", default=0, type=int,
                            help="Work mode: 0 - reactions adding to database; 1 - Protective Group(s) adding to database;"
                                 "2 - get statistic")
        return parser