#ifndef __INC_METIN2_PLAYERBOT_YOHARA_BONUS_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_BONUS_H__

// MT2009_PLUS_BOT_YOHARA_BONUS_V1 - a Yohara bot bonuses its own gear with the stones it holds (the owner, 27 October
// 2026, the 800 bots: "Nie bonuj EQ, daj im po 400 wzmocnien przedmiotow i po 800 zaczarowan przedmiotow, tak aby
// samodzielnie wybonowaly sobie potrzebny im EQ na Yohare"). The choice is playerbot_yohara_bonus_rules.h (pure); this
// is the engine's half.
//
// Who: a member of the Yohara cohorts (common.playerbot_yohara_cohort) or any bot with a Champion level, holding an
// ordinary Wzmocnienie Przedmiotu (USE_ADD_ATTRIBUTE: 71085 and its ItemShop copy) or Zaczarowanie Przedmiotu
// (USE_CHANGE_ATTRIBUTE: 71084 and its copy) - never the green ones (gear of forty and under) nor the tradeable
// 71284/71285 (millions on a counter). Such a bot is this pass's, not the ordinary one's (ManagePlayerBotBonusReroll):
// the ordinary pass's refine and level categories (+6, the level-30 family...) are the old world's and would leave a
// fresh +0 Yohara set untouched for good. Not a companion (its bag is its owner's).
//
// How: as a player does it - the piece comes off (the engine's USE_ADD/CHANGE_ATTRIBUTE refuses an equipped item),
// the stone's own item path rolls it (CItem::AddAttribute at aiItemAttributeAddPercent's odds for the line count,
// CItem::ChangeAttribute - the addon of a weapon that has one included), the stone is spent whether the add lands or
// not, the piece goes back on. Nothing writes an attribute directly. One piece and at most
// PLAYERBOT_YOHARA_BONUS_STONES_PER_PASS stones a pass, a pass every PLAYERBOT_YOHARA_BONUS_PASS_MS while there is
// work (else the ordinary PLAYERBOT_BONUS_INTERVAL), out of a fight only (the field pass's own gates and the equip
// window): 18 stones a minute out of a fight, so the ~400 stones a set takes (below) are spent within an hour or two
// of a hunting bot's play.
//
// The targets ("good enough for Yohara"). What the Sung Ma maps are made of - the ordinary monsters of
// tools/yohara_lokacje/lokalizacje.tsv (no bosses, no Metins) by mob_proto's race flags, 27 October:
//   373 Dongan        DEVIL 73%, ANIMAL 26%          385 Przelecz Yilad   DEVIL 100%
//   374 Twierdza      HUMAN 100%                     388 Wawoz            no race 52%, SAVAGE 48%
//   376 Seoganland    DESERT 100%                    389 Rozpadlina       no race 51%, SAVAGE 48%
//   377 Namgan        DESERT 50%, DEVIL 37%, ANIMAL  393 Schronienie      no race 100%
//                                                    394 Zejscie          SAVAGE 100%
// So "Silny przeciwko Demonom" (POINT_ATTBONUS_DEVIL) is the one race line that pays on Yohara (three maps of the
// band and most of Namgan), "Silny przeciwko Ludziom" (HUMAN) the Twierdza's (and the PvP line); DESERT rolls on a
// talisman only, and SAVAGE and the north maps' unflagged monsters on nothing - there the general lines carry it.
// Both race lines count, so a bot moving up the maps never rerolls a finished piece for its new map. The elements
// (playerbot_yohara_elements.h): fire on Dongan/Namgan, lightning on Wawoz/Rozpadlina/Zejscie, wind on Namgan - and
// since MT2009_PLUS_ELEMENT_RESIST_FULL_V1 a percent of resistance is a percent less damage, so the fire, lightning
// and wind resistances (global mode: body, bracelet, helmet to 15; the ice/earth/dark ones roll on a talisman only)
// are wanted lines. The bots' Precyzja is always full, so the glove's POINT_HIT_PCT is not.
//
// Per slot, from world.item_attr (which lines roll where; the live table, so both modes - M2_BONUS_MODE global and
// mt2009 - are read as they are: a line the mode does not roll on a slot is simply not asked there):
//   slot     must                       wanted                                                  strong      fair
//   weapon   DEVIL or HUMAN             critical, piercing, the class stat (STR; DEX ninja;      3: m4 o3    2: m4 o3
//                                       INT shaman/sura) [+ casting speed for a caster; the
//                                       addon's average (skill for a caster) on an addon weapon]
//   body     max HP                     attack value (casting speed for a caster), HP steal,     3: m4 o3    2: m4 o3
//                                       fire/lightning/wind resistance
//   helmet   DEVIL or HUMAN             attack speed, fire/lightning/wind resistance             3: m3 o3    2: m4 o3
//   necklace max HP                     critical, piercing                                       2: m4 o4    2: m3 o3
//   bracelet max HP                     DEVIL/HUMAN, piercing, HP steal, fire/lightning/wind     3: m4 o3    2: m4 o3
//   boots    max HP                     attack speed, critical                                   2: m4 o4    2: m3 o3
//   earrings DEVIL or HUMAN             movement speed, item drop                                2: m4 o4    2: m3 o3
//   shield   DEVIL or HUMAN             the class stat, vitality, block, stun immunity,          3: m4 o3    2: m4 o3
//                                       melee reflection
//   glove    -                          the class stat, vitality, HP steal                       3: o3       2: o3
// MT2009_PLUS_BOT_ELEMENT_RESIST_V1 (28 October 2026) changed the table for the owner's Yohara defence: E = the
// resistance to the bot's hunt element (playerbot_element_resist.h; fire, lightning or wind - the three that roll on
// gear), none when its element is one the gear cannot hold (ice, earth, dark: no must of it then).
//   body     max HP + E (two musts)     attack value / casting speed, HP steal, arrow, magic res  E: 2: m4 o3  2: m3 o3
//   helmet   E (else DEVIL or HUMAN)    race (with E), attack speed, arrow dodge, magic res       E: 2: m4 o3  2: m3 o3
//   bracelet max HP + E (two musts)     DEVIL/HUMAN, piercing, HP steal, magic resistance         E: 2: m4 o3  2: m3 o3
//   boots    max HP                     arrow dodge, arrow resistance, attack speed, critical      as above
//   necklace / earrings: + arrow resistance; shield: must = melee block (race, stat, vitality, stun, reflect wanted).
// Simulated (global table, 4-5 lines): body E strong 37-60 changes, fair 11-19; bracelet 57-101 / 18-31; helmet
// 15-24 / 8-13. Other elements' resistances are no line of any list.
// "3: m4 o3" = three lines of the list, the must line at level 4 or 5 of the table (race 10/20, HP 1500/2000 in the
// global mode) and the others at level 3 or more. Measured by simulation against the global table and the engine's
// change odds (lv2-5: 10/40/35/15): the strong tier takes 20-70 changes on average a piece, the fair one 4-20.
// Budgets (the slots' weights below; pool = the change stones held + spent on the pieces worn - the reserve): with
// 800 a weapon gets ~125, the armour ~110, the helmet and the jewellery ~85, the earrings and the shield ~70, the
// glove ~45 - and what the finished pieces did not use goes to those short of their target (the leftover). A run of
// the rules over nine pieces (200 simulated bots, 400 adds / 800 changes): ~45 adds and ~350 changes spent, every
// piece but the glove strong (the glove strong one time in two, fair otherwise), ~450 changes left for the next
// pieces - about 400 stones, i.e. 20-25 minutes of passes out of a fight.
//
// The log: PLAYERBOT_YOHARA_BONUS - "pass" (the piece, the stones of the pass by kind, its lines and tier before and
// after, its spend and share, the bag's stock, and every listed slot as name:lines tier spent/share - tier A strong,
// B fair, - neither), "unequip failed", and "done" (throttled) when nothing is left to do. The gear history:
// PLAYERBOT_YOHARA_BONUS_ADD / _MARBLE / _CHANGE item logs.
//
// MT2009_PLUS_BOT_ELEMENT_RESIST_V2 (the owner, 28 October 2026, the census 20 minutes after V1: lightning 34%, wind
// 33%, fire 22%, ice 18%, earth 8% on average - "musza znacznie lepiej bonowac EQ pod odpornosci"):
//   * the talisman (WEAR_PENDANT, the item_attr's pendant column) is a slot of the pass: the engine's 71085 / 71084 take
//     it as any armour (its attribute set is ATTRIBUTE_SET_PENDANT; a change keeps a Talizman Woli's 6th/7th lines -
//     ClearAttribute clears the five ordinary ones only). It rolls all six element resistances to 25 (ice, earth and
//     dark by the table; fire, lightning and wind 5 a level in the global mode, BonusModeAttrValue) - the only gear
//     line an ice, earth or dark bot has. Its must is the hunt element's resistance (any of the six), wanted the
//     Desert and Human races (Seoganland / Namgan, the Twierdza); nothing else on it pays on Yohara (no Max HP, no
//     element power roll there);
//   * the element phase (playerbot_yohara_bonus_rules.h 2a): talisman, armour, bracelet, helmet - each changed until
//     the hunt element's line stands at its TOP level (25 talisman, 15 the rest - the top of the piece's set, read
//     through BonusModeAttrValue) with the armour's / bracelet's Max HP at level 4 (1500), or level 3 (1000) once half
//     of the piece's element budget is gone; budgets GetPlayerBotYoharaElementCap (changes on the piece in all).
//     Simulated against the global table and the change odds (2000 pieces each): talisman 80 -> 97% reach it, ~22
//     changes; armour 300 -> 88%, ~146; bracelet 300 -> 73%, ~181; helmet 100 -> 92%, ~37: ~390 changes a bot on
//     average, the 400 extra stones the owner gave on 28 October. A piece whose target is met is strong - never
//     changed again; one whose budget ran out goes on by the shares and the leftover as before.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_bonus.h, in the anonymous namespace.

// playerbot_bonus_mode.cpp (MT2009_PLUS_GLOBAL_BONUS_V1): the value a line of that level gets on that item.
long BonusModeAttrValue(CItem* item, BYTE apply, BYTE level, long value);

namespace
{
	const int PLAYERBOT_YOHARA_BONUS_STONES_PER_PASS = 6;
	const DWORD PLAYERBOT_YOHARA_BONUS_PASS_MS = 20000;
	// change stones kept back for the pieces the bot will wear next (a new weapon, the next armour)
	const int PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE = 40;
	// a fair piece is rerolled towards strong out of the leftover only over the reserve and this margin
	const int PLAYERBOT_YOHARA_BONUS_SAFETY = 25;
	const int PLAYERBOT_YOHARA_BONUS_ADD_LINES = 4;	// the add stone's ceiling (USE_ADD_ATTRIBUTE)
	const DWORD PLAYERBOT_YOHARA_BONUS_DONE_LOG_MS = 30 * 60 * 1000;
	// the average / skill line of an addon weapon (item_addon.cpp, not item_attr): the levels' thresholds
	const int PLAYERBOT_YOHARA_BONUS_AVG_LEVELS[4] = { 5, 10, 20, 30 };
	const int PLAYERBOT_YOHARA_BONUS_SKILL_LEVELS[4] = { 2, 5, 10, 15 };

	struct TPlayerBotYoharaBonusSlot
	{
		BYTE bWearCell;
		const char* szName;
		int iWeight;
		playerbot_yohara_bonus_rules::TTier strong;
		playerbot_yohara_bonus_rules::TTier fair;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: the tiers while the hunt element's resistance is in the piece's target
		playerbot_yohara_bonus_rules::TTier strongE;
		playerbot_yohara_bonus_rules::TTier fairE;
	};

	// The priority order (weapon, talisman, armour, helmet, the jewellery, the earrings, the shield, the glove) and the
	// shares.
	const TPlayerBotYoharaBonusSlot PLAYERBOT_YOHARA_BONUS_SLOTS[] = {
		{ WEAR_WEAPON, "weapon", 16, { 3, 4, 3 }, { 2, 4, 3 }, { 3, 4, 3 }, { 2, 4, 3 } },
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the talisman - the hunt element's resistance (its must), else a wanted race line
		{ WEAR_PENDANT, "talisman", 10, { 1, 5, 3 }, { 1, 4, 3 }, { 1, 5, 3 }, { 1, 4, 3 } },
		{ WEAR_BODY,   "body",   14, { 3, 4, 3 }, { 2, 4, 3 }, { 2, 4, 3 }, { 2, 3, 3 } },
		{ WEAR_HEAD,   "head",   11, { 3, 3, 3 }, { 2, 4, 3 }, { 2, 4, 3 }, { 2, 3, 3 } },
		{ WEAR_NECK,   "neck",   11, { 2, 4, 4 }, { 2, 3, 3 }, { 2, 4, 4 }, { 2, 3, 3 } },
		{ WEAR_WRIST,  "wrist",  11, { 3, 4, 3 }, { 2, 4, 3 }, { 2, 4, 3 }, { 2, 3, 3 } },
		{ WEAR_FOOTS,  "foots",  11, { 2, 4, 4 }, { 2, 3, 3 }, { 2, 4, 4 }, { 2, 3, 3 } },
		{ WEAR_EAR,    "ear",     9, { 2, 4, 4 }, { 2, 3, 3 }, { 2, 4, 4 }, { 2, 3, 3 } },
		{ WEAR_SHIELD, "shield",  9, { 3, 4, 3 }, { 2, 4, 3 }, { 3, 4, 3 }, { 2, 4, 3 } },
		{ WEAR_GLOVE,  "glove",   6, { 3, 0, 3 }, { 2, 0, 3 }, { 3, 0, 3 }, { 2, 0, 3 } },
	};
	const int PLAYERBOT_YOHARA_BONUS_SLOT_COUNT =
			(int)(sizeof(PLAYERBOT_YOHARA_BONUS_SLOTS) / sizeof(PLAYERBOT_YOHARA_BONUS_SLOTS[0]));

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase's rank and budget (changes on the piece in all) - talisman,
	// armour, bracelet, helmet (the owner's order; the costume and the hairstyle are the costume pass's, 70064).
	int GetPlayerBotYoharaElementRank(BYTE wearCell)
	{
		switch (wearCell)
		{
			case WEAR_PENDANT: return 0;
			case WEAR_BODY: return 1;
			case WEAR_WRIST: return 2;
			case WEAR_HEAD: return 3;
			default: return -1;
		}
	}

	int GetPlayerBotYoharaElementCap(BYTE wearCell)
	{
		switch (wearCell)
		{
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the talisman's 25 is the only gear line of an ice, earth or dark bot - 160
			// changes for it (the census of 28 October: tal_top 43/65 dark, 36/54 ice; 42 talisman passes past 80 went on
			// by the shares with the line short)
			case WEAR_PENDANT: return 160;
#else
			case WEAR_PENDANT: return 80;
#endif
			case WEAR_BODY: return 300;
			case WEAR_WRIST: return 300;
			case WEAR_HEAD: return 100;
			default: return 0;
		}
	}

	// The hunt element's resistance point a piece in that slot works for: the talisman any of the six (all roll on it),
	// the armour, bracelet and helmet fire, lightning or wind (GetPlayerBotHuntResistPoint); 0 for none.
	BYTE GetPlayerBotYoharaSlotHuntPoint(LPCHARACTER ch, BYTE wearCell)
	{
		if (wearCell == WEAR_PENDANT)
			return GetPlayerBotElementResistPoint(GetPlayerBotHuntElementIndex(ch));
		if (wearCell == WEAR_BODY || wearCell == WEAR_WRIST || wearCell == WEAR_HEAD)
			return GetPlayerBotHuntResistPoint(ch);
		return 0;
	}

	// changes spent per piece (item id), per bot - this core's memory; a restart starts the shares from the stock
	std::map<DWORD, std::map<DWORD, int> > s_mapPlayerBotYoharaBonusSpent;

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the changes a piece had when the bot's hunt element became the one it has now -
	// the element budget counts from there (a talisman that spent its 80 on lightning got nothing for the ice after the
	// move up; the element now changes only up the maps, so this is a new element's fresh budget once per move).
	struct TPlayerBotYoharaElementBase
	{
		int iElement;
		int iBase;
	};
	std::map<DWORD, std::map<DWORD, TPlayerBotYoharaElementBase> > s_mapPlayerBotYoharaElementBase;

	int GetPlayerBotYoharaElementSpentBase(LPCHARACTER ch, LPITEM item, int spent)
	{
		if (!ch || !item)
			return 0;
		const int e = GetPlayerBotHuntElementIndex(ch);
		std::map<DWORD, TPlayerBotYoharaElementBase>& bases = s_mapPlayerBotYoharaElementBase[ch->GetPlayerID()];
		std::map<DWORD, TPlayerBotYoharaElementBase>::iterator it = bases.find(item->GetID());
		if (it == bases.end())
		{
			if (bases.size() > 64)
				bases.clear();
			const TPlayerBotYoharaElementBase fresh = { e, 0 };
			bases[item->GetID()] = fresh;
			return 0;
		}
		if (it->second.iElement != e)
		{
			it->second.iElement = e;
			it->second.iBase = spent;
		}
		return std::max(0, std::min(it->second.iBase, spent));
	}
#endif

	bool IsPlayerBotYoharaBonusMember(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotSidekickPID(pid))
			return false;
		return IsPlayerBotYoharaCohortPID(pid) || (int)ch->GetConquerorLevel() >= 1;
	}

	// The class stat a weapon, a shield and a glove are wanted for.
	BYTE GetPlayerBotYoharaBonusClassStat(LPCHARACTER ch)
	{
		if (IsPlayerBotCaster(ch))
			return POINT_IQ;
		return ch->GetJob() == JOB_ASSASSIN ? POINT_DX : POINT_ST;
	}

	// MT2009_PLUS_STEAL_CAP_V1: the HP absorption the worn gear (bonuses and the item's own) gives, the piece in
	// skipCell left out. The engine takes at most 50% (enginefixes, GetPoint): a line past that is wasted.
	int GetPlayerBotGearStealHp(LPCHARACTER ch, int skipCell)
	{
		int total = 0;
		for (int cell = 0; cell < WEAR_MAX_NUM; ++cell)
		{
			LPITEM item = cell == skipCell ? NULL : ch->GetWear(cell);
			if (!item || !item->GetProto())
				continue;
			for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
				if (item->GetProto()->aApplies[i].bType == APPLY_STEAL_HP)
					total += item->GetProto()->aApplies[i].lValue;
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
				if (item->GetAttributeType(i) == APPLY_STEAL_HP)
					total += item->GetAttributeValue(i);
		}
		return total;
	}

	// A line's role in a slot's target (the table at the head of the file).
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V1 (the owner, 28 October 2026: "na Yoharze najwazniejsze sa odpornosci i PZ"; the
	// element rules in playerbot_element_resist.h): the resistance to the bot's hunt element (GetPlayerBotHuntResistPoint
	// - only fire, lightning and wind roll on the armour, the helmet and the bracelet here) is a must of its own
	// (ROLE_MUST2) next to Max HP on the armour and the bracelet, and the helmet's must (the race line then only
	// wanted); every other element's resistance is wanted nowhere. The defensive lines the owner's guide asks for on
	// Yohara are wanted where they roll: arrow dodge (helmet, boots), arrow and magic resistance (armour, bracelet,
	// helmet, boots, necklace, earrings); the shield's must is the melee block.
	int GetPlayerBotYoharaBonusRole(LPCHARACTER ch, BYTE wearCell, BYTE type, bool addonWeapon)
	{
		using namespace playerbot_yohara_bonus_rules;
		const bool caster = IsPlayerBotCaster(ch);
		const BYTE stat = GetPlayerBotYoharaBonusClassStat(ch);
		const bool race = type == POINT_ATTBONUS_DEVIL || type == POINT_ATTBONUS_HUMAN;
		const BYTE hunt = GetPlayerBotHuntResistPoint(ch);
		const bool huntResist = hunt != 0 && type == hunt;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the talisman's must - the hunt element's resistance, whichever of the six
		if (wearCell == WEAR_PENDANT)
		{
			const BYTE tal = GetPlayerBotYoharaSlotHuntPoint(ch, WEAR_PENDANT);
			if (tal != 0 && type == tal)
				return ROLE_MUST;
			return type == POINT_ATTBONUS_DESERT || type == POINT_ATTBONUS_HUMAN ? ROLE_WANTED : ROLE_OTHER;
		}
		const bool arrow = type == POINT_RESIST_BOW;
		const bool magicResist = type == POINT_RESIST_MAGIC;
		// MT2009_PLUS_STEAL_CAP_V1: the rest of the gear already gives the 50% cap - absorption here is wasted.
		if (type == POINT_STEAL_HP && GetPlayerBotGearStealHp(ch, wearCell) >= 50)
			return ROLE_OTHER;
		switch (wearCell)
		{
			case WEAR_WEAPON:
				if (race)
					return ROLE_MUST;
				if (type == POINT_CRITICAL_PCT || type == POINT_PENETRATE_PCT || type == stat ||
						(caster && type == POINT_CASTING_SPEED) ||
						(addonWeapon && type == (caster ? POINT_SKILL_DAMAGE_BONUS : POINT_NORMAL_HIT_DAMAGE_BONUS)))
					return ROLE_WANTED;
				return ROLE_OTHER;
			case WEAR_BODY:
				if (type == POINT_MAX_HP)
					return ROLE_MUST;
				if (huntResist)
					return ROLE_MUST2;
				if (type == (caster ? POINT_CASTING_SPEED : POINT_ATT_GRADE_BONUS) || type == POINT_STEAL_HP || arrow ||
						magicResist)
					return ROLE_WANTED;
				return ROLE_OTHER;
			case WEAR_HEAD:
				if (huntResist)
					return ROLE_MUST;
				if (race)
					return hunt != 0 && IsPlayerBotApplyOnAttrSet(hunt, ATTRIBUTE_SET_HEAD) ? ROLE_WANTED : ROLE_MUST;
				return type == POINT_ATT_SPEED || type == POINT_DODGE || magicResist ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_NECK:
				if (type == POINT_MAX_HP)
					return ROLE_MUST;
				return type == POINT_CRITICAL_PCT || type == POINT_PENETRATE_PCT || arrow ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_WRIST:
				if (type == POINT_MAX_HP)
					return ROLE_MUST;
				if (huntResist)
					return ROLE_MUST2;
				return race || type == POINT_PENETRATE_PCT || type == POINT_STEAL_HP || magicResist
						? ROLE_WANTED : ROLE_OTHER;
			case WEAR_FOOTS:
				if (type == POINT_MAX_HP)
					return ROLE_MUST;
				return type == POINT_DODGE || arrow || type == POINT_ATT_SPEED || type == POINT_CRITICAL_PCT
						? ROLE_WANTED : ROLE_OTHER;
			case WEAR_EAR:
				if (race)
					return ROLE_MUST;
				return type == POINT_MOV_SPEED || type == POINT_ITEM_DROP_BONUS || arrow ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_SHIELD:
				if (type == POINT_BLOCK)
					return ROLE_MUST;
				return race || type == stat || type == POINT_HT || type == POINT_IMMUNE_STUN ||
						type == POINT_REFLECT_MELEE ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_GLOVE:
				return type == stat || type == POINT_HT || type == POINT_STEAL_HP ? ROLE_WANTED : ROLE_OTHER;
			default:
				return ROLE_OTHER;
		}
	}

	// The highest level a line may roll at on this piece's attribute set; 0 when it never rolls there.
	int GetPlayerBotYoharaBonusSlotMaxLevel(LPITEM item, BYTE type)
	{
		const int set = item ? item->GetAttributeSetIndex() : -1;
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM)
			return 0;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(type);
		if (it == g_map_itemAttr.end() || it->second.dwProb == 0)
			return 0;
		return std::min<int>(ITEM_ATTRIBUTE_MAX_LEVEL, it->second.bMaxLevelBySet[set]);
	}

	// A line's level (1-5) by the table's values; the slot's own top level counts as 5.
	int GetPlayerBotYoharaBonusLineLevel(LPITEM item, BYTE type, long value)
	{
		if (value <= 0)
			return 0;
		const int* steps = type == POINT_NORMAL_HIT_DAMAGE_BONUS ? PLAYERBOT_YOHARA_BONUS_AVG_LEVELS
				: (type == POINT_SKILL_DAMAGE_BONUS ? PLAYERBOT_YOHARA_BONUS_SKILL_LEVELS : NULL);
		if (steps)
		{
			int level = 1;
			for (int i = 0; i < 4; ++i)
				if (value >= steps[i])
					level = i + 2;
			return level;
		}
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(type);
		if (it == g_map_itemAttr.end())
			return 1;
		int level = 1;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the value the engine gives the level on this item (a talisman's fire,
		// lightning and wind are 5 a level in the global mode, not the table's 2-15)
		for (int l = ITEM_ATTRIBUTE_MAX_LEVEL; l >= 1; --l)
		{
			const long step = BonusModeAttrValue(item, type, (BYTE)l, it->second.lValues[l - 1]);
			if (step > 0 && value >= step)
			{
				level = l;
				break;
			}
		}
		const int slotMax = GetPlayerBotYoharaBonusSlotMaxLevel(item, type);
		return slotMax > 0 && level >= slotMax ? ITEM_ATTRIBUTE_MAX_LEVEL : level;
	}

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the top value of a line on this piece (its set's top level, the engine's value
	// for it); 0 when it never rolls there.
	long GetPlayerBotYoharaTopLineValue(LPITEM item, BYTE type)
	{
		const int top = GetPlayerBotYoharaBonusSlotMaxLevel(item, type);
		if (top <= 0)
			return 0;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(type);
		return it == g_map_itemAttr.end() ? 0 : BonusModeAttrValue(item, type, (BYTE)top, it->second.lValues[top - 1]);
	}

	// The piece's line of a type (0 none) - the five ordinary lines.
	long GetPlayerBotYoharaPieceLine(LPITEM item, BYTE type)
	{
		for (int i = 0; item && type && i < PLAYERBOT_BONUS_MARBLE_LINES && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == type)
				return item->GetAttributeValue(i);
		return 0;
	}

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase's target of a piece: 1 met (the hunt element's line at the
	// top value; the armour's / bracelet's Max HP at level 4, at level 3 once half of the budget is spent), 0 short,
	// -1 none (no hunt element, or its resistance does not roll on the piece).
	int GetPlayerBotYoharaElementTarget(LPCHARACTER ch, LPITEM item, BYTE wearCell, int spent)
	{
		if (!ch || !item || GetPlayerBotYoharaElementRank(wearCell) < 0)
			return -1;
		const BYTE point = GetPlayerBotYoharaSlotHuntPoint(ch, wearCell);
		const long top = point ? GetPlayerBotYoharaTopLineValue(item, point) : 0;
		if (top <= 0)
			return -1;
		if (GetPlayerBotYoharaPieceLine(item, point) < top)
			return 0;
		if ((wearCell == WEAR_BODY || wearCell == WEAR_WRIST) && GetPlayerBotYoharaBonusSlotMaxLevel(item, POINT_MAX_HP) > 0)
		{
			const int need = spent * 2 < GetPlayerBotYoharaElementCap(wearCell) ? 4 : 3;
			const long hp = GetPlayerBotYoharaPieceLine(item, POINT_MAX_HP);
			if (hp <= 0 || GetPlayerBotYoharaBonusLineLevel(item, POINT_MAX_HP, hp) < need)
				return 0;
		}
		return 1;
	}

	// How many kinds of the slot's list can roll on the piece at all, and which must kinds can (MUST_ROLLS_1/_2).
	int CountPlayerBotYoharaBonusAvailable(LPCHARACTER ch, LPITEM item, BYTE wearCell, bool addonWeapon, int& mustRolls)
	{
		mustRolls = 0;
		int available = 0;
		for (TItemAttrMap::const_iterator it = g_map_itemAttr.begin(); it != g_map_itemAttr.end(); ++it)
		{
			const int role = GetPlayerBotYoharaBonusRole(ch, wearCell, (BYTE)it->first, addonWeapon);
			if (role == playerbot_yohara_bonus_rules::ROLE_OTHER || GetPlayerBotYoharaBonusSlotMaxLevel(item, (BYTE)it->first) <= 0)
				continue;
			++available;
			if (role == playerbot_yohara_bonus_rules::ROLE_MUST)
				mustRolls |= playerbot_yohara_bonus_rules::MUST_ROLLS_1;
			else if (role == playerbot_yohara_bonus_rules::ROLE_MUST2)
				mustRolls |= playerbot_yohara_bonus_rules::MUST_ROLLS_2;
		}
		if (addonWeapon)
			++available;	// the addon's average (skill) line: not in item_attr
		return available;
	}

	int GetPlayerBotYoharaBonusTier(LPCHARACTER ch, LPITEM item, int slotIndex)
	{
		if (!ch || !item || slotIndex < 0 || slotIndex >= PLAYERBOT_YOHARA_BONUS_SLOT_COUNT)
			return playerbot_yohara_bonus_rules::TIER_NONE;
		const TPlayerBotYoharaBonusSlot& slot = PLAYERBOT_YOHARA_BONUS_SLOTS[slotIndex];
		const bool addonWeapon = slot.bWearCell == WEAR_WEAPON && HasPlayerBotDamageAddon(item);
		playerbot_yohara_bonus_rules::TLine lines[ITEM_ATTRIBUTE_MAX_NUM];
		int count = 0;
		for (int i = 0; i < PLAYERBOT_BONUS_MARBLE_LINES && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			const long value = item->GetAttributeValue(i);
			if (type == 0 || value <= 0)
				continue;
			lines[count].role = GetPlayerBotYoharaBonusRole(ch, slot.bWearCell, type, addonWeapon);
			lines[count].level = GetPlayerBotYoharaBonusLineLevel(item, type, value);
			++count;
		}
		int mustRolls = 0;
		const int available = CountPlayerBotYoharaBonusAvailable(ch, item, slot.bWearCell, addonWeapon, mustRolls);
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: a piece whose target holds the hunt element's resistance takes the
		// slot's element tiers (two musts at level 4 are some 40-100 changes, at level 3 some 10-30 - simulated
		// against the global table: armour, bracelet; the helmet's one must the same way).
		const bool element = GetPlayerBotYoharaSlotHuntPoint(ch, slot.bWearCell) != 0 &&
				GetPlayerBotYoharaBonusSlotMaxLevel(item, GetPlayerBotYoharaSlotHuntPoint(ch, slot.bWearCell)) > 0 &&
				(slot.bWearCell == WEAR_BODY || slot.bWearCell == WEAR_WRIST || slot.bWearCell == WEAR_HEAD ||
				 slot.bWearCell == WEAR_PENDANT);
		return playerbot_yohara_bonus_rules::TierOf(lines, count, element ? slot.strongE : slot.strong,
				element ? slot.fairE : slot.fair, mustRolls, available);
	}

	// The ordinary stones in the bag: the first cell of each kind and the units.
	struct TPlayerBotYoharaBonusBag
	{
		int addCell, changeCell, marbleCell;
		int addUnits, changeUnits;
	};

	void ReadPlayerBotYoharaBonusBag(LPCHARACTER ch, TPlayerBotYoharaBonusBag& bag)
	{
		bag.addCell = bag.changeCell = bag.marbleCell = -1;
		bag.addUnits = bag.changeUnits = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM stone = ch->GetInventoryItem(cell);
			if (!stone || stone->GetCell() != cell || stone->GetType() != ITEM_USE || stone->GetCount() == 0 ||
					stone->isLocked() || IsPlayerBotGreenBonusStone(stone->GetVnum()) ||
					IsPlayerBotTradeableBonusVnum(stone->GetVnum()))
				continue;
			switch (stone->GetSubType())
			{
				case USE_ADD_ATTRIBUTE:
					bag.addUnits += (int)stone->GetCount();
					if (bag.addCell < 0)
						bag.addCell = cell;
					break;
				case USE_CHANGE_ATTRIBUTE:
					bag.changeUnits += (int)stone->GetCount();
					if (bag.changeCell < 0)
						bag.changeCell = cell;
					break;
				case USE_ADD_ATTRIBUTE2:
					if (bag.marbleCell < 0)
						bag.marbleCell = cell;
					break;
				default:
					break;
			}
		}
		// MT2009_PLUS_BOT_EKWIPUNEK_V1: the change stones the bag lent the extra inventory (the bag keeps a stack of
		// them, playerbot_ekwipunek_bots.h) count for the plan too - 800 of them are four stacks, three of which may wait
		// there; the stones themselves are still used from the bag's cell.
		if (ch && bag.changeCell >= 0)
			for (WORD cell = 0; cell < SPECIAL_INVENTORY_MAX_NUM; ++cell)
			{
				LPITEM stone = ch->Mt2009SpecialGetItem(CHANGE_INVENTORY, cell);
				if (!stone || stone->GetCell() != cell || stone->GetType() != ITEM_USE ||
						stone->GetSubType() != USE_CHANGE_ATTRIBUTE || stone->GetCount() == 0 || stone->isLocked() ||
						IsPlayerBotGreenBonusStone(stone->GetVnum()) || IsPlayerBotTradeableBonusVnum(stone->GetVnum()))
					continue;
				bag.changeUnits += (int)stone->GetCount();
			}
	}

	struct TPlayerBotYoharaBonusPiece
	{
		LPITEM item;
		int slotIndex;
	};

	// The worn pieces a stone may go on, in the priority order: really worn in that slot, able to come off (it has to,
	// for the engine to touch it) and taking stones at all (an attribute set, no costume, no wedding piece...). No
	// refine or level gate: the Yohara set is bonused as the bot wears it.
	void CollectPlayerBotYoharaBonusPieces(LPCHARACTER ch, std::vector<TPlayerBotYoharaBonusPiece>& out)
	{
		out.clear();
		for (int s = 0; ch && s < PLAYERBOT_YOHARA_BONUS_SLOT_COUNT; ++s)
		{
			const BYTE wearCell = PLAYERBOT_YOHARA_BONUS_SLOTS[s].bWearCell;
			LPITEM item = ch->GetWear(wearCell);
			if (!item || !IsPlayerBotWornItemSound(ch, item, wearCell) || IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE) ||
					IsPlayerBotSidekickLockedItem(ch, item) || IsPlayerBotSidekickPinned(ch, item) ||
					!CanPlayerBotTakeBonusStone(item))
				continue;
			const TPlayerBotYoharaBonusPiece piece = { item, s };
			out.push_back(piece);
		}
	}

	playerbot_yohara_bonus_rules::TPiece BuildPlayerBotYoharaBonusPiece(LPCHARACTER ch, const TPlayerBotYoharaBonusPiece& p,
			const std::map<DWORD, int>& spent)
	{
		playerbot_yohara_bonus_rules::TPiece piece;
		piece.lines = p.item->GetAttributeCount();
		piece.maxStoneLines = PLAYERBOT_YOHARA_BONUS_ADD_LINES;
		piece.lineRolls = piece.lines < PLAYERBOT_BONUS_MARBLE_LINES && CanPlayerBotItemRollNewLine(p.item);
		piece.tier = GetPlayerBotYoharaBonusTier(ch, p.item, p.slotIndex);
		std::map<DWORD, int>::const_iterator it = spent.find(p.item->GetID());
		piece.spent = it != spent.end() ? it->second : 0;
		piece.weight = PLAYERBOT_YOHARA_BONUS_SLOTS[p.slotIndex].iWeight;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase; a piece at its element target is done (strong)
		const BYTE wearCell = PLAYERBOT_YOHARA_BONUS_SLOTS[p.slotIndex].bWearCell;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		const int base = GetPlayerBotYoharaElementRank(wearCell) >= 0 ? GetPlayerBotYoharaElementSpentBase(ch, p.item, piece.spent) : 0;
#else
		const int base = 0;
#endif
		const int target = GetPlayerBotYoharaElementTarget(ch, p.item, wearCell, piece.spent - base);
		piece.elemRank = target >= 0 ? GetPlayerBotYoharaElementRank(wearCell) : -1;
		piece.elemShort = target == 0;
		piece.elemCap = target >= 0 ? GetPlayerBotYoharaElementCap(wearCell) + base : 0;
		if (target > 0)
			piece.tier = playerbot_yohara_bonus_rules::TIER_STRONG;
		return piece;
	}

	playerbot_yohara_bonus_rules::TChoice PickPlayerBotYoharaBonus(LPCHARACTER ch,
			const std::vector<TPlayerBotYoharaBonusPiece>& pieces, const std::map<DWORD, int>& spent,
			const TPlayerBotYoharaBonusBag& bag, std::vector<playerbot_yohara_bonus_rules::TPiece>& built)
	{
		built.clear();
		for (size_t i = 0; i < pieces.size(); ++i)
			built.push_back(BuildPlayerBotYoharaBonusPiece(ch, pieces[i], spent));
		const playerbot_yohara_bonus_rules::TBag kinds = {
			bag.addCell >= 0 ? bag.addUnits : 0, bag.changeCell >= 0 ? bag.changeUnits : 0, bag.marbleCell >= 0
		};
		if (built.empty())
		{
			const playerbot_yohara_bonus_rules::TChoice none = { -1, playerbot_yohara_bonus_rules::STEP_NONE,
					playerbot_yohara_bonus_rules::WANT_NONE, false, 0, false };
			return none;
		}
		return playerbot_yohara_bonus_rules::Pick(&built[0], (int)built.size(), kinds,
				PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE, PLAYERBOT_YOHARA_BONUS_SAFETY);
	}

	char PlayerBotYoharaBonusTierChar(int tier)
	{
		return tier >= playerbot_yohara_bonus_rules::TIER_STRONG ? 'A'
				: (tier >= playerbot_yohara_bonus_rules::TIER_FAIR ? 'B' : '-');
	}

	// Every listed slot as name:lines tier spent/share.
	std::string DescribePlayerBotYoharaBonusGear(const std::vector<TPlayerBotYoharaBonusPiece>& pieces,
			const std::vector<playerbot_yohara_bonus_rules::TPiece>& built, int changeUnits)
	{
		int sumWeights = 0;
		for (size_t i = 0; i < built.size(); ++i)
			if (built[i].lines > 0)
				sumWeights += built[i].weight;
		const int pool = built.empty() ? 0 : playerbot_yohara_bonus_rules::Pool(&built[0], (int)built.size(), changeUnits,
				PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE);
		std::string out;
		char buf[64];
		for (size_t i = 0; i < pieces.size() && i < built.size(); ++i)
		{
			snprintf(buf, sizeof(buf), "%s%s:%d%c%d/%d", out.empty() ? "" : " ",
					PLAYERBOT_YOHARA_BONUS_SLOTS[pieces[i].slotIndex].szName, built[i].lines,
					PlayerBotYoharaBonusTierChar(built[i].tier), built[i].spent,
					playerbot_yohara_bonus_rules::PieceCap(built[i].weight, sumWeights, pool));
			out += buf;
		}
		return out;
	}

	// One pass: -1 when the bot is not this pass's (the ordinary pass goes on), else the stones spent.
	int ManagePlayerBotYoharaBonus(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!IsPlayerBotYoharaBonusMember(ch))
			return -1;
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		if (bag.addCell < 0 && bag.changeCell < 0 && bag.marbleCell < 0)
			return -1;
		if (IsPlayerBotGearFrozen(ch))
			return 0;

		std::map<DWORD, int>& spent = s_mapPlayerBotYoharaBonusSpent[ch->GetPlayerID()];
		std::vector<TPlayerBotYoharaBonusPiece> pieces;
		CollectPlayerBotYoharaBonusPieces(ch, pieces);
		// the memory keeps the pieces worn now (and a few taken off for a refine)
		if (spent.size() > 32)
		{
			std::map<DWORD, int> keep;
			for (size_t i = 0; i < pieces.size(); ++i)
				if (spent.count(pieces[i].item->GetID()))
					keep[pieces[i].item->GetID()] = spent[pieces[i].item->GetID()];
			spent.swap(keep);
		}
		std::vector<playerbot_yohara_bonus_rules::TPiece> built;
		playerbot_yohara_bonus_rules::TChoice choice = PickPlayerBotYoharaBonus(ch, pieces, spent, bag, built);
		if (choice.piece < 0)
		{
			PlayerBotLogThrottled("yohara_bonus_done", dwNow,
					"PLAYERBOT_YOHARA_BONUS: done pid=%u name=%s stock_add=%d stock_change=%d marble=%d gear=[%s]",
					ch->GetPlayerID(), ch->GetName(), bag.addUnits, bag.changeUnits, bag.marbleCell >= 0 ? 1 : 0,
					DescribePlayerBotYoharaBonusGear(pieces, built, bag.changeUnits).c_str());
			return 0;
		}
		// A worn piece comes off for its stones and goes straight back on: only while the engine lets it back on.
		if (IsPlayerBotEquipWindowShut(ch, state))
		{
			state.dwNextBonusCheckTime = dwNow + PLAYERBOT_EQUIPMENT_COMBAT_DELAY;
			return 0;
		}

		const TPlayerBotYoharaBonusPiece target = pieces[choice.piece];
		LPITEM item = target.item;
		const int linesBefore = item->GetAttributeCount();
		const int tierBefore = built[choice.piece].tier;
		const bool leftover = choice.leftover;
		const bool elementPhase = choice.element;	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2
		const int cap = choice.cap;
		if (!ch->UnequipItem(item))
		{
			PlayerBotLogThrottled("yohara_bonus_unequip", dwNow,
					"PLAYERBOT_YOHARA_BONUS: unequip failed pid=%u name=%s slot=%s vnum=%u free_cell=%d",
					ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_BONUS_SLOTS[target.slotIndex].szName,
					item->GetVnum(), ch->GetEmptyInventory(1));
			state.dwNextBonusCheckTime = dwNow + PLAYERBOT_YOHARA_BONUS_PASS_MS;
			return 0;
		}
		int used[4] = { 0, 0, 0, 0 };	// by EStep
		int stones = 0;
		while (stones < PLAYERBOT_YOHARA_BONUS_STONES_PER_PASS && choice.piece >= 0 &&
				pieces[choice.piece].item == item && choice.step != playerbot_yohara_bonus_rules::STEP_NONE)
		{
			const int cell = choice.step == playerbot_yohara_bonus_rules::STEP_ADD ? bag.addCell
					: (choice.step == playerbot_yohara_bonus_rules::STEP_MARBLE ? bag.marbleCell : bag.changeCell);
			if (cell < 0)
				break;
			// the stone's own path, as at the counter: the odds of a line by the count already there, the stone
			// spent whether it lands or not; a change rerolls every line (and a weapon's addon)
			const int count = item->GetAttributeCount();
			if (choice.step == playerbot_yohara_bonus_rules::STEP_CHANGE)
			{
				item->ChangeAttribute();
				++spent[item->GetID()];
			}
			else if (count < ITEM_ATTRIBUTE_MAX_NUM && number(1, 100) <= aiItemAttributeAddPercent[count])
				item->AddAttribute();
			ConsumePlayerBotBonusStoneAt(ch, cell);
			LogManager::instance().ItemLog(ch, item,
					choice.step == playerbot_yohara_bonus_rules::STEP_ADD ? "PLAYERBOT_YOHARA_BONUS_ADD"
						: (choice.step == playerbot_yohara_bonus_rules::STEP_MARBLE ? "PLAYERBOT_YOHARA_BONUS_MARBLE"
							: "PLAYERBOT_YOHARA_BONUS_CHANGE"), item->GetName());
			++used[choice.step];
			++stones;
			ReadPlayerBotYoharaBonusBag(ch, bag);
			choice = PickPlayerBotYoharaBonus(ch, pieces, spent, bag, built);
		}
		item->UpdatePacket();
		if (!PlayerBotEquipItem(ch, item))
			sys_err("PLAYERBOT_YOHARA_BONUS: could not re-equip pid=%u name=%s vnum=%u slot=%s stones=%d",
					ch->GetPlayerID(), ch->GetName(), item->GetVnum(),
					PLAYERBOT_YOHARA_BONUS_SLOTS[target.slotIndex].szName, stones);

		int tierAfter = playerbot_yohara_bonus_rules::TIER_NONE;
		for (size_t i = 0; i < pieces.size() && i < built.size(); ++i)
			if (pieces[i].item == item)
				tierAfter = built[i].tier;
		sys_log(0, "PLAYERBOT_YOHARA_BONUS: pass pid=%u name=%s cohort=%d champion=%d slot=%s vnum=%u+%d add=%d marble=%d change=%d "
				"lines=%d->%d tier=%c->%c%s spent=%d share=%d%s%s stock_add=%d stock_change=%d gear=[%s]",
				ch->GetPlayerID(), ch->GetName(), IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) ? 1 : 0,
				(int)ch->GetConquerorLevel(), PLAYERBOT_YOHARA_BONUS_SLOTS[target.slotIndex].szName, item->GetVnum(),
				(int)item->GetRefineLevel(), used[playerbot_yohara_bonus_rules::STEP_ADD],
				used[playerbot_yohara_bonus_rules::STEP_MARBLE], used[playerbot_yohara_bonus_rules::STEP_CHANGE],
				linesBefore, item->GetAttributeCount(), PlayerBotYoharaBonusTierChar(tierBefore),
				PlayerBotYoharaBonusTierChar(tierAfter),
				tierAfter > tierBefore && tierAfter >= playerbot_yohara_bonus_rules::TIER_STRONG ? " TARGET" : "",
				spent.count(item->GetID()) ? spent[item->GetID()] : 0, cap, leftover ? " leftover" : "",
				elementPhase ? " element" : "",
				bag.addUnits, bag.changeUnits, DescribePlayerBotYoharaBonusGear(pieces, built, bag.changeUnits).c_str());
		state.dwNextBonusCheckTime = dwNow + PLAYERBOT_YOHARA_BONUS_PASS_MS;
		return stones;
	}
}

#endif
