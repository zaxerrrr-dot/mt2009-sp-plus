#!/usr/bin/env python3
"""Put the client launcher (MT2009-Aktualizator.*) and CLIENT_VERSION into a
client update zip, at its root, next to metin2client.exe, and write the
client file list (client-files.json in the repository root) from that zip.

    python3 dodaj-do-paczki.py metin2-client-update-2.0.29.zip 2.0.29
    python3 dodaj-do-paczki.py --tylko-lista metin2-client-update-2.0.28.zip 2.0.28

--tylko-lista only writes client-files.json (the zip is not changed).
client-files.json lists the small files that change with every client
release (metin2client.exe, Dolacz.*, pack/Index, pack/*.index - not the big
.data files, whose .index changes with them, and not pack/dbdata.*, which the
player replaces from his server's panel); the launcher hashes them at start
to recognise a client with no CLIENT_VERSION. Commit it with the release.

Entries of the same names already in the zip are replaced. The zip must not
carry coop.cfg / coop2.cfg (the launcher keeps a player's own ones anyway, but
the package should not ship a server list). Prints the SHA-256 and size for
the manifest's "client" section - compute them only after this step.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER_FILES = ["MT2009-Aktualizator.bat", "MT2009-Aktualizator.ps1", "MT2009-Aktualizator.jpg"]
FORBIDDEN = {"coop.cfg", "coop2.cfg"}
FILE_LIST = os.path.normpath(os.path.join(HERE, "..", "..", "client-files.json"))


def listed(name):
    # What the launcher checks: every file except the big pack .data files,
    # the launcher itself, CLIENT_VERSION and the player's server list.
    lower = name.lower()
    if name.endswith("/") or lower.endswith(".data"):
        return False
    if name in LAUNCHER_FILES or name == "CLIENT_VERSION" or lower in FORBIDDEN:
        return False
    # MT2009_PLUS_DB_EDITOR_V1: pack/dbdata.* is the player's to replace (the
    # zip of his server's database editor), so a client with it unpacked
    # still counts as up to date.
    if lower.startswith("pack/dbdata."):
        return False
    return True


def write_file_list(zip_path, version, out_path=FILE_LIST):
    files = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if not listed(info.filename):
                continue
            digest = hashlib.sha256()
            with z.open(info) as data:
                for chunk in iter(lambda: data.read(1 << 20), b""):
                    digest.update(chunk)
            files.append({"path": info.filename, "size": info.file_size, "sha256": digest.hexdigest().upper()})
    if not any(f["path"] == "metin2client.exe" for f in files):
        sys.exit("brak metin2client.exe w paczce")
    files.sort(key=lambda f: f["path"].lower())
    with open(out_path, "w", encoding="ascii", newline="\n") as f:
        json.dump({"schema": 1, "version": version, "files": files}, f, indent=2)
        f.write("\n")
    print("zapisano %s: wersja %s, plikow %d" % (out_path, version, len(files)))


def main():
    args = sys.argv[1:]
    only_list = bool(args) and args[0] == "--tylko-lista"
    if only_list:
        args = args[1:]
    if len(args) != 2:
        sys.exit(__doc__)
    zip_path, version = args
    if not re.fullmatch(r"[0-9A-Za-z._-]{1,32}", version):
        sys.exit("nieprawidlowa wersja: %r" % version)
    if only_list:
        write_file_list(zip_path, version)
        return
    for name in LAUNCHER_FILES:
        if not os.path.isfile(os.path.join(HERE, name)):
            sys.exit("brak pliku %s" % name)
    with open(os.path.join(HERE, "MT2009-Aktualizator.ps1"), "rb") as f:
        if f.read(3) != b"\xef\xbb\xbf":
            sys.exit("MT2009-Aktualizator.ps1 musi byc UTF-8 z BOM")

    replaced = set(LAUNCHER_FILES) | {"CLIENT_VERSION"}
    fd, tmp = tempfile.mkstemp(suffix=".zip", dir=os.path.dirname(os.path.abspath(zip_path)))
    os.close(fd)
    try:
        with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
            names = [i.filename for i in src.infolist()]
            if "metin2client.exe" not in names:
                sys.exit("to nie wyglada na paczke klienta (brak metin2client.exe w korzeniu zip)")
            bad = [n for n in names if n.lower() in FORBIDDEN]
            if bad:
                sys.exit("paczka zawiera %s - usun je z paczki" % ", ".join(bad))
            for info in src.infolist():
                if info.filename in replaced:
                    continue
                with src.open(info) as data:
                    dst.writestr(info, data.read(), compress_type=info.compress_type)
            for name in LAUNCHER_FILES:
                dst.write(os.path.join(HERE, name), name)
            dst.writestr("CLIENT_VERSION", version + "\r\n")
        shutil.move(tmp, zip_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    digest = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    print("dodano: %s, CLIENT_VERSION=%s" % (", ".join(LAUNCHER_FILES), version))
    print('"sha256": "%s",' % digest.hexdigest().upper())
    print('"size": %d' % os.path.getsize(zip_path))
    write_file_list(zip_path, version)


if __name__ == "__main__":
    main()
