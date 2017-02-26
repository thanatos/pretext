import attr
import bs4
import docutils.core
import docutils.io


@attr.attributes
class RenderedRst(object):
    title = attr.attr()
    body_soup = attr.attr()
    metadata = attr.attr()

    @property
    def body(self):
        return ''.join(str(child) for child in self.body_soup.children).strip()


def _remove_section_div(div):
    for child in list(div.children):
        div.insert_before(child)
    div.extract()


def render_rst_file(filename, desouper='lxml'):
    with open(filename, 'rb') as fileobj:
        doc, publisher = docutils.core.publish_programmatically(
            source=fileobj,
            source_class=docutils.io.FileInput,
            source_path=None,
            destination=None,
            destination_class=docutils.io.StringOutput,
            destination_path=None,
            settings=None,
            settings_spec=None,
            settings_overrides={
                'embed_stylesheet': False,
                'halt_level': 3,
            },
            reader=None,
            reader_name='standalone',
            parser=None,
            parser_name='restructuredtext',
            writer=None,
            writer_name='html',
            config_section=None,
            enable_exit_status=False,
        )

    _ = publisher

    # we need to massage the output a tad.
    soup = bs4.BeautifulSoup(doc, features=desouper)

    title = soup.find('title').text
    meta_tags = soup.find('head').find_all('meta')

    metadata = {}
    for meta_tag in meta_tags:
        if 'name' not in meta_tag.attrs:
            continue
        if meta_tag.attrs['name'] == 'generator':
            continue
        metadata[meta_tag.attrs['name']] = meta_tag.attrs['content']

    main_doc = soup.find('div', class_='document')
    children = []

    for div in main_doc.find_all('div', class_='section'):
        _remove_section_div(div)

    return RenderedRst(title, main_doc, metadata)
