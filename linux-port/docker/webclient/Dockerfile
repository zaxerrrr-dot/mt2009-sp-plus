# MT2009_PLUS_WEBCLIENT_SERVICE_V1: the web client - nginx serving the browser game,
# the WebSocket -> TCP bridge to this stack's game container, and the site's download
# into the volume (tools/sync-site.js, pinned by site-release.json). See the webclient
# service in ../docker-compose.yml.
FROM nginx:1.27-alpine
RUN apk add --no-cache nodejs \
 && rm -f /etc/nginx/conf.d/default.conf \
 && mkdir -p /site/.ywc /websrc \
 && chown -R nginx:nginx /site
COPY nginx/ /etc/ywc/
COPY bridge/ /opt/ywc/bridge/
COPY tools/ /opt/ywc/tools/
COPY www/ /opt/ywc/www/
COPY site-release.json NOTICE.md /opt/ywc/
COPY --chmod=755 entrypoint.sh /opt/ywc/entrypoint.sh
USER nginx
EXPOSE 8080
VOLUME ["/site"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/_ywc/health || exit 1
ENTRYPOINT ["/opt/ywc/entrypoint.sh"]
