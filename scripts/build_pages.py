"""Build a static catalog without changing prototype source files. No dependencies."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '_site'
EXCLUDED = {'work', '_site', 'scripts', 'node_modules', '.git', '.github'}
ASSETS = {'.html', '.htm', '.css', '.js', '.mjs', '.json', '.png', '.jpg', '.jpeg',
          '.gif', '.webp', '.avif', '.svg', '.ico', '.woff', '.woff2', '.ttf',
          '.otf', '.mp4', '.webm', '.mp3', '.wav', '.ogg', '.wasm', '.webmanifest'}
LABELS = {
    'balance-transfer': ('Перенос баланса', 'Переводы'),
    'currency-switch': ('Переключение валюты', 'Платежи'),
    'full-splash-soft-conic': ('Сплэш · мягкий градиент', 'Вход и сплэш'),
    'full-splash': ('Сплэш · полный сценарий', 'Вход и сплэш'),
    'index-black': ('Пополнение · чёрные кнопки', 'Платежи'),
    'index-blue': ('Пополнение · синие кнопки', 'Платежи'),
    'main': ('Главный экран', 'Вход и сплэш'),
    'new-login-t': ('Вход · новая версия', 'Вход и сплэш'),
    'plastic-gift': ('Пластиковая карта', 'Карты'),
    'ppm-loader': ('Лоадер ППМ', 'Компоненты'),
    'splash-auth': ('Сплэш и авторизация', 'Вход и сплэш'),
    'splash-screen': ('Сплэш-экран', 'Вход и сплэш'),
    'success': ('Экран успеха', 'Компоненты'),
    'tid-login': ('Вход с T-ID', 'Вход и сплэш'),
    'ua-ban': ('Предупреждение об операции', 'Компоненты'),
}


def source_files():
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED or part.startswith('.') for part in rel.parts):
            continue
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in ASSETS:
            yield path


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and (name == 'src' or (name == 'href' and tag in {'link', 'a'})):
                self.references.append(value)


def details(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    match = re.search(r'<title[^>]*>(.*?)</title>', text, re.I | re.S)
    raw_title = re.sub(r'\s+', ' ', match.group(1)).strip() if match else path.stem
    title, category = LABELS.get(path.stem, (raw_title, 'Другие прототипы'))
    rel = path.relative_to(ROOT).as_posix()
    if len(path.relative_to(ROOT).parts) > 1:
        category = path.relative_to(ROOT).parts[0]
    parser = ResourceParser()
    parser.feed(text)
    missing = []
    for ref in parser.references:
        url = urlsplit(ref)
        if url.scheme or url.netloc or not url.path:
            continue
        local = unquote(url.path)
        target = ROOT / local.lstrip('/') if local.startswith('/') else path.parent / local
        if not target.exists():
            missing.append(local)
    return title, category, rel, sorted(set(missing))


def catalog(items):
    cards = []
    for number, (title, category, rel, missing) in enumerate(items, 1):
        note = ('Нужен ресурс: ' + ', '.join(missing)) if missing else 'Самостоятельный HTML-прототип'
        cards.append(f'''<a class="card" href="{quote(rel, safe='/')}" data-category="{escape(category, quote=True)}">
          <div class="card-top"><span class="tag">{escape(category)}</span><span class="arrow" aria-hidden="true">↗</span></div>
          <div class="card-art" aria-hidden="true"><span>{number:02d}</span><div class="phone"><i></i><b></b><b></b><em></em></div></div>
          <h2>{escape(title)}</h2><p class="filename">{escape(rel)}</p><p class="note{' warning' if missing else ''}">{escape(note)}</p>
        </a>''')
    categories = sorted({item[1] for item in items})
    options = ''.join(f'<option value="{escape(c, quote=True)}">{escape(c)}</option>' for c in categories)
    return TEMPLATE.replace('@@COUNT@@', str(len(items))).replace('@@OPTIONS@@', options).replace('@@CARDS@@', '\n'.join(cards))


TEMPLATE = '''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Каталог интерактивных прототипов ППМ. Откройте любой прототип по прямой ссылке.">
<title>ППМ — библиотека прототипов</title><style>
:root{color-scheme:dark;--bg:#101114;--panel:#191b20;--line:#2d3039;--muted:#a2a8b8;--accent:#8eaaff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#f5f6fa;font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit}header,main,footer{max-width:1240px;margin:auto;padding-left:40px;padding-right:40px}header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-top:30px;padding-bottom:30px;border-bottom:1px solid var(--line)}.brand{font-size:22px;font-weight:800;letter-spacing:-1px;text-decoration:none}.brand span{color:var(--accent)}.header-label{font-size:12px;letter-spacing:.13em;color:var(--muted);text-transform:uppercase}.hero{padding:64px 0 38px}.eyebrow{color:var(--accent);font-size:12px;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(36px,6vw,66px);line-height:1.08;letter-spacing:-.05em;margin:18px 0 24px;font-weight:650}.intro{color:var(--muted);max-width:610px;font-size:18px;margin:0}.toolbar{display:flex;gap:12px;align-items:center;margin:0 0 18px}input,select{font:inherit;color:inherit;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;min-width:0}input{flex:1}select{width:240px}input:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:4px}.result{color:var(--muted);font-size:13px;margin:0 0 22px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.card{display:block;min-width:0;text-decoration:none;border:1px solid var(--line);border-radius:18px;background:var(--panel);padding:20px;transition:border-color .15s,transform .15s}.card:hover{border-color:var(--accent);transform:translateY(-3px)}.card-top{display:flex;align-items:center;justify-content:space-between;gap:10px}.tag{font-size:11px;letter-spacing:.03em;color:#b8c2da;border:1px solid #353b49;padding:4px 9px;border-radius:20px}.arrow{font-size:21px;color:var(--muted)}.card-art{height:140px;position:relative;display:flex;align-items:center;justify-content:space-between;overflow:hidden;padding:12px 24px 0 8px;margin-top:14px;color:#4c5876}.card-art>span{font-size:70px;font-weight:300;letter-spacing:-.08em}.phone{height:122px;width:74px;transform:rotate(12deg);border:2px solid #576b9e;border-radius:16px;padding:10px;background:linear-gradient(145deg,#2d3d62,#192234);box-shadow:0 12px 24px #0003}.phone i{display:block;width:20px;height:4px;background:#7185b3;margin:0 auto 20px;border-radius:8px}.phone b{display:block;height:7px;margin:6px 0;background:#819bd1;border-radius:4px}.phone b+b{width:60%;background:#4a608b}.phone em{display:block;height:20px;margin-top:17px;background:#819fe9;border-radius:6px}.card:nth-child(3n+2) .phone{transform:rotate(-10deg)}.card:nth-child(3n+3) .phone{background:linear-gradient(145deg,#353c58,#1c2030)}h2{font-size:19px;font-weight:600;letter-spacing:-.02em;margin:18px 0 6px}.filename{font:11px/1.6 ui-monospace,SFMono-Regular,monospace;color:var(--muted);overflow-wrap:anywhere;margin:0}.note{font-size:12px;color:var(--muted);margin:16px 0 0}.warning{color:#e9be7e}.empty{padding:40px 0;color:var(--muted)}[hidden]{display:none!important}footer{margin-top:64px;padding-top:24px;padding-bottom:32px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;display:flex;justify-content:space-between;gap:16px}footer a{text-decoration:none}footer a:hover{text-decoration:underline}@media(max-width:980px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){header,main,footer{padding-left:20px;padding-right:20px}.header-label{font-size:10px}.hero{padding-top:42px}h1{font-size:42px}.intro{font-size:16px}.toolbar{flex-direction:column;align-items:stretch}input,select{width:100%}.grid{grid-template-columns:1fr}.card-art{height:120px}footer{flex-direction:column}}@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style></head><body>
<header><a class="brand" href="./">ППМ<span> / </span>Design</a><span class="header-label">Библиотека прототипов</span></header>
<main><section class="hero"><div class="eyebrow">Design playground · @@COUNT@@ прототипов</div><h1>От идеи<br>к взаимодействию.</h1><p class="intro">Рабочие сценарии, экраны и компоненты ППМ. Выберите прототип — каждый открывается отдельной страницей и доступен по прямой ссылке.</p></section>
<div class="toolbar"><input id="search" type="search" aria-label="Поиск прототипов" placeholder="Найти по названию или файлу…"><select id="category" aria-label="Раздел"><option value="">Все разделы</option>@@OPTIONS@@</select></div>
<p class="result" id="result" aria-live="polite">Показано @@COUNT@@ из @@COUNT@@</p><section class="grid" aria-label="Прототипы">@@CARDS@@</section><p class="empty" id="empty" hidden>Ничего не найдено. Попробуйте другое название или раздел.</p>
<noscript><p class="note">Все ссылки работают без JavaScript. Поиск и фильтр доступны при его включении.</p></noscript></main>
<footer><span>ППМ / Design · Откройте прототип и поделитесь его ссылкой</span><a href="https://github.com/ppvm-ut/ppm-design">Репозиторий ↗</a></footer>
<script>
const search=document.querySelector('#search'),category=document.querySelector('#category'),cards=[...document.querySelectorAll('.card')];
function filter(){const query=search.value.trim().toLocaleLowerCase('ru');let count=0;for(const card of cards){const visible=card.textContent.toLocaleLowerCase('ru').includes(query)&&(!category.value||card.dataset.category===category.value);card.hidden=!visible;if(visible)count++;}document.querySelector('#result').textContent=`Показано ${count} из ${cards.length}`;document.querySelector('#empty').hidden=count!==0;}
search.addEventListener('input',filter);category.addEventListener('change',filter);
</script></body></html>'''


def main():
    files = list(source_files())
    prototypes = [p for p in files if p.suffix.lower() in {'.html', '.htm'} and p != ROOT / 'index.html']
    items = [details(path) for path in prototypes]
    if not items:
        raise SystemExit('No prototypes found; refusing to publish an empty catalog.')
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()
    for path in files:
        if path == ROOT / 'index.html':
            continue
        target = DEST / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    html = catalog(items)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    (DEST / 'index.html').write_text(html, encoding='utf-8')
    (DEST / '.nojekyll').touch()
    for _, _, rel, missing in items:
        for ref in missing:
            print(f'WARNING: {rel}: missing resource {ref}')
    print(f'Built {len(items)} prototypes in {DEST}')


if __name__ == '__main__':
    main()
