# Updating

Nothing in this document touches your database. Accounts, characters, items,
guilds and safeboxes live in a Docker volume, and no step here goes near it.
The only command that would destroy them is `docker compose down -v`, and it
appears nowhere in this project.

There are two ways to update: by hand, which is the one to use, and from the
panel, which is off by default and which you should read the last section of
before switching on.

---

## Which version am I running?

Log into the admin panel. The version is at the bottom of every admin page, and
it is a link to the patch log — the changelog for the build you are running,
and, when there is a newer one, the changelog for that.

If it says **unknown**, this build has no `VERSION` file in it: a development
checkout, or an image built from a context that was staged by hand. The panel
will not guess a version and will not tell you that you are up to date when it
cannot know.

On the machine itself:

```sh
cat /var/cache/m2src/repo/VERSION      # what the checkout has
docker compose exec panel cat /opt/panel/VERSION   # what is actually running
```

Those two can differ: the first is what you would get, the second is what you
have.

---

## Updating by hand

On the server, as root (or with `sudo`). This is the whole thing — paste it in
one go:

```sh
REPO=/var/cache/m2src/repo
STACK=/opt/metin2/stack

git -C "$REPO" fetch --depth 1 origin main
git -C "$REPO" reset --hard FETCH_HEAD
sh "$REPO/linux-port/fetch-sources.sh" fetch
(cd "$REPO/linux-port/docker" && tar cf - .) | (cd "$STACK" && tar xf -)
cd "$STACK" && docker compose up -d --build
```

Those two paths are what `install.sh` uses. If you installed somewhere else,
use your own — `docker compose ls` shows where the stack lives.

What each line does:

1. **`git fetch` / `reset --hard`** — brings the checkout to the published
   version. The checkout is a copy of the repository; nothing local is ever
   committed into it, so there is nothing to merge and nothing to lose.
2. **`fetch-sources.sh fetch`** — re-stages the Docker build context from the
   refreshed checkout. It skips everything it has already done, so on an
   installed machine this takes seconds and downloads nothing: the upstream
   r40250 package is already in the cache.
3. **`tar`** — copies the new context over the installed stack. `tar` writes
   the files it carries and deletes nothing else, which is exactly why it is
   used here: your `.env` and your `docker-compose.override.yml` are not in the
   context, so they are not overwritten. Your passwords, ports and addresses
   survive.
4. **`docker compose up -d --build`** — rebuilds the images that changed and
   recreates the containers that changed. Anything unchanged is left running.

Players are disconnected while the game restarts. Most updates take two or
three minutes. An update that changes the Linux port itself recompiles the
game, which takes considerably longer — ten to forty minutes depending on the
machine. The panel's patch log tells you which kind you are getting before you
start.

### If the port patch changed

`fetch-sources.sh` reuses the patched source tree it staged last time. When an
update changes `linux-port/patches/*.patch`, that tree is stale and has to be
built again from the new patch:

```sh
sh "$REPO/linux-port/fetch-sources.sh" fetch --force restage
```

The panel's updater does this check itself. By hand, if you are unsure, running
it with `--force restage` is never wrong — only slower.

### If something goes wrong

Nothing is deleted at any point, so there is nothing to undo. The old images
are still on the machine until Docker prunes them, and the database was never
touched.

```sh
cd /opt/metin2/stack
docker compose ps                 # what is up
docker compose logs game --tail 80
docker compose logs panel --tail 40
```

To go back to a version that worked, check the old commit out and run the same
five lines again:

```sh
git -C /var/cache/m2src/repo fetch --depth 50 origin main
git -C /var/cache/m2src/repo checkout <commit>
```

---

## Updating from the panel

**This is off, and on a server other people can reach it should stay off.**
Read the trade-off at the end of this section before you switch it on.

### Turning it on

Two switches, both required, on purpose.

1. In `/opt/metin2/stack/.env`:

   ```
   M2_UPDATE_APPLY=1
   ```

2. Start the updater — it is in a compose profile, so `docker compose up -d`
   never starts it:

   ```sh
   cd /opt/metin2/stack
   docker compose --profile update up -d updater
   docker compose up -d panel          # picks up M2_UPDATE_APPLY
   ```

Check it is happy before you rely on it:

```sh
docker compose exec updater m2-updater selftest
```

That changes nothing. It reports whether it can see the Docker socket, the
checkout, and the installed stack, and it names whatever is missing.

An **Install it from here** button now appears on the panel's patch-log page —
but only while all three of these are true: the setting is on, the updater is
running, and there is actually a newer version. When the setting is on but the
updater is not running, the page says so and gives you the command, rather than
showing a button that would do nothing.

### Turning it off again

```sh
cd /opt/metin2/stack
docker compose stop updater && docker compose rm -f updater
# then set M2_UPDATE_APPLY=0 in .env and: docker compose up -d panel
```

### What it actually does

The panel cannot update anything. It writes a small file into a directory it
shares with the updater:

```
id=1754790000-31
version=1.2.0
time=1754790000
```

That is the entire message, and the updater reads exactly two things out of it:
the `id`, which is only used to tell a new request from one it has already
carried out, and the `version`, which it prints in the log and never acts on.
There is no field for a command, a path, a URL, a branch or an image name, and
nothing from that file is ever passed to a shell. A panel that has been
completely taken over can make the updater update the server, repeatedly — and
nothing else.

The updater then runs the same five steps as the manual procedure above, in the
same order, and writes its progress back into the shared directory so the panel
can show it. The script is
[`linux-port/docker/updater/bin/m2-updater`](linux-port/docker/updater/bin/m2-updater);
it is short enough to read in one sitting, and that is the point of it.

It never runs `docker compose down`, in any form. The word does not appear in
the file.

### The security trade-off, plainly

Updating means rebuilding images and recreating containers, and that needs the
host's Docker daemon. **Access to the Docker socket is root on the host** — not
"almost root", not "root in a container". Anything that can talk to it can
start a container with the host's entire filesystem mounted inside it and read
or change anything on the machine.

So the question is not whether that power is used — an update needs it — but
which process holds it.

- **The panel must not.** It is the one process here that faces the internet.
  It accepts registrations from strangers, serves a download, sends password
  reset links and renders HTML. Every one of those is an attack surface, and a
  bug in any of them would become a full host takeover the moment the panel
  holds the socket.
- **The updater may.** It is one shell script with one job. It has no network
  service, no port, no login, nothing that a stranger can reach and nothing to
  submit to it. The only way in is the request file, which cannot carry an
  instruction. If it is compromised, it is because the host already was.

That is the whole design, and it is why this feature is two containers rather
than four lines in the panel.

What you are accepting when you switch it on:

- **A container on your machine holds the Docker socket, permanently.** It is
  small and it is auditable, but it is there, and a hole in the Docker daemon
  or in that script is a hole in your host.
- **Whoever can log into the panel can restart your server.** That is the
  admin passphrase, and the rate limit on it. On a `--local` install, where the
  panel has no passphrase at all because it is reachable only from the machine
  itself, it means any program running on that computer can do it.
- **You are trusting the published repository.** The updater fetches what is on
  `main` and builds it. That is also true of updating by hand — the difference
  is that by hand you choose the moment and can read the patch log first.

If none of that is comfortable, leave it off. Updating by hand is one paste,
and it is the same five commands.

---

## What an update will never do

- Remove a volume, or run `docker compose down -v`.
- Touch your `.env` or your `docker-compose.override.yml`.
- Change your admin passphrase, your database password, or your Flask session
  secret. They are generated once, on first run, and are never regenerated.
- Delete a client build. `client.zip` is on its own volume and is left alone.

If an update ever needs you to do something by hand — move a setting, run a
command — it is a **MAJOR** version, and [CHANGELOG.md](CHANGELOG.md) says so
at the top of that release, in full, before anything else.

---

## Pliki klienta z edytora bazy danych – automatycznie przez patcher

(MT2009_PLUS_DBDATA_AUTO_V1) Po aktualizacji serwera, która zmienia przedmioty
w kliencie, albo po zmianach w edytorze bazy danych nie trzeba już rozsyłać
zipa z plikami klienta. Panel 7790 publikuje bez logowania tylko to, co i tak
jest w zipie:

- `GET /klient/dbdata/manifest.json` – wersja bazy klienta, znacznik
  (ten sam, który gra wysyła jako „DbDataStamp”), rozmiary i SHA-256
  `pack/dbdata.index` i `pack/dbdata.data`, treść `dbdata_stamp.txt`;
- `GET /klient/dbdata/<znacznik>/dbdata.index|dbdata.data` – sama paczka.

MT2009-Patcher sprawdza manifest serwera wybranego nad GRAJ po swojej zwykłej
aktualizacji i pobiera paczkę tylko wtedy, gdy różni się od tej w kliencie.
Gdzie szuka panelu: linia `panel=` w `coop.cfg`/`coop2.cfg` (port albo adres),
potem port 7790 tego serwera, port logowania + 6790 (bloki portów jak na
serwerach testowych) i port 80 (bramka, niżej). Na stałe można to ustawić w
`MT2009-Patcher.exe.config`: `DbDataManifest` (adresy oddzielone `;`, `{host}`
= adres serwera; `off` wyłącza).

Panel na 127.0.0.1 (domyślnie w launcherze Windows): patcher na tym samym
komputerze go widzi, znajomi z COOP – nie (dla nich zip jak dotąd albo bramka).
Serwer z zaporą, który wpuszcza graczy tylko na `/register` (serwer
wspierających): dodaj w bramce (nginx) przed panelem tylko tę ścieżkę, np.

```nginx
location ^~ /klient/dbdata/ {
    limit_except GET { deny all; }
    proxy_pass http://127.0.0.1:7790;   # panel 7790 (seban-panel:7789 w sieci dockera)
    proxy_set_header X-Real-IP $remote_addr;
}
```

na porcie 80 (patcher sprawdza go sam) albo na porcie bramki `/register` i
wpisz graczom `panel=<port bramki>` w `coop.cfg`. Reszta panelu zostaje
zamknięta. Wyłączenie publicznych ścieżek: `DBDATA_AUTO=0` w środowisku
kontenera seban-panel.

---

## Server settings (.env) from the advanced panel

The advanced panel's **Ustawienia → Ustawienia serwera (.env)** page
(`/advanced/server-env`, MT2009_PLUS_ENV_EDITOR_V1) shows every variable of
`linux-port/docker/.env` - described in Polish, grouped, searchable - and
changes them. The panel itself never writes `.env` and has no Docker socket:

1. the page leaves `env.request` (JSON: id + `KEY=value` changes) in the
   `update-spool` volume, after checking the values against
   `linux-port/docker/seban-panel/env_schema.py`;
2. the **updater** service (`update.sh watch`, the only container with the
   Docker socket) runs `linux-port/tools/env_apply.py`, which checks the
   request again against the same schema, refuses read-only keys (database
   passwords and user, the compose project name, the container prefix, host
   paths), backs `.env` up to `linux-port/docker/.env-backups/` (the last 10),
   rewrites only the named lines (comments and order stay; a key `.env` lacks
   is appended) and runs `docker compose up -d --no-deps --force-recreate` for exactly
   the services that read the changed keys. If compose fails, the backup is
   put back and compose runs again;
3. the result goes to `env.status`, which the page polls; `env.current` is the
   updater's snapshot of the values (secrets only as set / unset), refreshed
   at its start, after every change and once a minute.

The older `botcount.request` / `spawn-plan.request` of `/manage` go through
the same path now. Without a running updater (Windows, or a Linux server
that never started it) the page is read-only and says how to start it:

```sh
cd /opt/metin2/stack            # the folder with docker-compose.yml
docker compose --profile update up -d updater
```

`M2_UPDATE_WATCH_UPDATES=0` in `.env` (before starting it) keeps the updater
for the settings page alone: it never installs an update.

When a variable is added to `.env.example` or `docker-compose.yml`, describe
it in `env_schema.py` - `test_env_schema.py` fails until you do.

## Updating the updater

One wrinkle worth knowing about. The updater is in a compose profile that is
not active during the update it is running — which is deliberate, because
otherwise `docker compose up -d --build` would stop the very container running
the command, halfway through.

Since MT2009_PLUS_ENV_EDITOR_V1 the updater restarts itself once an update
that changed `linux-port/tools/update.sh` has finished (its container's restart
policy starts the new script), so a new request type such as the settings
page's reaches it without anybody touching the server. Only the image - the
tools inside it - stays as it was until you rebuild it:

```sh
cd /opt/metin2/stack
docker compose --profile update up -d --build updater
```

Worth doing after an update that mentions it in the changelog. Otherwise it
does not matter: the script has one job and it does not change often.
