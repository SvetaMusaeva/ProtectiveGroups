import re
import configparser
from pony.orm import db_session
from ..models import RawMedias, Medias


def media_core(**kwargs):
    if kwargs['update']:
        s = configparser.RawConfigParser(delimiters="<")
        s.optionxform = str
        s.SECTCRE = re.compile(r"\[\| *(?P<header>[^]]+?) *\|\]")
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
        pass
        # todo: get raw_medias without medias and medias without tags.
