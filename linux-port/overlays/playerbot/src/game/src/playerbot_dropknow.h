#ifndef __INC_METIN2_PLAYERBOT_DROPKNOW_H__
#define __INC_METIN2_PLAYERBOT_DROPKNOW_H__

// MT2009_PLUS_BOT_DROPKNOW_V1 (2.x, trimmed) - what drops from what, for the bots. The owner, 6 November 2026, with
// the 2.42 port: "port a trimmed-down drop knowledge module too (bots know what drops where - needed for Orc Tooth
// farming and the Dozorca swap)". The 3.x module (claude/yohara-3, 8eb25574) also knows chests, recipes, NPC shops,
// refine steps, the Yohara dungeons and the Dropki; 2.x keeps only the part the materials need:
//
//   * the index (BuildPlayerBotDropKnow, PLAYERBOT_DROPKNOW_FIRST_BUILD_MS after the core's start, again every
//     PLAYERBOT_DROPKNOW_REBUILD_MS): every monster's drops from the tables this core loaded - mob_drop_item.txt, the
//     drop and level groups - as the drop wiki reads them (ITEM_MANAGER::GetDropWikiRows: the chance a kill gives a
//     killer at the monster's own level), and every monster's maps from the map/index maps' regen.txt / boss.txt /
//     stone.txt (the drop wiki's own reading, regen.cpp's line types m/s/g/r). No engine patch: both come from what
//     2.x already has (MT2009_PLUS_DROP_WIKI_V1, the map regions).
//       item -> monsters (the best PLAYERBOT_DROPKNOW_MOB_SOURCES chances), monster -> items, monster -> maps;
//       a map is "open" when it is a frontier or a village map (IsPlayerBotFrontierMapIndex / IsPlayerBotVillageMap),
//       not an instance and no bot dungeon run's (PLAYERBOT_DGRUN_DEFS - the Demon Tower is one).
//   * the question "where does item X drop for a bot of level L" (PickPlayerBotDkSource): a monster on an open map
//     within the drop's level window - not more than 10 levels over the bot and PERCENT_LVDELTA(bot, monster) at least
//     PLAYERBOT_MATERIAL_MIN_DROP_PERCENT (CreateDropItem cuts every drop by it) - weighed chance x level penalty, the
//     map the bot stands on x4, a map this core hosts x2.
//   * the need pass (ManagePlayerBotDropKnow, PLAYERBOT_DROPKNOW_PASS_BOTS bots every PLAYERBOT_DROPKNOW_PASS_MS, each
//     bot every PLAYERBOT_DROPKNOW_NEED_MS): what the bot's anvil lacks (CollectPlayerBotWantedMaterials) and its belt
//     recipe (CollectPlayerBotBeltMissing), the first PLAYERBOT_DROPKNOW_NEEDS_A_BOT of them, each to
//       "bag" (enough) / "market" (the ledger has it and the bot can pay the last ask - playerbot_mats_flow.h) /
//       "farm:<map>/<mob>" (a farm order for PLAYERBOT_DROPKNOW_FARM_MS: the monster is a material target of the
//       bot's fight, and for PLAYERBOT_MATS_FARM_VNUMS the hunting map - playerbot_mats_flow.h) / "none".
//     No dungeon, craft or shop choice on 2.x.
// Event flag m2_bot_dropknow_off 1: no need pass, no farm order, no hook (the index stays).
//
// The log: BOT_DROPKNOW lines - built (items, monsters, places, ms), need (a bot's choices, again only when they
// change or every PLAYERBOT_DROPKNOW_RELOG_MS), status every PLAYERBOT_DROPKNOW_STATUS_MS. The operator's file
// playerbot_dropknow_test in the core's directory (renamed .done):
//     item <vnum>        the item's sources        bot <pid>       the bot's needs now (every line)
//     rebuild            the index again           status          the status line now
//
// An implementation fragment: included by playerbot_manager.cpp last (after the market, the belts, the saddlebag
// and the dungeon runs), at file scope; its hooks are declared where they are asked (playerbot_targeting.h).

#include "locale_service.h"

#if defined(PLAYERBOT_ENGINE_MT2009)

namespace
{
	const DWORD PLAYERBOT_DROPKNOW_FIRST_BUILD_MS = 150 * 1000;
	const DWORD PLAYERBOT_DROPKNOW_REBUILD_MS = 6 * 3600 * 1000;
	const DWORD PLAYERBOT_DROPKNOW_PASS_MS = 5000;
	const int PLAYERBOT_DROPKNOW_PASS_BOTS = 25;
	const DWORD PLAYERBOT_DROPKNOW_NEED_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKNOW_FARM_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKNOW_RELOG_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKNOW_STATUS_MS = 10 * 60 * 1000;
	const size_t PLAYERBOT_DROPKNOW_MOB_SOURCES = 48;	// an item's monsters kept (the best chances)
	const size_t PLAYERBOT_DROPKNOW_NEEDS_A_BOT = 4;
	const size_t PLAYERBOT_DROPKNOW_MAPS_A_MOB = 16;
	const char* const PLAYERBOT_DROPKNOW_TEST_FILE = "playerbot_dropknow_test";

	enum EPlayerBotDkKind
	{
		DROPKNOW_MOB = 0,	// the only kind on 2.x (the 3.x module's chests / recipes / shops / steps left out)
	};

	struct TPlayerBotDkSource
	{
		BYTE bKind;
		DWORD dwFrom;
		float fChance;
		int iCountMin, iCountMax;
	};

	struct TPlayerBotDkDrop
	{
		DWORD dwItem;
		float fChance;
	};

	struct TPlayerBotDropKnow
	{
		bool bBuilt;
		DWORD dwBuiltAt;
		std::map<DWORD, std::vector<TPlayerBotDkSource> > byItem;
		std::map<DWORD, std::vector<TPlayerBotDkDrop> > byMob;		// a monster's items (per kill)
		std::map<DWORD, std::vector<long> > mobMaps;			// a monster -> the maps it lives on
		std::map<long, std::vector<DWORD> > mapMobs;
		std::set<long> dungeonMaps;					// the bot dungeon runs' maps
		TPlayerBotDropKnow() : bBuilt(false), dwBuiltAt(0) {}
	};
	TPlayerBotDropKnow s_kPlayerBotDropKnow;

	enum EPlayerBotDkChoice
	{
		DKCHOICE_BAG = 0,
		DKCHOICE_MARKET,
		DKCHOICE_FARM,
		DKCHOICE_NONE,
		DKCHOICE_COUNT
	};
	const char* const PLAYERBOT_DKCHOICE_NAMES[DKCHOICE_COUNT] = { "bag", "market", "farm", "none" };

	struct TPlayerBotDkPick
	{
		int iChoice;
		long lMap;
		DWORD dwMob;
		float fChance;
		TPlayerBotDkPick() : iChoice(DKCHOICE_NONE), lMap(0), dwMob(0), fChance(0.0f) {}
	};

	struct TPlayerBotDkFarm
	{
		long lMap;
		DWORD dwMob, dwVnum, dwUntil;
	};
	struct TPlayerBotDkBot
	{
		DWORD dwNextLook;
		std::string last;
		DWORD dwLastLog;
		TPlayerBotDkBot() : dwNextLook(0), dwLastLog(0) {}
	};
	std::map<DWORD, TPlayerBotDkFarm> s_mapPlayerBotDkFarm;
	std::map<DWORD, TPlayerBotDkBot> s_mapPlayerBotDkBots;
	unsigned int s_auPlayerBotDkChoices[DKCHOICE_COUNT] = { 0, 0, 0, 0 };
	unsigned int s_uPlayerBotDkLooked = 0;

	// MT2009_PLUS_BOT_MATS_FLOW_V1: playerbot_mats_flow.h (later) - a market the bot cannot pay is no source; its status.
	bool IsPlayerBotMatsMarketUnaffordable(LPCHARACTER ch, DWORD vnum, int lack);
	void LogPlayerBotMatsStatus();

	// The event flag, looked at once a second (asked for every monster a scan weighs).
	bool IsPlayerBotDropKnowOff()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOff = false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			s_bOff = quest::CQuestManager::instance().GetEventFlag("m2_bot_dropknow_off") != 0;
		}
		return s_bOff;
	}

	const char* PlayerBotDkItemName(DWORD vnum)
	{
		const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnum);
		return t ? t->szLocaleName : "?";
	}

	int PlayerBotDkMobLevel(DWORD race)
	{
		const CMob* mob = CMobManager::instance().Get(race);
		return mob ? (int)mob->m_table.bLevel : 0;
	}

	// A map whose monsters a bot may farm: a frontier or a village map, no instance and no bot dungeon run's.
	bool IsPlayerBotDkOpenMap(long map)
	{
		return map > 0 && map < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && !s_kPlayerBotDropKnow.dungeonMaps.count(map) &&
				(IsPlayerBotFrontierMapIndex(map) || IsPlayerBotVillageMap(map));
	}

	// ------------------------------------------------------------ the build

	void AddPlayerBotDkPlace(DWORD race, long map)
	{
		if (!race || map <= 0)
			return;
		const CMob* mob = CMobManager::instance().Get(race);
		if (!mob || (mob->m_table.bType != CHAR_TYPE_MONSTER && mob->m_table.bType != CHAR_TYPE_STONE))
			return;
		std::vector<long>& maps = s_kPlayerBotDropKnow.mobMaps[race];
		if (std::find(maps.begin(), maps.end(), map) != maps.end() || maps.size() >= PLAYERBOT_DROPKNOW_MAPS_A_MOB)
			return;
		maps.push_back(map);
		s_kPlayerBotDropKnow.mapMobs[map].push_back(race);
	}

	void AddPlayerBotDkGroup(DWORD groupVnum, long map)
	{
		CMobGroup* group = CMobManager::instance().GetGroup(groupVnum);
		if (!group)
			return;
		const std::vector<DWORD>& members = group->GetMemberVector();
		for (size_t i = 0; i < members.size(); ++i)
			AddPlayerBotDkPlace(members[i], map);
	}

	// A regen file's monsters (regen.cpp read_line: m/s a monster, g a group, r a group of groups) - the drop wiki's
	// reading.
	size_t ReadPlayerBotDkRegen(const std::string& path, long map)
	{
		FILE* fp = fopen(path.c_str(), "r");
		if (!fp)
			return 0;
		size_t lines = 0;
		char line[512];
		while (fgets(line, sizeof(line), fp))
		{
			// "r 751 311 10 10 0 0 5s 100 1 101": the type, nine fields (the time written "5s" / "10m"), the vnum
			char type[32] = "", w[10][32];
			if (sscanf(line, "%31s %31s %31s %31s %31s %31s %31s %31s %31s %31s %31s", type, w[0], w[1], w[2], w[3],
						w[4], w[5], w[6], w[7], w[8], w[9]) != 11)
				continue;
			const unsigned long vnum = strtoul(w[9], NULL, 10);
			if (!vnum || type[0] == '/' || type[0] == '#')
				continue;
			++lines;
			const char t = type[0];
			if (t == 'm' || t == 's')
				AddPlayerBotDkPlace((DWORD)vnum, map);
			else if (t == 'g')
				AddPlayerBotDkGroup((DWORD)vnum, map);
			else if (t == 'r')
			{
				const std::vector<DWORD>* groups = CMobManager::instance().GetGroupGroupMembers((DWORD)vnum);
				for (size_t i = 0; groups && i < groups->size(); ++i)
					AddPlayerBotDkGroup((*groups)[i], map);
			}
		}
		fclose(fp);
		return lines;
	}

	void BuildPlayerBotDropKnow(DWORD dwNow)
	{
		const DWORD t0 = get_dword_time();
		TPlayerBotDropKnow& k = s_kPlayerBotDropKnow;
		k = TPlayerBotDropKnow();
		// the monsters' drops (the drop wiki's rows: a killer at the monster's level)
		std::map<DWORD, std::vector<TPlayerBotDkSource> > all;
		size_t mobs = 0;
		std::vector<TDropWikiRow> rows;
		for (CMobManager::iterator it = CMobManager::instance().begin(); it != CMobManager::instance().end(); ++it)
		{
			const CMob* mob = it->second;
			if (!mob || (mob->m_table.bType != CHAR_TYPE_MONSTER && mob->m_table.bType != CHAR_TYPE_STONE))
				continue;
			ITEM_MANAGER::instance().GetDropWikiRows(it->first, rows);
			if (rows.empty())
				continue;
			++mobs;
			for (size_t i = 0; i < rows.size(); ++i)
			{
				if (!rows[i].dwVnum || rows[i].dChance <= 0.0)
					continue;
				TPlayerBotDkSource s;
				s.bKind = DROPKNOW_MOB;
				s.dwFrom = it->first;
				s.fChance = (float)std::min(1.0, rows[i].dChance);
				s.iCountMin = rows[i].iCountMin;
				s.iCountMax = rows[i].iCountMax;
				all[rows[i].dwVnum].push_back(s);
				TPlayerBotDkDrop d;
				d.dwItem = rows[i].dwVnum;
				d.fChance = s.fChance;
				k.byMob[it->first].push_back(d);
			}
		}
		size_t sources = 0;
		for (std::map<DWORD, std::vector<TPlayerBotDkSource> >::iterator it = all.begin(); it != all.end(); ++it)
		{
			std::vector<TPlayerBotDkSource>& list = it->second;
			std::sort(list.begin(), list.end(), [](const TPlayerBotDkSource& a, const TPlayerBotDkSource& b)
					{ return a.fChance > b.fChance || (a.fChance == b.fChance && a.dwFrom < b.dwFrom); });
			if (list.size() > PLAYERBOT_DROPKNOW_MOB_SOURCES)
				list.resize(PLAYERBOT_DROPKNOW_MOB_SOURCES);
			sources += list.size();
			k.byItem[it->first].swap(list);
		}
		// the bot dungeon runs' maps
		for (int def = 0; def < PLAYERBOT_DGRUN_DEF_COUNT; ++def)
			k.dungeonMaps.insert(PLAYERBOT_DGRUN_DEFS[def].lMap);
		// where they live: every map/index map's regen, boss and stone files (this core's maps and the others')
		size_t regenLines = 0, maps = 0;
		for (long map = 1; map < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && map < 10000; ++map)
		{
			const TMapRegion* region = SECTREE_MANAGER::instance().GetMapRegion(map);
			if (!region || region->strMapName.empty())
				continue;
			++maps;
			const std::string base = LocaleService_GetMapPath() + "/" + region->strMapName + "/";
			static const char* const s_aFiles[] = { "regen.txt", "boss.txt", "stone.txt" };
			for (size_t f = 0; f < sizeof(s_aFiles) / sizeof(s_aFiles[0]); ++f)
				regenLines += ReadPlayerBotDkRegen(base + s_aFiles[f], map);
		}
		k.bBuilt = true;
		k.dwBuiltAt = dwNow ? dwNow : 1;
		size_t places = 0;
		for (std::map<DWORD, std::vector<long> >::const_iterator it = k.mobMaps.begin(); it != k.mobMaps.end(); ++it)
			places += it->second.size();
		sys_log(0, "BOT_DROPKNOW: built items=%u sources=%u mobs=%u placed_mobs=%u places=%u maps=%u regen_lines=%u "
				"dungeon_maps=%u took_ms=%u", (unsigned int)k.byItem.size(), (unsigned int)sources, (unsigned int)mobs,
				(unsigned int)k.mobMaps.size(), (unsigned int)places, (unsigned int)maps, (unsigned int)regenLines,
				(unsigned int)k.dungeonMaps.size(), get_dword_time() - t0);
	}

	// ------------------------------------------------------------ the questions

	// The farm order's monster (the fight's material target - playerbot_targeting.h).
	bool IsPlayerBotDropKnowFarmMob(LPCHARACTER ch, DWORD race)
	{
		if (!ch || !race || s_mapPlayerBotDkFarm.empty() || IsPlayerBotDropKnowOff())
			return false;
		std::map<DWORD, TPlayerBotDkFarm>::const_iterator f = s_mapPlayerBotDkFarm.find(ch->GetPlayerID());
		return f != s_mapPlayerBotDkFarm.end() && f->second.dwMob == race && (int)(f->second.dwUntil - get_dword_time()) > 0;
	}

	// The best monster of an open map a bot of this level still gets the item from (the market asked before).
	TPlayerBotDkPick PickPlayerBotDkSource(LPCHARACTER ch, DWORD vnum)
	{
		TPlayerBotDkPick pick;
		const TPlayerBotDropKnow& k = s_kPlayerBotDropKnow;
		std::map<DWORD, std::vector<TPlayerBotDkSource> >::const_iterator src = k.byItem.find(vnum);
		if (!ch || src == k.byItem.end())
			return pick;
		for (size_t i = 0; i < src->second.size(); ++i)
		{
			const TPlayerBotDkSource& s = src->second[i];
			const int mobLevel = PlayerBotDkMobLevel(s.dwFrom);
			if (mobLevel <= 0 || mobLevel > (int)ch->GetLevel() + 10 ||
					PERCENT_LVDELTA(ch->GetLevel(), mobLevel) < PLAYERBOT_MATERIAL_MIN_DROP_PERCENT)
				continue;
			const float eff = s.fChance * PERCENT_LVDELTA(ch->GetLevel(), mobLevel) / 100.0f;
			std::map<DWORD, std::vector<long> >::const_iterator maps = k.mobMaps.find(s.dwFrom);
			if (maps == k.mobMaps.end())
				continue;
			for (size_t m = 0; m < maps->second.size(); ++m)
			{
				const long map = maps->second[m];
				if (!IsPlayerBotDkOpenMap(map))
					continue;
				// the map it stands on first, then one this core hosts
				const float w = eff * (map == ch->GetMapIndex() ? 4.0f : (IsPlayerBotMapHostedHere(map) ? 2.0f : 1.0f));
				if (w > pick.fChance)
				{
					pick.iChoice = DKCHOICE_FARM;
					pick.lMap = map;
					pick.dwMob = s.dwFrom;
					pick.fChance = w;
				}
			}
		}
		return pick;
	}

	// One bot's needs, each to its source (see the head of this file). forced: the test file's (every line logged).
	void LookPlayerBotDkNeeds(LPCHARACTER ch, DWORD dwNow, bool forced)
	{
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotDkBot& b = s_mapPlayerBotDkBots[pid];
		b.dwNextLook = dwNow + PLAYERBOT_DROPKNOW_NEED_MS + (DWORD)number(0, 60000);
		++s_uPlayerBotDkLooked;
		// what is missing, and for what
		std::vector<std::pair<DWORD, std::pair<int, const char*> > > needs;	// vnum, (lack, why)
		std::set<DWORD> seen;
		{
			std::set<DWORD> refine;
			CollectPlayerBotWantedMaterials(ch, refine);
			for (std::set<DWORD>::const_iterator it = refine.begin(); it != refine.end(); ++it)
				if (!IsPlayerBotSafeRefineScroll(*it) && seen.insert(*it).second)
					needs.push_back(std::make_pair(*it, std::make_pair(1, "refine")));
			std::map<DWORD, int> belt;
			CollectPlayerBotBeltMissing(ch, belt);
			for (std::map<DWORD, int>::const_iterator it = belt.begin(); it != belt.end(); ++it)
				if (seen.insert(it->first).second)
					needs.push_back(std::make_pair(it->first, std::make_pair(it->second, "belt")));
		}
		// a farm order is this pass's, the old one goes when it ran out
		std::map<DWORD, TPlayerBotDkFarm>::iterator oldFarm = s_mapPlayerBotDkFarm.find(pid);
		if (oldFarm != s_mapPlayerBotDkFarm.end() && (int)(oldFarm->second.dwUntil - dwNow) <= 0)
			s_mapPlayerBotDkFarm.erase(oldFarm);
		std::string summary;
		for (size_t i = 0; i < needs.size() && i < PLAYERBOT_DROPKNOW_NEEDS_A_BOT; ++i)
		{
			const DWORD vnum = needs[i].first;
			const int lack = needs[i].second.first;
			const int have = (int)ch->CountSpecifyItem(vnum);
			TPlayerBotDkPick pick;
			if (lack <= 0)
				pick.iChoice = DKCHOICE_BAG;
			else
			{
				const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(vnum);
				// MT2009_PLUS_BOT_MATS_FLOW_V1: a market whose last ask the bot cannot pay is not its source (Zab Orka at
				// 1-9 million a piece against purses of 0.6-5 million, the 2.x analyses of 6 November)
				if (e && e->dwSupplyUnits > 0 && !IsPlayerBotMatsMarketUnaffordable(ch, vnum, lack))
					pick.iChoice = DKCHOICE_MARKET;
				else
					pick = PickPlayerBotDkSource(ch, vnum);
			}
			++s_auPlayerBotDkChoices[pick.iChoice];
			if (pick.iChoice == DKCHOICE_FARM && !s_mapPlayerBotDkFarm.count(pid))
			{
				TPlayerBotDkFarm& f = s_mapPlayerBotDkFarm[pid];
				f.lMap = pick.lMap;
				f.dwMob = pick.dwMob;
				f.dwVnum = vnum;
				f.dwUntil = dwNow + PLAYERBOT_DROPKNOW_FARM_MS;
			}
			char where[64];
			if (pick.iChoice == DKCHOICE_FARM)
				snprintf(where, sizeof(where), "farm:%ld/%u", pick.lMap, pick.dwMob);
			else
				snprintf(where, sizeof(where), "%s", PLAYERBOT_DKCHOICE_NAMES[pick.iChoice]);
			char line[96];
			snprintf(line, sizeof(line), "%s%u>%s", summary.empty() ? "" : ",", vnum, where);
			summary += line;
			if (forced)
				sys_log(0, "BOT_DROPKNOW: need pid=%u name=%s level=%d item=%u(%s) why=%s lack=%d have=%d source=%s chance=%.3f%%",
						pid, ch->GetName(), (int)ch->GetLevel(), vnum, PlayerBotDkItemName(vnum), needs[i].second.second,
						lack, have, where, pick.fChance * 100.0f);
		}
		if (forced || summary.empty())
		{
			b.last = summary;
			return;
		}
		// a bot's line when its choices change, or once an hour
		if (summary != b.last || dwNow - b.dwLastLog >= PLAYERBOT_DROPKNOW_RELOG_MS)
		{
			b.last = summary;
			b.dwLastLog = dwNow ? dwNow : 1;
			sys_log(0, "BOT_DROPKNOW: need pid=%u name=%s level=%d map=%ld needs=%u choices=%s", pid, ch->GetName(),
					(int)ch->GetLevel(), ch->GetMapIndex(), (unsigned int)needs.size(), summary.c_str());
		}
	}

	void LogPlayerBotDkItem(DWORD vnum)
	{
		const TPlayerBotDropKnow& k = s_kPlayerBotDropKnow;
		std::map<DWORD, std::vector<TPlayerBotDkSource> >::const_iterator src = k.byItem.find(vnum);
		std::string text;
		if (src != k.byItem.end())
			for (size_t i = 0; i < src->second.size() && text.size() < 900; ++i)
			{
				const TPlayerBotDkSource& s = src->second[i];
				std::string maps;
				std::map<DWORD, std::vector<long> >::const_iterator m = k.mobMaps.find(s.dwFrom);
				for (size_t j = 0; m != k.mobMaps.end() && j < m->second.size() && j < 4; ++j)
				{
					char mb[24];
					snprintf(mb, sizeof(mb), "%s%ld%s", maps.empty() ? "" : "/", m->second[j], IsPlayerBotDkOpenMap(m->second[j]) ? "" : "d");
					maps += mb;
				}
				char buf[128];
				snprintf(buf, sizeof(buf), "%s%u(lv%d):%.3f%%@%s", text.empty() ? "" : ",", s.dwFrom, PlayerBotDkMobLevel(s.dwFrom),
						s.fChance * 100.0f, maps.empty() ? "-" : maps.c_str());
				text += buf;
			}
		const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(vnum);
		sys_log(0, "BOT_DROPKNOW: item %u(%s) market=%u sources=%s", vnum, PlayerBotDkItemName(vnum),
				e ? e->dwSupplyUnits : 0U, text.empty() ? "-" : text.c_str());
	}

	void LogPlayerBotDkStatus()
	{
		const unsigned int* c = s_auPlayerBotDkChoices;
		sys_log(0, "BOT_DROPKNOW: status built=%d items=%u looked=%u bag=%u market=%u farm=%u none=%u farmers=%u off=%d",
				s_kPlayerBotDropKnow.bBuilt ? 1 : 0, (unsigned int)s_kPlayerBotDropKnow.byItem.size(), s_uPlayerBotDkLooked,
				c[DKCHOICE_BAG], c[DKCHOICE_MARKET], c[DKCHOICE_FARM], c[DKCHOICE_NONE],
				(unsigned int)s_mapPlayerBotDkFarm.size(), IsPlayerBotDropKnowOff() ? 1 : 0);
		LogPlayerBotMatsStatus();	// MT2009_PLUS_BOT_MATS_FLOW_V1
	}

	void RunPlayerBotDkTestFile(DWORD dwNow)
	{
		FILE* fp = fopen(PLAYERBOT_DROPKNOW_TEST_FILE, "r");
		if (!fp)
			return;
		std::vector<std::string> lines;
		char line[128];
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_DROPKNOW_TEST_FILE);
		rename(PLAYERBOT_DROPKNOW_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "", arg[64] = "";
			const int got = sscanf(lines[l].c_str(), "%31s %63s", cmd, arg);
			if (got < 1 || cmd[0] == '#')
				continue;
			if (!strcmp(cmd, "rebuild"))
				BuildPlayerBotDropKnow(dwNow);
			else if (!strcmp(cmd, "item") && got >= 2)
				LogPlayerBotDkItem((DWORD)strtoul(arg, NULL, 10));
			else if (!strcmp(cmd, "bot") && got >= 2)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID((DWORD)strtoul(arg, NULL, 10));
				if (ch && ch->IsItemLoaded())
					LookPlayerBotDkNeeds(ch, dwNow, true);
			}
			else if (!strcmp(cmd, "status"))
				LogPlayerBotDkStatus();
			else
				sys_log(0, "BOT_DROPKNOW: test unknown line=%s", lines[l].c_str());
		}
	}

	// The world's pass (CPlayerBotManager::Update): the build, the test file, the rolling need pass, the status.
	void ManagePlayerBotDropKnow(DWORD dwNow)
	{
		static DWORD s_dwStart = 0, s_dwNextPass = 0, s_dwNextFile = 0, s_dwNextStatus = 0;
		static DWORD s_dwCursor = 0;
		if (s_dwStart == 0)
			s_dwStart = dwNow ? dwNow : 1;
		if (!s_kPlayerBotDropKnow.bBuilt)
		{
			if (dwNow - s_dwStart < PLAYERBOT_DROPKNOW_FIRST_BUILD_MS)
				return;
			BuildPlayerBotDropKnow(dwNow);
		}
		else if (dwNow - s_kPlayerBotDropKnow.dwBuiltAt >= PLAYERBOT_DROPKNOW_REBUILD_MS)
			BuildPlayerBotDropKnow(dwNow);
		if ((int)(dwNow - s_dwNextFile) >= 0)
		{
			s_dwNextFile = dwNow + 5000;
			RunPlayerBotDkTestFile(dwNow);
		}
		if (s_dwNextStatus == 0 || (int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_DROPKNOW_STATUS_MS;
			LogPlayerBotDkStatus();
			// the gone bots' rows
			for (std::map<DWORD, TPlayerBotDkBot>::iterator it = s_mapPlayerBotDkBots.begin(); it != s_mapPlayerBotDkBots.end();)
			{
				if (!s_mapPlayerBotAIStates.count(it->first))
				{
					s_mapPlayerBotDkFarm.erase(it->first);
					s_mapPlayerBotDkBots.erase(it++);
				}
				else
					++it;
			}
		}
		if (IsPlayerBotDropKnowOff())
		{
			s_mapPlayerBotDkFarm.clear();
			return;
		}
		if (s_dwNextPass != 0 && (int)(dwNow - s_dwNextPass) < 0)
			return;
		s_dwNextPass = dwNow + PLAYERBOT_DROPKNOW_PASS_MS;
		// PLAYERBOT_DROPKNOW_PASS_BOTS bots on from the last pid looked at
		int done = 0, walked = 0;
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.upper_bound(s_dwCursor);
		const int total = (int)s_mapPlayerBotAIStates.size();
		while (done < PLAYERBOT_DROPKNOW_PASS_BOTS && walked < total)
		{
			if (it == s_mapPlayerBotAIStates.end())
				it = s_mapPlayerBotAIStates.begin();
			if (it == s_mapPlayerBotAIStates.end())
				break;
			++walked;
			const DWORD pid = it->first;
			s_dwCursor = pid;
			++it;
			std::map<DWORD, TPlayerBotDkBot>::const_iterator b = s_mapPlayerBotDkBots.find(pid);
			if (b != s_mapPlayerBotDkBots.end() && (int)(b->second.dwNextLook - dwNow) > 0)
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch || !ch->IsItemLoaded() || ch->IsDead() || IsPlayerBotSidekickPID(pid) || IsPlayerBotOnDungeonRun(pid))
				continue;
			LookPlayerBotDkNeeds(ch, dwNow, false);
			++done;
		}
	}
}

#else

namespace
{
	bool IsPlayerBotDropKnowFarmMob(LPCHARACTER, DWORD) { return false; }
	void ManagePlayerBotDropKnow(DWORD) {}
}

#endif

#endif
