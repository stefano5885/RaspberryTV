#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ] || [ "$#" -ne 1 ]; then
    echo "Uso: sudo ./scripts/prepare-sd.sh /percorso/rootfs-montata" >&2
    exit 1
fi

rootfs="$(readlink -f "$1")"
if [ "$rootfs" = "/" ] || [ ! -d "$rootfs/etc/systemd/system" ]; then
    echo "La destinazione non sembra una root filesystem Raspberry Pi valida" >&2
    exit 1
fi

source_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
bootstrap="$rootfs/opt/raspberrytv-bootstrap"
install -d -m 0755 "$bootstrap"
for entry in VERSION pyproject.toml README.md CHANGELOG.md assets src scripts config docs systemd; do
    cp -a "$source_dir/$entry" "$bootstrap/"
done
chmod 0755 "$bootstrap/scripts/install.sh"

install -m 0644 "$source_dir/systemd/raspberrytv-firstboot.service" \
    "$rootfs/etc/systemd/system/raspberrytv-firstboot.service"
install -d -m 0755 "$rootfs/etc/systemd/system/multi-user.target.wants"
ln -sfn ../raspberrytv-firstboot.service \
    "$rootfs/etc/systemd/system/multi-user.target.wants/raspberrytv-firstboot.service"

echo "SD predisposta. Al primo boot collegare Ethernet e attendere il provisioning automatico."
