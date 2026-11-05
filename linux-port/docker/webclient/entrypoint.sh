#!/bin/sh
# MT2009_PLUS_WEBCLIENT_SERVICE_V1: the web client container - nginx (page + /to/), the
# WebSocket bridge, and the site's download into the volume. If nginx or the bridge
# stops, the container stops and Docker starts it again (restart: unless-stopped).
set -u
say() { printf 'webclient: %s\n' "$*"; }

if [ "${M2_WEBCLIENT_ON:-1}" != 1 ]; then
    say "off (M2_WEBCLIENT_ON=${M2_WEBCLIENT_ON:-}) - nothing is served; set M2_WEBCLIENT_ON=1 in .env to play in the browser"
    exec tail -f /dev/null
fi

node /opt/ywc/tools/bridge-config.js > /tmp/bridge.json || { say "bad settings - see above"; sleep 60; exit 1; }
mkdir -p /site/.ywc

node /opt/ywc/bridge/src/index.js /tmp/bridge.json &
BRIDGE=$!
L="${M2_DEFAULT_LANGUAGE:-pl}"; case "$L" in pl|en|de|tr|ro|es|it|fr|pt|cz|hu|gr|ae) ;; *) L=pl ;; esac
echo "return 302 client.html?deflang=$L;" > /tmp/ywc-root.conf
nginx -c /etc/ywc/nginx.conf -g 'daemon off;' &
NGINX=$!
say "page on port ${M2_WEBCLIENT_PORT:-7792} of this server${M2_PUBLIC_ADDRESS:+ (http://$M2_PUBLIC_ADDRESS:${M2_WEBCLIENT_PORT:-7792}/)}"

# The site: until it is the pinned release, try again - 1 min, doubling up to 30 min.
(
    delay=60
    until node /opt/ywc/tools/sync-site.js; do
        say "next attempt in $((delay / 60)) min"
        sleep "$delay"
        delay=$((delay * 2)); [ "$delay" -gt 1800 ] && delay=1800
    done
) &
SYNC=$!

trap 'kill "$BRIDGE" "$NGINX" "$SYNC" 2>/dev/null; wait; exit 0' TERM INT
while kill -0 "$BRIDGE" 2>/dev/null && kill -0 "$NGINX" 2>/dev/null; do
    sleep 5
done
say "nginx or the bridge stopped - restarting the container"
kill "$BRIDGE" "$NGINX" "$SYNC" 2>/dev/null
exit 1
