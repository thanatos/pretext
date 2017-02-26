import argparse
import logging
from os import path as _path
from wsgiref import simple_server

from wob.http import errors as _errors
from wob.http import request as _request
from wob.http import response as _response
from wob.routing import router as _router
from wob.routing import path as _rpath

from . import render
from .. import post_index


class PretextBlog(object):
    def __init__(self, blog_path, renderer):
        self.blog_path = blog_path
        self.renderer = renderer
        self.index = post_index.PostIndex(blog_path)

        self.router = _router.Router()

        def route(path, handler):
            self.router.add_route(
                _rpath.path_rule(path),
                {_router.GET: handler},
            )

        route('/', self.root_page)
        route(
            '/<year:int>/<month:int>/<slug:string>',
            self.post_from_dated_slug,
        )

    def root_page(self, request, _):
        return _response.text_response(
            'The root page (not implemented yet).',
            mimetype='text/html',
        )

    def post_from_dated_slug(self, request, matches):
        year = matches['year']
        month = matches['month']
        slug = matches['slug']

        post_path = self.index.path_for_dated_slug(year, month, slug)
        full_path = _path.join(self.blog_path, post_path)
        page = self.renderer.render_post(full_path)
        return _response.text_response(page, mimetype='text/html')

    def process_request(self, request):
        try:
            response = self.router.route_request(request)
        except _errors.HttpError as err:
            response = _errors.to_simple_text_response(err)

        return response

    def wsgi_app(self, environ, start_response):
        request = _request.request_from_wsgi(environ)
        response = self.process_request(request)
        return response.return_from_wsgi_app(start_response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('blog_path')
    parser.add_argument('--template-config', action='store')
    pargs = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)

    logging.info('Indexing post directory.')
    index = post_index.PostIndex(pargs.blog_path)
    index.rebuild_index()

    if pargs.template_config is None:
        renderer = render.default_renderer()
    else:
        renderer = render.render_config_from_file(pargs.template_config)

    blog = PretextBlog(pargs.blog_path, renderer)
    httpd = simple_server.make_server('localhost', 8000, blog.wsgi_app)
    print('Serving HTTP on port 8000...')

    # Respond to requests until process is killed
    httpd.serve_forever()


if __name__ == '__main__':
    main()
