#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/transmutacja (MT2009_PLUS_CHANGE_LOOK_V1) from the list
below; the developer's tool (the apply scripts read edits.json only). Every edit keeps its anchor ("old") inside
"new" where it can, so another patch anchored on the same line still finds it."""
import json
import os

M = 'MT2009_PLUS_CHANGE_LOOK_V1'
E = []


def edit(path, tag, old, new):
    E.append({'file': path, 'marker': '%s (%s)' % (M, tag), 'old': old, 'new': new})


def after(path, tag, old, add):
    edit(path, tag, old, old + add)


def before(path, tag, old, add):
    edit(path, tag, old, add + old)


# ---- common ---------------------------------------------------------------------------------------------------------
after('../../common/CommonDefines.h', 'define',
      '#define ENABLE_CONQUEROR_LEVEL // MT2009_PLUS_CHAMPION_V1 (define): Poziom Czempiona + Sung Ma (server-patches/czempion)\n',
      '// %s (define): Transmutacja (server-patches/transmutacja) - the look of an item (CItem::m_dwTransmutation,\n'
      '// player.item.transmutation); the Ikarus shop\'s own ENABLE_CHANGELOOK_SYSTEM lines carry it through its windows.\n'
      '#define ENABLE_CHANGELOOK_SYSTEM\n' % M)

edit('../../common/tables.h', 'player item',
     '\tDWORD\towner;\n} TPlayerItem;',
     '\tDWORD\towner;\n'
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
     '\t// %s (player item): the look (another item\'s vnum, 0 none) - player.item.transmutation; the db core\n'
     '\t// and the game core from one header. The Ikarus shop\'s items (TShopPlayerItem) inherit it, so the 3.0 exe\'s\n'
     '\t// ikashop::TPlayerItem has it too (client-patches/exe Packet.h).\n'
     '\tDWORD\tdwTransmutation;\n'
     '#endif\n'
     '} TPlayerItem;' % M)

# ---- db -------------------------------------------------------------------------------------------------------------
edit('../../db/src/ClientManagerPlayer.cpp', 'load',
     '\t\titem.owner\t\t= dwPID;\n',
     '\t\t// %s (load): the look, when the query names it (every item SELECT of this core does)\n'
     '\t\titem.dwTransmutation = 0;\n'
     '\t\tif (cur < (int) mysql_num_fields(res) && row[cur])\n'
     '\t\t\tstr_to_number(item.dwTransmutation, row[cur++]);\n\n'
     '\t\titem.owner\t\t= dwPID;\n' % M)
SEL = 'attrtype5,attrvalue5,attrtype6,attrvalue6 "\n'
edit('../../db/src/ClientManagerPlayer.cpp', 'select 1',
     '\t\t\t\t\t"SELECT id,`window`+0,pos,count,vnum,socket0,socket1,socket2,attrtype0,attrvalue0,attrtype1,attrvalue1,attrtype2,attrvalue2,attrtype3,attrvalue3,attrtype4,attrvalue4,' + SEL,
     '\t\t\t\t\t"SELECT id,`window`+0,pos,count,vnum,socket0,socket1,socket2,attrtype0,attrvalue0,attrtype1,attrvalue1,attrtype2,attrvalue2,attrtype3,attrvalue3,attrtype4,attrvalue4,'
     'attrtype5,attrvalue5,attrtype6,attrvalue6,transmutation " // %s (select 1)\n' % M)
edit('../../db/src/ClientManagerPlayer.cpp', 'select 2',
     '\t\t\t\t"SELECT id,`window`+0,pos,count,vnum,socket0,socket1,socket2,attrtype0,attrvalue0,attrtype1,attrvalue1,attrtype2,attrvalue2,attrtype3,attrvalue3,attrtype4,attrvalue4,' + SEL,
     '\t\t\t\t"SELECT id,`window`+0,pos,count,vnum,socket0,socket1,socket2,attrtype0,attrvalue0,attrtype1,attrvalue1,attrtype2,attrvalue2,attrtype3,attrvalue3,attrtype4,attrvalue4,'
     'attrtype5,attrvalue5,attrtype6,attrvalue6,transmutation " // %s (select 2)\n' % M)
edit('../../db/src/ClientManager.cpp', 'safebox select',
     '\t\t\t\t"attrtype6, attrvalue6 "\n\t\t\t\t"FROM item%s WHERE owner_id=%d AND `window`=\'%s\'",',
     '\t\t\t\t"attrtype6, attrvalue6, transmutation " // %s (safebox select)\n\t\t\t\t"FROM item%%s WHERE owner_id=%%d AND `window`=\'%%s\'",' % M)
for path in ('../../db/src/ClientManager.cpp', '../../db/src/Cache.cpp'):
    edit(path, 'save',
         '"attrtype6={}, attrvalue6={} ")',
         '"attrtype6={}, attrvalue6={}, transmutation={} ") // %s (save): the look' % M)
    edit(path, 'save value',
         'p->aAttr[6].bType, p->aAttr[6].sValue\n',
         'p->aAttr[6].bType, p->aAttr[6].sValue,\n\t\t\t\t\t\t\t\t\t\t\t\t\t\tp->dwTransmutation // %s (save value)\n' % M)
# the Ikarus shop's ENABLE_CHANGELOOK_SYSTEM lines name the column `trans` in two of its three queries
edit('../../db/src/IkarusShopCache.cpp', 'ikashop safebox column',
     'query += " , `trans` ";',
     'query += " , `transmutation` "; // %s (ikashop safebox column)' % M)
edit('../../db/src/ClientManagerIkarusShop.cpp', 'ikashop auction column',
     'query += "i.`trans`, ";',
     'query += "i.`transmutation`, "; // %s (ikashop auction column)' % M)

# ---- game: the item -------------------------------------------------------------------------------------------------
after('item.h', 'item',
      '\t\tvoid        SetChangingAttr(bool changing) { m_bIsChangingAttr = changing; }\n',
      '\n#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
      '\t// %s (item): the look - another item\'s vnum (0: its own), drawn on the character (PART_MAIN /\n'
      '\t// PART_WEAPON, the mount) and shown in the tooltip; saved as player.item.transmutation (TPlayerItem).\n'
      '\tpublic:\n'
      '\t\tvoid\t\tSetTransmutation(DWORD dwVnum)\t{ m_dwTransmutation = dwVnum; }\n'
      '\t\tDWORD\t\tGetTransmutation() const\t\t{ return m_dwTransmutation; }\n'
      '\t\tDWORD\t\tGetLookVnum() const\t\t\t\t{ return m_dwTransmutation ? m_dwTransmutation : GetVnum(); }\n'
      '\tprotected:\n'
      '\t\tDWORD\t\tm_dwTransmutation = 0;\n'
      '\tpublic:\n'
      '#endif\n' % M)
after('item.cpp', 'init',
      '\tm_bSkipSave = false;\n\tm_dwLastOwnerPID = 0;\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tm_dwTransmutation = 0; // %s (init)\n#endif\n' % M)
after('item.cpp', 'update packet',
      '\tthecore_memcpy(pack.aAttr, GetAttributes(), sizeof(pack.aAttr));\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tpack.dwTransmutation = GetTransmutation(); // %s (update packet)\n#endif\n' % M)
before('item.cpp', 'parts',
       '\t// MT2009_PLUS_COSTUME_HIDE_V1 (hook): with the costumes hidden, the armour\n',
       '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
       '\t// %s (parts): a transmuted weapon, armour or costume worn or taken off - the body and the weapon\n'
       '\t// every player sees are the looks (playerbot_changelook.cpp; nothing changes without a look).\n'
       '\t{\n'
       '\t\tvoid Mt2009ChangeLookRefreshParts(LPCHARACTER ch, LPITEM self, LPITEM leaving);\n'
       '\t\tif (m_pOwner && (m_pProto->bType == ITEM_WEAPON || m_pProto->bType == ITEM_ARMOR || m_pProto->bType == ITEM_COSTUME))\n'
       '\t\t\tMt2009ChangeLookRefreshParts(m_pOwner, this, bAdd ? NULL : this);\n'
       '\t}\n'
       '#endif\n\n' % M)
# "Ukryj cudze" (playerqol, MT2009_PLUS_COSTUME_VIEW_OTHERS_V1): the armour and the weapon under a costume as they look
edit('item.cpp', 'plain body',
     '\t\tconst DWORD v = body ? body->GetVnum() : ch->GetOriginalPart(PART_MAIN);\n',
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
     '\t\tconst DWORD v = body ? body->GetLookVnum() : ch->GetOriginalPart(PART_MAIN); // %s (plain body)\n'
     '#else\n'
     '\t\tconst DWORD v = body ? body->GetVnum() : ch->GetOriginalPart(PART_MAIN);\n'
     '#endif\n' % M)
edit('item.cpp', 'plain weapon',
     '\t\tconst DWORD v = weapon ? weapon->GetVnum() : 0;\n',
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
     '\t\tconst DWORD v = weapon ? weapon->GetLookVnum() : 0; // %s (plain weapon)\n'
     '#else\n'
     '\t\tconst DWORD v = weapon ? weapon->GetVnum() : 0;\n'
     '#endif\n' % M)
after('item_manager.cpp', 'save',
      '\tthecore_memcpy(t.aAttr, item->GetAttributes(), sizeof(t.aAttr));\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tt.dwTransmutation = item->GetTransmutation(); // %s (save)\n#endif\n' % M)
after('input_db.cpp', 'load',
      '\t\titem->SetSockets(p->alSockets);\n\t\titem->SetAttributes(p->aAttr);\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\titem->SetTransmutation(p->dwTransmutation); // %s (load): before it is worn\n#endif\n' % M)
for box in ('Safebox', 'Mall'):
    edit('char.cpp', 'load %s' % box.lower(),
         '\t\t\titem->SetAttributes(pItems->aAttr);\n\n\t\t\tif (!m_pk%s->Add' % box,
         '\t\t\titem->SetAttributes(pItems->aAttr);\n'
         '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\titem->SetTransmutation(pItems->dwTransmutation); // %s (load %s)\n#endif\n\n'
         '\t\t\tif (!m_pk%s->Add' % (M, box.lower(), box))

# ---- game: the packets (the 3.0 exe's Packet.h has the same fields) -----------------------------------------------------
for struct in ('TPacketGCItemSet', 'TPacketGCItemUpdate'):
    edit('packet.h', 'packet %s' % struct,
         '\tTPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_MAX_NUM];\n} %s;' % struct,
         '\tTPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_MAX_NUM];\n'
         '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tDWORD\tdwTransmutation; // %s (packet %s)\n#endif\n} %s;' % (M, struct, struct))
edit('packet.h', 'packet exchange',
     '\tTPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_MAX_NUM];\n};\n\nenum EPacketTradeSubHeaders',
     '\tTPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_MAX_NUM];\n'
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tDWORD\tdwTransmutation; // %s (packet exchange)\n#endif\n};\n\nenum EPacketTradeSubHeaders' % M)
after('char_item.cpp', 'item set',
      '\t\t\tthecore_memcpy(pack.aAttr, pItem->GetAttributes(), sizeof(pack.aAttr));\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\tpack.dwTransmutation = pItem->GetTransmutation(); // %s (item set)\n#endif\n' % M)
after('safebox.cpp', 'safebox add',
      '\tpack.anti_flags\t= pkItem->GetAntiFlag();\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tpack.dwTransmutation = pkItem->GetTransmutation(); // %s (safebox add)\n#endif\n' % M)
after('safebox.cpp', 'safebox move',
      '\tpack.anti_flags = pkItem->GetAntiFlag();\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\tpack.dwTransmutation = pkItem->GetTransmutation(); // %s (safebox move)\n#endif\n' % M)
after('exchange.cpp', 'exchange add',
      '\t\tthecore_memcpy(&pack_exchg.aAttr, ((LPITEM) pvData)->GetAttributes(), sizeof(pack_exchg.aAttr));\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\tpack_exchg.dwTransmutation = ((LPITEM) pvData)->GetTransmutation(); // %s (exchange add)\n#endif\n' % M)
after('exchange.cpp', 'exchange other',
      '\t\tmemset(&pack_exchg.aAttr, 0, sizeof(pack_exchg.aAttr));\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\tpack_exchg.dwTransmutation = 0; // %s (exchange other)\n#endif\n' % M)
# the Ikarus shop: its ENABLE_CHANGELOOK_SYSTEM line was written for another struct (sitem.item)
edit('ikarus_shop_manager.cpp', 'ikashop add',
     '\t\tsitem.item.dwTransmutation = item->GetTransmutation();\n',
     '\t\tsitem.dwTransmutation = item->GetTransmutation(); // %s (ikashop add)\n' % M)

# ---- game: equip, the reversal items, the mounts ------------------------------------------------------------------------
after('char_item.cpp', 'equip',
      '\tif (FN_check_item_sex(this, item) == false)\n\t{\n'
      '\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You are not able to use that item because you do not have the right gender."));\n'
      '\t\tif (bDSTrace) sys_err("[DS_EQUIP_TRACE] return false at FN_check_item_sex()");\n\t\treturn false;\n\t}\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
      '\t// %s (equip): the look must fit the wearer too (its class; a costume look its gender)\n'
      '\t{\n\t\tbool Mt2009ChangeLookCanEquip(LPCHARACTER ch, LPITEM item);\n'
      '\t\tif (!Mt2009ChangeLookCanEquip(this, item))\n\t\t\treturn false;\n\t}\n'
      '#endif\n' % M)
after('char_item.cpp', 'use',
      '\t\treturn Mt2009PlusUseSashSkin(this, item, DestCell);\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
      '\t// %s (use): Anulacja Transmutacji / Polimorfii dragged onto an item; the tickets (the window\'s)\n'
      '\t{\n\t\tbool Mt2009ChangeLookUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell, bool& bResult);\n'
      '\t\tbool bChangeLookResult = false;\n'
      '\t\tif (item->GetType() == ITEM_USE && Mt2009ChangeLookUseItem(this, item, DestCell, bChangeLookResult))\n'
      '\t\t\treturn bChangeLookResult;\n\t}\n'
      '#endif\n' % M)
MOB = 'DWORD Mt2009MountMobVnum(LPITEM seal); // %s (mount): the look\'s mount (playerbot_changelook.cpp)\n'
edit('char_item.cpp', 'mount equip',
     '\t\tconst DWORD mobVnum = item->GetValue(1);\n',
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t' + (MOB % M) + '\t\tconst DWORD mobVnum = Mt2009MountMobVnum(item);\n'
     '#else\n\t\tconst DWORD mobVnum = item->GetValue(1);\n#endif\n')
E[-1]['marker'] = '%s (mount equip)' % M
E[-1]['new'] = E[-1]['new'].replace('(mount)', '(mount equip)')
for tag, old in (('mount summon', '\tDWORD mobVnum = mountItem->GetValue(1);\n\n\tif (0 == mobVnum)\n\t{\n'),
                 ('mount unsummon', '\tDWORD mobVnum = mountItem->GetValue(1);\n\n\tif (0 == mobVnum)\n\t\treturn;\n\n\tif (GetMountVnum() == mobVnum)'),
                 ('mount check', '\tDWORD mobVnum = mountItem->GetValue(1);\n\n\tif (0 == mobVnum)\n\t\treturn;\n\n\tif (mountSystem->CountSummoned() == 0)')):
    rest = old[len('\tDWORD mobVnum = mountItem->GetValue(1);\n'):]
    edit('MountSystem.cpp', tag, old,
         '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t' + (MOB % M).replace('(mount)', '(%s)' % tag) +
         '\tDWORD mobVnum = Mt2009MountMobVnum(mountItem);\n#else\n\tDWORD mobVnum = mountItem->GetValue(1);\n#endif\n' + rest)
edit('cmd_general.cpp', 'mount ride',
     '\t\t\tDWORD mobVnum = mountItem->GetValue(1);\n',
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\t' + (MOB % M).replace('(mount)', '(mount ride)') +
     '\t\t\tDWORD mobVnum = Mt2009MountMobVnum(mountItem);\n#else\n\t\t\tDWORD mobVnum = mountItem->GetValue(1);\n#endif\n')
edit('cmd_general.cpp', 'mount ride same key',
     '\t\t\t\t\tDWORD mobVnum = item->GetValue(1);\n',
     '#ifdef ENABLE_CHANGELOOK_SYSTEM\n\t\t\t\t\t' + (MOB % M).replace('(mount)', '(mount ride same key)') +
     '\t\t\t\t\tDWORD mobVnum = Mt2009MountMobVnum(item);\n#else\n\t\t\t\t\tDWORD mobVnum = item->GetValue(1);\n#endif\n')
edit('cmd_general.cpp', 'mount get off',
     '(DWORD)pkWornSeal->GetValue(1) == ch->GetMountVnum() &&',
     '(DWORD)Mt2009MountMobVnum(pkWornSeal) == ch->GetMountVnum() && // %s (mount get off)' % M)
before('cmd_general.cpp', 'mount declare',
       'ACMD(do_ride)\n',
       '#ifdef ENABLE_CHANGELOOK_SYSTEM\nDWORD Mt2009MountMobVnum(LPITEM seal); // %s (mount declare)\n'
       '#else\n#define Mt2009MountMobVnum(seal) ((seal)->GetValue(1))\n#endif\n' % M)

# ---- game: the window, the quest function, the command ------------------------------------------------------------------
after('questlua.cpp', 'lua',
      '\t\t{ void RegisterChampionFunctions(); RegisterChampionFunctions(); }\n',
      '#ifdef ENABLE_CHANGELOOK_SYSTEM\n'
      '\t\t// %s (lua): game.open_changelook, item.get_changelook_vnum (playerbot_changelook.cpp).\n'
      '\t\t{ void RegisterChangeLookFunctions(); RegisterChangeLookFunctions(); }\n'
      '#endif\n' % M)
after('cmd.cpp', 'declare',
      'ACMD(do_conqueror_stat);\nACMD(do_champion);\n',
      '// %s (declare): /transmutacja - the window at Teowaden (playerbot_changelook.cpp).\n'
      'ACMD(do_changelook);\n' % M)
after('cmd.cpp', 'table',
      '\t{ "champion",\tdo_champion,\t0,\t\tPOS_DEAD,\tGM_HIGH_WIZARD\t},\n',
      '\t// %s (table): the transmutation window (in / out / accept / cancel).\n'
      '\t{ "transmutacja",\tdo_changelook,\t0,\tPOS_DEAD,\tGM_PLAYER\t},\n' % M)

HERE = os.path.dirname(os.path.abspath(__file__))
for e in E:
    assert e['marker'] in e['new'], e['marker']
    assert e['old'] != e['new'], e['marker']
json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1, ensure_ascii=False)
print('%d edits' % len(E))
