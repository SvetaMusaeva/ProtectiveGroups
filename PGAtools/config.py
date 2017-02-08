# -*- coding: utf-8 -*-
#
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
from enum import Enum
from os import path

# dynamic
DEBUG = False
DB_USER = None
DB_PASS = None
DB_HOST = None
DB_NAME = None
DB_DATA = None
FP_DEEP = 6


class GroupStatus(Enum):
    CLEAVAGE = 0
    REMAIN = 1
    TRANSFORM = 2


config_list = ('DB_USER', 'DB_PASS', 'DB_HOST', 'DB_BASE', 'DB_DATA', 'FP_DEEP')

config_load_list = ['DEBUG']
config_load_list.extend(config_list)

if not path.exists(path.join(path.dirname(__file__), "config.ini")):
    with open(path.join(path.dirname(__file__), "config.ini"), 'w') as f:
        f.write('\n'.join('%s = %s' % (x, y) for x, y in globals().items()
                          if x in config_list))

with open(path.join(path.dirname(__file__), "config.ini")) as f:
    for line in f:
        try:
            k, v = line.split('=')
            k = k.strip()
            v = v.strip()
            if k in config_load_list:
                globals()[k] = int(v) if v.isdigit() else v
        except:
            pass
