import jinja2

from .. import publish_rst


def render_post(jinja_template, filename):
    rendered = publish_rst.render_rst_file(filename)

    #return jinja_template.render({
    #    'title': rendered.title,
    #    'body': rendered.body,
    #})
    return rendered.body
