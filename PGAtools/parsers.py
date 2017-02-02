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
import argparse
import importlib
from importlib.util import find_spec
from .cli.main_populate import populate_core
from .cli.main_media import media_core
from .cli.main_groups import groups_core


def populate(subparsers):
    parser = subparsers.add_parser('populate', help='DB populate',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input', '-i', default='input.rdf', type=argparse.FileType('r'),
                        help='RDF inputfile')
    parser.add_argument('--parser', '-p', default='reaxys', choices=['reaxys'], type=str, help='Data Format')
    parser.add_argument('--chunk', '-c', default=100, type=int, help='Chunks size')
    parser.set_defaults(func=populate_core)


def tag_processing(subparsers):
    parser = subparsers.add_parser('media_processing', help='DB media and tag processing',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file', '-f', default='file.cfg', type=str, help='tags dictionary')
    parser.add_argument('--update', '-u', action='store_true', help="update tags")
    parser.set_defaults(func=media_core)


def groups_processing(subparsers):
    parser = subparsers.add_parser('group_analysis', help='Reaction groups processing',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input', '-i', default='input.rdf', type=argparse.FileType('r'),
                        help='RDF inputfile')
    parser.set_defaults(func=groups_core)


def parse_args():
    parser = argparse.ArgumentParser(description="PGA tools", epilog="(c) Sveta Musaeva", prog='pgatools')
    parser.add_argument("--version", "-v", action="version", version=version(), default=False)
    subparsers = parser.add_subparsers(title='subcommands', description='available utilities')

    populate(subparsers)
    tag_processing(subparsers)
    groups_processing(subparsers)

    if find_spec('argcomplete'):
        argcomplete = importlib.import_module('argcomplete')
        argcomplete.autocomplete(parser)

    return parser


def launcher():
    parser = parse_args()
    args = parser.parse_args()
    if 'func' in args:
        args.func(**vars(args))
    else:
        parser.print_help()
