# Troubleshooting

## Comandi diagnostici

```sh
systemctl status raspberrytv-web raspberrytv-kiosk raspberrytv-cec
journalctl -u raspberrytv-web -u raspberrytv-kiosk -u raspberrytv-cec --since today
curl http://127.0.0.1:8080/api/health
nmcli device status
echo scan | cec-client -s -d 1
```

Se dopo un aggiornamento il portale segnala che non può leggere `release-state.json`, installare la release `0.3.1` o successiva. Il servizio web ripara automaticamente proprietario e permessi dei file JSON in `/var/lib/raspberrytv` prima di ogni avvio; URL, Wi-Fi e configurazione Telegram non vengono cancellati.

Riparazione immediata per una `0.3.0` già bloccata:

```bash
sudo chown raspberrytv:raspberrytv /var/lib/raspberrytv/*.json
sudo chmod 600 /var/lib/raspberrytv/*.json
sudo systemctl restart raspberrytv-web raspberrytv-kiosk raspberrytv-cec
```

Se `raspberrytv-kiosk` termina con `status=203/EXEC` e `Permission denied`, la release è stata estratta da Git senza bit eseguibili. Riparazione immediata:

```bash
sudo find /opt/raspberrytv/current/scripts -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod 755 {} +
sudo systemctl restart raspberrytv-kiosk
```

La correzione permanente è inclusa dalla release `0.3.2`.

I log sono limitati da journald a 100 MB persistenti e 14 giorni.

## La UI LAN non si apre

- Verificare l'IP nel router e provare `http://IP:8080` invece di `.local`.
- Controllare `raspberrytv-web.service` e che Ethernet sia `connected` in `nmcli`.
- Verificare che router/VLAN non isolino i client Wi-Fi e che la porta 8080 non sia filtrata.

## Schermo nero o browser assente

- Se era installato Raspberry Pi OS completo e si vede solo un cursore, aggiornare alla release `v0.2.0` o successiva rilanciando il bootstrap: il display manager del desktop e il kiosk non devono usare contemporaneamente lo schermo.
- Controllare `raspberrytv-kiosk.service` e `journalctl -u raspberrytv-kiosk`.
- Verificare `command -v brave-browser chromium-browser chromium`.
- Provare un URL leggero; il Pi 3 può esaurire RAM su siti molto pesanti.
- Se Brave è instabile, rimuoverlo temporaneamente: il launcher sceglierà Chromium al riavvio.

## Banner Brave o Shields non Aggressive

- Verificare in `brave://policy` che `BraveP3AEnabled=false`, `BraveStatsPingEnabled=false` e `DefaultBraveAdblockSetting=2` siano applicate.
- In `brave://settings/shields`, “Sistemi di tracciamento e annunci” deve risultare su **Aggressive**.
- Rilanciare il bootstrap se il profilo era stato creato con una release precedente; la configurazione viene applicata prima di ogni avvio kiosk.

## Telecomando non rilevato

- Abilitare HDMI-CEC nelle impostazioni TV; il nome commerciale varia.
- Verificare che `/dev/cec0` o l'adattatore Raspberry Pi siano visibili a `cec-client`.
- Provare `echo scan | cec-client -s -d 1` e osservare `journalctl -fu raspberrytv-cec` mentre si premono i tasti.
- Dalla versione 0.4.0 usare prima il pannello **Telecomando CEC** della dashboard: aggiorna ogni secondo e distingue bridge non disponibile, tasto ricevuto e tasto non associato.
- Per codici specifici della TV, premere il tasto, verificare il nome in **Ultimo segnale**, selezionare **Associa ultimo** sull'azione desiderata e salvare.
- Alcune TV non inviano Back/Home. Adattare i nomi in `cec_bridge.py` dopo aver osservato l'output reale.
- Se il Pi non viene rilevato, provare `hdmi_force_hotplug=1` nella configurazione boot, come suggerito dalla documentazione libCEC.
- Se il pannello va in standby mentre la TV è accesa, verificare nei log del kiosk che `xset` sia disponibile e controllare `xset q` con `DISPLAY=:0`: Screen Saver deve essere disabilitato e DPMS deve risultare Disabled.
- Se il browser non segue accensione e spegnimento, osservare `journalctl -fu raspberrytv-cec`: devono comparire `Stato alimentazione TV: accesa/spenta`. Alcune TV richiedono di abilitare separatamente controllo alimentazione e selezione automatica sorgente.

## Le frecce non seguono la geometria della pagina

In modalità **Focus**, Su/Sinistra producono Shift+Tab e Giù/Destra producono Tab: l'ordine dipende dal DOM del sito. Se la pagina non è ben navigabile da tastiera, selezionare **Puntatore** nel pannello CEC; le frecce muoveranno il mouse e OK farà clic. La modifica è immediata.

Se il mouse si muove ma il cursore resta invisibile, installare la release `v0.6.1` o successiva. Il cursore viene nascosto automaticamente dopo 0,5 secondi di inattività, ma deve ricomparire alla prima pressione di una freccia.

Se un tasto colorato non esegue l'azione prevista, premerlo e leggere **Ultimo segnale**. HDMI-CEC usa normalmente F1=blu, F2=rosso, F3=verde e F4=giallo, ma il produttore può inviare un nome diverso: usare **Associa ultimo** sulla riga del colore fisico e salvare.

## Temperatura o throttling anomali

- **Attivo ora:** controllare ventilazione e alimentatore. Sottotensione e temperatura possono ridurre immediatamente la frequenza.
- **Storico:** l'anomalia si è verificata dopo l'accensione ma non è necessariamente presente adesso; il codice esadecimale resta mostrato per diagnosi.
- **N/D:** `vcgencmd` non è disponibile. Su Raspberry Pi OS verificare `command -v vcgencmd`; la temperatura può comunque continuare a essere letta da `/sys`.

Per confermare via SSH:

```sh
vcgencmd get_throttled
cat /sys/class/thermal/thermal_zone0/temp
```

## Verificare accelerazione GPU e video senza tastiera

Dalla dashboard LAN usare **Test Brave sul monitor → Apri GPU Report**. “Hardware accelerated” conferma la GPU per quella funzione; “Software only” o “Disabled” indica il percorso CPU. Per la decodifica video, lasciare un video in riproduzione e aprire **Media Internals** dalla LAN: `GpuVideoDecoder` è hardware, `FFmpegVideoDecoder` è software.

Se compare “Comando di sistema non disponibile”, installare `v0.6.2` o successiva: le release precedenti attendevano erroneamente la conclusione del processo Brave fino al timeout HTTP. Se la nuova versione non apre la scheda, verificare che il kiosk sia attivo e leggere `journalctl -u raspberrytv-kiosk`. Il worker si collega al profilo del browser già avviato e non crea una sessione grafica indipendente. Usare **Torna al sito** per ripristinare la pagina normale.

## Telegram non trova messaggi

- Il bot deve essere presente nella chat e poter ricevere i messaggi.
- Verificare chat ID e topic ID; il token non viene mostrato di nuovo dalla UI.
- `getUpdates` restituisce update disponibili, non offre ricerca completa della cronologia. Inviare un nuovo messaggio dopo la configurazione.
- Un webhook configurato altrove impedisce `getUpdates`; rimuoverlo dal bot.

## Update fallito

- Leggere `journalctl -u raspberrytv-update` e lo stato mostrato nella dashboard.
- Verificare che il tag sia `vMAJOR.MINOR.PATCH`, senza suffissi.
- Per repository privati verificare permessi e accesso read-only della deploy key.
- Se il nuovo servizio non risponde con la versione attesa, l'updater ripristina automaticamente il symlink precedente.
- Il rollback manuale è abilitato soltanto quando `release-state.json` contiene una release precedente valida.

## Recupero estremo

Collegare Ethernet, usare SSH e ripristinare il symlink `/opt/raspberrytv/current` a una directory valida in `/opt/raspberrytv/releases`, poi riavviare i servizi. Non modificare o cancellare `/etc/raspberrytv` e `/var/lib/raspberrytv`.
