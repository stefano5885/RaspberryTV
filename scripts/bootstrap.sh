#!/bin/sh
set -eu

repository_url="https://github.com/stefano5885/RaspberryTV.git"

if [ "$(id -u)" -ne 0 ]; then
    echo "Eseguire con sudo: curl ... | sudo sh" >&2
    exit 1
fi

architecture="$(dpkg --print-architecture 2>/dev/null || true)"
if [ "$architecture" != "arm64" ]; then
    echo "Errore: serve Raspberry Pi OS Lite 64-bit (architettura arm64)." >&2
    exit 1
fi

model="$(tr -d '\000' < /proc/device-tree/model 2>/dev/null || true)"
case "$model" in
    *"Raspberry Pi 3 Model B"*) ;;
    *)
        echo "Errore: hardware rilevato '$model'. Questo installer è destinato a Raspberry Pi 3 Model B." >&2
        exit 1
        ;;
esac

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates git

work_dir="$(mktemp -d /tmp/raspberrytv-bootstrap.XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT INT TERM

requested_ref="${RASPBERRYTV_REF:-}"
if [ -z "$requested_ref" ]; then
    requested_ref="$(
        git ls-remote --tags --refs "$repository_url" \
        | awk -F/ '$3 ~ /^v[0-9]+\.[0-9]+\.[0-9]+$/ {print $3}' \
        | sort -V \
        | tail -n 1
    )"
fi
if [ -z "$requested_ref" ]; then requested_ref="main"; fi

echo "Installazione RaspberryTV dalla release $requested_ref..."
git clone --depth 1 --branch "$requested_ref" "$repository_url" "$work_dir/RaspberryTV"
chmod 0755 "$work_dir/RaspberryTV/scripts/install.sh"
"$work_dir/RaspberryTV/scripts/install.sh"

echo
echo "Installazione completata."
echo "Apri http://raspberrytv.local:8080 oppure l'indirizzo IP mostrato dal router."
