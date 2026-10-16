#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/yhelm100 (MT2009_PLUS_HELM100_CUBE_V1) from the code below; the
developer's tool (the apply scripts read edits.json only). Every anchor is checked against a patched engine tree
(after ysets and gaya) when one is given:

  python3 gen_edits.py [<engine game/src dir to check the anchors against>]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_HELM100_CUBE_V1'


def cstr(s):
    """a Polish text as a C string literal of cp1250 bytes (the sources are latin-1; the client reads cp1250)"""
    out = []
    for b in s.encode('cp1250'):
        if b == 0x22 or b == 0x5c:
            out.append('\\' + chr(b))
        elif 0x20 <= b < 0x7f:
            out.append(chr(b))
        else:
            out.append('\\%03o' % b)
    return '"' + ''.join(out) + '"'


FAIL_TEXT = cstr(u'Nie udało się. Materiały i Yang przepadły, przedmiot został w oknie.')

MAKE = '// ' + M + r''' (cube fail keep): round 15.10 #3 - a recipe with "fail_keep <vnum>" (Straznik Smokow
// Jaharr's Dragona helmets, cube.helm100.txt): the Yang, the Gaya and the other materials go either way, the recipe's
// item <vnum> (the helmet) only on a success - a failure leaves it in the inventory and in the window (wiki: the
// Dragona helmet stays when the refinement fails; the Smokow helmets are plain recipes - all is lost).
static bool Mt2009CubeMakeFailKeep(LPCHARACTER ch, CUBE_DATA* cube_proto, CUBE_VALUE* reward_value)
{
	LPITEM* items = ch->GetCubeItem();
	if (!Mt2009GayaCubeCheck(ch, cube_proto))
		return false;
	if (number(1, 100) <= cube_proto->percent)
	{
		cube_proto->remove_material(ch);
		Mt2009GayaCubeTake(ch, cube_proto);
		if (0 < cube_proto->gold)
			ch->ChangeGold(-(cube_proto->gold));
		ch->ChatPacket(CHAT_TYPE_COMMAND, "cube success %d %d", reward_value->vnum, reward_value->count);
		LPITEM new_item = ch->AutoGiveItem(reward_value->vnum, reward_value->count);
		LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(),
				reward_value->vnum, new_item ? new_item->GetID() : 0, reward_value->count, 1);
		return true;
	}
	for (size_t i = 0; i < cube_proto->item.size(); ++i)
		if (cube_proto->item[i].vnum != (DWORD)cube_proto->fail_keep)
			FN_remove_material(items, cube_proto->item[i].vnum, cube_proto->item[i].count);
	Mt2009GayaCubeTake(ch, cube_proto);
	if (0 < cube_proto->gold)
		ch->ChangeGold(-(cube_proto->gold));
	ch->ChatPacket(CHAT_TYPE_INFO, @FAIL@);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "cube fail");
	LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), reward_value->vnum, 0, 0, 0);
	return false;
}

// return new item
bool Cube_make (LPCHARACTER ch)
'''.replace('@FAIL@', FAIL_TEXT)

EDITS = [
    dict(file='cube.h', marker=M + ' (cube data)',
         old='\tint\t\t\t\t\t\tset_part = 0; // 1 weapon, 2 armour, 3 helmet\n',
         new='\tint\t\t\t\t\t\tset_part = 0; // 1 weapon, 2 armour, 3 helmet\n'
             '\tint\t\t\t\t\t\tfail_keep = 0; // ' + M + ' (cube data): this item of the recipe stays on a failure\n'),
    dict(file='cube.cpp', marker=M + ' (cube load)',
         old='\t\telse TOKEN("set_part")\n\t\t{\n\t\t\tcube_data->set_part = value1;\n\t\t}\n',
         new='\t\telse TOKEN("set_part")\n\t\t{\n\t\t\tcube_data->set_part = value1;\n\t\t}\n'
             '\t\telse TOKEN("fail_keep") // ' + M + ' (cube load)\n\t\t{\n\t\t\tcube_data->fail_keep = value1;\n\t\t}\n'),
    dict(file='cube.cpp', marker=M + ' (cube fail keep)',
         old='// return new item\nbool Cube_make (LPCHARACTER ch)\n',
         new=MAKE),
    dict(file='cube.cpp', marker=M + ' (cube make)',
         old='\tCUBE_VALUE\t*reward_value = cube_proto->reward_value();\n',
         new='\tCUBE_VALUE\t*reward_value = cube_proto->reward_value();\n'
             '\tif (cube_proto->fail_keep) // ' + M + ' (cube make): Jaharr\'s Dragona helmets - the helmet stays on a failure\n'
             '\t\treturn Mt2009CubeMakeFailKeep(ch, cube_proto, reward_value);\n'),
]


def check(src):
    ok = True
    texts = {}
    for e in EDITS:
        if e['file'] not in texts:
            texts[e['file']] = open(os.path.join(src, e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
        t = texts[e['file']]
        n = t.count(e['old'])
        if e['marker'] in t:
            print('already: %s %s' % (e['file'], e['marker']))
        elif n != 1:
            print('ANCHOR x%d: %s %s' % (n, e['file'], e['marker']))
            ok = False
        else:
            texts[e['file']] = t.replace(e['old'], e['new'])
    return ok


def main():
    if len(sys.argv) > 1 and not check(sys.argv[1]):
        sys.exit('anchors do not match - edits.json not written')
    for e in EDITS:
        e['new'].encode('latin-1')
    with open(os.path.join(HERE, 'edits.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(EDITS, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('edits.json: %d edits' % len(EDITS))


if __name__ == '__main__':
    main()
