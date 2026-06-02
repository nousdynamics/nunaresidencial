#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera site/form/index.html a partir de site/index.html.

- Reescreve refs de assets relativas (wp-content / wp-includes / cdn-cgi)
  para root-absolute, ja que a pagina passa a ser servida de /form/.
- Sequestra os CTAs de WhatsApp e injeta o funil de qualificacao (modal).

Re-rodar regenera /form a partir da landing atual.
Spec: docs/superpowers/specs/2026-06-02-form-funil-design.md
"""
import pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "site" / "index.html"
OUT = ROOT / "site" / "form" / "index.html"

WHATSAPP_PHONE = "5514991363259"
WEBHOOK = "https://hook.us2.make.com/h8dc6u1h184j14ovku6sbuv75enh8bqa"

# --- 1. reescreve paths relativos -> root-absolute ---------------------------
def rewrite_assets(html: str) -> str:
    repl = [
        ('"wp-content/', '"/wp-content/'),
        ('"wp-includes/', '"/wp-includes/'),
        ('"cdn-cgi/', '"/cdn-cgi/'),
        (' wp-content/', ' /wp-content/'),   # entradas de srcset apos virgula+espaco
    ]
    for a, b in repl:
        html = html.replace(a, b)
    return html

# --- 2. widget do funil (CSS + HTML + JS) ------------------------------------
FUNNEL = r"""
<!-- ===================== FUNIL DE QUALIFICACAO (/form) ===================== -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Mulish:wght@400;500;600;700;800&display=swap');
:root{
 --nf-cream:#FBF7EF;--nf-card:#FFFDF8;--nf-ink:#0B3A2C;--nf-green:#18A871;
 --nf-green-d:#0D7A52;--nf-amber:#E0A33B;--nf-muted:#6E7E73;--nf-line:#E7E0D2;
}
.nf-overlay{position:fixed;inset:0;z-index:999999;display:none;align-items:center;justify-content:center;padding:18px;
 background:radial-gradient(120% 120% at 50% 0%,rgba(13,122,82,.42),rgba(11,58,44,.74));
 -webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);
 font-family:'Mulish',system-ui,sans-serif}
.nf-overlay.nf-open{display:flex;animation:nf-fade .3s ease}
@keyframes nf-fade{from{opacity:0}to{opacity:1}}
.nf-card{position:relative;width:100%;max-width:462px;max-height:94vh;overflow-y:auto;
 background:var(--nf-card);border-radius:28px;padding:36px 32px 32px;
 box-shadow:0 30px 80px -20px rgba(11,58,44,.55),0 1px 0 rgba(255,255,255,.7) inset;
 animation:nf-rise .45s cubic-bezier(.16,1,.3,1)}
@keyframes nf-rise{from{opacity:0;transform:translateY(26px) scale(.985)}to{opacity:1;transform:none}}
.nf-card::before{content:"";position:absolute;inset:0;border-radius:28px;padding:1px;pointer-events:none;
 background:linear-gradient(180deg,rgba(224,163,59,.55),rgba(24,168,113,.22) 55%,transparent);
 -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);
 -webkit-mask-composite:xor;mask-composite:exclude}
.nf-close{position:absolute;top:15px;right:15px;width:34px;height:34px;border-radius:50%;
 border:1px solid var(--nf-line);background:#fff;color:var(--nf-muted);font-size:17px;line-height:1;
 cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.2s}
.nf-close:hover{background:var(--nf-ink);color:#fff;border-color:var(--nf-ink);transform:rotate(90deg)}
.nf-brand{display:flex;align-items:center;justify-content:center;margin:2px 0 20px}
.nf-wm{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:30px;letter-spacing:-.02em;
 line-height:1;color:var(--nf-ink)}
.nf-wm i{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--nf-amber);margin-left:3px}
.nf-eyebrow{display:block;text-align:center;font-size:11px;font-weight:800;letter-spacing:.2em;
 text-transform:uppercase;color:var(--nf-amber);margin:0 0 9px}
.nf-step{display:none}
.nf-step.nf-active{display:block;animation:nf-step .4s ease}
@keyframes nf-step{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.nf-h{font-family:'Fraunces',Georgia,serif;font-optical-sizing:auto;font-weight:600;font-size:27px;
 line-height:1.15;letter-spacing:-.01em;color:var(--nf-ink);margin:0 0 8px;text-align:center}
.nf-sub{font-size:15.5px;color:var(--nf-muted);margin:0 0 26px;text-align:center;line-height:1.5}
.nf-field{margin-bottom:17px;text-align:left}
.nf-label{display:block;font-size:13px;font-weight:700;color:var(--nf-ink);margin:0 0 7px}
.nf-input{width:100%;box-sizing:border-box;padding:15px 16px;font-family:inherit;font-size:16.5px;
 color:var(--nf-ink);background:#fff;border:1.5px solid var(--nf-line);border-radius:14px;outline:none;
 transition:border-color .18s,box-shadow .18s}
.nf-input::placeholder{color:#B7BEB6}
.nf-input:focus{border-color:var(--nf-green);box-shadow:0 0 0 4px rgba(24,168,113,.14)}
.nf-err{color:#C8443A;font-size:13.5px;margin:-4px 0 14px;display:none;text-align:left}
.nf-btn{position:relative;width:100%;box-sizing:border-box;padding:17px;font-family:inherit;font-size:16.5px;
 font-weight:800;letter-spacing:.02em;color:#fff;border:none;border-radius:14px;cursor:pointer;
 background:linear-gradient(135deg,var(--nf-green),var(--nf-green-d));
 box-shadow:0 12px 24px -8px rgba(13,122,82,.6);transition:transform .18s,box-shadow .18s}
.nf-btn:hover{transform:translateY(-2px);box-shadow:0 18px 30px -8px rgba(13,122,82,.65)}
.nf-btn:active{transform:translateY(0)}
.nf-arrow{display:inline-block;margin-left:8px;transition:transform .2s}
.nf-btn:hover .nf-arrow{transform:translateX(4px)}
.nf-opt{position:relative;width:100%;box-sizing:border-box;text-align:left;padding:18px 46px 18px 20px;
 margin-bottom:13px;font-family:inherit;font-size:16px;font-weight:700;color:var(--nf-ink);background:#fff;
 border:1.5px solid var(--nf-line);border-radius:16px;cursor:pointer;
 transition:border-color .18s,background .18s,transform .18s,box-shadow .18s}
.nf-opt::after{content:"";position:absolute;right:19px;top:50%;width:9px;height:9px;
 border-right:2px solid var(--nf-green);border-top:2px solid var(--nf-green);
 transform:translateY(-50%) rotate(45deg);transition:right .18s}
.nf-opt:hover{border-color:var(--nf-green);background:#F4FBF7;transform:translateY(-2px);
 box-shadow:0 10px 22px -12px rgba(13,122,82,.5)}
.nf-opt:hover::after{right:15px}
.nf-opt small{display:block;font-weight:500;font-size:13px;color:var(--nf-muted);margin-top:3px}
.nf-badge{width:74px;height:74px;margin:0 auto 18px;border-radius:50%;display:flex;align-items:center;
 justify-content:center;background:linear-gradient(135deg,rgba(24,168,113,.16),rgba(224,163,59,.2));
 color:var(--nf-green);animation:nf-pop .5s cubic-bezier(.18,1.4,.4,1)}
@keyframes nf-pop{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}
.nf-badge svg{width:34px;height:34px}
.nf-count{font-size:14.5px;color:var(--nf-muted);text-align:center;margin:20px 0 0}
.nf-count b{color:var(--nf-green);font-weight:800}
.nf-bar{height:5px;width:100%;background:var(--nf-line);border-radius:99px;overflow:hidden;margin-top:12px}
.nf-bar i{display:block;height:100%;width:100%;border-radius:99px;
 background:linear-gradient(90deg,var(--nf-green),var(--nf-amber))}
.nf-step[data-step="obrigado"].nf-active .nf-bar i{animation:nf-deplete 5s linear forwards}
@keyframes nf-deplete{from{width:100%}to{width:0}}
.nf-link{display:block;text-align:center;margin-top:16px;font-family:inherit;font-size:14px;color:var(--nf-muted);
 background:none;border:none;cursor:pointer;width:100%}
.nf-link:hover{color:var(--nf-ink);text-decoration:underline}
</style>

<div class="nf-overlay" id="nf-overlay" role="dialog" aria-modal="true">
 <div class="nf-card">
  <button class="nf-close" id="nf-close" aria-label="Fechar">&times;</button>
  <div class="nf-brand"><span class="nf-wm">nuna<i></i></span></div>

  <!-- Step: Lead -->
  <div class="nf-step nf-active" data-step="lead">
   <span class="nf-eyebrow">Atendimento Nuna</span>
   <p class="nf-h">Vamos conversar sobre a Nuna</p>
   <p class="nf-sub">Preencha seus dados e a gente continua pelo WhatsApp.</p>
   <div class="nf-field">
    <label class="nf-label" for="nf-nome">Seu nome</label>
    <input class="nf-input" id="nf-nome" type="text" placeholder="Nome completo" autocomplete="name">
   </div>
   <div class="nf-field">
    <label class="nf-label" for="nf-whats">Seu WhatsApp</label>
    <input class="nf-input" id="nf-whats" type="tel" placeholder="(14) 99999-9999" autocomplete="tel">
   </div>
   <div class="nf-err" id="nf-err">Preencha o nome e um WhatsApp valido com DDD.</div>
   <button class="nf-btn" id="nf-lead-go">Continuar<span class="nf-arrow">&rarr;</span></button>
  </div>

  <!-- Step: Qualificacao -->
  <div class="nf-step" data-step="qualificacao">
   <span class="nf-eyebrow">Passo 2</span>
   <p class="nf-h">A mensalidade parte de R$ 6.000/mes</p>
   <p class="nf-sub">Como isso se encaixa pra voce?</p>
   <button class="nf-opt" data-q="apto">Esta dentro do meu orcamento</button>
   <button class="nf-opt" data-q="orcamento">Esta acima do meu orcamento</button>
   <button class="nf-opt" data-q="emprego">Quero trabalhar / enviar curriculo</button>
  </div>

  <!-- Step: Orcamento -->
  <div class="nf-step" data-step="orcamento">
   <span class="nf-eyebrow">Quase la</span>
   <p class="nf-h">Qual orcamento mensal cabe pra voce?</p>
   <p class="nf-sub">Selecione a faixa mais proxima.</p>
   <button class="nf-opt" data-faixa="Ate R$ 1.000">Ate R$ 1.000</button>
   <button class="nf-opt" data-faixa="R$ 2.000 a R$ 3.000">R$ 2.000 a R$ 3.000</button>
   <button class="nf-opt" data-faixa="R$ 3.000 a R$ 4.000">R$ 3.000 a R$ 4.000</button>
   <button class="nf-opt" data-faixa="R$ 4.000 a R$ 5.000">R$ 4.000 a R$ 5.000</button>
  </div>

  <!-- Step: Obrigado (apto / orcamento) -->
  <div class="nf-step" data-step="obrigado">
   <div class="nf-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
   <p class="nf-h" id="nf-ob-h">Recebemos seus dados!</p>
   <p class="nf-sub" id="nf-ob-sub">Vamos te levar pro WhatsApp pra continuar o atendimento.</p>
   <button class="nf-btn" id="nf-wa-now">Falar agora no WhatsApp<span class="nf-arrow">&rarr;</span></button>
   <p class="nf-count">Redirecionando em <b id="nf-count">5</b>s...</p>
   <div class="nf-bar"><i></i></div>
  </div>

  <!-- Step: Emprego (beco sem saida) -->
  <div class="nf-step" data-step="emprego">
   <div class="nf-badge" style="background:linear-gradient(135deg,rgba(110,126,115,.16),rgba(224,163,59,.2));color:var(--nf-amber)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg></div>
   <p class="nf-h">Obrigado pelo interesse!</p>
   <p class="nf-sub">No momento nao recebemos curriculos por este canal.
    Agradecemos o contato e desejamos sucesso.</p>
   <button class="nf-btn" id="nf-emp-close" style="background:linear-gradient(135deg,#8A958C,#6E7E73);box-shadow:0 12px 24px -8px rgba(110,126,115,.5)">Fechar</button>
  </div>

 </div>
</div>

<script>
(function(){
 var PHONE="__PHONE__", WEBHOOK="__WEBHOOK__";
 var ov=document.getElementById('nf-overlay');
 var lead={nome:'',whatsapp:'',categoria:'',orcamento:null};
 var timer=null;

 function show(step){
  ov.querySelectorAll('.nf-step').forEach(function(s){
   s.classList.toggle('nf-active', s.dataset.step===step);
  });
 }
 function open(){ ov.classList.add('nf-open'); document.body.style.overflow='hidden'; show('lead'); }
 function close(){
  ov.classList.remove('nf-open'); document.body.style.overflow='';
  if(timer){clearInterval(timer);timer=null;}
  show('lead');
 }

 // sequestra todos os CTAs de WhatsApp
 document.querySelectorAll('a[href*="whatsapp"]').forEach(function(a){
  a.addEventListener('click',function(e){ e.preventDefault(); open(); });
 });
 document.getElementById('nf-close').addEventListener('click',close);
 ov.addEventListener('click',function(e){ if(e.target===ov) close(); });

 // Step Lead -> Qualificacao
 document.getElementById('nf-lead-go').addEventListener('click',function(){
  var nome=document.getElementById('nf-nome').value.trim();
  var whats=document.getElementById('nf-whats').value.trim();
  var digits=whats.replace(/\D/g,'');
  if(nome.length<2 || digits.length<10){
   document.getElementById('nf-err').style.display='block'; return;
  }
  document.getElementById('nf-err').style.display='none';
  lead.nome=nome; lead.whatsapp=whats;
  show('qualificacao');
 });

 // Step Qualificacao
 ov.querySelectorAll('[data-q]').forEach(function(b){
  b.addEventListener('click',function(){
   var q=b.dataset.q;
   if(q==='apto'){ lead.categoria='apto'; finishConversao('apto'); }
   else if(q==='orcamento'){ show('orcamento'); }
   else { lead.categoria='emprego'; finishEmprego(); }
  });
 });

 // Step Orcamento
 ov.querySelectorAll('[data-faixa]').forEach(function(b){
  b.addEventListener('click',function(){
   lead.categoria='orcamento'; lead.orcamento=b.dataset.faixa;
   finishConversao('orcamento');
  });
 });

 function sendWebhook(){
  try{
   fetch(WEBHOOK,{
    method:'POST', keepalive:true,
    headers:{'Content-Type':'text/plain;charset=UTF-8'},
    body:JSON.stringify({
     nome:lead.nome, whatsapp:lead.whatsapp, categoria:lead.categoria,
     orcamento:lead.orcamento, origem:'form', timestamp:new Date().toISOString()
    })
   }).catch(function(){});
  }catch(e){}
 }

 function waUrl(){
  var msg;
  if(lead.categoria==='apto'){
   msg='Ola! Me chamo '+lead.nome+'. Tenho interesse na Nuna Residencial Senior e a '+
       'mensalidade de R$ 6.000 esta dentro do meu orcamento.';
  }else{
   msg='Ola! Me chamo '+lead.nome+'. Tenho interesse na Nuna Residencial Senior. '+
       'Meu orcamento mensal e '+lead.orcamento+'.';
  }
  return 'https://api.whatsapp.com/send?phone='+PHONE+'&text='+encodeURIComponent(msg);
 }

 function finishConversao(cat){
  sendWebhook();
  var url=waUrl();
  document.getElementById('nf-ob-sub').textContent=
   (cat==='apto')
    ? 'Perfeito! Vamos te levar pro WhatsApp pra agendar uma visita.'
    : 'Obrigado! Vamos continuar pelo WhatsApp pra ver as melhores opcoes.';
  document.getElementById('nf-wa-now').onclick=function(){ go(url); };
  show('obrigado');
  startCountdown(5,url);
 }

 function finishEmprego(){
  sendWebhook();
  show('emprego');
 }

 function startCountdown(secs,url){
  var el=document.getElementById('nf-count'); el.textContent=secs;
  if(timer) clearInterval(timer);
  timer=setInterval(function(){
   secs--; el.textContent=secs;
   if(secs<=0){ clearInterval(timer); timer=null; go(url); }
  },1000);
 }
 function go(url){ if(timer){clearInterval(timer);timer=null;} window.location.href=url; }

 document.getElementById('nf-emp-close').addEventListener('click',close);
})();
</script>
<!-- =================== /FIM FUNIL DE QUALIFICACAO ========================== -->
"""

def main():
    html = SRC.read_text(encoding="utf-8")
    html = rewrite_assets(html)
    funnel = FUNNEL.replace("__PHONE__", WHATSAPP_PHONE).replace("__WEBHOOK__", WEBHOOK)
    if "</body>" in html:
        html = html.replace("</body>", funnel + "\n</body>", 1)
    else:
        html += funnel
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print("Gerado:", OUT)

if __name__ == "__main__":
    main()
