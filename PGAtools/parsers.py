import argparse
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
