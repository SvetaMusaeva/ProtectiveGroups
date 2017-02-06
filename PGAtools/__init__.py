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


def init():
    from pony.orm import sql_debug
    from .models import db
    from .config import DEBUG, DB_NAME, DB_DATA, DB_HOST, DB_PASS, DB_USER

    if DEBUG:
        sql_debug(True)
        db.bind('sqlite', 'database.sqlite')
    else:
        db.bind('postgres', user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)

    db.generate_mapping(create_tables=DEBUG)
