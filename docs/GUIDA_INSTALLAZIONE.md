# Guida rapida di installazione su Raspberry Pi

Questa è la procedura consigliata per Raspberry Pi 3 Model B. Non richiede tastiera collegata alla TV: per lanciare il comando iniziale si usa SSH da un altro computer sulla LAN.

## 1. Occorrente

- Raspberry Pi 3 Model B.
- Alimentatore stabile da almeno 5 V / 2,5 A.
- MicroSD A1/A2 da almeno 16 GB.
- Cavo Ethernet per la prima installazione.
- TV collegata via HDMI con HDMI-CEC abilitato.
- Un computer Windows, macOS o Linux sulla stessa rete.

## 2. Preparare Raspberry Pi OS

1. Installare [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Inserire la microSD nel computer.
3. In Imager selezionare:
   - dispositivo: **Raspberry Pi 3**;
   - sistema operativo: **Raspberry Pi OS Lite (64-bit)**;
   - memoria: la microSD corretta.
4. Aprire le personalizzazioni di Imager e impostare:
   - hostname: `raspberrytv`;
   - nome utente e password a scelta;
   - SSH abilitato con autenticazione tramite password o chiave;
   - fuso orario e tastiera;
   - Wi-Fi facoltativo: per il primo avvio è preferibile Ethernet.
5. Scrivere la SD e rimuoverla in sicurezza.

## 3. Primo avvio

1. Inserire la SD nel Raspberry Pi.
2. Collegare HDMI alla TV.
3. Collegare Ethernet al router.
4. Collegare l'alimentazione.
5. Attendere circa due minuti.

Dal computer aprire PowerShell, Terminale o una shell e collegarsi con l'utente scelto in Imager:

```sh
ssh NOME_UTENTE@raspberrytv.local
```

Se `.local` non funziona, individuare l'indirizzo IP nella pagina dei dispositivi collegati del router:

```sh
ssh NOME_UTENTE@192.168.1.123
```

## 4. Installare RaspberryTV con un solo comando

Nel terminale SSH del Raspberry eseguire:

```sh
curl -fsSL https://raw.githubusercontent.com/stefano5885/RaspberryTV/main/scripts/bootstrap.sh | sudo sh
```

Lo script:

1. verifica modello e sistema operativo a 64 bit;
2. individua l'ultima release stabile GitHub;
3. scarica il repository;
4. installa Brave o il fallback Chromium, Xorg, Openbox, NetworkManager e libCEC;
5. crea i servizi `systemd`;
6. avvia applicazione web, browser kiosk e bridge CEC.

Sul Raspberry Pi 3 l'operazione può richiedere 10–20 minuti. Non togliere alimentazione e non chiudere la connessione finché compare “Installazione completata”.

### Variante più prudente

Se si preferisce ispezionare lo script prima di eseguirlo come root:

```sh
curl -fsSLO https://raw.githubusercontent.com/stefano5885/RaspberryTV/main/scripts/bootstrap.sh
less bootstrap.sh
sudo sh bootstrap.sh
```

## 5. Aprire la dashboard

Dal computer o telefono sulla LAN aprire:

```text
http://raspberrytv.local:8080
```

In alternativa usare l'indirizzo IP:

```text
http://192.168.1.123:8080
```

## 6. Configurazione iniziale

Nella dashboard:

1. inserire l'URL da mostrare e premere **Salva URL**;
2. configurare il Wi-Fi e verificare che compaia come connesso;
3. configurare Telegram, se necessario;
4. premere **Apri sito**;
5. provare frecce, OK, Back e Home del telecomando;
6. scollegare Ethernet soltanto dopo aver verificato il Wi-Fi.

Il repository degli aggiornamenti è già impostato su `https://github.com/stefano5885/RaspberryTV.git`.

## 7. Verificare l'installazione

Via SSH:

```sh
systemctl status raspberrytv-web raspberrytv-kiosk raspberrytv-cec
curl http://127.0.0.1:8080/api/health
```

La seconda istruzione deve restituire un JSON con `"ok": true`.

## 8. Aggiornare in seguito

Dalla dashboard:

1. premere **Controlla**;
2. verificare il tag proposto;
3. premere **Aggiorna applicazione**.

Il dispositivo installa soltanto tag stabili `vMAJOR.MINOR.PATCH`. Se il nuovo servizio non supera l'health check, viene riattivata automaticamente la release precedente.

## 9. Problemi comuni

- **`raspberrytv.local` non risponde:** usare l'IP indicato dal router.
- **SSH rifiutato:** controllare che SSH sia stato abilitato in Raspberry Pi Imager.
- **Errore architettura:** rifare la SD scegliendo Raspberry Pi OS Lite **64-bit**.
- **Installazione interrotta:** rilanciare lo stesso comando; lo script è progettato per essere ripetibile.
- **TV nera:** consultare [Troubleshooting](TROUBLESHOOTING.md) e i log del servizio kiosk.
- **Telecomando non funziona:** abilitare HDMI-CEC nelle impostazioni della TV e controllare `raspberrytv-cec`.

## 10. Sicurezza

- Non creare port forwarding verso la porta 8080.
- Usare il sistema soltanto su una LAN fidata: la dashboard non richiede password per requisito.
- Non pubblicare token Telegram, password Wi-Fi o chiavi SSH.
- Il comando `curl | sudo sh` deve essere usato soltanto con il repository ufficiale controllato. La variante con download e ispezione è preferibile negli ambienti più sensibili.
