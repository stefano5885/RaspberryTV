#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:0}"
openbox-session &
unclutter -idle 0.5 -root &
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

rm -f /var/lib/raspberrytv/browser-profile/SingletonLock \
    /var/lib/raspberrytv/browser-profile/SingletonCookie \
    /var/lib/raspberrytv/browser-profile/SingletonSocket

loading_page="file:///opt/raspberrytv/current/src/raspberrytv/web/loading.html"

exec "$browser" \
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
    "$loading_page"
