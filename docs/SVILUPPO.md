# Segugio offerte – Torino e dintorni

File di progetto: decisioni, fonti e note di sviluppo.

## Obiettivo
Cercare periodicamente (1 volta a settimana, oppure ogni 10 giorni se il costo è alto) le offerte dei volantini dei supermercati di Torino e dintorni, elencare tutti i prodotti alimentari e ordinarli dal prezzo più conveniente.
Output iniziale: artefatto. In futuro: valutare una PWA.

## Domande aperte (09/11/2026)
- Catene da includere/escludere
- Zona esatta (comuni della cintura o raggio da un CAP)
- Ordinamento: prezzo al kg/litro o prezzo assoluto
- Raggruppamento: lista unica, per categoria, confronto stesso prodotto tra catene
- Offerte con carta fedeltà / 3x2 / coupon: sì o no
- Perimetro "alimentare": bevande, alcolici, pet food

## Registro sviluppo
- 09/11/2026 – Avvio progetto, domande di chiarimento inviate. Verifica fonti in corso.

## Fonti – verifica del 09/11/2026
- Accesso diretto (curl) dal container ai siti dei volantini: bloccato dalla rete dell'ambiente. Funziona invece la lettura web tramite lo strumento di fetch.
- promoqui.it/torino e doveconviene.it/torino: leggibili, ma elencano solo i volantini per catena con le date di validità. I prezzi dei singoli prodotti sono dentro il visualizzatore del volantino (immagini), non come testo.
- Alcune catene pubblicano il volantino in PDF (es. conad.it/assets/common/volantini/...), da cui i prezzi si possono estrarre.
- Volantini attivi a Torino in questi giorni: Coop/Ipercoop (fino 18/11), Crai (fino 11/11), Il Gigante (18/11), Bennet (18/11), Pam (18/11), Famila (25/11), Conad, MD, Aldi, Unes, Penny (dal 10/11), Lidl (dal 12/11), Prestofresco, Sigma, DPiù, Mercatò.
- Ipotesi di metodo: per ogni catena cercare il PDF o la pagina offerte del sito ufficiale, estrarre prodotto/formato/prezzo/prezzo al kg, poi unire e ordinare.

## Proposta di architettura di Pippo (09/11/2026)
- Individuare tutte le catene che pubblicano il volantino online.
- Scaricare periodicamente i volantini su un server/database accessibile a Claude, così si usano meno token.
- Con lo storico: variazione dei prezzi nel tempo, anche per zona.
- Prezzi: assoluto e al kg/litro quando indicato nel volantino.
- Fase successiva (PWA): mappa per scegliere il raggio di ricerca, distanza dei punti vendita e calcolo del percorso.

### Note tecniche (Claude)
- Il risparmio di token vale per lo scaricamento; l'estrazione dei prezzi dai volantini-immagine richiede comunque OCR o un modello. Dove c'è un PDF con testo, l'estrazione è quasi gratuita.
- Ipotesi proposta: repo GitHub + GitHub Actions programmate (gratis), che scaricano i volantini e salvano i dati (SQLite o JSON) nel repo. Claude legge il repo; la PWA può leggere gli stessi dati.
- Alternative: Supabase (Postgres gratuito), VPS/NAS proprio.
- Da verificare: condizioni d'uso dei siti aggregatori rispetto al download automatico; preferibile usare i siti ufficiali delle catene.

### Domande aperte sull'architettura
- Server/database: ne esiste già uno o va scelto?
- Repo GitHub nuovo (da creare a cura di Pippo)?
- Zona di riferimento per mappa/raggio (indirizzo o CAP).

## Decisioni (09/11/2026, 17:45)
- Repo: https://github.com/pippotorre/spesaok (GitHub come archivio/database).
- Zona: raggio impostabile rispetto alla posizione dell'utente (geolocalizzazione), non un indirizzo fisso.
- Carte fedeltà: includere le offerte, ma con un'etichetta chiara "prezzo con carta".
- Alimentare: cibo e bevande (alcolici compresi), esclusi i prodotti per animali.
- Visualizzazione iniziale: una lista unica con un campo di ricerca.
- Prezzi: assoluto + al kg/litro quando presente nel volantino.
- Prossimo passo: mappare per ogni catena il formato del volantino (PDF con testo / PDF solo immagine / solo immagini / pagina web) prima di scegliere le catene.
- 09/11/2026 – Repo pippotorre/spesaok collegato (vuoto). Mappatura formati in MAPPA_CATENE.md.
- 09/11/2026 18:15 – Catene iniziali: Coop (Nova Coop/Ipercoop) e Mercatò (richieste da Pippo) + Aldi, Carrefour, Eurospin, MD, Conad (scelta Claude).

## Stato al 09/11/2026 sera
- GitHub Actions funziona: workflow `raccolta-offerte` (scripts/collect.py) salva i dati grezzi in data/raw/<data>/ e li committa.
- Eurospin: API JSON del sito volantino (flyer.eurospin.com), serve l'header che il sito invia (catturato col browser). 253 prodotti, 130 alimentari, con prezzo al kg/l e categoria. FATTO.
- Coop (Nova Coop Torino-Collegno): PDF su resources.volantinopiu.it con testo estraibile; prezzi con "SOCI" = solo titolari Carta SocioCoop. Da scrivere il parser (impaginazione a colonne).
- Mercatò: PDF solo immagine (cdn.dimar.it/volantini/<id>/<id>_volantino.pdf), OCR Tesseract poco affidabile. Da decidere: OCR migliore o lettura con modello (costa token).
- Aldi: pagine offerte caricate via JavaScript, non ancora lette; PDF publitas con poco testo.
- Carrefour: bloccato da Cloudflare (verifica anti-bot).
- MD, Conad: richiedono scelta punto vendita, da fare.
- Coop ha un'API punti vendita con coordinate (novacoop.it/api/stores?lat=&lon=), utile per mappa/raggio.
- Pagina: app/template.html + scripts/build_page.py -> artefatto "Segugio Spesa Torino" (https://claude.ai/artifact/A2g9uSHCPpQX7ddmKYpqBn).
- Coop: parser scripts/parse_coop.py su pdftotext -bbox-layout (griglia nome/prezzi per colonna). 157 offerte alimentari, 80 circa "Soci". Imperfezioni note: qualche prezzo finale scambiato, pagine "sconto su tutta la linea" senza prezzi ignorate, bazar escluso con filtri a parole chiave.
- Il workflow ora normalizza (data/offerte.json) e genera app/index.html dopo ogni raccolta.
- 09/11/2026 notte – Mercatò: scelta di Pippo = OCR gratuito su GitHub. Tesseract (ita, psm 11) su tutte le pagine a 200 dpi, TSV con coordinate. Il prezzo grande (bianco su rosso) viene letto male, quindi il prezzo si ricava da "€/lt" o "€/kg" × formato (affidabile a ±1 cent), confrontato con le cifre lette nel riquadro. "SOLO CON" = prezzo con carta Club Mercatò. 202 offerte alimentari. Parser: scripts/parse_mercato.py.
- Lista ora: Eurospin 130, Coop 156, Mercatò 202 = 488 offerte.
- 09/11/2026 23:05 – PR #1 unita su main: raccolta settimanale attiva ogni giovedì 06:00 UTC (Eurospin, Coop, Mercatò). Prossimi: Aldi, MD, Conad.
- 09/11/2026 23:30 – Segnalazione di Pippo: alla Coop di Collegno Voiello 0,72 €/500 g e pancetta -50% mancavano. Cause: (1) leggevo solo un volantino dell'Ipercoop; ora la raccolta legge tutti i volantini di due negozi: Coop Collegno (negozi.volantinopiu.com/ccno-8001120004550.html, negozio di Pippo) e Ipercoop Torino (ccno-8001120004796). (2) Le pagine "Sconto X% su tutta la linea" mostrano solo i loghi delle marche, senza prezzi: l'OCR gratuito non legge bene i loghi (Voiello non riconosciuto). Nella pagina c'è un riquadro con sconto e link alla pagina del volantino. Possibile miglioramento: lettura dei loghi con Claude solo per quelle 4-6 pagine.
- Volantini solo immagine Coop (es. Black Friday, Feste in arrivo) passano dall'OCR; il Black Friday è elettronica, quindi scartato dal filtro.

## 10/11/2026 – Link al volantino, Aldi, MD, Conad, Carrefour
- Richiesta di Pippo: per ogni offerta il link al volantino originale da cui è stata letta (utile anche per la futura PWA, invece di incorporare il volantino). Campo `fonte` in data/offerte.json, link "volantino" su ogni riga.
- Aldi: le pagine "Speciali della settimana" (aldi.it/speciali-della-settimana/<data>) chiamano l'API asl.api.aldi.it/commerce/v3/product-search?promotionKey=<data>; la rileggiamo con gli stessi header della pagina. Prezzi nazionali (negozio predefinito del sito, San Giovanni Lupatoto), prezzo al kg/l incluso. Validità "fino a esaurimento": nella lista la data è indicativa (+6 giorni dall'uscita). ~75 offerte alimentari. Le "Offerte freschezza" (frutta e verdura) non passano da questa API: da approfondire.
- MD: la scheda del punto vendita (mdspa.it/punti-vendita/Piemonte/TO-Torino/223-TORINO, via Urbino) ha "Scarica volantino" = PDF di zona (…/volantini/nord-atm-na-gastro/volantino.pdf). PDF solo immagine: OCR Tesseract a 300 dpi + scripts/parse_md.py (prezzo = €/kg-l × formato, come Mercatò). ~77 offerte.
- Conad: la ricerca negozi usa reCAPTCHA e al browser automatico risponde "nessun risultato". Non aggiriamo le verifiche anti-bot: Conad per ora esclusa (alternativa: Pippo indica l'indirizzo della pagina del suo negozio Conad, se ha un link diretto al PDF).
- Carrefour: Cloudflare anti-bot, esclusa per lo stesso motivo.
- Filtro non alimentari corretto: "occhi" scartava "finocchiona/finocchio", "piatti" scartava i piatti pronti.
- Raccolta settimanale ora: Eurospin, Coop (2 negozi), Mercatò, Aldi, MD.

## 10/11/2026 – PWA "spesaok" su TopHost
- Decisioni di Pippo: indirizzo https://entratadisicurezza.com/spesaok/ ; PWA statica e pubblica; aggiornamento dati manuale (Claude avvisa, Pippo carica `offerte.json`); subito la funzione per raggiungere il supermercato; storico e lista della spesa rimandati; nome "spesaok" con grafica propria.
- Sorgenti in `pwa/` (index.html, style.css, app.js, sw.js, manifest, .htaccess, negozi.json, icons/). Build: `python scripts/build_pwa.py` -> `dist/spesaok/` + `dist/spesaok.zip` (dist/ non versionata).
- Funzioni: lista con ricerca, filtro per catena, ordinamento (kg/l, confezione, sconto), "senza carta", link al volantino con pagina, sezione Negozi, installazione (Android pulsante "Installa", iPhone suggerimento), uso offline (service worker; dati prima dalla rete, poi copia salvata).
- "Portami": Coop Collegno (Via Roma 74, Collegno) e Ipercoop Torino (Via Livorno 49) -> percorso Google Maps all'indirizzo; Aldi, Eurospin, Mercatò, MD (volantino di zona) -> ricerca su Google Maps del punto vendita più vicino.
- Logo: cartellino prezzo giallo con spunta su fondo verde (icons/logo.svg), icone 192/512/maskable/apple-touch.
- .htaccess: forza HTTPS, tipi MIME, no-cache per sw.js/offerte.json/index.html.
- Prossimi passi possibili: distanza dai negozi con geolocalizzazione e raggio, storico prezzi (servirà PHP/MySQL o JSON storici), lista della spesa.

## 10/11/2026 – Pubblicazione con GitHub Pages
- Proposta di Pippo: usare GitHub Pages. Il repo è pubblico, quindi Pages è gratuito.
- Workflow `.github/workflows/pages.yml` ("pubblica-pwa"): build della PWA e pubblicazione su Pages dopo ogni raccolta riuscita (workflow_run), a ogni push su main che tocca l'app o i dati, o a mano. Indirizzo: https://pippotorre.github.io/spesaok/
- Da fare una volta (Pippo): Settings → Pages → Source: "GitHub Actions".
- Opzioni per il dominio: (2) sottodominio spesaok.entratadisicurezza.com con record CNAME → pippotorre.github.io nel DNS di TopHost, poi impostarlo in Settings → Pages → Custom domain; (3) app su TopHost in /spesaok che legge i dati da Pages: `python scripts/build_pwa.py --dati https://pippotorre.github.io/spesaok/offerte.json --zip spesaok-tophost.zip` (caricata una volta, i dati si aggiornano da soli; GitHub Pages permette la lettura da altri siti).
- La PWA legge l'indirizzo dei dati dal meta `spesaok-dati` in index.html; il service worker salva una copia per l'uso offline anche se i dati arrivano da un altro sito.

## 10/11/2026 – Loghi delle catene
- Richiesta di Pippo: al posto dei pallini colorati e della fascia colorata, i loghi delle catene: in alto come filtri (a colori = attiva, grigio = esclusa), e nelle offerte accanto al nome.
- Loghi presi dai siti ufficiali con `scripts/fetch_logos.py` (workflow manuale "scarica-loghi"), scelti a mano e copiati in `pwa/logos/` (Aldi svg, Coop png 180, Eurospin svg, MD svg, Mercatò png 240). In `negozi.json`: campi `logo` ed `etichetta` (nome breve sotto il logo: Collegno / Ipercoop per i due negozi Coop). Se manca il logo si vedono le iniziali su fondo colorato.
- Corretto: il riquadro "sconti su intere linee Coop" non si nascondeva durante la ricerca (regola CSS `[hidden]`).
