#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica otimizacoes SEO ao site estatico (checklist seo-profissional).

Re-rodar apos scrape.py ou build-form.py para reaplicar patches.
Ordem recomendada: scrape.py -> build-seo.py -> build-form.py -> build-seo.py
"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import date

ROOT = pathlib.Path(__file__).parent
SITE = ROOT / "site"

BASE_URL = "https://nunaresidencial.com.br"
PHONE_E164 = "+5514991363259"
PHONE_DISPLAY = "(14) 99136-3259"
EMAIL = "contato@nunaresidencial.com.br"
ADDRESS = {
    "street": "Estrada do Baririzinho, 1899",
    "city": "Itapuí",
    "state": "SP",
    "postal": "17230-000",
    "country": "BR",
}
GEO = {"lat": -22.2323, "lng": -48.6789}

# Imagem OG 1200x630 (gerada por generate_og_image)
OG_REL_PATH = "wp-content/uploads/seo/og-nuna-residencial.jpg"
OG_IMAGE = f"{BASE_URL}/{OG_REL_PATH}"

# Dados legais publicos (CNPJ/razao social: preencher quando confirmados)
LEGAL_RAZAO = ""  # ex: "Nuna Residencial Senior Ltda"
LEGAL_CNPJ = ""  # ex: "00.000.000/0001-00"
ENTITY_NAME = "Nuna Residencial Sênior"
ADDRESS_FULL = (
    f"{ADDRESS['street']}, {ADDRESS['city']} - {ADDRESS['state']}, "
    f"CEP {ADDRESS['postal']}, Brasil"
)
LGPD_URL = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"

PAGES = [
    {"path": "/", "file": "index.html", "index": True},
    {"path": "/form/", "file": "form/index.html", "index": False},
    {"path": "/politica-de-privacidade/", "file": "politica-de-privacidade/index.html", "index": True},
    {"path": "/termos-de-uso/", "file": "termos-de-uso/index.html", "index": True},
]

PAGE_META = {
    "/": {
        "title": "Nuna Residencial Sênior em Itapuí-SP | Cuidado 24h",
        "description": (
            "Residencial sênior em Itapuí (SP) com cuidado humanizado 24h, moradia permanente, "
            "day use e reabilitação. Equipe especializada. Agende uma visita."
        ),
    },
    "/form/": {
        "title": "Fale com a Nuna | Residencial Sênior Itapuí-SP",
        "description": (
            "Qualifique seu interesse e fale com a equipe da Nuna Residencial Sênior em Itapuí. "
            "Moradia permanente, day use, temporada e centro dia."
        ),
    },
    "/politica-de-privacidade/": {
        "title": "Política de Privacidade — Nuna Residencial Sênior",
        "description": (
            "Saiba como a Nuna Residencial Sênior coleta, usa e protege seus dados pessoais "
            "em conformidade com a LGPD."
        ),
    },
    "/termos-de-uso/": {
        "title": "Termos de Uso — Nuna Residencial Sênior",
        "description": (
            "Termos de uso do site da Nuna Residencial Sênior em Itapuí (SP): regras de "
            "navegação, contato e propriedade intelectual."
        ),
    },
}

FAQ_ITEMS = [
    (
        "O que é o Residencial Nuna?",
        "O Residencial Nuna é um espaço dedicado a oferecer cuidado humanizado e individualizado "
        "para idosos, proporcionando uma vida melhor com conforto e atenção especializada.",
    ),
    (
        "Quais são os tipos de serviços oferecidos pelo Residencial Nuna?",
        "Oferecemos serviços personalizados para cada necessidade, incluindo assistência para "
        "idosos com mobilidade reduzida, cuidados paliativos, fisioterapia, atividades "
        "recreativas e alimentação balanceada.",
    ),
    (
        "Como é o ambiente do Residencial Nuna?",
        "Nosso espaço foi cuidadosamente projetado para proporcionar conforto e segurança em "
        "meio à natureza, com amplas áreas verdes, acomodações aconchegantes e uma estrutura "
        "que promove tranquilidade e bem-estar.",
    ),
    (
        "O Residencial Nuna oferece reabilitação para idosos com fraturas?",
        "Sim. Contamos com equipe multidisciplinar para acompanhar a reabilitação de idosos "
        "com fraturas, com planos personalizados de fisioterapia e cuidados contínuos.",
    ),
    (
        "Como posso agendar uma visita ao Residencial Nuna?",
        "Você pode agendar uma visita pelo site ou entrando em contato pelo WhatsApp ou "
        "telefone. Teremos prazer em mostrar nossas instalações.",
    ),
    (
        "O que está incluído na alimentação dos residentes?",
        "Oferecemos refeições nutritivas preparadas por nutricionista, com seis refeições "
        "diárias respeitando necessidades dietéticas e preferências de cada residente.",
    ),
    (
        "Quais profissionais fazem parte da equipe de cuidado?",
        "Médicos, enfermeiros, técnicos e auxiliares de enfermagem, fisioterapeutas e "
        "cuidadores treinados, dedicados a uma assistência completa e humanizada.",
    ),
]

WHATSAPP_TEXT = "Olá, vim do site da Nuna e gostaria de saber mais"
WHATSAPP_URL = (
    f"https://wa.me/5514991363259?text="
    + WHATSAPP_TEXT.replace(" ", "%20").replace(",", "%2C").replace("á", "%C3%A1")
)

SEO_MARKER = "<!-- nuna-seo-head -->"
BODY_MARKER = "<!-- nuna-seo-body -->"


def wa_url() -> str:
    from urllib.parse import quote

    return f"https://wa.me/5514991363259?text={quote('Olá, vim do site da Nuna e gostaria de saber mais')}"


def head_block(path: str, *, index: bool) -> str:
    meta = PAGE_META[path]
    url = BASE_URL + ("" if path == "/" else path.rstrip("/") + "/")
    if path == "/":
        url = BASE_URL + "/"
    robots = "index,follow,max-image-preview:large" if index else "noindex,follow"

    lines = [
        SEO_MARKER,
        f'<meta name="description" content="{meta["description"]}">',
        f'<meta name="robots" content="{robots}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:type" content="website">',
        f'<meta property="og:locale" content="pt_BR">',
        f'<meta property="og:site_name" content="Nuna Residencial Sênior">',
        f'<meta property="og:title" content="{meta["title"]}">',
        f'<meta property="og:description" content="{meta["description"]}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        f'<meta property="og:image:width" content="1200">',
        f'<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="Instalações do Nuna Residencial Sênior em Itapuí">',
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{meta["title"]}">',
        f'<meta name="twitter:description" content="{meta["description"]}">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
        f'<link rel="alternate" hreflang="pt-BR" href="{url}">',
    ]
    if path == "/":
        lines.append(schema_home())
    return "\n".join(lines)


def schema_home() -> str:
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": BASE_URL + "/",
                "name": "Nuna Residencial Sênior",
                "description": PAGE_META["/"]["description"],
                "inLanguage": "pt-BR",
                "publisher": {"@id": f"{BASE_URL}/#organization"},
            },
            {
                "@type": ["LocalBusiness", "NursingHome"],
                "@id": f"{BASE_URL}/#organization",
                "name": "Nuna Residencial Sênior",
                "url": BASE_URL + "/",
                "logo": f"{BASE_URL}/wp-content/uploads/2024/09/logo.svg",
                "image": OG_IMAGE,
                "description": (
                    "Residencial sênior em Itapuí (SP) com cuidado humanizado 24 horas, "
                    "moradia permanente, day use, temporada e centro dia."
                ),
                "telephone": PHONE_E164,
                "email": EMAIL,
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": ADDRESS["street"],
                    "addressLocality": ADDRESS["city"],
                    "addressRegion": ADDRESS["state"],
                    "postalCode": ADDRESS["postal"],
                    "addressCountry": ADDRESS["country"],
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": GEO["lat"],
                    "longitude": GEO["lng"],
                },
                "openingHoursSpecification": [
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "opens": "00:00",
                        "closes": "23:59",
                        "description": "Atendimento residencial 24 horas",
                    },
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                        ],
                        "opens": "08:00",
                        "closes": "17:00",
                        "description": "Administração",
                    },
                ],
                "sameAs": [
                    "https://www.facebook.com/nunaresidencial",
                    "https://www.instagram.com/nunasenior",
                ],
                "areaServed": {
                    "@type": "AdministrativeArea",
                    "name": "Itapuí e região de Bauru, SP",
                },
                "hasOfferCatalog": {
                    "@type": "OfferCatalog",
                    "name": "Serviços do Residencial Nuna",
                    "itemListElement": [
                        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Moradia permanente"}},
                        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Day use"}},
                        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Estadia por temporada"}},
                        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Centro dia"}},
                        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Reabilitação pós-fratura"}},
                    ],
                },
            },
            {
                "@type": "WebPage",
                "@id": f"{BASE_URL}/#webpage",
                "url": BASE_URL + "/",
                "name": PAGE_META["/"]["title"],
                "description": PAGE_META["/"]["description"],
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "about": {"@id": f"{BASE_URL}/#organization"},
                "inLanguage": "pt-BR",
            },
            {
                "@type": "FAQPage",
                "@id": f"{BASE_URL}/#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in FAQ_ITEMS
                ],
            },
        ],
    }
    payload = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">{payload}</script>'


ANSWER_CAPSULE = """<p class="nuna-answer-capsule" id="nuna-resposta-principal">
  <strong>O que é o Nuna Residencial Sênior?</strong>
  O Nuna é um residencial sênior em Itapuí (SP), em meio à natureza, com cuidado humanizado 24 horas.
  Oferece moradia permanente, day use, estadias por temporada e centro dia, com equipe multiprofissional
  e seis refeições diárias. Fundado em 2017 por enfermeiras especializadas em geriatria.
</p>"""

SEO_STYLES = """<!-- nuna-seo-body -->
<style>
.nuna-answer-capsule{max-width:720px;margin:0 auto 1.25rem;padding:0 1rem;font-size:1rem;line-height:1.6;color:#4a4350;text-align:center}
.nuna-answer-capsule strong{display:block;font-family:inherit;color:#574860;margin-bottom:.35rem}
*:focus-visible{outline:2px solid #6D5873;outline-offset:2px}
</style>"""


def strip_old_seo(html: str) -> str:
    html = re.sub(r"<!-- nuna-seo-head -->.*?<!-- /nuna-seo-head -->\n?", "", html, flags=re.S)
    html = re.sub(r"<!-- nuna-seo-head -->.*?(?=<style|<link|<script|\n\t<style|\n<link|\n<script|\n\t<meta name=\"viewport\")", "", html, flags=re.S)
    html = re.sub(r"<!-- nuna-seo-body -->.*?(?=</body>)", "", html, flags=re.S, count=1)
    html = re.sub(r'<meta name=[\'"]description[^>]+>\n?', "", html)
    html = re.sub(r'<meta name=[\'"]robots[^>]+>\n?', "", html)
    html = re.sub(r'<link rel=[\'"]canonical[^>]+>\n?', "", html)
    html = re.sub(r'<link rel=[\'"]shortlink[^>]+>\n?', "", html)
    html = re.sub(r'<meta property="og:[^"]+"[^>]+>\n?', "", html)
    html = re.sub(r'<meta name="twitter:[^"]+"[^>]+>\n?', "", html)
    html = re.sub(r'<link rel="alternate" hreflang[^>]+>\n?', "", html)
    html = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", html, flags=re.S)
    html = re.sub(r'<div class="elementor-widget-container nuna-capsule-wrap">.*?</div>\n?', "", html, flags=re.S)
    html = re.sub(r'<p class="nuna-answer-capsule" id="nuna-resposta-principal">.*?</p>\n?', "", html, flags=re.S)
    return html


def patch_landing(html: str) -> str:
    html = strip_old_seo(html)
    html = html.replace(
        "<title>nuna &#8211; Residêncial Sênior</title>",
        f"<title>{PAGE_META['/']['title']}</title>",
    )
    html = html.replace(
        "<title>nuna – Residêncial Sênior</title>",
        f"<title>{PAGE_META['/']['title']}</title>",
    )

    insert_at = html.find("<style id='wp-img-auto-sizes-contain-inline-css'>")
    if insert_at == -1:
        insert_at = html.find("<meta charset")
        end = html.find(">", insert_at) + 1
    else:
        end = insert_at
    block = head_block("/", index=True) + "\n"
    html = html[:end] + block + html[end:]

    # hero: unico H1
    html = html.replace(
        '<h2 class="elementor-heading-title elementor-size-default">Cuidado humanizado <br>e individualizado para uma vida melhor</h2>',
        '<h1 class="elementor-heading-title elementor-size-default">Residencial sênior em Itapuí: cuidado humanizado <br>e individualizado para uma vida melhor</h1>',
        1,
    )

    # whatsapp wa.me
    html = re.sub(
        r"https://api\.whatsapp\.com/send\?phone=5514991363259(?:&amp;[^\"']*)?",
        wa_url(),
        html,
    )

    # footer links institucionais
    for old, new in (
        (
            '<span class="elementor-icon-list-text">Termo de uso</span>',
            '<a href="/termos-de-uso/" class="elementor-icon-list-text">Termos de uso</a>',
        ),
        (
            '<span class="elementor-icon-list-text">Politica de privacidade</span>',
            '<a href="/politica-de-privacidade/" class="elementor-icon-list-text">Política de privacidade</a>',
        ),
        (
            '<span class="elementor-icon-list-text"><a href="/termos-de-uso/" style="color:inherit;text-decoration:none">Termo de uso</a></span>',
            '<a href="/termos-de-uso/" class="elementor-icon-list-text">Termos de uso</a>',
        ),
        (
            '<span class="elementor-icon-list-text"><a href="/politica-de-privacidade/" style="color:inherit;text-decoration:none">Politica de privacidade</a></span>',
            '<a href="/politica-de-privacidade/" class="elementor-icon-list-text">Política de privacidade</a>',
        ),
    ):
        html = html.replace(old, new)

    # logo alt (header + footer)
    html = html.replace(
        'data-src="wp-content/uploads/2024/09/logo.svg" class="attachment-full size-full wp-image-1375 lazy" alt=""',
        f'data-src="wp-content/uploads/2024/09/logo.svg" class="attachment-full size-full wp-image-1375 lazy" alt="{ENTITY_NAME} — logo"',
    )
    html = html.replace(
        'data-src="wp-content/uploads/2024/09/logo.svg" class="attachment-full size-full wp-image-1375 lazy" alt="Nuna Residencial Sênior — logo"',
        f'data-src="wp-content/uploads/2024/09/logo.svg" class="attachment-full size-full wp-image-1375 lazy" alt="{ENTITY_NAME} — logo"',
    )

    html = patch_image_alts(html)
    html = patch_social_links(html)
    html = html.replace("© 2025 -", "© 2026 —")

    if BODY_MARKER not in html:
        html = html.replace("</body>", SEO_STYLES + "\n</body>")

    return html


def patch_form(html: str) -> str:
    html = strip_old_seo(html)
    for old in (
        "<title>nuna &#8211; Residêncial Sênior</title>",
        f"<title>{PAGE_META['/']['title']}</title>",
    ):
        html = html.replace(old, f"<title>{PAGE_META['/form/']['title']}</title>")
    insert_at = html.find("<style id='wp-img-auto-sizes-contain-inline-css'>")
    end = insert_at if insert_at != -1 else html.find(">", html.find("<meta charset")) + 1
    html = html[:end] + head_block("/form/", index=False) + "\n" + html[end:]
    html = re.sub(
        r"https://api\.whatsapp\.com/send\?phone=5514991363259(?:&amp;[^\"']*)?",
        wa_url(),
        html,
    )
    html = html.replace('href="index.html"', 'href="/"')
    return html


def patch_image_alts(html: str) -> str:
    """Alt text descritivo em imagens de conteudo (nao decorativas)."""
    alts = {
        "image_nuna_8.webp": "Equipe e cuidadoras do Nuna Residencial Sênior em Itapuí",
        "IMG_INTER_1_CARROUSSEL.png": "Ambiente interno acolhedor do residencial sênior Nuna",
        "IMG_INTER_2_CARROUSSEL.png": "Sala de convivência do Nuna Residencial Sênior",
        "IMG_INTER_3_CARROUSSEL.png": "Espaço de descanso para residentes no Nuna",
        "IMG_SERV_1.png": "Cuidado especializado oferecido pelo Nuna em Itapuí",
        "Frame-1171275169.png": "Instalações do Nuna Residencial Sênior em meio à natureza",
        "Frame-1171275170.png": "Área externa verde do residencial Nuna",
        "Frame-1171275172.png": "Estrutura de acolhimento do Nuna Residencial Sênior",
        "1-DSC03133.png": "Jardim e área externa do Nuna Residencial Sênior",
        "3-DSC03160.png": "Espaço comum do residencial sênior Nuna em Itapuí",
    }
    for fname, alt in alts.items():
        html = re.sub(
            rf'((?:data-src|src)="[^"]*{re.escape(fname)}"[^>]*\s)alt="[^"]*"',
            rf'\1alt="{alt}"',
            html,
        )
    return html


def patch_social_links(html: str) -> str:
    return re.sub(
        r'(<a class="elementor-icon elementor-social-icon[^"]*"[^>]*target="_blank")(?![^>]*\brel=)',
        r'\1 rel="noopener noreferrer"',
        html,
    )


def legal_controller_intro() -> str:
    if LEGAL_RAZAO and LEGAL_CNPJ:
        return (
            f"a <strong>{LEGAL_RAZAO}</strong>, inscrita no CNPJ sob nº "
            f"<strong>{LEGAL_CNPJ}</strong>, com sede em <strong>{ADDRESS_FULL}</strong>"
        )
    return (
        f"o <strong>{ENTITY_NAME}</strong>, estabelecimento de cuidado a idosos com sede em "
        f"<strong>{ADDRESS_FULL}</strong>"
    )


LEGAL_STYLES = """@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Mulish:wght@400;500;600;700&display=swap');
:root{--plum:#6D5873;--plum-d:#574860;--mauve:#B89FBF;--ink:#3E3142;--muted:#6E6470;--cream:#F7F0F4;--line:#E7DEE6}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font-family:'Mulish',system-ui,sans-serif;line-height:1.65;font-size:16.5px}
.lp-head{background:linear-gradient(135deg,var(--plum),var(--plum-d));padding:26px 20px;text-align:center}
.lp-head img{height:34px;width:auto}
.lp-wrap{max-width:760px;margin:0 auto;padding:44px 22px 70px}
.lp-back{display:inline-block;margin-bottom:22px;color:var(--plum);font-weight:700;font-size:14px;text-decoration:none}
.lp-back:hover{text-decoration:underline}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:34px;line-height:1.12;letter-spacing:-.01em;color:var(--ink);margin:0 0 8px}
.lp-date{color:var(--muted);font-size:14px;margin:0 0 34px}
h2{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:22px;color:var(--plum-d);margin:38px 0 10px}
p,li{color:#4A4350}
a{color:var(--plum);font-weight:600}
ul{padding-left:22px}
li{margin-bottom:7px}
.lp-card{background:#FFFCFE;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin:18px 0}
.lp-foot{border-top:1px solid var(--line);margin-top:48px;padding-top:22px;font-size:14px;color:var(--muted);text-align:center}
.lp-foot a{margin:0 8px}"""


def legal_head(path: str) -> str:
    meta = PAGE_META[path]
    url = BASE_URL + path
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta['title']}</title>
<!-- nuna-seo-head -->
<meta name="description" content="{meta['description']}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{meta['title']}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{meta['title']}">
<meta name="twitter:description" content="{meta['description']}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="icon" href="/wp-content/uploads/2024/09/favicon.png">
<style>
{LEGAL_STYLES}
</style>"""


def write_politica_privacidade() -> None:
    intro = legal_controller_intro()
    today = "02 de junho de 2026"
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
{legal_head("/politica-de-privacidade/")}
</head>
<body>
<header class="lp-head"><img src="/wp-content/uploads/2024/09/logo.svg" alt="{ENTITY_NAME}"></header>
<main class="lp-wrap">
 <a class="lp-back" href="/">&larr; Voltar ao site</a>
 <h1>Política de Privacidade</h1>
 <p class="lp-date">Última atualização: {today}</p>

 <p>Esta Política de Privacidade descreve como {intro} ("Nuna", "nós"), controlador dos dados pessoais, coleta, usa, armazena e protege informações dos visitantes do site <strong>nunaresidencial.com.br</strong> ("Site"), em conformidade com a <a href="{LGPD_URL}" target="_blank" rel="noopener noreferrer">Lei nº 13.709/2018 (LGPD)</a>.</p>

 <h2>1. Dados que coletamos</h2>
 <p>Coletamos os seguintes dados pessoais:</p>
 <ul>
  <li><strong>Dados fornecidos por você</strong> no formulário de contato: nome e número de WhatsApp. Quando aplicável, a faixa de orçamento mensal informada.</li>
  <li><strong>Dados de navegação</strong> coletados automaticamente por cookies e tecnologias semelhantes: endereço IP, tipo de dispositivo e navegador, páginas visitadas e dados de uso.</li>
 </ul>

 <h2>2. Como e por que usamos seus dados</h2>
 <p>Utilizamos seus dados pessoais com as seguintes finalidades:</p>
 <ul>
  <li>Entrar em contato com você pelo WhatsApp para atendimento comercial e esclarecimento de dúvidas;</li>
  <li>Qualificar seu interesse e direcionar o atendimento adequado;</li>
  <li>Operar, manter e melhorar o Site e a experiência de navegação.</li>
 </ul>
 <p>A base legal para o tratamento é o <strong>consentimento</strong> do titular e os <strong>procedimentos preliminares relacionados a contrato</strong> (art. 7º, I e V, da LGPD).</p>

 <h2>3. Compartilhamento de dados</h2>
 <p>Não vendemos seus dados pessoais. Compartilhamos dados apenas com operadores que viabilizam nossos serviços:</p>
 <ul>
  <li><strong>Make (Make.com / Celonis)</strong> — automação que recebe e encaminha os dados do formulário;</li>
  <li><strong>WhatsApp / Meta Platforms</strong> — canal de contato escolhido por você;</li>
  <li><strong>Cloudflare</strong> — hospedagem e entrega do Site;</li>
  <li>Autoridades públicas, quando exigido por lei ou ordem judicial.</li>
 </ul>

 <h2>4. Cookies</h2>
 <p>O Site utiliza cookies para funcionamento, análise de uso e melhoria da experiência. Ao continuar navegando, você concorda com o uso de cookies. Você pode gerenciar ou desativar cookies nas configurações do seu navegador, ciente de que isso pode afetar funcionalidades do Site.</p>

 <h2>5. Armazenamento e segurança</h2>
 <p>Adotamos medidas técnicas e administrativas razoáveis para proteger seus dados contra acessos não autorizados, perda ou alteração. Os dados são mantidos pelo tempo necessário às finalidades descritas ou conforme exigências legais.</p>

 <h2>6. Seus direitos como titular</h2>
 <p>Nos termos do art. 18 da LGPD, você pode, a qualquer momento, solicitar:</p>
 <ul>
  <li>confirmação da existência de tratamento e acesso aos seus dados;</li>
  <li>correção de dados incompletos, inexatos ou desatualizados;</li>
  <li>anonimização, bloqueio ou eliminação de dados desnecessários;</li>
  <li>portabilidade e informação sobre compartilhamentos;</li>
  <li>revogação do consentimento e eliminação dos dados tratados com base nele.</li>
 </ul>
 <div class="lp-card">Para exercer seus direitos, entre em contato com nosso Encarregado pela Proteção de Dados (DPO): <strong><a href="mailto:{EMAIL}">{EMAIL}</a></strong> ou telefone <strong>{PHONE_DISPLAY}</strong>.</div>

 <h2>7. Retenção e eliminação</h2>
 <p>Seus dados serão eliminados quando deixarem de ser necessários às finalidades para as quais foram coletados, ou mediante solicitação, ressalvadas as hipóteses de guarda obrigatória previstas em lei.</p>

 <h2>8. Alterações desta Política</h2>
 <p>Esta Política pode ser atualizada periodicamente. A versão vigente estará sempre disponível nesta página, com a data da última atualização indicada acima.</p>

 <h2>9. Contato</h2>
 <p>Dúvidas sobre esta Política ou sobre o tratamento de seus dados podem ser enviadas para <strong><a href="mailto:{EMAIL}">{EMAIL}</a></strong>. Endereço: {ADDRESS_FULL}.</p>

 <div class="lp-foot">
  © 2026 {ENTITY_NAME} — Todos os direitos reservados.<br>
  <a href="/termos-de-uso/">Termos de Uso</a> · <a href="/politica-de-privacidade/">Política de Privacidade</a>
 </div>
</main>
</body>
</html>
"""
    (SITE / "politica-de-privacidade" / "index.html").write_text(html, encoding="utf-8")


def write_termos_uso() -> None:
    if LEGAL_RAZAO and LEGAL_CNPJ:
        maintainer = (
            f"a <strong>{LEGAL_RAZAO}</strong>, inscrita no CNPJ sob nº "
            f"<strong>{LEGAL_CNPJ}</strong>, com sede em <strong>{ADDRESS_FULL}</strong>"
        )
        owner = LEGAL_RAZAO
    else:
        maintainer = (
            f"pelo <strong>{ENTITY_NAME}</strong>, estabelecimento com sede em "
            f"<strong>{ADDRESS_FULL}</strong>"
        )
        owner = ENTITY_NAME
    today = "02 de junho de 2026"
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
{legal_head("/termos-de-uso/")}
</head>
<body>
<header class="lp-head"><img src="/wp-content/uploads/2024/09/logo.svg" alt="{ENTITY_NAME}"></header>
<main class="lp-wrap">
 <a class="lp-back" href="/">&larr; Voltar ao site</a>
 <h1>Termos de Uso</h1>
 <p class="lp-date">Última atualização: {today}</p>

 <p>Estes Termos de Uso regulam o acesso e a utilização do site <strong>nunaresidencial.com.br</strong> ("Site"), mantido {maintainer} ("Nuna", "nós"). Ao acessar ou usar o Site, você declara ter lido, compreendido e aceitado integralmente estes Termos.</p>

 <h2>1. Objeto</h2>
 <p>O Site tem caráter informativo e de contato, apresentando o residencial sênior Nuna e seus serviços, e disponibilizando formulário para que interessados solicitem atendimento. O Site não realiza vendas nem contratações online.</p>

 <h2>2. Uso do Site</h2>
 <p>Você se compromete a utilizar o Site de forma lícita e a fornecer informações verdadeiras e atualizadas nos formulários. É vedado:</p>
 <ul>
  <li>usar o Site para fins ilícitos ou que violem direitos de terceiros;</li>
  <li>tentar acessar áreas restritas, comprometer a segurança ou a disponibilidade do Site;</li>
  <li>reproduzir, copiar ou explorar o conteúdo sem autorização.</li>
 </ul>

 <h2>3. Informações fornecidas por você</h2>
 <p>Ao enviar nome, WhatsApp e demais dados pelo formulário, você autoriza o contato pela Nuna pelos canais informados. O tratamento desses dados observa nossa <a href="/politica-de-privacidade/">Política de Privacidade</a>.</p>

 <h2>4. Propriedade intelectual</h2>
 <p>Todo o conteúdo do Site — incluindo marca, logotipo, textos, imagens, vídeos e layout — é de titularidade da <strong>{owner}</strong> ou de seus licenciadores e é protegido pela legislação aplicável. Nenhum direito é cedido pelo simples acesso ao Site.</p>

 <h2>5. Links e serviços de terceiros</h2>
 <p>O Site pode conter links para serviços de terceiros, como o WhatsApp. A Nuna não se responsabiliza pelo conteúdo, políticas ou práticas desses serviços, regidos por seus próprios termos.</p>

 <h2>6. Limitação de responsabilidade</h2>
 <p>As informações do Site são fornecidas "no estado em que se encontram". A Nuna empenha-se em mantê-las corretas e atualizadas, mas não garante ausência de erros ou disponibilidade ininterrupta, não respondendo por danos decorrentes do uso ou da indisponibilidade do Site.</p>

 <h2>7. Alterações dos Termos</h2>
 <p>Estes Termos podem ser alterados a qualquer momento. A versão vigente estará sempre disponível nesta página, com a data da última atualização indicada acima. O uso continuado do Site após alterações implica concordância.</p>

 <h2>8. Lei aplicável e foro</h2>
 <p>Estes Termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro da comarca de <strong>Itapuí/SP</strong> para dirimir eventuais controvérsias, com renúncia a qualquer outro, por mais privilegiado que seja.</p>

 <h2>9. Contato</h2>
 <p>Dúvidas sobre estes Termos podem ser enviadas para <strong><a href="mailto:{EMAIL}">{EMAIL}</a></strong> ou telefone <strong>{PHONE_DISPLAY}</strong>. Endereço: {ADDRESS_FULL}.</p>

 <div class="lp-foot">
  © 2026 {ENTITY_NAME} — Todos os direitos reservados.<br>
  <a href="/termos-de-uso/">Termos de Uso</a> · <a href="/politica-de-privacidade/">Política de Privacidade</a>
 </div>
</main>
</body>
</html>
"""
    (SITE / "termos-de-uso" / "index.html").write_text(html, encoding="utf-8")


def generate_og_image() -> None:
    """Gera imagem Open Graph 1200x630 com identidade Nuna."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("AVISO: Pillow ausente — OG image nao gerada")
        return

    w, h = 1200, 630
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        if t < 0.55:
            u = t / 0.55
            r = int(87 + (109 - 87) * u)
            g = int(72 + (159 - 72) * u)
            b = int(96 + (191 - 96) * u)
        else:
            u = (t - 0.55) / 0.45
            r = int(109 + (247 - 109) * u)
            g = int(159 + (240 - 159) * u)
            b = int(191 + (244 - 191) * u)
        for x in range(w):
            px[x, y] = (r, g, b)

    draw = ImageDraw.Draw(img)
    fonts_dir = pathlib.Path("C:/Windows/Fonts")
    try:
        title_font = ImageFont.truetype(str(fonts_dir / "georgiab.ttf"), 96)
        sub_font = ImageFont.truetype(str(fonts_dir / "arial.ttf"), 42)
        tag_font = ImageFont.truetype(str(fonts_dir / "arial.ttf"), 30)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font
        tag_font = title_font

    draw.text((80, 180), "nuna", fill=(238, 237, 219), font=title_font)
    draw.text((80, 300), "Residencial Sênior", fill=(255, 252, 254), font=sub_font)
    draw.text((80, 370), "Itapuí · SP · Cuidado humanizado 24h", fill=(238, 237, 219), font=tag_font)

    out = SITE / OG_REL_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    kb = out.stat().st_size / 1024
    print(f"OK {OG_REL_PATH} ({kb:.0f} KB)")


def write_robots() -> None:
    (SITE / "robots.txt").write_text(
        f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
""",
        encoding="utf-8",
    )


def write_sitemap() -> None:
    today = date.today().isoformat()
    urls = []
    for p in PAGES:
        if not p["index"]:
            continue
        loc = BASE_URL + ("/" if p["path"] == "/" else p["path"])
        priority = "1.0" if p["path"] == "/" else "0.5"
        urls.append(
            f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{priority}</priority>
  </url>"""
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (SITE / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_llms() -> None:
    (SITE / "llms.txt").write_text(
        f"""# Nuna Residencial Sênior

> Residencial sênior em Itapuí (SP) com cuidado humanizado 24h, moradia permanente, day use, temporada e centro dia.

## Páginas principais

- Home: {BASE_URL}/
- Formulário de contato: {BASE_URL}/form/
- Política de privacidade: {BASE_URL}/politica-de-privacidade/
- Termos de uso: {BASE_URL}/termos-de-uso/

## Entidade

- Nome: {ENTITY_NAME}
- Endereço: {ADDRESS_FULL}
- Telefone: {PHONE_DISPLAY}
- E-mail: {EMAIL}
- Instagram: https://www.instagram.com/nunasenior
- Facebook: https://www.facebook.com/nunaresidencial

## Serviços

- Moradia permanente com cuidados 24 horas
- Day use e estadia por temporada
- Centro dia
- Reabilitação pós-fratura e fisioterapia

## Uso por sistemas de IA

Este arquivo orienta crawlers de IA sobre páginas prioritárias. Não garante citação ou indexação em sistemas generativos.
Conteúdo factual deve refletir apenas o que está publicado nas páginas listadas acima.
""",
        encoding="utf-8",
    )


def main() -> None:
    generate_og_image()

    index_path = SITE / "index.html"
    index_path.write_text(patch_landing(index_path.read_text(encoding="utf-8")), encoding="utf-8")
    print("OK index.html")

    form_path = SITE / "form" / "index.html"
    if form_path.exists():
        form_path.write_text(patch_form(form_path.read_text(encoding="utf-8")), encoding="utf-8")
        print("OK form/index.html")

    write_politica_privacidade()
    print("OK politica-de-privacidade/index.html")
    write_termos_uso()
    print("OK termos-de-uso/index.html")

    write_robots()
    write_sitemap()
    write_llms()
    print("OK robots.txt, sitemap.xml, llms.txt")


if __name__ == "__main__":
    main()
