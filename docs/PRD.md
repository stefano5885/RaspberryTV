# Product Requirements Document (PRD)

## 1. Overview

- **Product / Feature Name:** RaspberryTV Kiosk
- **Owner:** Project maintainer
- **Status:** Approved for implementation
- **Last Updated:** 2026-08-31

## 2. Summary

RaspberryTV trasforma un Raspberry Pi 3 Model B collegato via HDMI in un kiosk web controllabile dal telecomando della TV tramite HDMI-CEC. Una sola applicazione web locale serve sia la UI sulla TV sia l'amministrazione da browser LAN. Il dispositivo viene predisposto senza tastiera, avvia automaticamente il sito configurato, recupera su richiesta un URL da Telegram e aggiorna il proprio codice da tag Git stabili con rollback. La soluzione privilegia componenti standard, dipendenze minime e manutenzione comprensibile.

## 3. Problem Statement

Occorre mostrare stabilmente un sito pubblico su una TV senza lasciare tastiera o personale tecnico presso il dispositivo. Configurazione, diagnosi e aggiornamenti devono essere possibili dalla LAN, mentre il normale uso deve funzionare con il solo telecomando HDMI-CEC. Crash, reboot e interruzioni temporanee della rete non devono lasciare il kiosk inutilizzabile.

## 4. Goals and Non-Goals

**Goals**

- Avvio autonomo dalla SD preparata, senza operazioni interattive sul Raspberry Pi.
- Gestione completa via telecomando TV e UI LAN.
- Ethernet sempre disponibile come fallback e Wi-Fi configurabile dalla UI.
- Browser kiosk recuperabile, URL persistente e recupero Telegram su richiesta.
- Aggiornamenti applicativi basati su tag SemVer e rollback automatico.
- Configurazione e dati separati dal codice.
- Architettura piccola, verificabile e adatta a 1 GB di RAM.

**Non-Goals**

- Esposizione su Internet, UPnP, port forwarding o amministrazione cloud.
- Login al sito mostrato, gestione DRM o sessioni utente complesse.
- Aggiornamento automatico del sistema operativo.
- Container, microservizi, database, broker, reverse proxy o SPA.
- Supporto garantito a ogni telecomando/TV: le varianti CEC richiedono collaudo hardware.
- Alta disponibilità multi-nodo o gestione centralizzata di una flotta.

## 5. Success Metrics

| Metric | Baseline | Target | Timeframe | Notes |
|---|---:|---:|---|---|
| Boot fino al kiosk con URL e rete disponibili | N/D | <= 120 s | Ogni avvio | Pi 3, SD A1/A2 |
| Recupero automatico dopo crash browser/backend | N/D | <= 15 s | Ogni crash simulato | Supervisione systemd |
| Operazioni normali che richiedono tastiera | N/D | 0 | Sempre | Dopo SD preparata |
| Aggiornamento che conserva configurazione | N/D | 100% | Ogni release | Verifica automatica e manuale |
| Rollback dopo health check fallito | N/D | <= 90 s | Ogni test di failure | Ripristino release precedente |
| Dipendenze Python runtime di terze parti | N/D | 0 | Release iniziale | Standard library |
| Comandi applicativi per installazione standard | N/D | 1 | Prima installazione | Dopo accesso SSH |

## 6. Users and Use Cases

**Primary Users**

- Operatore davanti alla TV, con il solo telecomando.
- Amministratore sulla stessa LAN, con browser desktop o mobile.
- Manutentore che prepara la SD e pubblica release Git.

**Key Use Cases**

- Visualizzare automaticamente l'URL configurato a ogni boot.
- Navigare link e controlli del sito con frecce, OK e Back.
- Tornare alla dashboard locale e riaprire il kiosk.
- Configurare URL, Wi-Fi e Telegram dalla LAN.
- Recuperare l'ultimo URL Telegram valido con un pulsante.
- Controllare e installare una release stabile, con rollback.
- Diagnosticare rapidamente rete, browser, CEC e versione.

## 7. Requirements

| ID | Requirement | Priority | Rationale | Acceptance Criteria |
|---|---|---|---|---|
| R1 | Preparazione SD e primo boot senza tastiera | P0 | Installazione remota | Con Ethernet il servizio e la UI LAN diventano disponibili senza shell locale |
| R2 | Unica UI web per HDMI e LAN | P0 | Semplicità | Stesse pagine e API sono usate da Brave e client LAN |
| R3 | URL HTTP/HTTPS validato e persistente | P0 | Sicurezza/continuità | URL non validi sono rifiutati e l'ultimo valido resta attivo |
| R4 | Ethernet fallback e Wi-Fi via NetworkManager | P0 | Raggiungibilità | Il cavo rende nuovamente raggiungibile il Pi anche se il Wi-Fi fallisce |
| R5 | Brave kiosk ARM64 con fallback Chromium | P0 | Esperienza TV | Browser fullscreen senza chrome e riavviato dopo crash |
| R6 | CEC tradotto in eventi keyboard Linux | P0 | Telecomando nel sito | Frecce/OK raggiungono anche la pagina pubblica, Back torna indietro/UI |
| R7 | Telegram Bot API con polling manuale | P0 | Aggiornamento URL | Solo chat/topic ammessi; ultimo URL valido viene salvato |
| R8 | Segreti mai restituiti al frontend o nei log | P0 | Protezione locale | UI mostra solo configurato/non configurato; file mode 0600 |
| R9 | Update da ultimo tag SemVer stabile | P0 | Release controllate | Branch, prerelease e tag malformati non sono installati |
| R10 | Release precedente e rollback automatico | P0 | Affidabilità | Health check fallito ripristina symlink e servizi precedenti |
| R11 | systemd per web, kiosk e CEC | P0 | Recovery | Restart on-failure configurato e ordine di avvio documentato |
| R12 | Stato sintetico e journald limitato | P1 | Diagnosi | Dashboard mostra rete/versione/servizi senza segreti |
| R13 | Polling Telegram periodico opzionale e lento | P2 | Automazione | Disattivato per default; intervallo minimo documentato |
| R14 | Rollback manuale dalla UI | P1 | Recovery operatore | Disponibile solo se una release precedente è registrata |
| R15 | Bootstrap pubblico da GitHub con un solo comando | P0 | Setup senza copia manuale | Su Pi 3 con OS 64-bit lo script installa e avvia i servizi senza tastiera locale |
| R16 | Compatibilità con immagine OS completa | P0 | Disponibilità Raspberry Pi Imager | Il desktop preinstallato viene disabilitato e non compete con il kiosk su `:0` |
| R17 | Schermata di attesa e apertura automatica | P0 | Uso senza browser LAN | Al boot appare lo stato di caricamento e il sito configurato si apre senza premere pulsanti |
| R18 | Telemetria CPU e RAM | P1 | Diagnosi Pi 3 | Dashboard mostra CPU, temperatura, load, RAM usata e percentuale |
| R19 | Brave Shields Aggressive e nessun banner analytics | P0 | Esperienza kiosk/privacy | Profilo e policy impongono filtro aggressivo; P3A, stats ping, Web Discovery e Translate sono disabilitati |

## 8. User Experience and Flows

- **UX Notes:** controlli grandi, contrasto elevato, focus visibile, griglia navigabile con frecce, nessuna azione critica al semplice focus. Conferma richiesta per reboot, update e rollback.
- **Key Screens / States:** dashboard; configurazione URL; Wi-Fi; Telegram; aggiornamenti; stato incompleto; operazione in corso; errore recuperabile.
- **Direzione visiva:** control plane tecnico, scuro e moderno, con monospace, griglia, indicatori di stato e telemetria leggibile dalla LAN e dalla TV.
- **Flow References:**
  - Boot -> rete -> servizio web -> URL valido? -> browser sul sito : dashboard.
  - Back dedicato/lungo -> dashboard -> azione -> ritorno al sito.
  - Aggiorna URL -> Telegram `getUpdates` -> filtri -> validazione -> salvataggio -> reload browser.
  - Aggiorna app -> controllo tag -> richiesta one-shot -> release -> symlink -> restart -> health check -> conferma/rollback.
  - Imager -> primo boot Ethernet -> SSH -> bootstrap GitHub -> dashboard LAN -> configurazione -> kiosk.

## 9. Data and Analytics

**Eventi locali da registrare**

- Avvio servizio, cambio URL (senza query sensibili nei log), esito Telegram.
- Connessione Wi-Fi, richiesta reboot/browser, aggiornamento e rollback.
- Errori CEC e crash dei servizi tramite journald.

**Dashboard / report**

- Solo stato corrente e ultimo esito delle operazioni. Nessuna telemetria esterna.
- File persistenti: `config.json`, `secrets.json`, `state.json`, `update-status.json`.

## 10. Dependencies and Integrations

- Raspberry Pi OS 64-bit, Lite o completo, release stabile corrente compatibile col Pi 3; Xorg/Openbox minimi e sessione kiosk dedicata sono gestiti dal provisioning.
- Python 3 standard library; `git`; `curl`; `NetworkManager/nmcli`; `systemd`.
- Brave ufficiale ARM64. Chromium di Raspberry Pi OS è il fallback se Brave non supera il collaudo.
- `cec-utils/libCEC` per eventi CEC; `ydotool`/uinput per input sintetico sotto Wayland, con `xdotool` fallback X11 se necessario.
- Telegram Bot API via HTTPS `getUpdates`; nessun webhook.
- Repository pubblico `https://github.com/stefano5885/RaspberryTV` per bootstrap e release applicative.

## 11. Risks, Assumptions, and Open Questions

**Risks**

- Le implementazioni CEC dei produttori differiscono per codici e tasto Back.
- Il Pi 3 può essere lento su siti moderni pesanti; Brave e filtri aumentano il carico.
- La modalità Shields Aggressive può interrompere funzionalità first-party su alcuni siti; il requisito la impone e va collaudato sull'URL reale.
- L'iniezione input dipende dalla sessione grafica (Wayland/X11) e va provata sull'immagine scelta.
- Una deploy key Git privata mal gestita compromette il repository; deve essere read-only.
- L'esecuzione diretta di uno script remoto come root richiede fiducia nel repository e in GitHub; viene documentata anche la variante download-ispezione-esecuzione.
- La configurazione Wi-Fi può interrompere temporaneamente la richiesta HTTP in corso.

**Assumptions**

- La TV espone CEC e il sito pubblico ha elementi focusabili semanticamente.
- La LAN è fidata come dichiarato; l'app resta comunque protetta da controlli same-origin e bind configurabile.
- Ethernet riceve un indirizzo DHCP e mDNS o il router consente di trovare l'IP.
- I tag di release contengono un albero completo installabile.
- Il repository di distribuzione iniziale è pubblico e il Raspberry dispone di accesso Internet via Ethernet.
- La UI web può chiedere conferma ma non autenticazione.

**Open Questions**

- Modello TV e codici CEC effettivi: da chiudere durante il test hardware.
- URL definitivo e requisiti prestazionali del sito: da validare sul Pi 3.
- Repository pubblico o privato e relativo URL: configurabile in installazione.

## 12. Rollout Plan

- **Fase 1:** test unitari e integrazione simulata su workstation.
- **Fase 2:** pubblicazione repository GitHub e tag stabile iniziale.
- **Fase 3:** installazione bootstrap su SD di prova, rete e dashboard su Pi 3.
- **Fase 4:** collaudo Brave/Chromium, CEC e input con la TV reale.
- **Fase 5:** prova update e rollback end-to-end tra due tag stabili.
- **Launch Criteria:** tutti i P0 superati e checklist hardware firmata.
- **Rollback Plan:** symlink atomico alla release precedente; per problemi OS si conserva un'immagine SD nota funzionante.

## 13. Testing and QA

- **Test Strategy:** `unittest` per URL, configurazione, Telegram, API e SemVer/updater; test di integrazione con processi e repository Git temporanei; checklist hardware.
- **Key Test Cases:** segreti non esposti; file atomici; chat/topic errati; URL malformati; tag prerelease ignorati; update concorrenti; crash e rete assente.
- **Performance / Security:** misurare RAM/CPU e boot sul Pi 3; bind LAN; origin check sulle mutazioni; comandi privilegiati a lista chiusa; timeout per rete e subprocess; nessun secret nei log.

## 14. Appendix

### Decisioni architetturali

- **OS:** Raspberry Pi OS 64-bit Lite o completo. Il Pi 3 è ARMv8 e 64 bit permette Brave ARM64. Xorg e Openbox costituiscono la sessione kiosk dedicata; se l'immagine include un desktop, il relativo display manager viene disabilitato. L'immagine stabile corrente va collaudata prima della distribuzione.
- **Display server/window manager:** usare la sessione desktop supportata dall'immagine. Il bridge privilegia uinput, indipendente dal focus dell'app; X11 è fallback documentato.
- **Backend/frontend:** un processo Python e HTML/CSS/JS statici, senza framework e senza build frontend.
- **Storage:** JSON atomici fuori dal checkout, permessi 0600 per segreti.
- **Networking:** NetworkManager perché è lo strumento standard nelle release moderne e offre `nmcli`; non si mescolano dhcpcd/systemd-networkd.
- **Updater:** mirror Git locale, worktree per tag, symlink `current`, one-shot root e health check esterno.
- **Provisioning:** script idempotente eseguito sulla SD/nel primo boot; Raspberry Pi Imager prepara hostname, utente e rete iniziale.

### Controllo della complessità

| Categoria | Elementi | Motivazione |
|---|---|---|
| Processi applicativi | web, browser, CEC | Unico backend; browser e hardware richiedono processi propri |
| Dipendenze Python | nessuna | Standard library sufficiente |
| Dipendenze sistema | git, curl, NetworkManager, browser, cec-utils, ydotool | Integrazioni indispensabili |
| Unit systemd | web, kiosk, CEC, updater one-shot | Supervisione e update isolato |
| Porte | TCP 8080, LAN | Unica UI/API; configurabile |
| Persistenza | `/etc/raspberrytv`, `/var/lib/raspberrytv` | Separazione codice/configurazione/stato |

### Alternatives Considered

- Flask/FastAPI: più ergonomici, ma aggiungono packaging e dipendenze non necessarie per poche API.
- React/Vue: scartati per peso e doppia toolchain.
- SQLite: scartato; lo stato è piccolo e non relazionale.
- Docker: scartato per RAM, storage e complessità operativa.
- Polling Telegram continuo: scartato; richiesta manuale per default.
- Checkout Git unico: semplice ma meno atomico; worktree + symlink rende il rollback deterministico.

### References

- Raspberry Pi OS documentation: https://www.raspberrypi.com/documentation/usage/raspberry-pi-os/
- Brave Linux installation and ARM64 support: https://brave.com/linux/
- libCEC project: https://github.com/Pulse-Eight/libcec
