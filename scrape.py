#!/usr/bin/env python3
"""Mini site mirror usando apenas stdlib. Baixa nunaresidencial.com.br
para HTML/CSS/JS/imagens/fonts estaticos com caminhos relativos."""
import os, re, sys, urllib.request, urllib.parse, hashlib, ssl

BASE = "https://nunaresidencial.com.br/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
HOST = urllib.parse.urlparse(BASE).netloc

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

downloaded = {}   # absolute url -> local relative path
queue = []

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": BASE})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read(), r.headers.get("Content-Type", "")

def local_path_for(url):
    """Mapeia url absoluta -> caminho local relativo dentro de OUT."""
    p = urllib.parse.urlparse(url)
    path = p.path
    if path in ("", "/"):
        path = "/index.html"
    # query vira parte do nome pra evitar colisao
    rel = path.lstrip("/")
    if p.query:
        h = hashlib.md5(p.query.encode()).hexdigest()[:8]
        root, ext = os.path.splitext(rel)
        rel = f"{root}.{h}{ext}"
    if rel.endswith("/"):
        rel += "index.html"
    if not os.path.splitext(rel)[1]:
        rel = rel.rstrip("/") + "/index.html"
    return rel

ASSET_EXTS = {".css",".js",".mjs",".png",".jpg",".jpeg",".gif",".webp",".svg",
              ".ico",".bmp",".avif",".woff",".woff2",".ttf",".eot",".otf",
              ".mp4",".webm",".ogg",".mp3",".wav",".pdf"}

def is_same_host(url):
    return urllib.parse.urlparse(url).netloc in ("", HOST)

def is_asset(url):
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    return ext in ASSET_EXTS

def save(rel, data):
    full = os.path.join(OUT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)

def enqueue(url, doc_url=BASE):
    url = url.split("#")[0]
    if not url or url.startswith("data:") or url.startswith("javascript:") or url.startswith("mailto:") or url.startswith("tel:"):
        return None
    absu = urllib.parse.urljoin(doc_url, url)
    if not absu.startswith("http"):
        return None
    if not is_same_host(absu):
        return None  # mantem assets de terceiros como URL absoluta (CDN, fonts google etc)
    # so baixa assets reais; ignora paginas/feeds/wp-json (mirror visual de 1 pagina)
    if absu != BASE and not is_asset(absu):
        return None
    if absu in downloaded:
        return downloaded[absu]
    rel = local_path_for(absu)
    downloaded[absu] = rel
    queue.append(absu)
    return rel

# regexes de extracao
RE_ATTR = re.compile(r'(href|src|data-src|data-bg|data-background|data-lazy-src|data-large_image|poster|content)\s*=\s*["\']([^"\']+)["\']', re.I)
RE_SRCSET = re.compile(r'srcset\s*=\s*["\']([^"\']+)["\']', re.I)
RE_CSSURL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)
RE_CSSIMPORT = re.compile(r'@import\s+["\']([^"\']+)["\']', re.I)

def rel_from(from_rel, to_rel):
    """caminho relativo de from_rel(arquivo) para to_rel(target)."""
    from_dir = os.path.dirname(from_rel)
    try:
        r = os.path.relpath(to_rel, from_dir or ".")
    except ValueError:
        r = to_rel  # mounts diferentes (windows) -> usa caminho como esta
    return r.replace(os.sep, "/")

def process_html(url, rel, data):
    html = data.decode("utf-8", "replace")

    def repl_attr(m):
        attr, val = m.group(1), m.group(2)
        # content= so reescreve se parecer URL de asset (og:image etc)
        if attr.lower() == "content" and not re.match(r'https?://', val):
            return m.group(0)
        target = enqueue(val, url)
        if target is None:
            return m.group(0)
        return f'{attr}="{rel_from(rel, target)}"'

    def repl_srcset(m):
        parts = []
        for chunk in m.group(1).split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            bits = chunk.split()
            u = bits[0]
            target = enqueue(u, url)
            if target:
                bits[0] = rel_from(rel, target)
            parts.append(" ".join(bits))
        return 'srcset="' + ", ".join(parts) + '"'

    def repl_cssurl(m):
        target = enqueue(m.group(1), url)
        if target is None:
            return m.group(0)
        return f'url("{rel_from(rel, target)}")'

    html = RE_SRCSET.sub(repl_srcset, html)
    html = RE_ATTR.sub(repl_attr, html)
    html = RE_CSSURL.sub(repl_cssurl, html)  # inline style url()
    save(rel, html.encode("utf-8"))

def process_css(url, rel, data):
    css = data.decode("utf-8", "replace")
    def repl(m):
        target = enqueue(m.group(1), url)
        if target is None:
            return m.group(0)
        return f'url("{rel_from(rel, target)}")'
    def repl_imp(m):
        target = enqueue(m.group(1), url)
        if target is None:
            return m.group(0)
        return f'@import "{rel_from(rel, target)}"'
    css = RE_CSSURL.sub(repl, css)
    css = RE_CSSIMPORT.sub(repl_imp, css)
    save(rel, css.encode("utf-8"))

def main():
    enqueue(BASE)
    i = 0
    while queue:
        url = queue.pop(0)
        rel = downloaded[url]
        i += 1
        try:
            data, ctype = fetch(url)
        except Exception as e:
            print(f"  [ERRO] {url} -> {e}")
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext in (".html", ".htm") or "text/html" in ctype:
            print(f"[{i}] HTML  {url}")
            process_html(url, rel, data)
        elif ext == ".css" or "text/css" in ctype:
            print(f"[{i}] CSS   {url}")
            process_css(url, rel, data)
        else:
            print(f"[{i}] ASSET {url}")
            save(rel, data)
    print(f"\nConcluido. {len(downloaded)} arquivos em {OUT}")

if __name__ == "__main__":
    main()
