# Design — Rota `/form` (versão funil de qualificação)

Data: 2026-06-02
Projeto: nunaresidencial-lp (clone estático landing Nuna Residencial Sênior)

## Objetivo

Criar segunda versão da landing em `/form`. Visual idêntico à landing atual,
mas todos os CTAs (que hoje vão direto pro WhatsApp) passam a abrir um **funil
de qualificação em modal**. Objetivo de negócio: qualificar leads por orçamento
e **filtrar/cortar quem só quer mandar currículo** (candidatos a emprego), que
hoje contaminam o WhatsApp comercial.

## Decisões (brainstorming)

- **Escopo**: `/form` = cópia da landing inteira + funil no clique dos CTAs.
- **Mecânica**: modal overlay, rota única `/form`. Steps trocam via JS, sem reload.
- **Captura de lead**: POST client-side pro webhook Make (sem backend).
- **Disparo webhook**: nos 3 desfechos (apto, orçamento, emprego), com categoria.
- **Etapa orçamento**: botões de faixa (não digitação), todas abaixo de R$ 6.000.
- **Mensagem WhatsApp**: pré-preenchida com os dados do formulário.

## Constantes

- WhatsApp: `https://api.whatsapp.com/send?phone=5514991363259`
- Webhook Make: `https://hook.us2.make.com/h8dc6u1h184j14ovku6sbuv75enh8bqa`
- Cores marca: verde primário `#18A871`, amarelo `#FFD361`, CTA vermelho `#FF385C`,
  verde escuro `#0D8E5F`.

## Arquitetura

Arquivo novo `site/form/index.html`, derivado de `site/index.html` com 3 mudanças:

1. **Paths de assets reescritos** para root-absolute: `wp-content/…` → `/wp-content/…`,
   `wp-includes/…` → `/wp-includes/…`, `cdn-cgi/…` → `/cdn-cgi/…`. Necessário porque
   a página agora é servida de `/form/` e paths relativos quebrariam.
2. **CTAs sequestrados**: no carregamento, JS seleciona todo `a[href*="whatsapp"]`,
   aplica `preventDefault` e religa o clique para abrir o funil. Robusto
   independente de quantos CTAs existam na landing.
3. **Widget do funil injetado** no fim do `<body>`: markup do modal + `<style>`
   escopado (prefixo `.nf-`, evita colisão com Elementor) + `<script>` vanilla.

Não há backend. Tudo client-side. Servido como asset estático do Worker.

## Fluxo do funil

```
[Lead]  Nome + WhatsApp  → Continuar
   ↓
[Qualificação]  "A mensalidade parte de R$ 6.000/mês"
   ├─ (1) Dentro do orçamento ─→ [Obrigado-Apto]        CONVERSÃO PRINCIPAL
   ├─ (2) Fora do orçamento  ─→ [Orçamento] (4 faixas) → [Obrigado-Orçamento]  CONVERSÃO SECUNDÁRIA
   └─ (3) Busco emprego      ─→ [Emprego]               corte (fim)
```

### Step Lead
- Campos: `nome` (texto), `whatsapp` (tel).
- Validação: nome não-vazio; whatsapp com ao menos 10 dígitos numéricos.
- Botão "Continuar" avança pra Qualificação.

### Step Qualificação
- Texto: "A mensalidade da Nuna parte de R$ 6.000/mês."
- 3 botões: `Está dentro do meu orçamento` / `Está acima do meu orçamento` / `Quero trabalhar / enviar currículo`.

### Step Orçamento (ramo 2)
- Texto: "Qual orçamento mensal cabe pra você?"
- 4 botões de faixa (valores exatos, abaixo de R$ 6.000):
  - `Até R$ 1.000`
  - `R$ 2.000 – R$ 3.000`
  - `R$ 3.000 – R$ 4.000`
  - `R$ 4.000 – R$ 5.000`
- Selecionar a faixa avança direto pra Obrigado-Orçamento (sem botão extra).

### Desfechos

| Ramo | Webhook `categoria` | Contador 5s → WhatsApp | Botão principal |
|------|--------------------|------------------------|-----------------|
| Apto | `apto` | sim | "Falar agora no WhatsApp" (pula contador) |
| Orçamento | `orcamento` (+ faixa) | sim | "Falar agora no WhatsApp" |
| Emprego | `emprego` | **não** | só "Fechar" — beco sem saída |

- **Apto / Orçamento**: tela de obrigado mostra contador "Redirecionando em 5… 4…".
  Ao chegar a 0, `window.location.href` = URL do WhatsApp pré-preenchida.
  Botão "Falar agora" pula o contador e redireciona já.
- **Emprego**: mensagem "Obrigado pelo interesse. No momento não recebemos
  currículos por aqui." Sem contador, sem link de WhatsApp. Só botão "Fechar"
  que fecha o modal. Este é o filtro central do funil.

## Webhook (POST Make)

Disparado uma vez ao entrar em cada desfecho. JSON:

```json
{
  "nome": "string",
  "whatsapp": "string (dígitos)",
  "categoria": "apto | orcamento | emprego",
  "orcamento": "Até R$ 1.000 | R$ 2.000 – R$ 3.000 | ... (só ramo orçamento, senão null)",
  "origem": "form",
  "timestamp": "ISO 8601"
}
```

- `fetch(webhook, { method:'POST', body: JSON, keepalive:true })` — `keepalive`
  garante envio mesmo durante o redirect pro WhatsApp.
- Envolto em `try/catch`; falha do webhook **não** bloqueia contador/redirect.
- `Content-Type: text/plain` (evita preflight CORS; Make aceita o corpo JSON).

## Mensagem WhatsApp pré-preenchida

Parâmetro `text=` montado com os dados do lead. Exemplos:

- Apto: `Olá! Me chamo {nome}. Tenho interesse na Nuna Residencial Sênior e a mensalidade de R$ 6.000 está dentro do meu orçamento.`
- Orçamento: `Olá! Me chamo {nome}. Tenho interesse na Nuna Residencial Sênior. Meu orçamento mensal é {faixa}.`

URL final: `https://api.whatsapp.com/send?phone=5514991363259&text=` + `encodeURIComponent(msg)`.

## Estado / Data flow

Objeto JS em memória acumula `{ nome, whatsapp, categoria, orcamento }` conforme
o usuário avança. No desfecho: (1) monta payload, (2) POST webhook, (3) ramo
apto/orçamento monta msg + inicia contador → redirect; ramo emprego encerra.

## Tratamento de erro

- Validação client-side no step Lead (bloqueia avanço com dados inválidos).
- Webhook em `try/catch` — nunca trava UX.
- Redirect WhatsApp acontece independente do resultado do webhook.

## Visual

- Modal full-screen overlay, fundo escurecido, card central branco arredondado.
- Botões de opção grandes (mobile-first; público sênior/familiares).
- Cores da marca. CSS escopado com prefixo `.nf-`.
- Botão de fechar (X) no topo, disponível em qualquer step. Fechar = abandona o
  funil e volta pra landing.

## Testes / verificação

Site estático — verificação manual via `npm run preview` (http.server em :8765):
- Abrir `/form/`, conferir que a landing renderiza igual (assets carregam).
- Clicar um CTA → funil abre.
- Percorrer os 3 ramos; conferir webhook recebido no Make e redirect/contador.
- Conferir ramo emprego não redireciona nem mostra WhatsApp.

## Fora de escopo (YAGNI)

- Sem backend, sem armazenamento próprio (Make cuida).
- Sem A/B testing, sem analytics além do webhook + msg WhatsApp.
- Sem alterar a landing original (`site/index.html`) — `/form` é adição isolada.
