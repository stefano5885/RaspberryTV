# Changelog

## 0.6.2 - 2026-09-01

- Corretto “Comando di sistema non disponibile” aprendo i report Brave dalla stessa sessione del kiosk.
- La dashboard accoda la richiesta senza attendere l'avvio della scheda, evitando il timeout HTTP.
- Nuovo worker locale con allowlist stretta per GPU Report, Media Internals e Version Info.

## 0.6.1 - 2026-09-01

- Corretto il puntatore invisibile: Xorg non forza più il cursore sempre nascosto.
- Il cursore viene nascosto dopo 0,5 secondi di inattività e ricompare quando il telecomando lo muove.

## 0.6.0 - 2026-09-01

- Corretto il cambio Focus/Puntatore con configurazioni CEC provenienti dalle release precedenti.
- Il cambio modalità salva soltanto la modalità e non riconverte inutilmente la mappatura dei tasti.
- Nuovo modulo “Test Brave sul monitor” nella dashboard LAN.
- Apertura controllata in una nuova scheda di `brave://gpu`, `brave://media-internals` e `brave://version`.
- Supporto equivalente `chrome://` quando il kiosk usa Chromium come fallback.
- Il sito e la riproduzione corrente restano aperti durante la diagnostica; “Torna al sito” ripristina il kiosk normale.
- Le pagine interne non sono accettate come URL del kiosk e l'helper mantiene una allowlist stretta.

## 0.5.0 - 2026-09-01

- Modalità telecomando selezionabile: Focus oppure Puntatore, con frecce come mouse e OK come clic.
- Quattro tasti colorati/F1–F4 associabili dalla dashboard a Home, sito, ricarica, indietro o nessuna azione.
- Mappatura CEC compatibile con la convenzione standard F1 blu, F2 rosso, F3 verde e F4 giallo, correggibile con “Associa ultimo”.
- Nuova telemetria termica con temperatura SoC, stato throttling attuale, eventi storici e codice firmware.
- Nessuna nuova dipendenza runtime; movimento e clic sono generati direttamente tramite `uinput`.

## 0.4.0 - 2026-09-01

- Nuovo pannello HDMI-CEC con stato del bridge e registro strutturato aggiornato ogni secondo.
- Visualizzazione degli ultimi 100 eventi: tasti, azioni, alimentazione display ed errori dell'adattatore.
- Mappatura configurabile dei tasti CEC con funzione “Associa ultimo”.
- Comandi dalla dashboard per riavviare il bridge CEC e pulire il registro diagnostico.
- Diagnostica disponibile anche quando `/dev/uinput` o l'adattatore CEC non sono accessibili.
- Corretto il livello di output di `cec-client`: ora include gli eventi DEBUG necessari per ricevere i nomi decodificati dei tasti.

## 0.3.4 - 2026-08-31

- Ripristinato l'avvio silenzioso dopo la configurazione dello splash personalizzato.
- Nascosti i messaggi di avanzamento systemd `[ OK ]` che coprivano l'immagine RaspberryTV.
- Disabilitato anche il blanking della console già dalla fase iniziale del boot.

## 0.3.3 - 2026-08-31

- Eliminato lo splash Plymouth standard che poteva apparire dopo l'immagine RaspberryTV.
- Disabilitato anche il riquadro arcobaleno del firmware.
- Configurazione dello splash resa idempotente e applicata automaticamente anche passando dalla dashboard.
- Rimossa la pagina intermedia “This site may attempt to track you across other sites”: il documento principale prosegue, mentre Shields resta Aggressivo e continua a bloccare tracker e pubblicità incorporati.

## 0.3.2 - 2026-08-31

- Corretto `203/EXEC`: gli aggiornamenti ripristinano i permessi degli script e systemd usa esplicitamente gli interpreti.
- Supporto completo ai monitor privi di HDMI-CEC; il kiosk resta indipendente dal bridge telecomando.
- Splash tecnico RaspberryTV durante l'avvio, installato tramite il supporto ufficiale Raspberry Pi.

## 0.3.1 - 2026-08-31

- Autoriparazione di proprietario e permessi dei file di stato prima di ogni avvio del servizio web.
- Dashboard resistente a un file `release-state.json` o `update-status.json` temporaneamente non leggibile.
- Ripristino automatico del kiosk dopo la migrazione da una release che aveva scritto lo stato come root.

## 0.3.0 - 2026-08-31

- Wallpaper tecnico di fallback “Kiosk non avviato”, installato nella sessione Openbox priva di barra, cestino e icone.
- Riapertura automatica di Brave dopo una chiusura o un crash inatteso.
- Riparazione automatica dei permessi di `release-state.json` e degli altri file di stato dopo gli aggiornamenti eseguiti come root.
- Schermata di manutenzione visibile su TV e dashboard durante update/rollback, con riavvio automatico quando cambia release.
- Disabilitati screen blanking, salvaschermo e DPMS nella sessione kiosk.
- Monitoraggio periodico dello stato di alimentazione TV tramite HDMI-CEC.
- Chiusura di Brave e Xorg quando la TV entra in standby.
- Riavvio del kiosk e selezione automatica della sorgente RaspberryTV quando la TV si accende.

## 0.2.0 - 2026-08-31

- Nuova dashboard tecnica “control plane” con CPU, temperatura e RAM.
- Schermata di caricamento e apertura automatica del sito al boot.
- Compatibilità corretta con Raspberry Pi OS 64-bit completo tramite sessione kiosk dedicata.
- Brave Shields forzato su Aggressive.
- Disabilitati P3A, usage ping, Web Discovery, Translate e relativi banner.
- Sincronizzazione futura di policy e unità systemd durante gli aggiornamenti.

## 0.1.0 - 2026-08-31

- Prima release installabile.
