"""Build the prototypes directory and machine-readable catalog from HTML metadata."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'draft': 'Черновик', 'review': 'На проверке', 'approved': 'Согласован', 'archived': 'Архив'}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ''
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title': self.in_title = True
        if tag == 'meta': self.meta[attrs.get('name', '').lower()] = attrs.get('content', '')
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title += data


def collect(root=ROOT):
    folder = root / 'prototypes'
    records = []
    for path in sorted(folder.rglob('*')):
        rel = path.relative_to(folder)
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {'.html', '.htm'}:
            continue
        if rel.as_posix() == 'index.html' or any(p.startswith('.') for p in rel.parts):
            continue
        if any(p.is_symlink() for p in path.parents if p != folder and folder in p.parents):
            continue
        parser = Metadata()
        parser.feed(path.read_text(encoding='utf-8'))
        meta = parser.meta
        status = meta.get('prototype-status', 'draft')
        if status not in STATUSES:
            raise ValueError(f'{rel}: unknown prototype-status {status!r}')
        links = {}
        for field in ('task', 'figma', 'approval'):
            value = meta.get('prototype-' + field, '').strip()
            if value and (urlsplit(value).scheme not in {'https', 'http'} or not urlsplit(value).netloc):
                raise ValueError(f'{rel}: prototype-{field} must be an HTTP(S) URL')
            links[field] = value
        if status == 'approved' and not links['approval']:
            raise ValueError(f'{rel}: approved requires prototype-approval URL')
        records.append({
            'path': rel.as_posix(), 'url': quote(rel.as_posix(), safe='/'),
            'title': ' '.join(parser.title.split()) or path.stem,
            'description': meta.get('description', ''), 'status': status,
            'kind': 'example' if meta.get('prototype-kind') == 'example' else 'prototype',
            **links,
        })
    return records


def build(root=ROOT):
    records=collect(root)
    (root/'prototypes/catalog.json').write_text(json.dumps({'schema_version':1,'items':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return records

if __name__ == '__main__':
    print(f'Built prototypes catalog: {len(build())} HTML files')
