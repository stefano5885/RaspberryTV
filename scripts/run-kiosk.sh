#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:0}"
openbox-session &
unclutter -idle 0.5 -root &

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

target=""
while [ -z "$target" ]; do
    target="$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/api/kiosk-target || true)"
    if [ -z "$target" ]; then sleep 2; fi
done

exec "$browser" \
    --kiosk \
    --no-first-run \
    --no-default-browser-check \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --disable-translate \
    --disable-features=Translate,MediaRouter,OptimizationHints,AutofillServerCommunication \
    --autoplay-policy=no-user-gesture-required \
    --password-store=basic \
    --user-data-dir=/var/lib/raspberrytv/browser-profile \
    "$target"
