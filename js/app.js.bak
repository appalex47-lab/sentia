const state = {mentions: [], insights: [], filters:{from:"",to:"",search:""}, page:0, pageSize:50, searchTimer:null};

let API_BASE = "";
const COHERE_FALLBACK_MODELS = [
  {name:"command-a-plus-05-2026",label:"Command A+",description:"Modelo general avanzado para análisis y generación; recomendado como opción por defecto para Sentia.",recommended:true},
  {name:"command-a-reasoning-08-2025",label:"Command A Reasoning",description:"Modelo especializado en razonamiento y tareas complejas.",recommended:false},
  {name:"command-a-03-2025",label:"Command A",description:"Modelo general para generación, análisis e instrucciones.",recommended:false},
  {name:"command-r7b-12-2024",label:"Command R7B",description:"Modelo más ligero, apropiado cuando se priorizan recursos y velocidad.",recommended:false}
];

function apiUrl(path){
  if(!API_BASE) throw new Error("BACKEND_URL_NOT_CONFIGURED");
  return `${API_BASE}${path.startsWith("/")?path:`/${path}`}`;
}
async function apiFetch(path, options={}){
  return fetch(apiUrl(path), {...options, headers:{Accept:"application/json", ...(options.headers||{})}});
}
async function loadApiBase(){
  try{
    const meta=await DB.getMetadata("backend:base_url");
    API_BASE=String(meta?.value||"").replace(/\/$/,"");
  }catch{ API_BASE=""; }
}
async function fetchCohereModels(){
  try{
    if(!API_BASE) return COHERE_FALLBACK_MODELS;
    const r=await apiFetch("/api/cohere/models");
    if(!r.ok) throw new Error("COHERE_MODELS_FAILED");
    const d=await r.json();
    return Array.isArray(d.models)&&d.models.length?d.models:COHERE_FALLBACK_MODELS;
  }catch{ return COHERE_FALLBACK_MODELS; }
}
function renderCohereModelOptions(select, models, selected){
  if(!select)return;
  select.innerHTML=(models||COHERE_FALLBACK_MODELS).map(m=>`<option value="${escapeHtml(m.name)}">${escapeHtml(m.label||m.name)}${m.recommended?" · Recomendado":""}</option>`).join("");
  if(selected && [...select.options].some(o=>o.value===selected)) select.value=selected;
}
function cohereModelDescription(name, models){
  const m=(models||COHERE_FALLBACK_MODELS).find(x=>x.name===name);
  return m?.description||"Modelo de Cohere seleccionado para las funciones de IA de Sentia.";
}

function $(id){return document.getElementById(id);}
function filtered(){
  const from=state.filters.from?new Date(`${state.filters.from}T00:00:00`):null;
  const to=state.filters.to?new Date(`${state.filters.to}T23:59:59.999`):null;
  const q=(state.filters.search||'').trim().toLowerCase();
  return state.mentions.filter(m=>{
    const d=new Date(m.fecha||0);
    if(from && d<from)return false;
    if(to && d>to)return false;
    if(q){
      const hay=[m.texto_original,m.texto_limpio,m.categoria,m.subcategoria,m.fuente,m.entidad_detectada,m.sentimiento_pysentimiento,m.severidad].filter(Boolean).join(' ').toLowerCase();
      if(!hay.includes(q))return false;
    }
    return true;
  });
}
function escapeSvg(value){return escapeHtml(value);}
function renderSentimentChart(rows){
  const box=$('sentiment-chart'), fallback=$('chart-fallback');
  if(!box)return;
  if(!rows.length){box.innerHTML='<p class="muted">No hay datos para mostrar.</p>';fallback?.classList.add('hidden');return;}
  try{
    const groups={};
    rows.forEach(m=>{const day=String(m.fecha||'').slice(0,10)||'Sin fecha';(groups[day]??={positivo:0,negativo:0,neutro:0});const s=m.sentimiento_pysentimiento;if(groups[day][s]!==undefined)groups[day][s]++;});
    const days=Object.keys(groups).sort();
    const W=760,H=280,L=42,R=16,T=18,B=40;
    const innerW=Math.max(1,W-L-R),innerH=H-T-B;
    const max=Math.max(1,...days.map(d=>Math.max(groups[d].positivo,groups[d].negativo,groups[d].neutro)));
    const x=i=>days.length===1?L+innerW/2:L+(i/(days.length-1))*innerW;
    const y=v=>T+innerH-(v/max)*innerH;
    const grid=[];
    for(let i=0;i<=4;i++){const v=Math.round(max*i/4), yy=y(v);grid.push(`<line class="chart-grid" x1="${L}" y1="${yy}" x2="${W-R}" y2="${yy}"/><text class="chart-label" x="${L-8}" y="${yy+4}" text-anchor="end">${v}</text>`);}
    const series=['positivo','negativo','neutro'];
    const lines=series.map(s=>{const pts=days.map((d,i)=>`${x(i)},${y(groups[d][s])}`).join(' ');return `<polyline class="chart-line chart-${s}" points="${pts}"/>${days.map((d,i)=>`<circle class="chart-${s}" cx="${x(i)}" cy="${y(groups[d][s])}" r="3"/>`).join('')}`;}).join('');
    const labels=days.map((d,i)=>`<text class="chart-label" x="${x(i)}" y="${H-12}" text-anchor="middle">${escapeSvg(d.slice(5))}</text>`).join('');
    box.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Evolución del sentimiento por día">${grid.join('')}${lines}${labels}</svg><div class="chart-legend"><span><i class="legend-dot chart-positivo"></i>Positivo</span><span><i class="legend-dot chart-negativo"></i>Negativo</span><span><i class="legend-dot chart-neutro"></i>Neutro</span></div>`;
    fallback?.classList.add('hidden');
  }catch(error){console.error('CHART_RENDER_ERROR',error);box.innerHTML='';fallback?.classList.remove('hidden');}
}
function render(){
  const rows=filtered();
  const total=rows.length;
  const positive=rows.filter(m=>m.sentimiento_pysentimiento==='positivo').length;
  const negative=rows.filter(m=>m.sentimiento_pysentimiento==='negativo').length;
  const critical=rows.filter(m=>['alta','crítica','critica'].includes(String(m.severidad||'').toLowerCase()) || Number(m.score_matematico)>=80).length;
  const avg=(field,transform=v=>Number(v||0))=>total?rows.reduce((a,m)=>a+transform(m[field]),0)/total:0;
  const friction=rows.map(m=>Number(m.friccion??m.friction_score??m.score_friccion??0));
  const frictionAvg=friction.length?friction.reduce((a,b)=>a+b,0)/friction.length:0;
  const convIds=new Set(rows.map(m=>m.conversation_id).filter(Boolean));
  const set=(id,v)=>{const el=$(id);if(el)el.textContent=v;};
  set('kpi-total',total);set('kpi-positive',positive);set('kpi-negative',negative);set('kpi-critical',critical);set('kpi-score',avg('score_matematico').toFixed(1));
  const qualityMap={alta:1,media:.5,baja:0};
  const q=avg('calidad_dato',v=>{const mapped=qualityMap[String(v||'').toLowerCase()];return mapped!==undefined?mapped:Number(v)||0;});
  set('kpi-quality',`${Math.round(q*100)}%`);set('kpi-conversations',convIds.size||((state.conversations||[]).length&&total?new Set(rows.map(m=>m.id_mencion)).size:0));set('kpi-friction',frictionAvg.toFixed(1));
  const empty=$('empty-state');if(empty){if(!total){empty.textContent='No hay menciones que coincidan con los filtros actuales.';empty.classList.remove('hidden');}else empty.classList.add('hidden');}
  const body=$('mentions-body');
  const start=state.page*state.pageSize, pageRows=rows.slice(start,start+state.pageSize);
  if(body)body.innerHTML=pageRows.map(m=>`<tr><td>${escapeHtml(new Date(m.fecha||0).toLocaleString('es-MX'))}</td><td>${escapeHtml(m.texto_original||'')}</td><td><span class="badge">${escapeHtml(m.sentimiento_pysentimiento||'')}</span></td><td>${escapeHtml(m.categoria||'')}</td><td>${Number(m.score_matematico??0).toFixed(1)}</td><td>${escapeHtml(m.severidad||'')}</td><td>${escapeHtml(m.calidad_dato||'')}</td></tr>`).join('');
  set('mentions-count',`${rows.length} menciones`);set('page-status',`${total?start+1:0}-${Math.min(start+pageRows.length,total)} de ${total}`);
  const prev=$('prev-page'),next=$('next-page');if(prev)prev.disabled=state.page<=0;if(next)next.disabled=start+pageRows.length>=total;
  const insight=$('insight-content');if(insight){const latest=(state.insights||[])[0];insight.textContent=latest?(latest.texto||latest.insight||latest.resumen||JSON.stringify(latest)):'Sin insight disponible.';}
  const feed=$('critical-feed');if(feed){const crit=rows.filter(m=>['alta','crítica','critica'].includes(String(m.severidad||'').toLowerCase())||Number(m.score_matematico)>=80).sort((a,b)=>Number(b.score_matematico||0)-Number(a.score_matematico||0)).slice(0,8);feed.innerHTML=crit.length?crit.map(m=>`<article class="critical-item"><strong>${escapeHtml(m.severidad||'Crítica')} · ${Number(m.score_matematico||0).toFixed(0)}</strong><p>${escapeHtml(m.texto_original||'')}</p></article>`).join(''):'<p class="muted">No hay menciones críticas con los filtros actuales.</p>';}
  const insights=$('insights-list');if(insights){insights.innerHTML=(state.insights||[]).length?(state.insights||[]).map(i=>`<article class="insight"><strong>${escapeHtml(i.titulo||i.title||'Insight')}</strong><p>${escapeHtml(i.texto||i.insight||i.resumen||i.descripcion||'')}</p></article>`).join(''):'<p class="muted">Sin insights disponibles.</p>';}
  renderSentimentChart(rows);
}

const INTEGRATIONS = [
  {id:"meta",name:"Meta / Facebook Pages",kind:"Social",purpose:"Conectar páginas de Facebook y preparar la ingestión de publicaciones, comentarios y métricas permitidas.",auth:"OAuth 2.0",fields:["appId","pageId","redirectUri","scopes"],secrets:["META_APP_SECRET","META_ACCESS_TOKEN"],docs:"https://developers.facebook.com/docs/",connector:true,provider:"meta"},
  {id:"instagram",name:"Instagram",kind:"Social",purpose:"Conectar cuentas profesionales de Instagram mediante las APIs de Meta.",auth:"OAuth 2.0",fields:["appId","instagramAccountId","redirectUri","scopes"],secrets:["INSTAGRAM_ACCESS_TOKEN","META_APP_SECRET"],docs:"https://developers.facebook.com/docs/instagram-platform/",connector:true,provider:"meta"},
  {id:"x",name:"X",kind:"Social",purpose:"Lectura de posts mediante búsqueda reciente, según plan, permisos y límites de X API",auth:"OAuth 2.0 PKCE",fields:["clientId","redirectUri","scopes","query"],secrets:[],docs:"https://developer.x.com/",status:"PREPARED",connector:"x",provider:"x"},
  {id:"tiktok",name:"TikTok",kind:"Social",purpose:"Perfil y videos recientes mediante Display API; comentarios no forman parte de esta ruta",auth:"OAuth 2.0",fields:["clientKey","redirectUri","scopes"],secrets:["TIKTOK_CLIENT_SECRET"],docs:"https://developers.tiktok.com/docs/en/display-api-overview",status:"PREPARED",connector:"tiktok",provider:"tiktok"},
  {id:"youtube",name:"YouTube",kind:"Video / Social",purpose:"Canal, videos y comentarios mediante YouTube Data API",auth:"API key / OAuth 2.0",fields:["projectId","channelId","redirectUri","scopes"],secrets:["YOUTUBE_API_KEY / GOOGLE_CLIENT_SECRET"],docs:"https://developers.google.com/youtube/v3/docs",status:"PREPARED",connector:"youtube",provider:"youtube"},
  {id:"linkedin",name:"LinkedIn",kind:"Social / Professional",purpose:"Posts y comentarios de organizaciones según permisos aprobados",auth:"OAuth 2.0",fields:["clientId","organizationId","redirectUri","scopes"],secrets:["LINKEDIN_CLIENT_SECRET"],docs:"https://learn.microsoft.com/en-us/linkedin/marketing/",status:"PREPARED",connector:"linkedin",provider:"linkedin"},
  {id:"ga4",name:"Google Analytics 4",kind:"Analytics",purpose:"Métricas de adquisición y comportamiento como fuente complementaria",auth:"OAuth 2.0",fields:["clientId","projectId","propertyId","redirectUri","scopes"],secrets:["GOOGLE_CLIENT_SECRET"],docs:"https://developers.google.com/analytics",status:"PREPARED",connector:"ga4",provider:"ga4"},
  {id:"cohere",name:"Cohere",kind:"IA",purpose:"Insights generativos y resumen de menciones",auth:"Backend HTTPS + API key",fields:["model"],secrets:["COHERE_API_KEY"],docs:"https://docs.cohere.com/",status:"PREPARED"},
  {id:"custom",name:"Conector personalizado",kind:"REST / JSON",purpose:"Integrar una API adicional con el contrato normalizado de Sentia",auth:"Configurable",fields:["baseUrl","name","authType","scopes"],secrets:["CUSTOM_SECRET"],docs:"docs/INTEGRATIONS_GUIDE.md",status:"ARCHITECTURE"}
];
const FIELD_META = {
  appId:["App ID","Identificador público de la aplicación"], pageId:["Page ID","ID de la página que quieres analizar"], instagramAccountId:["Instagram Account ID","ID de la cuenta profesional"], redirectUri:["Redirect URI","URL de retorno registrada en el proveedor"], scopes:["Permisos / scopes","Permisos que el conector solicitará"], clientId:["Client ID","Identificador público OAuth"], clientKey:["Client Key","Clave pública de la aplicación"], projectId:["Project ID","Proyecto del proveedor"], channelId:["Channel ID","Canal de YouTube a consultar"], organizationId:["Organization ID","Organización de LinkedIn"], query:["Consulta X","Búsqueda reciente en X; por ejemplo: marca lang:es"], propertyId:["GA4 Property ID","ID numérico de la propiedad GA4"], model:["Modelo Cohere","Modelo que usará el conector"], baseUrl:["Base URL","URL base del servicio"], name:["Nombre","Nombre interno del conector"], authType:["Tipo de autenticación","OAuth, API key, Bearer, etc."]
};
function integrationCard(i){
  const action=i.connector ? `<button type="button" class="integration-config" data-integration="${escapeHtml(i.id)}">Configurar y conectar</button>` : `<button type="button" class="integration-config" data-integration="${escapeHtml(i.id)}">Configurar</button>`;
  const syncAction=(i.provider && ["x","tiktok","youtube","linkedin"].includes(i.provider))?`<button type="button" class="integration-sync outline" data-sync-provider="${escapeHtml(i.provider)}">Sincronizar</button>`:"";
  return `<article class="integration-card"><div class="integration-top"><div><span class="eyebrow">${escapeHtml(i.kind)}</span><h4>${escapeHtml(i.name)}</h4></div><span class="status-badge status-${String(i.status||"CATALOG").toLowerCase()}">${escapeHtml(i.status||"CATALOG")}</span></div><p>${escapeHtml(i.purpose)}</p><dl><dt>Autenticación</dt><dd>${escapeHtml(i.auth)}</dd><dt>Campos públicos</dt><dd>${escapeHtml(i.fields.map(f=>FIELD_META[f]?.[0]||f).join(", "))}</dd><dt>Secretos</dt><dd><code>${escapeHtml(i.secrets.join(" / ")||"No requerido en PKCE")}</code></dd></dl><div class="integration-actions"><a class="button-link" href="${escapeHtml(i.docs)}" target="_blank" rel="noopener">Documentación oficial</a>${action}${syncAction}</div><small class="muted">Los campos públicos se guardan localmente. Los secretos y tokens permanecen fuera del navegador.</small></article>`;
}
async function renderIntegrations(){
  if(!sessionStorage.getItem("sentia_maintenance_0_3_29")){try{await runOperationalMaintenance();sessionStorage.setItem("sentia_maintenance_0_3_29","1");}catch(e){}}
  const grid=$("integrations-grid"); if(!grid)return;
  const configs=await DB.getAll("integrations").catch(()=>[]); const byId=Object.fromEntries(configs.map(x=>[x.id,x]));
  const render=(filter="all")=>{grid.innerHTML=INTEGRATIONS.filter(i=>filter==="all"||i.kind===filter).map(i=>{const c=byId[i.id];return integrationCard(c?{...i,status:c.enabled?"CONFIGURED":(i.status||"CATALOG")}:i);}).join("");grid.querySelectorAll(".integration-config").forEach(btn=>btn.addEventListener("click",()=>configureIntegration(btn.dataset.integration)));grid.querySelectorAll(".integration-sync").forEach(btn=>btn.addEventListener("click",()=>syncProvider(btn.dataset.syncProvider,btn)));};
  document.querySelectorAll(".integration-filter").forEach(btn=>btn.onclick=()=>{document.querySelectorAll(".integration-filter").forEach(x=>x.classList.remove("active"));btn.classList.add("active");render(btn.dataset.integrationFilter||"all")});
  render(document.querySelector(".integration-filter.active")?.dataset.integrationFilter||"all");
  const configured=configs.filter(x=>x.enabled).length; $("integration-summary").textContent=`${configured} conexión(es) configurada(s) · ${INTEGRATIONS.length} servicio(s) disponibles.`; const hub=$("connection-hub-summary"); if(hub)hub.textContent=`${configured} configurada(s) · ${INTEGRATIONS.length} disponibles`;
}
async function syncProvider(provider, button){
  if(button)button.disabled=true;
  const summary=$("sync-summary"); if(summary)summary.textContent=`Sincronizando ${provider}…`;
  try{
    const cfg=await DB.getIntegration(provider).catch(()=>null);
    const values=cfg?.values||{};
    const body={providers:[provider],x_query:values.query||"",youtube_channel_id:values.channelId||"",linkedin_organization_id:values.organizationId||""};
    const r=await apiFetch("/api/sync/all",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json(); if(!r.ok)throw new Error(d.error||"SYNC_FAILED");
    const imported=await importPayload(d.payload,"append");
    if(d.run) await DB.saveSyncRun(d.run);
    for(const item of (d.providers||[])) {
      await DB.saveSyncState({provider:item.provider,status:item.ok?"awaiting_persistence":"error",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:item.error||"",last_sync_at:null,run_id:d.run?.run_id||""});
      if(item.ok) {
        const providerRows=(d.payload?.mentions||[]).filter(m=>m?.fuente===item.provider);
        const contentKeys=providerRows.map(m=>String(m?.id_mencion||m?.hash_mencion||"")).filter(Boolean);
        await DB.saveSyncManifest({manifest_id:`${d.run?.run_id||"manual"}:${item.provider}`,run_id:d.run?.run_id||"",provider:item.provider,source_count:Number(item.source_count||0),duplicate_count:Number(item.duplicate_count||0),received_count:providerRows.length,persisted_count:providerRows.length,content_keys:contentKeys,persisted_at:Date.now(),mode:"append"});
        const confirmed=await confirmSyncPersistence(item.provider,d.run?.run_id||"",providerRows.length,contentKeys);
        await DB.saveSyncState({provider:item.provider,status:"success",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:"",last_sync_at:new Date().toISOString(),run_id:d.run?.run_id||""});
      }
    }
    const item=(d.providers||[]).find(x=>x.provider===provider); if(summary)summary.textContent=item?.ok?`Última sincronización ${provider}: ${item.source_count||0} registro(s), ${item.duplicate_count||0} duplicado(s) evitado(s).`:`No se pudo sincronizar ${provider}: ${item?.error||"error"}`;
  }catch(e){if(summary)summary.textContent=`No se pudo sincronizar ${provider}: ${e.message}. Verifica el backend seguro.`;}
  finally{if(button)button.disabled=false;}
}
async function runOperationalMaintenance(){
  const summary=$("sync-summary");
  const policy=await DB.getMetadata("sync_retention_policy").catch(()=>null);
  const local=await DB.cleanupOperationalData(policy?.value||{});
  let remote={skipped:true};
  try{ const r=await apiFetch("/api/maintenance/cleanup",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({dry_run:false,policy:policy?.value||{}})}); remote=await r.json(); if(!r.ok)throw new Error(remote.error||"MAINTENANCE_FAILED"); }catch(e){ remote={skipped:false,error:e.message}; }
  if(summary)summary.textContent=`Mantenimiento: ${local.sync_runs.deleted+local.sync_manifests.deleted+local.sync_repairs.deleted} registros operativos locales depurados. Los datos de menciones, conversaciones y conocimiento no se tocaron.${remote.error?" Backend seguro no disponible; se limpió sólo IndexedDB.":""}`;
  return {local,remote};
}

async function refreshSyncObservability(){
  const health=$("sync-health"), history=$("sync-history"); if(!health&&!history)return;
  try{
    const scheduler=await getSyncScheduler();
    const interval=Math.max(5,Number(scheduler.interval_minutes||30));
    const [statusRes,runsRes,healthRes]=await Promise.all([apiFetch("/api/sync/status"),apiFetch("/api/sync/runs?limit=10"),apiFetch(`/api/sync/health?interval=${interval}&providers=x,tiktok,youtube,linkedin`),apiFetch(`/api/sync/alerts?interval=${interval}&providers=x,tiktok,youtube,linkedin`)]);
    const status=await statusRes.json(), runs=await runsRes.json(), healthData=await healthRes.json(), alertsData=await alertsRes.json();
    if(health) health.innerHTML=`<div class="sync-health-overall"><strong>Salud de sincronización: ${escapeHtml(healthData.overall||"never")}</strong><small>Política de frescura: ${interval} min</small></div>${(alertsData.alerts||[]).length?`<div class="sync-alerts"><strong>Alertas accionables</strong>${alertsData.alerts.map(a=>`<div class="sync-alert sync-alert-${escapeHtml(a.severity)}"><span><strong>${escapeHtml(a.provider.toUpperCase())}</strong> · ${escapeHtml(a.message)}</span><button type="button" class="outline sync-alert-action" data-provider="${escapeHtml(a.provider)}">${a.action==="retry"?"Reintentar":"Sincronizar"}</button></div>`).join("")}</div>`:""}<div class="sync-health-grid">${["x","tiktok","youtube","linkedin"].map(p=>{const x=status.providers?.[p]||{}, h=healthData.providers?.[p]||{}; return `<div class="sync-health-item"><strong>${escapeHtml(p.toUpperCase())}</strong><div class="sync-${escapeHtml(h.status||"never")}">${escapeHtml(h.status||"never")}</div><small>${Number(x.source_count||0)} nuevos · ${Number(x.duplicate_count||0)} duplicados evitados</small>${h.age_seconds!=null?`<small>Antigüedad: ${Math.round(Number(h.age_seconds)/60)} min</small>`:"<small>Sin sincronización exitosa registrada</small>"}</div>`}).join("")}</div>`;
    health?.querySelectorAll(".sync-alert-action").forEach(btn=>btn.addEventListener("click",async()=>{btn.disabled=true;try{await syncAllProviders();}finally{btn.disabled=false;}}));
    if(history){const items=runs.runs||[]; history.innerHTML=`<h4>Historial de sincronizaciones</h4>${items.length?`<table><thead><tr><th>Fecha</th><th>Estado</th><th>Fuentes</th><th>Registros</th><th>Duplicados</th><th>Reintentos</th><th>Duración</th></tr></thead><tbody>${items.map(r=>`<tr><td>${escapeHtml(new Date(Number(r.started_at)*1000).toLocaleString())}</td><td class="sync-${escapeHtml(r.status)}">${escapeHtml(r.status)}</td><td>${escapeHtml((r.requested_providers||[]).join(", "))}</td><td>${Number(r.source_count||0)}</td><td>${Number(r.duplicate_count||0)}</td><td>${Number(r.retry_count||0)}</td><td>${Number(r.duration_ms||0)} ms</td></tr>`).join("")}</tbody></table>`:`<p class="muted">Todavía no hay ejecuciones registradas.</p>`}`;}
  }catch(e){if(health)health.innerHTML=`<p class="muted">No se pudo consultar el estado del bridge: ${escapeHtml(e.message)}</p>`;}
}

async function reconcileSyncState(){
  const summary=$("sync-summary");
  const manifests=await DB.getSyncManifests(50).catch(()=>[]);
  const mentions=await DB.getAll("mentions").catch(()=>[]);
  const manifestsWithDb=manifests.map(m=>({...m,db_content_keys:mentions.filter(x=>x?.fuente===m.provider).map(x=>String(x?.id_mencion||x?.hash_mencion||"")).filter(Boolean)}));
  const r=await apiFetch("/api/sync/reconcile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({providers:["x","tiktok","youtube","linkedin"],local_manifests:manifestsWithDb})});
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||"SYNC_RECONCILE_FAILED");
  if(d.ok){ if(summary)summary.textContent="Consistencia correcta: no se detectaron checkpoints pendientes o inconsistencias."; }
  else {
    const details=(d.issues||[]).map(x=>`${x.provider}: ${x.code}`).join(" · ");
    if(summary)summary.textContent=`Revisión de consistencia: ${d.issue_count||0} incidencia(s). ${details}`;
  }
  await refreshSyncObservability();
}

async function repairSyncInconsistencies(){
  const summary=$("sync-summary");
  const manifests=await DB.getSyncManifests(50).catch(()=>[]);
  const mentions=await DB.getAll("mentions").catch(()=>[]);
  const manifestsWithDb=manifests.map(m=>({...m,db_content_keys:mentions.filter(x=>x?.fuente===m.provider).map(x=>String(x?.id_mencion||x?.hash_mencion||"")).filter(Boolean)}));
  const check=await apiFetch("/api/sync/reconcile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({providers:["x","tiktok","youtube","linkedin"],local_manifests:manifestsWithDb})});
  const report=await check.json();
  if(!check.ok) throw new Error(report.error||"SYNC_RECONCILE_FAILED");
  const plan=report.repair_plan||{providers:[]};
  const targets=(plan.providers||[]).filter(x=>(x.actions||[]).includes("resync_provider"));
  if(!targets.length){
    if(summary)summary.textContent=report.ok?"No hay inconsistencias reparables.":`Hay ${plan.requires_manual_review?.length||0} fuente(s) que requieren revisión manual; no se ejecutó ninguna reparación destructiva.`;
    return;
  }
  let repaired=0, failed=0, manual=plan.requires_manual_review?.length||0;
  for(const target of targets){
    const provider=target.provider;
    const repairId=`repair-${provider}-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
    const started=Date.now();
    await DB.saveSyncRepair({repair_id:repairId,provider,status:"running",reason_codes:target.codes||[],created_at:started});
    try{
      const cfg=await DB.getIntegration(provider).catch(()=>null), values=cfg?.values||{};
      const body={providers:[provider],x_query:values.query||"",youtube_channel_id:values.channelId||"",linkedin_organization_id:values.organizationId||""};
      const r=await apiFetch("/api/sync/all",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      const d=await r.json(); if(!r.ok)throw new Error(d.error||"SYNC_REPAIR_FAILED");
      if(d.run) await DB.saveSyncRun(d.run);
      const item=(d.providers||[]).find(x=>x.provider===provider);
      if(!item?.ok)throw new Error(item?.error||"SYNC_REPAIR_PROVIDER_FAILED");
      const mentions=d.payload?.mentions||[];
      const providerRows=mentions.filter(m=>m?.fuente===provider);
      await DB.saveSyncState({provider,status:"awaiting_persistence",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:"",last_sync_at:null,run_id:d.run?.run_id||""});
      const contentKeys=providerRows.map(m=>String(m?.id_mencion||m?.hash_mencion||"")).filter(Boolean);
      await DB.saveSyncManifest({manifest_id:`${d.run?.run_id||"manual"}:${provider}`,run_id:d.run?.run_id||"",provider,source_count:Number(item.source_count||0),duplicate_count:Number(item.duplicate_count||0),received_count:providerRows.length,persisted_count:providerRows.length,content_keys:contentKeys,persisted_at:Date.now(),mode:"repair-resync"});
      await confirmSyncPersistence(provider,d.run?.run_id||"",providerRows.length,contentKeys);
      await DB.saveSyncState({provider,status:"success",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:"",last_sync_at:new Date().toISOString(),run_id:d.run?.run_id||""});
      await DB.saveSyncRepair({repair_id:repairId,provider,status:"completed",reason_codes:target.codes||[],run_id:d.run?.run_id||"",records:Number(providerRows.length),duration_ms:Date.now()-started,created_at:started,completed_at:Date.now()});
      repaired++;
    }catch(e){
      await DB.saveSyncRepair({repair_id:repairId,provider,status:"failed",reason_codes:target.codes||[],error:String(e.message||e).slice(0,200),duration_ms:Date.now()-started,created_at:started,completed_at:Date.now()});
      failed++;
    }
  }
  if(summary)summary.textContent=`Reparación terminada: ${repaired} fuente(s) reparada(s), ${failed} fallida(s), ${manual} en revisión manual.`;
  await refreshSyncObservability();
}

async function exportSyncDiagnostic(){
  const scheduler=await getSyncScheduler();
  const interval=Math.max(5,Number(scheduler.interval_minutes||30));
  const r=await apiFetch(`/api/sync/diagnostic?interval=${interval}&providers=x,tiktok,youtube,linkedin`);
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||"SYNC_DIAGNOSTIC_FAILED");
  const blob=new Blob([JSON.stringify(d.report,null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob); const a=document.createElement("a");
  a.href=url; a.download=`sentia-sync-diagnostic-${new Date().toISOString().replace(/[:.]/g,"-")}.json`;
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

async function confirmSyncPersistence(provider, runId, persistedCount, contentKeys){
  const r=await apiFetch("/api/sync/confirm-persistence",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({provider,run_id:runId,persisted_count:persistedCount,content_keys:contentKeys})});
  const d=await r.json().catch(()=>({}));
  if(!r.ok || !d.ok) throw new Error(d.error||"SYNC_PERSISTENCE_CONFIRMATION_FAILED");
  return d;
}

async function syncAllProviders(){
  const btn=$("sync-all"); if(btn)btn.disabled=true; const summary=$("sync-summary"); if(summary)summary.textContent="Sincronizando fuentes conectadas…";
  try{
    const configs=await DB.getAll("integrations").catch(()=>[]); const enabled=configs.filter(x=>x.enabled && ["x","tiktok","youtube","linkedin"].includes(x.id));
    const body={providers:enabled.map(x=>x.id),x_query:configs.find(x=>x.id==="x")?.values?.query||"",youtube_channel_id:configs.find(x=>x.id==="youtube")?.values?.channelId||"",linkedin_organization_id:configs.find(x=>x.id==="linkedin")?.values?.organizationId||""};
    if(!body.providers.length){if(summary)summary.textContent="No hay fuentes sociales configuradas para sincronizar.";return;}
    const r=await apiFetch("/api/sync/all",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); const d=await r.json(); if(!r.ok)throw new Error(d.error||"SYNC_FAILED");
    const imported=(d.payload?.mentions||[]).length?await importPayload(d.payload,"append"): {mentions_written:0};
    if(d.run) await DB.saveSyncRun(d.run);
    for(const item of (d.providers||[])) {
      await DB.saveSyncState({provider:item.provider,status:item.ok?"awaiting_persistence":"error",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:item.error||"",last_sync_at:null,run_id:d.run?.run_id||""});
      if(item.ok) {
        const providerRows=(d.payload?.mentions||[]).filter(m=>m?.fuente===item.provider);
        const contentKeys=providerRows.map(m=>String(m?.id_mencion||m?.hash_mencion||"")).filter(Boolean);
        await DB.saveSyncManifest({manifest_id:`${d.run?.run_id||"manual"}:${item.provider}`,run_id:d.run?.run_id||"",provider:item.provider,source_count:Number(item.source_count||0),duplicate_count:Number(item.duplicate_count||0),received_count:providerRows.length,persisted_count:providerRows.length,content_keys:contentKeys,persisted_at:Date.now(),mode:"append"});
        const confirmed=await confirmSyncPersistence(item.provider,d.run?.run_id||"",providerRows.length,contentKeys);
        await DB.saveSyncState({provider:item.provider,status:"success",source_count:item.source_count||0,duplicate_count:item.duplicate_count||0,error:"",last_sync_at:new Date().toISOString(),run_id:d.run?.run_id||""});
      }
    }
    const ok=(d.providers||[]).filter(x=>x.ok).length, failed=(d.providers||[]).filter(x=>!x.ok).length; if(summary)summary.textContent=`Sincronización terminada: ${ok} fuente(s) correctas · ${failed} con incidencia · ${d.payload?.mentions?.length||0} mención(es) procesadas.`;
    await refreshSyncObservability();
  }catch(e){if(summary)summary.textContent=`No se pudo completar la sincronización: ${e.message}. Verifica el backend seguro.`;}
  finally{if(btn)btn.disabled=false;}
}
async function getSyncScheduler(){
  return await DB.getSyncScheduler().catch(()=>null) || {id:"default",enabled:false,interval_minutes:30,next_run_at:0,last_run_at:0,updated_at:null};
}
async function saveSyncScheduler(patch={}){
  const current=await getSyncScheduler();
  const next={...current,...patch,updated_at:new Date().toISOString()};
  await DB.saveSyncScheduler(next);
  return next;
}
async function runScheduledSync(force=false){
  const cfg=await getSyncScheduler();
  if(!cfg.enabled && !force)return false;
  if(!force && Number(cfg.next_run_at||0)>Date.now())return false;
  const configs=await DB.getAll("integrations").catch(()=>[]);
  const providers=configs.filter(x=>x.enabled && ["x","tiktok","youtube","linkedin"].includes(x.id)).map(x=>x.id);
  if(!providers.length){await saveSyncScheduler({next_run_at:0}); return false;}
  await saveSyncScheduler({last_run_at:Date.now(),next_run_at:Date.now()+Math.max(5,Number(cfg.interval_minutes||30))*60*1000});
  await syncAllProviders();
  return true;
}
async function setupSync(){
  $("sync-all")?.addEventListener("click",async()=>{await runScheduledSync(true);});
  $("sync-refresh")?.addEventListener("click",refreshSyncObservability);
  $("sync-reconcile")?.addEventListener("click",async()=>{const b=$("sync-reconcile"); try{b.disabled=true; await reconcileSyncState();}catch(e){const summary=$("sync-summary"); if(summary)summary.textContent=`No se pudo revisar la consistencia: ${e.message}. Verifica el backend seguro.`;}finally{b.disabled=false;}});
  $("sync-repair")?.addEventListener("click",async()=>{const b=$("sync-repair"); try{b.disabled=true; await repairSyncInconsistencies();}catch(e){const summary=$("sync-summary"); if(summary)summary.textContent=`No se pudo reparar la sincronización: ${e.message}. Verifica el backend seguro.`;}finally{b.disabled=false;}});
  $("sync-maintenance")?.addEventListener("click",async()=>{const b=$("sync-maintenance"); try{b.disabled=true; await runOperationalMaintenance();}catch(e){const summary=$("sync-summary"); if(summary)summary.textContent=`No se pudo ejecutar mantenimiento: ${e.message}.`;}finally{b.disabled=false;}});
  $("sync-diagnostic")?.addEventListener("click",async()=>{const b=$("sync-diagnostic"); try{b.disabled=true; await exportSyncDiagnostic();}catch(e){const summary=$("sync-summary"); if(summary)summary.textContent=`No se pudo exportar el diagnóstico: ${e.message}. Verifica el backend seguro.`;}finally{b.disabled=false;}});
  const scheduler=await getSyncScheduler();
  if($("sync-auto"))$("sync-auto").checked=!!scheduler.enabled;
  if($("sync-interval"))$("sync-interval").value=String(scheduler.interval_minutes||30);
  $("sync-auto")?.addEventListener("change",async e=>{
    const enabled=e.target.checked;
    await saveSyncScheduler({enabled,next_run_at:enabled?Date.now()+Math.max(5,Number($("sync-interval")?.value||30))*60*1000:0});
    if($("sync-summary"))$("sync-summary").textContent=enabled?"Sincronización automática activada; se ejecutará mientras Sentia esté abierta.":"Sincronización automática desactivada.";
  });
  $("sync-interval")?.addEventListener("change",async e=>{
    const minutes=Math.max(5,Number(e.target.value||30));
    const current=await getSyncScheduler();
    await saveSyncScheduler({interval_minutes:minutes,next_run_at:current.enabled?Date.now()+minutes*60*1000:0});
  });
  if(!window.__sentiaSyncSchedulerTimer) window.__sentiaSyncSchedulerTimer=setInterval(()=>runScheduledSync(false).catch(()=>{}),60*1000);
  document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")runScheduledSync(false).catch(()=>{});});
  refreshSyncObservability();
}

async function configureIntegration(id){
  const i=INTEGRATIONS.find(x=>x.id===id); if(!i)return;
  const existing=await DB.getIntegration(id).catch(()=>null); const values={...(existing?.values||{})};
  if(i.id==="cohere") return configureCohereIntegration(existing);
  const fieldRows=i.fields.map(key=>{const meta=FIELD_META[key]||[key,"Valor de configuración"]; return `<label class="integration-field"><span>${escapeHtml(meta[0])}</span><input data-config-field="${escapeHtml(key)}" value="${escapeHtml(values[key]||"")}" placeholder="${escapeHtml(meta[1])}"><small>${escapeHtml(meta[1])}</small></label>`;}).join("");
  const secretRows=i.secrets.map(s=>`<li><code>${escapeHtml(s)}</code><span>Debe existir en el entorno seguro de Python.</span></li>`).join("");
  const connectorHelp=i.connector?`<section class="connector-box"><h4>Conector local</h4><p>Sentia abrirá el flujo de conexión a través del backend seguro. Primero valida que el entorno tenga los secretos requeridos.</p><button id="connection-validate" type="button">Validar backend</button><button id="connection-authorize" type="button" disabled>Iniciar OAuth</button></section>`:"";
  const html=`<div class="connection-modal" role="dialog" aria-modal="true" aria-labelledby="connection-title"><div class="connection-panel"><div class="card-header"><div><span class="eyebrow">Centro de Integraciones</span><h3 id="connection-title">Conectar ${escapeHtml(i.name)}</h3></div><button id="connection-close" type="button" aria-label="Cerrar">Cerrar</button></div><p>${escapeHtml(i.purpose)}</p><div class="connection-steps"><strong>1. Completa los campos públicos</strong><span>2. Configura secretos en Python</span><span>3. Valida el entorno</span><span>4. Autoriza cuando el conector esté disponible</span></div><div class="connection-fields">${fieldRows}</div><section class="secret-box"><h4>Secretos requeridos</h4><ul>${secretRows}</ul><p><strong>Importante:</strong> Sentia no solicita ni almacena estos valores en IndexedDB/localStorage.</p></section>${connectorHelp}<div class="integration-actions"><button id="connection-save" type="button">Guardar configuración</button><a class="button-link" href="${escapeHtml(i.docs)}" target="_blank" rel="noopener">Abrir documentación</a><span id="connection-status" class="muted" aria-live="polite"></span></div></div></div>`;
  document.body.insertAdjacentHTML("beforeend",html); const modal=document.querySelector(".connection-modal"); const close=()=>modal?.remove();
  modal.querySelector("#connection-close").addEventListener("click",close);
  const previousFocus=document.activeElement;
  const focusables=()=>Array.from(modal.querySelectorAll("button,a[href],input,select,textarea,[tabindex]:not([tabindex=\"-1\"])")).filter(el=>!el.disabled);
  modal.addEventListener("keydown",event=>{if(event.key==="Escape"){event.preventDefault();close();previousFocus?.focus?.();return;}if(event.key!=="Tab")return;const items=focusables();if(!items.length)return;const first=items[0],last=items[items.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}});
  modal.querySelector("#connection-close").focus();
  modal.querySelector("#connection-save").addEventListener("click",async()=>{const vals={};modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); await DB.saveIntegration({id:i.id,name:i.name,enabled:true,auth:i.auth,values:vals,docs:i.docs,connector:i.provider||null}); modal.querySelector("#connection-status").textContent="Configuración pública guardada. Los secretos siguen fuera del navegador."; await renderIntegrations();});
  if(i.connector && ["x","tiktok","youtube","linkedin"].includes(i.provider)){
    const validate=modal.querySelector("#connection-validate"), auth=modal.querySelector("#connection-authorize"), status=modal.querySelector("#connection-status");
    validate?.addEventListener("click",async()=>{try{const vals={};modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); const r=await apiFetch(`/api/integrations/${i.provider}/config`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(vals)}); const d=await r.json(); if(!r.ok)throw new Error(d.error||"CONFIG_FAILED"); status.textContent=d.missing?.length?`Faltan: ${d.missing.join(", ")}`:"Entorno listo para OAuth."; if(auth)auth.disabled=!!d.missing?.length;}catch(e){status.textContent=`No se pudo validar: ${e.message}`;}});
    auth?.addEventListener("click",async()=>{try{const vals={};modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); await apiFetch(`/api/integrations/${i.provider}/config`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(vals)}); window.open(apiUrl(`/api/integrations/${i.provider}/authorize`),"_blank","noopener,noreferrer");}catch(e){status.textContent=`No se pudo iniciar OAuth: ${e.message}`;}});
    const box=document.createElement("section"); box.className="connector-box"; box.innerHTML=`<h4>Sincronización ${escapeHtml(i.name)}</h4><button id="social-sync" type="button">Sincronizar ahora</button><button id="social-disconnect" type="button">Desconectar</button><span id="social-sync-status" class="muted" aria-live="polite"></span>`; modal.querySelector(".connection-panel").insertBefore(box,modal.querySelector(".integration-actions"));
    box.querySelector("#social-sync").onclick=async()=>{const out=box.querySelector("#social-sync-status");try{let body={};if(i.provider==="x"){body={query:modal.querySelector('[data-config-field="query"]')?.value.trim()||"lang:es -is:retweet"};}else if(i.provider==="youtube"){body={channel_id:modal.querySelector('[data-config-field="channelId"]')?.value.trim()};}else if(i.provider==="linkedin"){body={organization_id:modal.querySelector('[data-config-field="organizationId"]')?.value.trim()};}out.textContent="Sincronizando…";const r=await apiFetch(`/api/integrations/${i.provider}/ingest`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw new Error(d.error||"SYNC_FAILED");if(d.payload)await importPayload(d.payload,"append");out.textContent=`Sincronización completada: ${d.source_count||0} mención(es).`;await renderIntegrations();}catch(e){out.textContent=`No se pudo sincronizar: ${e.message}`;}};
    box.querySelector("#social-disconnect").onclick=async()=>{await apiFetch(`/api/integrations/${i.provider}/disconnect`);await DB.saveIntegration({id:i.id,name:i.name,enabled:false,auth:i.auth,values:{},docs:i.docs,connector:i.provider});box.querySelector("#social-sync-status").textContent="Desconectado.";};
  }
  if(i.connector && ["meta","ga4"].includes(i.provider)){
    modal.querySelector("#connection-validate")?.addEventListener("click",async()=>{
      const status=modal.querySelector("#connection-status"); status.textContent="Guardando configuración pública y validando Python…";
      try{
        const vals={}; modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim());
        const cfg={appId:vals.appId||"",redirectUri:vals.redirectUri||"",scopes:vals.scopes||"",graphVersion:"v26.0",pageId:vals.pageId||"",instagramAccountId:vals.instagramAccountId||""};
        const save=await apiFetch("/api/integrations/meta/config",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(cfg)});
        if(!save.ok) throw new Error("CONFIG_SAVE_FAILED");
        const r=await apiFetch("/api/integrations/meta/status",{headers:{Accept:"application/json"}});
        const data=await r.json(); status.textContent=data.connected?"Meta ya está conectada en Python.":data.ready?"Backend listo para OAuth.":`Faltan secretos: ${(data.missing||[]).join(", ")||"revisa el servicio"}`;
        const auth=modal.querySelector("#connection-authorize"); if(auth)auth.disabled=!data.ready;
        if(data.ready) await loadMetaAccounts(modal);
      }catch(error){status.textContent="No se pudo contactar el backend seguro. Inícialo y vuelve a validar.";}
    });
    modal.querySelector("#connection-authorize")?.addEventListener("click",()=>{window.open(apiUrl("/api/integrations/meta/authorize"),"_blank","noopener,noreferrer");});
    const savedSelection=existing?.values||{};
    if(savedSelection.pageId) setTimeout(()=>loadMetaAccounts(modal),0);
  }
  if(i.id==="ga4") setupGa4Modal(modal, existing);
}
async function setupGa4Modal(modal, existing){
  const status=modal.querySelector("#connection-status");
  const validate=modal.querySelector("#connection-validate"); const auth=modal.querySelector("#connection-authorize");
  const saveConfig=async()=>{const vals={}; modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); await DB.saveIntegration({id:"ga4",name:"Google Analytics 4",enabled:true,auth:"OAuth 2.0",values:vals,docs:"https://developers.google.com/analytics",connector:"ga4"}); const r=await apiFetch("/api/integrations/ga4/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(vals)}); if(!r.ok) throw new Error("GA4_CONFIG_FAILED"); return vals;};
  validate?.addEventListener("click",async()=>{try{await saveConfig(); const r=await apiFetch("/api/integrations/ga4/status"); const d=await r.json(); status.textContent=d.ready?"Entorno GA4 listo para OAuth.":`Faltan secretos: ${(d.missing||[]).join(", ")||"revisa el servicio Python"}`; if(auth)auth.disabled=!d.ready;}catch(e){status.textContent=`No se pudo validar GA4: ${e.message}`;}});
  auth?.addEventListener("click",async()=>{try{await saveConfig(); window.open(apiUrl("/api/integrations/ga4/authorize"),"_blank","noopener,noreferrer"); setTimeout(()=>loadGa4Properties(modal),1200);}catch(e){status.textContent=`No se pudo iniciar OAuth: ${e.message}`;}});
  setTimeout(async()=>{try{const d=await apiFetch("/api/integrations/ga4/status").then(r=>r.json()); if(auth)auth.disabled=!d.ready; if(d.connected) await loadGa4Properties(modal); status.textContent=d.connected?"GA4 conectada.":d.ready?"Backend listo para OAuth.":"Configura y valida el backend seguro.";}catch{status.textContent="Backend seguro no disponible.";}},0);
}
async function loadGa4Properties(modal){
  const panel=modal.querySelector(".connection-panel"); if(!panel)return; let box=modal.querySelector("#ga4-properties-box"); if(!box){box=document.createElement("section"); box.id="ga4-properties-box"; box.className="connector-box"; box.innerHTML='<h4>Propiedades GA4</h4><label class="integration-field"><span>Propiedad</span><select id="ga4-property-select"></select></label><div class="ga4-report-fields"><label class="integration-field"><span>Desde</span><input id="ga4-start" type="date"></label><label class="integration-field"><span>Hasta</span><input id="ga4-end" type="date"></label></div><button id="ga4-sync" type="button">Consultar reporte</button><button id="ga4-disconnect" type="button">Desconectar</button><span id="ga4-status" class="muted" aria-live="polite"></span>'; panel.insertBefore(box,panel.querySelector(".integration-actions"));}
  const out=box.querySelector("#ga4-status"); try{const r=await apiFetch("/api/integrations/ga4/properties"); const d=await r.json(); if(!r.ok)throw new Error(d.error||"GA4_PROPERTIES_FAILED"); const select=box.querySelector("#ga4-property-select"); select.innerHTML=(d.properties||[]).map(p=>`<option value="${escapeHtml(p.property_id)}">${escapeHtml(p.display_name||p.property_id)} · ${escapeHtml(p.account_name||"")}</option>`).join(""); const current=(await DB.getIntegration("ga4").catch(()=>null))?.values?.propertyId||""; if(current && [...select.options].some(o=>o.value===current))select.value=current; const today=new Date(); const prior=new Date(today); prior.setDate(today.getDate()-29); box.querySelector("#ga4-end").value=today.toISOString().slice(0,10); box.querySelector("#ga4-start").value=prior.toISOString().slice(0,10); out.textContent=`${d.properties?.length||0} propiedad(es) disponibles.`;
    box.querySelector("#ga4-sync").onclick=async()=>{try{const vals={}; modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); vals.propertyId=select.value; await DB.saveIntegration({id:"ga4",name:"Google Analytics 4",enabled:true,auth:"OAuth 2.0",values:vals,docs:"https://developers.google.com/analytics",connector:"ga4"}); await apiFetch("/api/integrations/ga4/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(vals)}); out.textContent="Consultando GA4…"; const rr=await apiFetch("/api/integrations/ga4/report",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({property_id:select.value,start_date:box.querySelector("#ga4-start").value,end_date:box.querySelector("#ga4-end").value,dimensions:["date"],metrics:["activeUsers","sessions","eventCount"]})}); const data=await rr.json(); if(!rr.ok)throw new Error(data.error||"GA4_REPORT_FAILED"); const report={...data.report,report_id:`ga4:${select.value}:${data.report.start_date}:${data.report.end_date}`,synced_at:data.synced_at}; await DB.saveAnalyticsReport(report); out.textContent=`Reporte guardado: ${report.row_count} fila(s).`; }catch(e){out.textContent=`No se pudo consultar GA4: ${e.message}`;}};
    box.querySelector("#ga4-disconnect").onclick=async()=>{await apiFetch("/api/integrations/ga4/disconnect"); await DB.saveIntegration({id:"ga4",name:"Google Analytics 4",enabled:false,auth:"OAuth 2.0",values:{},docs:"https://developers.google.com/analytics",connector:"ga4"}); out.textContent="GA4 desconectada.";};
  }catch(e){out.textContent=`No se pudieron cargar las propiedades: ${e.message}`;}
}
async function loadMetaAccounts(modal){
  const status=modal.querySelector("#connection-status");
  try{
    const r=await apiFetch("/api/integrations/meta/pages",{headers:{Accept:"application/json"}});
    if(!r.ok) return;
    const data=await r.json();
    let box=modal.querySelector("#meta-account-picker");
    if(!box){ box=document.createElement("section"); box.id="meta-account-picker"; box.className="connector-box"; box.innerHTML='<h4>2. Selecciona la cuenta</h4><label class="integration-field"><span>Página de Facebook</span><select id="meta-page-select"></select></label><div id="meta-ig-choice"></div><div id="meta-lifecycle" class="muted" aria-live="polite"></div><button id="meta-save-selection" type="button">Guardar selección</button><button id="meta-sync" type="button" disabled>Sincronizar ahora</button><button id="meta-disconnect" type="button">Desconectar</button><span id="meta-sync-status" class="muted" aria-live="polite"></span>'; modal.querySelector(".connection-panel").insertBefore(box,modal.querySelector(".integration-actions")); }
    const select=box.querySelector("#meta-page-select"); const current=(await apiFetch("/api/integrations/meta/selection").then(x=>x.json()).catch(()=>({}))).page_id||"";
    select.innerHTML=data.pages.map(p=>`<option value="${escapeHtml(p.id)}" data-ig="${escapeHtml(p.instagram_business_account?.id||"")}">${escapeHtml(p.name||p.id)}</option>`).join(""); const lifecycle=box.querySelector("#meta-lifecycle"); try { const st=await apiFetch("/api/integrations/meta/status").then(x=>x.json()); const exp=st.token_expires_at?new Date(st.token_expires_at*1000).toLocaleString():"no informado"; lifecycle.textContent=st.connected?`Conectada · expiración del token: ${exp}`:"No conectada"; } catch { lifecycle.textContent="No se pudo consultar el estado del conector Python."; }
    if(current && [...select.options].some(o=>o.value===current)) select.value=current;
    const renderIg=()=>{const opt=select.selectedOptions[0]; const ig=opt?.dataset.ig||""; box.querySelector("#meta-ig-choice").innerHTML=ig?`<p>Instagram profesional detectado: <code>${escapeHtml(ig)}</code></p>`:'<p class="muted">No se detectó una cuenta profesional de Instagram vinculada a esta página.</p>';}; renderIg(); select.onchange=renderIg;
    box.querySelector("#meta-save-selection").onclick=async()=>{const opt=select.selectedOptions[0]; const vals={}; modal.querySelectorAll("[data-config-field]").forEach(input=>vals[input.dataset.configField]=input.value.trim()); vals.pageId=select.value; vals.instagramAccountId=opt?.dataset.ig||vals.instagramAccountId||""; await DB.saveIntegration({id:"meta",name:"Meta / Facebook Pages",enabled:true,auth:"OAuth 2.0",values:vals,docs:"https://developers.facebook.com/docs/",connector:"meta"}); await apiFetch("/api/integrations/meta/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({appId:vals.appId,redirectUri:vals.redirectUri,scopes:vals.scopes,graphVersion:"v26.0",pageId:vals.pageId,instagramAccountId:vals.instagramAccountId})}); box.querySelector("#meta-sync").disabled=false; box.querySelector("#meta-sync-status").textContent="Selección guardada.";};
    box.querySelector("#meta-disconnect").onclick=async()=>{await apiFetch("/api/integrations/meta/disconnect"); await DB.saveIntegration({id:"meta",name:"Meta / Facebook Pages",enabled:false,auth:"OAuth 2.0",values:{},docs:"https://developers.facebook.com/docs/",connector:"meta"}); box.querySelector("#meta-sync").disabled=true; box.querySelector("#meta-sync-status").textContent="Meta desconectada. Deberás autorizar nuevamente para sincronizar.";}; box.querySelector("#meta-sync").onclick=async()=>{const out=box.querySelector("#meta-sync-status"); out.textContent="Sincronizando y procesando…"; try{const r=await apiFetch("/api/integrations/meta/ingest"); const data=await r.json(); if(!r.ok) throw new Error(data.error||"META_INGEST_FAILED"); await importPayload(data.payload,"append"); await DB.setMetadata({key:"sync:meta",provider:"meta",at:data.synced_at,source_count:data.source_count,page_id:data.page?.id||"",instagram_account_id:data.instagram_account_id||""}); out.textContent=`Sincronización completada: ${data.source_count} fuente(s).`; closeModalAfterSync(modal);}catch(e){out.textContent=`No se pudo sincronizar: ${e.message}`;}};
    if(status) status.textContent="Cuentas disponibles cargadas.";
  }catch(e){ if(status) status.textContent="No se pudieron cargar las cuentas. Verifica la conexión OAuth."; }
}
function closeModalAfterSync(modal){setTimeout(()=>modal?.remove(),700);}

async function configureCohereIntegration(existing){
  const values={...(existing?.values||{})}; const models=await fetchCohereModels();
  const html=`<div class="connection-modal" role="dialog" aria-modal="true" aria-labelledby="cohere-title"><div class="connection-panel"><div class="card-header"><div><span class="eyebrow">Centro de Integraciones · IA</span><h3 id="cohere-title">Configurar Cohere</h3></div><button id="connection-close" type="button">Cerrar</button></div><p>Cohere aporta interpretación generativa y apoyo al análisis. Los KPIs determinísticos de Sentia no dependen de la IA.</p><div class="connection-fields"><label class="integration-field"><span>Modelo de Cohere</span><select id="cohere-center-model"></select><small>Selecciona el modelo que utilizará Sentia.</small></label><section class="model-description" aria-live="polite"><strong>Sobre este modelo</strong><p id="cohere-model-description"></p></section><label class="integration-field"><span>API Key de Cohere</span><input id="cohere-center-key" type="password" autocomplete="off" placeholder="Pega tu API key de Cohere"><small>La clave se envía exclusivamente al backend seguro; no se guarda en IndexedDB/localStorage.</small></label></div><section class="secret-box"><h4>Seguridad</h4><p>La clave permanece en el backend. El navegador solo conserva el modelo seleccionado.</p></section><div class="integration-actions"><button id="cohere-center-save" type="button">Guardar y probar</button><button id="cohere-center-disconnect" type="button" class="outline">Desconectar</button><a class="button-link" href="https://docs.cohere.com/v2/docs/playground-overview" target="_blank" rel="noopener">Ver modelos de Cohere</a><span id="cohere-center-status" class="muted" aria-live="polite"></span></div></div></div>`;
  document.body.insertAdjacentHTML("beforeend",html); const modal=document.querySelector(".connection-modal"); modal.querySelector("#connection-close").onclick=()=>modal.remove();
  const select=modal.querySelector("#cohere-center-model"); renderCohereModelOptions(select,models,values.model||""); const desc=modal.querySelector("#cohere-model-description"); const update=()=>desc.textContent=cohereModelDescription(select.value,models); update(); select.onchange=update;
  modal.querySelector("#cohere-center-save").onclick=async()=>{const status=modal.querySelector("#cohere-center-status"), apiKey=modal.querySelector("#cohere-center-key").value.trim(), model=select.value; if(!apiKey){status.textContent="Pega la API key de Cohere.";return;} try{const r=await apiFetch("/api/cohere/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({apiKey,model})}); const d=await r.json(); if(!r.ok)throw new Error(d.message||d.error||"COHERE_CONFIG_FAILED"); modal.querySelector("#cohere-center-key").value=""; await DB.saveIntegration({id:"cohere",name:"Cohere",enabled:true,auth:"Backend seguro + API key",values:{model:d.model},docs:"https://docs.cohere.com/",connector:"cohere"}); status.textContent=`Cohere conectado · ${d.model}. La API key permanece en el backend.`; await renderIntegrations();}catch(e){status.textContent=e.message==="BACKEND_URL_NOT_CONFIGURED"?"Configura primero la URL del backend seguro en Configuración.":`No se pudo configurar Cohere: ${e.message}`;}};
  modal.querySelector("#cohere-center-disconnect").onclick=async()=>{try{await apiFetch("/api/cohere/disconnect");}catch{} await DB.saveIntegration({id:"cohere",name:"Cohere",enabled:false,auth:"Backend seguro + API key",values:{},docs:"https://docs.cohere.com/",connector:"cohere"}); modal.querySelector("#cohere-center-status").textContent="Cohere desconectado.";};
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
async function importPayload(payload, mode="replace", options={}){
  validateClientPayload(payload);
  const isDemo=Boolean(options.demo);
  const mark=(row)=>isDemo?({...row,es_dato_ejemplo:true}):row;
  const mentions=payload.mentions.map(mark);
  const insights=(payload.insights||[]).map(mark);
  const conversations=(payload.conversations||[]).map(mark);
  const knowledge=(payload.knowledge||[]).map(x=>mark({...x,knowledge_id:isDemo?`demo:${x.knowledge_id||`${x.type}:${x.canonical_name}`}`:(x.knowledge_id||`${x.type}:${x.canonical_name}`)}));
  if(mode==="replace") await DB.replaceMany("mentions",mentions); else await DB.putMany("mentions",mentions);
  if(Array.isArray(payload.insights)) { if(mode==="replace") await DB.replaceMany("insights",insights); else await DB.putMany("insights",insights); }
  if(Array.isArray(payload.conversations)) { if(mode==="replace") await DB.replaceMany("conversations",conversations); else await DB.putMany("conversations",conversations); }
  if(Array.isArray(payload.knowledge)) { if(mode==="replace") await DB.replaceMany("knowledge_entities",knowledge); else await DB.putMany("knowledge_entities",knowledge); }
  await DB.setMetadata({key:"database",db_version:2,last_import_at:new Date().toISOString(),last_import_count:mentions.length,import_mode:mode,schema_version:payload.metadata?.version_schema||payload.metadata?.schema_version||"unknown"});
  state.mentions=await DB.getAll("mentions"); state.insights=await DB.getAll("insights"); state.conversations=await DB.getAll("conversations"); state.knowledge=await DB.getKnowledge(); state.page=0; render();
  return {mentions_written: mentions.length, insights_written: insights.length, conversations_written: conversations.length, knowledge_written: knowledge.length};
}
async function importExampleData(){
  const status=$("demo-status"); if(!status)return;
  const btn=$("demo-import"); if(btn)btn.disabled=true;
  status.textContent="Cargando el conjunto de ejemplos…";
  try{
    const res=await fetch("data/datos_ejemplo.json",{cache:"no-store"});
    if(!res.ok) throw new Error("DEMO_FILE_NOT_FOUND");
    const payload=await res.json();
    await importPayload(payload,"append",{demo:true});
    await DB.setMetadata({key:"demo_dataset",loaded:true,loaded_at:new Date().toISOString(),mention_count:payload.mentions.length,conversation_count:(payload.conversations||[]).length,knowledge_count:(payload.knowledge||[]).length,insight_count:(payload.insights||[]).length});
    status.textContent=`Ejemplos cargados: ${payload.mentions.length} menciones · ${(payload.conversations||[]).length} conversaciones · ${(payload.knowledge||[]).length} conocimientos · ${(payload.insights||[]).length} insights.`;
  }catch(e){status.textContent=`No se pudieron cargar los datos de ejemplo: ${e.message}`;}
  finally{if(btn)btn.disabled=false;}
}
async function deleteExampleData(){
  const status=$("demo-status"); if(!status)return;
  if(!confirm("¿Borrar únicamente los datos de ejemplo? Tus datos reales, conexiones y configuraciones no se eliminarán."))return;
  const btn=$("demo-delete"); if(btn)btn.disabled=true;
  status.textContent="Borrando únicamente datos marcados como ejemplo…";
  try{
    const stores=["mentions","insights","conversations","knowledge_entities"];
    const counts={};
    for(const store of stores) counts[store]=await DB.deleteWhere(store,row=>row?.es_dato_ejemplo===true);
    await DB.setMetadata({key:"demo_dataset",loaded:false,deleted_at:new Date().toISOString(),deleted_counts:counts});
    state.mentions=await DB.getAll("mentions"); state.insights=await DB.getAll("insights"); state.conversations=await DB.getAll("conversations"); state.knowledge=await DB.getKnowledge(); state.page=0; render();
    status.textContent=`Datos de ejemplo eliminados: ${Object.values(counts).reduce((a,b)=>a+b,0)} registros. Los datos reales permanecen intactos.`;
  }catch(e){status.textContent=`No se pudieron borrar los datos de ejemplo: ${e.message}`;}
  finally{if(btn)btn.disabled=false;}
}
async function loadData(){
  try{ state.mentions=await DB.getAll("mentions"); state.insights=await DB.getAll("insights"); state.conversations=await DB.getAll("conversations"); state.knowledge=await DB.getKnowledge(); if(!state.mentions.length){const res=await fetch("data/datos_procesados.json",{cache:"no-store"}); if(!res.ok) throw new Error("JSON_FETCH_ERROR"); await importPayload(await res.json(),"replace"); return;} render(); }
  catch(error){ $("empty-state").classList.remove("hidden"); $("empty-state").innerHTML="<strong>No fue posible cargar los datos.</strong><p>Revisa el servidor local, el JSON y la compatibilidad de IndexedDB.</p>"; console.error(error); }
}
function setupConfiguration(){
  const input=$("backend-base-url"), save=$("backend-save"), test=$("backend-test"), status=$("backend-status");
  if(!input || input.dataset.bound)return; input.dataset.bound="1"; input.value=API_BASE;
  const setStatus=(t)=>{if(status)status.textContent=t;};
  save?.addEventListener("click",async()=>{const value=input.value.trim().replace(/\/$/,""); if(value && !/^https:\/\//i.test(value)){setStatus("La URL del backend debe usar HTTPS.");return;} API_BASE=value; await DB.setMetadata({key:"backend:base_url",value}); setStatus(value?"URL del backend guardada.":"Backend desconfigurado.");});
  test?.addEventListener("click",async()=>{try{if(!API_BASE){setStatus("Guarda primero la URL del backend HTTPS.");return;} const r=await apiFetch("/api/health"); const d=await r.json(); if(!r.ok)throw new Error(d.error||"BACKEND_HEALTH_FAILED"); setStatus(`Backend conectado · ${d.service||"Sentia"} · ${d.version||"ok"}`);}catch(e){setStatus(`No se pudo conectar con el backend: ${e.message}`);}});
  if(API_BASE)setStatus(`Backend configurado: ${API_BASE}`);
}
function setupCallAudio(){
  const file=$("call-audio-file"), btn=$("call-audio-btn"), status=$("call-audio-status");
  if(!file||!btn||!status||file.dataset.bound)return; file.dataset.bound="1";
  file.addEventListener("change",()=>{const f=file.files?.[0]; btn.disabled=!f; status.textContent=f?`Listo: ${f.name} · ${Math.round(f.size/1024/1024*10)/10} MB`:"Selecciona un audio.";});
  btn.addEventListener("click",async()=>{const f=file.files?.[0]; if(!f)return; btn.disabled=true; status.textContent="Transcribiendo en Cohere y procesando en Python…"; try{const r=await apiFetch("/api/ingest/audio?language=es",{method:"POST",body:(()=>{const fd=new FormData(); fd.append("file",f,f.name); return fd;})()}); const data=await r.json(); if(!r.ok)throw new Error(data.message||data.error||"AUDIO_INGEST_FAILED"); await importPayload(data.payload,"append"); status.textContent="Llamada transcrita y analizada en español. Cohere Transcribe no identifica hablantes automáticamente.";}catch(e){status.textContent=`No se pudo procesar la llamada: ${e.message}`;}finally{btn.disabled=false;}});
}

async function setupManualIngestion(){
  const file=$("manual-file"), btn=$("manual-import-btn"), status=$("manual-import-status");
  if(!file||!btn)return;
  file.addEventListener("change",()=>{btn.disabled=!file.files?.[0]; status.textContent=file.files?.[0]?`Listo: ${file.files[0].name}`:"Selecciona un archivo para comenzar.";});
  btn.addEventListener("click",async()=>{
    const f=file.files?.[0]; if(!f)return;
    btn.disabled=true; status.textContent="Procesando en Python…";
    try{
      const content=await f.text();
      const body={filename:f.name,content,source_type:$("manual-source-type").value,source:$("manual-source-name").value.trim()||$("manual-source-type").value,analysis_language:$("manual-analysis-language").value.trim()||"es",translated:$("manual-translated").checked,auto_translate:$("manual-auto-translate").checked};
      const r=await apiFetch("/api/ingest/manual",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(body)});
      const data=await r.json(); if(!r.ok)throw new Error(data.error||"MANUAL_INGEST_FAILED");
      await importPayload(data.payload,"append");
      status.textContent=`Importación completada: ${data.source_count} conversación(es). Se conserva el original y, si existía, el texto traducido.`;
    }catch(e){status.textContent=`No se pudo procesar: ${e.message}. Verifica que el backend seguro esté activo.`;}
    finally{btn.disabled=false;}
  });
}

async function renderKnowledge(){
  const summary=$("knowledge-summary"), list=$("knowledge-list"), query=$("knowledge-query"), status=$("knowledge-search-status"); if(!summary||!list)return;
  const rows=await DB.getKnowledge().catch(()=>[]);
  summary.textContent=`${rows.length} conocimiento(s) conversacional(es) almacenado(s) localmente.`;
  const renderRows=(items, search=false)=>{
    list.innerHTML=items.length?`<table><thead><tr><th>Tipo</th><th>Concepto</th>${search?"<th>Similitud</th>":""}<th>Frecuencia</th><th>Confianza</th><th>Estado</th><th>Evidencia</th><th>Aliases</th></tr></thead><tbody>${items.slice(0,100).map(x=>`<tr><td>${escapeHtml(x.type)}</td><td>${escapeHtml(x.canonical_name)}</td>${search?`<td>${Math.round(Number(x.similarity||0)*100)}%<div class="knowledge-result-reason">${(x.match_reason||[]).map(r=>`<span>${escapeHtml(r)}</span>`).join("")}</div></td>`:""}<td>${escapeHtml(x.frequency)}</td><td>${Math.round(Number(x.confidence||0)*100)}%</td><td>${escapeHtml(x.status)}</td><td>${escapeHtml(`${Number(x.evidence_mention_count||0)} menciones · ${Number(x.evidence_conversation_count||0)} conversaciones`)}</td><td>${escapeHtml((x.aliases||[]).join(", "))}</td></tr>`).join("")}</tbody></table>`:`<p class="muted">${search?"No se encontraron coincidencias con el umbral actual.":"Todavía no hay conocimiento propuesto. Importa conversaciones para comenzar a aprender."}</p>`;
  };
  renderRows(rows);
  const doSearch=async()=>{
    const q=(query?.value||"").trim();
    if(!q){renderRows(rows); if(status)status.textContent="Consulta vacía: mostrando toda la memoria local."; return;}
    const results=await DB.searchKnowledge(q,{limit:20,minSimilarity:.35}).catch(()=>[]);
    renderRows(results,true);
    if(status)status.textContent=`${results.length} coincidencia(s) · motor local determinista · sin Cohere.`;
  };
  const searchBtn=$("knowledge-search-btn"), clearBtn=$("knowledge-search-clear");
  if(searchBtn) searchBtn.onclick=doSearch;
  if(query) query.onkeydown=e=>{if(e.key==="Enter")doSearch();};
  if(clearBtn) clearBtn.onclick=()=>{if(query)query.value="";if(status)status.textContent="";renderRows(rows);};
}
function setupNavigation(){document.querySelectorAll(".nav-item").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".nav-item").forEach(x=>{x.classList.remove("active");x.setAttribute("aria-current","false")}); document.querySelectorAll(".view").forEach(x=>x.classList.add("hidden")); btn.classList.add("active"); btn.setAttribute("aria-current","page"); const view=$("view-"+btn.dataset.view); view.classList.remove("hidden"); $("page-title").textContent=btn.textContent; document.querySelector("main")?.focus({preventScroll:true}); if(btn.dataset.view==="integrations") renderIntegrations(); if(btn.dataset.view==="knowledge") renderKnowledge(); if(btn.dataset.view==="ingestion"){ setupManualIngestion(); setupCallAudio(); }}));}

async function registerOffline(){if("serviceWorker" in navigator){try{await navigator.serviceWorker.register("sw.js",{scope:"./"});}catch(error){console.warn("SERVICE_WORKER_UNAVAILABLE",error);}}}
document.addEventListener("DOMContentLoaded",async()=>{await loadApiBase();setupNavigation();setupConfiguration();setupFilters();setupManualIngestion();setupSync();loadData();registerOffline();renderIntegrations();$("open-integrations-center")?.addEventListener("click",()=>document.querySelector('[data-view="integrations"]')?.click());});
