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
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from importlib.util import find_spec
from .main_groups import groups_core
from .main_media import media_core
from ..config import DB_DATA_LIST
from ..version import version


def tag_processing(subparsers):
    parser = subparsers.add_parser('media', help='DB media and tag processing',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file', '-f', default='file.cfg', type=str, help='tags dictionary')
    parser.add_argument('--update', '-u', action='store_true', help="update tags")
    parser.add_argument('--database', '-d', default=DB_DATA_LIST[0], type=str, choices=DB_DATA_LIST,
                        help='database name')
    parser.set_defaults(func=media_core)


def groups_processing(subparsers):
    parser = subparsers.add_parser('groups', help='Reaction groups processing',
                                   formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input', '-i', default=None, type=FileType(), help='RDF inputfile')
    parser.add_argument('--analyse', '-a', action='store_true', help="analyse groups")
    parser.add_argument('--database', '-d', default=DB_DATA_LIST[0], type=str, choices=DB_DATA_LIST,
                        help='database name')
    parser.set_defaults(func=groups_core)


def argparser():
    parser = ArgumentParser(description="PGA tools", epilog="(c) Sveta Musaeva; (c) Dr. Ramil Nugmanov",
                            prog='pgatools')
    parser.add_argument("--version", "-v", action="version", version=version(), default=False)
    subparsers = parser.add_subparsers(title='subcommands', description='available utilities')

    tag_processing(subparsers)
    groups_processing(subparsers)

    if find_spec('argcomplete'):
        from argcomplete import autocomplete
        autocomplete(parser)

    return parser
