import jinja2


def render_page(jinja_template, filename):
    rendered = publish_rst.render_rst_file(filename)

    return jinja_template.render({
        'title': rendered.title,
        'body': rendered.body,
    })
