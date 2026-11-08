#ifndef __INC_METIN2_PLAYERBOT_BONUS67_BOTS_H__
#define __INC_METIN2_PLAYERBOT_BONUS67_BOTS_H__

// MT2009_PLUS_BOT_BONUS67_V1 - the bots learn the whole 6/7 bonus system (Seon-Hae) from the Grotto of Exile stage on
// (the owner, 8 November 2026: "Naucz boty calego systemu", rules 1-8; "bardzo wazne").
//
// What there was (MT2009_PLUS_BOT_USE_SHOP_AIDS_V1 / MT2009_PLUS_BOT_SEONHAE_V2, playerbot_shop_aids.h): from level 50
// a bot walked to the Seon-Hae of its first village with any worn piece (weapon and armour with a spare in the bag,
// glove, helmet, jewellery, shield, boots), handed it in through the core's own mt2009_seonhae::Add and came back a
// day later (m2_seonhae_wait_min) to collect it; every worn piece with 6th/7th lines took 71052 until a "must" line
// came (PLAYERBOT_RARE67, 5-12 a slot), whatever its count of lines; the shards it kept were ten of any worn piece's
// band. With this pass on those two are off for the bots (an item Seon-Hae already keeps is still collected) and the
// Champion's glove pass (PLAYERBOT_GLOVE67) stays as it was.
//
// The owner's rules and how they are kept here:
//  1. When: from level PLAYERBOT_BONUS67_MIN_LEVEL (75, m2_bot_bonus67_min_level) - the Grotto of Exile stage, where
//     the shards drop for the bots too (MT2009_PLUS_BOT_SEONHAE_V2). Companions (sidekicks) never.
//  2. Which pieces (worn, nothing else - PLAYERBOT_BONUS67_SLOTS, GetPlayerBotBonus67Scope):
//       * the jewellery of Niebianskie Lzy ("niebieskie lzy": Bransol. 14200-14209, Naszyj. 16200-16209, Kolczyki
//         17200-17209, item level 54) and everything above it - every bracelet, necklace and earring of item level 54
//         and up: Krysztal Duszy (14220 / 16220 / 17220, 58-62), Rubin / Granat / Szmaragd / Szafir / Turmalin
//         (14500-14579, 16500-16579, 17500-17569, 85-100) and the Jade pieces (Obrecz / Kolia / Klipsy Jadeitu,
//         14580-14619, 16580-16619, 17570-17609, 105 - Zolte Lsniace Odlamki 39080; MT2009_PLUS_JADE_BONUS67_V1, the
//         owner 8 Nov 2026 "napraw": their Precyzja and Will are the base attribute (item_yextra,
//         MT2009_PLUS_JADE_BASE_V1), no 6/7 add or change touches them, both 6th/7th slots are free for the pool -
//         an old piece with a base line still in a slot moves it out first, Mt2009JadeBaseMigrate);
//       * jewellery and boots carrying the resistance of the element the bot needs now - the hunt element of a
//         Yohara bot (GetPlayerBotHuntElementIndex), else the element progression's goal
//         (MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1, GetPlayerBotElementMapGoal): in the proto (Miedziany / Drewniany /
//         Srebrny Naszyjnik, Bambusowe / Drewniane / Wyszywane Zlotem Buty) or on one of its five lines;
//       * a body armour of item level 61 and up; a helmet or a shield of 41 and up.
//  3. How: as a player - the core's rules (five ordinary lines, fewer than two extra, the rare pool's room, the shard
//     of the piece's band - mt2009_seonhae::MaterialVnum -, 1-10 shards, 0-5 Suplementy of one kind, the wiki's chance
//     mt2009_seonhae::ChancePct: 2 % a shard + the kind's % per piece) - but at once: no NPC, no 24 h; the roll is made
//     and the line added (CItem::AddRareAttribute, the panel's m2_rare_lv1..5 odds, as Seon-Hae's collect) in the same
//     pass, the piece off the body and on again (the engine refuses an equipped one). A Magiczny Przedmiot (71051) the
//     bot holds is used first (100 %, the engine's own use). The Suplementy: Silny (72067, 18 SM) from the ItemShop V3
//     ("bonus_b67add", within the daily SM pool - never urgent) up to five, while the coins and the pool's day room
//     pay for them; the add waits for them PLAYERBOT_BONUS67_ADDITIVE_WAIT_MS at most.
//  4. The shards: ten for an add. Short of them the bot wants the band's shard on the market (the stalls - its want,
//     PlayerBotWantsAnythingFromMarket - and the offline counters' sink scan, a part of a stack as needed, its own
//     price cap CanPlayerBotPayForBonus67Shard); with no counter holding it for PLAYERBOT_BONUS67_NO_SUPPLY_MS, the last
//     resort: Zdobna Skrz. z Odlamkiem (39068, V3 line 100000, 12 SM, "bonus_b67chest") - a few a day
//     (PLAYERBOT_BONUS67_CHEST_DAY), opened here at once (its colours are random: the right one 1-31 % by the chest's
//     weights; the rest is surplus). With shards in the bag and none to buy for PLAYERBOT_BONUS67_SHARD_WAIT_MS it adds
//     with what it holds (the chance at least PLAYERBOT_BONUS67_MIN_PCT). The surplus: a bag keeps ten of each band an
//     open add takes (GetPlayerBotBonus67ShardKeep, the visit's and the lada's keep - GetPlayerBotSeonHaeShardKeep);
//     the rest goes on the counters and the lada as before. A bot under the stage keeps none.
//  6. The lines (GetPlayerBotBonus67LineScore, units: Wartosc Ataku +35 = 100): the attack value (POINT_ATT_GRADE_BONUS,
//     the pool's 8/15/25/35/50) first on every slot; then by slot - the body: the needed element's resistance % and
//     Max HP, the boss defence; the necklace: the boss damage of the bot's fighting; the shield: the boss defence,
//     block; every slot: Max HP, the element's hit buffs, the "n-th bonus +x %" where that line exists. A Yohara-stage
//     bot (a Yohara member or a Champion) weighs the hunt element's resistance and Max HP higher; the attack value
//     stays the top line. A piece's score: its best line + half the other.
//  7. Mixing (71052 Blogoslawienstwo Przedmiotu, V3 100005, 129 SM - "bonus_b67mix"; a held Male Blogoslawienstwo
//     72351 first): ONLY a piece with both extra lines. A piece with one line takes the next add, before any other
//     piece, until it has two. The stopping rule: done at an attack value line of the target (m2_bot_bonus67_av_target,
//     35) or a score of PLAYERBOT_BONUS67_DONE_SCORE; after half the slot's mixes a score of PLAYERBOT_BONUS67_KEEP_SCORE
//     (an attack value +25 alone) is kept; never more than the slot's cap (PLAYERBOT_BONUS67_SLOTS, quest flags
//     playerbot.b67_mid_<wear> / playerbot.b67_mn_<wear>). One mix a look.
//  8. The SM: every purchase is a V3 goal through BuyPlayerBotIshop3Pieces - the account's daily pool, no new coins.
//
// Flags: m2_bot_bonus67_off (1: the pass, its goals and its keep off - the old Seon-Hae errand and the 71052 pass of
// shop aids come back), m2_bot_bonus67_mix_off (no mixing, no 71052 goal), m2_bot_bonus67_chest_off (no shard chest),
// m2_bot_bonus67_min_level (0: 75), m2_bot_bonus67_av_target (0: 35). m2_seonhae_on 0 stops it too.
// The log: PLAYERBOT_BONUS67 add / mix / chest (each), plan / wait / refused (throttled) and the census every 10 minutes
// (bots of the stage on this core, pieces in scope and their lines 0/1/2, adds tried / won, mixes, shards bought on the
// market / from chests, Suplementy used and bought, the SM spent, the average attack value of the 6/7 lines, the top
// lines).
//
// An implementation fragment: include it once, from playerbot_manager.cpp, right after playerbot_shop_aids.h; the
// declarations the earlier files ask are in playerbot_types.h.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_BONUS67_V1) && defined(MT2009_PLUS_BOT_USE_SHOP_AIDS_V1) && \
	defined(MT2009_PLUS_BOT_SEONHAE_V2)

namespace
{
	const char* const PLAYERBOT_BONUS67_OFF_FLAG = "m2_bot_bonus67_off";
	const char* const PLAYERBOT_BONUS67_MIX_OFF_FLAG = "m2_bot_bonus67_mix_off";
	const char* const PLAYERBOT_BONUS67_CHEST_OFF_FLAG = "m2_bot_bonus67_chest_off";
	const char* const PLAYERBOT_BONUS67_MIN_LEVEL_FLAG = "m2_bot_bonus67_min_level";
	const char* const PLAYERBOT_BONUS67_AV_TARGET_FLAG = "m2_bot_bonus67_av_target";
	const int PLAYERBOT_BONUS67_MIN_LEVEL = 75;
	const int PLAYERBOT_BONUS67_AV_TARGET = 35;
	const int PLAYERBOT_BONUS67_MIN_PCT = 20;
	const int PLAYERBOT_BONUS67_DONE_SCORE = 110;
	const int PLAYERBOT_BONUS67_KEEP_SCORE = 70;
	const int PLAYERBOT_BONUS67_JEWEL_LEVEL = 54;	// Niebianskie Lzy
	const int PLAYERBOT_BONUS67_BODY_LEVEL = 61;
	const int PLAYERBOT_BONUS67_HEAD_LEVEL = 41;	// and the shield
	const int PLAYERBOT_BONUS67_ADDITIVES_MAX = 5;
	const int PLAYERBOT_BONUS67_CHEST_DAY = 6;
	const int PLAYERBOT_BONUS67_CHEST_BATCH = 3;
	const int PLAYERBOT_BONUS67_KEEP_MAX = 20;
	const DWORD PLAYERBOT_BONUS67_LOOK_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_LOOK_MAX_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_ADDITIVE_WAIT_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_SHARD_WAIT_MS = 45 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_NO_SUPPLY_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_WANT_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_BONUS67_ADD_STONE = 71051;	// Magiczny Przedmiot - the engine's add, 100 %
	const DWORD PLAYERBOT_BONUS67_MIX_STONE = 71052;	// Blogoslawienstwo Przedmiotu
	const DWORD PLAYERBOT_BONUS67_SMALL_MIX_STONE = 72351;	// Male Blogoslawienstwo (the 71052 case, 10 %)
	const DWORD PLAYERBOT_BONUS67_STRONG_ADDITIVE = 72067;	// Silny Suplement
	const DWORD PLAYERBOT_BONUS67_SHARD_CHEST = 39068;	// Zdobna Skrz. z Odlamkiem
	const int PLAYERBOT_BONUS67_SHARD_PRICE_PCT = 400;	// a counter's shard: four times the sheet's price at most
	const int PLAYERBOT_BONUS67_SHARD_PURSE_PCT = 20;	// ... out of a fifth of what the bot can spare
	const char* const PLAYERBOT_BONUS67_GOAL_ADD = "bonus_b67add";
	const char* const PLAYERBOT_BONUS67_GOAL_MIX = "bonus_b67mix";
	const char* const PLAYERBOT_BONUS67_GOAL_CHEST = "bonus_b67chest";

	enum
	{
		B67_SCOPE_NONE = 0,
		B67_SCOPE_BODY,
		B67_SCOPE_HEAD,
		B67_SCOPE_SHIELD,
		B67_SCOPE_JEWEL,	// Niebianskie Lzy and higher
		B67_SCOPE_ELEMENT,	// jewellery or boots of the needed element
	};

	// The worn slots in the order a first line goes, with the mixes a piece may take there.
	struct TPlayerBotBonus67Slot
	{
		BYTE bWear;
		int iMixCap;
	};
	const TPlayerBotBonus67Slot PLAYERBOT_BONUS67_SLOTS[] = {
		{ WEAR_BODY, 10 },
		{ WEAR_NECK, 8 },
		{ WEAR_WRIST, 8 },
		{ WEAR_EAR, 8 },
		{ WEAR_HEAD, 6 },
		{ WEAR_SHIELD, 6 },
		{ WEAR_FOOTS, 5 },
	};
	const size_t PLAYERBOT_BONUS67_SLOT_COUNT = sizeof(PLAYERBOT_BONUS67_SLOTS) / sizeof(PLAYERBOT_BONUS67_SLOTS[0]);

	struct TPlayerBotBonus67
	{
		DWORD dwNextLook;
		DWORD dwPlanItem;		// the piece the open add is for (its id)
		DWORD dwPlanSince;		// when that add was first planned
		DWORD dwShardWant;		// the market's want: the shard and how many
		int iShardNeed;
		DWORD dwWantUntil;
		DWORD dwNoSupplySince;	// no counter has had the shard since (0: one has)
		TPlayerBotBonus67() : dwNextLook(0), dwPlanItem(0), dwPlanSince(0), dwShardWant(0), iShardNeed(0), dwWantUntil(0),
			dwNoSupplySince(0) {}
	};
	std::map<DWORD, TPlayerBotBonus67> s_mapPlayerBotBonus67;

	struct TPlayerBotBonus67Stats
	{
		unsigned int looks, addsTried, addsWon, adds71051, addsNoShard, addsWaitShard, addsWaitAdditive, refused;
		unsigned int mixes, mixesTop, mixesDone, mixesGiveUp, mixesNoStone;
		unsigned int shardsMarket, shardsChest, shardsChestOther, chestsOpened;
		unsigned int additivesUsed[4];
		long long shardsMarketYang;
		TPlayerBotBonus67Stats() { memset(this, 0, sizeof(*this)); }
	};
	TPlayerBotBonus67Stats s_kPlayerBotBonus67Stats;
	DWORD s_dwPlayerBotBonus67CensusAt = 0;

	int GetPlayerBotBonus67Flag(const char* flag)
	{
		return quest::CQuestManager::instance().GetEventFlag(flag);
	}

	bool IsPlayerBotBonus67On()
	{
		return GetPlayerBotBonus67Flag(PLAYERBOT_BONUS67_OFF_FLAG) == 0 && mt2009_seonhae::IsOn();
	}

	int GetPlayerBotBonus67MinLevel()
	{
		const int v = GetPlayerBotBonus67Flag(PLAYERBOT_BONUS67_MIN_LEVEL_FLAG);
		return v > 0 ? v : PLAYERBOT_BONUS67_MIN_LEVEL;
	}

	int GetPlayerBotBonus67AvTarget()
	{
		const int v = GetPlayerBotBonus67Flag(PLAYERBOT_BONUS67_AV_TARGET_FLAG);
		return v > 0 ? v : PLAYERBOT_BONUS67_AV_TARGET;
	}

	// A bot of the stage: its level, no companion, gear not frozen.
	bool IsPlayerBotBonus67Stage(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->IsItemLoaded() && ch->GetLevel() >= GetPlayerBotBonus67MinLevel() &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID()) && !IsPlayerBotGearFrozen(ch);
	}

	// The item level: the highest level limit (MT2009_PLUS_SEONHAE_LEVEL_FIX_V1's reading).
	int GetPlayerBotBonus67ItemLevel(LPITEM item)
	{
		int level = 0;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (item->GetLimitType(i) == LIMIT_LEVEL)
				level = std::max(level, (int)item->GetLimitValue(i));
		return level;
	}

	// The element the bot needs now (0 lightning, 1 fire, 2 ice, 3 wind, 4 earth, 5 dark), -1 none.
	int GetPlayerBotBonus67Element(LPCHARACTER ch)
	{
		const int hunt = GetPlayerBotHuntElementIndex(ch);
		if (hunt >= 0 && hunt < 6)
			return hunt;
		TPlayerBotElementMapView v;
		if (GetPlayerBotElementMapGoal(ch, v) && v.iElement >= 0 && v.iElement < 6)
			return v.iElement;
		return -1;
	}

	// The piece carries the element's resistance: in its proto or on one of its five lines.
	bool HasPlayerBotBonus67Resist(LPITEM item, int element)
	{
		if (!item || element < 0 || element >= 6)
			return false;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[element];
		if (item->GetProto())
			for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
				if (item->GetProto()->aApplies[i].bType == point && item->GetProto()->aApplies[i].lValue > 0)
					return true;
		for (int i = 0; i < ITEM_ATTRIBUTE_NORM_NUM; ++i)
			if (item->GetAttributeType(i) == point && item->GetAttributeValue(i) > 0)
				return true;
		return false;
	}

	// Rule 2: the scope of a worn piece (B67_SCOPE_NONE: not one of the owner's pieces, or one the engine refuses).
	int GetPlayerBotBonus67Scope(LPCHARACTER ch, LPITEM item, int element)
	{
		if (!item || item->GetType() != ITEM_ARMOR || item->GetAttributeSetIndex() < 0 || item->GetCount() != 1 ||
				IS_SET(item->GetFlag(), ITEM_FLAG_UNIQUE) || IsPlayerBotSidekickPinned(ch, item))
			return B67_SCOPE_NONE;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE t = item->GetLimitType(i);
			if (t == LIMIT_REAL_TIME || t == LIMIT_REAL_TIME_START_FIRST_USE || t == LIMIT_TIMER_BASED_ON_WEAR)
				return B67_SCOPE_NONE;
		}
		BYTE bReserved = 0;
		if (Mt2009WillTalismanType(item->GetVnum(), bReserved) || Mt2009GloveType(item->GetVnum(), bReserved))
			return B67_SCOPE_NONE;
		// MT2009_PLUS_JADE_BONUS67_V1: a Jade piece is jewellery of item level 105 like any other - an old one's base
		// line still in its 6th/7th slot leaves it before anything counts the extra bonuses (idempotent, the engine's
		// AddRareAttribute / ChangeRareAttribute and Seon-Hae do the same)
		if (Mt2009JadeBraceletType(item->GetVnum(), bReserved))
			Mt2009JadeBaseMigrate(item);
		const int level = GetPlayerBotBonus67ItemLevel(item);
		switch (item->GetSubType())
		{
			case ARMOR_BODY:
				return level >= PLAYERBOT_BONUS67_BODY_LEVEL ? B67_SCOPE_BODY : B67_SCOPE_NONE;
			case ARMOR_HEAD:
				return level >= PLAYERBOT_BONUS67_HEAD_LEVEL ? B67_SCOPE_HEAD : B67_SCOPE_NONE;
			case ARMOR_SHIELD:
				return level >= PLAYERBOT_BONUS67_HEAD_LEVEL ? B67_SCOPE_SHIELD : B67_SCOPE_NONE;
			case ARMOR_WRIST:
			case ARMOR_NECK:
			case ARMOR_EAR:
				if (level >= PLAYERBOT_BONUS67_JEWEL_LEVEL)
					return B67_SCOPE_JEWEL;
				return HasPlayerBotBonus67Resist(item, element) ? B67_SCOPE_ELEMENT : B67_SCOPE_NONE;
			case ARMOR_FOOTS:
				return HasPlayerBotBonus67Resist(item, element) ? B67_SCOPE_ELEMENT : B67_SCOPE_NONE;
			default:
				return B67_SCOPE_NONE;
		}
	}

	// The core's own conditions of an add (mt2009_seonhae::CheckItem, the piece still worn): five lines, fewer than two
	// extra, the pool's room.
	bool CanPlayerBotBonus67Add(LPITEM item)
	{
		return item && !item->isLocked() && !item->IsExchanging() && item->GetAttributeCount() >= ITEM_ATTRIBUTE_NORM_NUM &&
				item->GetRareAttrCount() < ITEM_ATTRIBUTE_RARE_NUM && mt2009_seonhae::RarePoolHasRoom(item);
	}

	// ------------------------------------------------------------------------------------------------ the lines' worth

	struct TPlayerBotBonus67Need
	{
		int iElement;
		bool bYohara;
		bool bCaster;
	};

	void ReadPlayerBotBonus67Need(LPCHARACTER ch, TPlayerBotBonus67Need& n)
	{
		n.iElement = GetPlayerBotBonus67Element(ch);
		n.bYohara = IsPlayerBotYoharaBonusMember(ch) || GetPlayerBotChampionLevel(ch) > 0;
		n.bCaster = IsPlayerBotCaster(ch);
	}

	// Rule 6: one 6th/7th line's worth on its piece (Wartosc Ataku +35 = 100).
	int GetPlayerBotBonus67LineScore(LPITEM item, WORD type, int value, const TPlayerBotBonus67Need& n) // MT2009_PLUS_WIDE_ATTR_V1
	{
		if (!type || value <= 0)
			return 0;
		if (type == POINT_ATT_GRADE_BONUS)
			return value * 100 / 35;
		if (type == POINT_MAGIC_ATT_GRADE_BONUS)
			return value * (n.bCaster ? 80 : 15) / 35;
		if (type == POINT_MAX_HP)
			return value * (n.bYohara ? 75 : 55) / 400;
		const int e = n.iElement;
		if (e >= 0 && type == PLAYERBOT_RARE67_RESIST_PER[e])
			return value * (n.bYohara ? 85 : 60) / 7;
		if (e >= 0 && type == PLAYERBOT_RARE67_HIT_RESIST[e])
			return value * 40 / 4;
		if (e >= 0 && type == PLAYERBOT_RARE67_HIT_ENCHANT[e])
			return value * 30 / 4;
		const WORD classBoss = n.bCaster ? POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE : POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE;
		if (type == classBoss)
			return value * 50 / 4;
		if (type == POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE || type == POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE)
			return value * 25 / 4;
		if (type == POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE || type == POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE)
			return value * 35 / 4;
		if (type == POINT_ATTBONUS_STONE)
			return value * 25 / 7;
		if (type >= POINT_FIRST_ATTRIBUTE_BONUS && type <= POINT_FIFTH_ATTRIBUTE_BONUS &&
				item->GetAttributeType(type - POINT_FIRST_ATTRIBUTE_BONUS) != 0)
			return value * 35 / 20;
		if (type == POINT_BLOCK)
			return value * 20 / 4;
		if (type == POINT_RESIST_PER_MAGIC)
			return value * 25 / 10;
		if (type == POINT_POISON_REDUCE)
			return value * 8 / 4;
		return 5;
	}

	// A piece's score (its best line + half the other) and its best attack value line.
	int GetPlayerBotBonus67ItemScore(LPITEM item, const TPlayerBotBonus67Need& n, int* bestAv = NULL)
	{
		int best = 0, other = 0, av = 0;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		{
			const WORD type = item->GetAttributeType(i); // MT2009_PLUS_WIDE_ATTR_V1
			const int value = item->GetAttributeValue(i);
			if (type == POINT_ATT_GRADE_BONUS)
				av = std::max(av, value);
			const int s = GetPlayerBotBonus67LineScore(item, type, value, n);
			if (s > best)
			{
				other = best;
				best = s;
			}
			else
				other = std::max(other, s);
		}
		if (bestAv)
			*bestAv = av;
		return best + other / 2;
	}

	void FormatPlayerBotBonus67Lines(LPITEM item, char* buf, size_t size)
	{
		int len = 0;
		buf[0] = 0;
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END && len >= 0 && len < (int)size - 16; ++i)
			len += snprintf(buf + len, size - len, "%s%u:%d", i == ITEM_ATTRIBUTE_RARE_START ? "" : ",",
					(unsigned int)item->GetAttributeType(i), (int)item->GetAttributeValue(i));
	}

	// ------------------------------------------------------------------------------------------------ the mixes' count

	void GetPlayerBotBonus67MixFlags(BYTE wear, char* idFlag, char* nFlag, size_t size)
	{
		snprintf(idFlag, size, "playerbot.b67_mid_%u", (unsigned int)wear);
		snprintf(nFlag, size, "playerbot.b67_mn_%u", (unsigned int)wear);
	}

	int GetPlayerBotBonus67Mixes(LPCHARACTER ch, BYTE wear, LPITEM item)
	{
		char idFlag[48], nFlag[48];
		GetPlayerBotBonus67MixFlags(wear, idFlag, nFlag, sizeof(idFlag));
		return (DWORD)ch->GetQuestFlag(idFlag) == item->GetID() ? ch->GetQuestFlag(nFlag) : 0;
	}

	// Rule 7's stopping rule: 0 mix on, 1 done (target / score), 2 kept (half the cap and a good score), 3 the cap.
	int GetPlayerBotBonus67MixVerdict(LPCHARACTER ch, BYTE wear, int cap, LPITEM item, const TPlayerBotBonus67Need& n)
	{
		int av = 0;
		const int score = GetPlayerBotBonus67ItemScore(item, n, &av);
		if (av >= GetPlayerBotBonus67AvTarget() || score >= PLAYERBOT_BONUS67_DONE_SCORE)
			return 1;
		const int mixes = GetPlayerBotBonus67Mixes(ch, wear, item);
		if (mixes * 2 >= cap && score >= PLAYERBOT_BONUS67_KEEP_SCORE)
			return 2;
		return mixes >= cap ? 3 : 0;
	}

	// The worn piece the mix pass would roll now (both extra lines, not done), NULL none.
	LPITEM GetPlayerBotBonus67MixTarget(LPCHARACTER ch, BYTE* wearOut, int* capOut)
	{
		if (!IsPlayerBotBonus67On() || GetPlayerBotBonus67Flag(PLAYERBOT_BONUS67_MIX_OFF_FLAG) != 0 || !IsPlayerBotBonus67Stage(ch))
			return NULL;
		TPlayerBotBonus67Need n;
		ReadPlayerBotBonus67Need(ch, n);
		for (size_t i = 0; i < PLAYERBOT_BONUS67_SLOT_COUNT; ++i)
		{
			const BYTE wear = PLAYERBOT_BONUS67_SLOTS[i].bWear;
			LPITEM item = ch->GetWear(wear);
			if (!item || GetPlayerBotBonus67Scope(ch, item, n.iElement) == B67_SCOPE_NONE ||
					item->GetRareAttrCount() < ITEM_ATTRIBUTE_RARE_NUM || item->isLocked() || item->IsExchanging())
				continue;
			if (GetPlayerBotBonus67MixVerdict(ch, wear, PLAYERBOT_BONUS67_SLOTS[i].iMixCap, item, n) != 0)
				continue;
			if (wearOut)
				*wearOut = wear;
			if (capOut)
				*capOut = PLAYERBOT_BONUS67_SLOTS[i].iMixCap;
			return item;
		}
		return NULL;
	}

	// ------------------------------------------------------------------------------------------------ the add's piece

	// Rule 7: the piece the next add goes to - one with a single extra line first (always that one), else the slots'
	// order. NULL: none.
	LPITEM GetPlayerBotBonus67AddTarget(LPCHARACTER ch, int element, BYTE* wearOut)
	{
		LPITEM firstEmpty = NULL;
		BYTE emptyWear = 0;
		for (size_t i = 0; i < PLAYERBOT_BONUS67_SLOT_COUNT; ++i)
		{
			const BYTE wear = PLAYERBOT_BONUS67_SLOTS[i].bWear;
			LPITEM item = ch->GetWear(wear);
			if (!item || GetPlayerBotBonus67Scope(ch, item, element) == B67_SCOPE_NONE || !CanPlayerBotBonus67Add(item))
				continue;
			if (item->GetRareAttrCount() == 1)
			{
				if (wearOut)
					*wearOut = wear;
				return item;
			}
			if (!firstEmpty)
			{
				firstEmpty = item;
				emptyWear = wear;
			}
		}
		if (firstEmpty && wearOut)
			*wearOut = emptyWear;
		return firstEmpty;
	}

	// The shards a bag keeps: ten of each band an open add of a worn piece of the scope takes (two pieces of one band:
	// twenty at most); a bot under the stage keeps none (they go on the counters and the lada).
	int GetPlayerBotBonus67ShardKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!IsPlayerBotBonus67Stage(ch))
			return 0;
		const int element = GetPlayerBotBonus67Element(ch);
		int keep = 0;
		for (size_t i = 0; i < PLAYERBOT_BONUS67_SLOT_COUNT; ++i)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_BONUS67_SLOTS[i].bWear);
			if (item && GetPlayerBotBonus67Scope(ch, item, element) != B67_SCOPE_NONE && CanPlayerBotBonus67Add(item) &&
					mt2009_seonhae::MaterialVnum(item) == vnum)
				keep += mt2009_seonhae::MATERIAL_MAX;
		}
		return std::min(keep, PLAYERBOT_BONUS67_KEEP_MAX);
	}

	// ------------------------------------------------------------------------------------------------ the market

	// The counters' want (the look writes it): this shard, this many at most.
	bool WantsPlayerBotBonus67ShardOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || !mt2009_seonhae::IsShardVnum(offer->GetVnum()) || !IsPlayerBotBonus67On())
			return false;
		std::map<DWORD, TPlayerBotBonus67>::const_iterator it = s_mapPlayerBotBonus67.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotBonus67.end() || !it->second.dwShardWant || it->second.dwShardWant != offer->GetVnum() ||
				(int)(get_dword_time() - it->second.dwWantUntil) >= 0)
			return false;
		// what the add still lacks now (a purchase since the look counted)
		const int need = (int)mt2009_seonhae::MATERIAL_MAX - (int)ch->CountSpecifyItem(offer->GetVnum());
		return need > 0 && (int)offer->GetCount() <= need;
	}

	DWORD GetPlayerBotBonus67ShardWantVnum(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotBonus67On())
			return 0;
		std::map<DWORD, TPlayerBotBonus67>::const_iterator it = s_mapPlayerBotBonus67.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotBonus67.end() || (int)(get_dword_time() - it->second.dwWantUntil) >= 0)
			return 0;
		return it->second.iShardNeed > 0 ? it->second.dwShardWant : 0;
	}

	// A trip to the counters is worth it: the want is open and the ledger says a counter holds the shard.
	bool WantsPlayerBotBonus67ShardsFromMarket(LPCHARACTER ch)
	{
		const DWORD vnum = GetPlayerBotBonus67ShardWantVnum(ch);
		if (!vnum)
			return false;
		const TPlayerBotMarketLedgerEntry* supply = GetPlayerBotMarketLedgerEntry(vnum);
		return supply && supply->dwSupplyUnits > 0;
	}

	// The price: up to PLAYERBOT_BONUS67_SHARD_PRICE_PCT of the sheet's a piece, out of a share of the spare yang.
	bool CanPlayerBotPayForBonus67Shard(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long count = std::max<long long>(1, (long long)item->GetCount());
		const long long fair = GetPlayerBotSeonHaeShardYang(item->GetVnum()) * count;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return price * 100 <= fair * PLAYERBOT_BONUS67_SHARD_PRICE_PCT && price <= spare * PLAYERBOT_BONUS67_SHARD_PURSE_PCT / 100;
	}

	void NotePlayerBotBonus67ShardBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!ch || !mt2009_seonhae::IsShardVnum(vnum) || GetPlayerBotBonus67ShardWantVnum(ch) != vnum)
			return;
		s_kPlayerBotBonus67Stats.shardsMarket += count;
		s_kPlayerBotBonus67Stats.shardsMarketYang += price;
		sys_log(0, "PLAYERBOT_BONUS67: shards bought pid=%u name=%s vnum=%u count=%u price=%lld have=%d source=market",
				ch->GetPlayerID(), ch->GetName(), vnum, (unsigned int)count, price, (int)ch->CountSpecifyItem(vnum));
	}

	// ------------------------------------------------------------------------------------------------ the V3 goals

	// The Silne the open add still lacks and the coins pay for today (0: none to buy).
	int GetPlayerBotBonus67AdditiveBuy(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		const int held = (int)ch->CountSpecifyItem(PLAYERBOT_BONUS67_STRONG_ADDITIVE);
		const int missing = PLAYERBOT_BONUS67_ADDITIVES_MAX - held;
		if (missing <= 0)
			return 0;
		const long long unit = GetPlayerBotShopAidUnitCoins(ch, PLAYERBOT_BONUS67_STRONG_ADDITIVE);
		if (unit <= 0)
			return 0;
		long long coins = std::max(0, state.iDragonCoins);
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		coins = std::min(coins, std::max(0LL, GetPlayerBotSmPoolRoom(ch, state, PLAYERBOT_BONUS67_GOAL_ADD).Room()));
#endif
		return (int)std::min<long long>(missing, coins / unit);
	}

	// The chests the day still allows (the V3 purchases' own day count).
	int GetPlayerBotBonus67ChestsLeft(LPCHARACTER ch)
	{
		return std::max(0, PLAYERBOT_BONUS67_CHEST_DAY - GetPlayerBotIshop3BoughtToday(ch->GetPlayerID(), PLAYERBOT_BONUS67_SHARD_CHEST));
	}

	// Asked by CollectPlayerBotShopAidGoals (playerbot_shop_aids.h).
	void CollectPlayerBotBonus67Goals(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotIshop3Goal* goals, int& n)
	{
		if (!ch || !IsPlayerBotBonus67On() || !IsPlayerBotBonus67Stage(ch))
			return;
		std::map<DWORD, TPlayerBotBonus67>::const_iterator s = s_mapPlayerBotBonus67.find(ch->GetPlayerID());
		const bool planned = s != s_mapPlayerBotBonus67.end() && s->second.dwPlanItem != 0;
		// the add's Silne (rule 3)
		if (planned && n < PLAYERBOT_ISHOP3_MAX_GOALS)
		{
			const int buy = GetPlayerBotBonus67AdditiveBuy(ch, state);
			if (buy > 0)
			{
				const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS67_STRONG_ADDITIVE, false, buy, PLAYERBOT_BONUS67_GOAL_ADD };
				goals[n++] = g;
			}
		}
		// the shard chest, the last resort (rule 4): no counter has had the shard for a while and the bag holds too few
		if (planned && n < PLAYERBOT_ISHOP3_MAX_GOALS && GetPlayerBotBonus67Flag(PLAYERBOT_BONUS67_CHEST_OFF_FLAG) == 0 &&
				s->second.dwShardWant && s->second.iShardNeed > 0 && s->second.dwNoSupplySince != 0 &&
				get_dword_time() - s->second.dwNoSupplySince >= PLAYERBOT_BONUS67_NO_SUPPLY_MS &&
				ch->CountSpecifyItem(PLAYERBOT_BONUS67_SHARD_CHEST) == 0)
		{
			const int left = GetPlayerBotBonus67ChestsLeft(ch);
			if (left > 0)
			{
				const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS67_SHARD_CHEST, false, std::min(left, PLAYERBOT_BONUS67_CHEST_BATCH),
					PLAYERBOT_BONUS67_GOAL_CHEST };
				goals[n++] = g;
			}
		}
		// the mix (rule 7)
		if (n < PLAYERBOT_ISHOP3_MAX_GOALS && ch->CountSpecifyItem(PLAYERBOT_BONUS67_MIX_STONE) == 0 &&
				ch->CountSpecifyItem(PLAYERBOT_BONUS67_SMALL_MIX_STONE) == 0 && GetPlayerBotBonus67MixTarget(ch, NULL, NULL))
		{
			const TPlayerBotIshop3Goal g = { PLAYERBOT_BONUS67_MIX_STONE, false, 1, PLAYERBOT_BONUS67_GOAL_MIX };
			goals[n++] = g;
		}
	}

	// ------------------------------------------------------------------------------------------------ the actions

	// The chests bought for the last resort, opened here (the chest pass would too - here the census sees them).
	void OpenPlayerBotBonus67Chests(LPCHARACTER ch, DWORD wanted)
	{
		for (int tries = 0; tries < PLAYERBOT_BONUS67_CHEST_BATCH; ++tries)
		{
			LPITEM chest = FindPlayerBotShopAidBagItem(ch, PLAYERBOT_BONUS67_SHARD_CHEST);
			if (!chest || ch->GetEmptyInventory(1) < 0)
				return;
			const int before = wanted ? (int)ch->CountSpecifyItem(wanted) : 0;
			const int chestsBefore = (int)ch->CountSpecifyItem(PLAYERBOT_BONUS67_SHARD_CHEST);
			if (!ch->UseItem(TItemPos(INVENTORY, chest->GetCell())) ||
					(int)ch->CountSpecifyItem(PLAYERBOT_BONUS67_SHARD_CHEST) >= chestsBefore)
				return;
			const int got = wanted ? (int)ch->CountSpecifyItem(wanted) - before : 0;
			++s_kPlayerBotBonus67Stats.chestsOpened;
			if (got > 0)
				s_kPlayerBotBonus67Stats.shardsChest += got;
			else
				++s_kPlayerBotBonus67Stats.shardsChestOther;
			sys_log(0, "PLAYERBOT_BONUS67: chest pid=%u name=%s wanted=%u got=%d have=%d", ch->GetPlayerID(), ch->GetName(),
					wanted, got, wanted ? (int)ch->CountSpecifyItem(wanted) : 0);
		}
	}

	// Rule 3: the add, at once - off the body, the shards and the Suplementy out, the roll, the line, on again.
	bool AddPlayerBotBonus67(LPCHARACTER ch, TPlayerBotAIState& state, LPITEM item, BYTE wear, DWORD dwNow)
	{
		const DWORD vnum = item->GetVnum();
		const int rareBefore = item->GetRareAttrCount();
		if (ch->GetEmptyInventory(item->GetSize()) < 0)
		{
			PlayerBotLogThrottled("b67_no_room", dwNow, "PLAYERBOT_BONUS67: no room pid=%u name=%s vnum=%u", ch->GetPlayerID(),
					ch->GetName(), vnum);
			return false;
		}
		// a Magiczny Przedmiot held: the engine's own add (100 %)
		LPITEM magic = ch->CountSpecifyItem(PLAYERBOT_BONUS67_ADD_STONE) > 0 ? FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_BONUS67_ADD_STONE) : NULL;
		const DWORD shard = mt2009_seonhae::MaterialVnum(item);
		const int shards = std::min((int)ch->CountSpecifyItem(shard), (int)mt2009_seonhae::MATERIAL_MAX);
		int grade = -1, additives = 0, pct = 0;
		if (!magic)
		{
			if (shards < 1)
				return false;
			// the kind of the best chance among the held ones (one kind an add, at most five)
			for (int g = 0; g < 4; ++g)
			{
				const DWORD a = PLAYERBOT_SEONHAE_ADDITIVES[g];
				const int held = std::min((int)ch->CountSpecifyItem(a), PLAYERBOT_BONUS67_ADDITIVES_MAX);
				if (held > 0 && mt2009_seonhae::ChancePct(shards, mt2009_seonhae::SupportPct(a), held) >
						mt2009_seonhae::ChancePct(shards, grade >= 0 ? mt2009_seonhae::SupportPct(PLAYERBOT_SEONHAE_ADDITIVES[grade]) : 0, additives))
				{
					grade = g;
					additives = held;
				}
			}
			pct = mt2009_seonhae::ChancePct(shards, grade >= 0 ? mt2009_seonhae::SupportPct(PLAYERBOT_SEONHAE_ADDITIVES[grade]) : 0,
					additives);
			if (pct < PLAYERBOT_BONUS67_MIN_PCT)
				return false;
		}
		if (!ch->UnequipItem(item) || item->IsEquipped())
		{
			PlayerBotLogThrottled("b67_unequip", dwNow, "PLAYERBOT_BONUS67: cannot take off pid=%u name=%s vnum=%u",
					ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		++s_kPlayerBotBonus67Stats.addsTried;
		bool won = false;
		const char* how = "seonhae";
		if (magic)
		{
			how = "71051";
			pct = 100;
			ch->UseItemEx(magic, TItemPos(INVENTORY, item->GetCell()));
			won = item->GetRareAttrCount() > rareBefore;
			if (won)
				++s_kPlayerBotBonus67Stats.adds71051;
		}
		else
		{
			// everything spent whatever the roll (the core's Add)
			ch->RemoveSpecifyItem(shard, (ITEM_COUNT)shards);
			if (grade >= 0 && additives > 0)
			{
				ch->RemoveSpecifyItem(PLAYERBOT_SEONHAE_ADDITIVES[grade], (ITEM_COUNT)additives);
				s_kPlayerBotBonus67Stats.additivesUsed[grade] += additives;
			}
			if (number(1, 100) <= pct)
			{
				item->AddRareAttribute();	// the level by the panel's m2_rare_lv1..5, as Seon-Hae's collect
				won = item->GetRareAttrCount() > rareBefore;
				if (!won)
					sys_err("PLAYERBOT_BONUS67: %s won %u but no extra bonus could be put on it", ch->GetName(), vnum);
			}
			char hint[96];
			snprintf(hint, sizeof(hint), "%u shards %u x%d additive %u x%d pct %d %s", vnum, shard, shards,
					grade >= 0 ? PLAYERBOT_SEONHAE_ADDITIVES[grade] : 0, additives, pct, won ? "OK" : "FAIL");
			LogManager::instance().ItemLog(ch, item, "SEONHAE_BOT_ADD", hint);
		}
		item->UpdatePacket();
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		PlayerBotEquipItem(ch, item);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if (won)
			++s_kPlayerBotBonus67Stats.addsWon;
		char lines[96];
		FormatPlayerBotBonus67Lines(item, lines, sizeof(lines));
		sys_log(0, "PLAYERBOT_BONUS67: add pid=%u name=%s lv=%d champion=%d wear=%u vnum=%u item_lv=%d how=%s shard=%u x%d "
				"additive=%u x%d pct=%d result=%s extra=%d->%d lines=[%s] coins=%d", ch->GetPlayerID(), ch->GetName(),
				ch->GetLevel(), GetPlayerBotChampionLevel(ch), (unsigned int)wear, vnum, GetPlayerBotBonus67ItemLevel(item), how,
				magic ? 0 : shard, magic ? 0 : shards, grade >= 0 ? PLAYERBOT_SEONHAE_ADDITIVES[grade] : 0, additives, pct,
				won ? "ADDED" : "NONE", rareBefore, item->GetRareAttrCount(), lines, state.iDragonCoins);
		return true;
	}

	// Rule 7: one mix of a piece with both lines (off the body and on again, as the engine wants it).
	bool MixPlayerBotBonus67(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		BYTE wear = 0;
		int cap = 0;
		LPITEM item = GetPlayerBotBonus67MixTarget(ch, &wear, &cap);
		if (!item)
			return false;
		LPITEM stone = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_BONUS67_SMALL_MIX_STONE);
		if (!stone)
			stone = FetchPlayerBotShopAidBagItem(ch, PLAYERBOT_BONUS67_MIX_STONE);
		if (!stone)
		{
			++s_kPlayerBotBonus67Stats.mixesNoStone;
			return false;
		}
		if (ch->GetEmptyInventory(item->GetSize()) < 0 || !ch->UnequipItem(item) || item->IsEquipped())
			return false;
		const DWORD stoneVnum = stone->GetVnum();
		char before[96], after[96], idFlag[48], nFlag[48];
		FormatPlayerBotBonus67Lines(item, before, sizeof(before));
		GetPlayerBotBonus67MixFlags(wear, idFlag, nFlag, sizeof(idFlag));
		const DWORD itemId = item->GetID();
		const int stonesBefore = (int)ch->CountSpecifyItem(stoneVnum);
		ch->UseItemEx(stone, TItemPos(INVENTORY, item->GetCell()));
		FormatPlayerBotBonus67Lines(item, after, sizeof(after));
		PlayerBotEquipItem(ch, item);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if ((DWORD)ch->GetQuestFlag(idFlag) != itemId)
		{
			ch->SetQuestFlag(idFlag, (int)itemId);
			ch->SetQuestFlag(nFlag, 0);
		}
		const bool spent = (int)ch->CountSpecifyItem(stoneVnum) < stonesBefore;
		if (!spent)
		{
			// the engine refused it: no second try on this piece
			ch->SetQuestFlag(nFlag, cap);
			++s_kPlayerBotBonus67Stats.refused;
			PlayerBotLogThrottled("b67_mix_refused", dwNow, "PLAYERBOT_BONUS67: mix refused pid=%u name=%s wear=%u vnum=%u lines=[%s]",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)wear, item->GetVnum(), before);
			return false;
		}
		const int mixes = ch->GetQuestFlag(nFlag) + 1;
		ch->SetQuestFlag(nFlag, mixes);
		++s_kPlayerBotBonus67Stats.mixes;
		TPlayerBotBonus67Need n;
		ReadPlayerBotBonus67Need(ch, n);
		int av = 0;
		const int score = GetPlayerBotBonus67ItemScore(item, n, &av);
		const int verdict = GetPlayerBotBonus67MixVerdict(ch, wear, cap, item, n);
		const char* word = "AGAIN";
		if (verdict == 1)
		{
			word = av >= GetPlayerBotBonus67AvTarget() ? "TOP" : "DONE";
			++(av >= GetPlayerBotBonus67AvTarget() ? s_kPlayerBotBonus67Stats.mixesTop : s_kPlayerBotBonus67Stats.mixesDone);
		}
		else if (verdict == 2)
		{
			word = "KEPT";
			++s_kPlayerBotBonus67Stats.mixesDone;
		}
		else if (verdict == 3)
		{
			word = "GIVE_UP";
			++s_kPlayerBotBonus67Stats.mixesGiveUp;
		}
		sys_log(0, "PLAYERBOT_BONUS67: mix pid=%u name=%s lv=%d champion=%d wear=%u vnum=%u stone=%u lines=[%s]->[%s] av=%d "
				"score=%d mixes=%d/%d %s coins=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotChampionLevel(ch),
				(unsigned int)wear, item->GetVnum(), stoneVnum, before, after, av, score, mixes, cap, word, state.iDragonCoins);
		return true;
	}

	// ------------------------------------------------------------------------------------------------ the census

	void LogPlayerBotBonus67Census(DWORD dwNow)
	{
		if (s_dwPlayerBotBonus67CensusAt != 0 && (int)(dwNow - s_dwPlayerBotBonus67CensusAt) < 0)
			return;
		const bool first = s_dwPlayerBotBonus67CensusAt == 0;
		s_dwPlayerBotBonus67CensusAt = dwNow + PLAYERBOT_BONUS67_CENSUS_MS;
		if (first)
			return;
		unsigned int bots = 0, botsWith = 0, pieces = 0, lines0 = 0, lines1 = 0, lines2 = 0, notFive = 0, avLines = 0, top = 0;
		long long avSum = 0;
		unsigned int scope[6] = { 0, 0, 0, 0, 0, 0 };
		std::map<WORD, unsigned int> kinds;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !IsPlayerBotBonus67Stage(ch))
				continue;
			++bots;
			const int element = GetPlayerBotBonus67Element(ch);
			bool any = false;
			for (size_t i = 0; i < PLAYERBOT_BONUS67_SLOT_COUNT; ++i)
			{
				LPITEM item = ch->GetWear(PLAYERBOT_BONUS67_SLOTS[i].bWear);
				const int sc = item ? GetPlayerBotBonus67Scope(ch, item, element) : B67_SCOPE_NONE;
				if (sc == B67_SCOPE_NONE)
					continue;
				any = true;
				++pieces;
				++scope[sc];
				const int rare = item->GetRareAttrCount();
				if (rare <= 0)
					++(item->GetAttributeCount() < ITEM_ATTRIBUTE_NORM_NUM ? notFive : lines0);
				else if (rare == 1)
					++lines1;
				else
					++lines2;
				for (int a = ITEM_ATTRIBUTE_RARE_START; a < ITEM_ATTRIBUTE_RARE_END; ++a)
				{
					const WORD type = item->GetAttributeType(a);
					if (!type)
						continue;
					++kinds[type];
					if (type == POINT_ATT_GRADE_BONUS)
					{
						++avLines;
						avSum += item->GetAttributeValue(a);
						if (item->GetAttributeValue(a) >= GetPlayerBotBonus67AvTarget())
							++top;
					}
				}
			}
			if (any)
				++botsWith;
		}
		// the top lines
		std::vector<std::pair<unsigned int, WORD> > order;
		for (std::map<WORD, unsigned int>::const_iterator it = kinds.begin(); it != kinds.end(); ++it)
			order.push_back(std::make_pair(it->second, it->first));
		std::sort(order.rbegin(), order.rend());
		char topLines[160] = "";
		int len = 0;
		for (size_t i = 0; i < order.size() && i < 8 && len >= 0 && len < (int)sizeof(topLines) - 16; ++i)
			len += snprintf(topLines + len, sizeof(topLines) - len, "%s%u:%u", i ? "," : "", (unsigned int)order[i].second,
					order[i].first);
		const TPlayerBotBonus67Stats& t = s_kPlayerBotBonus67Stats;
		const TPlayerBotIshop3Census& cAdd = GetPlayerBotIshop3Census(PLAYERBOT_BONUS67_GOAL_ADD);
		const TPlayerBotIshop3Census& cMix = GetPlayerBotIshop3Census(PLAYERBOT_BONUS67_GOAL_MIX);
		const TPlayerBotIshop3Census& cChest = GetPlayerBotIshop3Census(PLAYERBOT_BONUS67_GOAL_CHEST);
		sys_log(0, "PLAYERBOT_BONUS67: census on=%d min_lv=%d av_target=%d bots=%u with_scope=%u pieces=%u (body=%u head=%u "
				"shield=%u jewel=%u element=%u) lines0=%u lines1=%u lines2=%u under_five=%u looks=%u adds=%u won=%u by71051=%u "
				"no_shard=%u wait_shard=%u wait_additive=%u mixes=%u top=%u done=%u give_up=%u no_stone=%u refused=%u",
				IsPlayerBotBonus67On() ? 1 : 0, GetPlayerBotBonus67MinLevel(), GetPlayerBotBonus67AvTarget(), bots, botsWith,
				pieces, scope[B67_SCOPE_BODY], scope[B67_SCOPE_HEAD], scope[B67_SCOPE_SHIELD], scope[B67_SCOPE_JEWEL],
				scope[B67_SCOPE_ELEMENT], lines0, lines1, lines2, notFive, t.looks, t.addsTried, t.addsWon, t.adds71051,
				t.addsNoShard, t.addsWaitShard, t.addsWaitAdditive, t.mixes, t.mixesTop, t.mixesDone, t.mixesGiveUp,
				t.mixesNoStone, t.refused);
		sys_log(0, "PLAYERBOT_BONUS67: census shards_market=%u (%lld yang) chests=%u (bought %u, %lld SM) shards_chest=%u "
				"chest_other=%u additives_used=%u/%u/%u/%u silne_bought=%u (%lld SM) mix_stones_bought=%u (%lld SM) sm_total=%lld "
				"av_lines=%u av_avg=%.1f av_top=%u top_lines=[%s]", t.shardsMarket, t.shardsMarketYang, t.chestsOpened,
				cChest.uPieces, cChest.llCoins, t.shardsChest, t.shardsChestOther, t.additivesUsed[0], t.additivesUsed[1],
				t.additivesUsed[2], t.additivesUsed[3], cAdd.uPieces, cAdd.llCoins, cMix.uPieces, cMix.llCoins,
				cAdd.llCoins + cMix.llCoins + cChest.llCoins, avLines, avLines ? (double)avSum / avLines : 0.0, top, topLines);
	}

	// ------------------------------------------------------------------------------------------------ the tick

	// Asked by ManagePlayerBotShopAids on every tick: its own clock (PLAYERBOT_BONUS67_LOOK_*), one action a look - the
	// add to the piece with one line, else the add to a piece with none, else a mix. Never holds the bot.
	bool ManagePlayerBotBonus67(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LogPlayerBotBonus67Census(dwNow);
		if (!ch || !IsPlayerBotBonus67On() || !IsPlayerBotBonus67Stage(ch))
			return false;
		TPlayerBotBonus67& s = s_mapPlayerBotBonus67[ch->GetPlayerID()];
		if (s.dwNextLook != 0 && (int)(dwNow - s.dwNextLook) < 0)
			return false;
		if (ch->IsDead() || ch->GetVictim() != NULL || state.dwTargetVID != 0 || ch->GetExchange() || ch->GetMyShop() ||
				!ch->CanHandleItem())
		{
			s.dwNextLook = dwNow + 30 * 1000;
			return false;
		}
		s.dwNextLook = dwNow + number(PLAYERBOT_BONUS67_LOOK_MIN_MS, PLAYERBOT_BONUS67_LOOK_MAX_MS);
		++s_kPlayerBotBonus67Stats.looks;

		const int element = GetPlayerBotBonus67Element(ch);
		BYTE wear = 0;
		LPITEM target = GetPlayerBotBonus67AddTarget(ch, element, &wear);
		if (!target)
		{
			s.dwPlanItem = s.dwPlanSince = s.dwShardWant = 0;
			s.iShardNeed = 0;
			s.dwNoSupplySince = 0;
			return MixPlayerBotBonus67(ch, state, dwNow);
		}
		if (s.dwPlanItem != target->GetID())
		{
			s.dwPlanItem = target->GetID();
			s.dwPlanSince = dwNow;
			s.dwNoSupplySince = 0;
			char lines[96];
			FormatPlayerBotBonus67Lines(target, lines, sizeof(lines));
			sys_log(0, "PLAYERBOT_BONUS67: plan pid=%u name=%s lv=%d wear=%u vnum=%u item_lv=%d scope=%d shard=%u have=%d "
					"element=%d lines=[%s]", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)wear,
					target->GetVnum(), GetPlayerBotBonus67ItemLevel(target), GetPlayerBotBonus67Scope(ch, target, element),
					mt2009_seonhae::MaterialVnum(target), (int)ch->CountSpecifyItem(mt2009_seonhae::MaterialVnum(target)), element, lines);
		}
		const DWORD shard = mt2009_seonhae::MaterialVnum(target);
		OpenPlayerBotBonus67Chests(ch, shard);
		const int held = (int)ch->CountSpecifyItem(shard);
		const bool magic = ch->CountSpecifyItem(PLAYERBOT_BONUS67_ADD_STONE) > 0;
		// the market's want (rule 4) and whether a counter has the shard at all
		s.dwShardWant = shard;
		s.iShardNeed = std::max(0, (int)mt2009_seonhae::MATERIAL_MAX - held);
		s.dwWantUntil = dwNow + PLAYERBOT_BONUS67_WANT_MS;
		const TPlayerBotMarketLedgerEntry* supply = GetPlayerBotMarketLedgerEntry(shard);
		const bool onMarket = supply && supply->dwSupplyUnits > 0;
		if (onMarket || s.iShardNeed == 0)
			s.dwNoSupplySince = 0;
		else if (s.dwNoSupplySince == 0)
			s.dwNoSupplySince = dwNow;
		if (!magic)
		{
			if (held <= 0)
			{
				++s_kPlayerBotBonus67Stats.addsNoShard;
				PlayerBotLogThrottled("b67_no_shard", dwNow, "PLAYERBOT_BONUS67: wait shard pid=%u name=%s vnum=%u shard=%u have=0 "
						"on_market=%d", ch->GetPlayerID(), ch->GetName(), target->GetVnum(), shard, onMarket ? 1 : 0);
				return MixPlayerBotBonus67(ch, state, dwNow);
			}
			// fewer than ten: wait while a counter may still sell the rest, at most PLAYERBOT_BONUS67_SHARD_WAIT_MS
			if (held < (int)mt2009_seonhae::MATERIAL_MAX && dwNow - s.dwPlanSince < PLAYERBOT_BONUS67_SHARD_WAIT_MS)
			{
				++s_kPlayerBotBonus67Stats.addsWaitShard;
				return MixPlayerBotBonus67(ch, state, dwNow);
			}
			// the Silne the coins buy today: wait for the V3 goal, at most PLAYERBOT_BONUS67_ADDITIVE_WAIT_MS
			if (GetPlayerBotBonus67AdditiveBuy(ch, state) > 0 && dwNow - s.dwPlanSince < PLAYERBOT_BONUS67_ADDITIVE_WAIT_MS)
			{
				++s_kPlayerBotBonus67Stats.addsWaitAdditive;
				return MixPlayerBotBonus67(ch, state, dwNow);
			}
		}
		if (!AddPlayerBotBonus67(ch, state, target, wear, dwNow))
		{
			PlayerBotLogThrottled("b67_add_refused", dwNow, "PLAYERBOT_BONUS67: no add pid=%u name=%s vnum=%u shard=%u have=%d",
					ch->GetPlayerID(), ch->GetName(), target->GetVnum(), shard, held);
			return MixPlayerBotBonus67(ch, state, dwNow);
		}
		// the next add starts its own plan (the same piece while it has one line)
		s.dwPlanItem = 0;
		return true;
	}
}

#endif

#endif
