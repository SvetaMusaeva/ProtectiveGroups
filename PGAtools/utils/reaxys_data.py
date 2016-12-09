#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict


class Parser(object):
    def __init__(self, fields=None):

        self.__fields = fields or ['RX_ID', 'RX_NVAR', 'RX_RCT', 'RX_PRO', 'CL', 'LB', 'STP', 'TIM',
                                   'COND', 'COM', 'YPRO', 'YD', 'NYD', 'RGT', 'CAT', 'SOL', 'citation', 'P', 'SUB',
                                   'T', 'TXT', 'LCN']

    def parse(self, meta):
        rxds = defaultdict(dict)
        cleaned = {}
        for meta_key, meta_value in meta.items():
            *presection, section = meta_key.split(':')
            if section in self.__fields:
                if presection and presection[-1].startswith('RXD('):
                    if section in ('CAT', 'SOL', 'RGT'):
                        rxds[presection[-1]].setdefault('media', []).extend(meta_value.split('|'))
                    else:
                        rxds[presection[-1]][section] = meta_value
                else:
                    cleaned[section] = meta_value

        cleaned['rxd'] = list(rxds.values())
        return cleaned
