(() => {
  const status = document.getElementById("status");
  const idb = document.getElementById("indexeddb-status");
  const sw = document.getElementById("sw-status");
  const online = document.getElementById("online-status");
  idb.textContent = window.indexedDB ? "disponible" : "no disponible";
  online.textContent = navigator.onLine ? "online" : "offline";
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js", {scope:"./"})
      .then(() => { sw.textContent = "registrable"; })
      .catch(() => { sw.textContent = "error de registro"; });
  } else {
    sw.textContent = "no disponible";
  }
  status.textContent = "browser-smoke-ready";
})();
