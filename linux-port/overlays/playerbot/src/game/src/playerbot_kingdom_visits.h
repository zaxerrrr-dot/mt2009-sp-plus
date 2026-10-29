#ifndef __INC_METIN2_PLAYERBOT_KINGDOM_VISITS_H__
#define __INC_METIN2_PLAYERBOT_KINGDOM_VISITS_H__

// MT2009_PLUS_BOT_KINGDOM_VISITS_V1 - the bots' trips to another kingdom's
// first village, and the guilds' raids on one.
//
// The owner, 29 October: "Dodaj wycieczki botow na zakupy do M1 innego
// krolestwa. Moga handlowac miedzy soba (dogaduja sie na czacie handlowym),
// moga kupowac ze sklepow w innych krolestwach. Do M1 innego krolestwa ida
// przez Doline Orkow: wchodza swoim portalem i wychodza do tamtego M1 portalem
// tamtego krolestwa. W obcym krolestwie sa neutralni, nie atakuja innych botow
// - poza 10% botow, ktore przychodza wrogo: cala gildia, 10-20 minut najazdu
// na wrogie miasto, zabijaja wszystkie boty i graczy innego krolestwa.
// Krolestwo broni sie. Gdy najezdzcy gina szybko/wiele razy, wycofuja sie do
// strefy bezpiecznej, robia zakupy i wracaja do siebie. Najazd mniej wiecej
// raz na godzine na krolestwo, czyli 3 na godzine. Podczas najazdu boty
// obrazaja sie na czacie - nie na krzyku, nie na globalu - tylko na zwyklym."
//
// The way, both kinds alike:
//   - home -> Orc Valley: from the bot's own village by its Teleporter (the
//     fare as a person pays it), into the valley at its own kingdom's entry -
//     the Teleporter's own table (playerbot_empire_rules GetTeleportArrival);
//     a raider called from a hunting map is put there straight, as the guild
//     war's call puts its fighters on the arena;
//   - across the valley to the other kingdom's gate (GetFrontierGate: npc
//     10007/10009/10011, the warp whose name is that kingdom's first village)
//     and through it to where it puts a person down on that village's map
//     (PLAYERBOT_KV_M1_ARRIVAL, read off the warp's name in mob_proto);
//   - the walk to the village square (the stall ring, GetTownPitch - the safe
//     zone); a shopper browses the stands there (the market's own buyer,
//     playerbot_offline_market.h, which reads the stands of the map it stands
//     on) and may strike a deal with a local bot (the meeting of
//     playerbot_meetups.h: the talk on the trade chat, the window by the smith);
//   - home: the village's Teleporter to the valley (the bot's own entry, as
//     the quest's table does it for a person of another kingdom), its own gate,
//     its own village.
// Every leg has a clock; a leg that overruns it is made in one step (the
// stranded recovery's way, TransitionPlayerBotMap), a trip that overruns its
// own ends with the bot put down in its own village, and a bot found on
// another kingdom's ground after a restart is sent home (the quest flag
// kingdom_visit.away).
//
// A raid (one a target kingdom at a time, channel 1 - the guild wars' channel):
//   - called on its clock (RAID_EVERY_MIN, the three kingdoms a third of it
//     apart) or now (the panel's button: the spool file playerbot_raid_now,
//     or the event flag bot_raid_now = 1|2|3 for the kingdom, 9 for any);
//   - the raiders: one bot guild of one of the other two kingdoms, at most
//     RAID_SIZE of its free members on this core, the levels nearest to the
//     village's defenders' (their median and a few);
//   - the muster at the target's gate in the valley, the crossing together,
//     the march into the village; the fight lasts RAID_MIN_MIN..RAID_MAX_MIN
//     from the first raider in the village. A raider strikes every character
//     of another kingdom than its own there - bot or person - that a blow can
//     land on: not in the safe zone, not under PK_PROTECT_LEVEL (the engine's
//     own protection), not one it felled less than RAID_SPARE_SEC ago and not
//     one standing up invisible;
//   - the village defends itself: its kingdom's bots in the village go for the
//     raiders, and RAID_DEFENDERS more of its free bots of the raiders' levels
//     are called home from their maps;
//   - the raiders' deaths: RAID_RETREAT_DEATHS_PCT of their number in all, or
//     RAID_RETREAT_FAST_PCT within RAID_RETREAT_FAST_MIN minutes, and they fall
//     back into the safe zone; at the clock's end the same. Then they shop like
//     any visitor and go home the same way. A fallen raider stands up where it
//     fell (restart_here, invisible for its recovery, as every bot does);
//   - the taunts: on the local chat only (SendPlayerBotLocalChat, the talking
//     packet round the speaker), one line a side every RAID_TAUNT_SEC at most.
//
// Logs: PLAYERBOT_VISIT: (trips) and PLAYERBOT_TOWNRAID: (raids;
// PLAYERBOT_RAID: is the world bosses').
//
// An implementation fragment: include it once, last (after
// playerbot_yohara_bots.h); the manager calls ManagePlayerBotKingdomVisits once
// a tick, ManagePlayerBotKingdomVisit for each bot after the guild war's pass
// and HoldPlayerBotKingdomVisit after the market's.

#include <sys/stat.h>

namespace
{
	const char* const PLAYERBOT_RAID_NOW_PATH = "/opt/m2spool/playerbot_raid_now";
	const char* const PLAYERBOT_KV_AWAY_FLAG = "kingdom_visit.away";

	const long PLAYERBOT_KV_VALLEY = 64;
	// Where the valley's gate of a kingdom puts a person down on that
	// kingdom's first village (mob_proto: 10007 "Obszar_Youngan 4188 9560",
	// 10009 "Obszar_Joan 897 1127", 10011 "Obszar_Pyungmo 9343 3143").
	const long PLAYERBOT_KV_M1_ARRIVAL[4][2] = { { 0, 0 }, { 418800, 956000 }, { 89700, 112700 }, { 934300, 314300 } };
	const char* const PLAYERBOT_KV_KINGDOM[4] = { "", "Shinsoo", "Chunjo", "Jinno" };
	const char* const PLAYERBOT_KV_COLOUR[4] = { "", "czerwoni", "zolci", "niebiescy" };
	const char* const PLAYERBOT_KV_VILLAGE[4] = { "", "Yongan", "Joan", "Pyongmoo" };

	const DWORD PLAYERBOT_KV_PASS_MS = 1000;
	const DWORD PLAYERBOT_KV_FIRST_DELAY_MS = 3 * 60 * 1000;
	const long PLAYERBOT_KV_TOWN_RADIUS = 9000;     // the village round its square
	const long PLAYERBOT_KV_PITCH_ARRIVED = 900;
	const long PLAYERBOT_KV_MUSTER_RANGE = 1800;
	const int PLAYERBOT_KV_RAID_MIN_RAIDERS = 3;
	const DWORD PLAYERBOT_KV_SPAWN_GRACE_MS = 90 * 1000;
	const DWORD PLAYERBOT_KV_MOVE_MS = 900;
	const DWORD PLAYERBOT_KV_RETARGET_MS = 1500;
	const DWORD PLAYERBOT_KV_STUCK_MS = 60 * 1000;
	const long PLAYERBOT_KV_PROGRESS = 300;
	// The legs' clocks.
	const DWORD PLAYERBOT_KV_LEG_VALLEY_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_KV_LEG_CROSS_MS = 12 * 60 * 1000;
	const DWORD PLAYERBOT_KV_LEG_TOWN_MS = 7 * 60 * 1000;
	const DWORD PLAYERBOT_KV_LEG_LEAVE_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_KV_LEG_HOME_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_KV_SHOP_TTL_MS = 75 * 60 * 1000;
	const DWORD PLAYERBOT_KV_RAID_TTL_MS = 90 * 60 * 1000;
	// A raid's muster and crossing, at most.
	const DWORD PLAYERBOT_KV_MUSTER_MS = 12 * 60 * 1000;
	const DWORD PLAYERBOT_KV_CROSSING_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_KV_RAID_RETRY_MS = 5 * 60 * 1000;
	// After the raid: the raiders' shopping in the safe zone.
	const int PLAYERBOT_KV_RAID_SHOP_MIN = 3;
	const int PLAYERBOT_KV_RAID_SHOP_MAX = 6;
	// One bot says a raid line at most this often.
	const DWORD PLAYERBOT_KV_BOT_LINE_GAP_MS = 45 * 1000;
	const DWORD PLAYERBOT_KV_EVENT_LINE_GAP_MS = 6 * 1000;

	enum EPlayerBotKVKind { KV_KIND_SHOP = 1, KV_KIND_RAID = 2 };
	enum EPlayerBotKVPhase
	{
		KV_TO_VALLEY = 1,  // home (or a hunting map) -> Orc Valley at its own entry
		KV_TO_GATE,        // a shopper: across the valley and through the other kingdom's gate
		KV_MUSTER,         // a raider: at the target's gate, waiting for the guild
		KV_CROSS,          // a raider: through the gate
		KV_TO_TOWN,        // on the foreign village's map, to its square
		KV_FIGHT,          // a raider in the raid
		KV_DWELL,          // at the square: the stands, a deal
		KV_LEAVE,          // the village's Teleporter to the valley
		KV_HOME_GATE       // the valley: its own gate home
	};
	const char* GetPlayerBotKVPhaseName(BYTE phase)
	{
		static const char* const k[] = { "-", "to_valley", "to_gate", "muster", "cross", "to_town", "fight", "dwell", "leave", "home_gate" };
		return phase < sizeof(k) / sizeof(k[0]) ? k[phase] : "?";
	}

	struct TPlayerBotKVTrip
	{
		BYTE kind = 0;
		BYTE home = 0;
		BYTE target = 0;
		BYTE phase = 0;
		DWORD startedAt = 0;
		DWORD phaseSince = 0;
		DWORD dwellUntil = 0;
		DWORD nextMoveAt = 0;
		DWORD retargetAt = 0;
		DWORD progressAt = 0;
		long best = 0;
		int fails = 0;
		bool fallbackUsed = false;
		bool greeted = false;
		bool browsed = false;
		long patrolX = 0, patrolY = 0;
		DWORD patrolUntil = 0;
	};
	std::map<DWORD, TPlayerBotKVTrip> s_mapPlayerBotKVTrips;

	enum EPlayerBotKVRaidPhase { KV_RAID_GATHER = 1, KV_RAID_CROSS, KV_RAID_FIGHT, KV_RAID_OVER };
	struct TPlayerBotKVRaid
	{
		DWORD id = 0;
		BYTE target = 0;
		BYTE attacker = 0;
		BYTE phase = 0;
		DWORD guildId = 0;
		std::string guildName;
		long map = 0;
		long pitchX = 0, pitchY = 0;
		std::set<DWORD> raiders;
		std::set<DWORD> called;          // defenders called home
		std::set<DWORD> down;            // raiders lying now (a death counted once)
		std::deque<DWORD> deathTimes;
		int deaths = 0;
		int kills = 0;
		int defendersDown = 0;
		DWORD calledAt = 0, crossAt = 0, fightAt = 0, fightUntil = 0, overAt = 0;
		DWORD nextRaiderLine = 0, nextDefenderLine = 0, nextEventLine = 0;
		const char* overWhy = "";
		std::vector<std::pair<long, long> > patrol;
		std::vector<DWORD> victims;      // VIDs of the characters in the village a raider may look at
		std::vector<DWORD> homeBots;     // pids of the village's kingdom's bots in it (the speakers)
		int defMedian = 0;
	};
	std::map<BYTE, TPlayerBotKVRaid> s_mapPlayerBotKVRaids;   // by the raided kingdom
	DWORD s_dwPlayerBotKVRaidNextId = 1;
	DWORD s_adwPlayerBotKVRaidNext[4] = { 0, 0, 0, 0 };
	DWORD s_dwPlayerBotKVNextPass = 0;
	DWORD s_dwPlayerBotKVNextShopper = 0;
	DWORD s_dwPlayerBotKVNextCensus = 0;
	DWORD s_dwPlayerBotKVFlagHandledAt = 0;
	DWORD s_dwPlayerBotKVVisitFlagHandledAt = 0;
	time_t s_tPlayerBotKVNowSeen = (time_t)-1;
	bool s_bPlayerBotKVWasOn = true;
	std::map<DWORD, DWORD> s_mapPlayerBotKVSpared;      // victim pid -> left alone until
	std::map<DWORD, DWORD> s_mapPlayerBotKVLineAt;      // bot pid -> its last raid line
	std::map<DWORD, DWORD> s_mapPlayerBotKVDefMoveAt;   // defender pid -> next move
	std::map<DWORD, DWORD> s_mapPlayerBotKVDefTarget;   // defender pid -> retarget at
	std::map<DWORD, DWORD> s_mapPlayerBotKVAwayChecked; // pid -> the spawn whose flag was read
	unsigned int s_uPlayerBotKVTripsStarted = 0, s_uPlayerBotKVTripsHome = 0, s_uPlayerBotKVTripsFailed = 0;
	unsigned int s_uPlayerBotKVRaids = 0;

	// A clock's moment come (0 is "now"), past the wrap of get_dword_time.
	bool KVDue(DWORD dwNow, DWORD at)
	{
		return at == 0 || (int)(dwNow - at) >= 0;
	}

	int KVSetting(int key)
	{
		return GetPlayerBotVisitSetting(key);
	}
	bool IsPlayerBotKVOn()
	{
		return KVSetting(PLAYERBOT_KV_VISITS) != 0;
	}
	bool IsPlayerBotKVRaidsOn()
	{
		return IsPlayerBotKVOn() && KVSetting(PLAYERBOT_KV_RAIDS) != 0;
	}

	bool IsPlayerBotOnKingdomVisit(DWORD pid)
	{
		return !s_mapPlayerBotKVTrips.empty() && s_mapPlayerBotKVTrips.count(pid) != 0;
	}

	TPlayerBotKVTrip* FindPlayerBotKVTrip(DWORD pid)
	{
		std::map<DWORD, TPlayerBotKVTrip>::iterator it = s_mapPlayerBotKVTrips.find(pid);
		return it == s_mapPlayerBotKVTrips.end() ? NULL : &it->second;
	}

	long GetPlayerBotKVM1(int empire)
	{
		return playerbot_empire_rules::GetHomeMap(empire, playerbot_empire_rules::MAP_ROLE_M1);
	}

	bool GetPlayerBotKVPitch(int empire, long& x, long& y)
	{
		playerbot_empire_rules::TPoint p;
		if (!playerbot_empire_rules::GetTownPitch(GetPlayerBotKVM1(empire), p))
			return false;
		x = p.x;
		y = p.y;
		return true;
	}

	bool GetPlayerBotKVValleyEntry(int empire, long& x, long& y)
	{
		playerbot_empire_rules::TPoint p;
		if (!playerbot_empire_rules::GetTeleportArrival(empire, playerbot_empire_rules::TELEPORT_ORC_VALLEY, p))
			return false;
		x = p.x;
		y = p.y;
		return true;
	}

	bool GetPlayerBotKVValleyGate(int empire, long& x, long& y)
	{
		playerbot_empire_rules::TPoint p;
		if (!playerbot_empire_rules::GetFrontierGate(empire, PLAYERBOT_KV_VALLEY, p))
			return false;
		x = p.x;
		y = p.y;
		return true;
	}

	// The valley and the two villages on this core: a bot cannot cross cores.
	bool IsPlayerBotKVRouteHosted(int home, int target)
	{
		return home >= 1 && home <= 3 && target >= 1 && target <= 3 && home != target &&
				IsPlayerBotMapHostedHere(PLAYERBOT_KV_VALLEY) && IsPlayerBotMapHostedHere(GetPlayerBotKVM1(home)) &&
				IsPlayerBotMapHostedHere(GetPlayerBotKVM1(target));
	}

	bool IsPlayerBotKVTownGround(long map, long x, long y, int target, long extra = 0)
	{
		long px = 0, py = 0;
		return map == GetPlayerBotKVM1(target) && GetPlayerBotKVPitch(target, px, py) &&
				DISTANCE_APPROX(x - px, y - py) <= PLAYERBOT_KV_TOWN_RADIUS + extra;
	}

	// Free for a trip: alive and well, in no company and on no business a
	// trip would take it from - nor one of the world's special bots.
	bool IsPlayerBotKVFree(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded() ||
				!ch->GetSectree())
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotOnKingdomVisit(pid) || dwNow - state.dwSpawnTime < PLAYERBOT_KV_SPAWN_GRACE_MS)
			return false;
		if (IsPlayerBotSidekickPID(pid) || IsPlayerBotShouterPID(pid) || IsPlayerBotMedalShouterPID(pid) ||
				IsPlayerBotOnMercContract(pid) || IsPlayerBotSummoned(pid) ||
				CPlayerBotManager::instance().IsMedalDropperCohortPID(pid) || IsPlayerBotYoharaLeaving(pid))
			return false;
		if (IsPlayerBotDropper(state.bPersonality) || IsPlayerBotL30DropperAtWork(ch))
			return false;
		if (ch->GetParty() || IsPlayerBotHeldForCompany(ch) || IsPlayerBotArezzoHeld(ch) || IsPlayerBotOchaoForced(ch))
			return false;
		if (IsPlayerBotInDungeonBusiness(ch, state) || IsPlayerBotOnDungeonRun(pid) || IsPlayerBotOnZodiacRun(pid) ||
				IsPlayerBotCatacombRaider(pid) || IsPlayerBotShamanDuoMember(pid) || state.wBossRaidRace != 0 ||
				state.dwGuildWarEnemyGID != 0 || state.bWorldEventKind != 0)
			return false;
		if (IsPlayerBotInMeetup(pid) || IsPlayerBotDealMeeting(pid) || playerbot_pvp::IsInDuel(pid, dwNow))
			return false;
		if (ch->GetMyShop() || ch->GetExchange() || ch->GetShop() || ch->GetSafebox())
			return false;
		if (state.bVisitingShop || state.bVisitingBiologist || state.bVisitingStable || state.bMarketTrip ||
				state.bFishingSession || state.bRecoveringAfterDeath || state.bTacticalRetreat || state.bMultiPullActive ||
				state.bTownVisitPhase != BOT_TOWN_PHASE_NONE || state.lDesertCrossingTo != 0)
			return false;
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (state.bWaitingForShopChannel)
			return false;
#endif
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (state.offlineShop.visiting)
			return false;
#endif
		if (ch->GetMaxHP() <= 0 || ch->GetHP() * 100 < ch->GetMaxHP() * 70)
			return false;
		return ch->GetMapIndex() < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && IsPlayerBotMapHostedHere(ch->GetMapIndex());
	}

	// ------------------------------------------------------------- the chat

	bool SayPlayerBotKVLine(LPCHARACTER ch, const char* line, DWORD dwNow, bool force = false)
	{
		if (!ch || !line || !*line || ch->IsDead())
			return false;
		DWORD& last = s_mapPlayerBotKVLineAt[ch->GetPlayerID()];
		if (!force && last != 0 && dwNow - last < PLAYERBOT_KV_BOT_LINE_GAP_MS)
			return false;
		last = dwNow ? dwNow : 1;
		SendPlayerBotLocalChat(ch, line);
		sys_log(0, "PLAYERBOT_TOWNRAID: say pid=%u name=%s empire=%u text=\"%s\"", ch->GetPlayerID(), ch->GetName(),
				(unsigned int)ch->GetEmpire(), line);
		return true;
	}

	// A line of a bank, its %s (at most two) filled in.
	void FormatPlayerBotKVLine(char* out, size_t len, const char* const* bank, int n, const char* a, const char* b = "")
	{
		snprintf(out, len, bank[number(0, n - 1)], a ? a : "", b ? b : "");
	}

	const char* const KV_RAID_START[] = {
		"%s, wychodzic! Przyszlismy po was!",
		"Najazd na %s! Bierzemy ta wioske!",
		"Hej %s, wasza wioska jest teraz nasza!",
		"Spokojnie, tylko zwiedzamy... a nie, jednak bijemy, %s!",
		"Gildia %s melduje sie. Kto pierwszy do odstrzalu?",
	};
	const char* const KV_RAIDER_TAUNT[] = {
		"Slabo sie bronicie, %s!",
		"To ma byc obrona? Moja babcia bije mocniej.",
		"Gdzie wasi najlepsi? Pochowali sie w strefie?",
		"Ten miecz jeszcze sie nie zmeczyl.",
		"Uciekajcie do strefy, poki mozecie!",
		"Ile was jeszcze zostalo, %s?",
		"Lepiej idzcie expic, z PvP u was cienko.",
		"Ladna wioska. Szkoda, ze juz nie wasza.",
		"Nastepny chetny? Kolejka sie nie konczy!",
	};
	const char* const KV_RAIDER_KILL[] = {
		"Lezysz, %s!",
		"Nastepny prosze.",
		"GG, %s. Wstawaj, to powtorzymy.",
		"Jeden z glowy!",
		"%s, moze jednak potki na zapas?",
	};
	const char* const KV_DEFENDER_RALLY[] = {
		"Najazd na %s! Wszyscy do obrony!",
		"%s nas napadli, bierzemy ich!",
		"Nie oddamy wioski! Do mnie!",
		"Brac ich, %s nie przejda!",
		"Do broni! Wrog w wiosce!",
	};
	const char* const KV_DEFENDER_TAUNT[] = {
		"Po co przyszliscie? Po lanie?",
		"Wracajcie do siebie, %s!",
		"Za slabi jestescie na nasza wioske.",
		"Nastepnym razem zabierzcie wiecej potek.",
		"Nie ta wioska, koledzy.",
		"%s, mapy wam sie pomylily?",
		"Tu sie handluje, a nie rozrabia!",
	};
	const char* const KV_DEFENDER_KILL[] = {
		"Jeden mniej!",
		"Lezy %s! Dawac nastepnego!",
		"I po co to bylo, %s?",
		"Haha, i kto tu lezy?",
	};
	const char* const KV_RETREAT[] = {
		"Odwrot! Do strefy!",
		"Za duzo ich, wycofujemy sie!",
		"Dobra, starczy... idziemy na zakupy.",
		"Nastepnym razem was dorwiemy, %s!",
	};
	const char* const KV_RAID_END[] = {
		"Dobra, starczy na dzis. Zakupy i do domu.",
		"Bylo milo, %s. Do nastepnego razu!",
		"Koniec zabawy, chlopaki - do strefy.",
	};
	const char* const KV_DEFENDER_WIN[] = {
		"Uciekaja! Tak trzymac!",
		"I nie wracajcie, %s!",
		"Wioska obroniona!",
		"Gonic ich do strefy!",
	};
	const char* const KV_SHOPPER_HELLO[] = {
		"Siema, przyszedlem tylko na zakupy :)",
		"Spokojnie, jestem w pokoju. Co dobrego sprzedajecie?",
		"Jakie tu macie ceny? U nas drozej.",
		"Pierwszy raz w %s, ladnie tu.",
		"Hej, ktos cos sprzedaje taniej niz u nas?",
	};
	const char* const KV_SHOPPER_BYE[] = {
		"Dzieki, wracam do siebie.",
		"Fajny targ, jeszcze tu wpadne.",
		"Na dzis tyle, nara!",
	};

	template <size_t N>
	int KVBankSize(const char* const (&)[N]) { return (int)N; }

	// --------------------------------------------------------- the trips

	void StartPlayerBotKVTrip(LPCHARACTER ch, BYTE kind, BYTE target, DWORD dwNow, const char* why)
	{
		TPlayerBotKVTrip t;
		t.kind = kind;
		t.home = ch->GetEmpire();
		t.target = target;
		t.phase = KV_TO_VALLEY;
		t.startedAt = dwNow;
		t.phaseSince = dwNow;
		t.progressAt = dwNow;
		s_mapPlayerBotKVTrips[ch->GetPlayerID()] = t;
		++s_uPlayerBotKVTripsStarted;
		ch->SetQuestFlag(PLAYERBOT_KV_AWAY_FLAG, 1);
		sys_log(0, "PLAYERBOT_VISIT: start pid=%u name=%s kind=%s home=%u target=%u level=%u gold=%lld map=%ld why=%s",
				ch->GetPlayerID(), ch->GetName(), kind == KV_KIND_RAID ? "raid" : "shop", (unsigned int)t.home,
				(unsigned int)target, (unsigned int)ch->GetLevel(), (long long)ch->GetGold(), ch->GetMapIndex(), why);
	}

	void SetPlayerBotKVPhase(LPCHARACTER ch, TPlayerBotKVTrip& t, BYTE phase, DWORD dwNow)
	{
		if (t.phase == phase)
			return;
		sys_log(0, "PLAYERBOT_VISIT: phase pid=%u name=%s %s -> %s map=%ld pos=(%ld,%ld) after_s=%u",
				ch->GetPlayerID(), ch->GetName(), GetPlayerBotKVPhaseName(t.phase), GetPlayerBotKVPhaseName(phase),
				ch->GetMapIndex(), ch->GetX(), ch->GetY(), (dwNow - t.phaseSince) / 1000U);
		t.phase = phase;
		t.phaseSince = dwNow;
		t.progressAt = dwNow;
		t.best = 0;
		t.fails = 0;
		t.fallbackUsed = false;
		t.nextMoveAt = 0;
	}

	// Put down in its own village - the trip's last resort, and the way home
	// of a trip that ends anywhere but there.
	bool SendPlayerBotKVHome(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow, const char* why)
	{
		long x = 0, y = 0;
		const long m1 = GetPlayerBotKVM1(ch->GetEmpire());
		if (!GetPlayerBotKVPitch(ch->GetEmpire(), x, y) || !IsPlayerBotMapHostedHere(m1))
			return false;
		x += number(-300, 300);
		y += number(-300, 300);
		const bool ok = TransitionPlayerBotMap(ch, state, m1, x, y, dwNow, "kingdom_visit_home");
		sys_log(0, "PLAYERBOT_VISIT: sent home pid=%u name=%s from_map=%ld pos=(%ld,%ld) ok=%d why=%s",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), ok ? 1 : 0, why);
		return ok;
	}

	void EndPlayerBotKVTrip(LPCHARACTER ch, TPlayerBotAIState& state, const char* why, bool home, DWORD dwNow)
	{
		if (!ch)
			return;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotKVTrip>::iterator it = s_mapPlayerBotKVTrips.find(pid);
		if (it == s_mapPlayerBotKVTrips.end())
			return;
		const TPlayerBotKVTrip t = it->second;
		s_mapPlayerBotKVTrips.erase(it);
		// A meeting it planned there ends with it.
		if (TPlayerBotMeetup* m = FindPlayerBotMeetupOf(pid))
			EndPlayerBotMeetup(*m, false, "visit_over", ch, "Sorki, musze juz wracac do siebie.");
		const int owner = playerbot_empire_rules::GetMapOwnerEmpire(ch->GetMapIndex());
		const bool foreign = owner != 0 && owner != (int)ch->GetEmpire();
		bool sent = false;
		// Home in one step from another kingdom's ground or the valley - unless
		// another business took the bot (it moves it itself; the flag stays, so
		// a bot still there after a restart is sent home then).
		if (home && (foreign || ch->GetMapIndex() == PLAYERBOT_KV_VALLEY))
			sent = SendPlayerBotKVHome(ch, state, dwNow, why);
		if (!foreign || sent)
			ch->SetQuestFlag(PLAYERBOT_KV_AWAY_FLAG, 0);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		const bool ok = !strcmp(why, "home");
		if (ok)
			++s_uPlayerBotKVTripsHome;
		else
			++s_uPlayerBotKVTripsFailed;
		sys_log(0, "PLAYERBOT_VISIT: end pid=%u name=%s kind=%s home=%u target=%u phase=%s why=%s map=%ld took_s=%u gold=%lld",
				pid, ch->GetName(), t.kind == KV_KIND_RAID ? "raid" : "shop", (unsigned int)t.home, (unsigned int)t.target,
				GetPlayerBotKVPhaseName(t.phase), why, ch->GetMapIndex(), (dwNow - t.startedAt) / 1000U, (long long)ch->GetGold());
	}

	// Progress on a leg: the distance to its goal shrinking. False once it has
	// not for PLAYERBOT_KV_STUCK_MS.
	bool NotePlayerBotKVProgress(TPlayerBotKVTrip& t, long distance, DWORD dwNow)
	{
		if (t.best == 0 || distance + PLAYERBOT_KV_PROGRESS <= t.best)
		{
			t.best = distance;
			t.progressAt = dwNow;
			return true;
		}
		return dwNow - t.progressAt < PLAYERBOT_KV_STUCK_MS;
	}

	// A walk on the map it stands on, with its stuck rule: no progress for a
	// minute, twice, and it is put down at the goal (the war camp's way).
	bool WalkPlayerBotKV(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotKVTrip& t, long x, long y, DWORD dwNow,
			const char* why)
	{
		const long distance = DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y);
		state.dwLastMeaningfulActivityTime = dwNow;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (!NotePlayerBotKVProgress(t, distance, dwNow))
		{
			if (++t.fails >= 2)
			{
				sys_log(0, "PLAYERBOT_VISIT: stuck, put down pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld) why=%s",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), x, y, why);
				PlacePlayerBotAtWarCamp(ch, state, x, y, dwNow);
				t.fails = 0;
			}
			t.best = 0;
			t.progressAt = dwNow;
			ClearPlayerBotRoute(state, false);
			return true;
		}
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		if (KVDue(dwNow, t.nextMoveAt))
		{
			t.nextMoveAt = dwNow + PLAYERBOT_KV_MOVE_MS;
			MovePlayerBot(ch, x, y, dwNow, 8, true, true);
		}
		return true;
	}

	// A map change by a gate or a Teleporter, with the leg's clock: past it,
	// the move is made in one step, once; past it twice, false.
	bool PortalPlayerBotKV(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotKVTrip& t, long portalX, long portalY,
			long toMap, long toX, long toY, DWORD legMs, DWORD dwNow, const char* why)
	{
		state.dwLastMeaningfulActivityTime = dwNow;
		if (dwNow - t.phaseSince > legMs)
		{
			if (t.fallbackUsed)
				return false;
			t.fallbackUsed = true;
			t.phaseSince = dwNow;
			sys_log(0, "PLAYERBOT_VISIT: leg overran, moved pid=%u name=%s map=%ld pos=(%ld,%ld) to=%ld why=%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), toMap, why);
			TransitionPlayerBotMap(ch, state, toMap, toX, toY, dwNow, why);
			return true;
		}
		if (!MovePlayerBotToWorldPortal(ch, state, portalX, portalY, toMap, toX, toY, dwNow, why))
		{
			// Refused (the fare, a stall): the rest of the tick is the bot's,
			// the clock above still runs.
			if (KVDue(dwNow, t.nextMoveAt))
			{
				t.nextMoveAt = dwNow + 3000;
				MovePlayerBot(ch, portalX, portalY, dwNow, 8, true, true);
			}
		}
		return true;
	}

	// Through the Teleporter of the village it stands in - its own or the
	// foreign one - to the valley at its own kingdom's entry.
	bool TeleportPlayerBotKVToValley(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotKVTrip& t, DWORD legMs,
			DWORD dwNow, const char* why)
	{
		long ex = 0, ey = 0, tx = 0, ty = 0;
		if (!GetPlayerBotKVValleyEntry(ch->GetEmpire(), ex, ey))
			return false;
		if (!GetPlayerBotLocalTeleporter(ch, tx, ty) || ch->GetLevel() < PLAYERBOT_TELEPORTER_MIN_LEVEL ||
				ch->GetGold() < GetPlayerBotTeleporterFee(ch))
		{
			state.dwLastMeaningfulActivityTime = dwNow;
			if (!KVDue(dwNow, t.nextMoveAt))
				return true;
			t.nextMoveAt = dwNow + 5000;
			TransitionPlayerBotMap(ch, state, PLAYERBOT_KV_VALLEY, ex, ey, dwNow, why);
			return true;
		}
		return PortalPlayerBotKV(ch, state, t, tx, ty, PLAYERBOT_KV_VALLEY, ex, ey, legMs, dwNow, why);
	}

	// ------------------------------------------------------------ the fight

	bool IsPlayerBotKVRaider(const TPlayerBotKVRaid& raid, DWORD pid)
	{
		return raid.raiders.count(pid) != 0;
	}

	TPlayerBotKVRaid* FindPlayerBotKVRaidOn(long map)
	{
		for (std::map<BYTE, TPlayerBotKVRaid>::iterator it = s_mapPlayerBotKVRaids.begin(); it != s_mapPlayerBotKVRaids.end(); ++it)
			if (it->second.map == map)
				return &it->second;
		return NULL;
	}

	// A raider in the fight now: its trip in the fight and its raid fighting.
	bool IsPlayerBotKVRaiderFighting(DWORD pid, long map)
	{
		const TPlayerBotKVTrip* t = FindPlayerBotKVTrip(pid);
		if (!t || t->kind != KV_KIND_RAID || t->phase != KV_FIGHT)
			return false;
		std::map<BYTE, TPlayerBotKVRaid>::const_iterator r = s_mapPlayerBotKVRaids.find(t->target);
		return r != s_mapPlayerBotKVRaids.end() && r->second.phase == KV_RAID_FIGHT && r->second.map == map;
	}

	// Whether a blow can land on this one where it stands, as the engine asks
	// it (battle_is_attackable, CPVPManager::CanAttack) - without the
	// striker's own ground, which the striker walks off.
	bool IsPlayerBotKVStrikable(LPCHARACTER v)
	{
		return v && v->IsPC() && !v->IsDead() && v->GetHP() > 0 && !v->IsAffectFlag(AFF_REVIVE_INVISIBLE) &&
				!IsPlayerBotPersonUnseen(v) && !v->IsObserverMode() && v->GetPKMode() != PK_MODE_PROTECT &&
				(int)v->GetLevel() >= PK_PROTECT_LEVEL && v->GetGMLevel() == GM_PLAYER &&
				!IsPlayerBotSafeZone(v->GetMapIndex(), v->GetX(), v->GetY());
	}

	// A raider's victim: of another kingdom than the raider's, in the village,
	// strikable, and not one it felled a moment ago.
	bool IsPlayerBotKVVictim(LPCHARACTER raider, const TPlayerBotKVRaid& raid, LPCHARACTER v, DWORD dwNow)
	{
		if (!v || v == raider || v->GetEmpire() == raider->GetEmpire() || v->GetMapIndex() != raid.map ||
				!IsPlayerBotKVStrikable(v))
			return false;
		if (DISTANCE_APPROX(v->GetX() - raid.pitchX, v->GetY() - raid.pitchY) > PLAYERBOT_KV_TOWN_RADIUS + 1500)
			return false;
		std::map<DWORD, DWORD>::const_iterator spared = s_mapPlayerBotKVSpared.find(v->GetPlayerID());
		return spared == s_mapPlayerBotKVSpared.end() || KVDue(dwNow, spared->second);
	}

	// A defender's foe: a raider of the raid on this village, in the fight.
	bool IsPlayerBotKVDefenderFoe(const TPlayerBotKVRaid& raid, LPCHARACTER v)
	{
		return v && raid.phase == KV_RAID_FIGHT && IsPlayerBotKVRaider(raid, v->GetPlayerID()) &&
				v->GetMapIndex() == raid.map && IsPlayerBotKVStrikable(v) &&
				IsPlayerBotKVRaiderFighting(v->GetPlayerID(), raid.map) &&
				DISTANCE_APPROX(v->GetX() - raid.pitchX, v->GetY() - raid.pitchY) <= PLAYERBOT_KV_TOWN_RADIUS + 3000;
	}

	bool IsPlayerBotKingdomRaidFoe(LPCHARACTER ch, LPCHARACTER target)
	{
		if (!ch || !target || !target->IsPC() || s_mapPlayerBotKVRaids.empty())
			return false;
		TPlayerBotKVRaid* raid = FindPlayerBotKVRaidOn(ch->GetMapIndex());
		if (!raid || raid->phase != KV_RAID_FIGHT)
			return false;
		const DWORD pid = ch->GetPlayerID();
		// The raider's victims.
		if (IsPlayerBotKVRaider(*raid, pid))
			return IsPlayerBotKVRaiderFighting(pid, raid->map) && target->GetEmpire() != ch->GetEmpire();
		// Anybody's raider: the village's own bots defend it, and a visitor a
		// raider is at answers it.
		if (!IsPlayerBotKVRaider(*raid, target->GetPlayerID()) || !IsPlayerBotKVRaiderFighting(target->GetPlayerID(), raid->map))
			return false;
		if ((int)ch->GetEmpire() == raid->target)
			return true;
		TPlayerBotAIStateMap::const_iterator foe = s_mapPlayerBotAIStates.find(target->GetPlayerID());
		return foe != s_mapPlayerBotAIStates.end() && foe->second.dwTargetVID == (DWORD)ch->GetVID();
	}

	bool IsPlayerBotKingdomRaidBlow(LPCHARACTER victim, LPCHARACTER attacker)
	{
		if (!victim || !attacker || s_mapPlayerBotKVRaids.empty() || !victim->GetDesc() || !attacker->GetDesc() ||
				!victim->GetDesc()->IsBot() || !attacker->GetDesc()->IsBot())
			return false;
		const long map = attacker->GetMapIndex();
		return IsPlayerBotKVRaiderFighting(attacker->GetPlayerID(), map) ||
				IsPlayerBotKVRaiderFighting(victim->GetPlayerID(), map);
	}

	// The fight with one foe, the guild war's way: on foot, the aura first, a
	// caster from its range, a warrior across the gap, a blade where it reaches.
	bool FightPlayerBotKVFoe(LPCHARACTER ch, TPlayerBotAIState& state, LPCHARACTER foe, DWORD& nextMoveAt, DWORD dwNow)
	{
		const int distance = DISTANCE_APPROX(ch->GetX() - foe->GetX(), ch->GetY() - foe->GetY());
		state.dwTargetVID = (DWORD)foe->GetVID();
		state.dwLastMeaningfulActivityTime = dwNow;
		ch->SetVictim(foe);
		ch->SetRotationToXY(foe->GetX(), foe->GetY());
		SetPlayerBotAction(state, BOT_ACTION_FIGHT, dwNow);
		if (distance <= 2500 && ch->IsRiding() && !IsPlayerBotOnStandingMount(ch))
		{
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "kingdom_raid");
			if (ch->GetHorse())
				ch->HorseSummon(false);
			return true;
		}
		ReadyPlayerBotHandForFight(ch, state, dwNow, "kingdom_raid");
		if (distance <= PLAYERBOT_DUEL_BUFF_RANGE && ManagePlayerBotCombatBuffs(ch, state, dwNow, true))
			return true;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		const bool isBow = weapon && weapon->GetType() == ITEM_WEAPON && weapon->GetSubType() == WEAPON_BOW;
		const int combatRange = isBow ? 800 : PLAYERBOT_DUEL_MELEE_RANGE;
		const bool caster = ch->GetJob() == JOB_SHAMAN || (ch->GetJob() == JOB_SURA && ch->GetSkillGroup() == 2);
		const bool inSafeZone = IsPlayerBotSafeZone(ch->GetMapIndex(), ch->GetX(), ch->GetY());
		if (distance > combatRange || inSafeZone)
		{
			if (!inSafeZone && !isBow && caster && distance <= PLAYERBOT_DUEL_CASTER_RANGE &&
					dwNow >= state.dwNextSkillCastTime)
			{
				if (ch->IsStateMove())
					ch->Stop();
				if (CastPlayerBotDuelSkill(ch, foe, state, dwNow))
					return true;
			}
			if (!inSafeZone && !isBow && distance <= PLAYERBOT_SEARCH_RANGE &&
					TryPlayerBotDuelGapCloser(ch, foe, state, dwNow, distance))
				return true;
			if (KVDue(dwNow, nextMoveAt))
			{
				nextMoveAt = dwNow + 700;
				MovePlayerBot(ch, foe->GetX(), foe->GetY(), dwNow, 4, distance > PLAYERBOT_SEARCH_RANGE, false);
			}
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		ch->SetPosition(POS_FIGHTING);
		if (!CastPlayerBotDuelSkill(ch, foe, state, dwNow))
			ExecutePlayerBotBasicAttack(ch, foe, state, dwNow);
		return true;
	}

	// A foe it held has fallen: the raid's count, the victim left alone for a
	// while (no corpse camping), and a word.
	void NotePlayerBotKVFoeDown(LPCHARACTER ch, TPlayerBotKVRaid& raid, LPCHARACTER foe, bool raider, DWORD dwNow)
	{
		const DWORD foePid = foe->GetPlayerID();
		if (raider)
		{
			const DWORD spare = (DWORD)KVSetting(PLAYERBOT_KV_SPARE_SEC) * 1000U;
			std::map<DWORD, DWORD>::iterator was = s_mapPlayerBotKVSpared.find(foePid);
			if (was != s_mapPlayerBotKVSpared.end() && !KVDue(dwNow, was->second))
				return;   // counted already (another raider's blow)
			s_mapPlayerBotKVSpared[foePid] = dwNow + std::max<DWORD>(spare, 5000);
			++raid.kills;
			if ((int)foe->GetEmpire() == raid.target)
				++raid.defendersDown;
			sys_log(0, "PLAYERBOT_TOWNRAID: kill raid=%u raider=%u(%s) victim=%u(%s) empire=%u person=%d level=%u kills=%d",
					raid.id, ch->GetPlayerID(), ch->GetName(), foePid, foe->GetName(), (unsigned int)foe->GetEmpire(),
					foe->GetDesc() && !foe->GetDesc()->IsBot() ? 1 : 0, (unsigned int)foe->GetLevel(), raid.kills);
		}
		if (KVSetting(PLAYERBOT_KV_TAUNT_SEC) <= 0 || dwNow < raid.nextEventLine || number(1, 100) > 50)
			return;
		raid.nextEventLine = dwNow + PLAYERBOT_KV_EVENT_LINE_GAP_MS;
		char line[CHAT_MAX_LEN + 1];
		if (raider)
			FormatPlayerBotKVLine(line, sizeof(line), KV_RAIDER_KILL, KVBankSize(KV_RAIDER_KILL), foe->GetName());
		else
			FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_KILL, KVBankSize(KV_DEFENDER_KILL), foe->GetName());
		SayPlayerBotKVLine(ch, line, dwNow);
	}

	// A raider's pick: whoever strikes it first, then the raided kingdom's,
	// then the nearest - from the village's snapshot (the core's pass).
	LPCHARACTER FindPlayerBotKVVictim(LPCHARACTER ch, const TPlayerBotKVRaid& raid, DWORD dwNow)
	{
		LPCHARACTER best = NULL;
		long bestCost = LONG_MAX;
		for (size_t i = 0; i < raid.victims.size(); ++i)
		{
			LPCHARACTER v = CHARACTER_MANAGER::instance().Find(raid.victims[i]);
			if (!IsPlayerBotKVVictim(ch, raid, v, dwNow))
				continue;
			const long distance = DISTANCE_APPROX(ch->GetX() - v->GetX(), ch->GetY() - v->GetY());
			if (distance > 6000)
				continue;
			long cost = distance;
			if ((int)v->GetEmpire() != raid.target)
				cost += 2500;
			if (v->GetVictim() == ch)
				cost -= 3000;
			cost += (long)(PlayerBotNavHash(ch->GetPlayerID() * 2654435761U ^ v->GetPlayerID()) % 400U);
			if (cost < bestCost)
			{
				bestCost = cost;
				best = v;
			}
		}
		return best;
	}

	// The raider's tick in the village.
	bool FightPlayerBotKVRaid(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotKVTrip& t, TPlayerBotKVRaid& raid,
			DWORD dwNow)
	{
		// Drinks on its own one-second clocks, the war's thresholds.
		UseHealthPotion(ch, state, dwNow, PLAYERBOT_GUILD_WAR_POTION_HP_PERCENT);
		UseManaPotion(ch, state, dwNow, PLAYERBOT_GUILD_WAR_POTION_SP_PERCENT);
		ManagePlayerBotAutoPotions(ch, dwNow);
		LPCHARACTER foe = NULL;
		if (state.dwTargetVID != 0)
		{
			LPCHARACTER held = CHARACTER_MANAGER::instance().Find(state.dwTargetVID);
			if (held && held->IsPC() && (held->IsDead() || held->GetHP() <= 0))
				NotePlayerBotKVFoeDown(ch, raid, held, true, dwNow);
			else if (held && IsPlayerBotKVVictim(ch, raid, held, dwNow) &&
					DISTANCE_APPROX(ch->GetX() - held->GetX(), ch->GetY() - held->GetY()) <= 7000)
				foe = held;
		}
		if (!foe || KVDue(dwNow, t.retargetAt))
		{
			t.retargetAt = dwNow + PLAYERBOT_KV_RETARGET_MS;
			LPCHARACTER chosen = FindPlayerBotKVVictim(ch, raid, dwNow);
			if (chosen)
				foe = chosen;
		}
		if (foe)
			return FightPlayerBotKVFoe(ch, state, foe, t.nextMoveAt, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		state.dwLastMeaningfulActivityTime = dwNow;
		// Nobody to strike: through the village, from one of its open points
		// to the next.
		if (raid.patrol.empty())
		{
			t.patrolX = raid.pitchX;
			t.patrolY = raid.pitchY;
		}
		else if (KVDue(dwNow, t.patrolUntil) ||
				DISTANCE_APPROX(ch->GetX() - t.patrolX, ch->GetY() - t.patrolY) < 400)
		{
			const std::pair<long, long>& p = raid.patrol[(size_t)number(0, (int)raid.patrol.size() - 1)];
			t.patrolX = p.first + number(-250, 250);
			t.patrolY = p.second + number(-250, 250);
			t.patrolUntil = dwNow + 45000;
		}
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		if (KVDue(dwNow, t.nextMoveAt))
		{
			t.nextMoveAt = dwNow + PLAYERBOT_KV_MOVE_MS;
			MovePlayerBot(ch, t.patrolX, t.patrolY, dwNow, 6, true, true);
		}
		return true;
	}

	// A visitor (a shopper, or a raider after the fight) a raider is at, near:
	// it answers - the one fight a neutral bot takes on.
	LPCHARACTER FindPlayerBotKVAssailant(LPCHARACTER ch)
	{
		TPlayerBotKVRaid* raid = FindPlayerBotKVRaidOn(ch->GetMapIndex());
		if (!raid || raid->phase != KV_RAID_FIGHT)
			return NULL;
		for (std::set<DWORD>::const_iterator it = raid->raiders.begin(); it != raid->raiders.end(); ++it)
		{
			TPlayerBotAIStateMap::const_iterator rs = s_mapPlayerBotAIStates.find(*it);
			if (rs == s_mapPlayerBotAIStates.end() || rs->second.dwTargetVID != (DWORD)ch->GetVID())
				continue;
			LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
			if (r && IsPlayerBotKVStrikable(r) && r->GetMapIndex() == ch->GetMapIndex() &&
					DISTANCE_APPROX(ch->GetX() - r->GetX(), ch->GetY() - r->GetY()) <= 1500)
				return r;
		}
		return NULL;
	}

	// ------------------------------------------------------- the meeting

	// A deal with a bot of the village: one side short of a material or a
	// specimen, the other with it spare - the meeting of playerbot_meetups.h,
	// its talk on the trade chat, by the village's smith.
	bool PlanPlayerBotKVMeetup(LPCHARACTER visitor, DWORD dwNow)
	{
		if (!visitor || !IsPlayerBotTradeChatOn() || s_mapPlayerBotMeetups.size() >= PLAYERBOT_MEETUP_MAX_ACTIVE + 2 ||
				IsPlayerBotInMeetup(visitor->GetPlayerID()) || !IsPlayerBotPublicSpeaker(visitor, PLAYERBOT_MEETUP_MIN_LEVEL) ||
				visitor->GetExchange() || visitor->GetEmptyInventory(2) < 0)
			return false;
		const long village = visitor->GetMapIndex();
		if (!IsPlayerBotDealVillage(village))
			return false;
		std::map<DWORD, int> visitorWants;
		CollectPlayerBotMeetupWants(visitor, visitorWants);
		std::vector<LPCHARACTER> locals;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c == visitor || c->GetMapIndex() != village ||
					(int)c->GetEmpire() != playerbot_empire_rules::GetMapOwnerEmpire(village) ||
					DISTANCE_APPROX(c->GetX() - visitor->GetX(), c->GetY() - visitor->GetY()) > 8000 ||
					!IsPlayerBotMeetupFree(c, it->second))
				continue;
			locals.push_back(c);
		}
		if (locals.empty())
			return false;
		for (int tries = 0; tries < 12 && !locals.empty(); ++tries)
		{
			const size_t k = (size_t)number(0, (int)locals.size() - 1);
			LPCHARACTER local = locals[k];
			locals[k] = locals.back();
			locals.pop_back();
			// Both ways: the visitor buys what the local has spare, or sells it
			// what the local is short of.
			for (int way = 0; way < 2; ++way)
			{
				LPCHARACTER buyer = way == 0 ? visitor : local;
				LPCHARACTER seller = way == 0 ? local : visitor;
				std::map<DWORD, int> wants;
				if (way == 0)
					wants = visitorWants;
				else
					CollectPlayerBotMeetupWants(local, wants);
				for (std::map<DWORD, int>::const_iterator w = wants.begin(); w != wants.end(); ++w)
				{
					const int spare = GetPlayerBotMeetupSpare(seller, w->first);
					if (spare <= 0)
						continue;
					std::set<DWORD> sellerWants;
					CollectPlayerBotWantedMaterials(seller, sellerWants);
					if (sellerWants.count(w->first))
						continue;
					const TItemTable* proto = ITEM_MANAGER::instance().GetTable(w->first);
					const long long fair = GetPlayerBotDealFairPrice(w->first);
					if (!proto || fair <= 0)
						continue;
					long long unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(fair, 2000000000LL), false);
					const long long npcUnit = proto->bType == ITEM_WEAPON || proto->bType == ITEM_ARMOR
							? 0 : GetPlayerBotNpcShopUnitPrice(w->first);
					if (npcUnit > 0 && unit >= npcUnit)
						unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(npcUnit * 90 / 100, 2000000000LL), false);
					int count = std::min(spare, w->second);
					const long long purse = (long long)buyer->GetGold() * 60 / 100;
					if (unit > 0 && (long long)count * unit > purse)
						count = (int)(purse / unit);
					if (count <= 0 || unit <= 0)
						continue;
					long sx = 0, sy = 0;
					if (!GetPlayerBotDealSmithSpot(village, seller->GetPlayerID(), sx, sy))
						continue;
					TPlayerBotMeetup m;
					m.seller = seller->GetPlayerID();
					m.buyer = buyer->GetPlayerID();
					m.vnum = w->first;
					m.count = count;
					m.unit = unit;
					m.map = village;
					m.sx = sx;
					m.sy = sy;
					m.bx = sx + 160;
					m.by = sy + 120;
					m.at = dwNow;
					m.nextTalkAt = dwNow + (DWORD)number(2000, 8000);
					m.itemName = proto->szLocaleName;
					const DWORD id = s_dwPlayerBotMeetupNextId++;
					s_mapPlayerBotMeetups[id] = m;
					s_mapPlayerBotMeetupOf[m.seller] = id;
					s_mapPlayerBotMeetupOf[m.buyer] = id;
					sys_log(0, "PLAYERBOT_VISIT: deal planned id=%u visitor=%u(%s) local=%u(%s) visitor_buys=%d vnum=%u count=%d unit=%lld map=%ld",
							id, visitor->GetPlayerID(), visitor->GetName(), local->GetPlayerID(), local->GetName(),
							way == 0 ? 1 : 0, m.vnum, m.count, m.unit, village);
					return true;
				}
			}
		}
		return false;
	}

	// ------------------------------------------------------------- the tick

	// The village's square reached: the stay, a word, the stands looked at at
	// once, maybe a deal.
	void BeginPlayerBotKVDwell(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotKVTrip& t, DWORD dwNow)
	{
		int lo = KVSetting(PLAYERBOT_KV_STAY_MIN), hi = KVSetting(PLAYERBOT_KV_STAY_MAX);
		if (t.kind == KV_KIND_RAID)
		{
			lo = PLAYERBOT_KV_RAID_SHOP_MIN;
			hi = PLAYERBOT_KV_RAID_SHOP_MAX;
		}
		if (hi < lo)
			hi = lo;
		t.dwellUntil = dwNow + (DWORD)number(lo * 60, hi * 60) * 1000U;
		SetPlayerBotKVPhase(ch, t, KV_DWELL, dwNow);
		ClearPlayerBotRoute(state, false);
		if (ch->IsStateMove())
			ch->Stop();
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		state.offlineShop.nextBrowse = dwNow;
#endif
		state.dwNextShoppingTime = dwNow;
		if (t.kind == KV_KIND_SHOP && !t.greeted && number(1, 100) <= 40)
		{
			t.greeted = true;
			char line[CHAT_MAX_LEN + 1];
			FormatPlayerBotKVLine(line, sizeof(line), KV_SHOPPER_HELLO, KVBankSize(KV_SHOPPER_HELLO),
					PLAYERBOT_KV_VILLAGE[t.target]);
			SayPlayerBotKVLine(ch, line, dwNow);
		}
		if (number(1, 100) <= KVSetting(PLAYERBOT_KV_TRADE_PCT))
			PlanPlayerBotKVMeetup(ch, dwNow);
		sys_log(0, "PLAYERBOT_VISIT: at the square pid=%u name=%s kind=%s map=%ld stay_s=%u gold=%lld",
				ch->GetPlayerID(), ch->GetName(), t.kind == KV_KIND_RAID ? "raid" : "shop", ch->GetMapIndex(),
				(t.dwellUntil - dwNow) / 1000U, (long long)ch->GetGold());
	}

	// A bot that was on a trip when it last left the world stands in another
	// kingdom's village: home (the quest flag says so; read once a spawn).
	bool CheckPlayerBotKVAway(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		if (dwNow - state.dwSpawnTime < 20000)
			return false;
		DWORD& checked = s_mapPlayerBotKVAwayChecked[pid];
		if (checked == state.dwSpawnTime + 1)
			return false;
		checked = state.dwSpawnTime + 1;
		if (ch->GetQuestFlag(PLAYERBOT_KV_AWAY_FLAG) == 0)
			return false;
		const int owner = playerbot_empire_rules::GetMapOwnerEmpire(ch->GetMapIndex());
		if (owner != 0 && owner != (int)ch->GetEmpire() && !IsPlayerBotSidekickPID(pid) &&
				!(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())))
		{
			if (!SendPlayerBotKVHome(ch, state, dwNow, "away_after_restart"))
				return false;
		}
		ch->SetQuestFlag(PLAYERBOT_KV_AWAY_FLAG, 0);
		return true;
	}

	// The village's own bots defend it.
	bool ManagePlayerBotKVDefence(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_mapPlayerBotKVRaids.empty())
			return false;
		std::map<BYTE, TPlayerBotKVRaid>::iterator it = s_mapPlayerBotKVRaids.find(ch->GetEmpire());
		if (it == s_mapPlayerBotKVRaids.end() || it->second.phase != KV_RAID_FIGHT)
			return false;
		TPlayerBotKVRaid& raid = it->second;
		const DWORD pid = ch->GetPlayerID();
		const bool called = raid.called.count(pid) != 0;
		if ((int)ch->GetLevel() < PK_PROTECT_LEVEL || ch->GetPKMode() == PK_MODE_PROTECT)
			return false;
		if (IsPlayerBotSidekickPID(pid) || IsPlayerBotShouterPID(pid) || IsPlayerBotMedalShouterPID(pid) ||
				IsPlayerBotOnMercContract(pid) || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				ch->GetMyShop() || ch->GetExchange() || IsPlayerBotInMeetup(pid) || IsPlayerBotDealMeeting(pid) ||
				state.dwGuildWarEnemyGID != 0 || IsPlayerBotInDungeonBusiness(ch, state) || state.wBossRaidRace != 0 ||
				state.bWorldEventKind != 0 || IsPlayerBotOnDungeonRun(pid) || IsPlayerBotOnZodiacRun(pid) ||
				IsPlayerBotCatacombRaider(pid) || IsPlayerBotArezzoHeld(ch) || IsPlayerBotHeldForCompany(ch))
			return false;
		DWORD& moveAt = s_mapPlayerBotKVDefMoveAt[pid];
		if (ch->GetMapIndex() != raid.map)
		{
			if (!called)
				return false;
			// Called home: put down at its village's square (the Teleport Ring's
			// way home), once every few seconds until it is there.
			state.dwLastMeaningfulActivityTime = dwNow;
			if (!KVDue(dwNow, moveAt))
				return true;
			moveAt = dwNow + 5000;
			TransitionPlayerBotMap(ch, state, raid.map, raid.pitchX + number(-400, 400), raid.pitchY + number(-400, 400),
					dwNow, "kingdom_raid_defend");
			return true;
		}
		const long fromSquare = DISTANCE_APPROX(ch->GetX() - raid.pitchX, ch->GetY() - raid.pitchY);
		if (!called && fromSquare > PLAYERBOT_KV_TOWN_RADIUS + 3000)
			return false;
		if (state.bRecoveringAfterDeath)
			return called ? HandlePostDeathRecovery(ch, state, dwNow) : false;
		if (ch->GetMaxHP() <= 0 || (!called && ch->GetHP() * 100 < ch->GetMaxHP() * 35))
			return false;
		UseHealthPotion(ch, state, dwNow, PLAYERBOT_GUILD_WAR_POTION_HP_PERCENT);
		UseManaPotion(ch, state, dwNow, PLAYERBOT_GUILD_WAR_POTION_SP_PERCENT);
		LPCHARACTER foe = NULL;
		if (state.dwTargetVID != 0)
		{
			LPCHARACTER held = CHARACTER_MANAGER::instance().Find(state.dwTargetVID);
			if (held && held->IsPC() && (held->IsDead() || held->GetHP() <= 0) && IsPlayerBotKVRaider(raid, held->GetPlayerID()))
				NotePlayerBotKVFoeDown(ch, raid, held, false, dwNow);
			else if (held && IsPlayerBotKVDefenderFoe(raid, held))
				foe = held;
		}
		DWORD& retargetAt = s_mapPlayerBotKVDefTarget[pid];
		if (!foe || KVDue(dwNow, retargetAt))
		{
			retargetAt = dwNow + PLAYERBOT_KV_RETARGET_MS;
			const long reach = called ? PLAYERBOT_KV_TOWN_RADIUS * 2 : 6000;
			long best = LONG_MAX;
			for (std::set<DWORD>::const_iterator r = raid.raiders.begin(); r != raid.raiders.end(); ++r)
			{
				LPCHARACTER v = CHARACTER_MANAGER::instance().FindByPID(*r);
				if (!IsPlayerBotKVDefenderFoe(raid, v))
					continue;
				long d = DISTANCE_APPROX(ch->GetX() - v->GetX(), ch->GetY() - v->GetY());
				if (d > reach)
					continue;
				if (v->GetVictim() == ch)
					d -= 2000;
				if (d < best)
				{
					best = d;
					foe = v;
				}
			}
		}
		if (!foe)
		{
			if (!called)
				return false;
			// Called and nobody near: to the middle of the village, where the
			// raiders come.
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			state.dwLastMeaningfulActivityTime = dwNow;
			if (fromSquare > 2500 && KVDue(dwNow, moveAt))
			{
				moveAt = dwNow + PLAYERBOT_KV_MOVE_MS;
				MovePlayerBot(ch, raid.pitchX, raid.pitchY, dwNow, 8, true, true);
			}
			return true;
		}
		return FightPlayerBotKVFoe(ch, state, foe, moveAt, dwNow);
	}

	bool ManagePlayerBotKingdomVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || ch->GetHP() <= 0)
			return false;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotKVTrip* pt = FindPlayerBotKVTrip(pid);
		if (!pt)
		{
			if (CheckPlayerBotKVAway(ch, state, dwNow))
				return true;
			return ManagePlayerBotKVDefence(ch, state, dwNow);
		}
		TPlayerBotKVTrip& t = *pt;
		// Another business took it: a war, a raid's or a dungeon's call, a
		// person's party, a contract, a world event. That one moves it now.
		if (state.dwGuildWarEnemyGID != 0 || state.wBossRaidRace != 0 || state.bWorldEventKind != 0 ||
				IsPlayerBotOnDungeonRun(pid) || IsPlayerBotOnZodiacRun(pid) || IsPlayerBotCatacombRaider(pid) ||
				IsPlayerBotOnTowerBusiness(ch, state) || IsPlayerBotInDungeonBusiness(ch, state) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch) ||
				IsPlayerBotArezzoHeld(ch) || IsPlayerBotOchaoForced(ch))
		{
			EndPlayerBotKVTrip(ch, state, "taken", false, dwNow);
			return false;
		}
		const DWORD ttl = t.kind == KV_KIND_RAID ? PLAYERBOT_KV_RAID_TTL_MS : PLAYERBOT_KV_SHOP_TTL_MS;
		if (dwNow - t.startedAt > ttl)
		{
			EndPlayerBotKVTrip(ch, state, "ttl", true, dwNow);
			return true;
		}
		// A person's trade window, a deal or a meeting has the tick above this
		// pass; a window opened on the way holds the bot still.
		if (ch->GetExchange())
			return false;
		const long map = ch->GetMapIndex();
		const long homeM1 = GetPlayerBotKVM1(t.home);
		const long targetM1 = GetPlayerBotKVM1(t.target);
		// Back on its feet after a death: the recovery where it stood up,
		// claimed here so nothing below walks it off the foreign map.
		if (state.bRecoveringAfterDeath)
		{
			if (HandlePostDeathRecovery(ch, state, dwNow))
				return true;
		}
		// The potions, on their own one-second clock (the pass that drinks
		// them is below every one this trip claims).
		UseHealthPotion(ch, state, dwNow);
		// A raider in the fight answers to the raid.
		TPlayerBotKVRaid* raid = NULL;
		if (t.kind == KV_KIND_RAID)
		{
			std::map<BYTE, TPlayerBotKVRaid>::iterator r = s_mapPlayerBotKVRaids.find(t.target);
			if (r != s_mapPlayerBotKVRaids.end() && r->second.raiders.count(pid))
				raid = &r->second;
			if (!raid || raid->phase == KV_RAID_OVER)
			{
				// The raid is over: the fight ends; a raider not yet in the
				// village goes home, one there shops first.
				raid = NULL;
				if (t.phase == KV_TO_VALLEY || t.phase == KV_MUSTER || t.phase == KV_CROSS)
				{
					if (map == PLAYERBOT_KV_VALLEY)
						SetPlayerBotKVPhase(ch, t, KV_HOME_GATE, dwNow);
					else if (map != targetM1)
					{
						EndPlayerBotKVTrip(ch, state, "raid_over", false, dwNow);
						return false;
					}
					else
						SetPlayerBotKVPhase(ch, t, KV_TO_TOWN, dwNow);
				}
				else if (t.phase == KV_FIGHT)
				{
					state.dwTargetVID = 0;
					ch->SetVictim(NULL);
					SetPlayerBotKVPhase(ch, t, KV_TO_TOWN, dwNow);
				}
			}
		}
		// Hurt or set upon on the way (the valley's orcs): the tick's own
		// fight and potions first - not in the foreign village, where the bot
		// keeps to its business, and not in a raid's fight.
		if (map != targetM1 && t.phase != KV_MUSTER && IsPlayerBotSurvivalFirst(ch, state, dwNow))
			return false;
		switch (t.phase)
		{
			case KV_TO_VALLEY:
			{
				if (map == PLAYERBOT_KV_VALLEY)
				{
					SetPlayerBotKVPhase(ch, t, t.kind == KV_KIND_RAID ? KV_MUSTER : KV_TO_GATE, dwNow);
					return true;
				}
				const long homeM2 = playerbot_empire_rules::GetHomeMap(t.home, playerbot_empire_rules::MAP_ROLE_M2);
				if (map == homeM1 || map == homeM2)
				{
					if (TeleportPlayerBotKVToValley(ch, state, t, PLAYERBOT_KV_LEG_VALLEY_MS, dwNow, "kingdom_visit_valley"))
						return true;
				}
				else if (t.kind == KV_KIND_RAID && map != targetM1)
				{
					// Called from its hunting ground: into the valley at its own
					// kingdom's entry, as the war's call does it.
					long ex = 0, ey = 0;
					state.dwLastMeaningfulActivityTime = dwNow;
					if (!KVDue(dwNow, t.nextMoveAt))
						return true;
					t.nextMoveAt = dwNow + 5000;
					if (GetPlayerBotKVValleyEntry(t.home, ex, ey) && dwNow - t.phaseSince < PLAYERBOT_KV_LEG_VALLEY_MS &&
							TransitionPlayerBotMap(ch, state, PLAYERBOT_KV_VALLEY, ex, ey,
								dwNow, "kingdom_raid_muster"))
						return true;
				}
				EndPlayerBotKVTrip(ch, state, "no_way_to_valley", false, dwNow);
				return false;
			}
			case KV_TO_GATE:
			case KV_CROSS:
			{
				if (map == targetM1)
				{
					SetPlayerBotKVPhase(ch, t, t.kind == KV_KIND_RAID ? KV_FIGHT : KV_TO_TOWN, dwNow);
					sys_log(0, "PLAYERBOT_VISIT: crossed pid=%u name=%s kind=%s target=%u pos=(%ld,%ld)",
							pid, ch->GetName(), t.kind == KV_KIND_RAID ? "raid" : "shop", (unsigned int)t.target,
							ch->GetX(), ch->GetY());
					return true;
				}
				if (map != PLAYERBOT_KV_VALLEY)
				{
					EndPlayerBotKVTrip(ch, state, "lost_crossing", true, dwNow);
					return false;
				}
				long gx = 0, gy = 0;
				if (!GetPlayerBotKVValleyGate(t.target, gx, gy))
				{
					EndPlayerBotKVTrip(ch, state, "no_gate", true, dwNow);
					return false;
				}
				const long ax = PLAYERBOT_KV_M1_ARRIVAL[t.target][0];
				const long ay = PLAYERBOT_KV_M1_ARRIVAL[t.target][1];
				if (!PortalPlayerBotKV(ch, state, t, gx, gy, targetM1, ax, ay, PLAYERBOT_KV_LEG_CROSS_MS, dwNow,
						t.kind == KV_KIND_RAID ? "kingdom_raid_cross" : "kingdom_visit_cross"))
				{
					EndPlayerBotKVTrip(ch, state, "stuck_crossing", true, dwNow);
					return false;
				}
				return true;
			}
			case KV_MUSTER:
			{
				if (map != PLAYERBOT_KV_VALLEY)
				{
					EndPlayerBotKVTrip(ch, state, "lost_muster", false, dwNow);
					return false;
				}
				if (raid && raid->phase >= KV_RAID_CROSS)
				{
					SetPlayerBotKVPhase(ch, t, KV_CROSS, dwNow);
					return true;
				}
				long gx = 0, gy = 0;
				if (!GetPlayerBotKVValleyGate(t.target, gx, gy))
				{
					EndPlayerBotKVTrip(ch, state, "no_gate", true, dwNow);
					return false;
				}
				// By the gate, a little apart from one another.
				const long mx = gx + (long)(PlayerBotNavHash(pid) % 900U) - 450;
				const long my = gy + (long)(PlayerBotNavHash(pid ^ 0x4d555354U) % 900U) - 450;
				if (DISTANCE_APPROX(ch->GetX() - gx, ch->GetY() - gy) > PLAYERBOT_KV_MUSTER_RANGE - 300)
				{
					if (IsPlayerBotSurvivalFirst(ch, state, dwNow))
						return false;
					return WalkPlayerBotKV(ch, state, t, mx, my, dwNow, "muster");
				}
				// Waiting for the guild: buffs, potions, nothing else.
				state.dwLastMeaningfulActivityTime = dwNow;
				if (IsPlayerBotSurvivalFirst(ch, state, dwNow))
					return false;
				if (ch->IsStateMove())
					ch->Stop();
				ManagePlayerBotCombatBuffs(ch, state, dwNow, true);
				SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
				return true;
			}
			case KV_FIGHT:
			{
				if (map != targetM1 || !raid)
				{
					EndPlayerBotKVTrip(ch, state, "lost_fight", true, dwNow);
					return false;
				}
				// The march in: to the village before the raid's clock runs.
				if (!IsPlayerBotKVTownGround(map, ch->GetX(), ch->GetY(), t.target))
				{
					if (raid->phase == KV_RAID_FIGHT)
					{
						// Struck on the way in: it answers.
						LPCHARACTER held = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
						if (held && IsPlayerBotKVVictim(ch, *raid, held, dwNow))
							return FightPlayerBotKVRaid(ch, state, t, *raid, dwNow);
					}
					return WalkPlayerBotKV(ch, state, t, raid->pitchX, raid->pitchY, dwNow, "raid_march");
				}
				if (raid->phase != KV_RAID_FIGHT)
				{
					// In before the clock started (the first one in starts it).
					state.dwLastMeaningfulActivityTime = dwNow;
					if (ch->IsStateMove())
						ch->Stop();
					return true;
				}
				return FightPlayerBotKVRaid(ch, state, t, *raid, dwNow);
			}
			case KV_TO_TOWN:
			{
				if (map != targetM1)
				{
					EndPlayerBotKVTrip(ch, state, "lost_town", true, dwNow);
					return false;
				}
				long px = 0, py = 0;
				GetPlayerBotKVPitch(t.target, px, py);
				// A raider at it answers.
				if (LPCHARACTER assailant = FindPlayerBotKVAssailant(ch))
					return FightPlayerBotKVFoe(ch, state, assailant, t.nextMoveAt, dwNow);
				if (DISTANCE_APPROX(ch->GetX() - px, ch->GetY() - py) <= PLAYERBOT_KV_PITCH_ARRIVED)
				{
					BeginPlayerBotKVDwell(ch, state, t, dwNow);
					return true;
				}
				if (dwNow - t.phaseSince > PLAYERBOT_KV_LEG_TOWN_MS)
				{
					sys_log(0, "PLAYERBOT_VISIT: walk to the square overran, put down pid=%u name=%s map=%ld pos=(%ld,%ld)",
							pid, ch->GetName(), map, ch->GetX(), ch->GetY());
					PlacePlayerBotAtWarCamp(ch, state, px + number(-300, 300), py + number(-300, 300), dwNow);
					BeginPlayerBotKVDwell(ch, state, t, dwNow);
					return true;
				}
				return WalkPlayerBotKV(ch, state, t, px + (long)(PlayerBotNavHash(pid) % 600U) - 300,
						py + (long)(PlayerBotNavHash(pid ^ 0x50495443U) % 600U) - 300, dwNow, "to_square");
			}
			case KV_DWELL:
			{
				if (map != targetM1)
				{
					EndPlayerBotKVTrip(ch, state, "lost_dwell", true, dwNow);
					return false;
				}
				if (LPCHARACTER assailant = FindPlayerBotKVAssailant(ch))
					return FightPlayerBotKVFoe(ch, state, assailant, t.nextMoveAt, dwNow);
				const bool inMeetup = IsPlayerBotInMeetup(pid);
				bool buying = false;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
				buying = state.offlineShop.buyOwner != 0;
				// Half way through the stay the stands are looked at again.
				if (!t.browsed && (int)(dwNow - (t.dwellUntil - (t.dwellUntil - t.phaseSince) / 2)) >= 0)
				{
					t.browsed = true;
					state.offlineShop.nextBrowse = dwNow;
				}
#endif
				if ((int)(dwNow - t.dwellUntil) >= 0 &&
						((!inMeetup && !buying) || (int)(dwNow - t.dwellUntil) >= 10 * 60 * 1000))
				{
					if (t.kind == KV_KIND_SHOP && number(1, 100) <= 30)
					{
						char line[CHAT_MAX_LEN + 1];
						FormatPlayerBotKVLine(line, sizeof(line), KV_SHOPPER_BYE, KVBankSize(KV_SHOPPER_BYE), "");
						SayPlayerBotKVLine(ch, line, dwNow);
					}
					SetPlayerBotKVPhase(ch, t, KV_LEAVE, dwNow);
					return true;
				}
				// The market's own pass has the rest of the tick
				// (ManagePlayerBotShopping), then HoldPlayerBotKingdomVisit.
				state.dwLastMeaningfulActivityTime = dwNow;
				return false;
			}
			case KV_LEAVE:
			{
				if (map == PLAYERBOT_KV_VALLEY)
				{
					SetPlayerBotKVPhase(ch, t, KV_HOME_GATE, dwNow);
					return true;
				}
				if (map != targetM1)
				{
					EndPlayerBotKVTrip(ch, state, "lost_leave", true, dwNow);
					return false;
				}
				if (LPCHARACTER assailant = FindPlayerBotKVAssailant(ch))
					return FightPlayerBotKVFoe(ch, state, assailant, t.nextMoveAt, dwNow);
				if (!TeleportPlayerBotKVToValley(ch, state, t, PLAYERBOT_KV_LEG_LEAVE_MS, dwNow, "kingdom_visit_leave"))
				{
					EndPlayerBotKVTrip(ch, state, "stuck_leave", true, dwNow);
					return true;
				}
				return true;
			}
			case KV_HOME_GATE:
			{
				if (map == homeM1)
				{
					EndPlayerBotKVTrip(ch, state, "home", false, dwNow);
					return false;
				}
				if (map != PLAYERBOT_KV_VALLEY)
				{
					EndPlayerBotKVTrip(ch, state, "lost_home", true, dwNow);
					return false;
				}
				long gx = 0, gy = 0, px = 0, py = 0;
				if (!GetPlayerBotKVValleyGate(t.home, gx, gy) || !GetPlayerBotKVPitch(t.home, px, py))
				{
					EndPlayerBotKVTrip(ch, state, "no_gate", true, dwNow);
					return true;
				}
				if (!PortalPlayerBotKV(ch, state, t, gx, gy, homeM1, px + number(-300, 300), py + number(-300, 300),
						PLAYERBOT_KV_LEG_HOME_MS, dwNow, "kingdom_visit_return"))
				{
					EndPlayerBotKVTrip(ch, state, "stuck_home", true, dwNow);
					return true;
				}
				return true;
			}
			default:
				EndPlayerBotKVTrip(ch, state, "bad_phase", true, dwNow);
				return false;
		}
	}

	// After the market's pass, which had the tick and did not take it: a
	// visitor at the square stays there - idle, a step now and then.
	bool HoldPlayerBotKingdomVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || s_mapPlayerBotKVTrips.empty())
			return false;
		TPlayerBotKVTrip* t = FindPlayerBotKVTrip(ch->GetPlayerID());
		if (!t || t->phase != KV_DWELL)
			return false;
		long px = 0, py = 0;
		if (!GetPlayerBotKVPitch(t->target, px, py))
			return false;
		state.dwLastMeaningfulActivityTime = dwNow;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		if (KVDue(dwNow, t->nextMoveAt))
		{
			t->nextMoveAt = dwNow + (DWORD)number(20000, 45000);
			const long x = px + number(-500, 500);
			const long y = py + number(-500, 500);
			if (IsPlayerBotSafeZone(ch->GetMapIndex(), x, y) || DISTANCE_APPROX(ch->GetX() - px, ch->GetY() - py) > 1200)
				MovePlayerBot(ch, x, y, dwNow, 4, true, false);
		}
		return true;
	}

	// ------------------------------------------------------- the core's pass

	// Ends every trip (the switch went off): a bot on another kingdom's ground
	// is put down at home.
	void EndAllPlayerBotKVTrips(const char* why, DWORD dwNow)
	{
		std::vector<DWORD> pids;
		for (std::map<DWORD, TPlayerBotKVTrip>::const_iterator it = s_mapPlayerBotKVTrips.begin(); it != s_mapPlayerBotKVTrips.end(); ++it)
			pids.push_back(it->first);
		for (size_t i = 0; i < pids.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
			if (!c)
			{
				s_mapPlayerBotKVTrips.erase(pids[i]);
				continue;
			}
			EndPlayerBotKVTrip(c, s_mapPlayerBotAIStates[pids[i]], why, true, dwNow);
		}
		s_mapPlayerBotKVRaids.clear();
	}

	void StartPlayerBotKVShoppers(int n, DWORD dwNow, const char* why)
	{
		if (n <= 0)
			return;
		int active = 0;
		for (std::map<DWORD, TPlayerBotKVTrip>::const_iterator it = s_mapPlayerBotKVTrips.begin(); it != s_mapPlayerBotKVTrips.end(); ++it)
			if (it->second.kind == KV_KIND_SHOP)
				++active;
		const int cap = KVSetting(PLAYERBOT_KV_MAX);
		const int minLevel = KVSetting(PLAYERBOT_KV_MIN_LEVEL);
		const long long minGold = KVSetting(PLAYERBOT_KV_MIN_GOLD);
		std::vector<LPCHARACTER> pool;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || (int)c->GetLevel() < minLevel || (long long)c->GetGold() < minGold || !IsPlayerBotKVFree(c, it->second, dwNow))
				continue;
			const int e = c->GetEmpire();
			const long map = c->GetMapIndex();
			if (map != PLAYERBOT_KV_VALLEY && map != GetPlayerBotKVM1(e) &&
					map != playerbot_empire_rules::GetHomeMap(e, playerbot_empire_rules::MAP_ROLE_M2))
				continue;
			pool.push_back(c);
		}
		int started = 0;
		while (started < n && active < cap && !pool.empty())
		{
			const size_t k = (size_t)number(0, (int)pool.size() - 1);
			LPCHARACTER c = pool[k];
			pool[k] = pool.back();
			pool.pop_back();
			const int home = c->GetEmpire();
			int targets[2], nt = 0;
			for (int e = 1; e <= 3; ++e)
			{
				if (e == home || !IsPlayerBotKVRouteHosted(home, e))
					continue;
				// Not into a village under a raid.
				std::map<BYTE, TPlayerBotKVRaid>::const_iterator r = s_mapPlayerBotKVRaids.find((BYTE)e);
				if (r != s_mapPlayerBotKVRaids.end() && r->second.phase != KV_RAID_OVER)
					continue;
				targets[nt++] = e;
			}
			if (nt == 0)
				continue;
			StartPlayerBotKVTrip(c, KV_KIND_SHOP, (BYTE)targets[number(0, nt - 1)], dwNow, why);
			++started;
			++active;
		}
	}

	// The raid on a kingdom's village: one bot guild of another kingdom.
	bool CallPlayerBotKVRaid(BYTE target, DWORD dwNow, const char* why)
	{
		long px = 0, py = 0;
		if (!GetPlayerBotKVPitch(target, px, py))
			return false;
		const long map = GetPlayerBotKVM1(target);
		// The village's defenders' levels: its kingdom's bots of PvP age in it.
		std::vector<int> defLevels;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (c && !c->IsDead() && c->GetEmpire() == target && c->GetMapIndex() == map &&
					(int)c->GetLevel() >= PK_PROTECT_LEVEL &&
					DISTANCE_APPROX(c->GetX() - px, c->GetY() - py) <= PLAYERBOT_KV_TOWN_RADIUS)
				defLevels.push_back(c->GetLevel());
		}
		int defMedian = 0;
		if (!defLevels.empty())
		{
			std::nth_element(defLevels.begin(), defLevels.begin() + defLevels.size() / 2, defLevels.end());
			defMedian = defLevels[defLevels.size() / 2];
		}
		const int minLevel = KVSetting(PLAYERBOT_KV_RAID_MIN_LEVEL);
		const int want = std::max(minLevel, defMedian + 3);
		// The free members of every bot guild of the other kingdoms.
		std::map<DWORD, std::vector<LPCHARACTER> > byGuild;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c->GetEmpire() == target || (int)c->GetLevel() < minLevel || !c->GetGuild() ||
					!IsPlayerBotGuild(c->GetGuild()) || !IsPlayerBotKVRouteHosted(c->GetEmpire(), target) ||
					c->GetMapIndex() == map || !IsPlayerBotKVFree(c, it->second, dwNow))
				continue;
			byGuild[c->GetGuild()->GetID()].push_back(c);
		}
		const int size = KVSetting(PLAYERBOT_KV_RAID_SIZE);
		const int need = std::min(PLAYERBOT_KV_RAID_MIN_RAIDERS, size);
		DWORD bestGuild = 0;
		long bestScore = LONG_MIN;
		for (std::map<DWORD, std::vector<LPCHARACTER> >::iterator g = byGuild.begin(); g != byGuild.end(); ++g)
		{
			std::vector<LPCHARACTER>& members = g->second;
			if ((int)members.size() < need)
				continue;
			std::vector<int> levels;
			for (size_t i = 0; i < members.size(); ++i)
				levels.push_back(members[i]->GetLevel());
			std::nth_element(levels.begin(), levels.begin() + levels.size() / 2, levels.end());
			const int median = levels[levels.size() / 2];
			long score = -(long)abs(median - want) * 10 + (long)std::min<size_t>(members.size(), (size_t)size) * 3 +
					number(0, 15);
			if (score > bestScore)
			{
				bestScore = score;
				bestGuild = g->first;
			}
		}
		if (bestGuild == 0)
		{
			PlayerBotLogThrottled("kv_raid_none", dwNow, "PLAYERBOT_TOWNRAID: no guild to raid target=%u why=%s guilds=%u",
					(unsigned int)target, why, (unsigned int)byGuild.size());
			return false;
		}
		std::vector<LPCHARACTER>& members = byGuild[bestGuild];
		struct FByLevelGap
		{
			int want;
			bool operator()(LPCHARACTER a, LPCHARACTER b) const
			{
				const int da = abs((int)a->GetLevel() - want), db = abs((int)b->GetLevel() - want);
				return da != db ? da < db : a->GetPlayerID() < b->GetPlayerID();
			}
		};
		FByLevelGap order;
		order.want = want;
		std::sort(members.begin(), members.end(), order);
		if ((int)members.size() > size)
			members.resize(size);
		TPlayerBotKVRaid raid;
		raid.id = s_dwPlayerBotKVRaidNextId++;
		raid.target = target;
		raid.attacker = members[0]->GetEmpire();
		raid.phase = KV_RAID_GATHER;
		raid.guildId = bestGuild;
		raid.guildName = members[0]->GetGuild()->GetName();
		raid.map = map;
		raid.pitchX = px;
		raid.pitchY = py;
		raid.calledAt = dwNow;
		raid.defMedian = defMedian;
		// The village's open ground round its square, where the raiders go
		// when nobody is in reach: eight ways at three distances, off the safe
		// zone and joined to the square.
		static const int kDir[8][2] = { { 1000, 0 }, { 707, 707 }, { 0, 1000 }, { -707, 707 }, { -1000, 0 }, { -707, -707 }, { 0, -1000 }, { 707, -707 } };
		static const int kRing[3] = { 2500, 3800, 5200 };
		for (int d = 0; d < 8; ++d)
			for (int r = 0; r < 3; ++r)
			{
				const long x = px + kDir[d][0] * kRing[r] / 1000;
				const long y = py + kDir[d][1] * kRing[r] / 1000;
				if (!IsPlayerBotSafeZone(map, x, y) && IsPlayerBotReachable(map, px, py, x, y))
				{
					raid.patrol.push_back(std::make_pair(x, y));
					break;
				}
			}
		int lo = 255, hi = 0;
		for (size_t i = 0; i < members.size(); ++i)
		{
			raid.raiders.insert(members[i]->GetPlayerID());
			lo = std::min(lo, (int)members[i]->GetLevel());
			hi = std::max(hi, (int)members[i]->GetLevel());
			StartPlayerBotKVTrip(members[i], KV_KIND_RAID, target, dwNow, "raid");
		}
		++s_uPlayerBotKVRaids;
		sys_log(0, "PLAYERBOT_TOWNRAID: called raid=%u target=%u(%s) attacker=%u(%s) guild=%s raiders=%u levels=%d-%d def_median=%d patrol=%u why=%s",
				raid.id, (unsigned int)target, PLAYERBOT_KV_KINGDOM[target], (unsigned int)raid.attacker,
				PLAYERBOT_KV_KINGDOM[raid.attacker], raid.guildName.c_str(), (unsigned int)raid.raiders.size(), lo, hi,
				defMedian, (unsigned int)raid.patrol.size(), why);
		s_mapPlayerBotKVRaids[target] = raid;
		return true;
	}

	// The raid over - by its clock or its losses: the raiders fall back into
	// the safe zone and shop, the called defenders go back to their lives.
	void EndPlayerBotKVRaid(TPlayerBotKVRaid& raid, const char* why, DWORD dwNow)
	{
		if (raid.phase == KV_RAID_OVER)
			return;
		const bool fought = raid.phase == KV_RAID_FIGHT;
		raid.phase = KV_RAID_OVER;
		raid.overAt = dwNow;
		raid.overWhy = why;
		raid.called.clear();
		sys_log(0, "PLAYERBOT_TOWNRAID: over raid=%u target=%u attacker=%u guild=%s why=%s fought_s=%u raiders=%u deaths=%d kills=%d defenders_down=%d",
				raid.id, (unsigned int)raid.target, (unsigned int)raid.attacker, raid.guildName.c_str(), why,
				fought ? (dwNow - raid.fightAt) / 1000U : 0U, (unsigned int)raid.raiders.size(), raid.deaths, raid.kills,
				raid.defendersDown);
		if (!fought || KVSetting(PLAYERBOT_KV_TAUNT_SEC) <= 0)
			return;
		// A word from each side.
		const bool retreat = strcmp(why, "time") != 0;
		char line[CHAT_MAX_LEN + 1];
		for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
		{
			LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
			if (!r || r->IsDead() || r->GetMapIndex() != raid.map)
				continue;
			if (retreat)
				FormatPlayerBotKVLine(line, sizeof(line), KV_RETREAT, KVBankSize(KV_RETREAT), PLAYERBOT_KV_COLOUR[raid.target]);
			else
				FormatPlayerBotKVLine(line, sizeof(line), KV_RAID_END, KVBankSize(KV_RAID_END), PLAYERBOT_KV_COLOUR[raid.target]);
			SayPlayerBotKVLine(r, line, dwNow, true);
			break;
		}
		for (size_t i = 0; i < raid.homeBots.size(); ++i)
		{
			LPCHARACTER d = CHARACTER_MANAGER::instance().FindByPID(raid.homeBots[(i + (size_t)number(0, 7)) % raid.homeBots.size()]);
			if (!d || d->IsDead() || d->GetMapIndex() != raid.map)
				continue;
			FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_WIN, KVBankSize(KV_DEFENDER_WIN), PLAYERBOT_KV_COLOUR[raid.attacker]);
			SayPlayerBotKVLine(d, line, dwNow, true);
			break;
		}
	}

	// The defenders called home: free bots of the raided kingdom on other
	// maps, of the raiders' levels.
	void CallPlayerBotKVDefenders(TPlayerBotKVRaid& raid, DWORD dwNow)
	{
		const int n = KVSetting(PLAYERBOT_KV_RAID_DEFENDERS);
		if (n <= 0)
			return;
		int lo = 255, hi = 0;
		for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
		{
			LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
			if (!r)
				continue;
			lo = std::min(lo, (int)r->GetLevel());
			hi = std::max(hi, (int)r->GetLevel());
		}
		if (hi == 0)
			return;
		std::vector<DWORD> pool;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c->GetEmpire() != raid.target || c->GetMapIndex() == raid.map ||
					(int)c->GetLevel() < std::max((int)PK_PROTECT_LEVEL, lo - 10) || (int)c->GetLevel() > hi + 10 ||
					!IsPlayerBotKVFree(c, it->second, dwNow))
				continue;
			pool.push_back(it->first);
		}
		while ((int)raid.called.size() < n && !pool.empty())
		{
			const size_t k = (size_t)number(0, (int)pool.size() - 1);
			raid.called.insert(pool[k]);
			pool[k] = pool.back();
			pool.pop_back();
		}
		sys_log(0, "PLAYERBOT_TOWNRAID: defenders called raid=%u target=%u called=%u levels=%d-%d",
				raid.id, (unsigned int)raid.target, (unsigned int)raid.called.size(), std::max((int)PK_PROTECT_LEVEL, lo - 10), hi + 10);
	}

	// The village's snapshot, once a pass: who a raider may look at, and the
	// raided kingdom's bots in it (the speakers).
	void RefreshPlayerBotKVSnapshot(TPlayerBotKVRaid& raid)
	{
		raid.victims.clear();
		raid.homeBots.clear();
		const CHARACTER_MANAGER::NAME_MAP& pcs = CHARACTER_MANAGER::instance().GetPCMap();
		for (CHARACTER_MANAGER::NAME_MAP::const_iterator it = pcs.begin(); it != pcs.end(); ++it)
		{
			LPCHARACTER pc = it->second;
			if (!pc || pc->GetMapIndex() != raid.map || pc->IsDead() || (int)pc->GetEmpire() == raid.attacker ||
					DISTANCE_APPROX(pc->GetX() - raid.pitchX, pc->GetY() - raid.pitchY) > PLAYERBOT_KV_TOWN_RADIUS + 2500)
				continue;
			raid.victims.push_back((DWORD)pc->GetVID());
			if ((int)pc->GetEmpire() == raid.target && pc->GetDesc() && pc->GetDesc()->IsBot() &&
					(int)pc->GetLevel() >= PK_PROTECT_LEVEL)
				raid.homeBots.push_back(pc->GetPlayerID());
		}
	}

	// The taunts: a line a side every RAID_TAUNT_SEC, about.
	void TauntPlayerBotKVRaid(TPlayerBotKVRaid& raid, DWORD dwNow)
	{
		const int gap = KVSetting(PLAYERBOT_KV_TAUNT_SEC);
		if (gap <= 0)
			return;
		char line[CHAT_MAX_LEN + 1];
		if ((int)(dwNow - raid.nextRaiderLine) >= 0)
		{
			raid.nextRaiderLine = dwNow + (DWORD)gap * (DWORD)number(70, 130) * 10U;
			std::vector<LPCHARACTER> speakers;
			for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
			{
				LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
				if (r && !r->IsDead() && r->GetMapIndex() == raid.map && IsPlayerBotKVRaiderFighting(*it, raid.map))
					speakers.push_back(r);
			}
			if (!speakers.empty())
			{
				FormatPlayerBotKVLine(line, sizeof(line), KV_RAIDER_TAUNT, KVBankSize(KV_RAIDER_TAUNT),
						PLAYERBOT_KV_COLOUR[raid.target]);
				SayPlayerBotKVLine(speakers[(size_t)number(0, (int)speakers.size() - 1)], line, dwNow);
			}
		}
		if ((int)(dwNow - raid.nextDefenderLine) >= 0 && !raid.homeBots.empty())
		{
			raid.nextDefenderLine = dwNow + (DWORD)gap * (DWORD)number(70, 130) * 10U;
			LPCHARACTER d = CHARACTER_MANAGER::instance().FindByPID(raid.homeBots[(size_t)number(0, (int)raid.homeBots.size() - 1)]);
			if (d && !d->IsDead())
			{
				FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_TAUNT, KVBankSize(KV_DEFENDER_TAUNT),
						PLAYERBOT_KV_COLOUR[raid.attacker]);
				SayPlayerBotKVLine(d, line, dwNow);
			}
		}
	}

	// One raid's step on the core's clock.
	void StepPlayerBotKVRaid(TPlayerBotKVRaid& raid, DWORD dwNow)
	{
		// Raiders whose trip is gone (taken by another business, ended, logged
		// out) are no longer the raid's.
		for (std::set<DWORD>::iterator it = raid.raiders.begin(); it != raid.raiders.end(); )
		{
			const TPlayerBotKVTrip* t = FindPlayerBotKVTrip(*it);
			if (raid.phase != KV_RAID_OVER && (!t || t->kind != KV_KIND_RAID || t->target != raid.target))
				raid.raiders.erase(it++);
			else
				++it;
		}
		switch (raid.phase)
		{
			case KV_RAID_GATHER:
			{
				int mustered = 0, alive = 0;
				long gx = 0, gy = 0;
				GetPlayerBotKVValleyGate(raid.target, gx, gy);
				for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
				{
					LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
					if (!r)
						continue;
					++alive;
					const TPlayerBotKVTrip* t = FindPlayerBotKVTrip(*it);
					if (t && t->phase == KV_MUSTER && r->GetMapIndex() == PLAYERBOT_KV_VALLEY &&
							DISTANCE_APPROX(r->GetX() - gx, r->GetY() - gy) <= PLAYERBOT_KV_MUSTER_RANGE)
						++mustered;
				}
				const bool all = alive > 0 && mustered >= alive;
				if (all || dwNow - raid.calledAt >= PLAYERBOT_KV_MUSTER_MS)
				{
					if (mustered < 2)
					{
						EndPlayerBotKVRaid(raid, "no_muster", dwNow);
						s_adwPlayerBotKVRaidNext[raid.target] = dwNow + PLAYERBOT_KV_RAID_RETRY_MS * 2;
						return;
					}
					raid.phase = KV_RAID_CROSS;
					raid.crossAt = dwNow;
					sys_log(0, "PLAYERBOT_TOWNRAID: crossing raid=%u target=%u mustered=%d of %d after_s=%u",
							raid.id, (unsigned int)raid.target, mustered, alive, (dwNow - raid.calledAt) / 1000U);
				}
				return;
			}
			case KV_RAID_CROSS:
			{
				bool inTown = false, onMap = false;
				for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
				{
					LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
					if (!r || r->GetMapIndex() != raid.map)
						continue;
					onMap = true;
					if (IsPlayerBotKVTownGround(r->GetMapIndex(), r->GetX(), r->GetY(), raid.target))
						inTown = true;
				}
				if (!inTown && dwNow - raid.crossAt < PLAYERBOT_KV_CROSSING_MS)
					return;
				if (!onMap)
				{
					EndPlayerBotKVRaid(raid, "no_crossing", dwNow);
					return;
				}
				raid.phase = KV_RAID_FIGHT;
				raid.fightAt = dwNow;
				int lo = KVSetting(PLAYERBOT_KV_RAID_MIN_MIN), hi = KVSetting(PLAYERBOT_KV_RAID_MAX_MIN);
				if (hi < lo)
					hi = lo;
				raid.fightUntil = dwNow + (DWORD)number(lo * 60, hi * 60) * 1000U;
				raid.nextRaiderLine = dwNow + 8000;
				raid.nextDefenderLine = dwNow + 12000;
				RefreshPlayerBotKVSnapshot(raid);
				CallPlayerBotKVDefenders(raid, dwNow);
				sys_log(0, "PLAYERBOT_TOWNRAID: fight raid=%u target=%u attacker=%u guild=%s raiders=%u lasts_s=%u village_bots=%u",
						raid.id, (unsigned int)raid.target, (unsigned int)raid.attacker, raid.guildName.c_str(),
						(unsigned int)raid.raiders.size(), (raid.fightUntil - dwNow) / 1000U, (unsigned int)raid.homeBots.size());
				if (KVSetting(PLAYERBOT_KV_TAUNT_SEC) > 0)
				{
					char line[CHAT_MAX_LEN + 1];
					for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
					{
						LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
						if (!r || r->GetMapIndex() != raid.map)
							continue;
						if (number(0, 1))
							FormatPlayerBotKVLine(line, sizeof(line), KV_RAID_START, KVBankSize(KV_RAID_START),
									PLAYERBOT_KV_KINGDOM[raid.target]);
						else
							snprintf(line, sizeof(line), "Gildia %s melduje sie w %s. Kto pierwszy do odstrzalu?",
									raid.guildName.c_str(), PLAYERBOT_KV_VILLAGE[raid.target]);
						SayPlayerBotKVLine(r, line, dwNow, true);
						break;
					}
					if (!raid.homeBots.empty())
					{
						LPCHARACTER d = CHARACTER_MANAGER::instance().FindByPID(raid.homeBots[(size_t)number(0, (int)raid.homeBots.size() - 1)]);
						if (d && !d->IsDead())
						{
							if (number(0, 1))
								FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_RALLY, KVBankSize(KV_DEFENDER_RALLY),
										PLAYERBOT_KV_VILLAGE[raid.target]);
							else
								FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_RALLY, KVBankSize(KV_DEFENDER_RALLY),
										PLAYERBOT_KV_COLOUR[raid.attacker]);
							SayPlayerBotKVLine(d, line, dwNow, true);
						}
					}
				}
				return;
			}
			case KV_RAID_FIGHT:
			{
				RefreshPlayerBotKVSnapshot(raid);
				// The raiders' deaths, each counted once.
				int fighting = 0;
				for (std::set<DWORD>::const_iterator it = raid.raiders.begin(); it != raid.raiders.end(); ++it)
				{
					LPCHARACTER r = CHARACTER_MANAGER::instance().FindByPID(*it);
					if (!r)
						continue;
					const bool down = r->IsDead() || r->GetHP() <= 0;
					if (r->GetMapIndex() == raid.map)
						++fighting;
					if (down && raid.down.insert(*it).second)
					{
						++raid.deaths;
						raid.deathTimes.push_back(dwNow);
						sys_log(0, "PLAYERBOT_TOWNRAID: raider down raid=%u pid=%u name=%s deaths=%d",
								raid.id, *it, r->GetName(), raid.deaths);
						// A defender near says so.
						if (KVSetting(PLAYERBOT_KV_TAUNT_SEC) > 0 && dwNow >= raid.nextEventLine && number(1, 100) <= 60 &&
								!raid.homeBots.empty())
						{
							LPCHARACTER d = CHARACTER_MANAGER::instance().FindByPID(raid.homeBots[(size_t)number(0, (int)raid.homeBots.size() - 1)]);
							if (d && !d->IsDead() && DISTANCE_APPROX(d->GetX() - r->GetX(), d->GetY() - r->GetY()) <= 4000)
							{
								raid.nextEventLine = dwNow + PLAYERBOT_KV_EVENT_LINE_GAP_MS;
								char line[CHAT_MAX_LEN + 1];
								FormatPlayerBotKVLine(line, sizeof(line), KV_DEFENDER_KILL, KVBankSize(KV_DEFENDER_KILL), r->GetName());
								SayPlayerBotKVLine(d, line, dwNow);
							}
						}
					}
					else if (!down)
						raid.down.erase(*it);
				}
				const DWORD window = (DWORD)KVSetting(PLAYERBOT_KV_RETREAT_FAST_MIN) * 60000U;
				while (!raid.deathTimes.empty() && dwNow - raid.deathTimes.front() > window)
					raid.deathTimes.pop_front();
				const int n = std::max<int>(1, (int)raid.raiders.size());
				if (raid.deaths * 100 >= n * KVSetting(PLAYERBOT_KV_RETREAT_DEATHS_PCT))
					EndPlayerBotKVRaid(raid, "retreat_many", dwNow);
				else if ((int)raid.deathTimes.size() * 100 >= n * KVSetting(PLAYERBOT_KV_RETREAT_FAST_PCT))
					EndPlayerBotKVRaid(raid, "retreat_fast", dwNow);
				else if ((int)(dwNow - raid.fightUntil) >= 0)
					EndPlayerBotKVRaid(raid, "time", dwNow);
				else if (fighting == 0)
					EndPlayerBotKVRaid(raid, "no_raiders", dwNow);
				else
					TauntPlayerBotKVRaid(raid, dwNow);
				return;
			}
			default:
				return;
		}
	}

	bool PlayerBotKVRaidNowRequested(int& target)
	{
		target = 0;
		struct stat st;
		if (stat(PLAYERBOT_RAID_NOW_PATH, &st) != 0)
			return false;
		if (s_tPlayerBotKVNowSeen == (time_t)-1)
		{
			s_tPlayerBotKVNowSeen = st.st_mtime;
			return false;
		}
		if (st.st_mtime <= s_tPlayerBotKVNowSeen)
			return false;
		s_tPlayerBotKVNowSeen = st.st_mtime;
		FILE* fp = fopen(PLAYERBOT_RAID_NOW_PATH, "r");
		if (fp)
		{
			int v = 0;
			if (fscanf(fp, "%d", &v) == 1 && v >= 1 && v <= 3)
				target = v;
			fclose(fp);
		}
		return true;
	}

	// The world's pass: the trips' census and starts, the raids' clocks.
	void ManagePlayerBotKingdomVisits(DWORD dwNow)
	{
		if (s_dwPlayerBotKVNextPass != 0 && (int)(dwNow - s_dwPlayerBotKVNextPass) < 0)
			return;
		s_dwPlayerBotKVNextPass = dwNow + PLAYERBOT_KV_PASS_MS;
		const bool on = IsPlayerBotKVOn();
		if (!on)
		{
			if (s_bPlayerBotKVWasOn && !s_mapPlayerBotKVTrips.empty())
				EndAllPlayerBotKVTrips("switched_off", dwNow);
			s_bPlayerBotKVWasOn = false;
			return;
		}
		s_bPlayerBotKVWasOn = true;
		// Channel 1 only: the stands are its (playerbot_channel_rules.h - a
		// buyer on another channel asks to be moved there) and so are the
		// guild wars.
		// And the core that hosts Orc Valley - the only one a trip can start
		// from or a raid be called on (a GM's event flag is read here alone).
		if (g_bChannel != 1 || !IsPlayerBotMapHostedHere(PLAYERBOT_KV_VALLEY))
			return;
		// Trips of characters no longer in the world.
		for (std::map<DWORD, TPlayerBotKVTrip>::iterator it = s_mapPlayerBotKVTrips.begin(); it != s_mapPlayerBotKVTrips.end(); )
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first))
			{
				sys_log(0, "PLAYERBOT_VISIT: end pid=%u why=gone phase=%s", it->first, GetPlayerBotKVPhaseName(it->second.phase));
				s_mapPlayerBotKVTrips.erase(it++);
			}
			else
				++it;
		}
		if (s_mapPlayerBotKVSpared.size() > 256)
			for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotKVSpared.begin(); it != s_mapPlayerBotKVSpared.end(); )
				if (KVDue(dwNow, it->second))
					s_mapPlayerBotKVSpared.erase(it++);
				else
					++it;
		if (s_dwPlayerBotKVNextShopper == 0)
		{
			s_dwPlayerBotKVNextShopper = dwNow + PLAYERBOT_KV_FIRST_DELAY_MS;
			for (int e = 1; e <= 3; ++e)
				s_adwPlayerBotKVRaidNext[e] = dwNow + 5 * 60 * 1000 +
						(DWORD)(e - 1) * (DWORD)KVSetting(PLAYERBOT_KV_RAID_EVERY_MIN) * 20000U + (DWORD)number(0, 180) * 1000U;
			return;
		}
		// The shoppers: one at a time on the hour's clock, a few at once when a
		// GM asks (the event flag bot_visit_now = how many).
		{
			const int forced = quest::CQuestManager::instance().GetEventFlag("bot_visit_now");
			if (forced > 0 && dwNow - s_dwPlayerBotKVVisitFlagHandledAt > 10000)
			{
				s_dwPlayerBotKVVisitFlagHandledAt = dwNow;
				quest::CQuestManager::instance().RequestSetEventFlag("bot_visit_now", 0);
				StartPlayerBotKVShoppers(std::min(forced, 30), dwNow, "gm_now");
			}
			const int perHour = KVSetting(PLAYERBOT_KV_PER_HOUR);
			if (perHour > 0 && (int)(dwNow - s_dwPlayerBotKVNextShopper) >= 0)
			{
				const DWORD gap = 3600000U / (DWORD)perHour;
				s_dwPlayerBotKVNextShopper = dwNow + gap * (DWORD)number(70, 130) / 100U;
				StartPlayerBotKVShoppers(1, dwNow, "clock");
			}
		}
		// The raids: channel 1, the guild wars' channel.
		if (IsPlayerBotKVRaidsOn())
		{
			if (s_tPlayerBotKVNowSeen == (time_t)-1)
				s_tPlayerBotKVNowSeen = time(NULL);
			int forcedTarget = 0;
			bool forced = PlayerBotKVRaidNowRequested(forcedTarget);
			if (!forced)
			{
				const int flag = quest::CQuestManager::instance().GetEventFlag("bot_raid_now");
				if (flag > 0 && dwNow - s_dwPlayerBotKVFlagHandledAt > 10000)
				{
					s_dwPlayerBotKVFlagHandledAt = dwNow;
					quest::CQuestManager::instance().RequestSetEventFlag("bot_raid_now", 0);
					forced = true;
					forcedTarget = flag >= 1 && flag <= 3 ? flag : 0;
				}
			}
			if (forced && forcedTarget == 0)
			{
				// The kingdom whose raid is due soonest, of those with none.
				DWORD soonest = 0;
				for (int e = 1; e <= 3; ++e)
				{
					if (s_mapPlayerBotKVRaids.count((BYTE)e))
						continue;
					if (forcedTarget == 0 || (int)(s_adwPlayerBotKVRaidNext[e] - soonest) < 0)
					{
						forcedTarget = e;
						soonest = s_adwPlayerBotKVRaidNext[e];
					}
				}
			}
			for (int e = 1; e <= 3; ++e)
			{
				std::map<BYTE, TPlayerBotKVRaid>::iterator it = s_mapPlayerBotKVRaids.find((BYTE)e);
				if (it != s_mapPlayerBotKVRaids.end())
				{
					StepPlayerBotKVRaid(it->second, dwNow);
					// Forgotten once its raiders are home (or after half an hour).
					bool anyTrip = false;
					for (std::set<DWORD>::const_iterator r = it->second.raiders.begin(); r != it->second.raiders.end() && !anyTrip; ++r)
						anyTrip = IsPlayerBotOnKingdomVisit(*r);
					if (it->second.phase == KV_RAID_OVER && (!anyTrip || dwNow - it->second.overAt > 30 * 60 * 1000))
					{
						sys_log(0, "PLAYERBOT_TOWNRAID: closed raid=%u target=%u why=%s", it->second.id,
								(unsigned int)e, it->second.overWhy);
						s_mapPlayerBotKVRaids.erase(it);
					}
					continue;
				}
				const bool due = (int)(dwNow - s_adwPlayerBotKVRaidNext[e]) >= 0;
				const bool now = forced && forcedTarget == e;
				if (!due && !now)
					continue;
				bool hosted = false;
				for (int a = 1; a <= 3 && !hosted; ++a)
					hosted = IsPlayerBotKVRouteHosted(a, e);
				if (!hosted)
				{
					s_adwPlayerBotKVRaidNext[e] = dwNow + 60 * 60 * 1000;
					continue;
				}
				if (CallPlayerBotKVRaid((BYTE)e, dwNow, now ? "now" : "clock"))
				{
					const DWORD every = (DWORD)KVSetting(PLAYERBOT_KV_RAID_EVERY_MIN) * 60000U;
					s_adwPlayerBotKVRaidNext[e] = dwNow + every * (DWORD)number(90, 110) / 100U;
				}
				else
					s_adwPlayerBotKVRaidNext[e] = dwNow + PLAYERBOT_KV_RAID_RETRY_MS;
			}
		}
		else if (!s_mapPlayerBotKVRaids.empty())
		{
			for (std::map<BYTE, TPlayerBotKVRaid>::iterator it = s_mapPlayerBotKVRaids.begin(); it != s_mapPlayerBotKVRaids.end(); ++it)
				EndPlayerBotKVRaid(it->second, "switched_off", dwNow);
			s_mapPlayerBotKVRaids.clear();
		}
		// Once a minute, what is under way.
		if (s_dwPlayerBotKVNextCensus == 0 || (int)(dwNow - s_dwPlayerBotKVNextCensus) >= 0)
		{
			s_dwPlayerBotKVNextCensus = dwNow + 60000;
			int shoppers = 0, raiders = 0;
			int byPhase[KV_HOME_GATE + 1] = {};
			for (std::map<DWORD, TPlayerBotKVTrip>::const_iterator it = s_mapPlayerBotKVTrips.begin(); it != s_mapPlayerBotKVTrips.end(); ++it)
			{
				++(it->second.kind == KV_KIND_RAID ? raiders : shoppers);
				if (it->second.phase <= KV_HOME_GATE)
					++byPhase[it->second.phase];
			}
			if (shoppers || raiders || !s_mapPlayerBotKVRaids.empty())
				sys_log(0, "PLAYERBOT_VISIT: census shoppers=%d raiders=%d raids=%u valley=%d crossing=%d town=%d fight=%d dwell=%d leaving=%d started=%u home=%u failed=%u raids_called=%u",
						shoppers, raiders, (unsigned int)s_mapPlayerBotKVRaids.size(), byPhase[KV_TO_VALLEY],
						byPhase[KV_TO_GATE] + byPhase[KV_MUSTER] + byPhase[KV_CROSS], byPhase[KV_TO_TOWN], byPhase[KV_FIGHT],
						byPhase[KV_DWELL], byPhase[KV_LEAVE] + byPhase[KV_HOME_GATE], s_uPlayerBotKVTripsStarted,
						s_uPlayerBotKVTripsHome, s_uPlayerBotKVTripsFailed, s_uPlayerBotKVRaids);
		}
	}
}

#endif
