#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict


class Parser(object):
    def __init__(self):

        self.__fields = dict(COND='conditions', COM='comment', YD='product_yield',
                             TIM='time', STP='steps', T='temperature', P='pressure', TXT='description',
                             citation='citation', RGT=None, CAT=None, SOL=None)

    def parse(self, meta):
        rxds = defaultdict(dict)
        cleaned = dict(rx_id=int(meta['ROOT:RX_ID']))

        for meta_key, meta_value in meta.items():
            *presection, section = meta_key.split(':')
            if presection and section in self.__fields and presection[-1].startswith('RXD('):
                if section in ('CAT', 'SOL', 'RGT'):
                    rxds[presection[-1]].setdefault('media', []).extend(meta_value.split('|'))
                else:
                    rxds[presection[-1]][self.__fields[section]] = meta_value

        cleaned['rxd'] = list(rxds.values())
        return cleaned
