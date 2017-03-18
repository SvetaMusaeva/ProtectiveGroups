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
import re
import configparser
from pony.orm import db_session, select
from ..models import RawMedia, Media
from .. import init


def media_core(**kwargs):
    init()
    s = configparser.RawConfigParser(delimiters="<")
    s.optionxform = str
    s.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
    if kwargs['update']:
        s.read_file(open(kwargs['file']))
        with db_session:
            for k, v in s['STANDARD_NAME'].items():
                r = RawMedia.get(name=k)
                if r:
                    r.update_media(v)

            for k, v in s['TAGS'].items():
                m = Media.get(name=k)
                if m:
                    m.update_tags(v.split(','))

    else:
        s.add_section('|STANDARD_NAME|')
        with db_session:
            for name in select(x.name for x in RawMedia if not x.media):
                s.set('|STANDARD_NAME|', name, name)

        s.write(open(kwargs['file'], 'w'))
