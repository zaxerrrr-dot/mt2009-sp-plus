#!/usr/bin/env python3
"""check_tr2.py <input ID<TAB>Polish> <output ID<TAB>translation> [codepage, e.g. cp1252] - lists every ID missing / doubled / with other
placeholders, [TAGS], leading or trailing spaces than its Polish. Exit 0 when clean."""
import re, sys
CONV = re.compile(r"%(?:%|[-+#0]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|q|j|z|t)?[diouxXeEfgGcs])")
TAG = re.compile(r"\[[A-Z][A-Z_0-9]+(?:[ \t][^\]]*)?\]")
def load(p, cols):
    d, dup = {}, []
    for line in open(p, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        if "\t" not in line:
            print("NO TAB:", line[:80]); continue
        k, v = line.split("\t", 1)
        if k in d: dup.append(k)
        d[k] = v
    return d, dup
src, _ = load(sys.argv[1], 2)
src = {k: v.split("\t")[0] for k, v in src.items()}	# ID<TAB>Polish[<TAB>English]
out, dup = load(sys.argv[2], 2)
bad = 0
for k in dup:
    print("DOUBLE", k); bad += 1
for k, pl in src.items():
    if k not in out:
        print("MISSING", k); bad += 1; continue
    t = out[k]
    conv_pl = [c for c in CONV.findall(pl) if c != "%%"]
    conv_t = [c for c in CONV.findall(t) if c != "%%"]
    if conv_pl != conv_t:
        print("PLACEHOLDERS", k, conv_pl, conv_t); bad += 1
    if [x.split()[0] for x in TAG.findall(pl)] != [x.split()[0] for x in TAG.findall(t)]:
        print("TAGS", k); bad += 1
    if (pl[:1] == " ") != (t[:1] == " ") or (pl[-1:] == " ") != (t[-1:] == " "):
        print("EDGE SPACES", k, repr(pl[:15]), repr(t[:15]), repr(pl[-10:]), repr(t[-10:])); bad += 1
    if re.search(r"metin\s*2|gameforge|tieru|ameria|metin2alerts", t, re.I) and not re.search(r"metin\s*2|gameforge", pl, re.I):
        print("FORBIDDEN WORD", k); bad += 1
cpage = sys.argv[3] if len(sys.argv) > 3 else None
if cpage:
    for k, t in out.items():
        if t == src.get(k):
            continue
        try:
            t.encode(cpage)
        except UnicodeEncodeError as e:
            print("CODEPAGE %s: %s cannot hold %r" % (k, cpage, t[e.start:e.end])); bad += 1
for k in out:
    if k not in src:
        print("UNKNOWN ID", k); bad += 1
print("checked %d, problems %d" % (len(src), bad))
sys.exit(1 if bad else 0)
