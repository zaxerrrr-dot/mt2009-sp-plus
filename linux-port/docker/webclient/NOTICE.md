# Web client - credits and licences

The browser game served by this service (the page, the WebAssembly engine port and its
compatibility layer, and the WebSocket -> TCP bridge in `bridge/`) is built on the web
client kit **Metin2-WebClient by nairoad** - https://github.com/nairoad/Metin2-WebClient -
licensed under the **GNU General Public License, version 2** (GPL-2.0). The adapted kit
(our engine source and the bridge) is kept with its licence text and history; the GPL-2.0
applies to it and to every modification we made.

`bridge/node_modules/ws` is the `ws` WebSocket library (MIT licence, see its LICENSE).

nginx (BSD-2-Clause) and Node.js (MIT) come from the base image.
