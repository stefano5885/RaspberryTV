# Troubleshooting

## Comandi diagnostici

```sh
systemctl status raspberrytv-web raspberrytv-kiosk raspberrytv-cec
journalctl -u raspberrytv-web -u raspberrytv-kiosk -u raspberrytv-cec --since today
curl http://127.0.0.1:8080/api/health
nmcli device status
echo scan | cec-client -s -d 1
```

I log sono limitati da journald a 100 MB persistenti e 14 giorni.

## La UI LAN non si apre

- Verificare l'IP nel router e provare `http://IP:8080` invece di `.local`.
- Controllare `raspberrytv-web.service` e che Ethernet sia `connected` in `nmcli`.
- Verificare che router/VLAN non isolino i client Wi-Fi e che la porta 8080 non sia filtrata.

## Schermo nero o browser assente

- Controllare `raspberrytv-kiosk.service` e `journalctl -u raspberrytv-kiosk`.
- Verificare `command -v brave-browser chromium-browser chromium`.
- Provare un URL leggero; il Pi 3 può esaurire RAM su siti molto pesanti.
- Se Brave è instabile, rimuoverlo temporaneamente: il launcher sceglierà Chromium al riavvio.

## Telecomando non rilevato

- Abilitare HDMI-CEC nelle impostazioni TV; il nome commerciale varia.
- Verificare che `/dev/cec0` o l'adattatore Raspberry Pi siano visibili a `cec-client`.
- Provare `echo scan | cec-client -s -d 1` e osservare `journalctl -fu raspberrytv-cec` mentre si premono i tasti.
- Alcune TV non inviano Back/Home. Adattare i nomi in `cec_bridge.py` dopo aver osservato l'output reale.
- Se il Pi non viene rilevato, provare `hdmi_force_hotplug=1` nella configurazione boot, come suggerito dalla documentazione libCEC.

## Le frecce non seguono la geometria della pagina

Per compatibilità con siti arbitrari, Su/Sinistra producono Shift+Tab e Giù/Destra producono Tab. L'ordine dipende dal DOM del sito. Correggere `tabindex`, semantica di link/pulsanti e focus sul sito sorgente quando possibile.

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
