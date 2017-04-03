# -*- coding: utf-8 -*-
#
#  Copyright 2015-2016 Arkadiy Lin <arkadij.lin@rambler.ru>
#  Copyright 2016, 2017 Ramil Nugmanov <stsouko@live.ru>
#  Copyright 2016 Svetlana Musaeva <sveta_musaeva.95@mail.ru>
#  This file is part of PGAtools.
#
#  PGAtools is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
from CGRdb import Loader as CGRLoader
from pony.orm import Database, sql_debug
from .config import DEBUG, DB_PASS, DB_HOST, DB_USER, DB_NAME, DB_CGR_LIST, DB_DATA_LIST
from .models import load_tables


class Loader:
    __schemas = {}
    __databases = {}
    __cgr_database = {}

    @classmethod
    def load_schemas(cls):
        if not cls.__schemas:
            if DEBUG:
                sql_debug(True)

            CGRLoader.load_schemas()
            for cgr_schema, schema in zip(DB_CGR_LIST, DB_DATA_LIST):
                x = Database()
                cgr_molecule, cgr_reaction, *_ = CGRLoader.get_database(cgr_schema)

                cls.__schemas[schema] = x
                cls.__databases[schema] = load_tables(x, schema, cgr_molecule, cgr_reaction)
                cls.__cgr_database[schema] = cgr_schema
                if DEBUG:
                    x.bind('sqlite', 'database.sqlite')
                else:
                    x.bind('postgres', user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)

                x.generate_mapping(create_tables=True)

    @classmethod
    def list_databases(cls):
        return cls.__databases

    @classmethod
    def get_database(cls, name):
        return cls.__databases[name]

    @classmethod
    def get_cgr_database(cls, name):
        return CGRLoader.get_database(cls.__cgr_database[name])
