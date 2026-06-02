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
.nf-overlay{position:fixed;inset:0;background:rgba(11,90,64,.55);backdrop-filter:blur(2px);
 display:none;align-items:center;justify-content:center;z-index:999999;padding:16px;
 font-family:'Roboto','Inter',system-ui,sans-serif}
.nf-overlay.nf-open{display:flex}
.nf-card{background:#fff;width:100%;max-width:480px;max-height:92vh;overflow-y:auto;
 border-radius:20px;padding:28px 24px;box-shadow:0 18px 60px rgba(0,0,0,.35);
 position:relative;animation:nf-in .25s ease}
@keyframes nf-in{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
.nf-close{position:absolute;top:12px;right:14px;background:none;border:none;font-size:26px;
 line-height:1;color:#9aa0a6;cursor:pointer;padding:4px}
.nf-close:hover{color:#4B4B53}
.nf-step{display:none}
.nf-step.nf-active{display:block}
.nf-logo{display:block;height:34px;margin:0 auto 14px}
.nf-h{font-size:21px;font-weight:700;color:#0B5A40;margin:0 0 6px;text-align:center;line-height:1.25}
.nf-sub{font-size:15px;color:#4B4B53;margin:0 0 20px;text-align:center;line-height:1.4}
.nf-label{display:block;font-size:13px;font-weight:600;color:#4B4B53;margin:0 0 6px}
.nf-input{width:100%;box-sizing:border-box;padding:13px 14px;font-size:16px;border:1.5px solid #d6dbd8;
 border-radius:12px;margin-bottom:14px;outline:none;transition:border-color .15s}
.nf-input:focus{border-color:#18A871}
.nf-err{color:#FF385C;font-size:13px;margin:-8px 0 12px;display:none}
.nf-btn{width:100%;box-sizing:border-box;padding:15px;font-size:16px;font-weight:700;border:none;
 border-radius:12px;cursor:pointer;background:#18A871;color:#fff;transition:background .15s}
.nf-btn:hover{background:#0D8E5F}
.nf-opt{width:100%;box-sizing:border-box;text-align:left;padding:16px 18px;margin-bottom:12px;
 font-size:16px;font-weight:600;color:#0B5A40;background:#F4FBF7;border:1.5px solid #D3F8E3;
 border-radius:14px;cursor:pointer;transition:all .15s}
.nf-opt:hover{background:#D3F8E3;border-color:#18A871;transform:translateY(-1px)}
.nf-opt small{display:block;font-weight:400;font-size:13px;color:#4B4B53;margin-top:2px}
.nf-count{font-size:15px;color:#4B4B53;text-align:center;margin:18px 0}
.nf-count b{color:#18A871;font-size:18px}
.nf-link{display:block;text-align:center;margin-top:14px;font-size:14px;color:#9aa0a6;
 background:none;border:none;cursor:pointer;width:100%}
.nf-link:hover{color:#4B4B53}
.nf-emoji{font-size:44px;text-align:center;margin:0 0 10px}
</style>

<div class="nf-overlay" id="nf-overlay" role="dialog" aria-modal="true">
 <div class="nf-card">
  <button class="nf-close" id="nf-close" aria-label="Fechar">&times;</button>

  <!-- Step: Lead -->
  <div class="nf-step nf-active" data-step="lead">
   <p class="nf-h">Vamos conversar sobre a Nuna</p>
   <p class="nf-sub">Preencha seus dados para continuar.</p>
   <label class="nf-label" for="nf-nome">Seu nome</label>
   <input class="nf-input" id="nf-nome" type="text" placeholder="Nome completo" autocomplete="name">
   <label class="nf-label" for="nf-whats">Seu WhatsApp</label>
   <input class="nf-input" id="nf-whats" type="tel" placeholder="(14) 99999-9999" autocomplete="tel">
   <div class="nf-err" id="nf-err">Preencha nome e um WhatsApp valido (com DDD).</div>
   <button class="nf-btn" id="nf-lead-go">Continuar</button>
  </div>

  <!-- Step: Qualificacao -->
  <div class="nf-step" data-step="qualificacao">
   <p class="nf-h">A mensalidade da Nuna parte de R$ 6.000/mes</p>
   <p class="nf-sub">Como isso se encaixa pra voce?</p>
   <button class="nf-opt" data-q="apto">Esta dentro do meu orcamento</button>
   <button class="nf-opt" data-q="orcamento">Esta acima do meu orcamento</button>
   <button class="nf-opt" data-q="emprego">Quero trabalhar / enviar curriculo</button>
  </div>

  <!-- Step: Orcamento -->
  <div class="nf-step" data-step="orcamento">
   <p class="nf-h">Qual orcamento mensal cabe pra voce?</p>
   <p class="nf-sub">Selecione a faixa mais proxima.</p>
   <button class="nf-opt" data-faixa="Ate R$ 1.000">Ate R$ 1.000</button>
   <button class="nf-opt" data-faixa="R$ 2.000 a R$ 3.000">R$ 2.000 a R$ 3.000</button>
   <button class="nf-opt" data-faixa="R$ 3.000 a R$ 4.000">R$ 3.000 a R$ 4.000</button>
   <button class="nf-opt" data-faixa="R$ 4.000 a R$ 5.000">R$ 4.000 a R$ 5.000</button>
  </div>

  <!-- Step: Obrigado (apto / orcamento) -->
  <div class="nf-step" data-step="obrigado">
   <p class="nf-emoji">&#9989;</p>
   <p class="nf-h" id="nf-ob-h">Recebemos seus dados!</p>
   <p class="nf-sub" id="nf-ob-sub">Vamos te levar pro WhatsApp pra continuar o atendimento.</p>
   <button class="nf-btn" id="nf-wa-now">Falar agora no WhatsApp</button>
   <p class="nf-count">Redirecionando em <b id="nf-count">5</b>s...</p>
  </div>

  <!-- Step: Emprego (beco sem saida) -->
  <div class="nf-step" data-step="emprego">
   <p class="nf-emoji">&#128188;</p>
   <p class="nf-h">Obrigado pelo interesse!</p>
   <p class="nf-sub">No momento nao recebemos curriculos por este canal.
    Agradecemos o contato e desejamos sucesso.</p>
   <button class="nf-btn" id="nf-emp-close">Fechar</button>
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
