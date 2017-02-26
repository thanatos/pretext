import contextlib
import logging
import os
from os import path as _path
import sqlite3

import iso8601

from . import publish_rst


class PostIndex(object):
    def __init__(self, path):
        self.path = path
        filename = _path.join(path, 'index')
        self.connection = sqlite3.connect(filename)
        self._create_tables()

    def rebuild_index(self):
        with _wrap_cursor(self.connection.cursor()) as cursor:
            slugs_to_posts = {}
            cursor.execute('DELETE FROM posts;')
            for dirpath, dirnames, filenames in os.walk(self.path):
                if '.git' in dirnames:
                    dirnames.remove('.git')

                for filename in filenames:
                    _, ext = _path.splitext(filename)
                    if ext != '.rst':
                        continue
                    file_path = _path.join(dirpath, filename)
                    meta = publish_rst.parse_meta(file_path)
                    if 'slug' not in meta:
                        logging.error(
                            'File {} lacked a "slug" meta entry.',
                            file_path,
                        )
                        continue
                    if 'author-date' not in meta:
                        logging.error(
                            'File {} lacked a "slug" meta entry.',
                            file_path,
                        )
                        continue

                    slug = meta['slug']
                    date_str = meta['author-date']
                    date = iso8601.parse_date(date_str)

                    slash_len = 0 if self.path.endswith('/') else 1
                    rel_path = file_path[len(self.path) + slash_len:]

                    logging.info(
                        'Found post "%s" from date %s at path %s',
                        slug, date, rel_path,
                    )

                    if slug in slugs_to_posts:
                        logging.error(
                            'Multiple posts have the same slug "{}"!', slug,
                        )
                        _, existing_date, _ = slugs_to_posts[slug]
                        if date < existing_date:
                            slugs_to_posts[slug] = (rel_path, date, date_str)
                    else:
                        slugs_to_posts[slug] = (rel_path, date_str)

            for slug, (rel_path, date_str) in slugs_to_posts.items():
                cursor.execute(
                    'INSERT INTO posts (path, slug, date)'
                    ' VALUES (?, ?, ?)',
                    (rel_path, slug, date_str),
                )
        self.connection.commit()

    def path_for_dated_slug(self, year, month, slug):
        date_like = '{}-{:02}-%'.format(year, month)
        with _wrap_cursor(self.connection.cursor()) as cursor:
            cursor.execute(_FIND_POST_BY_DATED_SLUG, (slug, date_like))
            row = cursor.fetchone()
            if row is None:
                return None
            else:
                path, = row
                return path

    def _create_tables(self):
        with _wrap_cursor(self.connection.cursor()) as cursor:
            cursor.execute(
                'SELECT name FROM sqlite_master WHERE name = \'posts\';'
            )
            existed = cursor.fetchone()
            if not existed:
                cursor.execute(_POSTS_TABLE)
                cursor.execute(_POSTS_TABLE_INDEX)
        self.connection.commit()


_POSTS_TABLE = '''\
CREATE TABLE posts (
    path text,
    slug text,
    date text
);
'''

_POSTS_TABLE_INDEX = '''\
CREATE INDEX posts_by_slug_year ON posts (date, slug);\
'''

_FIND_POST_BY_DATED_SLUG = '''\
SELECT path FROM posts WHERE slug = ? AND date LIKE ?;\
'''


@contextlib.contextmanager
def _wrap_cursor(cursor):
    # Sqlite; yuno have __enter__
    try:
        yield cursor
    finally:
        cursor.close()
