# Pagina di trasferimento su Tophost

spesaok ora è su **https://spesaok.entratadisicurezza.com/** (GitHub Pages).
La cartella `spesaok/` qui accanto va caricata su Tophost al posto della vecchia app, in `/spesaok` nella radice del sito.

Contenuto:
- `index.html` — pagina «spesaok ha un nuovo indirizzo» con redirect dopo 4 secondi (anche senza JavaScript, con meta refresh); conserva `?…` e `#…` del vecchio link.
- `sw.js` — sostituisce il service worker della vecchia app: cancella le copie salvate `spesaok*`, si disinstalla e ricarica le pagine aperte, così chi aveva l'app installata vede il trasferimento invece della versione vecchia.
- `.htaccess` — HTTPS obbligatorio; ogni altro vecchio indirizzo (app.js, offerte.json…) mostra la pagina di trasferimento; `index.html` e `sw.js` mai in cache.
- `icons/` — icone per la pagina.

## Caricamento via FTP
1. Fai un backup della cartella `/spesaok` attuale su Tophost.
2. Cancella tutto il contenuto di `/spesaok` (compresi `.htaccess`, `negozi.json`, `offerte.json`, `logos/`…).
3. Carica il contenuto di `tophost-redirect/spesaok/` dentro `/spesaok`: `index.html`, `sw.js`, `.htaccess`, `icons/`.
   (`.htaccess` è un file nascosto: nel client FTP attiva la visualizzazione dei file nascosti.)
4. Prova https://www.entratadisicurezza.com/spesaok/ — compare la pagina verde e dopo 4 secondi si passa al nuovo indirizzo.
