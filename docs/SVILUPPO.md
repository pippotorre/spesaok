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
