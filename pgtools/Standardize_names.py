#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'arkadiy'
import re
from dbtools.models import PGdb
import configparser

PGdb = PGdb()


class StandardizeNames():
    def __init__(self, file):
        self.__synonyms = configparser.RawConfigParser(delimiters="<")
        self.__synonyms.optionxform = str
        self.__synonyms.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
        self.__synonyms.read_file(file)
        self.standardize()


    def standardize(self):
        for raw_name in PGdb.getAllRowMedia():
            if raw_name in self.__synonyms.options("STANDARD_NAME"):
                stand_name = self.__synonyms.get("STANDARD_NAME", raw_name)
                PGdb.StandardizeNames(raw_name.strip(), stand_name.strip())
