#!/bin/sh
# Builds lua50 (a plain Lua 5.0 interpreter of the engine's own liblua, 32-bit static) in the m2-libs:check image -
# the dumps of build_server_lang.py (the stock quest tables) and the syntax check of the quests' .lua files.
set -eu
cd "$(dirname "$0")"
docker run --rm -v "$PWD":/w m2-libs:check sh -c "cd /w && gcc -m32 -static -O2 -I/src/Server/liblua/5.0/include lua.c /src/Server/liblua/5.0/lib/liblualib.a /src/Server/liblua/5.0/lib/liblua.a -o lua50 && chown $(id -u) lua50"
./lua50 /dev/null && echo "lua50 built"
