#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-host das fontes (woff2) em vez de carregar do Google Fonts.

Baixa as familias usadas (subsets latin + latin-ext, fontes variaveis = 1
arquivo por subset), salva em site/wp-content/fonts/ e gera fonts.css local
com font-display:swap. As referencias no HTML sao trocadas pelos generators
(build-seo.py / build-form.py) que linkam /wp-content/fonts/fonts.css.

Rodar uma vez (precisa rede). Idempotente: re-baixa e regenera fonts.css.
"""
from __future__ import annotations

import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).parent
FONTS_DIR = ROOT / "site" / "wp-content" / "fonts"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# familia -> spec css2 (ranges variaveis = menos arquivos)
FAMILIES = {
    "roboto": "Roboto:wght@400..700",
    "roboto-slab": "Roboto+Slab:wght@400..700",
    "fraunces": "Fraunces:opsz,wght@9..144,400..700",
    "mulish": "Mulish:wght@400..800",
}
KEEP_SUBSETS = {"latin", "latin-ext"}

BLOCK_RE = re.compile(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def prop(body: str, name: str) -> str | None:
    m = re.search(rf"{name}\s*:\s*([^;]+);", body)
    return m.group(1).strip() if m else None


def main() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    css_blocks: list[str] = []
    for slug, spec in FAMILIES.items():
        url = f"https://fonts.googleapis.com/css2?family={spec}&display=swap"
        css = fetch(url).decode("utf-8")
        fam_dir = FONTS_DIR / slug
        fam_dir.mkdir(exist_ok=True)
        got = 0
        for subset, body in BLOCK_RE.findall(css):
            if subset not in KEEP_SUBSETS:
                continue
            src_m = re.search(r"src:\s*url\((https://[^)]+\.woff2)\)", body)
            if not src_m:
                continue
            woff2_url = src_m.group(1)
            fname = f"{slug}-{subset}.woff2"
            (fam_dir / fname).write_bytes(fetch(woff2_url))
            family = prop(body, "font-family") or f"'{slug}'"
            style = prop(body, "font-style") or "normal"
            weight = prop(body, "font-weight") or "400"
            urange = prop(body, "unicode-range") or ""
            block = (
                "@font-face{\n"
                f"  font-family:{family};\n"
                f"  font-style:{style};\n"
                f"  font-weight:{weight};\n"
                "  font-display:swap;\n"
                f"  src:url('./{slug}/{fname}') format('woff2');\n"
                + (f"  unicode-range:{urange};\n" if urange else "")
                + "}"
            )
            css_blocks.append(block)
            sz = (fam_dir / fname).stat().st_size
            print(f"  {slug} {subset}: {fname} ({sz/1024:.0f} KB)")
            got += 1
        if not got:
            print(f"  AVISO: nenhum subset baixado para {slug}")
    (FONTS_DIR / "fonts.css").write_text("\n".join(css_blocks) + "\n", encoding="utf-8")
    print(f"OK fonts.css ({len(css_blocks)} @font-face) em {FONTS_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
