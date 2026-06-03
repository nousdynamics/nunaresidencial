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

# arquivos a preservar como estao
KEEP = {"favicon.png"}
# nao referenciados (lixo) -> apagar
DEAD = ["2024/10/not.png", "2024/10/bg-mobile.png"]

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
    print("== videos ==")
    reencode_videos()
    print("== lixo ==")
    remove_dead()
    print("OK build-optim")


if __name__ == "__main__":
    main()
