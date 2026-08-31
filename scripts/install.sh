#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Eseguire come root: sudo ./scripts/install.sh" >&2
    exit 1
fi

source_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
first_boot=0
if [ "${1:-}" = "--first-boot" ]; then first_boot=1; fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates curl git openssh-client python3 sudo network-manager avahi-daemon \
    cec-utils xserver-xorg-core xserver-xorg-legacy xinit openbox unclutter

if [ "$(dpkg --print-architecture)" = "arm64" ]; then
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    curl -fsSLo /etc/apt/sources.list.d/brave-browser-release.sources \
        https://brave-browser-apt-release.s3.brave.com/brave-browser.sources
    apt-get update
    if ! apt-get install -y --no-install-recommends brave-browser; then
        echo "Brave non installabile: provo Chromium" >&2
        apt-get install -y --no-install-recommends chromium || apt-get install -y --no-install-recommends chromium-browser
    fi
else
    echo "Architettura non ARM64: uso Chromium come fallback" >&2
    apt-get install -y --no-install-recommends chromium || apt-get install -y --no-install-recommends chromium-browser
fi

if ! id raspberrytv >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash raspberrytv
fi
for group in audio video input render netdev; do
    if getent group "$group" >/dev/null 2>&1; then usermod -a -G "$group" raspberrytv; fi
done

version="$(tr -d '\r\n ' < "$source_dir/VERSION")"
release_dir="/opt/raspberrytv/releases/v$version"
install -d -o root -g root -m 0755 "$release_dir"
if [ "$source_dir" != "$release_dir" ]; then
    for entry in VERSION pyproject.toml README.md src scripts config docs systemd; do
        cp -a "$source_dir/$entry" "$release_dir/"
    done
fi
find "$release_dir/scripts" -type f -name '*.sh' -exec chmod 0755 {} \;
ln -sfn "$release_dir" /opt/raspberrytv/current

install -d -o raspberrytv -g raspberrytv -m 0750 /etc/raspberrytv /var/lib/raspberrytv
install -d -o root -g raspberrytv -m 0750 /etc/raspberrytv-git
install -d -o raspberrytv -g raspberrytv -m 0700 /var/lib/raspberrytv/browser-profile
if [ ! -f /etc/raspberrytv/config.json ]; then
    install -o raspberrytv -g raspberrytv -m 0600 "$source_dir/config/config.example.json" /etc/raspberrytv/config.json
fi
if [ ! -f /etc/raspberrytv/secrets.json ]; then
    printf '{}\n' > /etc/raspberrytv/secrets.json
    chown raspberrytv:raspberrytv /etc/raspberrytv/secrets.json
    chmod 0600 /etc/raspberrytv/secrets.json
fi

install -o root -g root -m 0755 "$source_dir/scripts/raspberrytv-control.py" /usr/local/sbin/raspberrytv-control
printf '%s\n' 'raspberrytv ALL=(root) NOPASSWD: /usr/local/sbin/raspberrytv-control *' > /etc/sudoers.d/raspberrytv
chmod 0440 /etc/sudoers.d/raspberrytv
visudo -cf /etc/sudoers.d/raspberrytv

install -d -m 0755 /etc/brave/policies/managed /etc/chromium/policies/managed
install -m 0644 "$source_dir/config/brave-policy.json" /etc/brave/policies/managed/raspberrytv.json
install -m 0644 "$source_dir/config/brave-policy.json" /etc/chromium/policies/managed/raspberrytv.json

install -m 0644 "$source_dir/systemd/raspberrytv-web.service" /etc/systemd/system/
install -m 0644 "$source_dir/systemd/raspberrytv-kiosk.service" /etc/systemd/system/
install -m 0644 "$source_dir/systemd/raspberrytv-cec.service" /etc/systemd/system/
install -m 0644 "$source_dir/systemd/raspberrytv-update.service" /etc/systemd/system/

printf '%s\n' 'uinput' > /etc/modules-load.d/raspberrytv.conf
modprobe uinput || true
printf '%s\n' 'allowed_users=anybody' 'needs_root_rights=yes' > /etc/X11/Xwrapper.config

install -d -m 0755 /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/raspberrytv.conf <<'EOF'
[Journal]
SystemMaxUse=100M
RuntimeMaxUse=50M
MaxRetentionSec=14day
EOF

systemctl daemon-reload
systemctl enable NetworkManager.service avahi-daemon.service
systemctl enable raspberrytv-web.service raspberrytv-kiosk.service raspberrytv-cec.service
systemctl set-default graphical.target
systemctl restart raspberrytv-web.service
systemctl restart raspberrytv-kiosk.service || true
systemctl restart raspberrytv-cec.service || true

if [ "$first_boot" -eq 1 ]; then
    systemctl disable raspberrytv-firstboot.service || true
fi

touch /var/lib/raspberrytv/installed
chown raspberrytv:raspberrytv /var/lib/raspberrytv/installed
echo "RaspberryTV $version installato e avviato."
