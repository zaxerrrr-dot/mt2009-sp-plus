#!/usr/bin/env python3
"""gen_edits.py [<engine game/src>] - writes edits.json of server-patches/aura (MT2009_PLUS_AURA_V1) from the list
below; the developer's tool (the apply scripts read edits.json only). With a game/src it also checks that every
anchor is there exactly once (or the edit already is). Every edit keeps its anchor ("old") inside "new", so another
patch anchored on the same line still finds it."""
import json
import os
import sys

M = 'MT2009_PLUS_AURA_V1'
E = []


def edit(path, tag, old, new):
    E.append({'file': path, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new})


def after(path, tag, old, add):
    edit(path, tag, old, old + add)


def before(path, tag, old, add):
    edit(path, tag, old, add + old)


# ---- common ---------------------------------------------------------------------------------------------------------
after('../../common/CommonDefines.h', 'define',
      '#define ENABLE_HIDE_COSTUME_SYSTEM\n',
      '// %s (define): Szata Aury (server-patches/aura) - WEAR_COSTUME_AURA 27, COSTUME_AURA 5, the outfit\'s points,\n'
      '// Theowahdan\'s windows, the effect the others see (playerbot_aura.cpp). After ukryjkostium (the aura\'s eye).\n'
      '#define ENABLE_AURA_COSTUME_SYSTEM\n' % M)
after('../../common/length.h', 'wear',
      '\tWEAR_GLOVE,\t\t\t// 26\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\tWEAR_COSTUME_AURA,\t// 27 - %s (wear): the aura outfit (root/uiaura.py: EQUIPMENT_SLOT_START + 27)\n'
      '#endif\n' % M)
after('../../common/item_length.h', 'subtype',
      '#ifdef ENABLE_WEAPON_COSTUME_SYSTEM\n\tCOSTUME_WEAPON\t= 4,\n#endif\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\tCOSTUME_AURA\t= 5,\t// %s (subtype): Szata Aury (49101-49106), the official number\n'
      '#endif\n' % M)

# ---- game: the slot, the points, the equip rule, the clearing certificate ------------------------------------------------
after('item.cpp', 'wear position',
      '\t\telse if (GetSubType() == COSTUME_WEAPON)\n\t\t\treturn WEAR_COSTUME_WEAPON;\n#endif\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t\telse if (GetSubType() == COSTUME_AURA)\n'
      '\t\t\treturn WEAR_COSTUME_AURA; // %s (wear position)\n'
      '#endif\n' % M)
after('item.cpp', 'points',
      'void CItem::ModifyPoints(bool bAdd)\n{\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t// %s (points): an aura outfit gives its rate of the absorbed item\'s bonuses and nothing else\n'
      '\t// (playerbot_aura.cpp) - its attributes are that item\'s, never worn at their full value.\n'
      '\t{\n'
      '\t\tbool Mt2009AuraModifyPoints(LPITEM item, LPCHARACTER owner, bool bAdd);\n'
      '\t\tif (Mt2009AuraModifyPoints(this, m_pOwner, bAdd))\n'
      '\t\t\treturn;\n'
      '\t}\n'
      '#endif\n' % M)
after('char_item.cpp', 'equip subtype',
      '\t\t|| item->GetSubType() == COSTUME_WEAPON\n#endif\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t\t|| item->GetSubType() == COSTUME_AURA // %s (equip subtype): its own slot, no part of the body\n'
      '#endif\n' % M)
before('char_item.cpp', 'use',
       '\t// MT2009_PLUS_GOBLIN_V1 (use): the Treasure Ticket, the Goblin Key and its\n',
       '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
       '\t// %s (use): Swiadectwo Aury+ (89999) dragged onto an aura outfit clears its bonuses (playerbot_aura.cpp)\n'
       '\t{\n'
       '\t\tbool Mt2009AuraUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell, bool& bResult);\n'
       '\t\tbool bAuraResult = false;\n'
       '\t\tif (Mt2009AuraUseItem(this, item, DestCell, bAuraResult))\n'
       '\t\t\treturn bAuraResult;\n'
       '\t}\n'
       '#endif\n' % M)

# ---- game: what the others see, the rune drop ---------------------------------------------------------------------------
after('char.cpp', 'insert',
      '\t\tRankPointsOnInsert(this, ch);\n\t}\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t// %s (insert): a character wearing an aura outfit comes into a player\'s view with "AURA view <vid> <vnum>"\n'
      '\t// - the 3.0 exe draws the outfit\'s effect (playerbot_aura.cpp, root/uiaura.py).\n'
      '\tif (IsPC() && ch && ch->IsPC() && !d->IsBot())\n'
      '\t{\n'
      '\t\tvoid Mt2009AuraOnInsert(LPCHARACTER, LPCHARACTER);\n'
      '\t\tMt2009AuraOnInsert(this, ch);\n'
      '\t}\n'
      '#endif\n' % M)
after('char.cpp', 'update',
      'void CHARACTER::UpdatePacket()\n{\n\tif (GetSectree() == NULL) return;\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t// %s (update): the aura outfit the others see, sent around once per change (playerbot_aura.cpp)\n'
      '\t{ void Mt2009AuraOnUpdatePacket(LPCHARACTER); Mt2009AuraOnUpdatePacket(this); }\n'
      '#endif\n' % M)
after('char_battle.cpp', 'kill',
      '\t\t{ void RankPointsOnKill(LPCHARACTER, LPCHARACTER); RankPointsOnKill(pkQuestKiller, this); }\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t\t// %s (kill): Lodowa Runa Aury from every monster (pl-wiki "Drop alternatywny", playerbot_aura.cpp)\n'
      '\t\t{ void Mt2009AuraOnKill(LPCHARACTER, LPCHARACTER); Mt2009AuraOnKill(pkQuestKiller, this); }\n'
      '#endif\n' % M)

# ---- game: the quest function, the command ------------------------------------------------------------------------------
after('questlua.cpp', 'lua',
      '\t\t{ void RegisterChangeLookFunctions(); RegisterChangeLookFunctions(); }\n#endif\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t\t// %s (lua): game.open_aura - Theowahdan\'s aura windows (playerbot_aura.cpp).\n'
      '\t\t{ void RegisterAuraFunctions(); RegisterAuraFunctions(); }\n'
      '#endif\n' % M)
after('cmd.cpp', 'declare',
      'ACMD(do_changelook);\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '// %s (declare): /aura - Theowahdan\'s aura windows (playerbot_aura.cpp).\n'
      'ACMD(do_aura);\n'
      '#endif\n' % M)
after('cmd.cpp', 'table',
      '\t{ "transmutacja",\tdo_changelook,\t0,\tPOS_DEAD,\tGM_PLAYER\t},\n',
      '#ifdef ENABLE_AURA_COSTUME_SYSTEM\n'
      '\t// %s (table): the aura windows (in / out / accept / cancel).\n'
      '\t{ "aura",\tdo_aura,\t0,\tPOS_DEAD,\tGM_PLAYER\t},\n'
      '#endif\n' % M)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for e in E:
        assert e['marker'] in e['new'], e['marker']
        assert e['old'] in e['new'], e['marker']
    if len(sys.argv) > 1:
        for e in E:
            text = open(os.path.join(sys.argv[1], e['file']), 'rb').read().decode('latin-1')
            n = text.count(e['old']) + text.count(e['old'].replace('\n', '\r\n'))
            assert e['marker'] in text or n == 1, (e['marker'], n)
        print('anchors ok')
    with open(os.path.join(here, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('%d edits' % len(E))


if __name__ == '__main__':
    main()
