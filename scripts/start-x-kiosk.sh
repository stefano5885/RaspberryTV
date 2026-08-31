#!/bin/sh
set -eu
exec xinit /opt/raspberrytv/current/scripts/run-kiosk.sh -- :0 vt7 -nolisten tcp -nocursor -s 0 -dpms
