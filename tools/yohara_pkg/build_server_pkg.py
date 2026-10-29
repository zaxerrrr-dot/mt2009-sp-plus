#!/usr/bin/env python3
"""Yohara (3.x) test server package: the full install zip and the server patch
from the previous full package (MT2009_PLUS_YOHARA_PKG_V1).

    python3 tools/yohara_pkg/build_server_pkg.py --version 3.0.3 --prev-version 3.0.2 \
        --client-version 3.0.3 --changelog CHANGELOG-YOHARA-3.0.3.md

What goes in (the way 3.0.0-3.0.2 were made, written down):
  * every file git tracks at --ref, without the repository-only trees
    (client-patches, server-patches, releases, .github, tests, mods-incoming,
    tools except New-M2UpdatePackage.ps1, client-files.json, test_update_serwer.txt);
  * the files git does not carry (.gitignore: engine source, extern, serverfiles,
    SQL dumps, the panels' pictures) from the test tree, which yohara-deploy.sh
    patched with every server-patches/* in its order - the patches are run once
    more here on the copy (an already applied edit is skipped) and their output
    is printed;
  * the Yohara package edits (mt2009-yohara-pkg-no-updates): no GitHub, no mirror,
    no update.sh download, the launcher reads only the package's own manifest and
    never runs MT2009-Patcher.exe;
  * VERSION <v>-test, CLIENT_VERSION, update-manifest-mt2009.json (channel
    yohara-test, no URL), INSTRUKCJA-YOHARA-TEST.txt, .m2launcher-rebuild-pending,
    CHANGELOG-YOHARA-<v>.md.
The patch zip holds every file of the new package that is new or differs from
the previous full package, plus LATKA-<v>-INSTRUKCJA.txt.
"""
import argparse
import datetime
import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import sys

REPO_ONLY = ('client-patches/', 'server-patches/', 'releases/', '.github/', 'tests/', 'mods-incoming/')
REPO_ONLY_FILES = ('client-files.json', 'test_update_serwer.txt')
TOOLS_KEEP = ('tools/New-M2UpdatePackage.ps1',)
# .gitignore'd trees the build needs, taken from the test tree.
IGNORED_TREES = (
    'linux-port/docker/game/src/server',
    'linux-port/docker/game/src/extern',
    'linux-port/docker/game/src/extern-tarballs',
    'linux-port/docker/game/src/serverfiles',
    'linux-port/docker/mariadb/initdb.d/dumps',
    'linux-port/docker/panel/app/static',
    'linux-port/docker/seban-panel/static/icons',
)
SKIP_SUFFIX = ('.orig', '.rej', '.pyc')
MARK = 'MT2009_PLUS_YOHARA_TEST_NO_UPDATES'


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def edit(root, rel, old, new):
    path = os.path.join(root, rel)
    with open(path, 'rb') as f:
        data = f.read()
    o, n = old.encode('utf-8'), new.encode('utf-8')
    if b'\r\n' in data:
        o, n = o.replace(b'\n', b'\r\n'), n.replace(b'\n', b'\r\n')
    if data.count(o) != 1:
        raise SystemExit('edit %s: expected once, found %d: %r' % (rel, data.count(o), old[:80]))
    with open(path, 'wb') as f:
        f.write(data.replace(o, n))


def no_update_edits(root, v):
    tag = '%s-test' % v
    edit(root, 'linux-port/tools/update.sh',
         'MIRROR_BASES=${M2_UPDATE_MIRROR-http://141.94.100.53/aktualizacje/}',
         'MIRROR_BASES=${M2_UPDATE_MIRROR-}  # %s' % MARK)
    edit(root, 'linux-port/tools/update.sh', 'run_update() {\n',
         'run_update() {\n'
         '    # %s: paczka testowa Yohara %s\n'
         '    if [ "${M2_YOHARA_ALLOW_UPDATE:-0}" != 1 ]; then\n'
         '        say "Aktualizacje sa wylaczone w paczce testowej Yohara %s - nic nie pobieram i nic nie instaluje."\n'
         '        return 0\n'
         '    fi\n' % (MARK, tag, tag))
    edit(root, 'linux-port/tools/update.sh', '    check) check_tree; fetch_manifest',
         '    check) if [ "${M2_YOHARA_ALLOW_UPDATE:-0}" != 1 ]; then say "Aktualizacje sa wylaczone w paczce testowej '
         'Yohara %s."; exit 0; fi; check_tree; fetch_manifest' % tag)
    edit(root, 'instaluj-vps.sh', '\nUPDATE=1\n',
         '\nUPDATE=0  # %s: paczka testowa Yohara - bez aktualizacji\n' % MARK)
    edit(root, 'instaluj-vps.sh', 'MIRROR=${M2_UPDATE_MIRROR-http://141.94.100.53/aktualizacje/}',
         'MIRROR=${M2_UPDATE_MIRROR-}  # %s' % MARK)
    edit(root, 'launcher/launcher.config.example.json',
         '"manifestUrl": "https://raw.githubusercontent.com/zaxerrrr-dot/mt2009-sp-plus/main/update-manifest-mt2009.json"',
         '"manifestUrl": ""')
    edit(root, 'launcher/Metin2Launcher.psm1',
         '$script:M2_MOD_MANIFEST_URL = "https://raw.githubusercontent.com/$($script:M2_MOD_REPOSITORY)/main/update-manifest-mt2009.json"',
         '# %s: paczka testowa Yohara - manifest lokalny, bez GitHuba i serwera zapasowego.\n'
         "$script:M2_MOD_MANIFEST_URL = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $PSScriptRoot) 'update-manifest-mt2009.json'))"
         % MARK)
    edit(root, 'launcher/Metin2Launcher.psm1',
         "$script:M2_UPDATE_MIRROR_BASE = 'http://141.94.100.53/aktualizacje/'",
         "$script:M2_UPDATE_MIRROR_BASE = ''  # %s" % MARK)
    # A launcher.config.json saved by 3.0.1/3.0.2 holds the GitHub manifest
    # (update-manifest-mt2009.json is not "foreign" to the 2.x test): every
    # address but the package's own file is replaced by it.
    edit(root, 'launcher/Metin2Launcher.psm1',
         '    param([AllowEmptyString()][string]$Url)\n    if ([string]::IsNullOrWhiteSpace($Url)) { return $true }\n',
         '    param([AllowEmptyString()][string]$Url)\n'
         '    # %s: tylko lokalny manifest paczki - adres z GitHuba (zapisany przez 3.0.1/3.0.2) jest zastepowany.\n'
         '    if (-not [string]::Equals($Url, $script:M2_MOD_MANIFEST_URL, [StringComparison]::OrdinalIgnoreCase)) { return $true }\n'
         '    if ([string]::IsNullOrWhiteSpace($Url)) { return $true }\n' % MARK)
    edit(root, 'launcher/Metin2Launcher.psm1',
         "    param([AllowEmptyString()][string]$ClientFolder)\n    if (-not $ClientFolder -or",
         "    param([AllowEmptyString()][string]$ClientFolder)\n"
         "    # %s: patcher pobiera klienta 2.x - w paczce testowej Yohara go nie uruchamiamy.\n"
         "    return ''\n"
         "    if (-not $ClientFolder -or" % MARK)


INSTRUKCJA = """MT2009 PLUS - Yohara {tag} (paczka serwerowa do testow)
=============================================================

To jest TESTOWA wersja serwera z aktualizacja Yohara ({tag}).
Udostepniam ja do testow - moga w niej byc bledy, a postacie i swiat
z tej wersji moga nie przejsc do wydania koncowego. Prosze o zglaszanie
bledow na Discordzie. Lista zmian: CHANGELOG-YOHARA-{v}.md.

AKTUALIZACJE SA WYLACZONE, EDYTOR .env DZIALA
---------------------------------------------
W tej paczce wylaczylem automatyczne aktualizacje (GitHub i serwer
zapasowy), zeby wydania 2.x nie nadpisaly plikow Yohary:
 - launcher czyta tylko lokalny plik update-manifest-mt2009.json
   (wersja {tag}), wiec nie proponuje aktualizacji serwera ani klienta,
   i nie uruchamia MT2009-Patcher.exe,
 - w .env: M2_UPDATE_CHECK=0, M2_UPDATE_APPLY=0, M2_UPDATE_WATCH_UPDATES=0
   (panele nic nie sprawdzaja i nic nie instaluja),
 - M2_UPDATE_AUTOSTART=1: aktualizator startuje sam, ale TYLKO jako edytor
   ustawien - dzieki niemu strona "Ustawienia serwera (.env)" w panelu
   zaawansowanym zapisuje zmiany (wczesniej byla tylko do odczytu),
 - linux-port/tools/update.sh nic nie pobiera ani nie instaluje,
 - instaluj-vps.sh domyslnie pomija aktualizacje.
Serwer zainstalowany z 3.0.0 (M2_UPDATE_AUTOSTART=0) albo z 3.0.1/3.0.2
(M2_UPDATE_CHECK=1) dostaje te ustawienia raz, przy pierwszym starcie
(znacznik M2_YOHARA_UPDATES_DEFAULTED=1 w .env); pozniejsza zmiana zostaje.
Nowa wersje testowa udostepnie jako nowa paczke albo latke.

INSTALACJA - WINDOWS
--------------------
1. Wymagany Docker Desktop (jak przy zwyklej paczce).
2. Rozpakuj paczke do NOWEGO, pustego folderu (np. C:\\MT2009-Yohara).
   Nie rozpakowuj jej na istniejacy serwer 2.x. Jesli serwer 2.x jest
   uruchomiony, najpierw go zatrzymaj (stop.bat), bo oba uzywaja tych
   samych portow. Serwer z poprzedniej paczki Yohara 3.0.2 zaktualizujesz
   latka MT2009-PLUS-Yohara-latka-{prev}-do-{v}-test.zip.
3. Uruchom Metin2-Launcher-GUI.bat i kliknij GRAJ.
   Pierwsze uruchomienie wymusza zbudowanie osobnych obrazow Yohary w
   Dockerze - trwa to dlugo (kilkanascie do kilkudziesieciu minut).
   Plik .env tworzy sie sam. Obrazy Yohary maja osobne nazwy i nie moga
   zostac zastapione obrazami zwyklego serwera 2.x.

INSTALACJA - LINUX / VPS
------------------------
Rozpakuj paczke na serwerze i z jej folderu uruchom:
    sudo sh linux-port/tools/vps-install.sh install
Pozostale kroki sa takie same jak przy zwyklej paczce (SERWER_PL.md).

KLIENT
------
Potrzebny jest klient Yohara {client}:
 1. klient 2.0.64,
 2. na niego klient-test-yohara-3.0.0.zip,
 3. na to klient-yohara-{client}-aktualizacja-od-3.0.0.zip
    (http://141.94.100.53/aktualizacje/test-plus/)
    - rozpakuj do folderu klienta i zastap pliki.
Ten klient ma 3 Loch Pajakow i Krypte Balathora - w tej paczce sa domyslnie
wlaczone (M2_SPIDER3_ON=1, M2_BALATHOR_ON=1). Starszy klient zamyka sie
przy wejsciu na te mapy.
Wazne: NIE uruchamiaj MT2009-Patcher.exe i nie klikaj w launcherze
"aktualizuj klienta" - patcher sciaga klienta 2.x i nadpisalby pliki
Yohary. Gre uruchamiaj bezposrednio przez metin2client.exe (albo
przyciskiem GRAJ w launcherze).
Edytor bazy danych w panelu: po aktualizacji pobierz zip na nowo.

Wersja serwera: {tag}
"""

LATKA = """MT2009 PLUS – Yohara: łatka serwera {prev}-test → {v}-test
===========================================================

Dla kogo: serwery zainstalowane z paczki Yohara {prev}-test (albo starszej Yohary 3.0.x zaktualizowanej łatkami do {prev}).
Kto instaluje od zera – niech pobierze pełną paczkę MT2009-PLUS-Yohara-{v}-test-serwer.zip zamiast tej łatki.

WINDOWS
1. Zatrzymaj serwer (STOP w launcherze albo stop.bat). Poczekaj, aż się zatrzyma.
2. Rozpakuj ten zip. Wejdź do folderu {name} i skopiuj CAŁĄ jego zawartość do folderu swojego serwera
   (tam, gdzie jest start-server.ps1). Na pytanie o zastąpienie plików – „Zastąp wszystkie”.
   W łatce jest ukryty plik „.m2launcher-rebuild-pending” – musi trafić do folderu serwera
   (w Eksploratorze: Widok → Pokaż → Ukryte elementy, jeśli go nie widzisz).
3. Uruchom Metin2-Launcher-GUI.bat i kliknij GRAJ. Launcher najpierw PRZEBUDUJE serwer (kilkanaście–kilkadziesiąt
   minut – to normalne), potem go uruchomi. Baza danych zaktualizuje się sama.
   Bez launchera: PowerShell w folderze serwera →
       powershell -ExecutionPolicy Bypass -File start-server.ps1 -Build

VPS (Linux)
1. Zatrzymaj serwer, wgraj zawartość folderu {name} do folderu serwera (scp / unzip -o na serwerze).
2. sudo sh linux-port/tools/vps-install.sh install
   (zachowuje .env i hasła, przebudowuje i uruchamia serwer; log: sudo sh linux-port/tools/vps-install.sh status)

AKTUALIZACJE I EDYTOR .env
- Aktualizacje zostają wyłączone (M2_UPDATE_CHECK=0, M2_UPDATE_APPLY=0, M2_UPDATE_WATCH_UPDATES=0), launcher czyta
  tylko lokalny manifest – także gdy launcher.config.json z 3.0.1/3.0.2 wskazywał GitHuba.
- Edytor „Ustawienia serwera (.env)” w panelu zaawansowanym działa: aktualizator startuje sam jako edytor .env
  (M2_UPDATE_AUTOSTART=1). U serwerów z 3.0.0 (M2_UPDATE_AUTOSTART=0) launcher / vps-install.sh przestawia to raz,
  przy pierwszym starcie po łatce (znacznik M2_YOHARA_UPDATES_DEFAULTED=1 w .env); późniejsza zmiana zostaje.
- 3 Loch Pająków i Krypta Balathora są włączone (M2_SPIDER3_ON=1, M2_BALATHOR_ON=1) – potrzebny klient Yohara {client}.

KLIENT
- Wgraj klienta klient-yohara-{client}-aktualizacja-od-3.0.0.zip (na klienta Yohara 3.0.0) – bez niego nowe mapy
  i okna (3 Loch Pająków, Krypta Balathora, Społeczność, Lokalizator NPC, okno wytwarzania) nie zadziałają.
- Edytor bazy danych w panelu: po aktualizacji pobierz zip na nowo.

Twój plik .env, hasła, postacie i świat zostają bez zmian.
Plików w łatce: {count}.
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, text, mode=None):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    if mode is not None:
        os.chmod(path, mode)


def zip_dir(parent, name, out):
    if os.path.exists(out):
        os.remove(out)
    run(['zip', '-r', '-q', '-X', out, name], cwd=parent)
    digest = sha256(out)
    write(out + '.sha256', '%s  %s\n' % (digest, os.path.basename(out)))
    return digest


def deploy_patch_order(script):
    with open(script, encoding='utf-8') as f:
        m = re.search(r'for p in ([^;]+); do python3 \$Z/server-patches/\$p/apply_\$p\.py', f.read())
    if not m:
        raise SystemExit('no patch list in %s' % script)
    return m.group(1).split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', required=True)
    ap.add_argument('--prev-version')
    ap.add_argument('--client-version', required=True)
    ap.add_argument('--changelog', required=True)
    ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--repo', default='/opt/metin2/git/wt-yohara')
    ap.add_argument('--test-tree', default='/opt/metin2/mt2009plustest')
    ap.add_argument('--deploy-script', default='/opt/metin2/cache/yohara-deploy.sh')
    ap.add_argument('--stage', default=None)
    ap.add_argument('--out', default='/opt/metin2/dist/aktualizacje/test-plus')
    ap.add_argument('--prev-zip', default=None)
    a = ap.parse_args()

    v, tag = a.version, a.version + '-test'
    stage = a.stage or '/opt/metin2/cache/yohara/pkg-%s' % v.replace('.', '')
    name = 'MT2009-PLUS-Serwer-Yohara-%s' % tag
    root = os.path.join(stage, name)
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(root)

    # 1. tracked files
    commit = subprocess.check_output(['git', '-C', a.repo, 'rev-parse', '--short', a.ref], text=True).strip()
    p1 = subprocess.Popen(['git', '-C', a.repo, 'archive', a.ref], stdout=subprocess.PIPE)
    run(['tar', '-x', '-C', root], stdin=p1.stdout)
    if p1.wait() != 0:
        raise SystemExit('git archive failed')
    for rel in REPO_ONLY:
        shutil.rmtree(os.path.join(root, rel), ignore_errors=True)
    for rel in REPO_ONLY_FILES:
        if os.path.exists(os.path.join(root, rel)):
            os.remove(os.path.join(root, rel))
    for dirpath, _dirs, files in os.walk(os.path.join(root, 'tools'), topdown=False):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, '/')
            if rel not in TOOLS_KEEP:
                os.remove(os.path.join(dirpath, fn))
        if not os.listdir(dirpath):
            os.rmdir(dirpath)

    # 2. the trees git does not carry, from the test tree
    for rel in IGNORED_TREES:
        src = os.path.join(a.test_tree, rel)
        if not os.path.isdir(src):
            raise SystemExit('missing in the test tree: %s' % src)
        os.makedirs(os.path.join(root, rel), exist_ok=True)
        excl = ['--exclude=__pycache__'] + ['--exclude=*%s' % s for s in SKIP_SUFFIX]
        run(['rsync', '-a'] + excl + [src + '/', os.path.join(root, rel) + '/'])
    # the overlay's game sources mirrored, as 20_sync_test_tree.sh does
    ov = os.path.join(root, 'linux-port/overlays/playerbot/src/game/src')
    gs = os.path.join(root, 'linux-port/docker/game/src/server/game/src')
    mirrored = []
    for fn in sorted(os.listdir(ov)):
        s = os.path.join(ov, fn)
        if os.path.isfile(s) and not (os.path.exists(os.path.join(gs, fn)) and filecmp.cmp(s, os.path.join(gs, fn), False)):
            shutil.copy2(s, os.path.join(gs, fn))
            mirrored.append(fn)
    print('overlay files mirrored into the engine source: %d %s' % (len(mirrored), ' '.join(mirrored[:20])))
    # every server patch in the deploy order (an applied edit is skipped)
    for p in deploy_patch_order(a.deploy_script):
        r = subprocess.run(['python3', os.path.join(a.repo, 'server-patches', p, 'apply_%s.py' % p), gs],
                           capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [''])[-1]
        print('patch %-18s rc=%d %s' % (p, r.returncode, last[:120]))
        if r.returncode != 0:
            raise SystemExit('patch %s failed:\n%s%s' % (p, r.stdout, r.stderr))
    for dirpath, dirs, files in os.walk(gs):
        for fn in files:
            if fn.endswith(SKIP_SUFFIX):
                os.remove(os.path.join(dirpath, fn))
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(dirpath, '__pycache__'))
            dirs.remove('__pycache__')

    # 3. Yohara package edits and version files
    no_update_edits(root, v)
    write(os.path.join(root, 'VERSION'), tag + '\n')
    write(os.path.join(root, 'CLIENT_VERSION'), a.client_version + '\n')
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    write(os.path.join(root, 'update-manifest-mt2009.json'),
          '{\n  "schema": 1,\n  "channel": "yohara-test",\n  "publishedAt": "%s",\n'
          '  "statusMessage": "MT2009 PLUS Yohara %s: paczka testowa, aktualizacje wylaczone.",\n'
          '  "server": {\n    "version": "%s"\n  }\n}\n' % (now, tag, tag))
    write(os.path.join(root, '.m2launcher-rebuild-pending'), 'Yohara %s: first build required\n' % tag)
    write(os.path.join(root, 'INSTRUKCJA-YOHARA-TEST.txt'),
          INSTRUKCJA.format(tag=tag, v=v, prev=a.prev_version or '?', client=a.client_version).replace('\n', '\r\n'))
    shutil.copy2(a.changelog, os.path.join(root, 'CHANGELOG-YOHARA-%s.md' % v))
    for keep in ('linux-port/docker/game/src/serverfiles/share/package', 'linux-port/docker/game/src/serverfiles/mark-default'):
        os.makedirs(os.path.join(root, keep), exist_ok=True)

    out = os.path.join(a.out, 'MT2009-PLUS-Yohara-%s-test-serwer.zip' % v)
    digest = zip_dir(stage, name, out)
    print('FULL %s %d %s (git %s)' % (out, os.path.getsize(out), digest, commit))

    # 4. the patch from the previous full package
    if a.prev_zip:
        prev_dir = os.path.join(stage, '_prev')
        os.makedirs(prev_dir)
        run(['unzip', '-q', a.prev_zip, '-d', prev_dir])
        (prev_root,) = [os.path.join(prev_dir, d) for d in os.listdir(prev_dir)]
        lname = 'MT2009-PLUS-Yohara-latka-%s-do-%s-test' % (a.prev_version, v)
        lroot = os.path.join(stage, lname)
        count = 0
        removed = []
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                old = os.path.join(prev_root, rel)
                if os.path.isfile(old) and filecmp.cmp(old, os.path.join(dirpath, fn), False):
                    continue
                os.makedirs(os.path.join(lroot, os.path.dirname(rel)), exist_ok=True)
                shutil.copy2(os.path.join(dirpath, fn), os.path.join(lroot, rel))
                count += 1
        for dirpath, _dirs, files in os.walk(prev_root):
            for fn in files:
                rel = os.path.relpath(os.path.join(dirpath, fn), prev_root)
                if not os.path.exists(os.path.join(root, rel)):
                    removed.append(rel)
        write(os.path.join(lroot, 'LATKA-%s-INSTRUKCJA.txt' % v),
              LATKA.format(prev=a.prev_version, v=v, name=lname, client=a.client_version, count=count + 1))
        lout = os.path.join(a.out, 'MT2009-PLUS-Yohara-latka-%s-do-%s-test.zip' % (a.prev_version, v))
        ldigest = zip_dir(stage, lname, lout)
        write(os.path.join(stage, 'latka-obsolete-files.txt'), '\n'.join(sorted(removed)) + '\n')
        print('LATKA %s %d %s files=%d obsolete-in-prev=%d' % (lout, os.path.getsize(lout), ldigest, count + 1, len(removed)))
        shutil.rmtree(prev_dir)


if __name__ == '__main__':
    main()
