"""Build the prototypes directory and machine-readable catalog from HTML metadata."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://github.com/ppvm-ut/ppm-design/tree/main/prototypes'
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


def render(records):
    cards=[]
    for record in records:
        e = lambda key: escape(record[key], quote=True)
        links = ''.join(f'<a href="{e(field)}">{label} ↗</a>' for field,label in [('task','Задача'),('figma','Figma'),('approval','Согласование')] if record[field])
        label = 'Технический пример' if record['kind'] == 'example' else STATUSES[record['status']]
        cards.append(f'<article class="card" data-status="{e("status")}" data-kind="{e("kind")}"><span class="badge">{label}</span><h2><a href="{e("url")}">{e("title")}</a></h2><p>{e("description")}</p><code>{e("path")}</code><div class="links"><a class="launch" href="{e("url")}">Открыть прототип ↗</a>{links}</div></article>')
    options=''.join(f'<option value="{key}">{label}</option>' for key,label in STATUSES.items())
    count=sum(x['kind']=='prototype' for x in records)
    template=(ROOT/'scripts/prototypes-catalog.html').read_text(encoding='utf-8')
    return template.replace('@@CARDS@@','\n'.join(cards)).replace('@@OPTIONS@@',options).replace('@@COUNT@@',str(count)).replace('@@SOURCE@@',SOURCE)


def build(root=ROOT):
    records=collect(root)
    (root/'prototypes/index.html').write_text(render(records),encoding='utf-8')
    (root/'prototypes/catalog.json').write_text(json.dumps({'schema_version':1,'items':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return records

if __name__ == '__main__':
    print(f'Built prototypes catalog: {len(build())} HTML files')
