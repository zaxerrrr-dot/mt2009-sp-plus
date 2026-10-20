#!/usr/bin/env python3
"""gen_edits.py [<game/src>] -- writes edits.json of server-patches/zestawy (MT2009_PLUS_COSTUME_SET_V2, README.md):
the costume sets as on the global server. With a game/src dir it also checks that every anchor is there exactly once
(or its marker already is) after the edits before it. The C++ of the set table lives in SETS_CODE below."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_COSTUME_SET_V2'

SETS_CODE = r'''// MT2009_PLUS_COSTUME_SET_V2 (sets): the costume sets as on the Polish global server (the owner, 20 October
// 2026: "dokladnie tak samo jak na globalu, czyli rozne stopnie bonusow i rozne bonusy dla danego zestawu"; his
// sheet Metin2_Zestawy_kostiumow.xlsx, tools/zestawy/gen_zestawy.py). A set has up to six parts - costume, hair,
// weapon skin, pet, mount, ring / amulet, sash - each a list of alternatives; the parts worn together give the
// grade of their count (2..6), each grade its own bonuses (the whole grade, not added to the lower ones). Counted:
// the worn costume, hair, weapon skin, mount and sash, both unique slots and the summoned pet's seal. The sets are
// the "#Z" lines of costume_sets.txt (comments to the V1 reader above, which the bots still ask); a V1 line whose
// vnums no "#Z" set claims stays a two-part set (costume + hair) with the old +800 HP / +15 attack value. The set
// with the most parts worn counts. Affect 545 as in V1 (not saved): its first entry has no point and the value
// set * 10 + parts (the client's affect bar names the set and its grade - uiaffectbar.py, costume_set_bonus.py),
// then one entry per bonus; the drop chance is no point - GetDropPct asks Mt2009PlusCostumeSetDropBonus.
// Judged when an item of a set is put on (CItem::ModifyPoints outside ComputePoints), taken off (CItem::Unequip,
// once it has left its slot) and at the end of every outermost ComputePoints (a pet called or sent away, the
// login) - never in the middle of a ComputePoints, where an affect put on would count twice.
#include "PetSystem.h"

int g_iMt2009PlusComputeDepth = 0;	// CHARACTER::ComputePoints nesting (char.cpp, MT2009_PLUS_COSTUME_SET_V2 (depth))

struct TMt2009PlusSetBonus
{
	BYTE bPoint;
	bool bDrop;
	long lValue;
};

struct TMt2009PlusSetDef
{
	int id;
	std::string name;
	std::vector<std::set<DWORD> > parts;
	std::map<int, std::vector<TMt2009PlusSetBonus> > grades;
};

struct TMt2009PlusSetTable
{
	bool loaded;
	std::vector<TMt2009PlusSetDef> sets;
	std::map<DWORD, std::vector<size_t> > byVnum;
	TMt2009PlusSetTable() : loaded(false) {}
};

static int Mt2009PlusSetPoint(const std::string& name)
{
#define MT2009_SET_POINT(p) { #p, p }
	static const struct { const char* name; int point; } s_points[] = {
		MT2009_SET_POINT(POINT_MAX_HP), MT2009_SET_POINT(POINT_ATT_SPEED), MT2009_SET_POINT(POINT_MOV_SPEED),
		MT2009_SET_POINT(POINT_CASTING_SPEED), MT2009_SET_POINT(POINT_HP_REGEN), MT2009_SET_POINT(POINT_STUN_PCT),
		MT2009_SET_POINT(POINT_CRITICAL_PCT), MT2009_SET_POINT(POINT_PENETRATE_PCT), MT2009_SET_POINT(POINT_STEAL_HP),
		MT2009_SET_POINT(POINT_RESIST_FIRE), MT2009_SET_POINT(POINT_RESIST_ICE), MT2009_SET_POINT(POINT_ATT_GRADE_BONUS),
		MT2009_SET_POINT(POINT_MAGIC_ATT_GRADE_BONUS), MT2009_SET_POINT(POINT_ATTBONUS_MONSTER),
		MT2009_SET_POINT(POINT_ATTBONUS_STONE), MT2009_SET_POINT(POINT_ATTBONUS_BOSS),
		MT2009_SET_POINT(POINT_RAMADAN_CANDY_BONUS_EXP), MT2009_SET_POINT(POINT_SKILL_DAMAGE_BONUS),
		MT2009_SET_POINT(POINT_NORMAL_HIT_DAMAGE_BONUS), MT2009_SET_POINT(POINT_MELEE_MAGIC_ATT_BONUS_PER),
		MT2009_SET_POINT(POINT_ENCHANT_ELECT), MT2009_SET_POINT(POINT_ENCHANT_FIRE), MT2009_SET_POINT(POINT_ENCHANT_ICE),
		MT2009_SET_POINT(POINT_ENCHANT_WIND), MT2009_SET_POINT(POINT_ENCHANT_EARTH), MT2009_SET_POINT(POINT_ENCHANT_DARK),
	};
#undef MT2009_SET_POINT
	for (size_t i = 0; i < sizeof(s_points) / sizeof(s_points[0]); ++i)
		if (name == s_points[i].name)
			return s_points[i].point;
	return -1;
}

static void Mt2009PlusSetSplit(const std::string& text, char sep, std::vector<std::string>& out)
{
	out.clear();
	std::string cur;
	for (size_t i = 0; i <= text.size(); ++i)
	{
		const char c = i < text.size() ? text[i] : sep;
		if (c == sep)
		{
			out.push_back(cur);
			cur.clear();
		}
		else if (c != '\r' && c != '\n')
			cur += c;
	}
}

static void Mt2009PlusSetVnums(const std::string& field, std::set<DWORD>& into)
{
	std::vector<std::string> v;
	Mt2009PlusSetSplit(field, ',', v);
	for (size_t i = 0; i < v.size(); ++i)
		if (!v[i].empty())
			into.insert((DWORD)strtoul(v[i].c_str(), NULL, 10));
}

static const TMt2009PlusSetTable& Mt2009PlusSetTable()
{
	static TMt2009PlusSetTable t;
	if (t.loaded)
		return t;
	t.loaded = true;
	const std::string path = LocaleService_GetBasePath() + "/costume_sets.txt";
	FILE* fp = fopen(path.c_str(), "rb");
	if (!fp)
	{
		sys_err("COSTUME_SET_V2: no %s - no sets", path.c_str());
		return t;
	}
	std::vector<std::string> lines;
	char buf[8192];
	while (fgets(buf, sizeof(buf), fp))
		lines.push_back(buf);
	fclose(fp);

	std::map<int, size_t> byId;
	std::set<DWORD> claimed;
	std::vector<std::string> f;
	// the "#Z" sets: "#Z<TAB>S<TAB>id<TAB>name", "#Z<TAB>P<TAB>id<TAB>vnums", "#Z<TAB>B<TAB>id<TAB>parts<TAB>POINT_x|DROP<TAB>value"
	for (size_t l = 0; l < lines.size(); ++l)
	{
		if (lines[l].compare(0, 3, "#Z\t") != 0)
			continue;
		Mt2009PlusSetSplit(lines[l], '\t', f);
		if (f.size() < 4)
			continue;
		const int id = atoi(f[2].c_str());
		if (f[1] == "S")
		{
			TMt2009PlusSetDef d;
			d.id = id;
			d.name = f[3];
			byId[id] = t.sets.size();
			t.sets.push_back(d);
			continue;
		}
		std::map<int, size_t>::const_iterator it = byId.find(id);
		if (it == byId.end())
		{
			sys_err("COSTUME_SET_V2: line %u - set %d not named yet", (unsigned int)(l + 1), id);
			continue;
		}
		TMt2009PlusSetDef& d = t.sets[it->second];
		if (f[1] == "P")
		{
			d.parts.push_back(std::set<DWORD>());
			Mt2009PlusSetVnums(f[3], d.parts.back());
			claimed.insert(d.parts.back().begin(), d.parts.back().end());
		}
		else if (f[1] == "B" && f.size() >= 6)
		{
			TMt2009PlusSetBonus b;
			b.bDrop = f[4] == "DROP";
			const int point = b.bDrop ? 0 : Mt2009PlusSetPoint(f[4]);
			if (point < 0)
			{
				sys_err("COSTUME_SET_V2: line %u - unknown point %s", (unsigned int)(l + 1), f[4].c_str());
				continue;
			}
			b.bPoint = (BYTE)point;
			b.lValue = atol(f[5].c_str());
			d.grades[atoi(f[3].c_str())].push_back(b);
		}
	}
	// the V1 lines (name<TAB>bodies<TAB>hairs) no "#Z" set claims: two parts, +800 HP / +15 attack value as before
	int legacy = 0, index = 0;
	for (size_t l = 0; l < lines.size(); ++l)
	{
		if (lines[l].empty() || lines[l][0] == '#' || lines[l][0] == '\r' || lines[l][0] == '\n')
			continue;
		Mt2009PlusSetSplit(lines[l], '\t', f);
		if (f.size() < 3)
			continue;
		const int id = 100 + index++;	// the V1 reader's order (the client: costume_set_bonus.py LEGACY_BASE)
		std::set<DWORD> bodies, hairs, all;
		Mt2009PlusSetVnums(f[1], all);
		for (std::set<DWORD>::const_iterator v = all.begin(); v != all.end(); ++v)
			if (claimed.find(*v) == claimed.end())
				bodies.insert(*v);
		all.clear();
		Mt2009PlusSetVnums(f[2], all);
		for (std::set<DWORD>::const_iterator v = all.begin(); v != all.end(); ++v)
			if (claimed.find(*v) == claimed.end())
				hairs.insert(*v);
		if (bodies.empty() || hairs.empty())
			continue;
		TMt2009PlusSetDef d;
		d.id = id;
		d.name = f[0];
		d.parts.push_back(bodies);
		d.parts.push_back(hairs);
		TMt2009PlusSetBonus hp = { (BYTE)POINT_MAX_HP, false, MT2009_PLUS_COSTUME_SET_HP };
		TMt2009PlusSetBonus att = { (BYTE)POINT_ATT_GRADE_BONUS, false, MT2009_PLUS_COSTUME_SET_ATT };
		d.grades[2].push_back(hp);
		d.grades[2].push_back(att);
		t.sets.push_back(d);
		++legacy;
	}
	for (size_t s = 0; s < t.sets.size(); ++s)
		for (size_t p = 0; p < t.sets[s].parts.size(); ++p)
			for (std::set<DWORD>::const_iterator v = t.sets[s].parts[p].begin(); v != t.sets[s].parts[p].end(); ++v)
			{
				std::vector<size_t>& in = t.byVnum[*v];
				if (in.empty() || in.back() != s)
					in.push_back(s);
			}
	sys_log(0, "COSTUME_SET_V2: %u sets (%d of the old two-part ones), %u items from %s", (unsigned int)t.sets.size(),
			legacy, (unsigned int)t.byVnum.size(), path.c_str());
	return t;
}

// the vnums that count: the worn looks, both unique slots, every summoned pet's seal
static void Mt2009PlusSetWorn(LPCHARACTER ch, std::vector<DWORD>& out)
{
	static const int s_aiSlots[] = {
		WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR,
#ifdef ENABLE_MOUNT_COSTUME_SYSTEM
		WEAR_COSTUME_MOUNT,
#endif
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		WEAR_COSTUME_ACCE,
#endif
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
		WEAR_COSTUME_WEAPON,
#endif
		WEAR_UNIQUE1, WEAR_UNIQUE2,
	};
	for (size_t i = 0; i < sizeof(s_aiSlots) / sizeof(s_aiSlots[0]); ++i)
		if (LPITEM item = ch->GetWear(s_aiSlots[i]))
			out.push_back(item->GetVnum());
#ifdef __PET_SYSTEM__
	CPetSystem* pets = ch->GetPetSystem();
	if (!pets || !pets->CountSummoned())
		return;
	for (WORD i = 0; i < INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetInventoryItem(i);
		if (!item || item->GetType() != ITEM_PET || (item->GetSubType() != PET_PAY && item->GetSubType() != PET_UPBRINGING))
			continue;
		CPetActor* pet = pets->GetByVnum(item->GetValue(0));
		if (pet && pet->IsSummoned() && pet->GetSummonItemVID() == item->GetVID())
			out.push_back(item->GetVnum());
	}
#endif
}

static const std::vector<TMt2009PlusSetBonus>* Mt2009PlusSetGrade(const TMt2009PlusSetDef& d, int parts)
{
	for (int g = parts; g >= 2; --g)
	{
		std::map<int, std::vector<TMt2009PlusSetBonus> >::const_iterator it = d.grades.find(g);
		if (it != d.grades.end() && !it->second.empty())
			return &it->second;
	}
	return NULL;
}

// the set worn now: the one with the most parts that has a grade for them; 0 when none
static long Mt2009PlusSetWanted(LPCHARACTER ch)
{
	const TMt2009PlusSetTable& t = Mt2009PlusSetTable();
	std::vector<DWORD> worn;
	Mt2009PlusSetWorn(ch, worn);
	std::map<size_t, std::set<size_t> > got;	// set -> parts worn
	for (size_t i = 0; i < worn.size(); ++i)
	{
		std::map<DWORD, std::vector<size_t> >::const_iterator it = t.byVnum.find(worn[i]);
		if (it == t.byVnum.end())
			continue;
		for (size_t s = 0; s < it->second.size(); ++s)
		{
			const TMt2009PlusSetDef& d = t.sets[it->second[s]];
			for (size_t p = 0; p < d.parts.size(); ++p)
				if (d.parts[p].find(worn[i]) != d.parts[p].end())
					got[it->second[s]].insert(p);
		}
	}
	long best = 0;
	size_t bestParts = 0;
	for (std::map<size_t, std::set<size_t> >::const_iterator it = got.begin(); it != got.end(); ++it)
	{
		const TMt2009PlusSetDef& d = t.sets[it->first];
		const size_t parts = it->second.size();
		if (parts > bestParts && Mt2009PlusSetGrade(d, (int)parts))
		{
			bestParts = parts;
			best = d.id * 10 + (long)parts;
		}
	}
	return best;
}

static const TMt2009PlusSetDef* Mt2009PlusSetById(int id)
{
	const TMt2009PlusSetTable& t = Mt2009PlusSetTable();
	for (size_t i = 0; i < t.sets.size(); ++i)
		if (t.sets[i].id == id)
			return &t.sets[i];
	return NULL;
}

static CAffect* Mt2009PlusSetInfoAffect(LPCHARACTER ch)
{
	const std::list<CAffect*>& l = ch->GetAffectContainer();
	for (std::list<CAffect*>::const_iterator it = l.begin(); it != l.end(); ++it)
		if ((*it)->dwType == MT2009_PLUS_AFFECT_COSTUME_SET && (*it)->bApplyOn == POINT_NONE)
			return *it;
	return NULL;
}

static void Mt2009PlusCostumeSetDecide(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;
	static bool s_bDeciding = false;	// RemoveAffect runs ComputePoints, whose end asks again
	if (s_bDeciding)
		return;
	struct TDeciding
	{
		TDeciding() { s_bDeciding = true; }
		~TDeciding() { s_bDeciding = false; }
	} deciding;
	const long want = Mt2009PlusSetWanted(ch);
	CAffect* info = Mt2009PlusSetInfoAffect(ch);
	const long have = info ? info->lApplyValue : 0;
	if (want == have && (want || !ch->FindAffect(MT2009_PLUS_AFFECT_COSTUME_SET)))
		return;
	if (ch->FindAffect(MT2009_PLUS_AFFECT_COSTUME_SET))
		ch->RemoveAffect(MT2009_PLUS_AFFECT_COSTUME_SET);
	const bool tell = ch->GetSectree() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	const TMt2009PlusSetDef* d = want ? Mt2009PlusSetById((int)(want / 10)) : NULL;
	const std::vector<TMt2009PlusSetBonus>* grade = d ? Mt2009PlusSetGrade(*d, (int)(want % 10)) : NULL;
	if (grade)
	{
		// the set's aura as in V1: the unused affect flag AFF_FIRE_RAGE (bit 44 in the client, game.py)
		ch->AddAffect(MT2009_PLUS_AFFECT_COSTUME_SET, POINT_NONE, want, AFF_FIRE_RAGE, INFINITE_AFFECT_DURATION, 0, false);
		for (size_t i = 0; i < grade->size(); ++i)
			if (!(*grade)[i].bDrop)
				ch->AddAffect(MT2009_PLUS_AFFECT_COSTUME_SET, (*grade)[i].bPoint, (*grade)[i].lValue, AFF_NONE,
						INFINITE_AFFECT_DURATION, 0, false);
		if (tell)
			ch->ChatPacket(CHAT_TYPE_INFO, "Bonus zestawu kostiumow (%s): %ld czesci.", d->name.c_str(), want % 10);
	}
	else if (tell && have)
		ch->ChatPacket(CHAT_TYPE_INFO, "Zestaw kostiumow niepelny - bonus zestawu zniknal.");
	// RemoveAffect recomputed the points, and ComputePoints put every worn item's look back on (V1, 28 September)
	void Mt2009PlusApplyCostumeParts(LPCHARACTER ch, LPITEM leaving);
	Mt2009PlusApplyCostumeParts(ch, NULL);
}

// CItem::ModifyPoints (put on) and CItem::Unequip (taken off): an item of a set, outside ComputePoints
void Mt2009PlusCheckCostumeSet(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || g_iMt2009PlusComputeDepth > 0)
		return;
	const TMt2009PlusSetTable& t = Mt2009PlusSetTable();
	if (t.byVnum.find(item->GetVnum()) == t.byVnum.end() && !ch->FindAffect(MT2009_PLUS_AFFECT_COSTUME_SET))
		return;
	Mt2009PlusCostumeSetDecide(ch);
}

// the end of the outermost CHARACTER::ComputePoints (a pet called or sent away, the login, every recompute)
void Mt2009PlusCostumeSetComputed(LPCHARACTER ch)
{
	if (g_iMt2009PlusComputeDepth == 1 && ch && ch->IsPC())
		Mt2009PlusCostumeSetDecide(ch);
}

// ITEM_MANAGER::GetDropPct: the worn set's "Szansa na dropy przedmiotow" (percent added to the drop bonus)
int Mt2009PlusCostumeSetDropBonus(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return 0;
	CAffect* info = Mt2009PlusSetInfoAffect(ch);
	if (!info)
		return 0;
	const TMt2009PlusSetDef* d = Mt2009PlusSetById((int)(info->lApplyValue / 10));
	const std::vector<TMt2009PlusSetBonus>* grade = d ? Mt2009PlusSetGrade(*d, (int)(info->lApplyValue % 10)) : NULL;
	int bonus = 0;
	for (size_t i = 0; grade && i < grade->size(); ++i)
		if ((*grade)[i].bDrop)
			bonus += (*grade)[i].lValue;
	return bonus;
}

'''

V1_CHECK = ('void Mt2009PlusCheckCostumeSet(LPCHARACTER ch, LPITEM leaving)\n{\n\tif (!ch || !ch->IsPC())\n\t\treturn;\n'
            '\t// Adding or removing the bonus recomputes')

EDITS = [
    # the new table and judge before V1's, which keeps its body under another name (unused; its V1 marker stays)
    dict(file='item.cpp', marker=M + ' (sets)', old=V1_CHECK,
         new=SETS_CODE + '// ' + M + ' (sets): V1\'s judge, no longer called (Mt2009PlusCostumeSetDecide above)\n'
             + V1_CHECK.replace('Mt2009PlusCheckCostumeSet(', 'Mt2009PlusCheckCostumeSetV1(')),
    dict(file='item.cpp', marker=M + ' (hook)',
         old='\t\tif (m_pOwner && m_pProto->bType == ITEM_COSTUME &&\n'
             '\t\t\t\t(GetSubType() == COSTUME_BODY || GetSubType() == COSTUME_HAIR))\n'
             '\t\t\tMt2009PlusCheckCostumeSet(m_pOwner, bAdd ? NULL : this);\n',
         new='\t\t// ' + M + ' (hook): any item of a set put on - a costume, hair, weapon skin, mount, sash, ring or\n'
             '\t\t// amulet; one taken off is judged in CItem::Unequip once it has left its slot ((unequip))\n'
             '\t\tif (m_pOwner && bAdd)\n'
             '\t\t\tMt2009PlusCheckCostumeSet(m_pOwner, this);\n'),
    dict(file='item.cpp', marker=M + ' (unequip)',
         old='\tm_pOwner->SetWear(GetCell() - INVENTORY_MAX_NUM, NULL);\n',
         new='\tm_pOwner->SetWear(GetCell() - INVENTORY_MAX_NUM, NULL);\n'
             '\t{ void Mt2009PlusCheckCostumeSet(LPCHARACTER ch, LPITEM item); Mt2009PlusCheckCostumeSet(m_pOwner, this); } // '
             + M + ' (unequip): the costume set without it\n'),
    dict(file='char.cpp', marker=M + ' (depth)',
         old='void CHARACTER::ComputePoints()\n{\n',
         new='extern int g_iMt2009PlusComputeDepth; // ' + M + ' (depth): item.cpp - the costume set is judged at the end\n'
             'void CHARACTER::ComputePoints()\n{\n'
             '\tstruct TMt2009PlusComputeDepth\n\t{\n'
             '\t\tTMt2009PlusComputeDepth() { ++g_iMt2009PlusComputeDepth; }\n'
             '\t\t~TMt2009PlusComputeDepth() { --g_iMt2009PlusComputeDepth; }\n'
             '\t} mt2009ComputeDepth;\n'),
    dict(file='char.cpp', marker=M + ' (computed)',
         old='#endif\n\tUpdatePacket();\n}\n\nvoid CHARACTER::ResetPlayTime',
         new='#endif\n'
             '\t// ' + M + ' (computed): the costume set of what is worn and called now (a pet called or sent away, the\n'
             '\t// login); only at the end of the outermost recompute, so an affect put on is not counted twice\n'
             '\t{ void Mt2009PlusCostumeSetComputed(LPCHARACTER ch); Mt2009PlusCostumeSetComputed(this); }\n'
             '\tUpdatePacket();\n}\n\nvoid CHARACTER::ResetPlayTime'),
    dict(file='item_manager.cpp', marker=M + ' (drop)',
         old='\t//iDeltaPercent = iDeltaPercent * (100 + MIN(item_drop_bonus, 225)) / 100;\n',
         new='\t// ' + M + ' (drop): the worn costume set\'s "Szansa na dropy przedmiotow" (item.cpp)\n'
             '\t{\n\t\tint Mt2009PlusCostumeSetDropBonus(LPCHARACTER ch);\n'
             '\t\tconst int set_drop = Mt2009PlusCostumeSetDropBonus(pkKiller);\n'
             '\t\tif (set_drop > 0)\n\t\t\tAddToBonusItemDrop(item_drop_bonus, set_drop);\n\t}\n'
             '\t//iDeltaPercent = iDeltaPercent * (100 + MIN(item_drop_bonus, 225)) / 100;\n'),
]


def check(src):
    ok = True
    texts = {}
    for e in EDITS:
        if e['file'] not in texts:
            texts[e['file']] = open(os.path.join(src, e['file']), 'rb').read().decode('latin-1').replace('\r\n', '\n')
        t = texts[e['file']]
        if e['marker'] in t:
            print('already: %s %s' % (e['file'], e['marker']))
            continue
        n = t.count(e['old'])
        if n != 1:
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
