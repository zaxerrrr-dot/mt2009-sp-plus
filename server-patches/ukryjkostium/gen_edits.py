#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/ukryjkostium (MT2009_PLUS_HIDE_COSTUME_V1) from the list
below; the developer's tool (the apply scripts read edits.json only). Every edit keeps its anchor ("old") inside
"new", so another patch anchored on the same line still finds it. After playerqol (its /kostiumy_ukryj) and
transmutacja (GetLookVnum)."""
import json
import os

M = 'MT2009_PLUS_HIDE_COSTUME_V1'
E = []


def after(path, tag, old, add):
    E.append({'file': path, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': old + add})


after('../../common/CommonDefines.h', 'define',
      '#define ENABLE_CONQUEROR_LEVEL // MT2009_PLUS_CHAMPION_V1 (define): Poziom Czempiona + Sung Ma (server-patches/czempion)\n',
      '// %s (define): Owsap\'s costume / hair / weapon skin / sash hiding (server-patches/ukryjkostium).\n'
      '#define ENABLE_HIDE_COSTUME_SYSTEM\n' % M)
HOOK = ('#ifdef ENABLE_HIDE_COSTUME_SYSTEM\n'
        '%(i)s// %(m)s (%(t)s): the hidden costume parts out (playerbot_hidecostume.cpp), before "Ukryj cudze".\n'
        '%(i)s{ void Mt2009HideCostumeParts(LPCHARACTER ch, DWORD* awPart); Mt2009HideCostumeParts(this, %(p)s.awPart); }\n'
        '#endif\n')
after('char.cpp', 'insert',
      '\t\taddPacket.awPart[CHR_EQUIPPART_ACCE] = GetPart(PART_ACCE);\n#endif\n',
      HOOK % {'i': '\t\t', 'm': M, 't': 'insert', 'p': 'addPacket'})
after('char.cpp', 'update',
      '\tpack.awPart[CHR_EQUIPPART_ACCE] = GetPart(PART_ACCE);\n#endif\n',
      HOOK % {'i': '\t', 'm': M, 't': 'update', 'p': 'pack'})
after('input_login.cpp', 'login',
      '\td->SetPhase(PHASE_GAME);\n',
      '#ifdef ENABLE_HIDE_COSTUME_SYSTEM\n'
      '\t// %s (login): the character\'s hidden parts from its quest flags, to the client and around.\n'
      '\t{ void Mt2009HideCostumeOnLogin(LPCHARACTER ch); Mt2009HideCostumeOnLogin(ch); }\n'
      '#endif\n' % M)
after('cmd_general.cpp', 'legacy',
      '\tconst BYTE mask = byMask ? (BYTE)(value & 7) : (value ? 7 : 0);\n',
      '#ifdef ENABLE_HIDE_COSTUME_SYSTEM\n'
      '\t// %s (legacy): the old client setting (kostiumy.cfg) is taken once per character as Owsap\'s quest flags;\n'
      '\t// the old mask (MT2009_PLUS_COSTUME_HIDE_V1/V2) stays empty, so its parts code never runs again.\n'
      '\t{ void Mt2009HideCostumeLegacy(LPCHARACTER ch, BYTE bMask); Mt2009HideCostumeLegacy(ch, mask); return; }\n'
      '#endif\n' % M)
after('cmd.cpp', 'declare',
      'ACMD(do_conqueror_stat);\nACMD(do_champion);\n',
      '#ifdef ENABLE_HIDE_COSTUME_SYSTEM\n// %s (declare): /hide_costume_part (playerbot_hidecostume.cpp).\n'
      'ACMD(do_hide_costume_part);\n#endif\n' % M)
after('cmd.cpp', 'table',
      '\t{ "champion",\tdo_champion,\t0,\t\tPOS_DEAD,\tGM_HIGH_WIZARD\t},\n',
      '#ifdef ENABLE_HIDE_COSTUME_SYSTEM\n\t// %s (table): Owsap\'s eye buttons of the costume window.\n'
      '\t{ "hide_costume_part",\tdo_hide_costume_part,\t0,\tPOS_DEAD,\tGM_PLAYER\t},\n#endif\n' % M)

HERE = os.path.dirname(os.path.abspath(__file__))
for e in E:
    assert e['marker'] in e['new'], e['marker']
json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1, ensure_ascii=False)
print('%d edits' % len(E))
