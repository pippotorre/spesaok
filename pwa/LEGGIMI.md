# spesaok – PWA

Sorgenti della PWA pubblicata su https://entratadisicurezza.com/spesaok/ (TopHost, Apache).

- `python scripts/build_pwa.py` crea `dist/spesaok/` e `dist/spesaok.zip` (con `data/offerte.json` e un numero di versione).
- Prima pubblicazione: caricare il contenuto di `dist/spesaok/` nella cartella `/spesaok/` del sito (compreso il file nascosto `.htaccess`).
- Aggiornamento settimanale dei dati: ricaricare solo `offerte.json`.
- Se cambiano i file dell'app (html, css, js, icone): ricaricare tutta la cartella; il service worker avvisa gli utenti con "Nuova versione disponibile".
- `negozi.json`: come raggiungere ogni catena (indirizzo del negozio o ricerca del più vicino su Google Maps).
- Icone: `icons/logo.svg` (sorgente), PNG generati da SVG.

## GitHub Pages
- Il workflow `pubblica-pwa` pubblica `dist/spesaok/` su https://pippotorre.github.io/spesaok/ dopo ogni raccolta.
- Versione per TopHost che legge i dati da Pages (si carica una volta sola):
  `python scripts/build_pwa.py --dati https://pippotorre.github.io/spesaok/offerte.json --zip spesaok-tophost.zip`
