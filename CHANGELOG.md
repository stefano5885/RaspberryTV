# Changelog

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
