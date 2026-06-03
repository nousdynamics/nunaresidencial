#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otimizacao de performance do site estatico (rodar POR ULTIMO no pipeline).

- Converte imagens grandes (PNG/JPG) para WebP, redimensionando para no maximo
  MAX_W de largura, e reescreve as referencias no HTML.
- Re-encoda os videos MP4 (H.264 720p, faststart) mantendo o nome.
- Remove assets nao referenciados.

Nivel: equilibrado (WebP q82 / max 1600px / video CRF 28 720p).
Ordem: scrape.py -> build-seo.py -> build-form.py -> build-seo.py -> build-optim.py
Idempotente: re-rodar nao reconverte (PNGs ja viraram WebP).
"""
from __future__ import annotations

import pathlib
import re
import subprocess

from PIL import Image

ROOT = pathlib.Path(__file__).parent
SITE = ROOT / "site"
UPLOADS = SITE / "wp-content" / "uploads"

WEBP_Q = 82
MAX_W = 1600
SIZE_THRESHOLD = 120 * 1024  # so converte acima de 120 KB
VIDEO_CRF = "28"
VIDEO_MAX_H = "720"

# Pesos de fonte realmente usados no CSS (verificado: 400/500/600/700, sem italico)
FONT_WEIGHTS = "400,500,600,700"
# Familias Google Fonts carregadas mas nao referenciadas em nenhum seletor -> remover
UNUSED_GF = ["inter"]
# Diretorio de webfonts do Font Awesome (so .woff2 e usado por browser moderno)
FA_FONTS = (SITE / "wp-content" / "plugins" / "elementor"
            / "assets" / "lib" / "font-awesome" / "webfonts")

# CSS decorativo / icones / widgets below-the-fold -> carregar sem bloquear o
# render (media=print + swap no onload, com <noscript> de fallback).
# NAO incluir CSS estrutural/above-fold (post-14, frontend, theme, reset,
# nav-menu, heading, image, swiper) para evitar FOUC.
DEFER_CSS = [
    "font-awesome-5-all", "font-awesome-4-shim",
    "widget-image-carousel", "widget-call-to-action", "e-transitions",
    "widget-nested-carousel", "widget-spacer", "widget-video",
    "widget-social-icons", "e-apple-webkit", "widget-icon-list",
    "widget-divider",
]

# arquivos a preservar como estao
KEEP = {"favicon.png"}
# nao referenciados (lixo) -> apagar.
# NOTA: not.png e bg-mobile.png NAO sao lixo -- sao backgrounds de parallax
# (motion-effects, elemento c63b2a4 em post-14.css). Removidos daqui; passam
# pelo pipeline normal de WebP como qualquer imagem.
DEAD: list[str] = []

HTML_FILES = [
    SITE / "index.html",
    SITE / "form" / "index.html",
    SITE / "politica-de-privacidade" / "index.html",
    SITE / "termos-de-uso" / "index.html",
]


def human(n: int) -> str:
    return f"{n/1048576:.2f} MB"


def optimize_images() -> dict[str, str]:
    """Converte rasters grandes para WebP. Retorna mapa nome.png -> nome.webp."""
    mapping: dict[str, str] = {}
    saved = 0
    for path in sorted(UPLOADS.rglob("*")):
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        if path.name in KEEP or "/seo/" in path.as_posix():
            continue
        before = path.stat().st_size
        if before < SIZE_THRESHOLD:
            continue
        try:
            im = Image.open(path)
        except Exception as e:  # noqa: BLE001
            print(f"  skip {path.name}: {e}")
            continue
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        elif im.mode == "CMYK":
            im = im.convert("RGB")
        w, h = im.size
        if w > MAX_W:
            im = im.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)
        out = path.with_suffix(".webp")
        im.save(out, "WEBP", quality=WEBP_Q, method=6)
        after = out.stat().st_size
        mapping[path.name] = out.name
        saved += before - after
        print(f"  {path.name} {human(before)} -> {out.name} {human(after)}")
        path.unlink()  # remove original
    print(f"Imagens: economia {human(saved)} ({len(mapping)} convertidas)")
    return mapping


def rewrite_html(mapping: dict[str, str]) -> None:
    for hf in HTML_FILES:
        if not hf.exists():
            continue
        txt = hf.read_text(encoding="utf-8")
        orig = txt
        for old, new in mapping.items():
            txt = txt.replace(old, new)
        if txt != orig:
            hf.write_text(txt, encoding="utf-8")
            print(f"  refs atualizadas em {hf.relative_to(SITE)}")


def fix_css_image_refs() -> None:
    """Repointa url(...png|jpg) -> .webp nos CSS quando o raster sumiu mas o
    .webp irmao existe. Self-healing e idempotente: conserta refs em CSS que o
    rewrite_html (so HTML) nao cobre, inclusive em estado ja commitado.
    Refs cujo raster foi removido como lixo (sem .webp) sao reportadas."""
    rx = re.compile(r"url\(\s*(['\"]?)([^)'\"]+\.(?:png|jpe?g))\1\s*\)", re.I)
    fixed = 0
    dangling: list[str] = []
    for css in sorted(SITE.rglob("*.css")):
        txt = css.read_text(encoding="utf-8", errors="ignore")

        def repl(m: re.Match) -> str:
            nonlocal fixed
            quote, ref = m.group(1), m.group(2)
            target = (css.parent / ref).resolve()
            if target.exists():
                return m.group(0)  # raster ainda presente, nao mexe
            webp = target.with_suffix(".webp")
            if webp.exists():
                fixed += 1
                new_ref = re.sub(r"\.(?:png|jpe?g)$", ".webp", ref, flags=re.I)
                return f"url({quote}{new_ref}{quote})"
            dangling.append(f"{css.relative_to(SITE)} -> {ref}")
            return m.group(0)

        new = rx.sub(repl, txt)
        if new != txt:
            css.write_text(new, encoding="utf-8")
            print(f"  refs CSS atualizadas em {css.relative_to(SITE)}")
    print(f"CSS: {fixed} ref(s) png/jpg -> webp")
    for d in dangling:
        print(f"  AVISO ref morta (sem webp): {d}")


def optimize_head() -> None:
    """Enxuga Google Fonts no <head>: remove familias nao usadas e reduz os
    pesos das restantes para apenas os realmente aplicados no CSS.
    Idempotente: re-rodar nao muda nada (regex ja convergiu)."""
    # remove a familia inteira (linha <link ...elementor-gf-<fam>-css... />)
    drop_links = [
        re.compile(rf"<link[^>]*elementor-gf-{fam}-css[^>]*/?>\s*", re.I)
        for fam in UNUSED_GF
    ]
    # reduz o trecho de pesos depois do nome da familia: family=Nome:<pesos>
    trim_weights = re.compile(
        r"(fonts\.googleapis\.com/css\?family=[^:'\"&]+):[^'\"&]*"
    )
    for hf in HTML_FILES:
        if not hf.exists():
            continue
        txt = hf.read_text(encoding="utf-8")
        orig = txt
        for rx in drop_links:
            txt = rx.sub("", txt)
        txt = trim_weights.sub(rf"\1:{FONT_WEIGHTS}", txt)
        if txt != orig:
            hf.write_text(txt, encoding="utf-8")
            print(f"  head enxugado em {hf.relative_to(SITE)}")


def defer_css() -> None:
    """Torna nao-bloqueante o CSS decorativo (DEFER_CSS) via media=print +
    swap no onload, com <noscript> de fallback. Idempotente (pula tags que
    ja tem onload)."""
    for hf in HTML_FILES:
        if not hf.exists():
            continue
        txt = hf.read_text(encoding="utf-8")
        orig = txt
        for css_id in DEFER_CSS:
            rx = re.compile(rf"<link\b[^>]*\bid='{re.escape(css_id)}-css'[^>]*>")
            m = rx.search(txt)
            if not m:
                continue
            tag = m.group(0)
            if "onload=" in tag or "media='all'" not in tag:
                continue  # ja deferido ou formato inesperado
            deferred = tag.replace(
                "media='all'", "media='print' onload=\"this.media='all'\""
            )
            replacement = f"{deferred}<noscript>{tag}</noscript>"
            txt = txt.replace(tag, replacement, 1)
        if txt != orig:
            hf.write_text(txt, encoding="utf-8")
            print(f"  CSS deferido em {hf.relative_to(SITE)}")


def remove_dead_fonts() -> None:
    """Apaga .eot/.ttf do Font Awesome (so IE/legado; browser usa .woff2)."""
    if not FA_FONTS.exists():
        return
    saved = 0
    for path in sorted(FA_FONTS.iterdir()):
        if path.suffix.lower() in (".eot", ".ttf"):
            sz = path.stat().st_size
            path.unlink()
            saved += sz
            print(f"  removido {path.name} ({human(sz)})")
    print(f"Fontes FA legado: economia {human(saved)}")


def reencode_videos() -> None:
    saved = 0
    for path in sorted(UPLOADS.rglob("*.mp4")):
        before = path.stat().st_size
        tmp = path.with_suffix(".opt.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", str(path),
            "-vf", f"scale=-2:'min({VIDEO_MAX_H},ih)'",
            "-c:v", "libx264", "-crf", VIDEO_CRF, "-preset", "medium",
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart",
            str(tmp),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not tmp.exists():
            print(f"  FALHA video {path.name}: {r.stderr[-300:]}")
            tmp.unlink(missing_ok=True)
            continue
        after = tmp.stat().st_size
        if after < before:
            tmp.replace(path)
            saved += before - after
            print(f"  {path.name} {human(before)} -> {human(after)}")
        else:
            tmp.unlink(missing_ok=True)
            print(f"  {path.name}: re-encode maior, mantido original")
    print(f"Videos: economia {human(saved)}")


def remove_dead() -> None:
    for rel in DEAD:
        p = UPLOADS / rel
        if p.exists():
            sz = p.stat().st_size
            p.unlink()
            print(f"  removido {rel} ({human(sz)})")


def main() -> None:
    print("== imagens ==")
    mapping = optimize_images()
    print("== refs HTML ==")
    rewrite_html(mapping)
    print("== refs CSS ==")
    fix_css_image_refs()
    print("== head (google fonts) ==")
    optimize_head()
    print("== css defer ==")
    defer_css()
    print("== fontes legado ==")
    remove_dead_fonts()
    print("== videos ==")
    reencode_videos()
    print("== lixo ==")
    remove_dead()
    print("OK build-optim")


if __name__ == "__main__":
    main()
