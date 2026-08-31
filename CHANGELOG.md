# Changelog

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
