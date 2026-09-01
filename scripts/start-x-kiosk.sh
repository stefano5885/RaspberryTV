#!/bin/sh
set -eu
exec xinit /bin/sh /opt/raspberrytv/current/scripts/run-kiosk.sh -- :0 vt7 -nolisten tcp -s 0 -dpms
