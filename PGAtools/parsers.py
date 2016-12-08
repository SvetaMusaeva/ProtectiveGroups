import argparse
from .cli.main_populate import populate_core


def populate(subparsers):
    parser = subparsers.add_parser('populate', help='DB populate',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", "-i", default="input.rdf", type=argparse.FileType('r'),
                        help="RDF inputfile")

    parser.set_defaults(func=populate_core)
