#!/usr/bin/env python3
"""Post one CHANGELOG.md release to a Discord channel as an embed.

    DISCORD_WEBHOOK_URL=... python3 .github/scripts/discord_release.py [VERSION]
    python3 .github/scripts/discord_release.py 2.2.6 --dry-run   # print the payload
    python3 .github/scripts/discord_release.py 2.0.7 --client    # a client release

A client release is the "## Klient X.Y.Z — ..." section (VERSION defaults to
the CLIENT_VERSION file).

The release is the "## X.Y.Z — ..." section of CHANGELOG.md (VERSION defaults
to the VERSION file). An optional title follows the date:

    ## 2.2.7 — 2026-09-24 — Nowe kostiumy, poprawki Auto Łowów

Without one, the section's "###" headings make the title.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.environ.get("GITHUB_REPOSITORY", "zaxerrrr-dot/mt2009-sp-plus")
COLOR = 0x2ECC71
DESC_MAX = 4000      # Discord: 4096 per embed description
TOTAL_MAX = 5800     # Discord: 6000 characters across all embeds of a message
HEAD_RE = re.compile(r"^##\s+(?:(Klient|Client)\s+)?(\d+\.\d+\.\d+)\b(.*)$", re.I)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8-sig") as f:
        return f.read()


def section(changelog, version, client=False):
    """(heading rest, body) of the version's section, or None."""
    lines = changelog.splitlines()
    for i, line in enumerate(lines):
        m = HEAD_RE.match(line)
        if m and m.group(2) == version and bool(m.group(1)) == client:
            body = []
            for nxt in lines[i + 1:]:
                if HEAD_RE.match(nxt) or nxt.strip() == "---":
                    break
                body.append(nxt)
            return m.group(3), "\n".join(body).strip()
    return None


def title_of(version, rest, body, client=False):
    parts = [p.strip() for p in re.split(r"\s+[—–-]\s+", rest.strip(" —–-")) if p.strip()]
    parts = [p for p in parts if not re.fullmatch(r"\d{4}-\d\d-\d\d", p)]
    if parts:
        name = " — ".join(parts)
    else:
        heads = [h.strip() for h in re.findall(r"^###\s+(.+)$", body, re.M)]
        heads = [re.sub(r"\s*\(.*?\)\s*$", "", h) for h in heads]
        if heads:
            name = ", ".join(heads[:3])
        else:
            first = next((l for l in to_discord(body).splitlines() if l.strip()), "Aktualizacja")
            name = re.split(r"[;.]", first.lstrip("• ").strip())[0].strip() or "Aktualizacja"
            if len(name) > 120:
                name = name[:117].rstrip() + "…"
    label = f"Klient {version}" if client else version
    title = f"🚀 {label} — {name}"
    return title if len(title) <= 256 else title[:253] + "…"


def to_discord(body):
    """CHANGELOG markdown -> Discord markdown: unwrap paragraphs, ### -> bold."""
    out, para = [], []

    def flush():
        if para:
            out.append(" ".join(para))
            para.clear()

    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            out.append("")
            continue
        m = re.match(r"^#{3,}\s+(.+)$", line)
        if m:
            flush()
            out.append(f"**{m.group(1).strip()}**")
            continue
        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if m:
            flush()
            para.append("• " + m.group(1).strip())
            continue
        if para or (out and out[-1].startswith("• ") and raw.startswith(" ")):
            if not para:
                para.append(out.pop())
            para.append(line.strip())
        else:
            para.append(line.strip())
    flush()
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return text


def chunks(text, size):
    """Split at blank lines, then lines, so no chunk passes 'size'."""
    parts, cur = [], ""
    for block in text.split("\n\n"):
        piece = block if not cur else "\n\n" + block
        if len(cur) + len(piece) <= size:
            cur += piece
            continue
        if cur:
            parts.append(cur)
        cur = ""
        while len(block) > size:
            cut = block.rfind("\n", 0, size)
            cut = cut if cut > 0 else size
            parts.append(block[:cut])
            block = block[cut:].lstrip("\n")
        cur = block
    if cur:
        parts.append(cur)
    return parts


def payloads(version, client=False):
    found = section(read("CHANGELOG.md"), version, client)
    if not found:
        sys.exit(f"CHANGELOG.md has no '## {'Klient ' if client else ''}{version}' section")
    rest, body = found
    title = title_of(version, rest, body, client)
    footer = ("MT2009 PLUS • aktualizacja w launcherze: AKTUALIZUJ KLIENTA" if client
              else "MT2009 PLUS • aktualizacja w launcherze: SPRAWDŹ AKTUALIZACJE")
    url = f"https://github.com/{REPO}/blob/main/CHANGELOG.md"
    parts = chunks(to_discord(body), DESC_MAX)
    messages, embeds, used = [], [], 0
    for n, part in enumerate(parts):
        embed = {"description": part, "color": COLOR}
        if n == 0:
            embed.update(title=title, url=url)
        if n == len(parts) - 1:
            embed["footer"] = {"text": footer}
        size = len(part) + (len(title) if n == 0 else 0) + 80
        if embeds and (len(embeds) == 10 or used + size > TOTAL_MAX):
            messages.append(embeds)
            embeds, used = [], 0
        embeds.append(embed)
        used += size
    messages.append(embeds)
    return [{"username": "MT2009 PLUS", "embeds": e, "allowed_mentions": {"parse": []}} for e in messages]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    client = "--client" in sys.argv
    version = args[0] if args else read("CLIENT_VERSION" if client else "VERSION").strip()
    msgs = payloads(version, client)
    if "--dry-run" in sys.argv:
        print(json.dumps(msgs, ensure_ascii=False, indent=2))
        return
    hook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not hook:
        sys.exit("DISCORD_WEBHOOK_URL is not set (repository secret)")
    for msg in msgs:
        req = urllib.request.Request(hook + ("&" if "?" in hook else "?") + "wait=true",
                                     data=json.dumps(msg).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "mt2009-plus-release-notes"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"posted {version}: HTTP {resp.status}")


if __name__ == "__main__":
    main()
