#ifndef __INC_METIN2_PLAYERBOT_BONUS75_H__
#define __INC_METIN2_PLAYERBOT_BONUS75_H__

// MT2009_PLUS_BOT_BONUS75_V1 - the owner, 10 November 2026: from level 75 (the Grotto of Exile) the bots want better
// bonuses, not only the element resistances, and they never refine an already bonused piece at the blacksmith when
// they have the ItemShop.
//
// 1. The 1-5 bonus targets of a bot of level PLAYERBOT_BONUS75_MIN_LEVEL (m2_bot_bonus75_min_level) and over, per slot
//    (GetPlayerBotBonus75RoleFor - must / wanted, the lines that can roll on the piece's set only, world.item_attr):
//      slot     must                               wanted                                                       strong / fair
//      armour   Max HP + E (the element needed)    defence: magic / arrow / the weapon-type resistances,         4: m4 o3 / 3: m3 o2
//                                                  the other elements' resistances, melee reflection,             (with E: 3: m4 o3 /
//                                                  dodge / block, the Sung Ma defence lines where they roll        2: m3 o3)
//      helmet   E (none without it)                the defence lines above, HP regeneration                      3: o3 / 2: o2
//                                                                                                                (with E: 2: m4 o3 /
//                                                                                                                 2: m3 o2)
//      shield   stun resistance (immunity)         vitality (its HP), block, melee reflection, slow immunity,    2: m5 o3 / 1: m5
//                                                  the defence lines
//      weapon   strong vs devils                   critical, piercing, the class stat, strong vs humans,         3: m4 o3 / 2: m3 o3
//                                                  casting speed (a caster), the addon's average / skill line     (or the old finish:
//                                                                                                                 average 30 / skill)
//      necklace critical                           Max HP, piercing                                              2: m4 o3 / 1: m3
//      bracelet Max HP + E                         strong vs devils, piercing, HP steal (under the 50% cap),     3: m4 o3 / 2: m3 o3
//                                                  magic resistance
//      earrings strong vs devils                   movement speed, item drop, strong vs humans                   2: m4 o3 / 1: m3
//      boots    Max HP                             critical, attack speed, arrow dodge, movement speed           3: m4 o3 / 2: m3 o3
//    "3: m4 o3" = three lines of the list, each must at level 4-5 of the table (HP 1500/2000, devils 10/20, critical
//    5/10 in the global mode; an immunity is level 5) and the wanted lines at 3 or more (playerbot_yohara_bonus_rules.h
//    Meets / TierOf - never more lines than the set can roll). E: the resistance of the bot's element - the hunt element
//    of a Yohara bot (GetPlayerBotHuntResistPoint), else the element map's goal (playerbot_element_maps.h, a gated map or
//    a want of 25+); a must wherever it rolls (armour, helmet, bracelet), so the required resistance is kept.
//    The ordinary pass (playerbot_bonus.h, PlayerBotWantsBonusChange): a worn piece of such a bot is changed while it is
//    under its strong target and has had fewer than half of its budget of changes (this core's memory), under its
//    fair target up to the whole budget (PLAYERBOT_BONUS75_SLOTS: 50-120 a piece, 250 the armour / bracelet and 120
//    the helmet carrying E; m2_bot_bonus75_cap_pct scales them), and never once it is strong - the old score / finish
//    stop and the protected-line rule are not asked for it (a top line of its list is part of the target). The Yohara
//    pass (playerbot_yohara_bonus.h) takes the same must / wanted lines from 75 with its own tiers, shares and element
//    phase. What stays: the element shop's pinned pieces are never changed, the marble-first gate (a bot with SM
//    changes only a five-line piece - the adds and the marble first; four lines only as its last resort) applies after
//    this rule in both passes, and the 6/7 pass is untouched (a change rerolls the five ordinary lines, never the
//    6th/7th; the pieces of the 6/7 scope still get their adds and marble first).
// 2. An already bonused piece (PLAYERBOT_BONUS_SCROLL_MIN_LINES lines or more, m2_bot_bonus_scroll_min_lines) of a bot
//    with ItemShop access (V3 the bots' source, the balance read, Smocze Monety or Smocze Znaki held -
//    PlayerBotHasItemShopAccess) is never raised at the plain anvil on a step that can fail: IsPlayerBotPlainAnvilBarred
//    says so (the blacksmith pass then puts the step under a scroll or lets it wait, the field pass takes it under a
//    scroll wherever the bot stands, the coin and the cheap-piece policy never send it to the anvil, the Demon Tower's
//    smith never takes it). The scroll is FindPlayerBotRefineScrollCell's (DoRefineWithScroll, char_item.cpp): the
//    Magiczny Kamien (25042, NO_REDUCTION_WHEN_FAIL - a failure keeps the piece and its plus) first on a low step, the
//    Zwoj Wojny (25044 / 71021 / 39014, UP_TO_3TH_LEVEL - 100% under +4), the Zwoj Blogoslawienstwa (25040 / 25041 /
//    76016), the Zwoj Boga Smokow (71032 / 25045, +10%) and the Podrecznik Kowala (70039 / 25043, +15%) - the last three
//    NORMAL_REFINE_SCROLL: a failure hands the piece back one plus down, bonuses kept. The plain anvil (DoRefine)
//    destroys the piece and its bonuses; the Gwarancje (REFINE_BONUS_SCROLL) destroy too and are never taken. Gear of
//    level 100+ keeps its own ladder (playerbot_high_gear_refine.h), gear no scroll goes on (level 18 and under, or worth
//    less than a scroll) its old rules. The shop: while a worn bonused piece waits for a scroll its step can take, the
//    V3 goal "refine_bonus" buys Zwoj Blogoslawienstwa (25041 - a Smocze Znaki line only, 350 / 720 for three: outside
//    the SM pool, as every Znaki purchase; the catalogue's hold 6 / day 6 clamp it), two a waiting piece up to
//    PLAYERBOT_BONUS_SCROLL_BATCH; the Blacksmith's crafting pass turns them into Zwoj Boga Smokow / Podrecznik Kowala
//    with Magiczny Metal / Kamien Kowala (the smith_scroll goal, Smocze Monety within the daily pool). A bot without
//    ItemShop access keeps today's behaviour.
// 3. The census every 10 minutes: PLAYERBOT_BONUS75 (the 75+ bots on this core, the worn pieces per slot and how many
//    meet the strong / the fair target, the changes by slot of the ordinary and the Yohara pass) and
//    PLAYERBOT_BONUS_SCROLL (the refines of bonused pieces by scroll and at the plain anvil, ok / tries, for the bots
//    with ItemShop access and without; the steps that waited for a scroll; the V3 goal's pieces wanted / bought; the
//    worn bonused pieces waiting now).
//
// Flags: m2_bot_bonus75_off (1: rule 1 off - the old targets), m2_bot_bonus75_min_level (0: 75), m2_bot_bonus75_cap_pct
// (0: 100 - the change budgets in per cent, 10-1000), m2_bot_bonus_scroll_off (1: rule 2 off - the old anvil rules),
// m2_bot_bonus_scroll_min_lines (0: 2; 1-5).
//
// An implementation fragment: include it once, from playerbot_manager.cpp, right after playerbot_marble_first.h; the
// declarations the earlier files ask are in playerbot_types.h.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_BONUS75_V1)

namespace
{
	const char* const PLAYERBOT_BONUS75_OFF_FLAG = "m2_bot_bonus75_off";
	const char* const PLAYERBOT_BONUS75_MIN_LEVEL_FLAG = "m2_bot_bonus75_min_level";
	const char* const PLAYERBOT_BONUS75_CAP_PCT_FLAG = "m2_bot_bonus75_cap_pct";
	const char* const PLAYERBOT_BONUS_SCROLL_OFF_FLAG = "m2_bot_bonus_scroll_off";
	const char* const PLAYERBOT_BONUS_SCROLL_MIN_LINES_FLAG = "m2_bot_bonus_scroll_min_lines";
	const int PLAYERBOT_BONUS75_MIN_LEVEL = 75;
	const int PLAYERBOT_BONUS_SCROLL_MIN_LINES = 2;
	const int PLAYERBOT_BONUS_SCROLL_BATCH = 4;
	const DWORD PLAYERBOT_BONUS75_CENSUS_MS = 10 * 60 * 1000;

	struct TPlayerBotBonus75Slot
	{
		BYTE bWearCell;
		const char* szName;
		playerbot_yohara_bonus_rules::TTier strong;
		playerbot_yohara_bonus_rules::TTier fair;
		// with the element needed (E) a must of the piece
		playerbot_yohara_bonus_rules::TTier strongE;
		playerbot_yohara_bonus_rules::TTier fairE;
		int iCap;	// changes on the piece (the ordinary pass), with E
		int iCapE;
	};

	const TPlayerBotBonus75Slot PLAYERBOT_BONUS75_SLOTS[] = {
		{ WEAR_WEAPON, "weapon", { 3, 4, 3 }, { 2, 3, 3 }, { 3, 4, 3 }, { 2, 3, 3 }, 100, 100 },
		{ WEAR_BODY,   "body",   { 4, 4, 3 }, { 3, 3, 2 }, { 3, 4, 3 }, { 2, 3, 3 }, 120, 250 },
		{ WEAR_HEAD,   "head",   { 3, 3, 3 }, { 2, 3, 2 }, { 2, 4, 3 }, { 2, 3, 2 },  80, 120 },
		{ WEAR_SHIELD, "shield", { 2, 5, 3 }, { 1, 5, 0 }, { 2, 5, 3 }, { 1, 5, 0 }, 100, 100 },
		{ WEAR_NECK,   "neck",   { 2, 4, 3 }, { 1, 3, 0 }, { 2, 4, 3 }, { 1, 3, 0 },  60,  60 },
		{ WEAR_WRIST,  "wrist",  { 3, 4, 3 }, { 2, 3, 3 }, { 3, 4, 3 }, { 2, 3, 3 },  80, 250 },
		{ WEAR_EAR,    "ear",    { 2, 4, 3 }, { 1, 3, 0 }, { 2, 4, 3 }, { 1, 3, 0 },  50,  50 },
		{ WEAR_FOOTS,  "foots",  { 3, 4, 3 }, { 2, 3, 3 }, { 3, 4, 3 }, { 2, 3, 3 },  60,  60 },
	};
	const int PLAYERBOT_BONUS75_SLOT_COUNT = (int)(sizeof(PLAYERBOT_BONUS75_SLOTS) / sizeof(PLAYERBOT_BONUS75_SLOTS[0]));

	struct TPlayerBotBonus75Stats
	{
		unsigned int changes[PLAYERBOT_BONUS75_SLOT_COUNT];
		unsigned int changesYohara[PLAYERBOT_BONUS75_SLOT_COUNT];
		// rule 2: the refines of bonused pieces - [ItemShop access][0 the plain anvil on a step that can fail, 1 a scroll]
		unsigned int refTries[2][2], refOk[2][2];
		unsigned int anvilSure;	// the plain anvil at 100% (nothing can burn)
		unsigned int waits, shopGoals, shopWanted, shopBought;
		TPlayerBotBonus75Stats() { memset(this, 0, sizeof(*this)); }
	};
	TPlayerBotBonus75Stats s_kPlayerBotBonus75Stats;
	DWORD s_dwPlayerBotBonus75CensusAt = 0;
	// changes per worn piece (item id) by the ordinary pass, per bot - this core's memory
	std::map<DWORD, std::map<DWORD, int> > s_mapPlayerBotBonus75Spent;

	int GetPlayerBotBonus75Flag(const char* flag)
	{
		return quest::CQuestManager::instance().GetEventFlag(flag);
	}

	int GetPlayerBotBonus75MinLevel()
	{
		const int v = GetPlayerBotBonus75Flag(PLAYERBOT_BONUS75_MIN_LEVEL_FLAG);
		return v > 0 && v <= 250 ? v : PLAYERBOT_BONUS75_MIN_LEVEL;
	}

	int FindPlayerBotBonus75Slot(BYTE wearCell)
	{
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
			if (PLAYERBOT_BONUS75_SLOTS[s].bWearCell == wearCell)
				return s;
		return -1;
	}

	// A bot of the stage: a bot (not a companion), level 75 or more, the rule on.
	bool IsPlayerBotBonus75Stage(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && !IsPlayerBotSidekickPID(ch->GetPlayerID()) &&
				GetPlayerBotBonus75Flag(PLAYERBOT_BONUS75_OFF_FLAG) == 0 && (int)ch->GetLevel() >= GetPlayerBotBonus75MinLevel();
	}

	// The element resistance the bot needs on its gear (0 none): a Yohara bot's hunt element, else the element map's goal.
	BYTE GetPlayerBotBonus75ElementPoint(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		if (IsPlayerBotYoharaBonusMember(ch))
			return GetPlayerBotHuntResistPoint(ch);
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementMapGoal(ch, v) || v.iElement < 0 || v.iElement >= 6)
			return 0;
		if (v.iGate <= 0 && v.iWant < PLAYERBOT_ELEMENT_MAP_REROLL_WANT)
			return 0;
		return PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
	}

	// The defence lines (the owner's "defence stats"): what lowers the damage taken - the magic, arrow, weapon-type and
	// element resistances, melee reflection, dodge, block, and the Sung Ma defence lines where a set rolls them.
	bool IsPlayerBotBonus75DefenceLine(WORD type) // MT2009_PLUS_WIDE_ATTR_V1
	{
		switch (type)
		{
			case APPLY_RESIST_MAGIC:
			case APPLY_RESIST_BOW:
			case APPLY_RESIST_SWORD:
			case APPLY_RESIST_TWOHAND:
			case APPLY_RESIST_DAGGER:
			case APPLY_RESIST_BELL:
			case APPLY_RESIST_FAN:
			case APPLY_RESIST_FIRE:
			case APPLY_RESIST_ELEC:
			case APPLY_RESIST_WIND:
			case APPLY_RESIST_ICE:
			case APPLY_RESIST_EARTH:
			case APPLY_RESIST_DARK:
			case APPLY_REFLECT_MELEE:
			case APPLY_DODGE:
			case APPLY_BLOCK:
			case POINT_DEF_BONUS:
			case POINT_NORMAL_HIT_DEFEND_BONUS:
			case POINT_SKILL_DEFEND_BONUS:
			case POINT_RESIST_CRITICAL:
			case POINT_RESIST_PENETRATE:
				return true;
			default:
				return false;
		}
	}

	// A line's role in the 75+ target of a slot (the table at the head of the file); -1: a slot the rule has no list
	// for (the glove, the talisman - their old rules). elem: GetPlayerBotBonus75ElementPoint.
	int GetPlayerBotBonus75RoleFor(LPCHARACTER ch, BYTE wearCell, WORD type, bool addonWeapon, BYTE elem) // MT2009_PLUS_WIDE_ATTR_V1
	{
		using namespace playerbot_yohara_bonus_rules;
		if (!ch || FindPlayerBotBonus75Slot(wearCell) < 0)
			return -1;
		const bool caster = IsPlayerBotCaster(ch);
		const bool defence = IsPlayerBotBonus75DefenceLine(type);
		const bool element = elem != 0 && type == elem;
		// MT2009_PLUS_STEAL_CAP_V1: the rest of the gear already gives the 50% cap - absorption here is wasted
		if (type == APPLY_STEAL_HP && GetPlayerBotGearStealHp(ch, wearCell) >= 50)
			return ROLE_OTHER;
		switch (wearCell)
		{
			case WEAR_WEAPON:
				if (type == APPLY_ATTBONUS_DEVIL)
					return ROLE_MUST;
				return type == APPLY_CRITICAL_PCT || type == APPLY_PENETRATE_PCT ||
						type == (WORD)GetPlayerBotYoharaBonusClassStat(ch) || type == APPLY_ATTBONUS_HUMAN ||
						(caster && type == APPLY_CAST_SPEED) ||
						(addonWeapon && type == (caster ? APPLY_SKILL_DAMAGE_BONUS : APPLY_NORMAL_HIT_DAMAGE_BONUS))
						? ROLE_WANTED : ROLE_OTHER;
			case WEAR_BODY:
				if (type == APPLY_MAX_HP)
					return ROLE_MUST;
				if (element)
					return ROLE_MUST2;
				return defence ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_HEAD:
				if (element)
					return ROLE_MUST;
				return defence || type == APPLY_HP_REGEN ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_SHIELD:
				if (type == APPLY_IMMUNE_STUN)
					return ROLE_MUST;
				return defence || type == APPLY_CON || type == APPLY_IMMUNE_SLOW ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_NECK:
				if (type == APPLY_CRITICAL_PCT)
					return ROLE_MUST;
				return type == APPLY_MAX_HP || type == APPLY_PENETRATE_PCT ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_WRIST:
				if (type == APPLY_MAX_HP)
					return ROLE_MUST;
				if (element)
					return ROLE_MUST2;
				return type == APPLY_ATTBONUS_DEVIL || type == APPLY_PENETRATE_PCT || type == APPLY_STEAL_HP ||
						type == APPLY_RESIST_MAGIC ? ROLE_WANTED : ROLE_OTHER;
			case WEAR_EAR:
				if (type == APPLY_ATTBONUS_DEVIL)
					return ROLE_MUST;
				return type == APPLY_MOV_SPEED || type == APPLY_ITEM_DROP_BONUS || type == APPLY_ATTBONUS_HUMAN
						? ROLE_WANTED : ROLE_OTHER;
			case WEAR_FOOTS:
				if (type == APPLY_MAX_HP)
					return ROLE_MUST;
				return type == APPLY_CRITICAL_PCT || type == APPLY_ATT_SPEED || type == APPLY_DODGE || type == APPLY_MOV_SPEED
						? ROLE_WANTED : ROLE_OTHER;
			default:
				return -1;
		}
	}

	// The piece's tier against its slot's 75+ target (-1: no list for the slot). *pElement: E is a must of the piece.
	int GetPlayerBotBonus75Tier(LPCHARACTER ch, LPITEM item, BYTE wearCell, BYTE elem, bool* pElement)
	{
		using namespace playerbot_yohara_bonus_rules;
		if (pElement)
			*pElement = false;
		const int s = FindPlayerBotBonus75Slot(wearCell);
		if (!ch || !item || s < 0)
			return -1;
		const TPlayerBotBonus75Slot& slot = PLAYERBOT_BONUS75_SLOTS[s];
		const bool addonWeapon = wearCell == WEAR_WEAPON && HasPlayerBotDamageAddon(item);
		TLine lines[ITEM_ATTRIBUTE_MAX_NUM];
		int count = 0;
		for (int i = 0; i < PLAYERBOT_BONUS_MARBLE_LINES && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const WORD type = item->GetAttributeType(i); // MT2009_PLUS_WIDE_ATTR_V1
			const long value = item->GetAttributeValue(i);
			if (type == 0 || value <= 0)
				continue;
			const int role = GetPlayerBotBonus75RoleFor(ch, wearCell, type, addonWeapon, elem);
			lines[count].role = role < 0 ? ROLE_OTHER : role;
			lines[count].level = GetPlayerBotYoharaBonusLineLevel(item, type, value);
			++count;
		}
		int mustRolls = 0, available = 0;
		for (TItemAttrMap::const_iterator it = g_map_itemAttr.begin(); it != g_map_itemAttr.end(); ++it)
		{
			const WORD type = (WORD)it->first;
			const int role = GetPlayerBotBonus75RoleFor(ch, wearCell, type, addonWeapon, elem);
			if (role <= ROLE_OTHER || GetPlayerBotYoharaBonusSlotMaxLevel(item, type) <= 0)
				continue;
			++available;
			if (role == ROLE_MUST)
				mustRolls |= MUST_ROLLS_1;
			else if (role == ROLE_MUST2)
				mustRolls |= MUST_ROLLS_2;
		}
		if (addonWeapon)
			++available;	// the addon's average (skill) line: not in item_attr
		const bool e = elem != 0 && (wearCell == WEAR_BODY || wearCell == WEAR_HEAD || wearCell == WEAR_WRIST) &&
				GetPlayerBotYoharaBonusSlotMaxLevel(item, elem) > 0;
		if (pElement)
			*pElement = e;
		int tier = TierOf(lines, count, e ? slot.strongE : slot.strong, e ? slot.fairE : slot.fair, mustRolls, available);
		// a weapon finished by the old rule (its average 30+, a big skill line) is never mixed off for the list
		if (wearCell == WEAR_WEAPON && tier < TIER_STRONG && HasPlayerBotFinishedBonus(ch, item, WEAR_WEAPON))
			tier = TIER_STRONG;
		return tier;
	}

	int GetPlayerBotBonus75Cap(int slot, bool element)
	{
		if (slot < 0 || slot >= PLAYERBOT_BONUS75_SLOT_COUNT)
			return 0;
		int pct = GetPlayerBotBonus75Flag(PLAYERBOT_BONUS75_CAP_PCT_FLAG);
		pct = pct <= 0 ? 100 : std::max(10, std::min(pct, 1000));
		const int cap = element ? PLAYERBOT_BONUS75_SLOTS[slot].iCapE : PLAYERBOT_BONUS75_SLOTS[slot].iCap;
		return std::max(1, cap * pct / 100);
	}

	int GetPlayerBotBonus75Spent(LPCHARACTER ch, LPITEM item)
	{
		std::map<DWORD, std::map<DWORD, int> >::const_iterator b = s_mapPlayerBotBonus75Spent.find(ch->GetPlayerID());
		if (b == s_mapPlayerBotBonus75Spent.end())
			return 0;
		std::map<DWORD, int>::const_iterator it = b->second.find(item->GetID());
		return it != b->second.end() ? it->second : 0;
	}

	// The ordinary pass's answer for a worn piece of a 75+ bot: -1 not this rule's (the old rules decide), 0 no change,
	// 1 a change wanted (strong under half of the budget, fair up to the whole budget, never past strong).
	int GetPlayerBotBonus75ChangeVerdict(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!item || !IsPlayerBotBonus75Stage(ch) || IsPlayerBotYoharaBonusMember(ch) ||
				IsPlayerBotSpecialLevel30WeaponVnum(item->GetVnum()))
			return -1;
		const int s = FindPlayerBotBonus75Slot(wearCell);
		if (s < 0)
			return -1;
		bool element = false;
		const int tier = GetPlayerBotBonus75Tier(ch, item, wearCell, GetPlayerBotBonus75ElementPoint(ch), &element);
		if (tier < 0)
			return -1;
		const playerbot_yohara_bonus_rules::EWant want = playerbot_yohara_bonus_rules::MainWant(tier,
				GetPlayerBotBonus75Spent(ch, item), GetPlayerBotBonus75Cap(s, element));
		return want != playerbot_yohara_bonus_rules::WANT_NONE ? 1 : 0;
	}

	// A change on a worn piece of a 75+ bot (the ordinary pass: its budget's memory too; the Yohara pass: the census).
	void NotePlayerBotBonus75Change(LPCHARACTER ch, LPITEM item, BYTE wearCell, bool yohara)
	{
		if (!ch || !item || !IsPlayerBotBonus75Stage(ch))
			return;
		const int s = FindPlayerBotBonus75Slot(wearCell);
		if (s < 0)
			return;
#ifdef MT2009_PLUS_BOT_BONUSMIX_V1
		NotePlayerBotBonusMixChange(ch, yohara);	// MT2009_PLUS_BOT_BONUSMIX_V1: in the field or in town, the mix's clock
#endif
		if (yohara)
		{
			++s_kPlayerBotBonus75Stats.changesYohara[s];
			return;
		}
		++s_kPlayerBotBonus75Stats.changes[s];
		std::map<DWORD, int>& spent = s_mapPlayerBotBonus75Spent[ch->GetPlayerID()];
		if (spent.size() > 32 && !spent.count(item->GetID()))
		{
			std::map<DWORD, int> keep;
			for (int w = 0; w < PLAYERBOT_BONUS75_SLOT_COUNT; ++w)
				if (LPITEM worn = ch->GetWear(PLAYERBOT_BONUS75_SLOTS[w].bWearCell))
					if (spent.count(worn->GetID()))
						keep[worn->GetID()] = spent[worn->GetID()];
			spent.swap(keep);
		}
		++spent[item->GetID()];
	}

	// ------------------------------------------------------------------------------------------------ rule 2

	// The ItemShop V3 is the bots' source and on, the bot's balance is read and holds Smocze Monety or Smocze Znaki.
	bool PlayerBotHasItemShopAccess(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled())
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return st != s_mapPlayerBotAIStates.end() && st->second.bDragonBalanceKnown &&
				(st->second.iDragonCoins > 0 || st->second.iDragonMarks > 0);
	}

	int GetPlayerBotBonusScrollMinLines()
	{
		const int v = GetPlayerBotBonus75Flag(PLAYERBOT_BONUS_SCROLL_MIN_LINES_FLAG);
		return v >= 1 && v <= PLAYERBOT_BONUS_MARBLE_LINES ? v : PLAYERBOT_BONUS_SCROLL_MIN_LINES;
	}

	// An already bonused weapon or armour piece of a bot with ItemShop access, one a scroll goes on: never to the plain
	// anvil on a step that can fail.
	bool IsPlayerBotBonusScrollPiece(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetRefinedVnum() == 0 || GetPlayerBotBonus75Flag(PLAYERBOT_BONUS_SCROLL_OFF_FLAG) != 0)
			return false;
		if (item->GetType() != ITEM_ARMOR && !(item->GetType() == ITEM_WEAPON && item->GetSubType() != WEAPON_ARROW))
			return false;
		if (item->GetAttributeCount() < GetPlayerBotBonusScrollMinLines() || IsPlayerBotTalismanItem(item) ||
				IsPlayerBotScrollFreeGear(item) || IsPlayerBotHighGear(item))
			return false;
		return PlayerBotHasItemShopAccess(ch);
	}

	// A refine attempt on a piece of linesBefore lines (the census; the bonused ones only).
	void NotePlayerBotBonusScrollRefine(LPCHARACTER ch, int linesBefore, bool scroll, bool success, int stepProb)
	{
		if (!ch || linesBefore < GetPlayerBotBonusScrollMinLines())
			return;
		TPlayerBotBonus75Stats& s = s_kPlayerBotBonus75Stats;
		if (!scroll && stepProb >= 100)
		{
			++s.anvilSure;
			return;
		}
		const int access = PlayerBotHasItemShopAccess(ch) ? 1 : 0;
		const int way = scroll ? 1 : 0;
		++s.refTries[access][way];
		if (success)
			++s.refOk[access][way];
	}

	// A bonused piece's step held for a scroll (the blacksmith pass).
	void NotePlayerBotBonusScrollWait(LPCHARACTER ch, LPITEM item)
	{
		if (!IsPlayerBotBonusScrollPiece(ch, item))
			return;
		++s_kPlayerBotBonus75Stats.waits;
		PlayerBotLogThrottled("bonus_scroll_wait", get_dword_time(),
				"PLAYERBOT_BONUS_SCROLL: waits for a scroll pid=%u name=%s vnum=%u plus=%u lines=%d safe_scrolls=%d",
				ch->GetPlayerID(), ch->GetName(), item->GetVnum(), (unsigned int)item->GetRefineLevel(),
				item->GetAttributeCount(), CountPlayerBotSafeRefineScrolls(ch));
	}

	// The worn bonused pieces under their target plus whose next step can fail and has no scroll in the bag.
	int CountPlayerBotBonusScrollWaiting(LPCHARACTER ch)
	{
		static const BYTE s_wears[] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR };
		int n = 0;
		for (size_t i = 0; ch && i < sizeof(s_wears) / sizeof(s_wears[0]); ++i)
		{
			LPITEM item = ch->GetWear(s_wears[i]);
			if (!item || !IsPlayerBotBonusScrollPiece(ch, item) ||
					(int)item->GetRefineLevel() >= (int)GetPlayerBotRefineTarget(ch, item))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(item->GetRefineSet());
			if (!recipe || recipe->prob >= 100 || !IsPlayerBotScrollStepAllowed(item->GetRefineLevel()))
				continue;
			if (FindPlayerBotRefineScrollCellFor(ch, item, (int)recipe->prob) >= 0)
				continue;
			++n;
		}
		return n;
	}

#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
	// The V3 goal (CollectPlayerBotIshop3Goals): Zwoj Blogoslawienstwa for the worn bonused pieces waiting for one - not
	// when another goal of the list buys it already.
	void CollectPlayerBotBonusScrollGoals(LPCHARACTER ch, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (!ch || n >= PLAYERBOT_ISHOP3_MAX_GOALS || GetPlayerBotBonus75Flag(PLAYERBOT_BONUS_SCROLL_OFF_FLAG) != 0)
			return;
		for (int i = 0; i < n; ++i)
			if (goals[i].dwVnum == PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM)
				return;
		const int waiting = CountPlayerBotBonusScrollWaiting(ch);
		if (waiting <= 0)
			return;
		const TPlayerBotIshop3Goal g = { PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM, true,
				std::min(waiting * 2, PLAYERBOT_BONUS_SCROLL_BATCH), "refine_bonus" };
		goals[n++] = g;
	}
#endif

	void NotePlayerBotBonusScrollShop(int wanted, int got)
	{
		TPlayerBotBonus75Stats& s = s_kPlayerBotBonus75Stats;
		++s.shopGoals;
		s.shopWanted += (unsigned int)std::max(0, wanted);
		s.shopBought += (unsigned int)std::max(0, got);
	}

	// ------------------------------------------------------------------------------------------------ the census

	void LogPlayerBotBonus75Census(DWORD dwNow)
	{
		if (s_dwPlayerBotBonus75CensusAt != 0 && (int)(dwNow - s_dwPlayerBotBonus75CensusAt) < 0)
			return;
		const bool first = s_dwPlayerBotBonus75CensusAt == 0;
		s_dwPlayerBotBonus75CensusAt = dwNow + PLAYERBOT_BONUS75_CENSUS_MS;
		if (first)
			return;
		unsigned int bots = 0, accessBots = 0, waitingPieces = 0;
		unsigned int pieces[PLAYERBOT_BONUS75_SLOT_COUNT], strong[PLAYERBOT_BONUS75_SLOT_COUNT], fair[PLAYERBOT_BONUS75_SLOT_COUNT];
		memset(pieces, 0, sizeof(pieces));
		memset(strong, 0, sizeof(strong));
		memset(fair, 0, sizeof(fair));
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || !IsPlayerBotBonus75Stage(ch))
				continue;
			++bots;
			if (PlayerBotHasItemShopAccess(ch))
			{
				++accessBots;
				waitingPieces += (unsigned int)CountPlayerBotBonusScrollWaiting(ch);
			}
			const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
			for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
			{
				LPITEM item = ch->GetWear(PLAYERBOT_BONUS75_SLOTS[s].bWearCell);
				if (!item || !CanPlayerBotTakeBonusStone(item))
					continue;
				const int tier = GetPlayerBotBonus75Tier(ch, item, PLAYERBOT_BONUS75_SLOTS[s].bWearCell, elem, NULL);
				if (tier < 0)
					continue;
				++pieces[s];
				if (tier >= playerbot_yohara_bonus_rules::TIER_STRONG)
					++strong[s];
				else if (tier >= playerbot_yohara_bonus_rules::TIER_FAIR)
					++fair[s];
			}
		}
		const TPlayerBotBonus75Stats& st = s_kPlayerBotBonus75Stats;
		std::string targets, changes, changesY;
		char buf[96];
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
		{
			snprintf(buf, sizeof(buf), "%s%s=%u:%u/%u", s ? " " : "", PLAYERBOT_BONUS75_SLOTS[s].szName, pieces[s], strong[s],
					fair[s]);
			targets += buf;
			snprintf(buf, sizeof(buf), "%s%s:%u", s ? " " : "", PLAYERBOT_BONUS75_SLOTS[s].szName, st.changes[s]);
			changes += buf;
			snprintf(buf, sizeof(buf), "%s%s:%u", s ? " " : "", PLAYERBOT_BONUS75_SLOTS[s].szName, st.changesYohara[s]);
			changesY += buf;
		}
		sys_log(0, "PLAYERBOT_BONUS75: census on=%d min_level=%d bots=%u targets(pieces:strong/fair) [%s] changes ordinary=[%s] "
				"yohara=[%s]",
				GetPlayerBotBonus75Flag(PLAYERBOT_BONUS75_OFF_FLAG) == 0 ? 1 : 0, GetPlayerBotBonus75MinLevel(), bots,
				targets.c_str(), changes.c_str(), changesY.c_str());
		sys_log(0, "PLAYERBOT_BONUS_SCROLL: census on=%d min_lines=%d bonused refines (ok/tries) ishop scroll=%u/%u anvil=%u/%u "
				"no_ishop scroll=%u/%u anvil=%u/%u anvil_100=%u waits=%u v3 goals=%u wanted=%u bought=%u stage_bots=%u "
				"ishop_bots=%u worn_waiting=%u",
				GetPlayerBotBonus75Flag(PLAYERBOT_BONUS_SCROLL_OFF_FLAG) == 0 ? 1 : 0, GetPlayerBotBonusScrollMinLines(),
				st.refOk[1][1], st.refTries[1][1], st.refOk[1][0], st.refTries[1][0], st.refOk[0][1], st.refTries[0][1],
				st.refOk[0][0], st.refTries[0][0], st.anvilSure, st.waits, st.shopGoals, st.shopWanted, st.shopBought, bots,
				accessBots, waitingPieces);
	}
}

#endif

#endif
