import logging
from os import path as _path

import attr
import jinja2
import markupsafe
import yaml

from .. import publish_rst


def render_config_from_file(filename):
    with open(filename, 'r') as config_file:
        yaml_data = yaml.load(config_file)

    template_path = yaml_data['template_path']
    # template path is relative to the YAML file:
    yaml_dir = _path.dirname(filename)
    template_path = _path.join(yaml_dir, template_path)
    logging.info('Creating template loader at path: %s', template_path)

    jinja_env = jinja2.Environment(
        autoescape=True,  # jinja why is the default False
        loader=jinja2.FileSystemLoader(template_path),
    )

    return Renderer(jinja_env, Templates(**yaml_data['templates']))


class Renderer(object):
    def __init__(self, jinja_env, templates):
        self.jinja_env = jinja_env
        self.templates = templates

    def render_post(self, filename):
        rendered = publish_rst.render_rst_file(filename)
        template = self.jinja_env.get_template(self.templates.post)
        return template.render({
            'title': rendered.title,
            'body': markupsafe.Markup(rendered.body),
        })


@attr.s
class Templates(object):
    post = attr.ib()
    root = attr.ib()


def default_renderer():
    templates = {
        'base': _DEFAULT_BASE_TEMPLATE,
        'post': _DEFAULT_POST_TEMPLATE,
        #'root': _DEFAULT_ROOT_TEMPLATE,
    }
    jinja_env = jinja2.Environment(
        autoescape=True,
        loader=jinja2.DictLoader(templates),
    )
    return Renderer(jinja_env, Templates(post='post', root='root'))


_DEFAULT_BASE_TEMPLATE = '''\
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{% block title %}{{ title }}{% endblock %}</title>
</head>
<body>
{% block body %}{% endblock %}
</body>
</html>
'''


_DEFAULT_POST_TEMPLATE = '''\
{% extends "base" %}
{% block body %}{{ body }}{% endblock %}
'''
