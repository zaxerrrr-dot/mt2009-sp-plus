#ifndef __INC_METIN2_PLAYERBOT_PETMAT_H__
#define __INC_METIN2_PLAYERBOT_PETMAT_H__

// MT2009_PLUS_BOT_PET_MATS_V1 - the growth pets' evolution materials reach the keepers (the owner, 7 November 2026:
// "Wprowadz A) Boty, ktorym brakuje Wstegi albo Spinki, ida polowac na moby, ktore je dropia. To czysto po stronie botow.
// C) Boty wymieniaja miedzy soba: kto ma nadmiar materialu, wystawia go na rynek, zamiast trzymac. Ale tez wprowadz, ze od
// teraz boty moga otrzymywac potrzebne przedmioty na kazdym lvl. Czyli nie maja capa na drop -15%. Czyli jak potrzebuja
// wstegi, to ida ja dropic i faktycznie im dropi."). The Yohara test world, 7 November: 446 keepers, 417 pets, 397 at
// stage 1 and 20 at stage 2, 166 with the level and the experience of the step and not one evolution - Biala Wstega+
// (30073) and Ozdobna Spinka (30017) come only from the Sworn commanders / archers and the Jung girls (levels 20-31,
// 0.5 % a kill), and a keeper of 40+ got 1 % of that (aiPercentByDeltaLev, fifteen levels over the monster).
//
// Three parts, each with its switch (event flags; m2_bot_petmat_off 1: all three):
//   hunt (m2_bot_petmat_hunt_off) - A. A keeper whose pet's next step is open (PlayerBotNewPetStepOpen: ready, or within
//        PLAYERBOT_NEWPET_NEAR_LEVELS) and lacks a material of that step the counters do not hold enough of goes hunting a
//        monster that drops it: the drop knowledge's sources (playerbot_dropknow.h - mob_drop_item, the drop / kill /
//        level groups, every map's regen / boss / stone files, loaded at the core's start), a monster no more than
//        PLAYERBOT_PETMAT_MOB_ABOVE levels over the bot and no boss, on a map this core hosts: the map it stands on (where
//        it may grind) or a frontier map of the 2.x world (no dungeon, no Arezzo / Sung Ma / loot-run map, the Spider
//        Dungeons only with their gear, the element gate passed) - the best chance first, the map it stands on counted
//        three times. The map becomes the bot's frontier (GetPlayerBotFrontierMapForLevelRaw, under the Biologist's row,
//        the droppers', the farmers' and a guild's errand), the monsters of the material its fight's material target
//        (BuildPlayerBotCombatContext) and its map scan's carrier (StartPlayerBotMaterialHunt) - an outgrown monster too.
//        Not a dropper, a party member, a dungeon runner, a Dropki, a Yohara trainee / cohort / resident, a horse trial, a
//        companion; a party or a run ends the hunt. PLAYERBOT_PETMAT_HUNT_MS at most, then PLAYERBOT_PETMAT_GIVEUP_MS
//        before that material is hunted again; at most PLAYERBOT_PETMAT_HUNTERS (env, 40) hunters a core. A keeper buys
//        what the counters hold of a step's materials when the rest is huntable (IsPlayerBotNewPetEvolutionReachable).
//   sell (m2_bot_petmat_sell_off) - C. A pet evolution material on a counter keeps back no "one of anything" floor
//        (GetPlayerBotStallBaseKeepRules): a bot with no pet, or one that is no keeper, lists everything its anvil does
//        not take; a keeper keeps what its pet's next steps take (GetPlayerBotNewPetStageKeep: the next stage's
//        materials and those of the stages after it whose level the bot is within PLAYERBOT_NEWPET_NEAR_LEVELS of) and
//        lists the rest. A bot of channel 2+ already goes to channel 1 for its own stand (MT2009_PLUS_BOT_STAND_ERRAND_NOW_V1).
//   drop (m2_bot_petmat_drop_off) - D. A bot's kill of a monster under its level drops an item it NEEDS at the chance of
//        a kill at its own level: the level fade (GetDropPct's PERCENT_LVDELTA / _BOSS) is lifted for that item alone
//        (server-patches/botneeddrop, MT2009_PLUS_BOT_NEED_DROP_V1 in item_manager.cpp's CreateDropItem: the drop groups,
//        the kill groups and the proto's etc drop). "Needed" is a kind of this file (EPlayerBotNeedKind - more kinds may
//        be added): BOTNEED_PET_EVOLUTION - a material of a keeper's open next step it holds fewer of than the step takes.
//        Players are never asked: the engine's hooks answer false for a person.
//
// The log: BOT_PETMAT lines - hunt start / done / timeout / end (throttled), no source (throttled), bypass (throttled),
// census every PLAYERBOT_PETMAT_CENSUS_MS: hunters now and by material, started, done, timeouts, ended, units gained by
// the hunters, the needed drops the bots got and how many of them the level fade would have refused, the units of pet
// materials the counters' cuts listed, the evolutions, the counters' supply of the stage-2 materials.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_deathloop.h (the pets, the market, the
// drop knowledge before it), in the anonymous namespace; the early headers ask its hooks through declarations. The
// engine's three hooks (Mt2009PlusBotNeedDrop*) are defined at the end, outside the namespace.

namespace
{
	const DWORD PLAYERBOT_PETMAT_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_LOOK_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_LOOK_MAX_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_HUNT_LOOK_MS = 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_HUNT_MS = 45 * 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_GIVEUP_MS = 3 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_PETMAT_SOURCE_CACHE_MS = 10 * 60 * 1000;
	const int PLAYERBOT_PETMAT_MOB_ABOVE = 5;
	const float PLAYERBOT_PETMAT_MIN_CHANCE = 0.0005f;	// 0.05 % a kill

	// EPlayerBotPetMatPart: playerbot_newpet_bots.h.
	bool IsPlayerBotPetMatOn(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[PETMAT_PART_COUNT] = { false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_petmat_off") != 0;
			s_abOff[PETMAT_HUNT] = all || q.GetEventFlag("m2_bot_petmat_hunt_off") != 0;
			s_abOff[PETMAT_SELL] = all || q.GetEventFlag("m2_bot_petmat_sell_off") != 0;
			s_abOff[PETMAT_DROP] = all || q.GetEventFlag("m2_bot_petmat_drop_off") != 0;
		}
		return part >= 0 && part < PETMAT_PART_COUNT && !s_abOff[part];
	}

	int GetPlayerBotPetMatHuntersMax()
	{
		static int s_iMax = -1;
		if (s_iMax < 0)
			s_iMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_PETMAT_HUNTERS", 40, 0, 2000);
		return s_iMax;
	}

	// ------------------------------------------------------------ the needed items (D)

	// The kinds of "an item this bot needs" the drop's level fade does not cut. One so far.
	enum EPlayerBotNeedKind
	{
		BOTNEED_PET_EVOLUTION = 0,
		BOTNEED_KIND_COUNT
	};
	const char* const PLAYERBOT_NEED_KIND_NAMES[BOTNEED_KIND_COUNT] = { "pet" };

	bool IsPlayerBotPetNeedBot(LPCHARACTER ch)
	{
		if (!IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !ch->IsItemLoaded())
			return false;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		return v && v->hasPet && v->nextStage && PlayerBotNewPetStepOpen(*v);
	}

	// Whether the bot has any need of the kind now (cheap: asked once a kill).
	bool PlayerBotHasNeedsOfKind(int kind, LPCHARACTER ch)
	{
		switch (kind)
		{
			case BOTNEED_PET_EVOLUTION:
				return IsPlayerBotPetNeedBot(ch);
		}
		return false;
	}

	// Whether this item is one the bot needs of the kind (asked a drop row at a time).
	bool IsPlayerBotNeededOfKind(int kind, LPCHARACTER ch, DWORD vnum)
	{
		switch (kind)
		{
			case BOTNEED_PET_EVOLUTION:
			{
				if (!IsPlayerBotNewPetEvolutionMaterialVnum(vnum) || !IsPlayerBotPetNeedBot(ch))
					return false;
				const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
				const int need = v ? GetPlayerBotNewPetMaterialNeed(ch, *v, vnum) : 0;
				return need > 0 && (int)ch->CountSpecifyItem(vnum) < need;
			}
		}
		return false;
	}

	int GetPlayerBotNeededKind(LPCHARACTER ch, DWORD vnum)
	{
		for (int k = 0; k < BOTNEED_KIND_COUNT; ++k)
			if (IsPlayerBotNeededOfKind(k, ch, vnum))
				return k;
		return -1;
	}

	bool IsPlayerBotNeedDropBot(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !IsPlayerBotPetMatOn(PETMAT_DROP))
			return false;
		for (int k = 0; k < BOTNEED_KIND_COUNT; ++k)
			if (PlayerBotHasNeedsOfKind(k, ch))
				return true;
		return false;
	}

	// ------------------------------------------------------------ the state and the stats

	struct TPlayerBotPetMatHunt
	{
		DWORD vnum, mob;
		long map;
		DWORD start, until;
		int need, haveStart, haveLast;
		float chance;
		TPlayerBotPetMatHunt() : vnum(0), mob(0), map(0), start(0), until(0), need(0), haveStart(0), haveLast(0), chance(0.0f) {}
	};
	struct TPlayerBotPetMatBot
	{
		DWORD nextLook, lastSeen;
		std::map<DWORD, DWORD> giveUpUntil;	// material -> no hunt for it before
		TPlayerBotPetMatBot() : nextLook(0), lastSeen(0) {}
	};
	struct TPlayerBotPetMatStats
	{
		DWORD started, done, timeouts, ended, gained, needDrops, bypassed, listedUnits, listedLines, evolved, noSource;
		std::map<DWORD, DWORD> needDropsBy, bypassedBy, listedBy;
		TPlayerBotPetMatStats() : started(0), done(0), timeouts(0), ended(0), gained(0), needDrops(0), bypassed(0),
				listedUnits(0), listedLines(0), evolved(0), noSource(0) {}
	};
	std::map<DWORD, TPlayerBotPetMatHunt> s_mapPlayerBotPetMatHunt;		// pid -> its hunt
	std::map<DWORD, TPlayerBotPetMatBot> s_mapPlayerBotPetMatBots;
	TPlayerBotPetMatStats s_kPlayerBotPetMatStats;
	DWORD s_dwPlayerBotPetMatCensusAt = 0;
	// (pid, vnum) -> (when, a source exists)
	std::map<std::pair<DWORD, DWORD>, std::pair<DWORD, bool> > s_mapPlayerBotPetMatSourceCache;

	// playerbot_newpet_bots.h's evolution and playerbot_offline_shop.h's cut of a line (declared there).
	void NotePlayerBotPetMatEvolved()
	{
		++s_kPlayerBotPetMatStats.evolved;
	}

	void NotePlayerBotPetMatListed(LPCHARACTER ch, DWORD vnum, int units)
	{
		if (!ch || units <= 0 || !IsPlayerBotNewPetEvolutionMaterialVnum(vnum))
			return;
		++s_kPlayerBotPetMatStats.listedLines;
		s_kPlayerBotPetMatStats.listedUnits += (DWORD)units;
		s_kPlayerBotPetMatStats.listedBy[vnum] += (DWORD)units;
		PlayerBotLogThrottledEvery("petmat_listed", get_dword_time(), 600000,
				"BOT_PETMAT: listed pid=%u name=%s keeper=%d vnum=%u(%s) units=%d left=%u keep=%d",
				ch->GetPlayerID(), ch->GetName(), IsPlayerBotNewPetKeeper(ch) ? 1 : 0, vnum, PlayerBotDkItemName(vnum), units,
				(unsigned int)ch->CountSpecifyItem(vnum), GetPlayerBotNewPetStageKeep(ch, vnum));
	}

	// ------------------------------------------------------------ the source (A)

	bool IsPlayerBotPetMatHuntMapOk(LPCHARACTER ch, long map)
	{
		if (map <= 0 || !IsPlayerBotMapHostedHere(map) || s_kPlayerBotDropKnow.mapDefs.count(map))
			return false;
		if (map == ch->GetMapIndex())
			return IsPlayerBotGrindAllowedHere(ch) && !IsPlayerBotSungmaBotMap(map) && !IsPlayerBotArezzoMap(map);
		if (!IsPlayerBotFrontierMapIndex(map) || IsPlayerBotArezzoMap(map) || IsPlayerBotSungmaBotMap(map) ||
				(map >= 301 && map <= 304) || map == PLAYERBOT_MAP_ZAKLETY || map == PLAYERBOT_MAP_OCHAO ||
				map == PLAYERBOT_MAP_DEMON_TOWER)
			return false;
		if (IsPlayerBotSpiderMap(map) && !IsPlayerBotSpiderGearReady(ch, map))
			return false;
		return PassPlayerBotElementMapGate(ch, map, NULL, NULL);
	}

	// The best monster and map of this core for the material: no boss, not over the bot's level by more than
	// PLAYERBOT_PETMAT_MOB_ABOVE, the chance of a kill at the bot's level (the full one while the drop part lifts the fade).
	bool PickPlayerBotPetMatSource(LPCHARACTER ch, DWORD vnum, DWORD& mobOut, long& mapOut, float& chanceOut)
	{
		mobOut = 0;
		mapOut = 0;
		chanceOut = 0.0f;
		const TPlayerBotDropKnow& k = s_kPlayerBotDropKnow;
		if (!ch || !k.bBuilt)
			return false;
		std::map<DWORD, std::vector<TPlayerBotDkSource> >::const_iterator src = k.byItem.find(vnum);
		if (src == k.byItem.end())
			return false;
		const int level = (int)ch->GetLevel();
		const bool noFade = IsPlayerBotPetMatOn(PETMAT_DROP);
		float best = 0.0f;
		for (size_t i = 0; i < src->second.size(); ++i)
		{
			const TPlayerBotDkSource& s = src->second[i];
			if (s.bKind != DROPKNOW_MOB)
				continue;
			const CMob* mob = CMobManager::instance().Get(s.dwFrom);
			if (!mob || mob->m_table.bRank >= MOB_RANK_BOSS || mob->m_table.bType != CHAR_TYPE_MONSTER)
				continue;
			const int mobLevel = (int)mob->m_table.bLevel;
			if (mobLevel <= 0 || mobLevel > level + PLAYERBOT_PETMAT_MOB_ABOVE)
				continue;
			float eff = s.fChance;
			if (!noFade || mobLevel >= level)
				eff = eff * std::min(100, (int)PERCENT_LVDELTA(level, mobLevel)) / 100.0f;
			if (eff < PLAYERBOT_PETMAT_MIN_CHANCE)
				continue;
			std::map<DWORD, std::vector<long> >::const_iterator maps = k.mobMaps.find(s.dwFrom);
			if (maps == k.mobMaps.end())
				continue;
			for (size_t m = 0; m < maps->second.size(); ++m)
			{
				const long map = maps->second[m];
				if (!IsPlayerBotPetMatHuntMapOk(ch, map))
					continue;
				const float w = eff * (map == ch->GetMapIndex() ? 3.0f : 1.0f);
				if (w > best)
				{
					best = w;
					mobOut = s.dwFrom;
					mapOut = map;
					chanceOut = eff;
				}
			}
		}
		return mobOut != 0;
	}

	// playerbot_newpet_bots.h (IsPlayerBotNewPetEvolutionReachable): whether this bot could hunt the material here.
	bool HasPlayerBotPetMatHuntSource(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || !IsPlayerBotPetMatOn(PETMAT_HUNT) || IsPlayerBotDropKnowOff() || !s_kPlayerBotDropKnow.bBuilt)
			return false;
		const DWORD now = get_dword_time();
		const std::pair<DWORD, DWORD> key(ch->GetPlayerID(), vnum);
		std::map<std::pair<DWORD, DWORD>, std::pair<DWORD, bool> >::iterator it = s_mapPlayerBotPetMatSourceCache.find(key);
		if (it != s_mapPlayerBotPetMatSourceCache.end() && now - it->second.first < PLAYERBOT_PETMAT_SOURCE_CACHE_MS)
			return it->second.second;
		if (s_mapPlayerBotPetMatSourceCache.size() > 50000)
			s_mapPlayerBotPetMatSourceCache.clear();
		DWORD mob = 0;
		long map = 0;
		float chance = 0.0f;
		const bool has = PickPlayerBotPetMatSource(ch, vnum, mob, map, chance);
		s_mapPlayerBotPetMatSourceCache[key] = std::make_pair(now ? now : 1, has);
		return has;
	}

	// ------------------------------------------------------------ the hunt's hooks (travel, targeting)

	const TPlayerBotPetMatHunt* GetPlayerBotPetMatHunt(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotPetMatOn(PETMAT_HUNT))
			return NULL;
		std::map<DWORD, TPlayerBotPetMatHunt>::const_iterator it = s_mapPlayerBotPetMatHunt.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotPetMatHunt.end() || (int)(it->second.until - get_dword_time()) <= 0)
			return NULL;
		return &it->second;
	}

	bool IsPlayerBotPetMatHunting(LPCHARACTER ch)
	{
		return GetPlayerBotPetMatHunt(ch) != NULL;
	}

	DWORD GetPlayerBotPetMatHuntVnum(LPCHARACTER ch)
	{
		const TPlayerBotPetMatHunt* h = GetPlayerBotPetMatHunt(ch);
		return h ? h->vnum : 0;
	}

	// GetPlayerBotFrontierMapForLevelRaw (playerbot_travel.h): the hunt's map, or 0.
	long GetPlayerBotPetMatHuntMap(LPCHARACTER ch)
	{
		const TPlayerBotPetMatHunt* h = GetPlayerBotPetMatHunt(ch);
		if (!h || ch->GetParty() || !IsPlayerBotMapHostedHere(h->map))
			return 0;
		return h->map;
	}

	// The fight's material target and the map scan's carrier (playerbot_targeting.h): a monster that drops the hunted
	// material (the hunt's own monster, or another the drop knowledge knows for it).
	bool IsPlayerBotPetMatHuntRace(LPCHARACTER ch, DWORD race)
	{
		const TPlayerBotPetMatHunt* h = GetPlayerBotPetMatHunt(ch);
		if (!h || !race)
			return false;
		if (race == h->mob)
			return true;
		std::map<DWORD, std::vector<TPlayerBotDkDrop> >::const_iterator it = s_kPlayerBotDropKnow.byMob.find(race);
		if (it == s_kPlayerBotDropKnow.byMob.end())
			return false;
		for (size_t i = 0; i < it->second.size(); ++i)
			if (it->second[i].dwItem == h->vnum && it->second[i].fChance >= PLAYERBOT_PETMAT_MIN_CHANCE)
				return true;
		return false;
	}

	bool IsPlayerBotPetMatHuntTarget(LPCHARACTER ch, LPCHARACTER mob)
	{
		return ch && mob && mob->IsMonster() && !mob->IsDead() &&
				mob->GetLevel() <= ch->GetLevel() + PLAYERBOT_PETMAT_MOB_ABOVE &&
				IsPlayerBotPetMatHuntRace(ch, mob->GetRaceNum());
	}

	// ------------------------------------------------------------ the bot's pass (A)

	// Why the bot may not hunt now (NULL: it may).
	const char* GetPlayerBotPetMatBusy(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotDropper(state.bPersonality))
			return "dropper";
		if (ch->GetParty())
			return "party";
		if (IsPlayerBotOnDungeonRun(pid))
			return "dungeon";
		if (IsPlayerBotDropkiRole(pid))
			return "dropki";
		if (IsPlayerBotYdgTrainee(pid) || IsPlayerBotYoharaCohortPID(pid))
			return "yohara";
		if (IsPlayerBotSungmaBotMap(ch->GetMapIndex()))
			return "sungma";
		if (IsPlayerBotOnAnyHorseTrial(ch))
			return "horse";
		if (IsPlayerBotSidekickPID(pid))
			return "companion";
		return NULL;
	}

	void EndPlayerBotPetMatHunt(LPCHARACTER ch, const char* why, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotPetMatHunt>::iterator it = s_mapPlayerBotPetMatHunt.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotPetMatHunt.end())
			return;
		const TPlayerBotPetMatHunt& h = it->second;
		const int have = (int)ch->CountSpecifyItem(h.vnum);
		if (!strcmp(why, "done"))
			++s_kPlayerBotPetMatStats.done;
		else if (!strcmp(why, "timeout"))
		{
			++s_kPlayerBotPetMatStats.timeouts;
			s_mapPlayerBotPetMatBots[ch->GetPlayerID()].giveUpUntil[h.vnum] = dwNow + PLAYERBOT_PETMAT_GIVEUP_MS;
		}
		else
			++s_kPlayerBotPetMatStats.ended;
		PlayerBotLogThrottledEvery(!strcmp(why, "done") ? "petmat_done" : "petmat_end", dwNow, 300000,
				"BOT_PETMAT: hunt %s pid=%u name=%s level=%d vnum=%u(%s) mob=%u map=%ld have=%d/%d from=%d minutes=%u",
				why, ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), h.vnum, PlayerBotDkItemName(h.vnum), h.mob, h.map,
				have, h.need, h.haveStart, (unsigned int)((dwNow - h.start) / 60000));
		s_mapPlayerBotPetMatHunt.erase(it);
	}

	bool StartPlayerBotPetMatHunt(LPCHARACTER ch, DWORD dwNow)
	{
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		std::vector<std::pair<DWORD, int> > mats;
		if (!v || !growth_pet::GetEvolutionMaterials(v->nextStage, mats))
			return false;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotPetMatBot& b = s_mapPlayerBotPetMatBots[pid];
		// the rarest on the counters first
		DWORD pickVnum = 0, pickMob = 0, pickSupply = 0xffffffffU;
		long pickMap = 0;
		int pickNeed = 0, pickHave = 0;
		float pickChance = 0.0f;
		for (size_t i = 0; i < mats.size(); ++i)
		{
			const DWORD vnum = mats[i].first;
			const int need = GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
			const int have = (int)ch->CountSpecifyItem(vnum);
			if (need <= have)
				continue;
			const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(vnum);
			const DWORD supply = e ? e->dwSupplyUnits : 0;
			if ((int)supply >= need - have)
				continue;	// the counters' (the pet's own market trip buys it)
			std::map<DWORD, DWORD>::iterator g = b.giveUpUntil.find(vnum);
			if (g != b.giveUpUntil.end())
			{
				if ((int)(g->second - dwNow) > 0)
					continue;
				b.giveUpUntil.erase(g);
			}
			if (supply >= pickSupply)
				continue;
			DWORD mob = 0;
			long map = 0;
			float chance = 0.0f;
			if (!PickPlayerBotPetMatSource(ch, vnum, mob, map, chance))
			{
				++s_kPlayerBotPetMatStats.noSource;
				PlayerBotLogThrottledEvery("petmat_nosource", dwNow, 600000,
						"BOT_PETMAT: no source pid=%u name=%s level=%d map=%ld vnum=%u(%s) lack=%d supply=%u",
						pid, ch->GetName(), (int)ch->GetLevel(), ch->GetMapIndex(), vnum, PlayerBotDkItemName(vnum),
						need - have, supply);
				continue;
			}
			pickVnum = vnum;
			pickMob = mob;
			pickMap = map;
			pickSupply = supply;
			pickNeed = need;
			pickHave = have;
			pickChance = chance;
		}
		if (!pickVnum)
			return false;
		if ((int)s_mapPlayerBotPetMatHunt.size() >= GetPlayerBotPetMatHuntersMax())
		{
			PlayerBotLogThrottledEvery("petmat_cap", dwNow, 600000, "BOT_PETMAT: hunters cap=%d pid=%u vnum=%u waits",
					GetPlayerBotPetMatHuntersMax(), pid, pickVnum);
			return false;
		}
		TPlayerBotPetMatHunt& h = s_mapPlayerBotPetMatHunt[pid];
		h.vnum = pickVnum;
		h.mob = pickMob;
		h.map = pickMap;
		h.start = dwNow ? dwNow : 1;
		h.until = dwNow + PLAYERBOT_PETMAT_HUNT_MS;
		h.need = pickNeed;
		h.haveStart = h.haveLast = pickHave;
		h.chance = pickChance;
		++s_kPlayerBotPetMatStats.started;
		PlayerBotLogThrottledEvery("petmat_start", dwNow, 120000,
				"BOT_PETMAT: hunt start pid=%u name=%s level=%d pet_level=%d stage=%d vnum=%u(%s) have=%d/%d supply=%u mob=%u(lv %d) "
				"map=%ld from=%ld chance=%.3f%% hunters=%u",
				pid, ch->GetName(), (int)ch->GetLevel(), v->pet.level, v->nextStage, pickVnum, PlayerBotDkItemName(pickVnum),
				pickHave, pickNeed, pickSupply, pickMob, PlayerBotDkMobLevel(pickMob), pickMap, ch->GetMapIndex(),
				pickChance * 100.0f, (unsigned int)s_mapPlayerBotPetMatHunt.size());
		return true;
	}

	void LogPlayerBotPetMatCensus()
	{
		TPlayerBotPetMatStats& s = s_kPlayerBotPetMatStats;
		std::map<DWORD, int> byMat;
		const DWORD now = get_dword_time();
		for (std::map<DWORD, TPlayerBotPetMatHunt>::const_iterator it = s_mapPlayerBotPetMatHunt.begin();
				it != s_mapPlayerBotPetMatHunt.end(); ++it)
			++byMat[it->second.vnum];
		std::string hunters;
		for (std::map<DWORD, int>::const_iterator it = byMat.begin(); it != byMat.end(); ++it)
		{
			char buf[32];
			snprintf(buf, sizeof(buf), "%s%u:%d", hunters.empty() ? "" : ",", it->first, it->second);
			hunters += buf;
		}
		std::string drops, bypassed, listed, supply;
		for (std::map<DWORD, DWORD>::const_iterator it = s.needDropsBy.begin(); it != s.needDropsBy.end() && drops.size() < 400; ++it)
		{
			char buf[32];
			snprintf(buf, sizeof(buf), "%s%u:%u", drops.empty() ? "" : ",", it->first, it->second);
			drops += buf;
		}
		for (std::map<DWORD, DWORD>::const_iterator it = s.bypassedBy.begin(); it != s.bypassedBy.end() && bypassed.size() < 400; ++it)
		{
			char buf[32];
			snprintf(buf, sizeof(buf), "%s%u:%u", bypassed.empty() ? "" : ",", it->first, it->second);
			bypassed += buf;
		}
		for (std::map<DWORD, DWORD>::const_iterator it = s.listedBy.begin(); it != s.listedBy.end() && listed.size() < 400; ++it)
		{
			char buf[32];
			snprintf(buf, sizeof(buf), "%s%u:%u", listed.empty() ? "" : ",", it->first, it->second);
			listed += buf;
		}
		{
			std::vector<std::pair<DWORD, int> > mats;
			growth_pet::GetEvolutionMaterials(2, mats);
			for (size_t i = 0; i < mats.size(); ++i)
			{
				const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(mats[i].first);
				char buf[32];
				snprintf(buf, sizeof(buf), "%s%u:%u", supply.empty() ? "" : ",", mats[i].first, e ? e->dwSupplyUnits : 0U);
				supply += buf;
			}
		}
		sys_log(0, "BOT_PETMAT: census hunt=%d sell=%d drop=%d hunters=%u cap=%d by_material=%s | started=%u done=%u timeouts=%u "
				"ended=%u gained=%u no_source=%u need_drops=%u (%s) bypassed=%u (%s) listed_units=%u listed_lines=%u (%s) "
				"evolved=%u supply_stage2=%s",
				IsPlayerBotPetMatOn(PETMAT_HUNT) ? 1 : 0, IsPlayerBotPetMatOn(PETMAT_SELL) ? 1 : 0,
				IsPlayerBotPetMatOn(PETMAT_DROP) ? 1 : 0, (unsigned int)s_mapPlayerBotPetMatHunt.size(),
				GetPlayerBotPetMatHuntersMax(), hunters.empty() ? "-" : hunters.c_str(), s.started, s.done, s.timeouts, s.ended,
				s.gained, s.noSource, s.needDrops, drops.empty() ? "-" : drops.c_str(), s.bypassed,
				bypassed.empty() ? "-" : bypassed.c_str(), s.listedUnits, s.listedLines, listed.empty() ? "-" : listed.c_str(),
				s.evolved, supply.c_str());
		s = TPlayerBotPetMatStats();
		// the gone bots' rows
		for (std::map<DWORD, TPlayerBotPetMatBot>::iterator it = s_mapPlayerBotPetMatBots.begin(); it != s_mapPlayerBotPetMatBots.end();)
		{
			if (now - it->second.lastSeen > 60 * 60 * 1000)
			{
				s_mapPlayerBotPetMatHunt.erase(it->first);
				s_mapPlayerBotPetMatBots.erase(it++);
			}
			else
				++it;
		}
	}

	// The tick's call (playerbot_manager.cpp, after ManagePlayerBotNewPet).
	void ManagePlayerBotPetMat(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_dwPlayerBotPetMatCensusAt == 0 || (int)(dwNow - s_dwPlayerBotPetMatCensusAt) >= 0)
		{
			if (s_dwPlayerBotPetMatCensusAt != 0)
				LogPlayerBotPetMatCensus();
			s_dwPlayerBotPetMatCensusAt = dwNow + PLAYERBOT_PETMAT_CENSUS_MS;
		}
		if (!ch || ch->IsDead() || !ch->IsItemLoaded())
			return;
		const DWORD pid = ch->GetPlayerID();
		const bool hunting = s_mapPlayerBotPetMatHunt.count(pid) != 0;
		if (!hunting && !IsPlayerBotNewPetKeeper(ch))
			return;
		TPlayerBotPetMatBot& b = s_mapPlayerBotPetMatBots[pid];
		b.lastSeen = dwNow ? dwNow : 1;
		if (b.nextLook != 0 && (int)(dwNow - b.nextLook) < 0)
			return;
		b.nextLook = dwNow + (hunting ? PLAYERBOT_PETMAT_HUNT_LOOK_MS
				: (DWORD)number(PLAYERBOT_PETMAT_LOOK_MIN_MS, PLAYERBOT_PETMAT_LOOK_MAX_MS));
		if (!IsPlayerBotPetMatOn(PETMAT_HUNT) || IsPlayerBotDropKnowOff())
		{
			if (hunting)
				EndPlayerBotPetMatHunt(ch, "off", dwNow);
			return;
		}
		const char* busy = GetPlayerBotPetMatBusy(ch, state);
		if (hunting)
		{
			TPlayerBotPetMatHunt& h = s_mapPlayerBotPetMatHunt[pid];
			const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
			const int need = v && PlayerBotNewPetStepOpen(*v) ? GetPlayerBotNewPetMaterialNeed(ch, *v, h.vnum) : 0;
			const int have = (int)ch->CountSpecifyItem(h.vnum);
			if (have > h.haveLast)
				s_kPlayerBotPetMatStats.gained += (DWORD)(have - h.haveLast);
			h.haveLast = have;
			if (need <= 0)
				EndPlayerBotPetMatHunt(ch, "step_closed", dwNow);
			else if (have >= need)
				EndPlayerBotPetMatHunt(ch, "done", dwNow);
			else if (busy)
				EndPlayerBotPetMatHunt(ch, busy, dwNow);
			else if ((int)(dwNow - h.until) >= 0)
				EndPlayerBotPetMatHunt(ch, "timeout", dwNow);
			return;
		}
		if (busy || !IsPlayerBotPetNeedBot(ch) || !s_kPlayerBotDropKnow.bBuilt)
			return;
		StartPlayerBotPetMatHunt(ch, dwNow);
	}
}

// ------------------------------------------------------------ the engine's hooks (server-patches/botneeddrop)

// MT2009_PLUS_BOT_NEED_DROP_V1: whether the killer is a bot with a needed item now (the drop part on). A person: false.
bool Mt2009PlusBotNeedDropKiller(LPCHARACTER pkKiller)
{
	return IsPlayerBotNeedDropBot(pkKiller);
}

// Whether the killer bot needs this item (a drop row's vnum).
bool Mt2009PlusBotNeedsDropItem(LPCHARACTER pkKiller, DWORD dwVnum)
{
	return IsPlayerBotNeedDropBot(pkKiller) && GetPlayerBotNeededKind(pkKiller, dwVnum) >= 0;
}

// A drop of a needed item was made for the bot; bBypassed: only because the level fade was lifted.
void Mt2009PlusBotNeedDropNote(LPCHARACTER pkKiller, DWORD dwVnum, bool bBypassed)
{
	if (!pkKiller || !pkKiller->IsPC() || !pkKiller->GetDesc() || !pkKiller->GetDesc()->IsBot())
		return;
	const int kind = GetPlayerBotNeededKind(pkKiller, dwVnum);
	if (kind < 0)
		return;
	++s_kPlayerBotPetMatStats.needDrops;
	++s_kPlayerBotPetMatStats.needDropsBy[dwVnum];
	if (bBypassed)
	{
		++s_kPlayerBotPetMatStats.bypassed;
		++s_kPlayerBotPetMatStats.bypassedBy[dwVnum];
		PlayerBotLogThrottledEvery("petmat_bypass", get_dword_time(), 300000,
				"BOT_PETMAT: bypass pid=%u name=%s level=%d kind=%s vnum=%u(%s) map=%ld have=%u",
				pkKiller->GetPlayerID(), pkKiller->GetName(), (int)pkKiller->GetLevel(), PLAYERBOT_NEED_KIND_NAMES[kind], dwVnum,
				PlayerBotDkItemName(dwVnum), pkKiller->GetMapIndex(), (unsigned int)pkKiller->CountSpecifyItem(dwVnum));
	}
}

#endif
