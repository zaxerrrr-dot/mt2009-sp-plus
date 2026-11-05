#ifndef __INC_METIN2_PLAYERBOT_DROPKI_H__
#define __INC_METIN2_PLAYERBOT_DROPKI_H__

// MT2009_PLUS_BOT_DROPKI_V1 - "Dropki", the drop farmers of the Yohara dungeons (the owner, night of 5/6 November 2026:
// "Zrob tez nowe Dropki. Na kazdy wazny loch powinny byc Dropki, ktorych cala rozgrywka jest nastawiona na zbudowanie
// idealnej postaci pod dany loch Yohary. Gdy dojda do odpowiedniego Poziomu Czempiona pod dany loch, robia go 24/7 -
// non stop na ile pozwalaja limity. Od razu wystawiaja caly drop na sprzedaz, rozwijaja postac za yang, zeby robic loch
// szybciej. Jak nie ma ulepszaczy do ekwipunku w miescie - robia je sami w przerwach miedzy lochami. Takie Dropki na
// wszystkie lochy Yohary").
//
// The rows (PLAYERBOT_DROPKI_DGS): Erebu, Zaklety Las (SZC), Grota Wygnancow 2 / Twierdza Czerwonego Smoka / Straznica
// Nemere (SZC), the Awakened Bosses (Beran, Razador, Nemere, Jotun), Swiatynia Wezy, Glebie Polnocnego Wiatru (weak,
// strong), Jaskinie Gnolli and Schronienie Meley (game1, the helmets' materials), and Wieza Sung Mahi ("wieza_smh", solo -
// a "party" of one: MT2009_PLUS_BOT_WIEZA_V1, playerbot_dgrun_wieza.h - the quest lets a bot's own climb in now; the file
// takes "wieza" for it as well). Not here: Krypta Balathora
// - a guild's registered lair (playerbot_balathor_bots.h, the bot guilds go); Labirynt - once a character; Obrona Statku -
// the Hydra cohort's fixed parties.
//
// A Dropki is a bot of the core that hosts its dungeon with a role (the quest flag mt2009_dropki.dg = the row's id, kept
// over restarts and trips): the roles pass (PLAYERBOT_DROPKI_ROLE_MS) gives each row its count (the file, else the row's
// default) from this core's bots - first those whose level is nearest the dungeon's (from PLAYERBOT_DROPKI_LEVEL_REACH
// under it), then the strongest (ScorePlayerBotYdg), a healing Shaman per party and the Nemere rows' Ninja first, in the
// kingdom with the most of them (a party is one kingdom's); never a training party's member (playerbot_ydg_train), the
// Hydra's or Erebu's trainees, a Meley visitor or a sidekick; an SZC resident only for Zaklety Las. Over the count, the
// least fit lose the role.
//
// The ideal build of a row (GetPlayerBotDropkiTarget): the dungeon's level (the bots' floor of the row) up to the world's
// top, its Champion level (PLAYERBOT_DROPKI_DGS' rough ladder by the dungeons' Sung Ma asks), the map's Sung Ma
// requirement (champion::MapRequirement - the server's sungma_table / the instance's), the weapon and armour of the
// dungeon's level - 20 (100 for the 120 ones), the boss's element (the panel's boss, its race flags) for the log. A Dropki
// is READY with the guard's asks met (the level, a Champion level, Glebie's / Gnolle's rules - CanPlayerBotDoDkDef), a
// weapon and an armour of the gear floor and PLAYERBOT_DROPKI_SUNGMA_READY_PCT of each Sung Ma stat (the YDG runs fill
// the rest for the run - BuffPlayerBotYdgSungma), IDEAL with all of it. Until ready it lives as every bot (its Sung Ma
// maps level it), only aimed: its Champion points go to its dungeon's Sung Ma first (ChoosePlayerBotSungmaStat ->
// ChoosePlayerBotDropkiSungmaStat), its GEAR2 / craft purchases may take PLAYERBOT_DROPKI_PURSE_PCT of its spare purse
// (not the 40%), the gap logged (BOT_DROPKI gap).
//
// Ready (and not over its dungeon's day - Meley's five, Erebu's 2 h): ACTIVE - a training member to every other pass
// (IsPlayerBotYdgTrainee: no clock call, no other planner, kept on the core between runs). The active Dropki of a row and
// a kingdom stand in parties (size by the row; a healing Shaman where the rule asks one, a Ninja for the Nemere rows),
// refilled from the free ones; a party calls its dungeon (OpenPlayerBotDgRun - the same run as every bot run: the entry,
// its ticket / keys / fee paid by the dungeon's charge, the day's count, the quest's stages) as soon as it is out of its
// rest (PLAYERBOT_DROPKI_REST_*) and its members are free - up to PLAYERBOT_DROPKI_WAIT_MS for the late ones - within
// the Dropki's own caps (the file's "cap", default PLAYERBOT_DROPKI_MAX_RUNS at once on the core, PLAYERBOT_DROPKI_PER_DG
// of one dungeon), the dungeons with the drop knowledge's demand first (playerbot_dropknow.h), then the longest waiting.
// Glebie (strong): a party with a member short of the three weak runs goes to the weak one first.
//
// Between runs (ManagePlayerBotDropkiBot):
//   * the drop for sale at once: PLAYERBOT_DROPKI_SELL_GOODS lines a counter would take (or a full bag) - a counter on this
//     core is served now (its next service due); a Yohara resident goes home on a trade trip ("dropki", the Sung Ma trade
//     trip's road: its counter served, the stands browsed, back to its map), at most PLAYERBOT_DROPKI_SALE_TRIPS of them
//     away, one of a party, every PLAYERBOT_DROPKI_SALE_GAP_MS. What it keeps: its own plans' materials
//     (IsPlayerBotKeptCraftGoods). The market's guards: a dungeon drop a Dropki would list while the world's counters hold
//     PLAYERBOT_DROPKI_FLOOD_UNITS of it stays off its counter (IsPlayerBotDropkiFloodHeld), and its line never asks less
//     than PLAYERBOT_DROPKI_PRICE_FLOOR_PCT of the bots' asking price (ApplyPlayerBotDropkiPriceFloor);
//   * the yang into the character: the purse above, the anvil and the crafts' errands as every bot;
//   * a material break: a refine / GEAR2 material it lacks that no counter holds, whose best source (the drop knowledge) is
//     a monster of a map this core hosts - out of its party for PLAYERBOT_DROPKI_BREAK_MS, to a living one of them (the
//     drop knowledge's farm order makes it the bot's target); one of a party at a time, every PLAYERBOT_DROPKI_BREAK_GAP_MS.
//
// The operator: the file playerbot_dropki in the core's directory (read every 30 s when it changed; kept):
//     <dungeon> <count> [size]   that many Dropki of the row on this core (0: none), its parties' size
//     cap <runs> [per_dungeon]   the Dropki's runs at once on the core / of one dungeon
//     sell <lines>               the goods that send a Dropki to sell
//     off                        no Dropki (the roles stay in the flags, nobody held)
//     # ...                      a comment
// .env: PLAYERBOT_DROPKI (1; 0 off), PLAYERBOT_DROPKI_MAX_RUNS (10), PLAYERBOT_DROPKI_PER_DG (2), PLAYERBOT_DROPKI_SALE_TRIPS
// (6), PLAYERBOT_DROPKI_FLOOD_UNITS (300), PLAYERBOT_DROPKI_PRICE_FLOOR_PCT (70), PLAYERBOT_DROPKI_PURSE_PCT (70). Event flag
// m2_bot_dropki_off 1: no new call, nobody held. The test file playerbot_dropki_test (renamed .done): status, roles,
// now <dungeon>.
//
// The log: BOT_DROPKI lines - config, target (a row's ideal build), role (assigned / restored / released), gap, party
// (formed / refilled / disbanded), called, run end (result, won, time, the members' gold and items), sale (counter / trip),
// break, status every PLAYERBOT_DROPKI_STATUS_MS (a row's roles, online, ready, ideal, active, parties, running, runs,
// wins, gold, items) - and the BOT_DGRUN / BOT_YDG lines of every run.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_dropknow.h, in the anonymous namespace.

namespace
{
	struct TPlayerBotDropkiDg
	{
		int iId;		// the flag's value (stable)
		const char* szKey;	// the PLAYERBOT_DGRUN_DEFS row
		int iDefault;		// Dropki on the core hosting it
		int iSize;		// a party (1: alone)
		int iChampion;		// the ideal Champion level (rough: the dungeons' Sung Ma asks)
		const char* szPrep;	// the row its party runs while a member lacks the guard's ask (Glebie strong: the weak one)
	};

	const TPlayerBotDropkiDg PLAYERBOT_DROPKI_DGS[] = {
		{ 1, "erebu", 10, 5, 8, NULL },
		{ 2, "jotun_szc", 10, 5, 6, NULL },
		{ 3, "beran_szc", 10, 5, 14, NULL },
		{ 4, "razador_szc", 10, 5, 14, NULL },
		{ 5, "nemere_szc", 10, 5, 16, NULL },
		{ 6, "beran_pb", 10, 5, 10, NULL },
		{ 7, "razador_pb", 10, 5, 10, NULL },
		{ 8, "nemere_pb", 10, 5, 12, NULL },
		{ 9, "jotun_pb", 10, 5, 12, NULL },
		{ 10, "swiatynia", 10, 5, 18, NULL },
		{ 11, "glebie_slaby", 10, 5, 20, NULL },
		{ 12, "glebie_silny", 10, 5, 26, "glebie_slaby" },
		{ 13, "gnolle", 10, 5, 16, NULL },
		{ 14, "meley", 10, 6, 0, NULL },
		// MT2009_PLUS_BOT_WIEZA_V1: Wieza Sung Mahi - a solo climb (size 1), the bots' runner playerbot_dgrun_wieza.h
		{ 15, "wieza_smh", 10, 1, 20, NULL },
	};
	const int PLAYERBOT_DROPKI_DG_COUNT = (int)(sizeof(PLAYERBOT_DROPKI_DGS) / sizeof(PLAYERBOT_DROPKI_DGS[0]));

	const DWORD PLAYERBOT_DROPKI_PLAN_MS = 10 * 1000;
	const DWORD PLAYERBOT_DROPKI_FILE_MS = 30 * 1000;
	const DWORD PLAYERBOT_DROPKI_FIRST_ROLES_MS = 4 * 60 * 1000;	// the bots logged in, the YDG / Erebu trainings formed
	const DWORD PLAYERBOT_DROPKI_ROLE_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_CHECK_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_GAP_LOG_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_STATUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_REST_MIN_MS = 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_REST_SPREAD_MS = 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_WAIT_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_SALE_GAP_MS = 40 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_BREAK_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_BREAK_GAP_MS = 45 * 60 * 1000;
	const DWORD PLAYERBOT_DROPKI_TRIP_LOST_MS = 90 * 60 * 1000;
	const int PLAYERBOT_DROPKI_LEVEL_REACH = 15;
	const int PLAYERBOT_DROPKI_SUNGMA_READY_PCT = 70;
	const int PLAYERBOT_DROPKI_SELL_GOODS = 6;
	const char* const PLAYERBOT_DROPKI_FILE = "playerbot_dropki";
	const char* const PLAYERBOT_DROPKI_TEST_FILE = "playerbot_dropki_test";
	const char* const PLAYERBOT_DROPKI_FLAG = "mt2009_dropki.dg";

	struct TPlayerBotDropkiConfig
	{
		bool bFile, bOff;
		int count[PLAYERBOT_DROPKI_DG_COUNT];
		int size[PLAYERBOT_DROPKI_DG_COUNT];
		int capTotal, capPerDg, sellGoods;
		TPlayerBotDropkiConfig() : bFile(false), bOff(false), capTotal(0), capPerDg(0), sellGoods(PLAYERBOT_DROPKI_SELL_GOODS)
		{
			for (int i = 0; i < PLAYERBOT_DROPKI_DG_COUNT; ++i)
			{
				count[i] = PLAYERBOT_DROPKI_DGS[i].iDefault;
				size[i] = PLAYERBOT_DROPKI_DGS[i].iSize;
			}
		}
	};
	TPlayerBotDropkiConfig s_kPlayerBotDropkiCfg;

	struct TPlayerBotDropkiBot
	{
		int iDg;
		bool bReady, bIdeal, bDayDone;
		DWORD dwNextCheck, dwNextGapLog, dwSince;
		DWORD dwNextSale, dwSaleAt, dwBreakUntil, dwNextBreak;
		int iParty;
		unsigned int runs, wins;
		long long llGold;
		int iItems;
		std::string gap;
		TPlayerBotDropkiBot() : iDg(-1), bReady(false), bIdeal(false), bDayDone(false), dwNextCheck(0), dwNextGapLog(0), dwSince(0),
			dwNextSale(0), dwSaleAt(0), dwBreakUntil(0), dwNextBreak(0), iParty(0), runs(0), wins(0), llGold(0), iItems(0) {}
	};
	std::map<DWORD, TPlayerBotDropkiBot> s_mapPlayerBotDropki;

	struct TPlayerBotDropkiParty
	{
		int iId, iDg;
		BYTE bEmpire;
		std::vector<DWORD> pids;
		int iRun;
		DWORD dwRestUntil, dwWaitSince, dwLastCall;
		unsigned int runs, wins;
		std::string last;
		TPlayerBotDropkiParty() : iId(0), iDg(-1), bEmpire(0), iRun(0), dwRestUntil(0), dwWaitSince(0), dwLastCall(0), runs(0), wins(0) {}
	};
	std::vector<TPlayerBotDropkiParty> s_vecPlayerBotDropkiParties;
	int s_iPlayerBotDropkiNextParty = 1;
	std::map<int, int> s_mapPlayerBotDropkiRunParty;	// run -> party id
	struct TPlayerBotDropkiSnap
	{
		long long gold;
		int items;
	};
	std::map<int, std::map<DWORD, TPlayerBotDropkiSnap> > s_mapPlayerBotDropkiSnaps;
	std::map<DWORD, DWORD> s_mapPlayerBotDropkiTripOut;	// pid -> when it left on a sale trip (this core)

	struct TPlayerBotDropkiStats
	{
		unsigned int called, entered, won, saleCounter, saleTrips, breaks;
		long long gold;
		int items;
		TPlayerBotDropkiStats() : called(0), entered(0), won(0), saleCounter(0), saleTrips(0), breaks(0), gold(0), items(0) {}
	};
	TPlayerBotDropkiStats s_akPlayerBotDropkiStats[PLAYERBOT_DROPKI_DG_COUNT];

	// ------------------------------------------------------------ the switches and the file

	int GetPlayerBotDropkiEnv(const char* name, int def, int lo, int hi)
	{
		return ReadPlayerBotYoharaEnvInt(name, def, lo, hi);
	}

	// The switches (the event flag looked at once a second - asked by every pass that asks IsPlayerBotYdgTrainee).
	bool IsPlayerBotDropkiOn()
	{
		static int s_iOn = -1;
		if (s_iOn < 0)
			s_iOn = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI", 1, 0, 1);
		static DWORD s_dwAt = 0;
		static bool s_bFlagOff = false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			s_bFlagOff = quest::CQuestManager::instance().GetEventFlag("m2_bot_dropki_off") != 0;
		}
		return s_iOn == 1 && !s_kPlayerBotDropkiCfg.bOff && !s_bFlagOff;
	}

	int FindPlayerBotDropkiDg(const char* key)
	{
		if (key && !strcmp(key, "wieza"))	// MT2009_PLUS_BOT_WIEZA_V1: the operator's short name of Wieza Sung Mahi
			key = "wieza_smh";
		for (int i = 0; i < PLAYERBOT_DROPKI_DG_COUNT; ++i)
			if (!strcmp(PLAYERBOT_DROPKI_DGS[i].szKey, key))
				return i;
		return -1;
	}

	int FindPlayerBotDropkiDgById(int id)
	{
		for (int i = 0; i < PLAYERBOT_DROPKI_DG_COUNT; ++i)
			if (PLAYERBOT_DROPKI_DGS[i].iId == id)
				return i;
		return -1;
	}

	// The row's PLAYERBOT_DGRUN_DEFS index, or -1 (no runner: the tower).
	int GetPlayerBotDropkiDef(int dg)
	{
		if (dg < 0 || dg >= PLAYERBOT_DROPKI_DG_COUNT)
			return -1;
		const int def = ParsePlayerBotDgRunKey(PLAYERBOT_DROPKI_DGS[dg].szKey);
		if (def < 0)
			return -1;
		const BYTE kind = PLAYERBOT_DGRUN_DEFS[def].bKind;
		return kind == DGRUN_KIND_TOWER || kind == DGRUN_KIND_HYDRA ? -1 : def;
	}

	bool IsPlayerBotDropkiDgHere(int dg)
	{
		const int def = GetPlayerBotDropkiDef(dg);
		return def >= 0 && IsPlayerBotMapHostedHere(PLAYERBOT_DGRUN_DEFS[def].lMap) &&
				SECTREE_MANAGER::instance().GetMap(PLAYERBOT_DGRUN_DEFS[def].lMap);
	}

	int GetPlayerBotDropkiCapTotal()
	{
		static int s_iCap = -1;
		if (s_iCap < 0)
			s_iCap = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_MAX_RUNS", 10, 0, 60);
		return s_kPlayerBotDropkiCfg.capTotal > 0 ? s_kPlayerBotDropkiCfg.capTotal : s_iCap;
	}

	int GetPlayerBotDropkiCapPerDg()
	{
		static int s_iCap = -1;
		if (s_iCap < 0)
			s_iCap = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_PER_DG", 2, 0, 20);
		return s_kPlayerBotDropkiCfg.capPerDg > 0 ? s_kPlayerBotDropkiCfg.capPerDg : s_iCap;
	}

	void ReadPlayerBotDropkiFile(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		static time_t s_tMtime = (time_t)-1;
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_DROPKI_FILE_MS;
		struct stat st;
		const time_t mtime = stat(PLAYERBOT_DROPKI_FILE, &st) == 0 ? st.st_mtime : (time_t)0;
		if (mtime == s_tMtime)
			return;
		s_tMtime = mtime;
		TPlayerBotDropkiConfig c;
		FILE* fp = mtime ? fopen(PLAYERBOT_DROPKI_FILE, "r") : NULL;
		if (fp)
		{
			c.bFile = true;
			char line[160];
			while (fgets(line, sizeof(line), fp))
			{
				char cmd[48] = "";
				int a = 0, b = 0;
				const int got = sscanf(line, "%47s %d %d", cmd, &a, &b);
				if (got < 1 || cmd[0] == '#')
					continue;
				if (!strcmp(cmd, "off"))
					c.bOff = true;
				else if (!strcmp(cmd, "cap") && got >= 2)
				{
					c.capTotal = std::max(0, std::min(a, 60));
					if (got >= 3)
						c.capPerDg = std::max(0, std::min(b, 20));
				}
				else if (!strcmp(cmd, "sell") && got >= 2)
					c.sellGoods = std::max(1, std::min(a, 60));
				else
				{
					const int dg = FindPlayerBotDropkiDg(cmd);
					if (dg < 0 || got < 2)
					{
						sys_log(0, "BOT_DROPKI: file line unknown: %s", line);
						continue;
					}
					if (GetPlayerBotDropkiDef(dg) < 0 && a > 0)
					{
						sys_log(0, "BOT_DROPKI: file line refused: %s has no bot runner here", cmd);
						a = 0;
					}
					c.count[dg] = std::max(0, std::min(a, 80));
					if (got >= 3)
						c.size[dg] = std::max(1, std::min(b, playerbot_dgrun::PARTY_MAX));
				}
			}
			fclose(fp);
		}
		s_kPlayerBotDropkiCfg = c;
		std::string rows;
		for (int i = 0; i < PLAYERBOT_DROPKI_DG_COUNT; ++i)
		{
			if (!IsPlayerBotDropkiDgHere(i) || c.count[i] <= 0)
				continue;
			char buf[48];
			snprintf(buf, sizeof(buf), "%s%s:%d/%d", rows.empty() ? "" : ",", PLAYERBOT_DROPKI_DGS[i].szKey, c.count[i], c.size[i]);
			rows += buf;
		}
		sys_log(0, "BOT_DROPKI: config file=%d off=%d on=%d cap=%d per_dungeon=%d sell=%d rows_here=%s", c.bFile ? 1 : 0, c.bOff ? 1 : 0,
				IsPlayerBotDropkiOn() ? 1 : 0, GetPlayerBotDropkiCapTotal(), GetPlayerBotDropkiCapPerDg(), c.sellGoods,
				rows.empty() ? "-" : rows.c_str());
	}

	// ------------------------------------------------------------ the ideal build

	struct TPlayerBotDropkiTarget
	{
		int minLevel, level, champion, gearMin, gearIdeal;
		int sungma[4];
		bool hasSungma;
		const char* element;
	};

	const char* PlayerBotDropkiBossElement(int def)
	{
		const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey(PLAYERBOT_DGRUN_DEFS[def].szKey);
		const CMob* mob = panel && panel->boss ? CMobManager::instance().Get(panel->boss) : NULL;
		if (!mob)
			return "-";
		static const DWORD flags[6] = { RACE_FLAG_ATT_FIRE, RACE_FLAG_ATT_ELEC, RACE_FLAG_ATT_ICE, RACE_FLAG_ATT_TEMPLE,
				RACE_FLAG_ATT_EARTH, RACE_FLAG_ATT_DARK };
		static const char* const names[6] = { "fire", "lightning", "ice", "wind", "earth", "dark" };
		for (int i = 0; i < 6; ++i)
			if (mob->m_table.dwRaceFlag & flags[i])
				return names[i];
		return "none";
	}

	TPlayerBotDropkiTarget GetPlayerBotDropkiTarget(int dg)
	{
		TPlayerBotDropkiTarget t;
		memset(&t, 0, sizeof(t));
		t.element = "-";
		const int def = GetPlayerBotDropkiDef(dg);
		if (def < 0)
			return t;
		t.minLevel = GetPlayerBotDkDefMinLevel(def);
		t.level = std::min((int)gPlayerMaxLevel, t.minLevel + 5);
		t.champion = PLAYERBOT_DROPKI_DGS[dg].iChampion;
		t.gearMin = GetPlayerBotDropkiEnv("PLAYERBOT_YDG_MIN_GEAR_LEVEL", 75, 0, 250);
		t.gearIdeal = std::max(t.gearMin, t.minLevel - 20);
		// the map's Sung Ma ask (Jaskinie Gnolli: the deepest of its three levels)
		std::vector<long> maps;
		GetPlayerBotDkDefMaps(def, maps);
		for (size_t m = 0; m < maps.size(); ++m)
		{
			const champion::SungmaRequirement* req = champion::MapRequirement(maps[m]);
			if (!req)
				continue;
			t.hasSungma = true;
			t.sungma[0] = std::max(t.sungma[0], req->str);
			t.sungma[1] = std::max(t.sungma[1], req->hp);
			t.sungma[2] = std::max(t.sungma[2], req->move);
			t.sungma[3] = std::max(t.sungma[3], req->immune);
		}
		t.element = PlayerBotDropkiBossElement(def);
		return t;
	}

	void LogPlayerBotDropkiTargets()
	{
		for (int dg = 0; dg < PLAYERBOT_DROPKI_DG_COUNT; ++dg)
		{
			if (!IsPlayerBotDropkiDgHere(dg))
				continue;
			const TPlayerBotDropkiTarget t = GetPlayerBotDropkiTarget(dg);
			sys_log(0, "BOT_DROPKI: target dungeon=%s count=%d size=%d min_level=%d level=%d champion=%d sungma=%d/%d/%d/%d gear=%d/%d "
					"element=%s bonuses=monster,%s_attack,%s_resist,crit,pierce notable=%s",
					PLAYERBOT_DROPKI_DGS[dg].szKey, s_kPlayerBotDropkiCfg.count[dg], s_kPlayerBotDropkiCfg.size[dg], t.minLevel, t.level,
					t.champion, t.sungma[0], t.sungma[1], t.sungma[2], t.sungma[3], t.gearMin, t.gearIdeal, t.element, t.element, t.element,
					DescribePlayerBotDkDungeon(GetPlayerBotDropkiDef(dg), 6).c_str());
		}
	}

	int GetPlayerBotDropkiGearLevel(LPCHARACTER ch)
	{
		LPITEM w = ch->GetWear(WEAR_WEAPON);
		LPITEM b = ch->GetWear(WEAR_BODY);
		if (!w || !b)
			return 0;
		return std::min((int)w->GetLevelLimit(), (int)b->GetLevelLimit());
	}

	// Ready / ideal and the gap ("lv118/120 ch6/20 sm str40/60,... gear90/100"); the day's limits.
	void CheckPlayerBotDropki(LPCHARACTER ch, TPlayerBotDropkiBot& b, DWORD dwNow)
	{
		b.dwNextCheck = dwNow + PLAYERBOT_DROPKI_CHECK_MS;
		const int dg = b.iDg;
		const int def = GetPlayerBotDropkiDef(dg);
		if (def < 0)
		{
			b.bReady = b.bIdeal = false;
			return;
		}
		const TPlayerBotDropkiTarget t = GetPlayerBotDropkiTarget(dg);
		const int level = ch->GetLevel(), champion = GetPlayerBotChampionLevel(ch), gear = GetPlayerBotDropkiGearLevel(ch);
		std::string gap;
		char buf[96];
		bool smReady = true, smIdeal = true;
		if (t.hasSungma)
		{
			static const char* const names[4] = { "str", "hp", "move", "immune" };
			for (int k = 0; k < 4; ++k)
			{
				const int have = yohara_gear::SungmaEffective(ch, (unsigned char)(POINT_SUNGMA_STR + k));
				if (have * 100 < t.sungma[k] * PLAYERBOT_DROPKI_SUNGMA_READY_PCT)
					smReady = false;
				if (have < t.sungma[k])
				{
					smIdeal = false;
					snprintf(buf, sizeof(buf), "%s%s%d/%d", gap.empty() ? "sm:" : ",", names[k], have, t.sungma[k]);
					gap += buf;
				}
			}
		}
		if (level < t.level)
		{
			snprintf(buf, sizeof(buf), " lv%d/%d", level, t.level);
			gap += buf;
		}
		if (champion < t.champion)
		{
			snprintf(buf, sizeof(buf), " ch%d/%d", champion, t.champion);
			gap += buf;
		}
		if (gear < t.gearIdeal)
		{
			snprintf(buf, sizeof(buf), " gear%d/%d", gear, t.gearIdeal);
			gap += buf;
		}
		// the guard's asks: its own row, or the prep row (Glebie strong: the weak one first)
		bool guard = CanPlayerBotDoDkDef(ch, def);
		if (!guard && PLAYERBOT_DROPKI_DGS[dg].szPrep)
			guard = CanPlayerBotDoDkDef(ch, ParsePlayerBotDgRunKey(PLAYERBOT_DROPKI_DGS[dg].szPrep));
		const bool gearOk = gear >= t.gearMin;
		b.bReady = guard && gearOk && smReady && level >= t.minLevel;
		b.bIdeal = b.bReady && smIdeal && level >= t.level && champion >= t.champion && gear >= t.gearIdeal;
		if (!guard)
			gap += " guard";
		if (!gearOk)
			gap += " gear_floor";
		// over the dungeon's day (Meley's five; Erebu's two hours, a person's): not held, back tomorrow / after it
		const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
		b.bDayDone = false;
		if (info.bKind != DGRUN_KIND_YDG && info.iDaily > 0 && GetPlayerBotDgRunRunsToday(ch, info) >= info.iDaily)
			b.bDayDone = true;
		if (info.bKind == DGRUN_KIND_EREBU)
		{
			const mt2009_dpanel::Def* panel = mt2009_dpanel::FindKey(info.szKey);
			if (panel && mt2009_dpanel::CooldownLeft(ch, *panel) > 5 * 60)
				b.bDayDone = true;
		}
		if (b.bDayDone)
			gap += " day_done";
		b.gap = gap.empty() ? "-" : gap;
		if (b.dwNextGapLog == 0 || (int)(dwNow - b.dwNextGapLog) >= 0)
		{
			b.dwNextGapLog = dwNow + PLAYERBOT_DROPKI_GAP_LOG_MS;
			sys_log(0, "BOT_DROPKI: gap pid=%u name=%s dungeon=%s ready=%d ideal=%d level=%d champion=%d gear=%d gold=%lld runs=%u gap=%s",
					ch->GetPlayerID(), ch->GetName(), PLAYERBOT_DROPKI_DGS[dg].szKey, b.bReady ? 1 : 0, b.bIdeal ? 1 : 0, level, champion,
					gear, (long long)ch->GetGold(), b.runs, b.gap.c_str());
		}
	}

	// ------------------------------------------------------------ the questions others ask

	bool IsPlayerBotDropkiRole(DWORD pid)
	{
		return !s_mapPlayerBotDropki.empty() && s_mapPlayerBotDropki.count(pid) != 0;
	}

	// Held for its dungeon: ready, out of its day's limit and its break, the switch on, no operator's training of it.
	bool IsPlayerBotDropkiActive(DWORD pid)
	{
		if (s_mapPlayerBotDropki.empty())
			return false;
		std::map<DWORD, TPlayerBotDropkiBot>::const_iterator it = s_mapPlayerBotDropki.find(pid);
		if (it == s_mapPlayerBotDropki.end() || !it->second.bReady || it->second.bDayDone)
			return false;
		if (it->second.dwBreakUntil && (int)(it->second.dwBreakUntil - get_dword_time()) > 0)
			return false;
		if (s_setPlayerBotYdgTrainees.count(pid))
			return false;
		return IsPlayerBotDropkiOn();
	}

	int GetPlayerBotDropkiPursePercent(LPCHARACTER ch, int base)
	{
		if (!ch || !IsPlayerBotDropkiRole(ch->GetPlayerID()) || !IsPlayerBotDropkiOn())
			return base;
		static int s_iPct = -1;
		if (s_iPct < 0)
			s_iPct = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_PURSE_PCT", 70, 10, 95);
		return std::max(base, s_iPct);
	}

	// Its Champion points: its dungeon's Sung Ma ask first (the biggest gap; Sila first on a tie). -1: the usual choice.
	int ChoosePlayerBotDropkiSungmaStat(LPCHARACTER ch)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		if (!ch)
			return -1;
		std::map<DWORD, TPlayerBotDropkiBot>::const_iterator it = s_mapPlayerBotDropki.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDropki.end() || !IsPlayerBotDropkiOn())
			return -1;
		const TPlayerBotDropkiTarget t = GetPlayerBotDropkiTarget(it->second.iDg);
		if (!t.hasSungma)
			return -1;
		static const BYTE s_aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
		static const int order[4] = { 0, 2, 1, 3 };
		int best = -1, bestGap = 0;
		for (int k = 0; k < 4; ++k)
		{
			const int i = order[k];
			if (ch->GetRealPoint(s_aPoint[i]) >= (int)champion::STAT_MAX)
				continue;
			const int gap = t.sungma[i] - GetPlayerBotSungmaWill(ch, i);
			if (gap > bestGap)
			{
				best = i;
				bestGap = gap;
			}
		}
		return best;
#else
		(void)ch;
		return -1;
#endif
	}

	// A dungeon drop of its own row the world's counters hold enough of stays off a Dropki's counter.
	bool IsPlayerBotDropkiFloodHeld(LPCHARACTER owner, LPITEM item)
	{
		if (!owner || !item || !owner->IsPC())
			return false;
		std::map<DWORD, TPlayerBotDropkiBot>::const_iterator it = s_mapPlayerBotDropki.find(owner->GetPlayerID());
		if (it == s_mapPlayerBotDropki.end())
			return false;
		static int s_iUnits = -1;
		if (s_iUnits < 0)
			s_iUnits = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_FLOOD_UNITS", 300, 10, 100000);
		const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(item->GetVnum());
		if (!e || (int)e->dwSupplyUnits < s_iUnits)
			return false;
		const int def = GetPlayerBotDropkiDef(it->second.iDg);
		std::map<int, std::vector<TPlayerBotDkDrop> >::const_iterator drops = s_kPlayerBotDropKnow.dungeonDrops.find(def);
		if (drops == s_kPlayerBotDropKnow.dungeonDrops.end())
			return false;
		for (size_t i = 0; i < drops->second.size(); ++i)
			if (drops->second[i].dwItem == item->GetVnum())
			{
				PlayerBotLogThrottled("dropki_flood", get_dword_time(), "BOT_DROPKI: flood hold pid=%u name=%s vnum=%u supply=%u cap=%d",
						owner->GetPlayerID(), owner->GetName(), item->GetVnum(), e->dwSupplyUnits, s_iUnits);
				return true;
			}
		return false;
	}

	// A Dropki's line never under PLAYERBOT_DROPKI_PRICE_FLOOR_PCT of the bots' asking price (the markdowns, the glut).
	DWORD ApplyPlayerBotDropkiPriceFloor(LPITEM item, DWORD asking, DWORD price)
	{
		if (!item || asking == 0)
			return price;
		LPCHARACTER owner = item->GetOwner();
		if (!owner || !IsPlayerBotDropkiRole(owner->GetPlayerID()))
			return price;
		static int s_iPct = -1;
		if (s_iPct < 0)
			s_iPct = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_PRICE_FLOOR_PCT", 70, 10, 100);
		const unsigned long long floor = (unsigned long long)asking * (unsigned long long)s_iPct / 100ULL;
		return (unsigned long long)price < floor ? (DWORD)std::min<unsigned long long>(floor, 0xFFFFFFFEULL) : price;
	}

	// ------------------------------------------------------------ the roles

	long long ScorePlayerBotDropkiFit(LPCHARACTER ch, int minLevel)
	{
		// nearest the dungeon's level first (under it counts double), then the strongest
		const int d = (int)ch->GetLevel() - minLevel;
		const long long away = d >= 0 ? d : -2 * d;
		return -away * 100000000LL + ScorePlayerBotYdg(ch);
	}

	bool IsPlayerBotDropkiCandidate(DWORD pid, LPCHARACTER ch, int dg)
	{
		if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
			return false;
		if (IsPlayerBotSidekickPID(pid) || s_setPlayerBotYdgTrainees.count(pid) || IsPlayerBotYoharaHydraResident(pid) ||
				IsPlayerBotErebuTrainee(pid) || IsPlayerBotMeleyVisitor(pid) || IsPlayerBotWiezaTrainee(pid))	// MT2009_PLUS_BOT_WIEZA_V1
			return false;
		const int def = GetPlayerBotDropkiDef(dg);
		if (def < 0)
			return false;
		// a bot the handover brought for the Time Rift only for Zaklety Las
		if (IsPlayerBotYoharaSzcResident(pid) && PLAYERBOT_DGRUN_DEFS[def].bKind != DGRUN_KIND_SZC)
			return false;
		return (int)ch->GetLevel() + PLAYERBOT_DROPKI_LEVEL_REACH >= GetPlayerBotDkDefMinLevel(def);
	}

	void SetPlayerBotDropkiRole(LPCHARACTER ch, int dg, const char* why, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		if (dg < 0)
		{
			std::map<DWORD, TPlayerBotDropkiBot>::iterator it = s_mapPlayerBotDropki.find(pid);
			if (it != s_mapPlayerBotDropki.end())
				sys_log(0, "BOT_DROPKI: role released pid=%u name=%s dungeon=%s why=%s runs=%u wins=%u", pid, ch->GetName(),
						PLAYERBOT_DROPKI_DGS[it->second.iDg].szKey, why, it->second.runs, it->second.wins);
			s_mapPlayerBotDropki.erase(pid);
			ch->SetQuestFlag(PLAYERBOT_DROPKI_FLAG, 0);
			return;
		}
		TPlayerBotDropkiBot& b = s_mapPlayerBotDropki[pid];
		const bool restored = !strcmp(why, "restored");
		b = TPlayerBotDropkiBot();
		b.iDg = dg;
		b.dwSince = dwNow ? dwNow : 1;
		if (!restored)
			ch->SetQuestFlag(PLAYERBOT_DROPKI_FLAG, PLAYERBOT_DROPKI_DGS[dg].iId);
		CheckPlayerBotDropki(ch, b, dwNow);
		sys_log(0, "BOT_DROPKI: role %s pid=%u name=%s dungeon=%s empire=%u job=%d level=%d champion=%d ready=%d ideal=%d gap=%s",
				restored ? "restored" : "assigned", pid, ch->GetName(), PLAYERBOT_DROPKI_DGS[dg].szKey, (unsigned int)ch->GetEmpire(),
				(int)(ch->GetJob() % 4), (int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), b.bReady ? 1 : 0, b.bIdeal ? 1 : 0,
				b.gap.c_str());
	}

	struct TPlayerBotDropkiPick
	{
		DWORD pid;
		long long score;
		int job;
		bool healer;
	};

	void AssignPlayerBotDropkiRoles(DWORD dwNow)
	{
		// the roles the flags hold (a restart, a trip back) and the gone ones
		std::map<DWORD, TPlayerBotDropkiBot>::iterator gone = s_mapPlayerBotDropki.begin();
		while (gone != s_mapPlayerBotDropki.end())
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(gone->first) || !s_mapPlayerBotAIStates.count(gone->first))
				s_mapPlayerBotDropki.erase(gone++);
			else
				++gone;
		}
		int have[PLAYERBOT_DROPKI_DG_COUNT];
		memset(have, 0, sizeof(have));
		std::vector<std::pair<long long, DWORD> > members[PLAYERBOT_DROPKI_DG_COUNT];
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot())
				continue;
			int dg = -1;
			std::map<DWORD, TPlayerBotDropkiBot>::const_iterator known = s_mapPlayerBotDropki.find(it->first);
			if (known != s_mapPlayerBotDropki.end())
				dg = known->second.iDg;
			else
			{
				const int id = ch->GetQuestFlag(PLAYERBOT_DROPKI_FLAG);
				dg = id > 0 ? FindPlayerBotDropkiDgById(id) : -1;
				if (dg < 0 || !IsPlayerBotDropkiDgHere(dg))
					continue;	// a role of another core's dungeon stays in its flag
				SetPlayerBotDropkiRole(ch, dg, "restored", dwNow);
			}
			if (dg < 0)
				continue;
			// an operator's training took it, or the row is gone from this core: the role goes
			if (s_setPlayerBotYdgTrainees.count(it->first) || !IsPlayerBotDropkiDgHere(dg))
			{
				SetPlayerBotDropkiRole(ch, -1, s_setPlayerBotYdgTrainees.count(it->first) ? "ydg_training" : "not_here", dwNow);
				continue;
			}
			const int def = GetPlayerBotDropkiDef(dg);
			members[dg].push_back(std::make_pair(ScorePlayerBotDropkiFit(ch, GetPlayerBotDkDefMinLevel(def)), it->first));
			++have[dg];
		}
		if (!IsPlayerBotDropkiOn())
			return;
		// over the count: the least fit go
		for (int dg = 0; dg < PLAYERBOT_DROPKI_DG_COUNT; ++dg)
		{
			const int want = IsPlayerBotDropkiDgHere(dg) ? s_kPlayerBotDropkiCfg.count[dg] : 0;
			if (have[dg] <= want)
				continue;
			std::sort(members[dg].begin(), members[dg].end());
			for (int i = 0; i < have[dg] - want && i < (int)members[dg].size(); ++i)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(members[dg][i].second);
				if (ch && !IsPlayerBotOnDungeonRun(members[dg][i].second))
					SetPlayerBotDropkiRole(ch, -1, "over_count", dwNow);
			}
		}
		// the vacancies: the hardest rows first (their bots are the rarest)
		std::vector<std::pair<int, int> > order;
		for (int dg = 0; dg < PLAYERBOT_DROPKI_DG_COUNT; ++dg)
			if (IsPlayerBotDropkiDgHere(dg) && s_kPlayerBotDropkiCfg.count[dg] > have[dg])
				order.push_back(std::make_pair(-(GetPlayerBotDkDefMinLevel(GetPlayerBotDropkiDef(dg)) * 100 + PLAYERBOT_DROPKI_DGS[dg].iChampion), dg));
		std::sort(order.begin(), order.end());
		for (size_t o = 0; o < order.size(); ++o)
		{
			const int dg = order[o].second;
			const int def = GetPlayerBotDropkiDef(dg);
			const int minLevel = GetPlayerBotDkDefMinLevel(def);
			const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor(PLAYERBOT_DGRUN_DEFS[def].szKey);
			std::vector<TPlayerBotDropkiPick> pool[4];
			int memberIn[4] = { 0, 0, 0, 0 };
			for (size_t m = 0; m < members[dg].size(); ++m)
			{
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(members[dg][m].second);
				if (c && c->GetEmpire() >= 1 && c->GetEmpire() <= 3)
					++memberIn[c->GetEmpire()];
			}
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				if (s_mapPlayerBotDropki.count(it->first))
					continue;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (!IsPlayerBotDropkiCandidate(it->first, ch, dg))
					continue;
				// a role of another core's dungeon in its flag: kept for that one
				const int id = ch->GetQuestFlag(PLAYERBOT_DROPKI_FLAG);
				if (id > 0 && FindPlayerBotDropkiDgById(id) >= 0)
					continue;
				TPlayerBotDropkiPick p;
				p.pid = it->first;
				p.score = ScorePlayerBotDropkiFit(ch, minLevel);
				p.job = ch->GetJob() % 4;
				p.healer = p.job == JOB_SHAMAN && ch->GetSkillGroup() != 0;
				pool[ch->GetEmpire()].push_back(p);
			}
			int need = s_kPlayerBotDropkiCfg.count[dg] - have[dg];
			const int size = std::max(1, s_kPlayerBotDropkiCfg.size[dg]);
			for (int round = 0; need > 0 && round < 3; ++round)
			{
				// the kingdom with the most (its members and its free)
				int e = 0;
				for (int k = 1; k <= 3; ++k)
					if (!pool[k].empty() && (e == 0 || pool[k].size() + memberIn[k] > pool[e].size() + memberIn[e]))
						e = k;
				if (e == 0)
					break;
				std::vector<TPlayerBotDropkiPick>& v = pool[e];
				std::sort(v.begin(), v.end(), [](const TPlayerBotDropkiPick& a, const TPlayerBotDropkiPick& b) { return a.score > b.score; });
				std::vector<TPlayerBotDropkiPick> take;
				const int parties = std::max(1, (need + size - 1) / size);
				// a healing Shaman per party (where the rule asks one), a Ninja per party for the Nemere rows
				for (int want = 0; want < 2; ++want)
				{
					if ((want == 0 && !rule.needHealer && size < 4) || (want == 1 && !rule.needNinja))
						continue;
					int got = 0;
					for (size_t i = 0; i < v.size() && got < parties && (int)take.size() < need;)
					{
						if ((want == 0 && v[i].healer) || (want == 1 && v[i].job == JOB_ASSASSIN))
						{
							take.push_back(v[i]);
							v.erase(v.begin() + i);
							++got;
						}
						else
							++i;
					}
				}
				int perJob[4] = { 0, 0, 0, 0 };
				for (size_t i = 0; i < take.size(); ++i)
					++perJob[take[i].job & 3];
				const int cap = std::max(2, (need + 2) / 3 + 1);
				for (size_t i = 0; i < v.size() && (int)take.size() < need;)
				{
					if (perJob[v[i].job & 3] < cap)
					{
						++perJob[v[i].job & 3];
						take.push_back(v[i]);
						v.erase(v.begin() + i);
					}
					else
						++i;
				}
				for (size_t i = 0; i < take.size(); ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(take[i].pid);
					if (!ch)
						continue;
					SetPlayerBotDropkiRole(ch, dg, "assigned", dwNow);
					++memberIn[e];
					--need;
				}
				v.clear();
			}
			if (need > 0)
				PlayerBotLogThrottled("dropki_short", dwNow, "BOT_DROPKI: role short dungeon=%s missing=%d (no free bot from level %d on this core)",
						PLAYERBOT_DROPKI_DGS[dg].szKey, need, minLevel - PLAYERBOT_DROPKI_LEVEL_REACH);
		}
	}

	// ------------------------------------------------------------ the parties

	TPlayerBotDropkiParty* FindPlayerBotDropkiParty(int id)
	{
		for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size(); ++i)
			if (s_vecPlayerBotDropkiParties[i].iId == id)
				return &s_vecPlayerBotDropkiParties[i];
		return NULL;
	}

	int CountPlayerBotDropkiRuns(int def)
	{
		int n = 0;
		for (std::map<int, int>::const_iterator it = s_mapPlayerBotDropkiRunParty.begin(); it != s_mapPlayerBotDropkiRunParty.end(); ++it)
		{
			std::map<int, TPlayerBotDgRun>::const_iterator r = s_mapPlayerBotDgRuns.find(it->first);
			if (r != s_mapPlayerBotDgRuns.end() && (def < 0 || r->second.iDef == def))
				++n;
		}
		return n;
	}

	bool IsPlayerBotDropkiAway(DWORD pid, DWORD dwNow)
	{
		std::map<DWORD, DWORD>::const_iterator t = s_mapPlayerBotDropkiTripOut.find(pid);
		return t != s_mapPlayerBotDropkiTripOut.end() && dwNow - t->second < PLAYERBOT_DROPKI_TRIP_LOST_MS;
	}

	void TidyPlayerBotDropkiParties(DWORD dwNow)
	{
		for (std::map<int, int>::iterator it = s_mapPlayerBotDropkiRunParty.begin(); it != s_mapPlayerBotDropkiRunParty.end();)
		{
			if (!s_mapPlayerBotDgRuns.count(it->first))
				s_mapPlayerBotDropkiRunParty.erase(it++);
			else
				++it;
		}
		for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size();)
		{
			TPlayerBotDropkiParty& p = s_vecPlayerBotDropkiParties[i];
			const bool running = p.iRun && s_mapPlayerBotDgRuns.count(p.iRun);
			if (!running)
				p.iRun = 0;
			// the members: still Dropki of the row and here (a trip away keeps its place)
			for (size_t k = 0; k < p.pids.size();)
			{
				const DWORD pid = p.pids[k];
				std::map<DWORD, TPlayerBotDropkiBot>::iterator b = s_mapPlayerBotDropki.find(pid);
				// a Dropki of the row held for it (an inactive one - its break, its day, its build - frees the place), one
				// away on a sale trip, one in the party's run
				const bool keep = (b != s_mapPlayerBotDropki.end() && b->second.iDg == p.iDg && IsPlayerBotDropkiActive(pid)) ||
						IsPlayerBotDropkiAway(pid, dwNow) || (running && s_mapPlayerBotDgRunBots.count(pid));
				if (!keep)
				{
					if (b != s_mapPlayerBotDropki.end() && b->second.iParty == p.iId)
						b->second.iParty = 0;
					p.pids.erase(p.pids.begin() + k);
				}
				else
					++k;
			}
			if (!running && p.pids.empty())
			{
				sys_log(0, "BOT_DROPKI: party disbanded party=%d dungeon=%s runs=%u wins=%u", p.iId, PLAYERBOT_DROPKI_DGS[p.iDg].szKey,
						p.runs, p.wins);
				s_vecPlayerBotDropkiParties.erase(s_vecPlayerBotDropkiParties.begin() + i);
				continue;
			}
			++i;
		}
	}

	int FindPlayerBotDropkiPartyOf(DWORD pid)
	{
		for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size(); ++i)
			if (std::find(s_vecPlayerBotDropkiParties[i].pids.begin(), s_vecPlayerBotDropkiParties[i].pids.end(), pid) !=
					s_vecPlayerBotDropkiParties[i].pids.end())
				return s_vecPlayerBotDropkiParties[i].iId;
		return 0;
	}

	// The active Dropki of a row and a kingdom with no party: new parties, the short ones refilled.
	void FormPlayerBotDropkiParties(DWORD dwNow)
	{
		std::vector<DWORD> free[PLAYERBOT_DROPKI_DG_COUNT][4];
		for (std::map<DWORD, TPlayerBotDropkiBot>::iterator it = s_mapPlayerBotDropki.begin(); it != s_mapPlayerBotDropki.end(); ++it)
		{
			if (it->second.iParty && FindPlayerBotDropkiParty(it->second.iParty))
				continue;
			// back from a sale trip (its row restored): its party kept its place
			it->second.iParty = FindPlayerBotDropkiPartyOf(it->first);
			if (it->second.iParty)
				continue;
			if (!IsPlayerBotDropkiActive(it->first))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
				continue;
			free[it->second.iDg][ch->GetEmpire()].push_back(it->first);
		}
		for (int dg = 0; dg < PLAYERBOT_DROPKI_DG_COUNT; ++dg)
			for (int e = 1; e <= 3; ++e)
			{
				std::vector<DWORD>& v = free[dg][e];
				if (v.empty())
					continue;
				const int size = std::max(1, s_kPlayerBotDropkiCfg.size[dg]);
				// the short parties of this row and kingdom first
				for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size() && !v.empty(); ++i)
				{
					TPlayerBotDropkiParty& p = s_vecPlayerBotDropkiParties[i];
					if (p.iDg != dg || p.bEmpire != e)
						continue;
					std::string added;
					while ((int)p.pids.size() < size && !v.empty())
					{
						p.pids.push_back(v.back());
						s_mapPlayerBotDropki[v.back()].iParty = p.iId;
						LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(v.back());
						added += std::string(added.empty() ? "" : ",") + (c ? c->GetName() : "?");
						v.pop_back();
					}
					if (!added.empty())
						sys_log(0, "BOT_DROPKI: party refilled party=%d dungeon=%s members=%u added=%s", p.iId, PLAYERBOT_DROPKI_DGS[dg].szKey,
								(unsigned int)p.pids.size(), added.c_str());
				}
				const int def = GetPlayerBotDropkiDef(dg);
				const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor(PLAYERBOT_DGRUN_DEFS[def].szKey);
				const int least = size == 1 ? 1 : std::max(2, std::min(size, rule.startMin));
				while ((int)v.size() >= least)
				{
					// a healer and (the Nemere rows) a Ninja first, then the rest
					std::vector<DWORD> party;
					for (int want = 0; want < 2; ++want)
						for (size_t i = 0; i < v.size() && (int)party.size() < size; ++i)
						{
							LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(v[i]);
							if (!c)
								continue;
							const bool healer = c->GetJob() == JOB_SHAMAN && c->GetSkillGroup() != 0;
							if ((want == 0 && healer && size > 1) || (want == 1 && rule.needNinja && c->GetJob() == JOB_ASSASSIN))
							{
								party.push_back(v[i]);
								v.erase(v.begin() + i);
								break;
							}
						}
					while ((int)party.size() < size && !v.empty())
					{
						party.push_back(v.back());
						v.pop_back();
					}
					TPlayerBotDropkiParty p;
					p.iId = s_iPlayerBotDropkiNextParty++;
					p.iDg = dg;
					p.bEmpire = (BYTE)e;
					p.pids = party;
					std::string names;
					for (size_t i = 0; i < party.size(); ++i)
					{
						s_mapPlayerBotDropki[party[i]].iParty = p.iId;
						LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(party[i]);
						char buf[64];
						snprintf(buf, sizeof(buf), "%s%s(%d/j%d)", names.empty() ? "" : ",", c ? c->GetName() : "?", c ? (int)c->GetLevel() : 0,
								c ? (int)(c->GetJob() % 4) : 0);
						names += buf;
					}
					s_vecPlayerBotDropkiParties.push_back(p);
					sys_log(0, "BOT_DROPKI: party formed party=%d dungeon=%s empire=%d members=%u names=%s", p.iId,
							PLAYERBOT_DROPKI_DGS[dg].szKey, e, (unsigned int)party.size(), names.c_str());
				}
			}
	}

	int OpenPlayerBotDropkiRun(TPlayerBotDropkiParty& p, int def, const std::vector<playerbot_dgrun::TCand>& free, DWORD dwNow)
	{
		const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
		const BYTE empire = p.bEmpire;
		TPlayerBotDgRunSlot slot;
		slot.lvMin = GetPlayerBotDkDefMinLevel(def);
		slot.lvMax = gPlayerMaxLevel;
		slot.partyMin = 1;
		slot.partyMax = playerbot_dgrun::PARTY_MAX;
		slot.panel = mt2009_dpanel::FindKey(info.szKey);
		TPlayerBotLfgPlace& place = slot.place[empire];
		if (!ResolvePlayerBotLfgPlace(info.szKey, 0, empire, slot.lvMin, place))
		{
			if (info.bKind != DGRUN_KIND_MELEY)
			{
				PlayerBotLogThrottled("dropki_place", dwNow, "BOT_DROPKI: party=%d dungeon=%s - no entrance here (the panel's row)", p.iId,
						info.szKey);
				return 0;
			}
			// the panel's entrance of Meley: Straznik Smokow Dolnarr on Doyyumhwaji (playerbot_dgrun_meley.h's)
			place = TPlayerBotLfgPlace();
			place.key = "meley";
			place.map = 62;
			place.x = 597200;
			place.y = 699700;
			place.lvMin = slot.lvMin;
			place.lvMax = slot.lvMax;
		}
		slot.ok = slot.empireOk[empire] = true;
		const int id = OpenPlayerBotDgRun(def, empire, free, slot, free.size(), dwNow, "dropki");
		if (id == 0)
			return 0;
		s_mapPlayerBotDropkiRunParty[id] = p.iId;
		std::map<DWORD, TPlayerBotDropkiSnap>& snaps = s_mapPlayerBotDropkiSnaps[id];
		snaps.clear();
		for (size_t i = 0; i < free.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(free[i].pid);
			if (!c)
				continue;
			TPlayerBotDropkiSnap s;
			s.gold = (long long)c->GetGold();
			s.items = CountPlayerBotYdgBagItems(c);
			snaps[free[i].pid] = s;
		}
		return id;
	}

	// One party's call when it is due (forced: the test file's "now", no rest or wait).
	bool CallPlayerBotDropkiParty(TPlayerBotDropkiParty& p, DWORD dwNow, bool forced, int& running)
	{
		if (p.iRun || (!forced && p.dwRestUntil && (int)(p.dwRestUntil - dwNow) > 0))
			return false;
		const int dg = p.iDg;
		int def = GetPlayerBotDropkiDef(dg);
		if (def < 0 || !IsPlayerBotDropkiDgHere(dg))
			return false;
		std::vector<playerbot_dgrun::TCand> free;
		int away = 0;
		std::string why;
		for (size_t k = 0; k < p.pids.size(); ++k)
		{
			const DWORD pid = p.pids[k];
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			TPlayerBotAIState* state = GetPlayerBotDgRunState(pid);
			if (!ch || !state || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			{
				++away;
				continue;
			}
			if (!IsPlayerBotDropkiActive(pid))
			{
				why += std::string(why.empty() ? "" : ",") + ch->GetName() + ":inactive";
				continue;
			}
			if (s_mapPlayerBotDgRunBots.count(pid) || ch->IsDead())
			{
				why += std::string(why.empty() ? "" : ",") + ch->GetName() + (ch->IsDead() ? ":dead" : ":in_run");
				continue;
			}
			if (const char* refusal = GetPlayerBotDgRunRefusal(ch, *state, dwNow))
			{
				const bool broke = BreakOffPlayerBotDgRunTrainee(ch, *state, refusal, dwNow);
				why += std::string(why.empty() ? "" : ",") + ch->GetName() + ":" + refusal + (broke ? "(broken_off)" : "");
				continue;
			}
			if (ch->GetEmpire() != p.bEmpire)
				continue;
			const bool healer = ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0;
			free.push_back(playerbot_dgrun::TCand(pid, ch->GetLevel(), ch->GetJob(), 10 + (int)(p.pids.size() - k), healer));
		}
		if (!forced && (int)free.size() + away < (int)p.pids.size())
		{
			if (p.dwWaitSince == 0)
				p.dwWaitSince = dwNow ? dwNow : 1;
			if (dwNow - p.dwWaitSince < PLAYERBOT_DROPKI_WAIT_MS)
				return false;
		}
		// Glebie strong: a member short of the weak runs - the party goes to the weak one
		const char* prep = PLAYERBOT_DROPKI_DGS[dg].szPrep;
		if (prep)
		{
			std::string w;
			if (!IsPlayerBotGlebiePartyOk(def, free, w))
			{
				const int pdef = ParsePlayerBotDgRunKey(prep);
				if (pdef >= 0)
					def = pdef;
			}
		}
		const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
		const playerbot_dgrun::TRunRule& rule = playerbot_dgrun::RuleFor(info.szKey);
		const int size = std::max(1, s_kPlayerBotDropkiCfg.size[dg]);
		const int least = size == 1 ? 1 : std::max(2, std::min(size, rule.startMin));
		std::string reqWhy;
		const bool partyOk = (int)free.size() >= least && (size == 1 || playerbot_dgrun::PartyOk(free, rule)) &&
				IsPlayerBotGlebiePartyOk(def, free, reqWhy);
		if (!partyOk)
		{
			PlayerBotLogThrottled("dropki_wait", dwNow, "BOT_DROPKI: party=%d dungeon=%s waits - free=%u of %u away=%d least=%d not_free=%s%s%s",
					p.iId, info.szKey, (unsigned int)free.size(), (unsigned int)p.pids.size(), away, least, why.empty() ? "-" : why.c_str(),
					reqWhy.empty() ? "" : " req=", reqWhy.c_str());
			return false;
		}
		if (CountPlayerBotDropkiRuns(def) >= GetPlayerBotDropkiCapPerDg() || (!forced && running >= GetPlayerBotDropkiCapTotal()))
			return false;
		const int id = OpenPlayerBotDropkiRun(p, def, free, dwNow);
		if (id == 0)
			return false;
		p.iRun = id;
		p.dwWaitSince = 0;
		p.dwLastCall = dwNow ? dwNow : 1;
		++running;
		++s_akPlayerBotDropkiStats[dg].called;
		sys_log(0, "BOT_DROPKI: called party=%d run=%d dungeon=%s%s members=%u of %u away=%d running=%d/%d demand=%d not_free=%s", p.iId, id,
				info.szKey, def != GetPlayerBotDropkiDef(dg) ? "(prep)" : "", (unsigned int)free.size(), (unsigned int)p.pids.size(), away,
				running, GetPlayerBotDropkiCapTotal(), CountPlayerBotDropKnowDemand(def), why.empty() ? "-" : why.c_str());
		return true;
	}

	void CallPlayerBotDropkiParties(DWORD dwNow, int onlyDg)
	{
		int running = CountPlayerBotDropkiRuns(-1);
		if (running >= GetPlayerBotDropkiCapTotal() && onlyDg < 0)
			return;
		// the dungeons the drop knowledge's demand asks for first, then the longest waiting
		std::vector<std::pair<std::pair<int, DWORD>, size_t> > order;
		for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size(); ++i)
		{
			const TPlayerBotDropkiParty& p = s_vecPlayerBotDropkiParties[i];
			if (onlyDg >= 0 && p.iDg != onlyDg)
				continue;
			const int def = GetPlayerBotDropkiDef(p.iDg);
			order.push_back(std::make_pair(std::make_pair(-CountPlayerBotDropKnowDemand(def), p.dwLastCall), i));
		}
		std::sort(order.begin(), order.end());
		for (size_t o = 0; o < order.size(); ++o)
		{
			if (onlyDg < 0 && running >= GetPlayerBotDropkiCapTotal())
				break;
			CallPlayerBotDropkiParty(s_vecPlayerBotDropkiParties[order[o].second], dwNow, onlyDg >= 0, running);
		}
	}

	// ------------------------------------------------------------ the run's end

	// ClosePlayerBotDgRun: a Dropki run's end - the party's count, the gains, a short rest.
	DWORD NotePlayerBotDropkiRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS, DWORD rest)
	{
		std::map<int, int>::iterator rp = s_mapPlayerBotDropkiRunParty.find(run.iId);
		if (rp == s_mapPlayerBotDropkiRunParty.end())
			return rest;
		const int partyId = rp->second;
		s_mapPlayerBotDropkiRunParty.erase(rp);
		const DWORD dwNow = get_dword_time();
		const bool won = run.dwFinishedAt != 0;
		TPlayerBotDropkiParty* p = FindPlayerBotDropkiParty(partyId);
		const int dg = p ? p->iDg : -1;
		if (p)
		{
			p->iRun = 0;
			p->runs += entered ? 1 : 0;
			p->wins += won ? 1 : 0;
			char buf[96];
			snprintf(buf, sizeof(buf), "%s:%s:%us:st%d", PLAYERBOT_DGRUN_DEFS[run.iDef].szKey, result ? result : "-", tookS, run.iStage);
			p->last = buf;
		}
		long long gold = 0;
		int items = 0;
		std::map<DWORD, TPlayerBotDropkiSnap>& snaps = s_mapPlayerBotDropkiSnaps[run.iId];
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			std::map<DWORD, TPlayerBotDropkiBot>::iterator b = s_mapPlayerBotDropki.find(run.members[i]);
			if (b != s_mapPlayerBotDropki.end())
			{
				b->second.runs += entered ? 1 : 0;
				b->second.wins += won ? 1 : 0;
				b->second.dwNextSale = dwNow;	// the drop for sale now
				b->second.dwNextCheck = 0;		// the day's limit, the build again
			}
			std::map<DWORD, TPlayerBotDropkiSnap>::const_iterator s = snaps.find(run.members[i]);
			if (!c || s == snaps.end())
				continue;
			const long long g = (long long)c->GetGold() - s->second.gold;
			const int it = CountPlayerBotYdgBagItems(c) - s->second.items;
			gold += g;
			items += it;
			if (b != s_mapPlayerBotDropki.end())
			{
				b->second.llGold += g;
				b->second.iItems += it;
			}
		}
		s_mapPlayerBotDropkiSnaps.erase(run.iId);
		if (dg >= 0)
		{
			TPlayerBotDropkiStats& st = s_akPlayerBotDropkiStats[dg];
			st.entered += entered ? 1 : 0;
			st.won += won ? 1 : 0;
			st.gold += gold;
			st.items += items;
		}
		const DWORD shortRest = PLAYERBOT_DROPKI_REST_MIN_MS + (DWORD)number(0, (int)PLAYERBOT_DROPKI_REST_SPREAD_MS);
		if (p)
			p->dwRestUntil = dwNow + shortRest;
		sys_log(0, "BOT_DROPKI: run end party=%d run=%d dungeon=%s result=%s won=%d entered=%d took_s=%u stage=%d deaths=%d members=%u "
				"gold=%lld items=%d rest_s=%u", partyId, run.iId, PLAYERBOT_DGRUN_DEFS[run.iDef].szKey, result ? result : "-", won ? 1 : 0,
				entered ? 1 : 0, tookS, run.iStage, run.iDeaths, (unsigned int)run.members.size(), gold, items, shortRest / 1000);
		return entered ? shortRest : std::min(rest, shortRest * 2);
	}

	// ------------------------------------------------------------ between the runs

	// The drop for sale: a counter on this core served now; a Yohara resident home on a trade trip. 1 gone, 0 not.
	bool SellPlayerBotDropkiDrop(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDropkiBot& b, DWORD dwNow)
	{
		if ((int)(dwNow - b.dwNextSale) < 0 || IsPlayerBotOnDungeonRun(ch->GetPlayerID()))
			return false;
		b.dwNextSale = dwNow + 5 * 60 * 1000;
		if (b.dwSaleAt && dwNow - b.dwSaleAt < PLAYERBOT_DROPKI_SALE_GAP_MS)
			return false;
		const int goods = CountPlayerBotSungmaTradeGoods(ch, state);
		const bool full = ch->GetEmptyInventory(3) < 0;
		if (goods < s_kPlayerBotDropkiCfg.sellGoods && !(full && goods > 0))
			return false;
		const int dg = b.iDg;
		// a counter this core serves: its visit now
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		{
			auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
			if (shop && shop->GetSpawn().channel == g_bChannel && IsPlayerBotMapHostedHere(shop->GetSpawn().map))
			{
				if (HurryPlayerBotStallForBagRoom(ch, state, dwNow))
				{
					b.dwSaleAt = dwNow ? dwNow : 1;
					++s_akPlayerBotDropkiStats[dg].saleCounter;
					sys_log(0, "BOT_DROPKI: sale counter pid=%u name=%s dungeon=%s goods=%d full=%d", ch->GetPlayerID(), ch->GetName(),
							PLAYERBOT_DROPKI_DGS[dg].szKey, goods, full ? 1 : 0);
					return false;	// the service does it where the bot stands
				}
			}
		}
#endif
		// a Yohara resident: home on the Sung Ma trade trip's road (its counter, the stands), back to its map
		TPlayerBotYoharaResident* res = FindPlayerBotYoharaResident(ch->GetPlayerID());
		if (!res || !IsPlayerBotYoharaOn())
			return false;
		static int s_iTrips = -1;
		if (s_iTrips < 0)
			s_iTrips = GetPlayerBotDropkiEnv("PLAYERBOT_DROPKI_SALE_TRIPS", 6, 0, 60);
		int awayNow = 0;
		for (std::map<DWORD, DWORD>::iterator t = s_mapPlayerBotDropkiTripOut.begin(); t != s_mapPlayerBotDropkiTripOut.end();)
		{
			if (dwNow - t->second >= PLAYERBOT_DROPKI_TRIP_LOST_MS || (CHARACTER_MANAGER::instance().FindByPID(t->first) &&
					!IsPlayerBotSungmaTradeVisitor(t->first) && dwNow - t->second > 60 * 1000 &&
					IsPlayerBotMapHostedHere(CHARACTER_MANAGER::instance().FindByPID(t->first)->GetMapIndex())))
				s_mapPlayerBotDropkiTripOut.erase(t++);	// lost, or back
			else
			{
				++awayNow;
				++t;
			}
		}
		if (awayNow >= s_iTrips)
		{
			PlayerBotLogThrottled("dropki_sale_cap", dwNow, "BOT_DROPKI: sale trip waits pid=%u name=%s away=%d cap=%d", ch->GetPlayerID(),
					ch->GetName(), awayNow, s_iTrips);
			return false;
		}
		// one of a party at a time
		if (b.iParty)
			if (TPlayerBotDropkiParty* p = FindPlayerBotDropkiParty(b.iParty))
				for (size_t k = 0; k < p->pids.size(); ++k)
					if (p->pids[k] != ch->GetPlayerID() && IsPlayerBotDropkiAway(p->pids[k], dwNow))
						return false;
		if (state.dwTargetVID != 0 || ch->GetVictim() != NULL || ch->IsDead() || ch->GetHP() * 100 < ch->GetMaxHP() * 40)
			return false;
		long home = 0, x = 0, y = 0;
		if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, home, x, y) || IsPlayerBotMapHostedHere(home))
			return false;
		long ox = 0, oy = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x44524f50U, PLAYERBOT_SHOP_RING_MIN, PLAYERBOT_SHOP_RING_RADIUS, ox, oy);
		char reason[48];
		snprintf(reason, sizeof(reason), "sungma_trade:%ld:dropki", res->lMap);
		LeavePlayerBotSungmaParty(ch, "dropki_sale", true);
		if (!RequestPlayerBotYoharaHandover(ch, state, home, x + ox, y + oy, YOHARA_PURPOSE_HOME, reason, dwNow))
			return false;
		b.dwSaleAt = dwNow ? dwNow : 1;
		s_mapPlayerBotDropkiTripOut[ch->GetPlayerID()] = b.dwSaleAt;
		TPlayerBotSungmaTradeOut& out = s_mapPlayerBotSungmaTradeOut[ch->GetPlayerID()];
		out.dwAt = b.dwSaleAt;
		out.lMap = res->lMap;
		s_mapPlayerBotSungmaTradeLast[ch->GetPlayerID()] = b.dwSaleAt;
		++s_akPlayerBotDropkiStats[dg].saleTrips;
		sys_log(0, "BOT_DROPKI: sale trip pid=%u name=%s dungeon=%s goods=%d full=%d gold=%lld home=%ld back=%ld away=%d", ch->GetPlayerID(),
				ch->GetName(), PLAYERBOT_DROPKI_DGS[dg].szKey, goods, full ? 1 : 0, (long long)ch->GetGold(), home, res->lMap, awayNow + 1);
		return true;
	}

	struct FPlayerBotDropkiFindRace
	{
		DWORD m_dwRace;
		LPCHARACTER m_found;
		explicit FPlayerBotDropkiFindRace(DWORD race) : m_dwRace(race), m_found(NULL) {}
		void operator()(LPENTITY ent)
		{
			if (m_found || !ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER c = (LPCHARACTER)ent;
			if (!c->IsPC() && !c->IsDead() && c->GetRaceNum() == m_dwRace)
				m_found = c;
		}
	};

	// A material break: a material its plans lack, no counter holds and a monster of a map this core hosts gives.
	bool TakePlayerBotDropkiBreak(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDropkiBot& b, DWORD dwNow)
	{
		if ((int)(dwNow - b.dwNextBreak) < 0 || IsPlayerBotDropKnowOff() || !s_kPlayerBotDropKnow.bBuilt ||
				IsPlayerBotOnDungeonRun(ch->GetPlayerID()))
			return false;
		b.dwNextBreak = dwNow + 10 * 60 * 1000;
		if (b.iParty)
			if (TPlayerBotDropkiParty* p = FindPlayerBotDropkiParty(b.iParty))
			{
				if (p->iRun)
					return false;
				for (size_t k = 0; k < p->pids.size(); ++k)
				{
					std::map<DWORD, TPlayerBotDropkiBot>::const_iterator o = s_mapPlayerBotDropki.find(p->pids[k]);
					if (p->pids[k] != ch->GetPlayerID() && o != s_mapPlayerBotDropki.end() && o->second.dwBreakUntil &&
							(int)(o->second.dwBreakUntil - dwNow) > 0)
						return false;	// one of a party
				}
			}
		std::set<DWORD> wanted;
		CollectPlayerBotWantedMaterials(ch, wanted);
		for (std::set<DWORD>::const_iterator w = wanted.begin(); w != wanted.end(); ++w)
		{
			const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(*w);
			if (e && e->dwSupplyUnits > 0)
				continue;	// the market's
			const TPlayerBotDkPick pick = PickPlayerBotDkSource(ch, *w);
			if (pick.iChoice == DKCHOICE_CRAFT)
			{
				PlayerBotLogThrottled("dropki_craft", dwNow, "BOT_DROPKI: break craft pid=%u name=%s vnum=%u(%s) npc=%u (the craft's errand)",
						ch->GetPlayerID(), ch->GetName(), *w, PlayerBotDkItemName(*w), pick.dwNpc);
				continue;
			}
			if (pick.iChoice != DKCHOICE_FARM || !IsPlayerBotMapHostedHere(pick.lMap) || !SECTREE_MANAGER::instance().GetMap(pick.lMap))
				continue;
			// a living one of them on that map (the map's entities - the race index holds the registered races only)
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(pick.lMap);
			if (!pMap)
				continue;
			FPlayerBotDropkiFindRace finder(pick.dwMob);
			pMap->for_each(finder);
			LPCHARACTER mob = finder.m_found;
			if (!mob)
				continue;
			const bool there = ch->GetMapIndex() == pick.lMap;
			if (!there && !TransitionPlayerBotMap(ch, state, pick.lMap, mob->GetX(), mob->GetY(), dwNow, "dropki_break"))
				continue;
			b.dwBreakUntil = dwNow + PLAYERBOT_DROPKI_BREAK_MS;
			b.dwNextBreak = dwNow + PLAYERBOT_DROPKI_BREAK_GAP_MS;
			TPlayerBotDkFarm& f = s_mapPlayerBotDkFarm[ch->GetPlayerID()];
			f.lMap = pick.lMap;
			f.dwMob = pick.dwMob;
			f.dwVnum = *w;
			f.dwUntil = b.dwBreakUntil;
			++s_akPlayerBotDropkiStats[b.iDg].breaks;
			sys_log(0, "BOT_DROPKI: break pid=%u name=%s dungeon=%s vnum=%u(%s) mob=%u map=%ld chance=%.3f%% minutes=%u travel=%d", ch->GetPlayerID(),
					ch->GetName(), PLAYERBOT_DROPKI_DGS[b.iDg].szKey, *w, PlayerBotDkItemName(*w), pick.dwMob, pick.lMap, pick.fChance * 100.0f,
					PLAYERBOT_DROPKI_BREAK_MS / 60000, there ? 0 : 1);
			return true;
		}
		return false;
	}

	// playerbot_yohara_bots.h, the residents' pass for a held trainee: a Dropki's sale trip. True: it is gone.
	bool ManagePlayerBotDropkiResident(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;
		std::map<DWORD, TPlayerBotDropkiBot>::iterator it = s_mapPlayerBotDropki.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDropki.end() || !IsPlayerBotDropkiOn())
			return false;
		return SellPlayerBotDropkiDrop(ch, state, it->second, dwNow);
	}

	// ------------------------------------------------------------ the world's pass

	void LogPlayerBotDropkiStatus()
	{
		for (int dg = 0; dg < PLAYERBOT_DROPKI_DG_COUNT; ++dg)
		{
			if (!IsPlayerBotDropkiDgHere(dg))
				continue;
			int roles = 0, ready = 0, ideal = 0, active = 0, onBreak = 0, day = 0, parties = 0;
			const DWORD now = get_dword_time();
			for (std::map<DWORD, TPlayerBotDropkiBot>::const_iterator it = s_mapPlayerBotDropki.begin(); it != s_mapPlayerBotDropki.end(); ++it)
			{
				if (it->second.iDg != dg)
					continue;
				++roles;
				ready += it->second.bReady ? 1 : 0;
				ideal += it->second.bIdeal ? 1 : 0;
				day += it->second.bDayDone ? 1 : 0;
				onBreak += it->second.dwBreakUntil && (int)(it->second.dwBreakUntil - now) > 0 ? 1 : 0;
				active += IsPlayerBotDropkiActive(it->first) ? 1 : 0;
			}
			for (size_t i = 0; i < s_vecPlayerBotDropkiParties.size(); ++i)
				parties += s_vecPlayerBotDropkiParties[i].iDg == dg ? 1 : 0;
			const TPlayerBotDropkiStats& st = s_akPlayerBotDropkiStats[dg];
			const int def = GetPlayerBotDropkiDef(dg);
			sys_log(0, "BOT_DROPKI: status dungeon=%s want=%d roles=%d ready=%d ideal=%d active=%d break=%d day_done=%d parties=%d running=%d "
					"called=%u entered=%u won=%u gold=%lld items=%d sales=%u/%u breaks=%u demand=%d", PLAYERBOT_DROPKI_DGS[dg].szKey,
					s_kPlayerBotDropkiCfg.count[dg], roles, ready, ideal, active, onBreak, day, parties, CountPlayerBotDropkiRuns(def),
					st.called, st.entered, st.won, st.gold, st.items, st.saleCounter, st.saleTrips, st.breaks, CountPlayerBotDropKnowDemand(def));
		}
		sys_log(0, "BOT_DROPKI: status on=%d roles=%u parties=%u running=%d cap=%d per_dungeon=%d trips_out=%u", IsPlayerBotDropkiOn() ? 1 : 0,
				(unsigned int)s_mapPlayerBotDropki.size(), (unsigned int)s_vecPlayerBotDropkiParties.size(), CountPlayerBotDropkiRuns(-1),
				GetPlayerBotDropkiCapTotal(), GetPlayerBotDropkiCapPerDg(), (unsigned int)s_mapPlayerBotDropkiTripOut.size());
	}

	void RunPlayerBotDropkiTestFile(DWORD dwNow)
	{
		FILE* fp = fopen(PLAYERBOT_DROPKI_TEST_FILE, "r");
		if (!fp)
			return;
		std::vector<std::string> lines;
		char line[128];
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_DROPKI_TEST_FILE);
		rename(PLAYERBOT_DROPKI_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "", arg[48] = "";
			const int got = sscanf(lines[l].c_str(), "%31s %47s", cmd, arg);
			if (got < 1 || cmd[0] == '#')
				continue;
			if (!strcmp(cmd, "status"))
				LogPlayerBotDropkiStatus();
			else if (!strcmp(cmd, "roles"))
			{
				AssignPlayerBotDropkiRoles(dwNow);
				LogPlayerBotDropkiTargets();
			}
			else if (!strcmp(cmd, "now") && got >= 2)
			{
				const int dg = FindPlayerBotDropkiDg(arg);
				if (dg >= 0)
				{
					FormPlayerBotDropkiParties(dwNow);
					CallPlayerBotDropkiParties(dwNow, dg);
				}
				sys_log(0, "BOT_DROPKI: test now %s row=%d", arg, dg);
			}
			else
				sys_log(0, "BOT_DROPKI: test unknown line=%s", lines[l].c_str());
		}
	}

	// ManagePlayerBotDungeonRuns' second: the file, the roles, the checks, the parties and their calls, the breaks and sales
	// of the bots not on a Yohara core's residents' pass.
	void ManagePlayerBotDropki(DWORD dwNow)
	{
		static DWORD s_dwStart = 0, s_dwNext = 0, s_dwNextRoles = 0, s_dwNextStatus = 0, s_dwNextFile = 0;
		if (s_dwStart == 0)
		{
			s_dwStart = dwNow ? dwNow : 1;
			s_dwNextRoles = dwNow + PLAYERBOT_DROPKI_FIRST_ROLES_MS;
			s_dwNextStatus = dwNow + PLAYERBOT_DROPKI_FIRST_ROLES_MS + 60 * 1000;
		}
		ReadPlayerBotDropkiFile(dwNow);
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_DROPKI_PLAN_MS;
		if ((int)(dwNow - s_dwNextFile) >= 0)
		{
			s_dwNextFile = dwNow + 5000;
			RunPlayerBotDropkiTestFile(dwNow);
		}
		if ((int)(dwNow - s_dwNextRoles) >= 0)
		{
			const bool first = s_dwNextRoles == s_dwStart + PLAYERBOT_DROPKI_FIRST_ROLES_MS;
			s_dwNextRoles = dwNow + PLAYERBOT_DROPKI_ROLE_MS;
			AssignPlayerBotDropkiRoles(dwNow);
			if (first)
				LogPlayerBotDropkiTargets();
		}
		if ((int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_DROPKI_STATUS_MS;
			LogPlayerBotDropkiStatus();
		}
		if (s_mapPlayerBotDropki.empty())
			return;
		// the checks, and the breaks / sales of the Dropki this core's residents' pass does not see
		for (std::map<DWORD, TPlayerBotDropkiBot>::iterator it = s_mapPlayerBotDropki.begin(); it != s_mapPlayerBotDropki.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			TPlayerBotAIState* state = GetPlayerBotDgRunState(it->first);
			if (!ch || !state || !ch->IsItemLoaded())
				continue;
			TPlayerBotDropkiBot& b = it->second;
			if (b.dwNextCheck == 0 || (int)(dwNow - b.dwNextCheck) >= 0)
				CheckPlayerBotDropki(ch, b, dwNow);
			if (!IsPlayerBotDropkiActive(it->first) || !IsPlayerBotDropkiOn())
				continue;
			if (ch->IsDead() || IsPlayerBotOnDungeonRun(it->first))
				continue;
			if (!FindPlayerBotYoharaResident(it->first))
				SellPlayerBotDropkiDrop(ch, *state, b, dwNow);
			TakePlayerBotDropkiBreak(ch, *state, b, dwNow);
		}
		TidyPlayerBotDropkiParties(dwNow);
		if (!IsPlayerBotDropkiOn() || !IsPlayerBotDgRunOn(dwNow))
			return;
		FormPlayerBotDropkiParties(dwNow);
		CallPlayerBotDropkiParties(dwNow, -1);
	}
}

#endif
