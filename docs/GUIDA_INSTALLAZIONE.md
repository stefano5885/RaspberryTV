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
   - sistema operativo: **Raspberry Pi OS (64-bit)**. L'edizione completa con desktop è supportata; se Lite 64-bit è disponibile, rimane la scelta più leggera;
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
5. se è presente il desktop completo, disabilita il relativo display manager per evitare conflitti con il kiosk dedicato;
6. configura Brave Shields su **Aggressive** e disabilita banner P3A, usage ping, Web Discovery e traduzione;
7. crea i servizi `systemd`;
8. avvia applicazione web, schermata di caricamento, browser kiosk e bridge CEC.

Brave non interrompe il kiosk con la pagina “This site may attempt to track you across other sites”: l'apertura del documento principale viene consentita automaticamente, ma gli Shields restano su **Aggressivo** e continuano a bloccare le connessioni pubblicitarie e di tracciamento incorporate nella pagina.

Durante l'installazione vengono inoltre disabilitati salvaschermo e standby software dell'uscita video. Il Raspberry resta acceso quando la TV viene spenta: in questo modo può ricevere il successivo evento CEC, riaprire il browser e richiamare automaticamente l'ingresso HDMI corretto.

La sessione kiosk non usa il pannello né le icone del desktop Raspberry Pi. Prima del browser viene applicato un wallpaper tecnico “Kiosk non avviato”, che rimane visibile se Brave si chiude e durante i tre secondi precedenti il tentativo automatico di riapertura.

Se disponibile per la release di Raspberry Pi OS installata, il bootstrap configura anche lo splash iniziale fullscreen RaspberryTV con il pacchetto ufficiale `rpi-splash-screen-support`. Lo splash standard Plymouth e il riquadro arcobaleno del firmware vengono disabilitati, così non ricompaiono dopo l'immagine personalizzata. Un monitor senza HDMI-CEC è supportato: rimangono escluse soltanto le funzioni telecomando e sincronizzazione accensione TV.

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

La sezione **Telecomando CEC** mostra in tempo quasi reale ciò che il Raspberry riceve. Se un tasto compare come “non associato”, premere **Associa ultimo** accanto all'azione desiderata e poi **Salva mappatura**. Il pulsante **Riavvia bridge** consente di riprovare l'inizializzazione senza riavviare tutto il Raspberry.

Nella stessa sezione si può scegliere:

- **Focus:** le frecce passano tra link e pulsanti; è la modalità iniziale.
- **Puntatore:** le frecce muovono il mouse e OK esegue un clic; è utile per siti non ottimizzati per tastiera.

Rosso, verde, giallo e blu possono essere configurati come scorciatoie per Dashboard/Home, apertura del sito, ricarica, indietro o nessuna azione. Lo standard HDMI-CEC identifica F1 come blu, F2 rosso, F3 verde e F4 giallo; se il telecomando usa nomi diversi, premere il tasto fisico e usare **Associa ultimo** sulla riga del colore corretto.

Il riquadro **Termica** mostra la temperatura e il throttling. “Attivo” richiede attenzione immediata a raffreddamento o alimentatore; “storico” indica che il problema si è verificato dall'accensione anche se ora non è presente.

### Verificare l'accelerazione di Brave dalla dashboard

Nel modulo **Test Brave sul monitor** sono disponibili tre comandi:

1. **Apri GPU Report:** nella sezione “Graphics Feature Status” verificare se Compositing, Rasterization e WebGL risultano hardware accelerated.
2. **Apri Media Internals:** avviare prima un video sul sito, quindi premere il comando dalla dashboard LAN. Nel player cercare `video_decoder`: `GpuVideoDecoder` indica decodifica hardware, `FFmpegVideoDecoder` decodifica software.
3. **Apri Version Info:** mostra build Brave/Chromium, sistema e parametri di avvio realmente usati.

I report si aprono in una nuova scheda sul monitor collegato al Raspberry. Il campo URL non viene cambiato. Premere **Torna al sito** per chiudere la diagnostica e riavviare il kiosk sulla destinazione configurata.

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
- **Errore architettura:** rifare la SD scegliendo Raspberry Pi OS **64-bit**.
- **Schermo nero con cursore:** rilanciare il bootstrap per installare la release correttiva più recente; il desktop completo deve essere disabilitato in favore della sessione kiosk.
- **Compare lo splash standard o l'elenco dei servizi `[ OK ]`:** installare almeno la versione 0.3.4 dalla dashboard e riavviare; la correzione viene applicata automaticamente all'avvio del kiosk.
- **Installazione interrotta:** rilanciare lo stesso comando; lo script è progettato per essere ripetibile.
- **TV nera:** consultare [Troubleshooting](TROUBLESHOOTING.md) e i log del servizio kiosk.
- **Telecomando non funziona:** aprire il pannello **Telecomando CEC**. Se non appare alcun tasto, verificare HDMI-CEC sulla TV e l'errore mostrato; se il tasto appare come non associato, mapparlo dalla stessa pagina.
- **Frecce scomode sul sito:** provare la modalità **Puntatore**; la modifica viene applicata subito.
- **Termica segnala sottotensione:** usare un alimentatore stabile e un cavo corto di buona qualità; il flag storico può restare visibile fino a un ciclo di alimentazione.
- **La TV non riapre il kiosk:** controllare che l'avvio automatico dei dispositivi e il cambio sorgente siano consentiti nelle impostazioni CEC della TV; alcuni produttori espongono opzioni separate.

## 10. Sicurezza

- Non creare port forwarding verso la porta 8080.
- Usare il sistema soltanto su una LAN fidata: la dashboard non richiede password per requisito.
- Non pubblicare token Telegram, password Wi-Fi o chiavi SSH.
- Il comando `curl | sudo sh` deve essere usato soltanto con il repository ufficiale controllato. La variante con download e ispezione è preferibile negli ambienti più sensibili.
