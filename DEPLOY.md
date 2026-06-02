# Deploy no Cloudflare Pages

Site estatico (HTML/CSS/JS) na pasta [`site/`](site/). Tudo pronto pra publicar.

## Estrutura

```
nunaresidencial-lp/
├─ site/              <- conteudo publicado (output dir)
│  ├─ index.html
│  ├─ _headers        <- cache + headers de seguranca
│  └─ wp-content/ ... <- css, js, imagens, fonts
├─ wrangler.toml      <- config Cloudflare Pages
├─ package.json       <- scripts (preview/deploy)
└─ scrape.py          <- script que gerou o clone (re-rodar atualiza)
```

## Opcao 1 — Wrangler CLI (recomendado)

Wrangler nao esta instalado localmente; roda via `npx` (baixa on-demand).

```powershell
# 1. login (abre o browser, autentica na conta Cloudflare)
npx wrangler login

# 2. deploy (cria o projeto "nuna-residencial" na 1a vez)
npx wrangler pages deploy site --project-name=nuna-residencial
```

Saida: URL `https://nuna-residencial.pages.dev`.

## Opcao 2 — Dashboard (drag & drop, sem CLI)

1. Cloudflare Dashboard -> **Workers & Pages** -> **Create** -> **Pages** -> **Upload assets**.
2. Nome do projeto: `nuna-residencial`.
3. Arrastar **o conteudo da pasta `site/`** (nao a pasta pai).
4. **Deploy**.

## Opcao 3 — Git (deploy continuo)

1. `git init && git add . && git commit -m "clone estatico"` e push pro GitHub.
2. Dashboard -> Pages -> **Connect to Git** -> escolher o repo.
3. Build settings:
   - Framework preset: **None**
   - Build command: *(vazio)*
   - Build output directory: **site**
4. Save and Deploy. Cada push republica.

## Preview local

```powershell
npm run preview   # serve em http://localhost:8765
```

## Dominio proprio

Pages -> projeto -> **Custom domains** -> adicionar `nunaresidencial.com.br` (ou subdominio). Cloudflare ajusta DNS se o dominio estiver na conta.

## Observacoes

- Limite Pages: 25 MB/arquivo, 20.000 arquivos. Este projeto: 141 arquivos, maior = ~10 MB. OK.
- CTAs de WhatsApp e links sociais funcionam (URLs externas).
- Fontes Google (Roboto/Inter) carregam de fonts.googleapis.com.
- Formularios/area dinamica do WordPress original (admin-ajax/jet-engine) NAO existem aqui — e site estatico.
