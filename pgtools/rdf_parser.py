#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'arkadiy'


class rdf_parser():
    def get_standardized(self, data, fields_list):
        tmp = dict(id=data['meta']['ROOT:RX_ID'], smiles=data['meta']['ROOT:RX_SMILES'].strip(),
                   substrats=data['substrats'], products=data['products'], meta={})

        for i in range(int(data['meta']['ROOT:RX_NVAR'])):
            tmp['meta'][i]={}
            tmp['meta'][i]['COND_ID']=i+1
            cat_sol_rgt = ''
            for meta_key, meta_value in data['meta'].items():
                section = meta_key.split(':')[-1]#Ключи в RDF типа RX_RCT или RX_NVAR, кроме RX_ID
                if section in fields_list and 'RXD(' not in meta_key and section!='RX_ID' and section!='RX_SMILES':
                    tmp['meta'][i][section] = meta_value
                elif section in fields_list and 'RXD('+str(i+1)+')' in meta_key:
                    if section=='CAT' or section=='SOL' or section=='RGT':
                        cat_sol_rgt+=('|' + meta_value)
                    else:
                        tmp['meta'][i][section] = meta_value

            tmp['meta'][i]['media'] = self.cat_sol_rgtParsing(cat_sol_rgt)
        return tmp

    def cat_sol_rgtParsing(self, cat_sol_rgt):
        csr_list = []
        for element in cat_sol_rgt.split('|'):
            if element.strip():
                csr_list.append(element.strip())
        return csr_list
