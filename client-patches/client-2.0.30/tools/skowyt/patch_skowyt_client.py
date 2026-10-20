# -*- coding: utf-8 -*-
# MT2009_PLUS_SKOWYT_CLIENT_V1 - Smoczy Skowyt (shaman skill 93, "paeryong") in the client's locale/pl/skilldesc.txt:
# its attribute column (the 11th) gets CAN_USE_FOR_ME next to ATTACK_SKILL|NEED_TARGET.
#
# Why: NEED_TARGET (client 2.0.26, server-patches/dragonroartarget) made the exe refuse the skill with no target
# ("NEED_TARGET"). The owner (15 October): with no target selected Skowyt is cast round the Shaman. In the exe
# (UserInterface/PythonPlayerSkill.cpp, CPythonPlayer::__UseSkill) a NEED_TARGET skill with no alive target falls
# back to the caster when CanUseForMe() - the target and the fly target become the Shaman, its VID goes to the
# server, which then splashes round the Shaman (GetSelfOnlySkillVictim: no attackable GetTarget()). With a target
# nothing changes: the exe walks into reach (skilltable 1800) and casts at it. The burst itself plays at that fly
# target, once (the paeryong*.msa of build_skowyt_pack.py).
#
# Run on a plain copy (clientY.sh: in the data chain after ../skilldesc/patch_skilldesc_client.py):
#   python3 <repo>/client-patches/client-2.0.30/tools/skowyt/patch_skowyt_client.py <skilldesc.txt> [<out dir>]
# Without an out dir the file is rewritten in place (only when something changed). A second run changes nothing.
import io
import os
import sys

VNUM = u'93'
COLUMN = 10         # 0 vnum, 1 job, 2-4 names, 5 description, 6-8 level texts, 9 empty, 10 attributes
ADD = u'CAN_USE_FOR_ME'


def patch(data):
    text = data.decode('cp1250')
    nl = u'\r\n' if u'\r\n' in text else u'\n'
    lines = text.split(nl)
    found = 0
    changed = 0
    for i, line in enumerate(lines):
        cols = line.split(u'\t')
        if cols[0].strip() != VNUM or len(cols) <= COLUMN:
            continue
        found += 1
        flags = [f for f in cols[COLUMN].split(u'|') if f]
        if u'ATTACK_SKILL' not in flags:
            raise SystemExit('skilldesc.txt: skill 93 attributes %r - not the attack skill expected' % cols[COLUMN])
        if ADD not in flags:
            flags.append(ADD)
            cols[COLUMN] = u'|'.join(flags)
            lines[i] = u'\t'.join(cols)
            changed += 1
    if found != 1:
        raise SystemExit('skilldesc.txt: %d lines for skill 93' % found)
    return nl.join(lines).encode('cp1250'), changed


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_skowyt_client.py <skilldesc.txt> [<out dir>]')
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else None
    with open(path, 'rb') as f:
        data, changed = patch(f.read())
    target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
    if changed or out_dir:
        with open(target, 'wb') as f:
            f.write(data)
    print('skowyt: skilldesc.txt %d line(s) changed' % changed)


if __name__ == '__main__':
    main()
