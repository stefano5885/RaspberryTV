# Installazione e preparazione SD

Per la procedura più semplice basata sul repository GitHub pubblico, usare la [guida rapida](GUIDA_INSTALLAZIONE.md). Questo documento conserva anche i metodi manuale e pre-provisioning della SD.

## Hardware consigliato

- Raspberry Pi 3 Model B, alimentatore 5 V adeguato e microSD A1/A2 da almeno 16 GB.
- TV con HDMI-CEC abilitato (Anynet+, Simplink, Bravia Sync o nome equivalente).
- Ethernet per il primo avvio; mouse opzionale.

## Metodo A: installazione su Raspberry Pi OS già avviato

1. Con Raspberry Pi Imager scegliere Raspberry Pi 3 e **Raspberry Pi OS Lite 64-bit** stabile.
2. Nelle opzioni di Imager configurare hostname (ad esempio `raspberrytv`), utente amministrativo e, facoltativamente, SSH. Non serve configurare il Wi-Fi se si usa Ethernet.
3. Scrivere la SD, inserirla, collegare HDMI, Ethernet e alimentazione.
4. Clonare il repository sul Pi.
5. Eseguire una sola volta:

   ```sh
   git clone https://github.com/stefano5885/RaspberryTV.git
   cd RaspberryTV
   sudo ./scripts/install.sh
   sudo reboot
   ```

6. Aprire `http://raspberrytv.local:8080` oppure l'IP assegnato dal router.

Questo metodo usa SSH per la prima installazione; non richiede tastiera o terminale sulla TV.

## Metodo B: SD predisposta prima del primo boot

Questo metodo richiede un computer Linux o WSL capace di montare la partizione ext4 della SD.

1. Scrivere Raspberry Pi OS Lite 64-bit con Imager e impostare hostname/utente.
2. Reinserire e montare la partizione root della SD, ad esempio in `/media/pi-root`.
3. Dal repository eseguire:

   ```sh
   sudo ./scripts/prepare-sd.sh /media/pi-root
   ```

4. Smontare correttamente la SD, inserirla nel Pi e collegare Ethernet, HDMI e alimentazione.
5. Il primo boot installa pacchetti e servizi automaticamente. In base alla rete e alla SD può richiedere 10–20 minuti; lo stato è disponibile su console e in `journalctl -u raspberrytv-firstboot`.
6. Riavviare se l'installazione non lo ha già fatto, quindi aprire `http://raspberrytv.local:8080`.

Il primo boot richiede Internet via Ethernet per scaricare browser e pacchetti firmati. Per una distribuzione totalmente offline occorre produrre un'immagine derivata con i pacchetti già inclusi; non è compreso nella release iniziale.

## Configurazione iniziale dalla UI

1. Impostare e salvare l'URL pubblico.
2. Inserire SSID e password, poi verificare l'indirizzo Wi-Fi.
3. Configurare bot token, chat ID e topic ID opzionale.
4. Inviare al bot `URL https://example.com/percorso` e premere “Aggiorna URL da Telegram”.
5. Configurare il repository Git e verificare gli aggiornamenti.
6. Premere “Apri sito”, poi provare frecce, OK, Back e Home sul telecomando.
7. Scollegare Ethernet soltanto dopo aver verificato il Wi-Fi.

## Repository privato

Creare una deploy key SSH con accesso **sola lettura** e installare la chiave privata:

```sh
sudo install -o root -g raspberrytv -m 0640 deploy_key /etc/raspberrytv-git/deploy_key
```

Usare nella UI l'URL SSH del repository. Al primo collegamento l'host key viene accettata automaticamente; in ambienti ad alta sicurezza precompilare invece `known_hosts` e rimuovere `accept-new` dal codice.

## Configurazione firewall/router

Non creare port forwarding. Se si usa un firewall locale, consentire TCP 8080 soltanto dalle subnet LAN amministrative. L'app ascolta per default su tutte le interfacce locali perché Ethernet e Wi-Fi devono entrambe funzionare.

## Aggiornamenti di Raspberry Pi OS

Gli update applicativi non eseguono `apt upgrade`. Pianificare separatamente finestre di manutenzione per aggiornamenti di sicurezza e provare browser/CEC dopo ogni cambio di release principale del sistema operativo.
