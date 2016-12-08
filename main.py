import argparse
import importlib
from importlib.util import find_spec
from PGAtools.version import version
from PGAtools.parsers import populate


def parse_args():
    parser = argparse.ArgumentParser(description="PGA tools", epilog="(c) Sveta Musaeva", prog='pgatools')
    parser.add_argument("--version", "-v", action="version", version=version(), default=False)
    subparsers = parser.add_subparsers(title='subcommands', description='available utilities')

    populate(subparsers)

    if find_spec('argcomplete'):
        argcomplete = importlib.import_module('argcomplete')
        argcomplete.autocomplete(parser)

    return parser


def main():
    parser = parse_args()
    args = parser.parse_args()
    if 'func' in args:
        args.func(**vars(args))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
