# Checklist di collaudo hardware

Compilare su Raspberry Pi 3 Model B e sulla TV destinata all'uso.

## SD, boot e recovery

- [ ] SD predisposta avvia il provisioning senza tastiera.
- [ ] UI LAN disponibile entro il tempo obiettivo.
- [ ] Con URL valido il kiosk parte automaticamente.
- [ ] Senza URL appare la dashboard.
- [ ] Dopo reboot completo torna al kiosk.
- [ ] Durante il boot compare soltanto lo splash RaspberryTV, senza Plymouth standard, riquadro arcobaleno, righe `[ OK ]` o altro testo della console sovrapposto.
- [ ] Su monitor senza HDMI-CEC il kiosk parte normalmente; solo telecomando e ciclo alimentazione restano indisponibili.
- [ ] Chiudendo Brave manualmente compare il wallpaper “Kiosk non avviato” senza barra, cestino o icone, poi il browser riparte entro 5 secondi.
- [ ] Interruzione alimentazione non corrompe configurazione o stato.

## Rete

- [ ] Ethernet ottiene DHCP ed espone la UI.
- [ ] Wi-Fi configurabile dalla UI senza mostrare nuovamente la password.
- [ ] Dopo rimozione Ethernet la UI e Internet funzionano via Wi-Fi.
- [ ] Dopo perdita Wi-Fi, ricollegando Ethernet la UI torna raggiungibile.
- [ ] Reboot con entrambe le interfacce mantiene configurazione e raggiungibilità.

## HDMI, browser e prestazioni

- [ ] Risoluzione e overscan corretti sulla TV.
- [ ] Brave ARM64 parte fullscreen senza first-run, popup o notifiche.
- [ ] Il boot mostra la schermata tecnica di attesa e apre automaticamente l'URL senza intervento LAN.
- [ ] Su immagine OS completa il vecchio desktop non compete con la sessione kiosk.
- [ ] Nessun banner P3A/lingua compare nella parte alta di Brave.
- [ ] Shields mostra “Sistemi di tracciamento e annunci” su Aggressive.
- [ ] Dashboard mostra valori plausibili di CPU, temperatura e RAM.
- [ ] Se Brave fallisce, Chromium fallback mantiene le funzioni.
- [ ] Il sito reale carica e resta fluido per almeno 4 ore.
- [ ] Crash forzato del browser viene recuperato da systemd.
- [ ] Cambio URL e “Apri sito” non richiedono reboot del Pi.

## HDMI-CEC

- [ ] A TV accesa per almeno 30 minuti il segnale non entra in standby e non compare uno schermo nero.
- [ ] Spegnendo la TV, Brave e la sessione Xorg vengono chiusi entro 20 secondi.
- [ ] Riaccendendo la TV, il kiosk riparte e l'ingresso HDMI del Raspberry viene selezionato automaticamente.
- [ ] Il cambio ingresso non viene ripetuto durante il normale utilizzo a TV accesa.

- [ ] TV rileva RaspberryTV come dispositivo playback.
- [ ] Giù/Destra spostano il focus avanti nel sito reale.
- [ ] Su/Sinistra spostano il focus indietro.
- [ ] OK attiva link e pulsanti.
- [ ] Back torna alla pagina precedente.
- [ ] Home/Root menu torna alla dashboard.
- [ ] Comportamento verificato dopo spegnimento/riaccensione TV.
- [ ] Eventuali codici specifici della TV sono documentati.
- [ ] Dashboard CEC passa a “In ascolto” e mostra ogni tasto entro due secondi.
- [ ] Un tasto sconosciuto compare come “non associato” e può essere mappato con “Associa ultimo”.
- [ ] “Riavvia bridge” ripristina il listener senza riavviare il Raspberry.
- [ ] Il registro non supera 100 eventi e non contiene segreti.

## Telegram

- [ ] Token non appare in API, UI o log.
- [ ] Chat diversa viene ignorata.
- [ ] Topic diverso viene ignorato.
- [ ] URL non valido non sostituisce quello attivo.
- [ ] Ultimo nuovo URL valido viene salvato con timestamp.
- [ ] Indisponibilità Telegram produce errore recuperabile senza bloccare il kiosk.

## Aggiornamento e rollback

- [ ] “Controlla” trova l'ultimo tag SemVer stabile.
- [ ] Prerelease e branch sono ignorati.
- [ ] Update riavvia servizi e mostra la nuova versione.
- [ ] URL, Wi-Fi e Telegram restano invariati.
- [ ] Release volutamente guasta fallisce health check e ripristina la precedente.
- [ ] Rollback manuale ripristina la release indicata.
- [ ] Due richieste concorrenti non avviano due updater.

## Sicurezza e risorse

- [ ] Porta 8080 non è pubblicata verso Internet.
- [ ] File segreti hanno permessi previsti.
- [ ] Deploy key è read-only e non compare nei log.
- [ ] Journald resta entro i limiti configurati.
- [ ] RAM, CPU, temperatura e spazio SD sono accettabili dopo 4 ore.
