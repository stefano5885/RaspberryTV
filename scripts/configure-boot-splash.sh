#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "La configurazione dello splash richiede root" >&2
    exit 1
fi

asset="${1:-/opt/raspberrytv/current/assets/boot-splash.tga}"
if [ ! -f "$asset" ]; then
    echo "Immagine splash RaspberryTV non trovata: $asset" >&2
    exit 0
fi

# configure-splash installa il logo fullscreen nell'initramfs. Il confronto evita
# di rigenerarlo a ogni semplice riavvio del browser kiosk.
cmdline=/boot/firmware/cmdline.txt
[ -f "$cmdline" ] || cmdline=/boot/cmdline.txt
needs_configure=0
if [ ! -f /lib/firmware/logo.tga ] || ! cmp -s "$asset" /lib/firmware/logo.tga; then
    needs_configure=1
elif [ ! -f "$cmdline" ] || ! grep -q 'fullscreen_logo=1' "$cmdline"; then
    needs_configure=1
fi

if command -v configure-splash >/dev/null 2>&1; then
    if [ "$needs_configure" -eq 1 ]; then
        echo "Configuro lo splash iniziale RaspberryTV..."
        configure-splash "$asset"
    fi
else
    echo "rpi-splash-screen-support non disponibile; salto lo splash iniziale" >&2
fi

# Raspberry Pi OS può mostrare Plymouth dopo il logo iniziale. Lo disattiviamo
# affinché non ricompaia lo splash Raspberry Pi standard.
if command -v raspi-config >/dev/null 2>&1 && raspi-config nonint do_boot_splash 1; then
    :
else
    if [ -f "$cmdline" ]; then
        sed -i -e 's/ quiet//g' -e 's/ splash//g' \
            -e 's/ plymouth.ignore-serial-consoles//g' "$cmdline"
    fi
fi

# configure-splash e raspi-config rimuovono "quiet". Senza questi parametri
# systemd stampa i servizi [ OK ] sulla console e copre il logo fullscreen.
# Manteniamo Plymouth disattivato (nessun token "splash"), ma rendiamo il boot
# davvero silenzioso e impediamo lo spegnimento della console.
if [ -f "$cmdline" ]; then
    boot_args="$(tr '\r\n' '  ' < "$cmdline")"
    for key in quiet loglevel systemd.show_status rd.systemd.show_status udev.log_level consoleblank; do
        boot_args="$(printf '%s\n' "$boot_args" | sed -E "s/(^|[[:space:]])${key}(=[^[:space:]]*)?([[:space:]]|$)/ /g")"
    done
    boot_args="$(printf '%s\n' "$boot_args" | tr -s ' ' | sed -E 's/^ +| +$//g')"
    printf '%s\n' "$boot_args quiet loglevel=3 systemd.show_status=false rd.systemd.show_status=false udev.log_level=3 consoleblank=0" > "$cmdline"
fi

# Nasconde anche il breve riquadro arcobaleno del firmware, che è indipendente
# sia dal logo fullscreen sia da Plymouth.
config=/boot/firmware/config.txt
[ -f "$config" ] || config=/boot/config.txt
if [ -f "$config" ]; then
    if grep -q '^[#[:space:]]*disable_splash=' "$config"; then
        sed -i 's/^[#[:space:]]*disable_splash=.*/disable_splash=1/' "$config"
    else
        printf '\n# RaspberryTV: nasconde lo splash firmware standard\ndisable_splash=1\n' >> "$config"
    fi
fi
