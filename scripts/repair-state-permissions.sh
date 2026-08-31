#!/bin/sh
set -eu

state_dir="/var/lib/raspberrytv"
if ! id raspberrytv >/dev/null 2>&1; then
    exit 0
fi

install -d -o raspberrytv -g raspberrytv -m 0750 "$state_dir"
find "$state_dir" -maxdepth 1 -type f -name '*.json' \
    -exec chown raspberrytv:raspberrytv {} + \
    -exec chmod 0600 {} +
