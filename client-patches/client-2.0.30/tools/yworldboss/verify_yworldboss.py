# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 - checks the packs build_yworldboss_packs.py wrote: the pack "yworldboss" in Index and under
# the 29 MB limit with every staged file; every name the six w_* models' text files (.msm/.msa/.mse/motlist) give
# resolves to a name of the client (the OUT packs + c58.lst + the base client's pre-import listing); npclist has the
# 36 rows 4420-4479 (the bosses on their w_* model); gamedata/dbdata hold the rows of worldboss_client.json (a second
# patch must change nothing).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/yworldboss/verify_yworldboss.py \
#     <OUT pack dir> [<work dir with c58.lst>]
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_yworldboss_client as pc  # noqa: E402

OUT = sys.argv[1]
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'yworldboss_manifest.json'), encoding='utf-8'))
RE_REF = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|msa|mse|mde|wav|mss))"', re.I)


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


fail = []
CONTENT = {}
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, p + '.index'))
    d = packlib.rd(os.path.join(OUT, p + '.data'))
    if p in MAN['new_packs'] and len(d) >= ZIP_LIMIT:
        fail.append('pack %s over the 29 MB limit' % p)
    for e in ents:
        CONTENT.setdefault(e['name'], m2pack.read_entry(d, e))
NAMES = set(CONTENT)
for l in open(os.path.join(WORK, 'c58.lst'), encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        NAMES.add(norm(t[1]))
for l in open(PRE_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 3)
    if len(t) == 4:
        NAMES.add(norm(t[3]))
ix = [l.strip() for l in open(os.path.join(OUT, 'Index'), 'rb').read().decode('latin1').replace('\r', '').split('\n')]
for p in MAN['new_packs']:
    if p not in ix:
        fail.append('pack %s is not in Index' % p)
for e in MAN['packs']['yworldboss']:
    if e['name'] not in CONTENT:
        fail.append('staged %s is in no pack of OUT' % e['name'])
unknown = set()
for m in MAN['models']:
    folder = 'd:/ymir work/monster2/%s/' % m
    if folder + m + '.msm' not in CONTENT:
        fail.append('%s.msm missing' % m)
    for k, b in CONTENT.items():
        if not k.startswith(folder) or not k.endswith(('.msm', '.msa', '.txt')):
            continue
        for r in RE_REF.findall(b.decode('latin1')):
            r = norm(r)
            full = r if r.startswith(('d:/', 'sound/')) else ('d:/' + r if r.startswith('ymir work/') else folder + r)
            if full not in NAMES:
                unknown.add((k, full))
if unknown:
    fail.append('names not in the client: %s' % sorted(unknown)[:20])
# gamedata / dbdata: a second patch changes nothing
for pack, files in (('gamedata', (('gamedata/mob_proto', pc.mob_proto), ('gamedata/npclist.txt', pc.npclist),
                                  ('gamedata/item_list.txt', pc.item_list))),
                    ('dbdata', (('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)))):
    for n, fn in files:
        if n not in CONTENT:
            fail.append('%s not in OUT' % n)
            continue
        nb, changed = fn(CONTENT[n])
        if changed:
            fail.append('%s: %d row(s) missing' % (n, changed))
npc = CONTENT.get('gamedata/npclist.txt', b'').decode('cp1250')
for k, model in pc.data()['models'].items():
    if not re.search(r'(?m)^%s\s+%s\s*$' % (k, re.escape(model)), npc):
        fail.append('npclist: %s %s' % (k, model))
print('yworldboss: %d staged files, %d models checked' % (len(MAN['packs']['yworldboss']), len(MAN['models'])))
if fail:
    print('FAIL')
    for f in fail:
        print(' -', f)
    sys.exit(1)
print('OK')
