import re
import configparser
from pony.orm import db_session, select
from ..models import RawMedias, Medias


def media_core(**kwargs):
    s = configparser.RawConfigParser(delimiters="<")
    s.optionxform = str
    s.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
    if kwargs['update']:
        s.read_file(open(kwargs['file']))
        with db_session:
            for k, v in s['STANDARD_NAME'].items():
                r = RawMedias.get(name=k)
                if r:
                    r.update_media(v)

            for k, v in s['TAGS'].items():
                m = Medias.get(name=k)
                if m:
                    m.update_tags(v.split(','))

    else:
        s.add_section('|STANDARD_NAME|')
        with db_session:
            for name in select(x.name for x in RawMedias if not x.media):
                s.set('|STANDARD_NAME|', name, name)

        s.write(open(kwargs['file'], 'w'))
