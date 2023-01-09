from collections import namedtuple

import flask
from blazeutils.strings import normalizews

from . import markdown

MailParts = namedtuple('MailParts', 'subject text html')


def mail_template(template_name_or_list, **kwargs):
    multi_part_content = flask.render_template(template_name_or_list, **kwargs)
    parts = multi_part_content.split('---multi-part:xFE+Ab7j+w,mdIL%---')
    subject, mdown = map(lambda p: p.strip(), parts)

    return MailParts(normalizews(subject), mdown, markdown.render(mdown))
