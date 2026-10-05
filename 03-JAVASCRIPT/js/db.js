const DB_NAME = "SocialListeningDB";
const DB_VERSION = 13;

const DB = {
  open() {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new Error("DB_NOT_SUPPORTED"));
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        const mentions = db.objectStoreNames.contains("mentions")
          ? event.target.transaction.objectStore("mentions")
          : db.createObjectStore("mentions", { keyPath: "id_mencion" });
        for (const index of ["fecha","sentimiento_pysentimiento","categoria","severidad","score_matematico","calidad_dato","es_duplicado","fuente"]) {
          if (!mentions.indexNames.contains(index)) mentions.createIndex(index, index, { unique:false });
        }
        if (!db.objectStoreNames.contains("insights")) db.createObjectStore("insights", {keyPath:"id_insight"});
        if (!db.objectStoreNames.contains("metadata")) db.createObjectStore("metadata", {keyPath:"key"});
        if (!db.objectStoreNames.contains("integrations")) db.createObjectStore("integrations", {keyPath:"id"});
        if (!db.objectStoreNames.contains("analytics_reports")) db.createObjectStore("analytics_reports", {keyPath:"report_id"});
        if (!db.objectStoreNames.contains("conversations")) db.createObjectStore("conversations", {keyPath:"conversation_id"});
        if (!db.objectStoreNames.contains("knowledge_entities")) db.createObjectStore("knowledge_entities", {keyPath:"knowledge_id"});
        if (!db.objectStoreNames.contains("sync_state")) db.createObjectStore("sync_state", {keyPath:"provider"});
        if (!db.objectStoreNames.contains("sync_scheduler")) db.createObjectStore("sync_scheduler", {keyPath:"id"});
        if (!db.objectStoreNames.contains("sync_runs")) {
          const runs = db.createObjectStore("sync_runs", {keyPath:"run_id"});
          runs.createIndex("started_at", "started_at", {unique:false});
          runs.createIndex("status", "status", {unique:false});
        }
        if (!db.objectStoreNames.contains("sync_manifests")) {
          const manifests = db.createObjectStore("sync_manifests", {keyPath:"manifest_id"});
          manifests.createIndex("run_id", "run_id", {unique:false});
          manifests.createIndex("provider", "provider", {unique:false});
          manifests.createIndex("persisted_at", "persisted_at", {unique:false});
        }
        if (!db.objectStoreNames.contains("sync_repairs")) {
          const repairs = db.createObjectStore("sync_repairs", {keyPath:"repair_id"});
          repairs.createIndex("provider", "provider", {unique:false});
          repairs.createIndex("status", "status", {unique:false});
          repairs.createIndex("created_at", "created_at", {unique:false});
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error("DB_OPEN_ERROR"));
    });
  },
  async get(store, key) { const db=await this.open(); return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).get(key); req.onsuccess=()=>resolve(req.result||null); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); }); },
  async count(store="mentions") {
    const db = await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).count(); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async deleteWhere(store, predicate) {
    const db = await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readwrite"), os=tx.objectStore(store), req=os.openCursor();
      let deleted=0;
      req.onsuccess=()=>{ const cursor=req.result; if(!cursor) return; if(predicate(cursor.value)){ cursor.delete(); deleted++; } cursor.continue(); };
      tx.oncomplete=()=>resolve(deleted); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); tx.onabort=()=>reject(new Error("DB_DELETE_ERROR"));
      req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async clear(store="mentions") {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readwrite"), req=tx.objectStore(store).clear(); tx.oncomplete=()=>resolve(); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); req.onerror=()=>reject(new Error("DB_CLEAR_ERROR")); });
  },
  async putMany(store, rows) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readwrite"), os=tx.objectStore(store); try { rows.forEach(row=>os.put(row)); } catch (e) { tx.abort(); reject(new Error("DB_IMPORT_ERROR")); return; } tx.oncomplete=()=>resolve(rows.length); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); tx.onabort=()=>reject(new Error("DB_IMPORT_ERROR")); });
  },
  async replaceMany(store, rows) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readwrite"), os=tx.objectStore(store); try { os.clear(); rows.forEach(row=>os.put(row)); } catch (e) { tx.abort(); reject(new Error("DB_IMPORT_ERROR")); return; } tx.oncomplete=()=>resolve(rows.length); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); tx.onabort=()=>reject(new Error("DB_IMPORT_ERROR")); });
  },
  async getAll(store="mentions") {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).getAll(); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async getAllPaged(store="mentions", offset=0, limit=100) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).openCursor(); const rows=[]; let skipped=0; req.onsuccess=()=>{ const cursor=req.result; if(!cursor) return resolve(rows); if(skipped<offset){skipped++;cursor.continue();return;} rows.push(cursor.value); if(rows.length>=limit)return resolve(rows); cursor.continue(); }; req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async getCount(store="mentions") {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).count(); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async getAllByIndex(store, indexName, query=null, limit=1000) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readonly"), os=tx.objectStore(store);
      if(!os.indexNames.contains(indexName)) return reject(new Error("DB_INDEX_NOT_FOUND"));
      const req=os.index(indexName).openCursor(query); const rows=[];
      req.onsuccess=()=>{ const cursor=req.result; if(!cursor || rows.length>=limit) return resolve(rows); rows.push(cursor.value); cursor.continue(); };
      req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async getById(id) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const req=db.transaction("mentions","readonly").objectStore("mentions").get(id); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async getMetadata(key) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const req=db.transaction("metadata","readonly").objectStore("metadata").get(key); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async setMetadata(data) { return this.putMany("metadata", [data]); },
  async saveKnowledge(rows) { return this.putMany("knowledge_entities", rows.map(x => ({...x, knowledge_id: x.knowledge_id || `${x.type}:${x.canonical_name}`, evidence_mention_ids:(x.evidence_mention_ids||[]).slice(0,100), evidence_conversation_ids:(x.evidence_conversation_ids||[]).slice(0,100)}))); },
  async getKnowledge() { return this.getAll("knowledge_entities"); },
  async put(store, row) { const db=await this.open(); return new Promise((resolve,reject)=>{ const tx=db.transaction(store,"readwrite"); tx.objectStore(store).put(row); tx.oncomplete=()=>resolve(row); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); }); },
  async saveAnalyticsReport(report) { const report_id = report.report_id || `ga4:${report.property_id}:${report.start_date}:${report.end_date}`; return this.put("analytics_reports", {...report, report_id}); },
  async saveSyncState(row) { return this.put("sync_state", row); },
  async getSyncState(provider) { return this.get("sync_state", provider); },
  async getSyncStates() { return this.getAll("sync_state"); },
  async saveSyncRun(row) { return this.put("sync_runs", row); },
  async getSyncRuns(limit=20) { const rows=await this.getAll("sync_runs"); return rows.sort((a,b)=>Number(b.started_at||0)-Number(a.started_at||0)).slice(0,limit); },
  async saveSyncManifest(row) { return this.put("sync_manifests", row); },
  async getSyncManifests(limit=50) { const rows=await this.getAll("sync_manifests"); return rows.sort((a,b)=>Number(b.persisted_at||0)-Number(a.persisted_at||0)).slice(0,limit); },
  async saveSyncRepair(row) { return this.put("sync_repairs", row); },
  async getSyncRepairs(limit=50) { const rows=await this.getAll("sync_repairs"); return rows.sort((a,b)=>Number(b.created_at||0)-Number(a.created_at||0)).slice(0,limit); },
  async cleanupOperationalData(policy = {}) {
    const now = Date.now();
    const defaults = {sync_runs_days:90,sync_runs_max:500,sync_manifests_days:90,sync_manifests_max:500,sync_repairs_days:180,sync_repairs_max:250};
    const cfg = Object.fromEntries(Object.entries(defaults).map(([k,v]) => [k, Math.max(1, Math.min(k.endsWith("_days")?3650:10000, Number(policy[k] ?? v)||v))]));
    const prune = async (store, timeField, days, max) => {
      const rows = await this.getAll(store);
      const ordered = rows.slice().sort((a,b)=>Number(b[timeField]||0)-Number(a[timeField]||0));
      const cutoff = now - days*86400000; const keep=[]; let age=0, limit=0;
      for (const row of ordered) { const ts=Number(row[timeField]||0); if(ts && ts<cutoff){age++;continue;} if(keep.length>=max){limit++;continue;} keep.push(row); }
      const keepKeys = new Set(keep.map(x=>x[store==="sync_runs"?"run_id":store==="sync_manifests"?"manifest_id":"repair_id"]));
      const deleted = await this.deleteWhere(store, row => !keepKeys.has(row[store==="sync_runs"?"run_id":store==="sync_manifests"?"manifest_id":"repair_id"]));
      return {before:rows.length,after:rows.length-deleted,deleted,removed_by_age:age,removed_by_limit:limit};
    };
    return {version:1,scope:["sync_runs","sync_manifests","sync_repairs"],sync_runs:await prune("sync_runs","started_at",cfg.sync_runs_days,cfg.sync_runs_max),sync_manifests:await prune("sync_manifests","persisted_at",cfg.sync_manifests_days,cfg.sync_manifests_max),sync_repairs:await prune("sync_repairs","created_at",cfg.sync_repairs_days,cfg.sync_repairs_max),business_data_untouched:true};
  },
  async getSyncScheduler() { return this.get("sync_scheduler", "default"); },
  async saveSyncScheduler(config) { return this.put("sync_scheduler", {...config, id:"default"}); },
  async getAnalyticsReports() { return this.getAll("analytics_reports"); },
  async searchKnowledge(query, options = {}) {
    const rows = await this.getKnowledge();
    const normalize = (text) => String(text || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9ñü\s-]/g, " ").replace(/\s+/g, " ").trim();
    const stop = new Set(["a","al","el","la","lo","y","o","de","en","un","una","me","te","se","mi","tu","ya","todavia","dias","hoy","ahora","para","porque","como","este","esta","esto","tengo","tiene","quiero","puede","puedo","cuando","donde","desde","sobre","entre","pero","muy","que","del","las","los","con","por","sin","mas"]);
    const equivalents = {demoro:"demora",demorado:"demora",demorada:"demora",demorar:"demora",retraso:"demora",retrasado:"demora",retrasada:"demora",tarde:"demora",esperando:"demora",esperan:"demora",esperar:"demora",esperado:"demora",espera:"demora",entregan:"entrega",entregado:"entrega",entregar:"entrega",llega:"entrega",llegado:"entrega",llegar:"entrega"};
    const tokens = (v) => new Set(normalize(v).replace(/_/g," ").split(/\s+/).filter(t => t.length >= 2 && !stop.has(t)).map(t=>equivalents[t]||t));
    const jaccard = (a,b) => a.size && b.size ? [...a].filter(x => b.has(x)).length / new Set([...a,...b]).size : 0;
    const queryNorm = normalize(query);
    const limit = Math.max(1, Math.min(50, Number(options.limit || 10)));
    const min = Math.max(0, Math.min(1, Number(options.minSimilarity ?? 0.35)));
    return rows.filter(x => x.status !== "rejected").map(x => {
      const candidates = [x.canonical_name, x.label, ...(x.aliases || [])].filter(Boolean);
      let similarity = 0, reason = [];
      candidates.forEach(c => {
        const cn = normalize(c), score = jaccard(tokens(query), tokens(c));
        let value = score, r = "";
        if(queryNorm === cn){value=1;r="exact_match";}
        else if((x.aliases||[]).includes(c) && (queryNorm.includes(cn) || cn.includes(queryNorm))){value=Math.max(value,.96);r="alias_match";}
        else if(queryNorm.includes(cn) || cn.includes(queryNorm)){value=Math.max(value,.82);r="normalized_phrase_match";}
        else if(value >= .34){r="token_similarity";}
        if(value > similarity){similarity=value;reason=r?[r]:[];}
        else if(value===similarity && r && !reason.includes(r))reason.push(r);
      });
      return {...x, knowledge_id:x.knowledge_id || `${x.type}:${x.canonical_name}`, similarity:Number(similarity.toFixed(4)), match_reason:reason};
    }).filter(x => x.similarity >= min).sort((a,b)=>b.similarity-a.similarity || Number(b.confidence||0)-Number(a.confidence||0) || Number(b.frequency||0)-Number(a.frequency||0)).slice(0,limit);
  },
  async getIntegration(id) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{ const req=db.transaction("integrations","readonly").objectStore("integrations").get(id); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR")); });
  },
  async saveIntegration(config) {
    const safe = {...config};
    delete safe.apiKey; delete safe.clientSecret; delete safe.accessToken; delete safe.refreshToken; delete safe.privateKey;
    safe.updatedAt = new Date().toISOString();
    return this.putMany("integrations", [safe]);
  }
};
