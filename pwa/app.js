"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const eur = n => n == null ? "" : n.toLocaleString("it-IT",{minimumFractionDigits:2,maximumFractionDigits:2});
const fmtD = s => s ? s.slice(8,10)+"/"+s.slice(5,7) : "";
const norm = s => (s||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"");
const PAGE = 60;
// Da dove leggere le offerte: il file accanto all'app, oppure un indirizzo esterno (es. GitHub Pages)
const DATA_URL = (document.querySelector('meta[name="spesaok-dati"]') || {}).content || "offerte.json";
const ICON_GO = `<svg viewBox="0 0 24 24"><path d="M3 11 21 3l-8 18-2-8-8-2Z"/></svg>`;
const ICON_DOC = `<svg viewBox="0 0 24 24"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>`;

let DATA = {offerte:[]}, NEG = {}, chains = [];
const state = {q:"", on:new Set(), sort:"unit", nocard:false, shown:PAGE};
try { const s = JSON.parse(localStorage.getItem("spesaok")||"{}"); if (s.sort) state.sort = s.sort; if (s.nocard) state.nocard = true; } catch(e) {}
const save = () => { try { localStorage.setItem("spesaok", JSON.stringify({sort:state.sort, nocard:state.nocard})); } catch(e) {} };

function mapsUrl(catena){
  const n = NEG[catena];
  if (n && n.tipo === "negozio")
    return "https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=" + encodeURIComponent(n.indirizzo);
  return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent((n && n.cerca) || catena);
}
const color = c => (NEG[c] && NEG[c].colore) || "var(--accent)";
const short = c => (NEG[c] && NEG[c].etichetta) || c;
// Logo della catena; se manca, iniziali su fondo colorato
const logo = (c, cls) => NEG[c] && NEG[c].logo
  ? `<span class="${cls}"><img src="${esc(NEG[c].logo)}" alt="${esc(c)}" loading="lazy"></span>`
  : `<span class="${cls} ini" style="background:${color(c)}" aria-label="${esc(c)}">${esc(c.slice(0,2).toUpperCase())}</span>`;

async function load(){
  const [o, n] = await Promise.all([
    fetch(DATA_URL, {cache:"no-cache"}).then(r => r.json()),
    fetch("negozi.json").then(r => r.json()).catch(() => ({}))
  ]);
  DATA = o; NEG = n;
  chains = [...new Set(DATA.offerte.map(x => x.catena))].sort();
  chains.forEach(c => state.on.add(c));
  $("sub").textContent = `${DATA.offerte.length} offerte · aggiornate al ${DATA.aggiornato.split("-").reverse().join("/")}`;
  buildChips(); buildStores(); buildInfo(); buildLinee(); render();
}

function buildChips(){
  $("chains").innerHTML = chains.map(c => `<button class="brand-t" aria-pressed="true" data-c="${esc(c)}" title="${esc(c)}">${logo(c, "lg")}<span class="cap">${esc(short(c))}</span></button>`).join("");
  $("chains").onclick = e => {
    const b = e.target.closest(".brand-t"); if (!b) return;
    const c = b.dataset.c; state.on.has(c) ? state.on.delete(c) : state.on.add(c);
    b.setAttribute("aria-pressed", state.on.has(c)); state.shown = PAGE; render();
  };
}

function key(o){
  if (state.sort === "price") return o.prezzo;
  if (state.sort === "disc") return -(o.sconto_pct || (o.prezzo_pieno ? 100*(1-o.prezzo/o.prezzo_pieno) : 0));
  return o.prezzo_unita ?? 1e9;
}

let rows = [];
function render(){
  const words = state.q.split(/\s+/).filter(Boolean);
  rows = DATA.offerte.filter(o => state.on.has(o.catena) && !(state.nocard && o.con_carta) &&
      words.every(w => norm(`${o.nome} ${o.marca} ${o.categoria} ${o.catena} ${o.formato}`).includes(w)))
    .sort((a,b) => key(a)-key(b) || a.prezzo-b.prezzo);
  $("count").textContent = `${rows.length} risultati`;
  if ((DATA.linee_coop||[]).length) $("linee").hidden = !!state.q || !state.on.has("Coop Collegno");
  const list = $("list");
  if (!rows.length) { list.innerHTML = `<div class="empty">Nessuna offerta trovata.<br>Prova un'altra parola o riattiva le catene.</div>`; $("more").hidden = true; return; }
  list.innerHTML = rows.slice(0, state.shown).map(card).join("");
  $("more").hidden = rows.length <= state.shown;
}

function card(o){
  const pct = o.sconto_pct || (o.prezzo_pieno && o.prezzo_pieno > o.prezzo ? Math.round(100*(1-o.prezzo/o.prezzo_pieno)) : null);
  return `<li class="item">
    ${logo(o.catena, "lg item-logo")}
    <div class="body"><div class="name">${esc(o.nome)}${o.marca ? ` <small>· ${esc(o.marca)}</small>` : ""}</div>
      <div class="meta"><span class="store">${esc(o.catena)}</span>${o.formato ? `<span>${esc(o.formato)}</span>` : ""}
        <span>fino al ${fmtD(o.valido_al)}</span>${o.con_carta ? `<span class="badge">prezzo con carta</span>` : ""}${o.da_verificare ? `<span class="badge warn">da verificare</span>` : ""}</div></div>
    <div class="tag">${pct ? `<span class="pct">−${pct}%</span>` : ""}${o.prezzo_pieno && o.prezzo_pieno > o.prezzo ? `<div class="old">€ ${eur(o.prezzo_pieno)}</div>` : ""}
      <div class="p">€ ${eur(o.prezzo)}</div>${o.prezzo_unita ? `<div class="u">€ ${eur(o.prezzo_unita)}/${esc(o.unita||"pz")}</div>` : ""}</div>
    <div class="actions">
      <a class="go primary" href="${mapsUrl(o.catena)}" target="_blank" rel="noopener">${ICON_GO}Portami</a>
      ${o.fonte ? `<a class="go" href="${esc(o.fonte)}" target="_blank" rel="noopener">${ICON_DOC}Volantino${o.pagina ? " p. "+o.pagina : ""}</a>` : ""}
    </div></li>`;
}

function buildStores(){
  const cnt = {}; DATA.offerte.forEach(o => cnt[o.catena] = (cnt[o.catena]||0)+1);
  $("stores").innerHTML = chains.map(c => {
    const n = NEG[c] || {tipo:"catena"};
    const fonte = (DATA.offerte.find(o => o.catena === c && o.fonte) || {}).fonte;
    return `<div class="store-card">
      <div class="store-h">${logo(c, "lg")}<h3>${esc(c)}</h3></div>
      <p>${n.tipo === "negozio" ? `📍 ${esc(n.indirizzo)} · prezzi del volantino di questo negozio` : "Prezzi validi nei punti vendita della zona: cerchiamo il più vicino a te"}</p>
      ${n.nota ? `<p>${esc(n.nota)}</p>` : ""}
      <p>${cnt[c]} offerte in lista</p>
      <div class="actions">
        <a class="go primary" href="${mapsUrl(c)}" target="_blank" rel="noopener">${ICON_GO}${n.tipo === "negozio" ? "Portami" : "Il più vicino"}</a>
        ${fonte ? `<a class="go" href="${esc(fonte)}" target="_blank" rel="noopener">${ICON_DOC}Volantino</a>` : ""}
        <button class="go" data-filter="${esc(c)}">Solo le sue offerte</button>
      </div></div>`;
  }).join("");
  $("stores").onclick = e => {
    const b = e.target.closest("[data-filter]"); if (!b) return;
    state.on = new Set([b.dataset.filter]);
    document.querySelectorAll("#chains .brand-t").forEach(x => x.setAttribute("aria-pressed", state.on.has(x.dataset.c)));
    state.shown = PAGE; render(); show("offerte");
  };
}

function buildInfo(){
  $("info").innerHTML = `
    <p><b>spesaok</b> raccoglie ogni settimana le offerte alimentari dai volantini online dei supermercati di Torino e dintorni e le ordina dalla più conveniente, al kg/litro o per confezione.</p>
    <p>Fonti: ${(DATA.fonti||[]).map(esc).join(" · ")}. Aggiornamento del ${DATA.aggiornato.split("-").reverse().join("/")}.</p>
    <p>Le offerte "prezzo con carta" valgono solo per i titolari della carta fedeltà della catena.</p>
    <p>Mercatò e MD sono letti con riconoscimento automatico del testo (OCR) dalle immagini del volantino: il prezzo può differire di qualche centesimo. Aldi: prezzi nazionali, fino a esaurimento scorte; la data "fino al" è indicativa.</p>
    <p>I prezzi sono quelli pubblicati nei volantini: verifica sempre in negozio. Ogni offerta ha il link al volantino originale.</p>
    <p>Funziona anche senza connessione, con le ultime offerte scaricate.</p>`;
}

function buildLinee(){
  const L = DATA.linee_coop || []; if (!L.length) return;
  const box = $("linee");
  box.innerHTML = `<h2>Coop Collegno: sconti su intere linee di marca</h2>
    <p>In queste pagine lo sconto vale su tutti i prodotti delle marche raffigurate. Il volantino mostra solo i loghi, senza prezzi.</p>
    <ul>${L.map(l => `<li><b>−${l.pct}%</b> su tutta la linea · <a href="${esc(l.volantino)}" target="_blank" rel="noopener">pagina ${l.pagina} del volantino</a></li>`).join("")}</ul>`;
  box.hidden = false;
}

/* Navigazione tra le sezioni */
function show(v){
  ["offerte","negozi","info"].forEach(x => $("v-"+x).hidden = x !== v);
  document.querySelectorAll(".tabs button").forEach(b => b.dataset.v === v ? b.setAttribute("aria-current","page") : b.removeAttribute("aria-current"));
  if (location.hash.slice(1) !== v) history.replaceState(null, "", v === "offerte" ? location.pathname : "#"+v);
  window.scrollTo(0,0);
}
document.querySelector(".tabs").onclick = e => { const b = e.target.closest("button"); if (b) show(b.dataset.v); };

let t; $("q").oninput = e => { clearTimeout(t); t = setTimeout(() => { state.q = norm(e.target.value); state.shown = PAGE; render(); }, 120); };
$("sort").value = state.sort;
$("sort").onchange = e => { state.sort = e.target.value; save(); state.shown = PAGE; render(); };
$("nocard").setAttribute("aria-pressed", state.nocard);
$("nocard").onclick = () => { state.nocard = !state.nocard; $("nocard").setAttribute("aria-pressed", state.nocard); save(); render(); };
$("more").onclick = () => { state.shown += PAGE; render(); };

function toast(html, ms){ const el = $("toast"); el.innerHTML = html; el.hidden = false; if (ms) setTimeout(() => el.hidden = true, ms); return el; }

/* Installazione */
let deferred;
window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); deferred = e; $("install").hidden = false; });
$("install").onclick = async () => { if (!deferred) return; deferred.prompt(); await deferred.userChoice; deferred = null; $("install").hidden = true; };
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent), standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone;
if (isIOS && !standalone) { try { if (!localStorage.getItem("spesaok-ios")) { localStorage.setItem("spesaok-ios","1"); setTimeout(() => toast("Per installarla: tocca Condividi e poi “Aggiungi alla schermata Home”.", 9000), 1500); } } catch(e) {} }

/* Service worker: uso offline e avviso di nuova versione */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").then(reg => {
    reg.addEventListener("updatefound", () => {
      const nw = reg.installing;
      nw.addEventListener("statechange", () => {
        if (nw.state === "installed" && navigator.serviceWorker.controller)
          toast(`Nuova versione disponibile <button id="reload">Aggiorna</button>`).querySelector("#reload").onclick = () => location.reload();
      });
    });
  }).catch(() => {});
}
window.addEventListener("offline", () => toast("Sei offline: vedi le ultime offerte scaricate.", 4000));

show(["negozi","info"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "offerte");
load().catch(() => { $("list").innerHTML = `<div class="empty">Non riesco a caricare le offerte. Controlla la connessione e riprova.</div>`; });
