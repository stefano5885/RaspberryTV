# RaspberryTV

Kiosk web minimale per Raspberry Pi 3 Model B, controllato dal telecomando TV via HDMI-CEC e amministrabile dalla LAN.

## Caratteristiche

- Una sola applicazione web locale per TV e browser LAN.
- Nessuna dipendenza Python runtime, database, container o build frontend.
- URL manuale o recuperato su richiesta dalla Telegram Bot API.
- Ethernet di fallback e configurazione Wi-Fi tramite NetworkManager.
- Brave ARM64 in kiosk; Chromium viene installato come fallback.
- `libCEC` + tastiera virtuale `uinput` per controllare anche siti esterni.
- Tag Git SemVer, release separate, attivazione con symlink e rollback.
- `systemd` per avvio e recovery di web, kiosk, CEC e updater one-shot.

## Documentazione

- [Guida rapida: installazione dal Raspberry Pi](docs/GUIDA_INSTALLAZIONE.md)
- [PRD](docs/PRD.md)
- [Architettura](docs/ARCHITECTURE.md)
- [Installazione e preparazione SD](docs/INSTALL.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Checklist hardware](docs/HARDWARE_TESTS.md)

## Installazione rapida sul Raspberry Pi

Dopo aver preparato Raspberry Pi OS Lite 64-bit con SSH ed Ethernet, collegarsi al Pi ed eseguire:

```sh
curl -fsSL https://raw.githubusercontent.com/stefano5885/RaspberryTV/main/scripts/bootstrap.sh | sudo sh
```

La procedura completa e la variante che consente di ispezionare prima lo script sono nella [guida di installazione](docs/GUIDA_INSTALLAZIONE.md).

## Avvio per sviluppo

Serve Python 3.11 o successivo. In una shell Linux/macOS:

```sh
export PYTHONPATH="$PWD/src"
export RASPBERRYTV_CONFIG_DIR="$PWD/.local/etc"
export RASPBERRYTV_STATE_DIR="$PWD/.local/state"
python3 -m raspberrytv
```

In PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$env:RASPBERRYTV_CONFIG_DIR = "$PWD/.local/etc"
$env:RASPBERRYTV_STATE_DIR = "$PWD/.local/state"
python -m raspberrytv
```

Aprire `http://127.0.0.1:8080`. Le azioni privilegiate (Wi-Fi, browser, update, reboot) funzionano soltanto sul Raspberry Pi installato.

## Test

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Pubblicazione release

1. Aggiornare `VERSION` e la versione in `pyproject.toml` allo stesso valore.
2. Eseguire i test.
3. Creare un tag stabile, ad esempio `v1.1.0`.
4. Pubblicare il tag nel repository configurato nel dispositivo.

Tag prerelease, branch e commit non taggati vengono ignorati dall'updater.

## Sicurezza operativa

L'interfaccia non ha autenticazione per requisito ed è destinata esclusivamente a una LAN fidata. Non pubblicare la porta 8080 su Internet. Token Telegram, deploy key e password Wi-Fi non devono essere aggiunti al repository. La deploy key per repository privati deve essere read-only.

## Stato della validazione

La logica applicativa è coperta da test automatici. Browser ARM64, codici CEC, Xorg e prestazioni del sito devono essere collaudati sul Raspberry Pi 3 e sulla TV reali seguendo la checklist hardware.
