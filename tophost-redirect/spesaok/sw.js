/* spesaok – service worker di "spegnimento".
   Sostituisce quello della vecchia app su entratadisicurezza.com/spesaok/:
   cancella le copie salvate, si disinstalla e ricarica le pagine aperte,
   che così mostrano la pagina di trasferimento verso spesaok.entratadisicurezza.com. */
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const chiavi = await caches.keys();
    await Promise.all(chiavi.filter(k => k.startsWith('spesaok')).map(k => caches.delete(k)));
    await self.registration.unregister();
    const finestre = await self.clients.matchAll({ type: 'window' });
    finestre.forEach(f => f.navigate(f.url).catch(() => {}));
  })());
});
