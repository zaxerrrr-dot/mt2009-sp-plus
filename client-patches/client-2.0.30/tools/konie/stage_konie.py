# -*- coding: utf-8 -*-
# MT2009_PLUS_HORSE40_V1 - stages the files of the new client pack "konie" (server-patches/konie/README.md) from the
# GF 26.1.11 client into pliki/ and writes konie_files.json (size, sha256, entry type, source of every file):
#
#   d:/ymir work/ui/konie/riding_extend_001.dds       GF ui/riding_extend_001.dds (the Mount Upgrade window's atlas)
#   d:/ymir work/ui/konie/newskillcommon_konie.dds    GF ui/newskillcommon.dds - the horse skill icons sit at 0-256 x
#                                                      480-544 of GF's 256 x 768 atlas; our client's newskillcommon.dds
#                                                      (zodiak_maps) is an older, smaller one, so GF's goes in by its
#                                                      own name and replaces nothing
#   d:/ymir work/ui/konie/<name>.sub                  GF ui/game/mount_upgrade_system/*.sub and ui/skill/common/
#                                                      mount_upgrade/*.sub with the image renamed (a version 1.0 .sub
#                                                      names its image from d:/ymir work/ui/)
#   d:/ymir work/npc_mount/horse_guild/*              GF's Potezny Kon Wojskowy (20149-20151: horse_guild_01 / 02,
#                                                      npclist.txt has their lines already; motions from npc/horse)
#
# Rerun after a change of the list (python3 stage_konie.py [GF client dir]); the builder checks pliki/ against the json.
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GF = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
OUT = os.path.join(HERE, 'pliki')
MANIFEST = os.path.join(HERE, 'konie_files.json')
UI = 'ymir work/ui'
CTYPE = {'dds': 1, 'tga': 1, 'gr2': 1, 'sub': 2, 'msm': 2, 'msa': 2, 'txt': 2}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    files = {}

    def put(name, data, source):
        path = os.path.join(OUT, name.replace('d:/', '', 1))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        files[name] = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                           ctype=CTYPE[name.rsplit('.', 1)[1].lower()], source=source)

    src = os.path.join(GF, 'd_', UI)
    put('d:/ymir work/ui/konie/riding_extend_001.dds', open(os.path.join(src, 'riding_extend_001.dds'), 'rb').read(),
        'GF 26.1.11 d_/ymir work/ui/riding_extend_001.dds')
    put('d:/ymir work/ui/konie/newskillcommon_konie.dds', open(os.path.join(src, 'newskillcommon.dds'), 'rb').read(),
        'GF 26.1.11 d_/ymir work/ui/newskillcommon.dds')
    for sub, image, new in (('game/mount_upgrade_system', 'riding_extend_001.dds', 'konie/riding_extend_001.dds'),
                            ('skill/common/mount_upgrade', 'newskillcommon.dds', 'konie/newskillcommon_konie.dds')):
        d = os.path.join(src, sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.sub'):
                continue
            text = open(os.path.join(d, fn), 'rb').read().decode('ascii')
            assert ('"%s"' % image) in text, fn
            text = text.replace('"%s"' % image, '"%s"' % new)
            put('d:/ymir work/ui/konie/' + fn, text.encode('ascii'),
                'GF 26.1.11 d_/ymir work/ui/%s/%s, image %s' % (sub, fn, new))
    # the model and its motion scripts; the motions themselves (GF's npc/horse/00 and npc/horse_event1/*.gr2 - the
    # base client's horse_event1 folder is not on this server to check) go in beside it as mot_<name>.gr2 and the
    # .msa files name them there, so the horse needs nothing of the base packs
    d = os.path.join(GF, 'd_', 'ymir work', 'npc_mount', 'horse_guild')
    for fn in sorted(os.listdir(d)):
        data = open(os.path.join(d, fn), 'rb').read()
        if fn.endswith('.msa'):
            text = data.decode('ascii')
            for line in text.replace('\r\n', '\n').split('\n'):
                if line.startswith('MotionFileName'):
                    path = line.split('"')[1]
                    folder, name = path.replace('\\', '/').lower().rsplit('/', 2)[-2:]
                    motion = os.path.join(GF, 'd_', 'ymir work', 'npc', folder, name)
                    target = 'mot_%s_%s' % (folder, name)
                    if ('d:/ymir work/npc_mount/horse_guild/' + target) not in files:
                        put('d:/ymir work/npc_mount/horse_guild/' + target, open(motion, 'rb').read(),
                            'GF 26.1.11 d_/ymir work/npc/%s/%s' % (folder, name))
                    text = text.replace(path, 'D:\\Ymir Work\\npc_mount\\horse_guild\\' + target)
            data = text.encode('ascii')
            src_note = 'GF 26.1.11 d_/ymir work/npc_mount/horse_guild/%s, motion renamed' % fn
        else:
            src_note = 'GF 26.1.11 d_/ymir work/npc_mount/horse_guild/' + fn
        put('d:/ymir work/npc_mount/horse_guild/' + fn, data, src_note)
    with open(MANIFEST, 'w') as f:
        json.dump({'marker': 'MT2009_PLUS_HORSE40_V1', 'files': files}, f, indent=1, sort_keys=True)
        f.write('\n')
    print('konie: %d files staged, %.1f kB' % (len(files), sum(v['size'] for v in files.values()) / 1e3))


if __name__ == '__main__':
    main()
