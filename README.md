# nunaresidencial

Clone estatico (HTML/CSS/JS) da landing page **nunaresidencial.com.br**, pronto para deploy no **Cloudflare Pages**.

Origem: site WordPress/Elementor Pro, espelhado para arquivos estaticos.

## Estrutura

```
.
├─ site/          <- conteudo publicado (output dir do Pages)
│  ├─ index.html
│  ├─ _headers    <- cache + headers de seguranca
│  └─ wp-content/ ... css, js, imagens, fonts, video
├─ wrangler.toml  <- config Cloudflare Pages (pages_build_output_dir = site)
├─ package.json   <- scripts preview/deploy
├─ scrape.py      <- gerador do clone (re-rodar atualiza o espelho)
└─ DEPLOY.md      <- instrucoes de deploy
```

## Deploy rapido

```bash
npx wrangler login
npx wrangler pages deploy site --project-name=nuna-residencial
```

Detalhes e alternativas (dashboard / Git CI): ver [DEPLOY.md](DEPLOY.md).

## Preview local

```bash
npm run preview   # http://localhost:8765
```
