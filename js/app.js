const state = {mentions: [], insights: [], filters:{from:"",to:"",search:""}, page:0, pageSize:50, searchTimer:null};
function $(id){return document.getElementById(id)}
function inRange(m){
  if(state.filters.from && m.fecha < state.filters.from) return false;
  if(state.filters.to && m.fecha > state.filters.to + "T23:59:59") return false;
  const q=state.filters.search.trim().toLowerCase();
  if(q){ const hay=[m.texto_original,m.texto_limpio,m.categoria,m.subcategoria,m.entidad_detectada].filter(Boolean).join(" ").toLowerCase(); if(!hay.includes(q)) return false; }
  return true;
}
function filtered(){return state.mentions.filter(inRange)}
function renderInsight(){
  const best=state.insights.slice().sort((a,b)=>(b.fecha||"").localeCompare(a.fecha||""))[0];
  $("insight-content").textContent=best ? (best.texto||best.summary||best.contenido||"Insight disponible.") : "Sin insight disponible.";
  $("insights-list").innerHTML=state.insights.length ? state.insights.map(x=>`<article class="insight-item"><strong>${escapeHtml(x.tipo||"Insight")}</strong><p>${escapeHtml(x.texto||x.summary||x.contenido||"")}</p><small>${escapeHtml(x.fecha||x.generated_at||"")}</small></article>`).join("") : "<p class='muted'>No hay insights disponibles.</p>";
}
function render(){
  const rows=filtered(), total=rows.length;
  const pos=rows.filter(x=>x.sentimiento_pysentimiento==="positivo").length;
  const neg=rows.filter(x=>x.sentimiento_pysentimiento==="negativo").length;
  const critical=rows.filter(x=>x.severidad==="critica").length;
  const avgScore=total ? rows.reduce((a,x)=>a+Number(x.score_matematico||0),0)/total : 0;
  const qualityMap={alta:1,media:.66,baja:.33,invalida:0};
  const avgQuality=total ? rows.reduce((a,x)=>a+(qualityMap[x.calidad_dato]??0),0)/total*100 : 0;
  $("kpi-total").textContent=total; $("kpi-positive").textContent=pos; $("kpi-negative").textContent=neg; $("kpi-critical").textContent=critical; $("kpi-score").textContent=avgScore.toFixed(1); $("kpi-quality").textContent=avgQuality.toFixed(0)+"%";
  const empty=$("empty-state"); empty.classList.toggle("hidden", total>0); if(total===0) empty.innerHTML="<strong>Aún no hay datos visibles.</strong><p>Ejecuta el pipeline de Python y carga datos_procesados.json.</p>";
  const byDay={}; rows.forEach(m=>{const d=(m.fecha||"").slice(0,10); if(!d)return; byDay[d]??={positivo:0,negativo:0,neutro:0}; byDay[d][m.sentimiento_pysentimiento]=(byDay[d][m.sentimiento_pysentimiento]||0)+1;});
  const labels=Object.keys(byDay).sort();
  renderNativeChart($("sentiment-chart"), labels, byDay);
  const start=state.page*state.pageSize, pageRows=rows.slice(start,start+state.pageSize); $("mentions-count").textContent=total; $("mentions-body").innerHTML=pageRows.map(m=>`<tr><td>${escapeHtml((m.fecha||"").slice(0,10))}</td><td>${escapeHtml(m.texto_original||"")}</td><td class="sent-${escapeHtml(m.sentimiento_pysentimiento||"")}">${escapeHtml(m.sentimiento_pysentimiento||"")}</td><td>${escapeHtml(m.categoria||"otro")}</td><td>${Number(m.score_matematico||0).toFixed(1)}</td><td>${escapeHtml(m.severidad||"")}</td><td>${escapeHtml(m.calidad_dato||"")}</td></tr>`).join("");
  $("page-status").textContent=total ? `${start+1}–${Math.min(start+pageRows.length,total)} de ${total}` : "0 de 0"; $("prev-page").disabled=state.page===0; $("next-page").disabled=start+state.pageSize>=total;
  const criticalRows=rows.filter(x=>x.severidad==="critica").slice(0,10); $("critical-feed").innerHTML=criticalRows.length ? criticalRows.map(m=>`<div class="feed-item"><strong>${escapeHtml(m.categoria||"otro")}</strong><div>${escapeHtml(m.texto_original||"")}</div><small>Score ${Number(m.score_matematico||0).toFixed(1)}</small></div>`).join("") : "<p class='muted'>No hay menciones críticas en el filtro actual.</p>";
  renderInsight();
}
function renderNativeChart(container, labels, byDay){
  const series=["positivo","negativo","neutro"];
  const width=900, height=300, pad={l:48,r:18,t:18,b:44};
  const innerW=width-pad.l-pad.r, innerH=height-pad.t-pad.b;
  const values=series.flatMap(k=>labels.map(d=>Number(byDay[d]?.[k]||0)));
  const max=Math.max(1,...values);
  const x=i=>labels.length<=1 ? pad.l+innerW/2 : pad.l+(i/(labels.length-1))*innerW;
  const y=v=>pad.t+innerH-(v/max)*innerH;
  const esc=escapeHtml;
  const grid=[0,.25,.5,.75,1].map(p=>{const yy=pad.t+innerH-p*innerH; return `<line x1="${pad.l}" y1="${yy}" x2="${width-pad.r}" y2="${yy}" class="chart-grid"/><text x="${pad.l-8}" y="${yy+4}" text-anchor="end" class="chart-label">${Math.round(max*p)}</text>`;}).join("");
  const paths=series.map(k=>{const pts=labels.map((d,i)=>`${x(i)},${y(Number(byDay[d]?.[k]||0))}`).join(" "); return `<polyline points="${pts}" class="chart-line chart-${k}" fill="none"/>`;}).join("");
  const legend=series.map(k=>`<span><i class="legend-dot chart-${k}"></i>${esc(k)}</span>`).join("");
  const ticks=labels.map((d,i)=>{if(labels.length>10 && i%Math.ceil(labels.length/10)!==0 && i!==labels.length-1)return ""; return `<text x="${x(i)}" y="${height-12}" text-anchor="middle" class="chart-label">${esc(d.slice(5))}</text>`;}).join("");
  container.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="sentiment-chart-title sentiment-chart-desc" preserveAspectRatio="none"><title id="sentiment-chart-title">Evolución del sentimiento</title><desc id="sentiment-chart-desc">Conteo diario de menciones positivas, negativas y neutras.</desc>${grid}${paths}${ticks}</svg><div class="chart-legend">${legend}</div>`;
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function validateClientPayload(payload){
  if(!payload || !Array.isArray(payload.mentions)) throw new Error("JSON_VALIDATION_ERROR");
  const required=["id_mencion","fecha","fuente","texto_original","sentimiento_pysentimiento","score_matematico","calidad_dato","severidad"];
  for(const m of payload.mentions){
    if(!m || required.some(k=>!(k in m))) throw new Error("JSON_CONTRACT_ERROR");
    if(!["positivo","negativo","neutro"].includes(m.sentimiento_pysentimiento)) throw new Error("JSON_SENTIMENT_ERROR");
    if(Number(m.score_matematico)<0 || Number(m.score_matematico)>100) throw new Error("JSON_SCORE_ERROR");
  }
  return true;
}
async function importPayload(payload, mode="replace"){
  validateClientPayload(payload);
  if(mode==="replace") await DB.replaceMany("mentions",payload.mentions); else await DB.putMany("mentions",payload.mentions);
  if(Array.isArray(payload.insights)) { if(mode==="replace") await DB.replaceMany("insights",payload.insights); else await DB.putMany("insights",payload.insights); }
  await DB.setMetadata({key:"database",db_version:2,last_import_at:new Date().toISOString(),last_import_count:payload.mentions.length,import_mode:mode,schema_version:payload.metadata?.version_schema||"unknown"});
  state.mentions=await DB.getAll("mentions"); state.insights=await DB.getAll("insights"); state.page=0; render();
}
async function loadData(){
  try{ state.mentions=await DB.getAll("mentions"); state.insights=await DB.getAll("insights"); if(!state.mentions.length){const res=await fetch("data/datos_procesados.json",{cache:"no-store"}); if(!res.ok) throw new Error("JSON_FETCH_ERROR"); await importPayload(await res.json(),"replace"); return;} render(); }
  catch(error){ $("empty-state").classList.remove("hidden"); $("empty-state").innerHTML="<strong>No fue posible cargar los datos.</strong><p>Revisa el servidor local, el JSON y la compatibilidad de IndexedDB.</p>"; console.error(error); }
}
function setupNavigation(){document.querySelectorAll(".nav-item").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active")); document.querySelectorAll(".view").forEach(x=>x.classList.add("hidden")); btn.classList.add("active"); $("view-"+btn.dataset.view).classList.remove("hidden"); $("page-title").textContent=btn.textContent;}));}
function setupFilters(){[["date-from","from"],["date-to","to"]].forEach(([id,key])=>$(id).addEventListener("input",e=>{state.filters[key]=e.target.value;state.page=0;render();})); $("global-search").addEventListener("input",e=>{state.filters.search=e.target.value;state.page=0;clearTimeout(state.searchTimer);state.searchTimer=setTimeout(render,150);}); $("prev-page").addEventListener("click",()=>{if(state.page>0){state.page--;render();}}); $("next-page").addEventListener("click",()=>{if((state.page+1)*state.pageSize<filtered().length){state.page++;render();}}); $("reload-data").addEventListener("click",loadData); $("clear-data").addEventListener("click",async()=>{if(confirm("¿Eliminar los datos locales?")){await DB.replaceMany("mentions",[]);await DB.replaceMany("insights",[]);state.mentions=[];state.insights=[];render();}});}
async function registerOffline(){if("serviceWorker" in navigator){try{await navigator.serviceWorker.register("sw.js",{scope:"./"});}catch(error){console.warn("SERVICE_WORKER_UNAVAILABLE",error);}}}
document.addEventListener("DOMContentLoaded",()=>{setupNavigation();setupFilters();loadData();registerOffline()});
