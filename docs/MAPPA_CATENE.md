# Mappa formati volantini – catene Torino (verifica 09/11/2026)

Verifica fatta leggendo l'HTML delle pagine ufficiali (senza eseguire JavaScript). "Non verificato" = la pagina carica il volantino via JavaScript o blocca i lettori automatici; servirà una prova con browser headless (es. da GitHub Actions).

| Catena | Formato | Prezzo al kg | Serve scegliere il negozio | Prezzi con carta | Costo estrazione |
|---|---|---|---|---|---|
| Aldi | Pagina web con offerte in testo + sfogliabile (no PDF) | Sì | No (offerte nazionali) | Non segnalati | Basso |
| Carrefour | Pagina web con offerte in testo (schede prodotto) | Sì | Sì (per volantino) | Etichetta PAYBACK | Basso |
| Eurospin | Pagina web con offerte in testo + sfogliabile separato | Non visto | Sì | "Offerte Family" (app) | Basso |
| MD | Sfogliabile con "scarica il PDF" | Da verificare | Sì | Sì (Buona Spesa Card) | Basso/medio (se PDF con testo) |
| Conad | Volantino per negozio; PDF su conad.it/assets/common/volantini/... | Non visto | Sì | "Riservato ai titolari di Carte Conad" | Basso/medio |
| Nova Coop / Ipercoop | Sfogliabile per negozio su volantinopiu.com; esistono PDF su resources.volantinopiu.it | Da verificare | Sì | Da verificare | Medio |
| Il Gigante | Visualizzatore ShopFully per negozio: API con i prodotti (titolo, marca, prezzo, pagina, testo letto dall'immagine) | Sì (API) | Sì | Blucard ("CON BLUCARD" nel testo) | Basso – **nella raccolta dal 10/11/2026** (corso Marche, punto=47) |
| Unes | Pagine in SVG per negozio (l'SVG può contenere testo) | Da verificare | Sì | Unes Family | Medio |
| Lidl | Sfogliabile a immagini | Da verificare | Sì | Lidl Plus | Alto (OCR) |
| Penny | Sfogliabile (caricato da altro sito) | Da verificare | Da verificare | Penny Card | Alto (probabile OCR) |
| Famila | Sfogliabile per negozio | Da verificare | Sì | Carta Club | Alto (probabile) |
| Despar/Eurospar | Offerte per negozio (formato non chiaro) | Da verificare | Sì | Da verificare | Da verificare |
| Crai | Volantino per negozio, caricato dinamicamente | Da verificare | Sì | CartaPiù | Da verificare |
| Esselunga | Non verificato (blocca i lettori automatici) | – | – | Fidaty | Da verificare |
| Bennet, Pam Panorama | Non verificato (contenuto solo via JavaScript) | – | – | – | Da verificare |
| Mercatò/DPiù, Prestofresco, Sigma | Non verificato | – | – | – | Da verificare |

## Osservazioni
- Quasi tutte le catene legano il volantino al punto vendita: il dato va raccolto per negozio, il che si sposa con il raggio dalla posizione.
- Le più economiche da leggere sono Aldi, Carrefour ed Eurospin (testo HTML), poi MD e Conad (PDF).
- Le catene a sole immagini richiedono OCR: fattibile nell'automazione GitHub (es. Tesseract) senza token, ma con più errori.
- Da rispettare le condizioni d'uso dei siti; Esselunga blocca esplicitamente i lettori automatici.
