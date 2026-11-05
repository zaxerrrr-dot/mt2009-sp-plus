#!/usr/bin/env python3
"""Check the bots' chat catalogs (playerbot_i18n.h) and try them on real lines.

    check_catalog.py [lang ...]                 coverage and slot errors per language
    check_catalog.py --corpus FILE lang         translate the bot lines of a game
                                                syslog (text="...") and show the hits
    check_catalog.py --line "Polish" lang       translate one line

The matcher here is the core's (TranslatePlayerBotI18nLine) in Python: case
and Polish marks folded, a closing full stop optional, slots $NAME / {n}, a
line cut at ". ", ", ", "? ", "! " and smileys when no template covers it whole.
"""
import argparse, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', '..', 'linux-port/docker/game/playerbot_i18n')
SLOT = re.compile(r'\$[A-Z][A-Z0-9_]*|\{[1-9][0-9]*\}')


def fold(s):
    out = []
    for ch in s:
        if ch in 'łŁ':
            out.append('l'); continue
        base = unicodedata.normalize('NFKD', ch)[0]
        out.append(base.lower() if len(base) == 1 else ch.lower())
    return ''.join(out)


def trim_end(s):
    s = s.rstrip(' ')
    if len(s) >= 2 and s[-1] == '.' and s[-2] != '.':
        s = s[:-1]
    return s


def load_tsv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#') or '\t' not in line:
            continue
        a, b = line.split('\t')[:2]
        rows.append((a, b))
    return rows


def cut_at(s, i):
    if i + 1 >= len(s) or s[i + 1] != ' ':
        return False
    c = s[i]
    if c in '.!?,;:':
        return True
    if i == 0:
        return False
    p = s[i - 1]
    return (p in ':;' and c in 'DPp)(d') or (p in 'xX' and c in 'Dd')


class Entry:
    def __init__(self, pl, out):
        pl = trim_end(pl)
        self.pieces = []
        self.slots = []
        pos = 0
        for m in SLOT.finditer(pl):
            if m.start() > pos:
                self.pieces.append((False, fold(pl[pos:m.start()])))
            self.pieces.append((True, m.group(0)))
            self.slots.append(m.group(0))
            pos = m.end()
        if pos < len(pl):
            self.pieces.append((False, fold(pl[pos:])))
        self.literal = sum(len(t) for s, t in self.pieces if not s)
        self.out = out


class Lang:
    def __init__(self, code):
        self.entries = []
        for pl, tr in load_tsv(os.path.join(DIR, 'chat_%s.tsv' % code)):
            if tr == '-' or not tr:
                continue
            e = Entry(pl, tr)
            if sum(c.isalpha() for sl, t in e.pieces if not sl for c in t) >= 2:
                self.entries.append(e)
        self.entries.sort(key=lambda e: -e.literal)

    def match(self, e, folded, ti, end, pi, caps, budget):
        budget[0] -= 1
        if budget[0] < 0:
            return False
        if pi == len(e.pieces):
            return ti == end
        slot, text = e.pieces[pi]
        if not slot:
            if folded.startswith(text, ti) and ti + len(text) <= end:
                return self.match(e, folded, ti + len(text), end, pi + 1, caps, budget)
            return False
        if ti >= end:
            return False
        if pi + 1 == len(e.pieces):
            caps.append((ti, end - ti))
            return True
        nslot, ntext = e.pieces[pi + 1]
        if nslot:
            for ln in range(1, end - ti):
                caps.append((ti, ln))
                if self.match(e, folded, ti + ln, end, pi + 1, caps, budget):
                    return True
                caps.pop()
            return False
        at = folded.find(ntext, ti + 1)
        while at != -1 and at + len(ntext) <= end:
            caps.append((ti, at - ti))
            if self.match(e, folded, at, end, pi + 1, caps, budget):
                return True
            caps.pop()
            at = folded.find(ntext, at + 1)
        return False

    def whole(self, raw, folded, s, e_, depth):
        if depth > 4:
            return None
        for e in self.entries:
            if e.literal > e_ - s:
                continue
            caps = []
            if not self.match(e, folded, s, e_, 0, caps, [2000]):
                continue
            vals, good = {}, True
            for name, (o, ln) in zip(e.slots, caps):
                v, ok = self.value(raw[o:o + ln], depth + 1)
                if not ok and any(cut_at(raw, i) for i in range(o, o + ln - 1)):
                    good = False
                    break
                vals[name] = v
            if not good:
                continue
            out = e.out
            for name in sorted(vals, key=len, reverse=True):
                out = out.replace(name, vals[name])
            return out
        return None

    def value(self, v, depth):
        core = v.strip()
        if not core or depth > 3 or re.fullmatch(r'[0-9.,k%+\-]+', core):
            return v, True
        f = fold(core)
        t = trim_end(f)
        r = self.whole(core, f, 0, len(t), depth)
        # (the core also takes a list of item names, by its name tables)
        return v.replace(core, r if r is not None else core), r is not None

    def line(self, text):
        return self.line_as(text)

    def line_as(self, text):
        folded = fold(text)
        cuts = [0]
        for i in range(len(text) - 1):
            if cut_at(text, i):
                cuts.append(i + 2)
        cuts.append(len(text))
        n = len(cuts)
        INF = 10 ** 9
        best, frm, piece = [INF] * n, [-1] * n, [''] * n
        best[0] = 0
        for j in range(1, n):
            for i in range(j):
                if best[i] == INF or best[i] + 1 >= best[j]:
                    continue
                s, e = cuts[i], cuts[j] - (1 if j + 1 < n else 0)
                seg = folded[s:e]
                core = len(seg.rstrip(' '))
                if core and seg[core - 1] in ',;':
                    core -= 1
                if core >= 2 and seg[core - 1] == '.' and seg[core - 2] != '.':
                    core -= 1
                t = self.whole(text, folded, s, s + core, 0)
                if t is None:
                    m = re.search(r' [:;x][dDpP)(]$', seg[:core])
                    if not m:
                        continue
                    cut = core - 3
                    b = seg[:cut]
                    if len(b) >= 2 and b[-1] == '.' and b[-2] != '.':
                        cut -= 1
                    t = self.whole(text, folded, s, s + cut, 0)
                    if t is None:
                        continue
                    core = cut
                tail = text[s + core:e]
                if tail and t and t[-1] in '.!?' and tail[0] in ',;.':
                    t = t[:-1]
                t += tail
                if text[s].islower() and t[:1].isupper() and not t[1:2].isupper():
                    t = t[0].lower() + t[1:]
                best[j], frm[j], piece[j] = best[i] + 1, i, t
        if best[-1] == INF:
            return None
        parts, j = [], n - 1
        while j > 0:
            parts.append(piece[j]); j = frm[j]
        out = ' '.join(reversed(parts))
        if not text.endswith('.') and out.endswith('.') and not out.endswith('..'):
            out = out[:-1]
        return out


def coverage(lang):
    keys = [k for k, _ in load_tsv(os.path.join(DIR, 'catalog_pl.tsv'))]
    rows = dict(load_tsv(os.path.join(DIR, 'chat_%s.tsv' % lang)))
    done = sum(1 for k in keys if rows.get(k, '-') not in ('-', ''))
    bad = []
    for pl, tr in rows.items():
        if tr in ('-', ''):
            continue
        a, b = sorted(SLOT.findall(pl)), sorted(set(SLOT.findall(tr)))
        if not set(b) <= set(a) or set(a) - set(b):
            bad.append((pl, tr))
        low = tr.lower()
        if 'metin2' in low or 'gameforge' in low:
            bad.append((pl, tr))
    page = 1252
    for line in open(os.path.join(DIR, 'chat_%s.tsv' % lang), encoding='utf-8'):
        if line.startswith('#@codepage\t'):
            page = int(line.split('\t')[1])
    lossy = 0
    for pl, tr in rows.items():
        t = tr.translate({0x219: 0x15F, 0x218: 0x15E, 0x21B: 0x163, 0x21A: 0x162, 0x2019: 39, 0x2018: 39,
                          0x201C: 34, 0x201D: 34, 0x201E: 34, 0x2013: 45, 0x2014: 45, 0x2026: 46, 0xA0: 32})
        try:
            t.encode('cp%d' % page)
        except UnicodeEncodeError:
            lossy += 1
            if lossy <= 5:
                print('    not in cp%d:' % page, tr)
    if lossy:
        print('   ', lossy, 'translations with letters code page', page, 'has not got (sent as ?)')
    print('%s: %d/%d templates (%.1f%%), %d with slot or name problems' % (
        lang, done, len(keys), 100.0 * done / max(1, len(keys)), len(bad)))
    for pl, tr in bad[:20]:
        print('   ', pl, '|', tr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus')
    ap.add_argument('--line')
    ap.add_argument('--show', type=int, default=30)
    ap.add_argument('langs', nargs='*')
    a = ap.parse_args()
    langs = a.langs or sorted(f[5:-4] for f in os.listdir(DIR) if f.startswith('chat_') and f.endswith('.tsv'))
    if a.line:
        L = Lang(langs[0])
        print(L.line(a.line))
        return
    if a.corpus:
        L = Lang(langs[0])
        lines = []
        for raw in open(a.corpus, 'rb'):
            m = re.search(rb'text="(.*)"', raw)
            if m:
                lines.append(m.group(1).decode('cp1250', 'replace'))
        uniq = list(dict.fromkeys(lines))
        hit = miss = 0
        misses = []
        for t in uniq:
            r = L.line(t)
            if r is None:
                miss += 1; misses.append(t)
            else:
                hit += 1
                if hit <= a.show:
                    print('OK  ', t, '\n  ->', r)
        print('%d distinct lines: %d translated (%.1f%%), %d not' % (len(uniq), hit, 100.0 * hit / max(1, len(uniq)), miss))
        for t in misses[:a.show]:
            print('MISS', t)
        return
    for l in langs:
        coverage(l)


if __name__ == '__main__':
    main()
