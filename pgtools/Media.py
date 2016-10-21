#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'arkadiy'

from dbtools.models import PGdb
import configparser
import re
PGdb = PGdb()

class Media():
    def __init__(self, file):
        self.__synonyms = configparser.RawConfigParser(delimiters="<")
        self.__synonyms.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
        self.__synonyms.optionxform = str
        self.__synonyms.read_file(file)
        self.addTags()
        print("Tags added!")

    def addTags(self):
        for stand_name, tags in self.__synonyms.items("TAGS"):
            if PGdb.getMediaID(stand_name.strip()):
                pass
            else:
                PGdb.addMedia(stand_name.strip())
            for tag in tags.strip().split(','):
                if PGdb.getTagID(tag.strip()):
                    pass
                else:
                    PGdb.addTag(tag.strip())
                PGdb.addTag_to_Media(stand_name.strip(), tag.strip())

