# Architettura

## Componenti

```text
Telecomando TV --HDMI-CEC--> cec-client --> bridge uinput --> Brave/Chromium
                                                       |
Browser TV/LAN ----------------HTTP :8080---------------+
                                                       v
                                            applicazione Python unica
                                             |      |       |
                                      file JSON   Telegram  helper root
                                                         /    |      \
                                                     nmcli  systemd  reboot
```

### Applicazione web

`raspberrytv-web.service` esegue un server HTTP multithread della standard library. Serve HTML/CSS/JavaScript statici e le API JSON, incluse telemetria CPU, temperatura, load e RAM letta da `/proc` e `/sys`. `vcgencmd get_throttled` aggiunge il bitmask firmware, separando anomalie attive da quelle avvenute dopo l'accensione. Configurazione e stato sono scritti atomicamente; il token Telegram vive in `secrets.json` e non viene mai restituito dalle API.

### Kiosk

`raspberrytv-kiosk.service` avvia una sessione Xorg/Openbox minimale e un solo browser. Sull'immagine Raspberry Pi OS completa, il display manager del desktop viene disabilitato per impedire il conflitto su `:0`. Il browser mostra subito una pagina tecnica di boot, attende il backend e apre automaticamente il sito configurato oppure la dashboard.

Xorg viene avviato con screen blanking e DPMS disabilitati; anche `xset` riafferma la configurazione nella sessione. Finché la TV è accesa il segnale HDMI resta quindi attivo senza timeout software.

Openbox non avvia pannelli, file manager desktop, cestino o icone. `feh` applica il wallpaper diagnostico incluso nella release prima di Brave. Se il browser termina inaspettatamente, lo sfondo resta visibile e lo script tenta di riaprire Brave dopo tre secondi; quando lo spegnimento arriva dal CEC, systemd arresta invece l'intera sessione.

Gli script della sessione sono richiamati tramite `/bin/sh` e Python espliciti, quindi un checkout Git che perda il bit eseguibile non può più produrre `203/EXEC`. L'updater ripristina comunque mode `0755` come ulteriore protezione.

Il bootstrap installa, quando disponibile, `rpi-splash-screen-support` e configura `assets/boot-splash.tga` come immagine iniziale fullscreen. Il file rispetta i vincoli Raspberry Pi: 1920×1080, 24 bit, 224 colori, TGA non compresso. `configure-boot-splash.sh` elimina inoltre il successivo splash Plymouth standard e il riquadro arcobaleno del firmware; mantiene `quiet`, imposta `systemd.show_status=false` e disabilita il blanking della console, impedendo ai messaggi `[ OK ]` di coprire il logo. Il confronto con il logo già installato evita di rigenerare inutilmente l'initramfs.

Il profilo Brave viene riconfigurato prima di ogni avvio: adblock attivo, filtro cosmetico first-party in modalità `BLOCK` (Aggressive), P3A e usage ping disabilitati. Le policy amministrative impediscono la ricomparsa dei relativi banner. Il solo interstitial `BraveDomainBlock` è disattivato: il documento principale può caricarsi senza richiedere “Proceed”, mentre le richieste pubblicitarie e di tracciamento della pagina restano filtrate dagli Shields.

La dashboard accoda in `/var/lib/raspberrytv/browser-diagnostic-request.json` la richiesta di una nuova scheda diagnostica. Un worker non privilegiato, avviato nella stessa sessione X11 e con lo stesso profilo del kiosk, la consuma e contatta l'istanza browser già attiva. Sono consentite esclusivamente `gpu`, `media-internals` e `version`; lo schema è scelto dal worker (`brave://` o `chrome://`) in base al browser installato. Queste pagine non passano dalla validazione dell'URL pubblico, non modificano la configurazione e non rendono disponibile un navigatore interno generico.

### CEC, focus e puntatore

`raspberrytv-cec.service` legge `cec-client` con maschera log `31` e crea tramite `/dev/uinput` un dispositivo virtuale con tastiera e mouse relativo. Il livello DEBUG è necessario perché libCEC pubblica lì gli eventi decodificati `key pressed`; il traffico grezzo non viene esposto dalla dashboard:

| Telecomando | Evento Linux | Effetto |
|---|---|---|
| Giù / Destra | Tab | Focus successivo |
| Su / Sinistra | Shift+Tab | Focus precedente |
| OK / Select | Enter | Attivazione |
| Back / Return | Alt+Sinistra | Cronologia browser |
| Home / Root menu | riavvio kiosk sulla dashboard | Amministrazione locale |
| Rosso/Verde/Giallo/Blu | azione configurata | Home, sito, ricarica, indietro o nessuna |

In modalità Focus, Tab/Shift+Tab funziona sugli elementi semanticamente focusabili anche nei siti esterni. In modalità Puntatore, le quattro frecce producono spostamenti mouse relativi e OK un clic sinistro. Non viene iniettato JavaScript. La convenzione CEC assegna F1 al blu, F2 al rosso, F3 al verde e F4 al giallo; la dashboard consente di apprendere il nome effettivo trasmesso dalla TV.

Il bridge mantiene in `/var/lib/raspberrytv/cec-diagnostics.json` un registro strutturato limitato agli ultimi 100 eventi. La dashboard interroga `/api/cec` ogni secondo e mostra stato, tasti ricevuti, azione applicata, transizioni di alimentazione ed errori. Non viene esposto l'intero journal di sistema. `cec_keymap`, `cec_input_mode` e `cec_color_actions` sono riletti dal bridge a ogni pressione, senza riavvio.

Lo stesso client CEC interroga ogni 15 secondi lo stato di alimentazione del televisore. In standby arresta `raspberrytv-kiosk.service`, chiudendo Brave e Xorg ma lasciando acceso il Raspberry e il listener CEC. Quando rileva la riaccensione, riavvia il kiosk e invia `Active Source` per selezionare l'ingresso HDMI del Raspberry. Il cambio sorgente avviene una sola volta per ogni transizione verso acceso.

Su un monitor senza HDMI-CEC il bridge può restare in attesa o essere disabilitato: web e kiosk non dipendono dal servizio CEC.

### Networking

NetworkManager è l'unico gestore di rete. L'app legge stato e indirizzi con `nmcli`/`ip`; una richiesta Wi-Fi temporanea protetta con mode `0600` viene consumata dal piccolo helper root e subito eliminata. La password resta poi nel profilo protetto di NetworkManager.

### Telegram

Il pulsante chiama `getUpdates` con polling zero. Sono accettati solo chat e topic configurati, poi si seleziona il messaggio valido più recente. Telegram Bot API non è un'API di ricerca della cronologia: il bot può leggere gli update che Telegram non ha ancora eliminato e conserva localmente l'offset e l'ultimo risultato.

### Update e rollback

Il controllo usa `git ls-remote --tags --refs`. L'installazione è una unità root one-shot:

1. lock esclusivo;
2. clone/fetch del mirror;
3. validazione tag SemVer stabile;
4. worktree in `/opt/raspberrytv/releases/vX.Y.Z`;
5. symlink atomico `/opt/raspberrytv/current`;
6. restart web/kiosk;
7. health check con verifica della versione;
8. rollback del symlink se il check fallisce.

L'updater non modifica `/etc/raspberrytv`, `/var/lib/raspberrytv`, Wi-Fi o Raspberry Pi OS.

## File e permessi

| Percorso | Proprietario/mode | Contenuto |
|---|---|---|
| `/opt/raspberrytv/releases` | root, 0755 | codice immutabile per release |
| `/opt/raspberrytv/current` | root | symlink release attiva |
| `/etc/raspberrytv/config.json` | raspberrytv, 0600 | configurazione non segreta |
| `/etc/raspberrytv/secrets.json` | raspberrytv, 0600 | token Telegram |
| `/etc/raspberrytv-git/deploy_key` | root:raspberrytv, 0640 | chiave Git read-only opzionale |
| `/var/lib/raspberrytv/git-known-hosts` | raspberrytv, 0644 | host key SSH apprese al primo collegamento |
| `/var/lib/raspberrytv` | raspberrytv, 0750 | stato e profilo browser |

## Porte e confini

L'unica porta applicativa è TCP 8080. Xorg usa `-nolisten tcp`. Telegram e Git sono connessioni in uscita. Non sono presenti webhook, UPnP o reverse proxy.
