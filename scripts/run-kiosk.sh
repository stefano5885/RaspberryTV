#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:0}"
openbox-session &
unclutter -idle 0.5 -root &
if command -v xset >/dev/null 2>&1; then
    xset s off || true
    xset s noblank || true
    xset -dpms || true
fi
sleep 1
if command -v feh >/dev/null 2>&1; then
    feh --no-fehbg --bg-fill /opt/raspberrytv/current/assets/kiosk-offline.png || true
fi
/opt/raspberrytv/current/scripts/configure-browser-profile.py

browser=""
for candidate in brave-browser chromium-browser chromium; do
    if command -v "$candidate" >/dev/null 2>&1; then
        browser="$candidate"
        break
    fi
done

if [ -z "$browser" ]; then
    echo "Nessun browser compatibile installato" >&2
    exit 1
fi

loading_page="file:///opt/raspberrytv/current/src/raspberrytv/web/loading.html"

while :; do
    rm -f /var/lib/raspberrytv/browser-profile/SingletonLock \
        /var/lib/raspberrytv/browser-profile/SingletonCookie \
        /var/lib/raspberrytv/browser-profile/SingletonSocket
    "$browser" \
        --kiosk \
        --no-first-run \
        --no-default-browser-check \
        --disable-session-crashed-bubble \
        --disable-infobars \
        --disable-translate \
        --disable-features=Translate,MediaRouter,OptimizationHints,AutofillServerCommunication \
        --lang=it-IT \
        --autoplay-policy=no-user-gesture-required \
        --password-store=basic \
        --user-data-dir=/var/lib/raspberrytv/browser-profile \
        "$loading_page" || true
    echo "Browser chiuso: nuovo tentativo tra 3 secondi" >&2
    sleep 3
done
