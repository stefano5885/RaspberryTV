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

`raspberrytv-web.service` esegue un server HTTP multithread della standard library. Serve HTML/CSS/JavaScript statici e le API JSON, incluse telemetria CPU, temperatura, load e RAM letta da `/proc`. Configurazione e stato sono scritti atomicamente; il token Telegram vive in `secrets.json` e non viene mai restituito dalle API.

### Kiosk

`raspberrytv-kiosk.service` avvia una sessione Xorg/Openbox minimale e un solo browser. Sull'immagine Raspberry Pi OS completa, il display manager del desktop viene disabilitato per impedire il conflitto su `:0`. Il browser mostra subito una pagina tecnica di boot, attende il backend e apre automaticamente il sito configurato oppure la dashboard.

Il profilo Brave viene riconfigurato prima di ogni avvio: adblock attivo, filtro cosmetico first-party in modalità `BLOCK` (Aggressive), P3A e usage ping disabilitati. Le policy amministrative impediscono la ricomparsa dei relativi banner.

### CEC e focus

`raspberrytv-cec.service` legge `cec-client` e crea `/dev/uinput` una tastiera virtuale:

| Telecomando | Evento Linux | Effetto |
|---|---|---|
| Giù / Destra | Tab | Focus successivo |
| Su / Sinistra | Shift+Tab | Focus precedente |
| OK / Select | Enter | Attivazione |
| Back / Return | Alt+Sinistra | Cronologia browser |
| Home / Root menu | riavvio kiosk sulla dashboard | Amministrazione locale |

La scelta Tab/Shift+Tab è deliberata: funziona sugli elementi semanticamente focusabili anche nei siti esterni, dove non è possibile iniettare JavaScript. Il comportamento esatto di Home/Back dipende dai codici inviati dalla TV.

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
