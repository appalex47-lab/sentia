const DB_NAME = "SocialListeningDB";
const DB_VERSION = 2;

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
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error("DB_OPEN_ERROR"));
    });
  },
  async count(store="mentions") {
    const db = await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).count();
      req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async clear(store="mentions") {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readwrite"), req=tx.objectStore(store).clear();
      tx.oncomplete=()=>resolve(); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
      req.onerror=()=>reject(new Error("DB_CLEAR_ERROR"));
    });
  },
  async putMany(store, rows) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readwrite"), os=tx.objectStore(store);
      try { rows.forEach(row=>os.put(row)); } catch (e) { tx.abort(); reject(new Error("DB_IMPORT_ERROR")); return; }
      tx.oncomplete=()=>resolve(rows.length); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
      tx.onabort=()=>reject(new Error("DB_IMPORT_ERROR"));
    });
  },
  async replaceMany(store, rows) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readwrite"), os=tx.objectStore(store);
      try { os.clear(); rows.forEach(row=>os.put(row)); } catch (e) { tx.abort(); reject(new Error("DB_IMPORT_ERROR")); return; }
      tx.oncomplete=()=>resolve(rows.length); tx.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
      tx.onabort=()=>reject(new Error("DB_IMPORT_ERROR"));
    });
  },
  async getAll(store="mentions") {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).getAll();
      req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async getAllPaged(store="mentions", offset=0, limit=100) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(store,"readonly"), req=tx.objectStore(store).openCursor();
      const rows=[]; let skipped=0;
      req.onsuccess=()=>{
        const cursor=req.result;
        if(!cursor) return resolve(rows);
        if(skipped<offset) { skipped++; cursor.continue(); return; }
        rows.push(cursor.value);
        if(rows.length>=limit) return resolve(rows);
        cursor.continue();
      };
      req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async getById(id) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const req=db.transaction("mentions","readonly").objectStore("mentions").get(id);
      req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async getMetadata(key) {
    const db=await this.open();
    return new Promise((resolve,reject)=>{
      const req=db.transaction("metadata","readonly").objectStore("metadata").get(key);
      req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(new Error("DB_TRANSACTION_ERROR"));
    });
  },
  async setMetadata(data) { return this.putMany("metadata", [data]); }
};
