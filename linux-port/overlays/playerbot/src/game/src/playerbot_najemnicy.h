#pragma once
// MT2009_PLUS_NAJEMNICY_V1: "Najemnicy" - a player's own hired party (the owner, 8 November 2026,
// /opt/metin2/cache/yohara/najemnicy-plan.md: "stala druzyna botow gracza do lochow, map i expienia", the answer to the
// withdrawn Towarzysz). Stage 1, the core: the tables, the unlock, creating / summoning / dismissing, level, stats and
// skills, the vault and the hourly fee, the party, following and fighting, logging out with the player, the guild and
// guild-war rules, the equipment placeholder (give one piece / take everything back).
//
// What a mercenary is:
//   * a dedicated identity of its own, made GAME-SIDE when the player asks for it in the "Najemnicy" quest (the
//     Towarzysz's new-identity path, MakePlayerBotSidekickIdentity: NewPlayerTable2 + the account / player /
//     player_index rows, written through AccountDB as that one is): an account playerbot_njNNNN (password '!', status
//     BLOCK - no person logs in there), the character with the class, sex, path and name the player chose (letters
//     and digits, the engine's check_name and the ban list, unique in player.player), its row in player.najemnicy.
//     It is NOT in common.playerbot_seed_state, so the population's registry never knows it - as PVP Fan's characters
//     (playerbot_pvpfan.h): no hunting, market, trading, quests of the bots, rankings, SM grants, census or chat;
//   * owned by one character for good (player.najemnicy.owner_pid), in one of the owner's slots. The slots are the
//     Kolekcjoner Najemnikow's (the owner's unlock, plan's last section): each of its 6 tasks done is a tier that counts
//     once the character has the tier's level - 1 task + 80 -> 2, 2 + 85 -> 3, 3 + 90 -> 4, 4 + 95 -> 5, 5 + 100 -> 6,
//     6 + 105 -> 7 (a party is the player + 7). Stage 1 has no collector yet: the tasks count is the quest flag
//     najemnicy.tasks (the collector's quest will raise it) or the row player.najemnicy_unlock.tasks, which the GM's
//     "/najemnicy odblokuj|zadania|zablokuj" and the Seban panel write - the higher of the two counts (GetNajemnicyTasks);
//     the test flag m2_najemnicy_free_unlock counts as all six;
//   * offline unless summoned. "Wezwij" logs it in straight beside the player on the player's core and channel - PVP
//     Fan's own spawn (CPlayerBotManager::SpawnPvpFan with the mercenary's account: the registry's guards stepped
//     over for that one pid) and PVP Fan's load hook (CPlayerBotManager::PlaceLoadingBot asks
//     PlacePlayerBotNajemnikLoading, which answers with the owner's map and position);
//   * at its first entry its bag is emptied (PVP Fan's ClearPlayerBotPvpFanBelongings) - the starter items of a new
//     character never become the player's through "take everything back";
//   * level = the owner's level (ResetPoint, then the bots' own stat allocator ManagePlayerBotStats for its path);
//     skills are "half" the owner's counted from M1 - L < 20: L, else 20 + (L - 20) / 2 (P -> G1, M4 -> M2, M1 -> M1),
//     the owner's best skill onto the mercenary's main one (the path's build order, GetPlayerBotSkillBuild), the
//     second onto the second and so on; again at every summon, every owner's level-up and when it outgrows the owner;
//   * its tick is its own (ManagePlayerBotNajemnikBot, before every pass of the population - as a PvP-fan bot's): in
//     the owner's party (made when the owner has none), at the owner's side, fighting what the owner fights and what
//     attacks either of them, as the Towarzysz did - the same helpers (FindPlayerBotSidekickFoe,
//     FightPlayerBotSidekickFoe, GetPlayerBotSidekickSpot, WalkPlayerBotSidekick, ManagePlayerBotBuffPerson), its own
//     drops (the party's share of a kill that is its own) into its own bag;
//   * no trade (an exchange is cancelled at once), no shop, no market; it strikes no character and no character
//     strikes it (battle_is_attackable, NajemnicyBlockAttack) except in a guild war of its own guild;
//   * it may join the owner's guild ("Gildia" in the quest, or the owner's invitation) - Balathor wants the party in
//     the leader's guild - and it follows its owner onto a guild war's map only when it is in the owner's guild;
//   * a death costs nothing: no item dropped (CHARACTER::ItemDropPenalty, NajemnikNoItemDrop), no experience (the
//     dead event that restarts a character - and takes the experience - is cancelled); it stands up beside the owner
//     after 30 s;
//   * the fee: m2_najemnicy_price_h a summoned mercenary an hour (5 000 000), taken a minute at a time (the first
//     minute at its entry) from the owner's vault (player.najemnicy_vault, the quest's "Wplac"); a warning when ten
//     minutes are left; all of the owner's mercenaries dismissed when the vault cannot pay the next minute;
//   * it leaves when the owner dismisses it, when the owner is out of this core's world for 20 s (a logout - it comes
//     back at the next login, V3) or on another core or channel (at once - and in again there, V3; a warp between two
//     maps of one core it follows), when the vault is empty or when the module is switched off.
//
// MT2009_PLUS_NAJEMNICY_V2 - stage 2, the equipment: the Towarzysz's equipment window (client uisidekickinventory.py,
// the same bag window, costume panel and protocol) re-targeted to one mercenary - "/najemnicy eq <nr> ..." and
// "/najemnicy okno <nr>" (HandleNajemnikEqCommand; the target board's "Ekwipunek" through NajemnikVids). Only the owner,
// only a summoned mercenary within 50 m on its map. What it wears and carries stays its owner's: no AI touches it (it
// sells, drops, trades and stores nothing; nothing goes into the extra inventory's storages - PlayerBotEkwRouteWindow);
// the engine's rules of wearing apply. It uses its owner's consumables from its bag and never buys
// (UseNajemnikConsumables): HP/SP potions at the bots' thresholds, the auto potions, and in a fight the green and purple
// potions, the dews, the Energy Crystal and the other buff items. Its drops and rewards go into its bag: its share of a
// kill, the people's boss loot (CHARACTER::PickupItem lets it - NajemnikMayTakePeopleLoot), the dungeons' rewards that
// count it among the people (pc.is_najemnik: Razador, Nemere, the Blue Dragon, the Scorpion Ruins, the Ancient Jungle,
// Wukong's Hill, Atlantis, Meley, the Snake Temple, the Depths) and the Zodiac's chests (every character on the floor).
//
// MT2009_PLUS_NAJEMNICY_V3 - stage 3, maps, orders and dungeons (no engine edit; server-patches/najemnicy/README.md):
//   * the rejoin: player.najemnicy.summoned keeps who is summoned (only a dismissal, the empty vault, the module off or
//     a load that never came clear it). An owner seen on another core or channel (P2P) takes its mercenaries off this
//     core at once (owner_moved, still in the owner's party); the quest's login on the core the owner arrived on runs
//     "/najemnicy przybycie" (OnNajemnicyOwnerArrived): the summoned ones not here are spawned beside the owner (PVP
//     Fan's spawn and PlaceLoadingBot, a dungeon's instance too), tried every 2 s for 90 s (ProcessNajemnicyRejoins).
//     player.najemnicy_vault.billed_until carries the paid minute across the move; a paid minute that ran out over
//     30 s ago makes the arrival a login, when the owner's najemnicy.no_rejoin / m2_najemnicy_rejoin_off decide
//     ("Najemnicy wracaja..."). The arrival also sends NajemnikVids at once (no 20 s wait for "Ekwipunek");
//   * the orders (order_mode, no_loot; "/najemnicy rozkaz", the letter, the target board's "Rozkazy"): za mna, stoj
//     tutaj, bij moj cel, walcz sam w poblizu, the loot switch (ChooseNajemnikFoe);
//   * the dungeons with the owner as leader (ManageNajemnikDungeon): the party bots' dungeon items and fight round the
//     owner, the Yohara keys by class over the owner's party (ManagePlayerBotYdgItems), never a way out of its own.
//
// Commands (cmd.cpp "najemnicy", server-patches/najemnicy; the quest's buttons use them): /najemnicy [lista] | sync |
// stworz <rasa 0-7> <droga 1-2> <imie> | wezwij <miejsce|wszyscy> | odwolaj <miejsce|wszyscy> | wplac <yang> |
// skarbiec | okno <miejsce> | eq <miejsce> [polecenie] | daj <miejsce> <pole> | zabierz <miejsce> | gildia <miejsce> |
// gildia_wyjdz <miejsce> |
// zwolnij <miejsce> tak; GM (GM_HIGH_WIZARD): odblokuj <postac> [zadania, 6] | zadania <postac> <0-6> |
// zablokuj <postac> | spis.
//
// Switches - event flags (the game's, or the player.quest row with dwPID 0 the Seban panel writes, read every 10 s):
// m2_najemnicy_off (1 = nobody summons, the summoned leave), m2_najemnicy_free_unlock (1 = everybody counts all six
// collector tasks - the level table still decides, for the tests), m2_najemnicy_price_h (the hourly fee of one mercenary; 0 = 5 000 000). Logs:
// "NAJEMNICY:" lines (throttled where they repeat), a census every 10 minutes.
//
// An implementation fragment in the sense playerbot_types.h describes: included once, after playerbot_pvpfan.h (it
// uses PVP Fan's spawn, load hook and belongings reset and the Towarzysz's fight, walk and identity helpers).
#include <sstream>
#include <functional>

int NajemnicyBlockAttack(LPCHARACTER ch, LPCHARACTER victim);
bool NajemnikNoItemDrop(LPCHARACTER ch);
bool NajemnikMayTakePeopleLoot(LPCHARACTER ch);	// MT2009_PLUS_NAJEMNICY_V2
bool IsNajemnikCharacter(LPCHARACTER ch);			// MT2009_PLUS_NAJEMNICY_V2
void PlayerBotNajemnicyCommand(LPCHARACTER ch, const char* argument);

namespace
{
	const DWORD NAJEMNICY_TICK_MS = 1000;
	const DWORD NAJEMNICY_FLAG_POLL_MS = 10000;
	const DWORD NAJEMNICY_CENSUS_MS = 10 * 60 * 1000;
	const DWORD NAJEMNICY_BILL_MS = 60 * 1000;
	const DWORD NAJEMNICY_LOAD_TIMEOUT_MS = 45000;
	const DWORD NAJEMNICY_OWNER_GONE_MS = 20000;
	const DWORD NAJEMNICY_REVIVE_MS = 30000;
	const DWORD NAJEMNICY_SYNC_CHECK_MS = 5000;
	const DWORD NAJEMNICY_PARTY_CHECK_MS = 3000;
	const DWORD NAJEMNICY_SAVE_MS = 5 * 60 * 1000;
	const DWORD NAJEMNICY_LOOT_MS = 500;
	const DWORD NAJEMNICY_LOOT_GIVE_UP_MS = 8000;
	const int NAJEMNICY_LOOT_RANGE = 1200;
	const int NAJEMNICY_FOLLOW_DISTANCE = 450;
	const int NAJEMNICY_TELEPORT_DISTANCE = 3000;
	const int NAJEMNICY_DG_TELEPORT_DISTANCE = 7000;	// MT2009_PLUS_NAJEMNICY_V4: inside a dungeon (the objective's room)
	const long long NAJEMNICY_DEFAULT_PRICE_H = 5000000LL;
	const int NAJEMNICY_WARN_MINUTES = 10;
	const int NAJEMNICY_MIN_LEVEL = 80;
	const int NAJEMNICY_MAX_SLOTS = 7;
	const int NAJEMNICY_MAX_TASKS = 6;	// the Kolekcjoner Najemnikow's tasks
	const int NAJEMNICY_RETIRED_DELETE_MINUTES = 20;
	const unsigned int NAJEMNICY_MAX_SEQ = 9999;	// playerbot_nj%04u: 16 characters, the account's login column
	// MT2009_PLUS_NAJEMNICY_V2: the equipment window and the consumables.
	const int NAJEMNICY_EQ_RANGE = 5000;					// the owner within 50 m of it, on its map
	const DWORD NAJEMNICY_PENDING_WEAR_MS = 20000;			// how long a piece put on mid-blow waits for its moment
	const DWORD NAJEMNICY_CONSUMABLE_MS = 1000;
	const DWORD NAJEMNICY_BUFF_ITEM_MS = 2000;				// one buff item every two seconds at most
	const DWORD NAJEMNICY_BUFF_RETRY_MS = 30000;			// a buff item the engine refused waits this long
	const DWORD NAJEMNICY_FIGHT_MEMORY_MS = 10000;			// "in a fight": a blow or a target in the last 10 s
	const DWORD NAJEMNICY_BAG_SWEEP_MS = 5000;
	const DWORD NAJEMNICY_BAG_FULL_TELL_MS = 5 * 60 * 1000;
	const DWORD NAJEMNICY_VID_RESEND_MS = 20000;
	// MT2009_PLUS_NAJEMNICY_V3: the rejoin after a core / channel change and after a login, the orders.
	const DWORD NAJEMNICY_REJOIN_WINDOW_MS = 90000;		// how long an arrived owner's mercenaries are waited for
	const DWORD NAJEMNICY_REJOIN_TRY_MS = 2000;			// a try every two seconds (the old core lets them go first)
	const int NAJEMNICY_MOVE_GRACE_S = 30;					// a paid minute ran out at most 30 s ago: a move, not a login
	const DWORD NAJEMNICY_ARRIVAL_VID_MS = 3000;			// the VIDs again 3 s after an arrival (the warp's new client)
	const int NAJEMNICY_HOLD_RETURN = 200;					// "Stoj tutaj": back to its spot beyond 2 m
	const int NAJEMNICY_HOLD_FIGHT_RANGE = 700;			// ... and what stands within 7 m of the spot it takes on
	const int NAJEMNICY_FREE_RANGE = 2500;					// "Walcz sam w poblizu": any monster or stone within 25 m of the owner
	const int NAJEMNICY_FREE_LEASH = 1500;					// ... and back to the owner beyond 15 m when nothing is left

	// MT2009_PLUS_NAJEMNICY_V3: the owner's orders (player.najemnicy.order_mode; the loot switch is no_loot).
	enum ENajemnikOrder
	{
		NAJEMNIK_ORDER_FOLLOW = 0,	// "Za mna" (default): at the owner's side, the owner's fight and what is near
		NAJEMNIK_ORDER_HOLD = 1,	// "Stoj tutaj": keeps its spot, fights what comes to it
		NAJEMNIK_ORDER_FOCUS = 2,	// "Bij moj cel": the owner's target only (else what hits the owner or itself)
		NAJEMNIK_ORDER_FREE = 3,	// "Walcz sam w poblizu": every monster and stone near the owner, bosses too
		NAJEMNIK_ORDER_COUNT = 4,
	};

	enum ENajemnikPhase
	{
		NAJEMNIK_LOADING = 0,
		NAJEMNIK_READY,
	};

	struct TNajemnik
	{
		DWORD pid = 0;
		DWORD ownerPid = 0;
		DWORD accountId = 0;
		BYTE slot = 0;
		BYTE race = 0;
		BYTE group = 1;
		bool setupDone = false;
		std::string login;
		std::string name;
		int phase = NAJEMNIK_LOADING;
		DWORD askedAt = 0;
		DWORD readyAt = 0;
		DWORD deadAt = 0;
		DWORD nextSync = 0;
		DWORD nextParty = 0;
		DWORD nextLoot = 0;
		DWORD nextSave = 0;
		DWORD lootVid = 0;
		DWORD lootSince = 0;
		DWORD nextCatchUp = 0;
		int syncedOwnerLevel = -1;
		bool dismiss = false;
		std::string dismissWhy;
		// The Towarzysz's per-companion runtime, which its fight helpers keep (FightPlayerBotSidekickFoe).
		// MT2009_PLUS_NAJEMNICY_V2: and the equipment window's picture (mapEqSent, dwEqGen, llEqGoldSent).
		TPlayerBotSidekickRuntime rt;
		// MT2009_PLUS_NAJEMNICY_V2: a piece the owner put on while a blow was still landing - worn at the first
		// moment the engine lets it (RetryNajemnikPendingWear), the fight held off for it.
		DWORD pendingWearItem = 0;
		int pendingWearSlot = -1;
		DWORD pendingWearUntil = 0;
		// MT2009_PLUS_NAJEMNICY_V2: its consumables (UseNajemnikConsumables), its storages' sweep, the full bag's word.
		DWORD nextConsumable = 0;
		DWORD nextBuffItem = 0;
		DWORD nextBagSweep = 0;
		DWORD nextBagFullTell = 0;
		std::map<DWORD, DWORD> mapItemRetry;	// vnum -> when a buff item of it may be tried again
		// MT2009_PLUS_NAJEMNICY_V3: its order, the loot switch, the spot of "Stoj tutaj", a rejoin's quiet entry.
		BYTE order = NAJEMNIK_ORDER_FOLLOW;
		bool noLoot = false;
		long holdMap = 0;
		long holdX = 0;
		long holdY = 0;
		bool rejoin = false;
		// MT2009_PLUS_NAJEMNICY_V4: a dungeon's duty under way (the egg chamber, an NPC across the room, the objective) -
		// no catch-up beside the owner till then while both stand in one instance (ManageNajemnikDungeon).
		DWORD dutyUntil = 0;
	};

	struct TNajemnicyOwner
	{
		DWORD nextBill = 0;
		DWORD goneSince = 0;
		long long carry = 0;	// the fee's remainder (price * n mod 60), carried to the next minute
		bool warned = false;
		// MT2009_PLUS_NAJEMNICY_V2: what the owner's client was last told of its mercenaries' VIDs (NajemnikVids).
		std::string vidSig;
		DWORD nextVidSend = 0;
	};

	// MT2009_PLUS_NAJEMNICY_V3: an owner who arrived on this core (a login, a warp from another core or channel) and
	// whose summoned mercenaries are on their way - tried every NAJEMNICY_REJOIN_TRY_MS until NAJEMNICY_REJOIN_WINDOW_MS.
	struct TNajemnicyRejoin
	{
		DWORD until = 0;
		DWORD nextTry = 0;
		bool login = false;	// a login (they "come back"), not a move
	};
	std::map<DWORD, TNajemnicyRejoin> s_mapNajemnicyRejoin;	// owner pid -> its rejoin

	// MT2009_PLUS_NAJEMNICY_V2: the owner's client told which characters are its mercenaries (defined with the window).
	void AnnounceNajemnicyVids(LPCHARACTER owner, TNajemnicyOwner& rec, DWORD dwNow);
	// MT2009_PLUS_NAJEMNICY_V3: the arrived owners' rejoins (defined with the commands, after SummonNajemnik).
	void ProcessNajemnicyRejoins(DWORD dwNow);

	std::map<DWORD, TNajemnik> s_mapNajemnik;				// mercenary pid -> its runtime (summoned on this core)
	std::map<DWORD, TNajemnicyOwner> s_mapNajemnicyOwner;	// owner pid -> its billing
	DWORD s_dwNajemnicyNextTick = 0;
	DWORD s_dwNajemnicyNextFlagPoll = 0;
	DWORD s_dwNajemnicyNextCensus = 0;
	bool s_bNajemnicyDbOff = false;
	bool s_bNajemnicyDbFreeUnlock = false;
	long long s_llNajemnicyDbPrice = 0;
	bool s_bNajemnicyTables = false;
	// The census's counters since the last one.
	unsigned int s_uNajemnicySummons = 0, s_uNajemnicyDismissals = 0, s_uNajemnicyEmpty = 0, s_uNajemnicyCreated = 0,
			s_uNajemnicyRetired = 0, s_uNajemnicyDeaths = 0, s_uNajemnicyDeleted = 0;
	long long s_llNajemnicyBilled = 0, s_llNajemnicyDeposited = 0;

	// ------------------------------------------------------------------ switches and lookups

	bool IsPlayerBotNajemnikPID(DWORD pid)
	{
		return !s_mapNajemnik.empty() && s_mapNajemnik.find(pid) != s_mapNajemnik.end();
	}

	bool IsNajemnicyOff()
	{
		return s_bNajemnicyDbOff || quest::CQuestManager::instance().GetEventFlag("m2_najemnicy_off") != 0;
	}

	bool IsNajemnicyFreeUnlock()
	{
		return s_bNajemnicyDbFreeUnlock || quest::CQuestManager::instance().GetEventFlag("m2_najemnicy_free_unlock") != 0;
	}

	long long GetNajemnicyPriceH()
	{
		const long long game = quest::CQuestManager::instance().GetEventFlag("m2_najemnicy_price_h");
		if (game > 0)
			return game;
		if (s_llNajemnicyDbPrice > 0)
			return s_llNajemnicyDbPrice;
		return NAJEMNICY_DEFAULT_PRICE_H;
	}

	// MT2009_PLUS_NAJEMNICY_V1 (the Kolekcjoner Najemnikow, the owner, 8 November 2026): every task of the collector
	// done is a tier, and a tier counts once the character has its level - 1 task + 80 -> 2 mercenaries, 2 + 85 -> 3,
	// 3 + 90 -> 4, 4 + 95 -> 5, 5 + 100 -> 6, 6 + 105 -> 7. Tasks done early wait for the level. 0 = locked.
	int GetNajemnicySlots(int tasks, int level)
	{
		int tiers = 0;
		for (int t = 1; t <= MIN(tasks, NAJEMNICY_MAX_TASKS); ++t)
			if (level >= NAJEMNICY_MIN_LEVEL + (t - 1) * 5)
				tiers = t;
		return tiers > 0 ? MIN(NAJEMNICY_MAX_SLOTS, tiers + 1) : 0;
	}

	// The skill of a mercenary from the owner's: the same below M1, half the way above it.
	int GetNajemnikHalfSkill(int ownerLevel)
	{
		if (ownerLevel < 20)
			return MAX(0, ownerLevel);
		return 20 + (ownerLevel - 20) / 2;
	}

	const char* GetNajemnikClassName(BYTE race)
	{
		switch (race % 4)
		{
			case 0: return "Wojownik";
			case 1: return "Ninja";
			case 2: return "Sura";
			default: return "Szaman";
		}
	}

	BYTE GetNajemnikJobOfRace(BYTE race)
	{
		// player.job: 0 warrior, 1 ninja, 2 sura, 3 shaman in the sex they were first made in, + 4 the other sex.
		static const BYTE jobs[8] = { JOB_WARRIOR, JOB_ASSASSIN, JOB_SURA, JOB_SHAMAN, JOB_WARRIOR, JOB_ASSASSIN, JOB_SURA, JOB_SHAMAN };
		return jobs[race & 7];
	}

	const char* GetNajemnikPathName(BYTE race, BYTE group)
	{
		static const char* names[4][2] = { { "Cialo", "Mental" }, { "Skrytobojca", "Lucznik" }, { "Bron", "Czarna Magia" },
				{ "Smok", "Leczenie" } };
		return names[GetNajemnikJobOfRace(race) & 3][group == 2 ? 1 : 0];
	}

	void TellNajemnicy(LPCHARACTER owner, const char* fmt, ...)
	{
		if (!owner || !owner->GetDesc())
			return;
		char text[512];
		va_list args;
		va_start(args, fmt);
		vsnprintf(text, sizeof(text), fmt, args);
		va_end(args);
		owner->ChatPacket(CHAT_TYPE_INFO, "[Najemnicy] %s", text);
	}

	LPCHARACTER FindNajemnicyOwnerHere(DWORD ownerPid)
	{
		LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(ownerPid);
		if (!owner || !owner->GetDesc() || owner->GetDesc()->IsBot())
			return NULL;
		return owner;
	}

	// ------------------------------------------------------------------ database

	std::unique_ptr<SQLMsg> NajemnicyQuery(const char* fmt, ...)
	{
		char buf[4096];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		return std::unique_ptr<SQLMsg>(AccountDB::instance().DirectQuery(buf));
	}

	bool NajemnicyOk(const std::unique_ptr<SQLMsg>& m)
	{
		return m.get() && m->uiSQLErrno == 0 && m->Get();
	}

	// The first column of the first row, or fallback.
	long long NajemnicyNumber(const std::unique_ptr<SQLMsg>& m, long long fallback)
	{
		MYSQL_ROW row = NULL;
		if (!NajemnicyOk(m) || !m->Get()->pSQLResult || !(row = mysql_fetch_row(m->Get()->pSQLResult)) || !row[0])
			return fallback;
		long long value = fallback;
		str_to_number(value, row[0]);
		return value;
	}

	// The tables, as najemnicy.sql makes them (the migration runs before the cores; this is the net for a world whose
	// migration has not run yet).
	bool EnsureNajemnicyTables()
	{
		if (s_bNajemnicyTables)
			return true;
		std::unique_ptr<SQLMsg> a(NajemnicyQuery(
				"CREATE TABLE IF NOT EXISTS player.najemnicy ("
				"merc_pid INT UNSIGNED NOT NULL PRIMARY KEY, owner_pid INT UNSIGNED NOT NULL, "
				"slot TINYINT UNSIGNED NOT NULL DEFAULT 1, account_id INT UNSIGNED NOT NULL DEFAULT 0, "
				"login VARCHAR(16) NOT NULL DEFAULT '', seq INT UNSIGNED NOT NULL DEFAULT 0, "
				"job TINYINT UNSIGNED NOT NULL DEFAULT 0, skill_group TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"sex TINYINT UNSIGNED NOT NULL DEFAULT 0, name VARCHAR(24) NOT NULL DEFAULT '', "
				"setup_done TINYINT UNSIGNED NOT NULL DEFAULT 0, created_at DATETIME NULL, "
				"retired TINYINT UNSIGNED NOT NULL DEFAULT 0, retired_at DATETIME NULL, "
				"KEY owner_live (owner_pid, retired), KEY seq (seq)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> b(NajemnicyQuery(
				"CREATE TABLE IF NOT EXISTS player.najemnicy_vault ("
				"owner_pid INT UNSIGNED NOT NULL PRIMARY KEY, balance BIGINT NOT NULL DEFAULT 0, "
				"total_paid BIGINT NOT NULL DEFAULT 0, total_deposit BIGINT NOT NULL DEFAULT 0, "
				"updated_at DATETIME NULL) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> c(NajemnicyQuery(
				"CREATE TABLE IF NOT EXISTS player.najemnicy_unlock ("
				"owner_pid INT UNSIGNED NOT NULL PRIMARY KEY, unlocked TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"tasks TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"unlocked_at DATETIME NULL, source VARCHAR(32) NOT NULL DEFAULT '') ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> d(NajemnicyQuery(
				"ALTER TABLE player.najemnicy_unlock ADD COLUMN IF NOT EXISTS tasks TINYINT UNSIGNED NOT NULL DEFAULT 0 "
				"AFTER unlocked"));
		// MT2009_PLUS_NAJEMNICY_V3: the rejoin (summoned, the vault's paid-till second) and the orders.
		std::unique_ptr<SQLMsg> e(NajemnicyQuery(
				"ALTER TABLE player.najemnicy ADD COLUMN IF NOT EXISTS summoned TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER "
				"setup_done, ADD COLUMN IF NOT EXISTS order_mode TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER summoned, "
				"ADD COLUMN IF NOT EXISTS no_loot TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER order_mode"));
		std::unique_ptr<SQLMsg> f(NajemnicyQuery(
				"ALTER TABLE player.najemnicy_vault ADD COLUMN IF NOT EXISTS billed_until INT UNSIGNED NOT NULL DEFAULT 0 "
				"AFTER total_deposit"));
		s_bNajemnicyTables = NajemnicyOk(a) && NajemnicyOk(b) && NajemnicyOk(c) && NajemnicyOk(d) && NajemnicyOk(e) &&
				NajemnicyOk(f);
		if (!s_bNajemnicyTables)
			sys_err("NAJEMNICY: the tables cannot be made (najemnicy.sql)");
		return s_bNajemnicyTables;
	}

	struct TNajemnikRow
	{
		DWORD pid = 0;
		DWORD accountId = 0;
		BYTE slot = 0;
		BYTE race = 0;
		BYTE group = 1;
		bool setupDone = false;
		std::string login;
		std::string name;
		// MT2009_PLUS_NAJEMNICY_V3: summoned when the owner left (it comes back), its last order, the loot switch.
		bool summoned = false;
		BYTE order = NAJEMNIK_ORDER_FOLLOW;
		bool noLoot = false;
	};

	// The owner's mercenaries in service, by slot.
	std::vector<TNajemnikRow> LoadNajemnicyOf(DWORD ownerPid)
	{
		std::vector<TNajemnikRow> out;
		if (!EnsureNajemnicyTables())
			return out;
		std::unique_ptr<SQLMsg> m(NajemnicyQuery(
				"SELECT merc_pid, account_id, slot, job, skill_group, setup_done, login, name, summoned, order_mode, no_loot "
				"FROM player.najemnicy WHERE owner_pid=%u AND retired=0 ORDER BY slot", ownerPid));
		if (!NajemnicyOk(m) || !m->Get()->pSQLResult)
			return out;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(m->Get()->pSQLResult)))
		{
			TNajemnikRow r;
			unsigned int v = 0;
			str_to_number(r.pid, row[0] ? row[0] : "0");
			str_to_number(r.accountId, row[1] ? row[1] : "0");
			v = 0; str_to_number(v, row[2] ? row[2] : "0"); r.slot = (BYTE)v;
			v = 0; str_to_number(v, row[3] ? row[3] : "0"); r.race = (BYTE)MIN(7U, v);
			v = 0; str_to_number(v, row[4] ? row[4] : "1"); r.group = (BYTE)(v == 2 ? 2 : 1);
			v = 0; str_to_number(v, row[5] ? row[5] : "0"); r.setupDone = v != 0;
			r.login = row[6] ? row[6] : "";
			r.name = row[7] ? row[7] : "";
			v = 0; str_to_number(v, row[8] ? row[8] : "0"); r.summoned = v != 0;
			v = 0; str_to_number(v, row[9] ? row[9] : "0"); r.order = (BYTE)(v < NAJEMNIK_ORDER_COUNT ? v : 0);
			v = 0; str_to_number(v, row[10] ? row[10] : "0"); r.noLoot = v != 0;
			if (r.pid)
				out.push_back(r);
		}
		return out;
	}

	long long GetNajemnicyBalance(DWORD ownerPid)
	{
		if (!EnsureNajemnicyTables())
			return 0;
		std::unique_ptr<SQLMsg> m(NajemnicyQuery("SELECT balance FROM player.najemnicy_vault WHERE owner_pid=%u", ownerPid));
		return NajemnicyNumber(m, 0);
	}

	// The collector's tasks done (0..6): the quest flag najemnicy.tasks - which the Kolekcjoner Najemnikow will raise -
	// or the row of player.najemnicy_unlock the GM's command and the panel write, whichever is higher (a higher row is
	// copied onto the flag); the test flag m2_najemnicy_free_unlock counts as all six.
	int GetNajemnicyTasks(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		if (IsNajemnicyFreeUnlock())
			return NAJEMNICY_MAX_TASKS;
		int tasks = MINMAX(0, ch->GetQuestFlag("najemnicy.tasks"), NAJEMNICY_MAX_TASKS);
		if (EnsureNajemnicyTables())
		{
			const int row = (int)MINMAX(0LL, NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"SELECT tasks FROM player.najemnicy_unlock WHERE owner_pid=%u", ch->GetPlayerID())), 0),
					(long long)NAJEMNICY_MAX_TASKS);
			if (row > tasks)
			{
				tasks = row;
				ch->SetQuestFlag("najemnicy.tasks", tasks);
			}
		}
		return tasks;
	}

	int GetNajemnicySlotsOf(LPCHARACTER ch)
	{
		return ch ? GetNajemnicySlots(GetNajemnicyTasks(ch), ch->GetLevel()) : 0;
	}

	bool IsNajemnicyUnlocked(LPCHARACTER ch)
	{
		return GetNajemnicySlotsOf(ch) > 0;
	}

	int CountNajemnicySummonedOf(DWORD ownerPid)
	{
		int n = 0;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			if (it->second.ownerPid == ownerPid && !it->second.dismiss)
				++n;
		return n;
	}

	// The quest's flags: unlocked, slots, how many it has, which are summoned (a bit a slot) and the fee.
	void SyncNajemnicyQuestFlags(LPCHARACTER ch)
	{
		if (!ch)
			return;
		const int tasks = GetNajemnicyTasks(ch);
		const int slots = GetNajemnicySlots(tasks, ch->GetLevel());
		// For the letter only: najemnicy.tasks itself is the collector's count and never takes the test flag's six.
		ch->SetQuestFlag("najemnicy.tasks_view", tasks);
		ch->SetQuestFlag("najemnicy.unlocked", slots > 0 ? 1 : 0);
		ch->SetQuestFlag("najemnicy.slots", slots);
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		ch->SetQuestFlag("najemnicy.count", (int)rows.size());
		int mask = 0;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			if (it->second.ownerPid == ch->GetPlayerID() && !it->second.dismiss && it->second.slot >= 1 && it->second.slot <= 7)
				mask |= 1 << it->second.slot;
		ch->SetQuestFlag("najemnicy.summoned", mask);
		ch->SetQuestFlag("najemnicy.price_h", (int)MIN(2000000000LL, GetNajemnicyPriceH()));
		ch->SetQuestFlag("najemnicy.off", IsNajemnicyOff() ? 1 : 0);
	}

	// ------------------------------------------------------------------ the identity

	// A new mercenary's identity, game-side: the account, the character, its index row and its ledger row - the
	// Towarzysz's MakePlayerBotSidekickIdentity, with an account of its own kind (playerbot_njNNNN) outside the
	// population's ledger, the name the player chose and the auto-increment pid a person's character gets. 0 on any
	// failure, with nothing of it left behind.
	DWORD MakeNajemnikIdentity(LPCHARACTER owner, BYTE race, BYTE group, BYTE slot, const char* name)
	{
		const BYTE empire = owner->GetEmpire();
		if (empire < 1 || empire > 3 || race > 7)
			return 0;
		TPlayerTable fresh;
		if (!NewPlayerTable2(&fresh, name, race, 0, empire))
		{
			sys_err("NAJEMNICY: NewPlayerTable2 refused race=%u empire=%u", (unsigned int)race, (unsigned int)empire);
			return 0;
		}
		// The next free number: past the highest, or the first gap once the highest is the last.
		unsigned int seq = (unsigned int)NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
				"SELECT IFNULL(MAX(seq),0)+1 FROM player.najemnicy")), 1);
		if (seq > NAJEMNICY_MAX_SEQ)
			seq = (unsigned int)NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"SELECT IFNULL(MIN(t.seq+1),1) FROM player.najemnicy t LEFT JOIN player.najemnicy u ON u.seq=t.seq+1 "
					"WHERE u.seq IS NULL AND t.seq < %u", NAJEMNICY_MAX_SEQ)), NAJEMNICY_MAX_SEQ + 1);
		char login[32] = "";
		for (int tries = 0; tries < 50; ++tries, ++seq)
		{
			if (seq < 1 || seq > NAJEMNICY_MAX_SEQ)
			{
				sys_err("NAJEMNICY: no free login number (playerbot_nj0001-%04u)", NAJEMNICY_MAX_SEQ);
				return 0;
			}
			snprintf(login, sizeof(login), "playerbot_nj%04u", seq);
			std::unique_ptr<SQLMsg> taken(NajemnicyQuery(
					"SELECT (SELECT COUNT(*) FROM account.account WHERE login='%s') + "
					"(SELECT COUNT(*) FROM player.najemnicy WHERE seq=%u)", login, seq));
			if (NajemnicyNumber(taken, 1) == 0)
				break;
			login[0] = 0;
		}
		if (!login[0])
			return 0;
		char social[16];
		snprintf(social, sizeof(social), "8%012u", seq);
		std::unique_ptr<SQLMsg> acc(NajemnicyQuery(
				"INSERT INTO account.account (login, password, social_id, email, create_time, status, availDt, last_play) "
				"VALUES ('%s', '!', '%s', '', UTC_TIMESTAMP(), 'BLOCK', UTC_TIMESTAMP(), UTC_TIMESTAMP())", login, social));
		const DWORD accountId = NajemnicyOk(acc) ? (DWORD)NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
				"SELECT id FROM account.account WHERE login='%s'", login)), 0) : 0;
		DWORD pid = 0;
		if (accountId)
		{
			std::unique_ptr<SQLMsg> ins(NajemnicyQuery(
					"INSERT INTO player.player "
					"(account_id,name,level,st,ht,dx,iq,job,voice,dir,x,y,z,hp,mp,stamina,"
					"part_base,part_main,part_hair,part_acce,gold,playtime,exp,stat_point,skill_group,last_play) VALUES "
					"(%u,'%s',1,%u,%u,%u,%u,%u,%u,%u,%d,%d,%d,%d,%d,%d,%u,%u,0,0,0,0,0,0,%u,NOW())",
					accountId, name,
					(unsigned)fresh.st, (unsigned)fresh.ht, (unsigned)fresh.dx, (unsigned)fresh.iq,
					(unsigned)fresh.job, (unsigned)fresh.voice, (unsigned)fresh.dir,
					(int)fresh.x, (int)fresh.y, (int)fresh.z, (int)fresh.hp, (int)fresh.sp, (int)fresh.stamina,
					(unsigned)fresh.part_base, (unsigned)fresh.part_base, (unsigned int)group));
			if (NajemnicyOk(ins))
				pid = (DWORD)NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
						"SELECT id FROM player.player WHERE account_id=%u AND name='%s'", accountId, name)), 0);
		}
		bool ok = pid != 0;
		if (ok)
			ok = NajemnicyOk(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"INSERT INTO player.player_index (id, pid1, pid2, pid3, pid4, empire) VALUES (%u, %u, 0, 0, 0, %u)",
					accountId, pid, (unsigned int)empire)));
		if (ok)
			ok = NajemnicyOk(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"INSERT INTO player.najemnicy (merc_pid, owner_pid, slot, account_id, login, seq, job, skill_group, sex, "
					"name, setup_done, created_at, retired) VALUES (%u, %u, %u, %u, '%s', %u, %u, %u, %u, '%s', 0, NOW(), 0)",
					pid, owner->GetPlayerID(), (unsigned int)slot, accountId, login, seq, (unsigned int)race,
					(unsigned int)group, (unsigned int)((race == 1 || race == 3 || race == 4 || race == 6) ? 1 : 0), name)));
		if (!ok)
		{
			if (pid)
			{
				NajemnicyQuery("DELETE FROM player.najemnicy WHERE merc_pid=%u", pid);
				NajemnicyQuery("DELETE FROM player.player_index WHERE id=%u AND pid1=%u", accountId, pid);
				NajemnicyQuery("DELETE FROM player.player WHERE id=%u AND account_id=%u", pid, accountId);
			}
			if (accountId)
				NajemnicyQuery("DELETE FROM account.account WHERE id=%u AND login='%s' AND password='!'", accountId, login);
			sys_err("NAJEMNICY: new identity failed owner=%u login=%s account=%u pid=%u", owner->GetPlayerID(), login,
					accountId, pid);
			return 0;
		}
		sys_log(0, "NAJEMNICY: identity made owner=%u owner_name=%s pid=%u account=%u login=%s race=%u group=%u slot=%u "
				"name=%s empire=%u", owner->GetPlayerID(), owner->GetName(), pid, accountId, login, (unsigned int)race,
				(unsigned int)group, (unsigned int)slot, name, (unsigned int)empire);
		return pid;
	}

	// ------------------------------------------------------------------ level, stats, skills

	// The six skills of a path in the order the path's build trains them (its main skill first), then the rest.
	void GetNajemnikPathSkills(BYTE job, BYTE group, DWORD pid, std::vector<DWORD>& out)
	{
		out.clear();
		if (group < 1 || group > 2)
			return;
		const DWORD base = (DWORD)job * 30 + (DWORD)(group - 1) * 15 + 1;
		const TJobSkillBuild build = GetPlayerBotSkillBuild(job, group, pid);
		for (int i = 0; i < build.bSkillCount && i < 6; ++i)
		{
			const DWORD v = build.dwSkills[i];
			if (v >= base && v < base + 6 && std::find(out.begin(), out.end(), v) == out.end())
				out.push_back(v);
		}
		for (DWORD v = base; v < base + 6; ++v)
			if (std::find(out.begin(), out.end(), v) == out.end())
				out.push_back(v);
	}

	// The owner's level, stats for the path, and the half skills. Rebuilt only when something differs.
	void SyncNajemnik(LPCHARACTER ch, TPlayerBotAIState& state, TNajemnik& n, LPCHARACTER owner, DWORD dwNow, const char* why)
	{
		const int level = MINMAX(1, (int)owner->GetLevel(), gPlayerMaxLevel);
		bool changed = false;
		if (ch->GetLevel() != level)
		{
			const int before = ch->GetLevel();
			ch->SetExp(0);
			ch->ResetPoint(level);
			state.dwNextStatCheckTime = 0;
			ManagePlayerBotStats(ch, state, dwNow);
			changed = true;
			sys_log(0, "NAJEMNICY: level pid=%u name=%s owner=%u %d->%d why=%s st=%d ht=%d dx=%d iq=%d", n.pid,
					ch->GetName(), n.ownerPid, before, level, why, (int)ch->GetRealPoint(POINT_ST),
					(int)ch->GetRealPoint(POINT_HT), (int)ch->GetRealPoint(POINT_DX), (int)ch->GetRealPoint(POINT_IQ));
		}
		else if (ch->GetPoint(POINT_STAT) > 0)
		{
			state.dwNextStatCheckTime = 0;
			ManagePlayerBotStats(ch, state, dwNow);
			changed = true;
		}
		// The skills: the owner's six of its path, best first, onto the mercenary's in its build's order.
		if (ch->GetSkillGroup() != n.group)
		{
			ch->ClearSkill();
			ch->SetSkillGroup(n.group);
			changed = true;
		}
		std::vector<DWORD> ownerSkills, mine;
		GetNajemnikPathSkills(owner->GetJob(), owner->GetSkillGroup(), owner->GetPlayerID(), ownerSkills);
		GetNajemnikPathSkills(GetNajemnikJobOfRace(n.race), n.group, n.pid, mine);
		std::vector<int> levels;
		for (size_t i = 0; i < ownerSkills.size(); ++i)
			levels.push_back(owner->GetSkillLevel(ownerSkills[i]));
		std::sort(levels.begin(), levels.end(), std::greater<int>());
		int skillsSet = 0;
		for (size_t i = 0; i < mine.size(); ++i)
		{
			const int want = i < levels.size() ? GetNajemnikHalfSkill(levels[i]) : 0;
			if (ch->GetSkillLevel(mine[i]) != want)
			{
				ch->SetSkillLevel(mine[i], want);
				++skillsSet;
			}
		}
		if (skillsSet > 0)
		{
			if (ch->GetPoint(POINT_SKILL) > 0)
				ch->PointChange(POINT_SKILL, -ch->GetPoint(POINT_SKILL));
			ch->SkillLevelPacket();
			changed = true;
			sys_log(0, "NAJEMNICY: skills pid=%u name=%s owner=%u why=%s set=%d main=%d owner_best=%d", n.pid, ch->GetName(),
					n.ownerPid, why, skillsSet, mine.empty() ? 0 : ch->GetSkillLevel(mine[0]), levels.empty() ? 0 : levels[0]);
		}
		n.syncedOwnerLevel = owner->GetLevel();
		if (changed)
		{
			ch->ComputePoints();
			ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
			ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
			ch->PointsPacket();
			ch->Save();
		}
	}

	// ------------------------------------------------------------------ coming and going

	// Beside the owner on the owner's map - PlacePlayerBotSidekickAt without its off-limits rule (a mercenary goes
	// wherever its owner stands; the guild war's rule is the caller's).
	bool PlaceNajemnikBesideOwner(LPCHARACTER ch, TPlayerBotAIState& state, LPCHARACTER owner, DWORD dwNow, const char* why)
	{
		long x = 0, y = 0;
		GetPlayerBotSidekickSpot(ch, owner, x, y);
		const long targetMap = owner->GetMapIndex();
		const long oldMap = ch->GetMapIndex();
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		if (ch->IsRiding())
			ch->StopRiding();
		ch->HorseSummon(false);
		ClearPlayerBotRoute(state, true);
		LPDUNGEON before = ch->GetDungeon();
		if (!ch->Show(targetMap, x, y, 0))
		{
			PlayerBotLogThrottled("najemnicy_place", dwNow, "NAJEMNICY: cannot stand beside the owner pid=%u name=%s from=%ld "
					"to=%ld why=%s", ch->GetPlayerID(), ch->GetName(), oldMap, targetMap, why);
			return false;
		}
		ch->Stop();
		ch->SendMovePacket(FUNC_MOVE, 0, x, y, 0, dwNow);
		LPDUNGEON after = targetMap >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? CDungeonManager::instance().FindByMapIndex(targetMap) : NULL;
		if (before != after)
		{
			if (before)
				ch->SetDungeon(NULL);
			if (after)
				ch->SetDungeon(after);
		}
		CPlayerBotNavigation::instance(targetMap).Init(targetMap);
		if (oldMap != targetMap)
		{
			SyncPlayerBotZodiac(ch, targetMap);
			ch->Save();
			sys_log(0, "NAJEMNICY: beside the owner pid=%u name=%s owner=%u from=%ld to=%ld why=%s", ch->GetPlayerID(),
					ch->GetName(), owner->GetPlayerID(), oldMap, targetMap, why);
		}
		state.lLastX = x;
		state.lLastY = y;
		state.dwLastMeaningfulActivityTime = dwNow;
		return true;
	}

	// In the owner's party (made for the owner when there is none), as long as a place is free.
	void KeepNajemnikInParty(LPCHARACTER ch, LPCHARACTER owner, DWORD dwNow)
	{
		LPPARTY party = owner->GetParty();
		if (party && ch->GetParty() == party)
			return;
		// MT2009_PLUS_NAJEMNICY_V4: inside a dungeon too. The engine's PERR_DUNGEON is the invitation's rule
		// (CHARACTER::IsPartyJoinableMutableCondition - no stranger brought into a running instance); CParty::Join and
		// Link check nothing of it. Only a mercenary joins here, only its owner's party, only in the owner's instance -
		// the owner's relog inside a dungeon left them out (their party went with the logout) and the instance's
		// bookkeeping is kept below (CDungeon::IncPartyMember, as CHARACTER::SetDungeon counts a member that came in
		// with its party), so the instance's party count stays even when they leave it.
		LPDUNGEON dungeon = owner->GetDungeon();
		if (dungeon && ch->GetMapIndex() != owner->GetMapIndex())
			return;
		if (party && party->GetMemberCount() >= PARTY_MAX_MEMBER)
		{
			PlayerBotLogThrottled("najemnicy_party_full", dwNow, "NAJEMNICY: the owner's party is full pid=%u name=%s owner=%u",
					ch->GetPlayerID(), ch->GetName(), owner->GetPlayerID());
			return;
		}
		if (ch->GetParty())
			LeavePlayerBotParty(ch);
		if (!party)
		{
			party = CPartyManager::instance().CreateParty(owner);
			if (!party)
				return;
			if (dungeon)
				dungeon->IncPartyMember(party, owner);	// the owner was counted alone at its entry (IncMember)
			sys_log(0, "NAJEMNICY: made a party for owner=%u name=%s dungeon=%ld", owner->GetPlayerID(), owner->GetName(),
					dungeon ? owner->GetMapIndex() : 0L);
		}
		party->Join(ch->GetPlayerID());
		party->Link(ch);
		if (dungeon && ch->GetParty() == party && ch->GetDungeon() == dungeon)
			dungeon->IncPartyMember(party, ch);	// it was counted alone at its entry (IncMember - the set keeps it once)
		sys_log(0, "NAJEMNICY: joined the owner's party pid=%u name=%s owner=%u members=%d dungeon=%ld", ch->GetPlayerID(),
				ch->GetName(), owner->GetPlayerID(), (int)party->GetMemberCount(), dungeon ? owner->GetMapIndex() : 0L);
	}

	// A character the mercenary may strike: any monster or stone; a character only in a guild war of its own guild.
	bool MayNajemnikStrike(LPCHARACTER ch, LPCHARACTER target)
	{
		if (!target || !target->IsPC())
			return true;
		CGuild* mine = ch->GetGuild();
		CGuild* theirs = target->GetGuild();
		return mine && theirs && mine != theirs && mine->UnderWar(theirs->GetID());
	}

	// Its own drops: a thing on the ground whose ownership is the mercenary's and not the owner's (the party's share
	// of a kill, CParty::GetNextOwnership) - the owner picks up the rest.
	// MT2009_PLUS_NAJEMNICY_V2 (the owner: "caly drop i wszystkie nagrody trafiaja do ekwipunku najemnika"): also the
	// people's boss loot a dungeon quest leaves on the ground (game.drop_item_at with people 1, Mt2009PlusIsPeopleLoot) -
	// a mercenary is one of the people there (pc.is_najemnik in the quests' loot_people), and the engine's pickup lets
	// it take its own share (CHARACTER::PickupItem, NajemnikMayTakePeopleLoot, server-patches/najemnicy).
	struct FNajemnikLoot
	{
		LPCHARACTER self;
		LPCHARACTER owner;
		LPITEM best;
		int bestDist;

		FNajemnikLoot(LPCHARACTER s, LPCHARACTER o) : self(s), owner(o), best(NULL), bestDist(NAJEMNICY_LOOT_RANGE)
		{
		}

		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_ITEM))
				return;
			LPITEM item = (LPITEM)ent;
			if (!item->GetSectree() || item->GetOwner())
				return;
			if (!item->IsOwnership(self) || item->IsOwnership(owner))
				return;
			const int d = DISTANCE_APPROX(item->GetX() - self->GetX(), item->GetY() - self->GetY());
			if (d < bestDist)
			{
				best = item;
				bestDist = d;
			}
		}
	};

	bool RunNajemnikLoot(LPCHARACTER ch, TPlayerBotAIState& state, TNajemnik& n, LPCHARACTER owner, DWORD dwNow)
	{
		if (n.lootVid == 0 && (int)(dwNow - n.nextLoot) < 0)
			return false;
		n.nextLoot = dwNow + NAJEMNICY_LOOT_MS;
		if (!ch->GetSectree())
			return false;
		FNajemnikLoot loot(ch, owner);
		ch->GetSectree()->ForEachAround(loot);
		if (!loot.best)
		{
			n.lootVid = 0;
			return false;
		}
		// MT2009_PLUS_NAJEMNICY_V2: no room for its share - the owner hears it (now and then) and empties its bag.
		if (ch->GetEmptyInventory(loot.best->GetSize()) < 0)
		{
			n.lootVid = 0;
			if ((int)(dwNow - n.nextBagFullTell) >= 0)
			{
				n.nextBagFullTell = dwNow + NAJEMNICY_BAG_FULL_TELL_MS;
				TellNajemnicy(owner, "%s ma pelny plecak i nie podniesie swojego lupu - zabierz od niego rzeczy (okno "
						"ekwipunku najemnika).", ch->GetName());
				sys_log(0, "NAJEMNICY: bag full pid=%u name=%s owner=%u vnum=%u", n.pid, ch->GetName(), n.ownerPid,
						loot.best->GetVnum());
			}
			return false;
		}
		const DWORD vid = loot.best->GetVID();
		if (vid != n.lootVid)
		{
			n.lootVid = vid;
			n.lootSince = dwNow;
		}
		else if (dwNow - n.lootSince > NAJEMNICY_LOOT_GIVE_UP_MS)
		{
			n.lootVid = 0;
			n.nextLoot = dwNow + NAJEMNICY_LOOT_GIVE_UP_MS;
			return false;
		}
		if (loot.bestDist > 250)
		{
			WalkPlayerBotSidekick(ch, loot.best->GetX(), loot.best->GetY(), dwNow, false);
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			state.dwLastMeaningfulActivityTime = dwNow;
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		const DWORD vnum = loot.best->GetVnum();
		if (ch->PickupItem(vid))
			PlayerBotLogThrottled("najemnicy_loot", dwNow, "NAJEMNICY: picked up pid=%u name=%s vid=%u vnum=%u", ch->GetPlayerID(),
					ch->GetName(), vid, vnum);
		n.lootVid = 0;
		return true;
	}

	// ------------------------------------------------------------------ MT2009_PLUS_NAJEMNICY_V2: what it uses

	// Any potion of the owner's that heals (HP) or restores mana (SP): ITEM_USE, USE_POTION or USE_POTION_NODELAY with
	// the amount in value0 (HP) or value1 (SP) - whatever the owner gave it, past the bots' own vnum lists.
	bool IsNajemnikPotion(LPITEM item, bool hp)
	{
		if (!item || item->GetType() != ITEM_USE || item->isLocked() || item->IsExchanging())
			return false;
		if (item->GetSubType() != USE_POTION && item->GetSubType() != USE_POTION_NODELAY)
			return false;
		return hp ? item->GetValue(0) > 0 : item->GetValue(1) > 0;
	}

	bool UseNajemnikAnyPotion(LPCHARACTER ch, bool hp)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsNajemnikPotion(item, hp))
				continue;
			const DWORD vnum = item->GetVnum();
			if (ch->UseItem(TItemPos(INVENTORY, cell)))
			{
				PlayerBotLogPerBot(hp ? "najemnik_hp" : "najemnik_sp", ch->GetPlayerID(), get_dword_time(),
						"NAJEMNICY: potion pid=%u name=%s vnum=%u hp=%d/%d sp=%d/%d", ch->GetPlayerID(), ch->GetName(), vnum,
						(int)ch->GetHP(), (int)ch->GetMaxHP(), (int)ch->GetSP(), (int)ch->GetMaxSP());
				return true;
			}
		}
		return false;
	}

	// A buff of the owner's from its bag in a fight: the dews and the Energy Crystal (ITEM_BLEND), the attack, defence,
	// speed and critical potions, the juices - whatever the bots' own reading of a buff item knows
	// (GetPlayerBotBuffItemAffect), not while the same buff runs as strong (IsPlayerBotBuffItemCovered). Never a book's
	// affect (the Hermit's Advice, the Exorcism Scroll). One a call; an item the engine refused waits half a minute.
	bool UseNajemnikBuffItem(LPCHARACTER ch, TNajemnik& n, DWORD dwNow)
	{
		if ((int)(dwNow - n.nextBuffItem) < 0)
			return false;
		n.nextBuffItem = dwNow + NAJEMNICY_BUFF_ITEM_MS;
		std::set<DWORD> tried;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->isLocked() || item->IsExchanging())
				continue;
			if (item->GetType() != ITEM_BLEND && !(item->GetType() == ITEM_USE &&
					(item->GetSubType() == USE_AFFECT || item->GetSubType() == USE_ABILITY_UP)))
				continue;
			if (IsPlayerBotBookAffectItem(item))
				continue;
			DWORD type = 0;
			WORD point = 0;
			long value = 0;
			if (!GetPlayerBotBuffItemAffect(item, type, point, value) || IsPlayerBotBuffItemCovered(ch, item))
				continue;
			const DWORD vnum = item->GetVnum();
			if (!tried.insert(vnum).second)
				continue;
			std::map<DWORD, DWORD>::iterator retry = n.mapItemRetry.find(vnum);
			if (retry != n.mapItemRetry.end() && (int)(dwNow - retry->second) < 0)
				continue;
			n.mapItemRetry[vnum] = dwNow + NAJEMNICY_BUFF_RETRY_MS;
			if (ch->UseItem(TItemPos(INVENTORY, cell)))
			{
				PlayerBotLogPerBot("najemnik_buff", ch->GetPlayerID(), dwNow, "NAJEMNICY: buff item pid=%u name=%s vnum=%u "
						"type=%u point=%u", ch->GetPlayerID(), ch->GetName(), vnum, (unsigned int)type, (unsigned int)point);
				return true;
			}
		}
		return false;
	}

	// Its consumables, all its owner's (it never buys): HP and SP potions at the bots' thresholds (the bots' own vnum
	// lists first - the reds, the blues, the healing fish and wine - then any potion of the owner's), the auto potions,
	// and in a fight the green and purple potions and the buff items (UseNajemnikBuffItem), as a bot in a party.
	void UseNajemnikConsumables(LPCHARACTER ch, TPlayerBotAIState& state, TNajemnik& n, bool fighting, DWORD dwNow)
	{
		if ((int)(dwNow - n.nextConsumable) < 0 || ch->IsDead() || !ch->IsItemLoaded())
			return;
		n.nextConsumable = dwNow + NAJEMNICY_CONSUMABLE_MS;
		const bool war = ch->GetWarMap() != NULL;
		const bool lowHp = ch->GetMaxHP() > 0 && ((long long)ch->GetHP() + ch->GetPoint(POINT_HP_RECOVERY)) * 100 <=
				(long long)ch->GetMaxHP() * PLAYERBOT_POTION_HP_PERCENT;
		const bool lowSp = ch->GetMaxSP() > 0 && ((long long)ch->GetSP() + ch->GetPoint(POINT_SP_RECOVERY)) * 100 <=
				(long long)ch->GetMaxSP() * PLAYERBOT_POTION_SP_PERCENT;
		if (lowHp && !UseHealthPotion(ch, state, dwNow) && !war)
			UseNajemnikAnyPotion(ch, true);
		if (lowSp && !UseManaPotion(ch, state, dwNow))
			UseNajemnikAnyPotion(ch, false);
		ManagePlayerBotAutoPotions(ch, dwNow);
		if (!fighting)
			return;
		UseUtilityPotions(ch, state, dwNow);
		UseNajemnikBuffItem(ch, n, dwNow);
	}

	// A piece the owner put on while a blow was landing: worn at the engine's first chance. True while it still waits
	// (the tick holds the fight off meanwhile, as the Towarzysz's equipment pass did).
	bool RetryNajemnikPendingWear(LPCHARACTER ch, TPlayerBotAIState& state, TNajemnik& n, DWORD dwNow)
	{
		if (!n.pendingWearItem)
			return false;
		LPITEM item = ITEM_MANAGER::instance().Find(n.pendingWearItem);
		if (!item || item->GetOwner() != ch || item->IsEquipped() || item->GetWindow() != INVENTORY ||
				(int)(dwNow - n.pendingWearUntil) >= 0)
		{
			if (item && item->GetOwner() == ch && !item->IsEquipped() && (int)(dwNow - n.pendingWearUntil) >= 0)
				sys_log(0, "NAJEMNICY: pending wear given up pid=%u name=%s vnum=%u", n.pid, ch->GetName(), item->GetVnum());
			n.pendingWearItem = 0;
			n.pendingWearSlot = -1;
			return false;
		}
		if (IsPlayerBotEquipWindowShut(ch, state) || item->isLocked() || item->IsExchanging())
		{
			if (ch->GetVictim())
				ch->SetVictim(NULL);
			state.dwTargetVID = 0;
			return true;
		}
		const int slot = n.pendingWearSlot;
		LPITEM old = slot >= 0 && slot < WEAR_MAX_NUM ? ch->GetWear(slot) : NULL;
		if ((slot == WEAR_UNIQUE1 || slot == WEAR_UNIQUE2) && old && old->IsEquipped() &&
				ch->GetEmptyInventory(old->GetSize()) >= 0)
			ch->UnequipItem(old);
		bool worn = PlayerBotEquipItem(ch, item) && item->IsEquipped();
		if (!worn && old && old->IsEquipped() && ch->GetEmptyInventory(old->GetSize()) >= 0 && ch->UnequipItem(old) &&
				!old->IsEquipped())
			worn = PlayerBotEquipItem(ch, item) && item->IsEquipped();
		sys_log(0, "NAJEMNICY: pending wear pid=%u name=%s vnum=%u slot=%d worn=%d", n.pid, ch->GetName(), item->GetVnum(),
				slot, worn ? 1 : 0);
		if (worn)
		{
			FlushPlayerBotItemRow(item);
			FlushPlayerBotItemRow(old);
			ch->ComputePoints();
			ch->PointsPacket();
		}
		n.pendingWearItem = 0;
		n.pendingWearSlot = -1;
		return false;
	}

	// The extra inventory's storages are never a mercenary's (PlayerBotEkwRouteWindow sends nothing there); what is
	// there from before comes into its bag, where the owner's window sees it.
	void SweepNajemnikStorage(LPCHARACTER ch, TNajemnik& n, DWORD dwNow)
	{
		if ((int)(dwNow - n.nextBagSweep) < 0)
			return;
		n.nextBagSweep = dwNow + NAJEMNICY_BAG_SWEEP_MS;
		std::vector<LPITEM> stored;
		CollectPlayerBotEkwStored(ch, stored);
		int moved = 0;
		for (size_t i = 0; i < stored.size() && moved < 10; ++i)
		{
			LPITEM item = stored[i];
			if (!item || item->isLocked() || item->IsExchanging())
				continue;
			const int cell = ch->GetEmptyInventory(item->GetSize());
			if (cell < 0)
				break;
			item->RemoveFromCharacter();
			item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			ITEM_MANAGER::instance().FlushDelayedSave(item);
			++moved;
		}
		if (moved > 0)
			sys_log(0, "NAJEMNICY: storage swept pid=%u name=%s moved=%d", n.pid, ch->GetName(), moved);
	}

	// The whole tick of a summoned mercenary; true for every mercenary (nothing of the population's runs for it).
	// MT2009_PLUS_NAJEMNICY_V3: "Walcz sam w poblizu" - the nearest monster or stone within NAJEMNICY_FREE_RANGE of the
	// owner, bosses and stones included (the Towarzysz's hunt leaves those to the owner).
	struct FNajemnikFreeFoe
	{
		LPCHARACTER self;
		LPCHARACTER owner;
		LPCHARACTER best;
		int bestDist;

		FNajemnikFreeFoe(LPCHARACTER s, LPCHARACTER o) : self(s), owner(o), best(NULL), bestDist(INT_MAX)
		{
		}

		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER c = (LPCHARACTER)ent;
			if (c == self || c == owner || c->IsDead() || (!c->IsMonster() && !c->IsStone()) ||
					c->GetMapIndex() != owner->GetMapIndex())
				return;
			if (c->IsStone() && IsPlayerBotEventStone(c->GetRaceNum()))
				return;
			if (DISTANCE_APPROX(c->GetX() - owner->GetX(), c->GetY() - owner->GetY()) > NAJEMNICY_FREE_RANGE)
				return;
			const int d = DISTANCE_APPROX(c->GetX() - self->GetX(), c->GetY() - self->GetY());
			if (d < bestDist && IsPlayerBotAttackableTarget(self, c))
			{
				best = c;
				bestDist = d;
			}
		}
	};

	// The owner's target as "Bij moj cel" takes it: any monster or stone (a boss too, merely clicked or not), a guild
	// war's foe, on the owner's map within the Towarzysz's assist range.
	LPCHARACTER GetNajemnikOwnerTarget(LPCHARACTER ch, LPCHARACTER owner)
	{
		LPCHARACTER target = owner->GetTarget();
		if (!target || target == ch || target->IsDead() || target->GetMapIndex() != owner->GetMapIndex())
			return NULL;
		if (!target->IsMonster() && !target->IsStone() && !IsPlayerBotSidekickWarFoe(owner, target))
			return NULL;
		if (target->IsStone() && IsPlayerBotEventStone(target->GetRaceNum()))
			return NULL;
		if (DISTANCE_APPROX(target->GetX() - owner->GetX(), target->GetY() - owner->GetY()) > PLAYERBOT_SIDEKICK_ASSIST_RANGE)
			return NULL;
		return IsPlayerBotAttackableTarget(ch, target) ? target : NULL;
	}

	// What the mercenary fights now, by its order.
	LPCHARACTER ChooseNajemnikFoe(LPCHARACTER ch, LPCHARACTER owner, TNajemnik& n, int& why)
	{
		bool ownerFighting = false;
		switch (n.order)
		{
			case NAJEMNIK_ORDER_FOCUS:
			{
				LPCHARACTER target = GetNajemnikOwnerTarget(ch, owner);
				if (target)
				{
					why = PLAYERBOT_SIDEKICK_FOE_OWNER_TARGET;
					return target;
				}
				// No target of the owner's: only what hits the owner or itself.
				return FindPlayerBotSidekickFoe(ch, owner, PLAYERBOT_SIDEKICK_STANCE_DEFEND, why, ownerFighting);
			}
			case NAJEMNIK_ORDER_FREE:
			{
				LPCHARACTER foe = FindPlayerBotSidekickFoe(ch, owner, PLAYERBOT_SIDEKICK_STANCE_ATTACK, why, ownerFighting);
				if (foe || !owner->GetSectree())
					return foe;
				FNajemnikFreeFoe free(ch, owner);
				owner->GetSectree()->ForEachAround(free);
				why = PLAYERBOT_SIDEKICK_FOE_NEARBY;
				return free.best;
			}
			case NAJEMNIK_ORDER_HOLD:
			{
				if (!ch->GetSectree())
					return NULL;
				// The Towarzysz's look round, centred on its spot: what hits it or the owner there, what idles by the spot.
				FPlayerBotSidekickFoes foes(ch, owner, n.holdX, n.holdY, ch->GetMapIndex());
				ch->GetSectree()->ForEachAround(foes);
				if (foes.onSelf)
				{
					why = PLAYERBOT_SIDEKICK_FOE_AT_SELF;
					return foes.onSelf;
				}
				if (foes.onOwner)
				{
					why = PLAYERBOT_SIDEKICK_FOE_AT_OWNER;
					return foes.onOwner;
				}
				if (foes.idle && DISTANCE_APPROX(foes.idle->GetX() - n.holdX, foes.idle->GetY() - n.holdY) <=
						NAJEMNICY_HOLD_FIGHT_RANGE)
				{
					why = PLAYERBOT_SIDEKICK_FOE_NEARBY;
					return foes.idle;
				}
				LPCHARACTER target = GetNajemnikOwnerTarget(ch, owner);
				if (target && DISTANCE_APPROX(target->GetX() - n.holdX, target->GetY() - n.holdY) <= NAJEMNICY_HOLD_FIGHT_RANGE)
				{
					why = PLAYERBOT_SIDEKICK_FOE_OWNER_TARGET;
					return target;
				}
				return NULL;
			}
			default:
				return FindPlayerBotSidekickFoe(ch, owner, PLAYERBOT_SIDEKICK_STANCE_ATTACK, why, ownerFighting);
		}
	}

	// ------------------------------------------------------------------ MT2009_PLUS_NAJEMNICY_V3: the dungeons

	// A dungeon's instance the bots of a person's party know (IsPlayerBotPartyDungeonMap: the classic and Arezzo
	// dungeons, Atlantis, Zodiac, the ship, Meley, the Yohara ones).
	bool IsNajemnikDungeonMap(long map)
	{
		return map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN && IsPlayerBotPartyDungeonMap(map);
	}

	// MT2009_PLUS_NAJEMNICY_V4: the bots' run definition of a dungeon's instance (PLAYERBOT_DGRUN_DEFS by its map) whose
	// leader's objectives and scripts fit a party its owner leads - not the Arezzo ones (the cohort's plan, which the
	// party pass already plays: seals, the boss's break-off), the Demon Tower, the ship, the Gnolle caves or the Sung Mahi
	// tower. Glebie by the instance's kind (the weak or the strong Alastor). -1: none.
	int FindNajemnikDgRunDef(long map, LPDUNGEON d)
	{
		if (map < PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return -1;
		const long base = map / 10000;
		const char* glebie = base == PLAYERBOT_GLEBIE_MAP ? (GetPlayerBotGlebieDKind(d) == 2 ? "glebie_silny" : "glebie_slaby") : NULL;
		for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
		{
			const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[i];
			if (def.lMap != base || (glebie && (!def.szKey || std::strcmp(def.szKey, glebie) != 0)))
				continue;
			switch (def.bKind)
			{
				case DGRUN_KIND_BIBLIO:
				case DGRUN_KIND_RAZADOR:
				case DGRUN_KIND_NEMERE:
				case DGRUN_KIND_SMOK:
				case DGRUN_KIND_ATLANTYDA:
				case DGRUN_KIND_MELEY:
				case DGRUN_KIND_SZC:
				case DGRUN_KIND_EREBU:
				case DGRUN_KIND_YDG:
					return i;
				default:
					return -1;
			}
		}
		return -1;
	}

	// The Yohara dungeon run definition of an instance whose items (keys, cogs, stones, stars) and scripts the bots' own
	// item pass handles round a member list (ManagePlayerBotYdgItems) - Nemere / Razador / Beran / Jotun, Przebudzeni and
	// Szczeliny, and (MT2009_PLUS_NAJEMNICY_V4) Swiatynia Wezy (its keys, cages, heads - ManagePlayerBotWezeItems) and
	// Glebie (the egg chamber's duty and its portals - ManagePlayerBotGlebieBot, with the record below).
	int FindNajemnikYdgDef(long map, LPDUNGEON d)
	{
		const int i = FindNajemnikDgRunDef(map, d);
		if (i < 0 || PLAYERBOT_DGRUN_DEFS[i].bKind != DGRUN_KIND_YDG || !FindPlayerBotYdgDef(PLAYERBOT_DGRUN_DEFS[i].szKey))
			return -1;
		return i;
	}

	// MT2009_PLUS_NAJEMNICY_V4: an owner's party's own id among the runs' records - negative, so it is never a bots' run
	// (their ids count up from 1) and never in the runs' registry (no planner, monitor, pull, stall or member lookup of
	// theirs ever finds it: FPlayerBotDgRunThreat and IsPlayerBotDgRunMemberOf see no member of it).
	int GetNajemnicyDgRunId(DWORD ownerPid)
	{
		return -1 - (int)(ownerPid & 0x3fffffffU);
	}

	// An owner's party in one instance as the bots' item and duty scripts see a run (never registered in the runs'
	// registry, so no planner, monitor, pull or stall of theirs ever touches it): the owner's mercenaries there, then the
	// owner - the leader (a key of the wrong class goes to a mercenary of the right one, or to the owner; the leader has
	// no egg duty; the zones' dodge steps towards the leader).
	std::map<DWORD, TPlayerBotDgRun> s_mapNajemnicyDgRun;	// owner pid -> its party's view

	TPlayerBotDgRun& GetNajemnicyDgRun(DWORD ownerPid, int iDef, long map)
	{
		TPlayerBotDgRun& run = s_mapNajemnicyDgRun[ownerPid];
		run.iId = GetNajemnicyDgRunId(ownerPid);
		run.iDef = iDef;
		run.bPhase = DGRUN_PHASE_INSIDE;
		run.dwLeader = ownerPid;
		run.dwAnchor = ownerPid;
		run.lInstance = map;
		run.members.clear();
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			if (it->second.ownerPid == ownerPid && !it->second.dismiss)
				run.members.push_back(it->first);
		run.members.push_back(ownerPid);
		return run;
	}

	// A character of the owner's party: the owner, or one of the owner's mercenaries.
	bool IsNajemnikPartyOf(LPCHARACTER c, DWORD ownerPid)
	{
		if (!c || !c->IsPC())
			return false;
		if (c->GetPlayerID() == ownerPid)
			return true;
		std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.find(c->GetPlayerID());
		return it != s_mapNajemnik.end() && it->second.ownerPid == ownerPid;
	}

	// ---- MT2009_PLUS_NAJEMNICY_V4: Glebie (Alastor) - the egg chamber and the ground zones as a bots' run has them

	// The bots' run record (s_mapPlayerBotGlebieRuns) of an owner's party in Glebie, under the party's own id: how many
	// go to the egg chamber (a mercenary of two or more, two of six or more - the leader, the owner, never), its egg
	// duty picked when Alastor wakes (PickPlayerBotGlebieEggBots: Ninja, Sura, Warrior, the strongest first), its
	// portals' and dodges' counts. Made anew for every instance, dropped when the party is in another dungeon.
	std::map<DWORD, long> s_mapNajemnicyGlebie;	// owner pid -> the instance its record is of

	void KeepNajemnicyGlebieRecord(DWORD ownerPid, const TPlayerBotDgRun& run, LPDUNGEON d)
	{
		const bool glebie = d && run.iDef >= 0 && GetPlayerBotGlebieRunKind(run) != 0;
		std::map<DWORD, long>::iterator g = s_mapNajemnicyGlebie.find(ownerPid);
		if (g != s_mapNajemnicyGlebie.end() && (!glebie || g->second != run.lInstance))
		{
			s_mapPlayerBotGlebieRuns.erase(run.iId);
			s_mapNajemnicyGlebie.erase(g);
			g = s_mapNajemnicyGlebie.end();
		}
		if (!glebie)
			return;
		TPlayerBotGlebieRun& gr = s_mapPlayerBotGlebieRuns[run.iId];
		if (g == s_mapNajemnicyGlebie.end())
		{
			gr = TPlayerBotGlebieRun();
			s_mapNajemnicyGlebie[ownerPid] = run.lInstance;
		}
		gr.iKind = GetPlayerBotGlebieDKind(d);
		if (!gr.bEggPicked)
		{
			int mercs = 0;
			for (size_t i = 0; i < run.members.size(); ++i)
			{
				LPCHARACTER c = run.members[i] != ownerPid ? CHARACTER_MANAGER::instance().FindByPID(run.members[i]) : NULL;
				mercs += c && c->GetMapIndex() == run.lInstance ? 1 : 0;
			}
			const int wanted = mercs >= 6 ? 2 : (mercs >= 2 ? 1 : 0);
			if (wanted != gr.iEggWanted)
				sys_log(0, "NAJEMNICY: glebie owner=%u instance=%ld kind=%d mercs=%d egg_duty=%d", ownerPid, run.lInstance, gr.iKind,
						mercs, wanted);
			gr.iEggWanted = wanted;
		}
	}

	// ---- MT2009_PLUS_NAJEMNICY_V4: Schronienie Meley - the roles of the bots' Meley run (MT2009_PLUS_BOT_MELEY16_V1)

	const int NAJEMNICY_MELEY_ROLE_STATUE = 0;	// with the owner: the eggs, Idall, then the most hurt statue (the objective)
	const int NAJEMNICY_MELEY_ROLE_HEAL = 1;	// a healing Shaman: the party's buffs and heals first
	const int NAJEMNICY_MELEY_ROLE_EGG = 2;		// an egg of its own while eggs stand (the statues' shield)
	const int NAJEMNICY_MELEY_ROLE_MAGMA = 3;	// the magma guard: what strikes the party (the healers first in stages 2-3)
	const DWORD NAJEMNICY_MELEY_ROLE_MS = 60 * 1000;

	struct TNajemnicyMeley
	{
		long instance = 0;
		DWORD nextAssign = 0;
		std::string sig;
		std::map<DWORD, std::pair<int, int> > roles;	// mercenary pid -> role, its index among the role's members
	};
	std::map<DWORD, TNajemnicyMeley> s_mapNajemnicyMeley;	// owner pid -> its party's roles in the lair

	// The bots' run's roles (AssignPlayerBotMeleyRoles) for the owner's mercenaries in the lair, again whenever who is
	// inside changed and every minute: the healing Shamans heal; of two or more the strongest quarter (one at the least)
	// break the eggs; of four or more a quarter of the bodies (the Warriors, then the Suras, the most health first) is the
	// magma guard; the rest are the statue team with the owner. A bots' run gives roles from nine up - its leader is a
	// bot; here the owner leads and the eggs are the reason a small party never got past the second stage.
	void AssignNajemnicyMeleyRoles(DWORD ownerPid, long instance, TNajemnicyMeley& m, DWORD dwNow)
	{
		std::vector<LPCHARACTER> mercs;
		std::string sig;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
		{
			if (it->second.ownerPid != ownerPid || it->second.dismiss)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c->GetMapIndex() != instance)
				continue;
			mercs.push_back(c);
			sig += std::to_string(it->first) + ",";
		}
		if (m.instance == instance && m.sig == sig && (int)(dwNow - m.nextAssign) < 0)
			return;
		m.instance = instance;
		m.sig = sig;
		m.nextAssign = dwNow + NAJEMNICY_MELEY_ROLE_MS;
		m.roles.clear();
		if (mercs.size() < 2)
			return;
		int count[4] = { 0, 0, 0, 0 };
		std::vector<LPCHARACTER> rest;
		for (size_t i = 0; i < mercs.size(); ++i)
		{
			if (mercs[i]->GetJob() == JOB_SHAMAN && mercs[i]->GetSkillGroup() != 0)
				m.roles[mercs[i]->GetPlayerID()] = std::make_pair(NAJEMNICY_MELEY_ROLE_HEAL, count[NAJEMNICY_MELEY_ROLE_HEAL]++);
			else
				rest.push_back(mercs[i]);
		}
		const int all = (int)mercs.size();
		const int quarter = std::max(1, all / 4);
		const int magmaWanted = all >= 4 ? quarter : 0;
		std::sort(rest.begin(), rest.end(), [](LPCHARACTER a, LPCHARACTER b)
				{
					const int ka = a->GetJob() == JOB_WARRIOR ? 0 : (a->GetJob() == JOB_SURA ? 1 : 2);
					const int kb = b->GetJob() == JOB_WARRIOR ? 0 : (b->GetJob() == JOB_SURA ? 1 : 2);
					return ka != kb ? ka < kb : a->GetMaxHP() > b->GetMaxHP();
				});
		std::vector<LPCHARACTER> left;
		for (size_t i = 0; i < rest.size(); ++i)
			if (count[NAJEMNICY_MELEY_ROLE_MAGMA] < magmaWanted && (int)(rest.size() - i) > quarter)
				m.roles[rest[i]->GetPlayerID()] = std::make_pair(NAJEMNICY_MELEY_ROLE_MAGMA, count[NAJEMNICY_MELEY_ROLE_MAGMA]++);
			else
				left.push_back(rest[i]);
		std::sort(left.begin(), left.end(), [](LPCHARACTER a, LPCHARACTER b) { return ScorePlayerBotYdg(a) > ScorePlayerBotYdg(b); });
		for (size_t i = 0; i < left.size(); ++i)
			if (count[NAJEMNICY_MELEY_ROLE_EGG] < quarter)
				m.roles[left[i]->GetPlayerID()] = std::make_pair(NAJEMNICY_MELEY_ROLE_EGG, count[NAJEMNICY_MELEY_ROLE_EGG]++);
			else
				m.roles[left[i]->GetPlayerID()] = std::make_pair(NAJEMNICY_MELEY_ROLE_STATUE, count[NAJEMNICY_MELEY_ROLE_STATUE]++);
		static const char* const name[4] = { "statue", "heal", "egg", "magma" };
		std::string line;
		for (std::map<DWORD, std::pair<int, int> >::const_iterator r = m.roles.begin(); r != m.roles.end(); ++r)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(r->first);
			if (line.size() < 400)
				line += std::string(line.empty() ? "" : ",") + (c ? c->GetName() : "?") + ":" + name[r->second.first & 3];
		}
		sys_log(0, "NAJEMNICY: meley roles owner=%u instance=%ld mercs=%d statue=%d heal=%d egg=%d magma=%d (%s)", ownerPid, instance,
				all, count[0], count[1], count[2], count[3], line.c_str());
	}

	int GetNajemnikMeleyRole(const TNajemnik& n, long instance, DWORD dwNow)
	{
		TNajemnicyMeley& m = s_mapNajemnicyMeley[n.ownerPid];
		AssignNajemnicyMeleyRoles(n.ownerPid, instance, m, dwNow);
		std::map<DWORD, std::pair<int, int> >::const_iterator r = m.roles.find(n.pid);
		return r == m.roles.end() ? NAJEMNICY_MELEY_ROLE_STATUE : r->second.first;
	}

	// An egg killer's egg (by its index among the killers, the eggs by vid) or the magma guard's monster (one on the
	// owner's party round the owner - in stages 2-3 only one on a healer, else it joins the objective as the bots'
	// guard does, MT2009_PLUS_BOT_MELEY_GUARD_HEALERS_V1). NULL: the role has nothing now, or the mercenary is under a
	// fifth of its health (FightPlayerBotMeleyRole's rule) - then the objective and the party pass.
	LPCHARACTER PickNajemnikMeleyRoleFoe(LPCHARACTER ch, TPlayerBotAIState& state, const TNajemnik& n, LPCHARACTER owner, LPDUNGEON d,
			DWORD dwNow)
	{
		const int stage = d ? d->GetFlag("stage") : 0;
		if (stage < 1 || stage > 4 || state.bRecoveringAfterDeath || ch->GetMaxHP() <= 0 ||
				(long long)ch->GetHP() * 100 < (long long)ch->GetMaxHP() * PLAYERBOT_MELEY_ROLE_FOCUS_HP)
			return NULL;
		TNajemnicyMeley& m = s_mapNajemnicyMeley[n.ownerPid];
		AssignNajemnicyMeleyRoles(n.ownerPid, ch->GetMapIndex(), m, dwNow);
		std::map<DWORD, std::pair<int, int> >::const_iterator r = m.roles.find(n.pid);
		if (r == m.roles.end() || (r->second.first != NAJEMNICY_MELEY_ROLE_EGG && r->second.first != NAJEMNICY_MELEY_ROLE_MAGMA))
			return NULL;
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(ch->GetMapIndex(), dwNow);
		if (r->second.first == NAJEMNICY_MELEY_ROLE_EGG)
		{
			std::vector<LPCHARACTER> eggs;
			for (size_t i = 0; i < scan.foes.size(); ++i)
			{
				if (scan.foes[i].dwRace != 20422)
					continue;
				LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
				if (IsPlayerBotPdgFoe(ch, c))
					eggs.push_back(c);
			}
			if (eggs.empty())
				return NULL;
			std::sort(eggs.begin(), eggs.end(), [](LPCHARACTER a, LPCHARACTER b) { return (DWORD)a->GetVID() < (DWORD)b->GetVID(); });
			return eggs[(size_t)r->second.second % eggs.size()];
		}
		LPCHARACTER cur = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		LPCHARACTER best = NULL;
		int bestScore = INT_MAX;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD race = scan.foes[i].dwRace;
			if (race >= 20000 || race == 6118 || race == 6116)
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c))
				continue;
			LPCHARACTER v = c->GetVictim();
			if (!IsNajemnikPartyOf(v, n.ownerPid) ||
					DISTANCE_APPROX(owner->GetX() - c->GetX(), owner->GetY() - c->GetY()) > PLAYERBOT_PDG_HUNT_RANGE)
				continue;
			if (stage >= 2 && stage <= 3 && v->GetJob() != JOB_SHAMAN)
				continue;
			int score = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			if (v->GetJob() == JOB_SHAMAN)
				score -= 3000;
			if (c == cur)
				score -= 2000;
			if (score < bestScore)
			{
				bestScore = score;
				best = c;
			}
		}
		return best;
	}

	// ---- MT2009_PLUS_NAJEMNICY_V4: the objective of the stage, as the bots' run leader takes it

	const int NAJEMNICY_DG_GOAL_RANGE = 6000;	// an objective this near the owner (its room)
	const int NAJEMNICY_DG_GOAL_HP = 30;		// under it the mercenary leaves the objective to the party pass
	const int NAJEMNICY_DG_OWNER_LOW_HP = 40;	// the owner under it and struck: the party pass defends the owner first

	// The stage's objective (GetPlayerBotDgRunObjectives - what the bots' run leader hits and its party with it): the
	// Biblioteka's Metins, Queens and Baroness, Razador's Ignitor, Metin and Razador, Nemere's Szels, Pillar and Nemere,
	// the Blue Dragon's stones, Atlantis's shells and Guardians, Meley's eggs, Idall and statues, Erebu's healers, the
	// Yohara dungeons' key monsters, Metins and bosses, Swiatynia Wezy's Metin of the turn (never one out of its order),
	// its Time Metins, Warriors and Nethis, Alastor. Within NAJEMNICY_DG_GOAL_RANGE of the owner and reachable; the
	// owner's own target first when it is one, Meley's statues the most hurt first (MT2009_PLUS_BOT_MELEY_STATUE_FOCUS_V1),
	// else the one in hand, else the nearest. NULL: no objective now (the party pass's fight round the owner).
	LPCHARACTER PickNajemnikDgObjective(LPCHARACTER ch, const TPlayerBotAIState& state, LPCHARACTER owner, LPDUNGEON d, int iDef,
			DWORD dwNow)
	{
		if (iDef < 0 || !d || ch->GetMaxHP() <= 0 || (long long)ch->GetHP() * 100 < (long long)ch->GetMaxHP() * NAJEMNICY_DG_GOAL_HP)
			return NULL;
		if (owner->GetMaxHP() > 0 && (long long)owner->GetHP() * 100 < (long long)owner->GetMaxHP() * NAJEMNICY_DG_OWNER_LOW_HP)
			return NULL;
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[iDef];
		const long map = ch->GetMapIndex();
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(map, dwNow);
		std::vector<DWORD> goals;
		GetPlayerBotDgRunObjectives(def, d, scan, goals);
		if (goals.empty())
			return NULL;
		const bool meley = def.bKind == DGRUN_KIND_MELEY;
		LPCHARACTER ownerTarget = owner->GetTarget();
		LPCHARACTER cur = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		LPCHARACTER best = NULL;
		long long bestScore = 0;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const DWORD race = scan.foes[i].dwRace;
			if (std::find(goals.begin(), goals.end(), race) == goals.end() || IsPlayerBotZodiacLeftToPerson(race))
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c) || (def.bKind == DGRUN_KIND_YDG && IsPlayerBotYdgGoalAway(map, c)))
				continue;
			if (DISTANCE_APPROX(owner->GetX() - c->GetX(), owner->GetY() - c->GetY()) > NAJEMNICY_DG_GOAL_RANGE)
				continue;
			long long score = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			if (meley && race == 6118 && c->GetMaxHP() > 0)
				score += (long long)c->GetHP() * 100 / c->GetMaxHP() * 100000LL;
			if (c == cur)
				score -= meley && race == 6118 ? 150000LL : 3000LL;
			if (c == ownerTarget)
				score -= 100000000LL;
			if (!best || score < bestScore)
			{
				best = c;
				bestScore = score;
			}
		}
		if (best && best != cur && !IsPlayerBotReachable(map, ch->GetX(), ch->GetY(), best->GetX(), best->GetY()))
			return NULL;
		return best;
	}

	// ---- MT2009_PLUS_NAJEMNICY_V4: what the bots' runs do with the people's part of a dungeon

	// Swiatynia Wezy: Pyl Wezowy from the mercenary's bag (its owner's - it never buys one) while the Portal's clock is
	// under the quest's 60 minutes - a minute a dust (UsePlayerBotWezeDust's rule), one use in the instance every 3 s.
	std::map<long, DWORD> s_mapNajemnicyWezeDust;	// instance -> the next use

	bool UseNajemnikWezeDust(LPCHARACTER ch, LPDUNGEON d, DWORD dwNow)
	{
		if (!IsPlayerBotWezeDungeon(d))
			return false;
		const long map = d->GetMapIndex();
		if (d->GetFlag("closed") == 1)
		{
			s_mapNajemnicyWezeDust.erase(map);
			return false;
		}
		if (d->GetFlag("started") != 1)
			return false;
		DWORD& next = s_mapNajemnicyWezeDust[map];
		if (next != 0 && (int)(next - dwNow) > 0)
			return false;
		next = dwNow + 3000;
		const int before = d->GetFlag("limit_at");
		if ((d->GetFlag("start") + PLAYERBOT_WEZE_LIMIT_MAX_S - before) / 60 <= 0)
			return false;
		const int cell = FindPlayerBotTowerItemCell(ch, PLAYERBOT_WEZE_DUST);
		if (cell < 0)
			return false;
		const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)cell));
		sys_log(0, "NAJEMNICY: weze dust pid=%u name=%s instance=%ld ok=%d limit_at=%d->%d", ch->GetPlayerID(), ch->GetName(), map,
				ok ? 1 : 0, before, d->GetFlag("limit_at"));
		return true;
	}

	// Beran (Przebudzeni and Szczelina): Duch Sura takes three Krete Klucze from every PERSON inside (krypta's people,
	// not the bots) - the mercenaries' keys (their kills' drops, picked up by the item pass) go to their owner while the
	// owner holds fewer than three, the whole stack into a free cell of the owner's (the window's "Zabierz").
	bool HandNajemnikBeranKeys(LPCHARACTER ch, LPCHARACTER owner, LPDUNGEON d, int iYdgDef, DWORD dwNow)
	{
		if (iYdgDef < 0 || !d || d->GetFlag("level") != 0 || owner->GetMapIndex() != ch->GetMapIndex() || !owner->IsItemLoaded())
			return false;
		const TPlayerBotYdgDef* y = FindPlayerBotYdgDef(PLAYERBOT_DGRUN_DEFS[iYdgDef].szKey);
		if (!y || y->iBoss != YDG_BERAN)
			return false;
		const DWORD key = PlayerBotYdgVnum(*y, 31180);
		const int has = (int)owner->CountSpecifyItem(key);
		if (has >= PLAYERBOT_YDG_KEYS_EACH)
			return false;
		const int cell = FindPlayerBotTowerItemCell(ch, key);
		LPITEM item = cell >= 0 ? ch->GetInventoryItem(cell) : NULL;
		if (!item)
			return false;
		const int to = owner->GetEmptyInventory(item->GetSize());
		if (to < 0)
		{
			PlayerBotLogThrottled("najemnicy_beran_keys_full", dwNow, "NAJEMNICY: beran keys wait pid=%u name=%s owner=%u (owner's bag full)",
					ch->GetPlayerID(), ch->GetName(), owner->GetPlayerID());
			return false;
		}
		const int count = (int)item->GetCount();
		HandPlayerBotSidekickItemOver(ch, owner, item, to);
		LogManager::instance().ItemLog(owner, item, "NAJEMNIK_KLUCZ", ch->GetName());
		TellNajemnicy(owner, "%s oddaje ci Krete Klucze: %d (masz %d/%d).", ch->GetName(), count, has + count, PLAYERBOT_YDG_KEYS_EACH);
		sys_log(0, "NAJEMNICY: beran keys pid=%u name=%s owner=%u vnum=%u count=%d owner_had=%d", ch->GetPlayerID(), ch->GetName(),
				owner->GetPlayerID(), (unsigned int)key, count, has);
		return true;
	}

	// Inside a dungeon at its owner's side ("the player as leader"): the dungeon's items first - a seal or a key it
	// holds is used, a cog, a Maat stone, a crystal or the Atlantis key handed to its NPC, the Meley ring, Balathor's
	// arrow (ManagePlayerBotPdgItems), the Yohara dungeons' keys by class (Nemere's Frost Key a Shaman's, the Ice Flower
	// Key a Ninja's or a Shaman's: ManagePlayerBotYdgItems); then, under "Za mna" and "Walcz sam", the fight of a
	// person's party bot - the dungeon's own foes only (the Blue Dragon's stones first, no shielded statue, no Metin out
	// of its order, no Balathor egg, no Zodiac boss left to the person): round the owner (PickPlayerBotPdgFoe) or on its
	// own (PickPlayerBotPdgSoloFoe). It never leaves: the owner's map is its map (the catch-up above), the dungeon's
	// d.exit_all its way out. False when nothing here took the tick (the ordinary follow and fight go on, the
	// dungeon's no-target rules still applied - IsPlayerBotPdgFoe).
	//
	// MT2009_PLUS_NAJEMNICY_V4 - what a bots' run does there, with the owner as the run's leader (GetNajemnicyDgRun):
	//   * Krypta Balathora: the module's player list (CBalathor::Login, the ice's polymorph ended - the bots' presence
	//     pass, ManagePlayerBotBalathorBot, which a mercenary's tick never reaches otherwise);
	//   * Glebie: the ground zones stepped out of (DodgePlayerBotGlebieZonesOnly - no run bonus), the egg chamber's
	//     duty and its portals (ManagePlayerBotGlebieBot through the Yohara item pass, the record above), Alastor the
	//     objective; waking him is the leader's - the owner's touch of the White Dragon Egg;
	//   * Swiatynia Wezy: the Kolumny's keys, the cages' keys, the Heads' shards (ManagePlayerBotWezeItems through the
	//     Yohara item pass), the dust it carries, the Metin of the turn and the 4th level's and Nethis as objectives;
	//   * Beran: the keys to the owner (Duch Sura counts the people's);
	//   * Meley: the roles (the egg killers, the magma guard, the healers; the statue team on the objective);
	//   * every dungeon of a bots' run (FindNajemnikDgRunDef): the stage's objective (PickNajemnikDgObjective).
	// A duty that takes it away from the owner (the egg chamber, an NPC across the room) holds the catch-up off
	// (n.dutyUntil). The talks a run's leader has (Razador's statue, Nemere's lion, Beran's Duch Sura, Wezy's Portal and
	// Smith, Glebie's egg, Meley's Dolnarr) stay the owner's - the owner is the leader.
	bool ManageNajemnikDungeon(LPCHARACTER ch, TPlayerBotAIState& state, TNajemnik& n, LPCHARACTER owner, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		TPlayerBotPdgBot& b = s_mapPlayerBotPdg[n.pid];
		if (b.lInstance != map)
		{
			b.lInstance = map;
			b.dwEnteredAt = dwNow;
			b.dwKills = 0;
			b.dwPersonGoneSince = 0;
			sys_log(0, "NAJEMNICY: dungeon pid=%u name=%s owner=%u instance=%ld order=%u", n.pid, ch->GetName(), n.ownerPid,
					map, (unsigned int)n.order);
		}
		// MT2009_PLUS_NAJEMNICY_V4: Krypta Balathora's player list and the ice's polymorph (nothing for a mercenary else -
		// it is no bots' Krypta run's member).
		if (map / 10000 == 420)
			ManagePlayerBotBalathorBot(ch, state, dwNow);
		LPDUNGEON dg = ch->GetDungeon() ? ch->GetDungeon() : CDungeonManager::instance().FindByMapIndex(map);
		const int iDef = FindNajemnikDgRunDef(map, dg);
		const int iYdg = FindNajemnikYdgDef(map, dg);
		TPlayerBotDgRun& run = GetNajemnicyDgRun(n.ownerPid, iDef, map);
		KeepNajemnicyGlebieRecord(n.ownerPid, run, dg);
		// Glebie's ground zones before anything (the bots' run's rule).
		if (iYdg >= 0 && DodgePlayerBotGlebieZonesOnly(ch, state, run, dwNow))
		{
			n.dutyUntil = dwNow + 3000;
			return true;
		}
		if (ManagePlayerBotPdgItems(ch, state, b, dwNow))
		{
			n.dutyUntil = dwNow + 5000;
			return true;
		}
		if (iYdg >= 0 && dg)
		{
			if (ManagePlayerBotYdgItems(ch, state, run, dg, dwNow))
			{
				n.dutyUntil = dwNow + 8000;
				return true;
			}
			if (HandNajemnikBeranKeys(ch, owner, dg, iYdg, dwNow) || UseNajemnikWezeDust(ch, dg, dwNow))
				return true;
		}
		if (n.order != NAJEMNIK_ORDER_FOLLOW && n.order != NAJEMNIK_ORDER_FREE)
			return false;
		LPCHARACTER foe = NULL;
		const char* why = "party";
		const bool meley = iDef >= 0 && PLAYERBOT_DGRUN_DEFS[iDef].bKind == DGRUN_KIND_MELEY;
		if (meley && dg)
		{
			// the healers' party buffs and heals before any role or objective (the bots' Meley healers)
			if (GetNajemnikMeleyRole(n, map, dwNow) == NAJEMNICY_MELEY_ROLE_HEAL && BuffPlayerBotTowerFellows(ch, state, dwNow))
				return true;
			foe = PickNajemnikMeleyRoleFoe(ch, state, n, owner, dg, dwNow);
			if (foe)
				why = foe->GetRaceNum() == 20422 ? "meley_egg" : "meley_magma";
		}
		if (!foe)
		{
			foe = PickNajemnikDgObjective(ch, state, owner, dg, iDef, dwNow);
			if (foe)
				why = "objective";
		}
		if (!foe)
			foe = n.order == NAJEMNIK_ORDER_FREE ? PickPlayerBotPdgSoloFoe(ch, state, owner, dwNow)
					: PickPlayerBotPdgFoe(ch, state, owner, dwNow);
		if (!foe)
			return false;
		if (std::strcmp(why, "party") != 0)
		{
			n.dutyUntil = dwNow + 4000;
			PlayerBotLogThrottled("najemnicy_dg_goal", dwNow, "NAJEMNICY: dungeon goal pid=%u name=%s owner=%u instance=%ld why=%s foe=%u hp=%d/%d",
					n.pid, ch->GetName(), n.ownerPid, map, why, (unsigned int)foe->GetRaceNum(), foe->GetHP(), foe->GetMaxHP());
		}
		if (BreakOffPlayerBotArzDgBoss(ch, state, map, dwNow))
			return true;
		if (ch->GetJob() == JOB_SHAMAN && ManagePlayerBotBuffPerson(ch, state, owner, dwNow, false, true))
			return true;
		state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
		const bool fought = FightPlayerBotTowerObjective(ch, state, foe, dwNow);
		if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
		{
			// A big monster on cells the routes do not end on (the party bots' way): any cell near it, else beside it.
			state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
			ClearPlayerBotRoute(state, false);
			state.dwNextNavPlanTime = 0;
			MovePlayerBot(ch, foe->GetX(), foe->GetY(), dwNow, 24, true, false);
			if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
				UnstickPlayerBotArzDgFoe(ch, foe, owner->GetX(), owner->GetY(), dwNow);
		}
		state.dwLastMeaningfulActivityTime = dwNow;
		return fought;
	}

	bool ManagePlayerBotNajemnikBot(LPDESC d, LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_mapNajemnik.empty() || !ch)
			return false;
		std::map<DWORD, TNajemnik>::iterator it = s_mapNajemnik.find(ch->GetPlayerID());
		if (it == s_mapNajemnik.end())
			return false;
		TNajemnik& n = it->second;
		if (!d || !d->IsPhase(PHASE_GAME) || n.dismiss)
			return true;
		// No trade, ever: an exchange opened with it is cancelled at once.
		if (ch->GetExchange())
		{
			ch->GetExchange()->Cancel();
			PlayerBotLogThrottled("najemnicy_exchange", dwNow, "NAJEMNICY: exchange cancelled pid=%u name=%s", n.pid,
					ch->GetName());
		}
		LPCHARACTER owner = FindNajemnicyOwnerHere(n.ownerPid);
		if (ch->IsDead())
		{
			// No restart of the engine's (it takes experience): it stands up beside the owner after 30 s.
			if (ch->m_pkDeadEvent)
				event_cancel(&ch->m_pkDeadEvent);
			state.dwTargetVID = 0;
			if (n.deadAt == 0)
			{
				n.deadAt = dwNow;
				++s_uNajemnicyDeaths;
				if (owner)
					TellNajemnicy(owner, "%s padl - wstanie przy tobie za 30 sekund.", ch->GetName());
				sys_log(0, "NAJEMNICY: died pid=%u name=%s owner=%u map=%ld", n.pid, ch->GetName(), n.ownerPid,
						ch->GetMapIndex());
			}
			if (dwNow - n.deadAt >= NAJEMNICY_REVIVE_MS)
			{
				StandPlayerBotUpHere(ch);
				ch->PointChange(POINT_HP, ch->GetMaxHP() / 2 - ch->GetHP());
				ch->PointChange(POINT_SP, ch->GetMaxSP() / 2 - ch->GetSP());
				n.deadAt = 0;
				if (owner && !owner->IsWarping())
					PlaceNajemnikBesideOwner(ch, state, owner, dwNow, "revive");
				sys_log(0, "NAJEMNICY: stood up pid=%u name=%s owner=%u", n.pid, ch->GetName(), n.ownerPid);
			}
			return true;
		}
		n.deadAt = 0;
		if (ch->GetHP() <= 0)
		{
			if (ch->IsStateMove())
				ch->Stop();
			return true;
		}
		// Its first entry: the bag of a new character emptied, then the owner's level and skills.
		if (!n.setupDone)
		{
			if (!ch->IsItemLoaded())
				return true;
			ClearPlayerBotPvpFanBelongings(ch);
			ch->SetGold(0);
			if (CGuild* g = ch->GetGuild())
				g->RequestRemoveMember(ch->GetPlayerID());
			n.setupDone = true;
			NajemnicyQuery("UPDATE player.najemnicy SET setup_done=1 WHERE merc_pid=%u", n.pid);
			sys_log(0, "NAJEMNICY: first setup pid=%u name=%s owner=%u", n.pid, ch->GetName(), n.ownerPid);
		}
		if (!owner || !owner->GetSectree() || owner->IsWarping())
		{
			// A warp: it waits (ManagePlayerBotNajemnicy lets it go when the owner does not come back).
			if (ch->IsStateMove())
				ch->Stop();
			ch->SetVictim(NULL);
			state.dwTargetVID = 0;
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		if (n.syncedOwnerLevel != (int)owner->GetLevel() || (int)(dwNow - n.nextSync) >= 0)
		{
			n.nextSync = dwNow + NAJEMNICY_SYNC_CHECK_MS;
			if (n.syncedOwnerLevel != (int)owner->GetLevel() || ch->GetLevel() != owner->GetLevel())
				SyncNajemnik(ch, state, n, owner, dwNow, n.syncedOwnerLevel < 0 ? "summon" : "owner_level");
		}
		if ((int)(dwNow - n.nextSave) >= 0)
		{
			n.nextSave = dwNow + NAJEMNICY_SAVE_MS;
			PersistPlayerBot(ch, state, dwNow);
		}
		// MT2009_PLUS_NAJEMNICY_V2: its storages into its bag, and its owner's consumables from it (it never buys).
		SweepNajemnikStorage(ch, n, dwNow);
		const bool fighting = state.dwTargetVID != 0 || (DWORD)(dwNow - ch->GetLastAttackTime()) < NAJEMNICY_FIGHT_MEMORY_MS;
		UseNajemnikConsumables(ch, state, n, fighting, dwNow);
		// A guild war's map: only a member of the owner's guild goes there.
		const bool ownerOnWarMap = CWarMapManager::instance().IsWarMap(owner->GetMapIndex());
		const bool inOwnersGuild = ch->GetGuild() && ch->GetGuild() == owner->GetGuild();
		const bool otherMap = owner->GetMapIndex() != ch->GetMapIndex();
		if (otherMap && ownerOnWarMap && !inOwnersGuild)
		{
			if (ch->IsStateMove())
				ch->Stop();
			ch->SetVictim(NULL);
			state.dwTargetVID = 0;
			PlayerBotLogThrottled("najemnicy_war_hold", dwNow, "NAJEMNICY: waits outside a guild war map pid=%u name=%s "
					"owner=%u map=%ld (not in the owner's guild)", n.pid, ch->GetName(), n.ownerPid, owner->GetMapIndex());
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		const int dist = otherMap ? INT_MAX : DISTANCE_APPROX(ch->GetX() - owner->GetX(), ch->GetY() - owner->GetY());
		// MT2009_PLUS_NAJEMNICY_V3: "Stoj tutaj" keeps its spot on the owner's map, however far the owner walks; another
		// map (a warp, a dungeon, a rejoin) anchors it anew beside the owner there.
		const bool hold = n.order == NAJEMNIK_ORDER_HOLD;
		// MT2009_PLUS_NAJEMNICY_V4: inside the owner's dungeon a duty (the egg chamber, a hand-in, the stage's objective)
		// keeps it where the duty is, and the room's objective may lie a little further than the open map's leash.
		const bool sameDungeon = !otherMap && IsNajemnikDungeonMap(ch->GetMapIndex());
		const bool onDuty = sameDungeon && n.dutyUntil != 0 && (int)(n.dutyUntil - dwNow) > 0;
		const int catchUp = sameDungeon ? NAJEMNICY_DG_TELEPORT_DISTANCE : NAJEMNICY_TELEPORT_DISTANCE;
		if (otherMap || (!hold && !onDuty && dist > catchUp))
		{
			if (owner->IsDead() || (int)(dwNow - n.nextCatchUp) < 0)
				return true;
			n.nextCatchUp = dwNow + 3000;
			PlaceNajemnikBesideOwner(ch, state, owner, dwNow, otherMap ? "follow" : "catch_up");
			return true;
		}
		if (hold && n.holdMap != ch->GetMapIndex())
		{
			n.holdMap = ch->GetMapIndex();
			n.holdX = ch->GetX();
			n.holdY = ch->GetY();
		}
		if ((int)(dwNow - n.nextParty) >= 0)
		{
			n.nextParty = dwNow + NAJEMNICY_PARTY_CHECK_MS;
			KeepNajemnikInParty(ch, owner, dwNow);
		}
		// MT2009_PLUS_NAJEMNICY_V2: a piece its owner put on mid-blow waits for the engine's moment - no new blow till then.
		if (RetryNajemnikPendingWear(ch, state, n, dwNow))
		{
			if (dist > NAJEMNICY_FOLLOW_DISTANCE)
			{
				long x = 0, y = 0;
				GetPlayerBotSidekickSpot(ch, owner, x, y);
				WalkPlayerBotSidekick(ch, x, y, dwNow, dist > 1500);
			}
			else if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		// The fight - by the owner's order (MT2009_PLUS_NAJEMNICY_V3, ChooseNajemnikFoe): "Za mna" what the owner fights,
		// what attacks either of them, then what stands near (the Towarzysz's "atakuj"); "Bij moj cel" the owner's target;
		// "Walcz sam" everything near the owner; "Stoj tutaj" what comes to its spot.
		// MT2009_PLUS_NAJEMNICY_V3: a dungeon with the owner - its items and the party bots' dungeon fight first.
		const bool dungeon = IsNajemnikDungeonMap(ch->GetMapIndex()) && !owner->IsDead();
		if (dungeon && ManageNajemnikDungeon(ch, state, n, owner, dwNow))
			return true;
		int why = PLAYERBOT_SIDEKICK_FOE_NEARBY;
		LPCHARACTER foe = owner->IsDead() ? NULL : ChooseNajemnikFoe(ch, owner, n, why);
		if (foe && dungeon && !IsPlayerBotPdgFoe(ch, foe))
			foe = NULL;	// the dungeon's no-target rules (a Metin out of its order, a shielded statue, an egg)
		if (foe && !MayNajemnikStrike(ch, foe))
		{
			PlayerBotLogThrottled("najemnicy_no_pvp", dwNow, "NAJEMNICY: leaves a character alone pid=%u name=%s foe=%s "
					"(no guild war of its guild)", n.pid, ch->GetName(), foe->GetName());
			foe = NULL;
		}
		const bool mayLoot = !n.noLoot && !hold;
		if (foe && why == PLAYERBOT_SIDEKICK_FOE_NEARBY && mayLoot && RunNajemnikLoot(ch, state, n, owner, dwNow))
			return true;
		if (foe)
		{
			if (ch->GetJob() == JOB_SHAMAN && ManagePlayerBotBuffPerson(ch, state, owner, dwNow, false, true))
				return true;
			return FightPlayerBotSidekickFoe(ch, state, n.rt, foe, why, dwNow);
		}
		if (state.dwTargetVID != 0)
		{
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
		}
		if (mayLoot && RunNajemnikLoot(ch, state, n, owner, dwNow))
			return true;
		if (hold)
		{
			const int fromSpot = DISTANCE_APPROX(ch->GetX() - n.holdX, ch->GetY() - n.holdY);
			if (fromSpot > NAJEMNICY_HOLD_RETURN)
			{
				WalkPlayerBotSidekick(ch, n.holdX, n.holdY, dwNow, false);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				state.dwLastMeaningfulActivityTime = dwNow;
				return true;
			}
			if (ch->IsStateMove())
				ch->Stop();
		}
		else
		{
			const int leash = n.order == NAJEMNIK_ORDER_FREE ? NAJEMNICY_FREE_LEASH : NAJEMNICY_FOLLOW_DISTANCE;
			if (dist > leash)
			{
				long x = 0, y = 0;
				GetPlayerBotSidekickSpot(ch, owner, x, y);
				WalkPlayerBotSidekick(ch, x, y, dwNow, dist > 1500);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				state.dwLastMeaningfulActivityTime = dwNow;
				return true;
			}
			if (ch->IsStateMove() && dist <= NAJEMNICY_FOLLOW_DISTANCE / 2)
				ch->Stop();
		}
		state.dwLastMeaningfulActivityTime = dwNow;
		if (ch->GetJob() == JOB_SHAMAN && ManagePlayerBotBuffPerson(ch, state, owner, dwNow, true, true))
			return true;
		ManagePlayerBotCombatBuffs(ch, state, dwNow, true);
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// A mercenary's login (CPlayerBotManager::OnPlayerLoaded).
	void OnPlayerBotNajemnikLoaded(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		std::map<DWORD, TNajemnik>::iterator it = ch ? s_mapNajemnik.find(ch->GetPlayerID()) : s_mapNajemnik.end();
		if (it == s_mapNajemnik.end())
			return;
		TNajemnik& n = it->second;
		n.phase = NAJEMNIK_READY;
		n.readyAt = dwNow;
		n.nextSync = 0;
		n.syncedOwnerLevel = -1;
		n.nextSave = dwNow + NAJEMNICY_SAVE_MS;
		state.bBotRole = BOT_ROLE_PARTY_FIGHTER;
		++s_uNajemnicySummons;
		// The fee: the first minute at its entry, then one a minute (ManagePlayerBotNajemnicy).
		TNajemnicyOwner& o = s_mapNajemnicyOwner[n.ownerPid];
		if (o.nextBill == 0)
		{
			// MT2009_PLUS_NAJEMNICY_V3: a minute paid on another core (a move) runs out first - no gap, no minute twice.
			const long long paidLeft = NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"SELECT CAST(billed_until AS SIGNED) - CAST(UNIX_TIMESTAMP() AS SIGNED) FROM player.najemnicy_vault WHERE owner_pid=%u",
					n.ownerPid)), 0);
			o.nextBill = dwNow + (DWORD)(MINMAX(0LL, paidLeft, 60LL) * 1000);
		}
		o.nextVidSend = 0;	// MT2009_PLUS_NAJEMNICY_V2: its VID to the owner's client at the next pass
		o.vidSig.clear();
		LPCHARACTER owner = FindNajemnicyOwnerHere(n.ownerPid);
		if (owner && !n.rejoin)
			TellNajemnicy(owner, "%s jest przy tobie.", ch->GetName());
		sys_log(0, "NAJEMNICY: entered pid=%u name=%s owner=%u slot=%u map=%ld (%ld,%ld) rejoin=%d order=%u no_loot=%d", n.pid,
				ch->GetName(), n.ownerPid, (unsigned int)n.slot, ch->GetMapIndex(), ch->GetX(), ch->GetY(), n.rejoin ? 1 : 0,
				(unsigned int)n.order, n.noLoot ? 1 : 0);
	}

	// Where a mercenary loads (CPlayerBotManager::PlaceLoadingBot, PVP Fan's hook): beside its owner.
	bool PlacePlayerBotNajemnikLoading(DWORD pid, long& lMapIndex, long& x, long& y)
	{
		std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.find(pid);
		if (it == s_mapNajemnik.end())
			return false;
		LPCHARACTER owner = FindNajemnicyOwnerHere(it->second.ownerPid);
		if (!owner || !owner->GetSectree() || !map_allow_find(owner->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN
				? owner->GetMapIndex() / 10000 : owner->GetMapIndex()))
			return false;
		lMapIndex = owner->GetMapIndex();
		x = owner->GetX() + number(-150, 150);
		y = owner->GetY() + number(-150, 150);
		return true;
	}

	// Out of the world: out of the party (an offline member would stay in it), saved, logged off. Never from inside the
	// bots' pass (the tick only marks n.dismiss).
	void DespawnNajemnik(DWORD pid, const char* why)
	{
		std::map<DWORD, TNajemnik>::iterator it = s_mapNajemnik.find(pid);
		if (it == s_mapNajemnik.end())
			return;
		const DWORD ownerPid = it->second.ownerPid;
		const std::string name = it->second.name;
		// MT2009_PLUS_NAJEMNICY_V3: the owner went to another core or channel (owner_moved) or logged out (owner_gone) -
		// it stays summoned (player.najemnicy.summoned) and comes back where the owner arrives; a move keeps it in the
		// owner's party too (the engine links it again at its entry, a dungeon's party included). Any other way out
		// (the owner's dismissal, the empty vault, the module off, a load that never came) ends the summon.
		const bool move = std::strcmp(why, "owner_moved") == 0;
		const bool keepSummoned = move || std::strcmp(why, "owner_gone") == 0;
		if (!keepSummoned)
			NajemnicyQuery("UPDATE player.najemnicy SET summoned=0 WHERE merc_pid=%u", pid);
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (ch)
		{
			if (ch->GetExchange())
				ch->GetExchange()->Cancel();
			if (ch->IsDead())
				StandPlayerBotUpHere(ch);
			if (!move)
				LeavePlayerBotParty(ch);
			ch->Save();
		}
		CPlayerBotManager::instance().Despawn(pid, playerbot_session_rules::OUT_GM);
		s_mapNajemnik.erase(it);
		++s_uNajemnicyDismissals;
		sys_log(0, "NAJEMNICY: dismissed pid=%u name=%s owner=%u why=%s", pid, name.c_str(), ownerPid, why);
		if (CountNajemnicySummonedOf(ownerPid) == 0)
			s_mapNajemnicyOwner.erase(ownerPid);
		// MT2009_PLUS_NAJEMNICY_V2: the owner's client forgets it at once (the target board's "Ekwipunek").
		LPCHARACTER owner = FindNajemnicyOwnerHere(ownerPid);
		if (owner)
		{
			std::map<DWORD, TNajemnicyOwner>::iterator rec = s_mapNajemnicyOwner.find(ownerPid);
			TNajemnicyOwner none;
			AnnounceNajemnicyVids(owner, rec != s_mapNajemnicyOwner.end() ? rec->second : none, get_dword_time());
		}
	}

	void DespawnNajemnicyOf(DWORD ownerPid, const char* why)
	{
		std::vector<DWORD> pids;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			if (it->second.ownerPid == ownerPid)
				pids.push_back(it->first);
		for (size_t i = 0; i < pids.size(); ++i)
			DespawnNajemnik(pids[i], why);
	}

	// ------------------------------------------------------------------ the vault

	// One minute of the owner's summoned mercenaries; false when the vault could not pay it (everything left is taken).
	bool BillNajemnicyOwner(DWORD ownerPid, TNajemnicyOwner& o, int count, LPCHARACTER owner)
	{
		const long long priceH = GetNajemnicyPriceH();
		const long long total = priceH * count + o.carry;
		const long long due = total / 60;
		o.carry = total % 60;
		if (due <= 0)
			return true;
		std::unique_ptr<SQLMsg> m(NajemnicyQuery(
				"UPDATE player.najemnicy_vault SET balance=balance-%lld, total_paid=total_paid+%lld, updated_at=NOW(), "
				"billed_until=UNIX_TIMESTAMP()+60 WHERE owner_pid=%u AND balance>=%lld", due, due, ownerPid, due));
		if (NajemnicyOk(m) && m->Get()->uiAffectedRows > 0)
		{
			s_llNajemnicyBilled += due;
			const long long left = GetNajemnicyBalance(ownerPid);
			const long long perMinute = MAX(1LL, priceH * count / 60);
			const long long minutes = left / perMinute;
			if (minutes <= NAJEMNICY_WARN_MINUTES && !o.warned)
			{
				o.warned = true;
				TellNajemnicy(owner, "W skarbcu zostalo %lld yang - wystarczy na okolo %lld min. Wplac yang (list "
						"\"Najemnicy\"), inaczej najemnicy odejda.", left, minutes);
				sys_log(0, "NAJEMNICY: warned owner=%u balance=%lld minutes=%lld summoned=%d", ownerPid, left, minutes, count);
			}
			else if (minutes > NAJEMNICY_WARN_MINUTES)
				o.warned = false;
			return true;
		}
		// Not enough: what is left is taken and they leave.
		const long long left = GetNajemnicyBalance(ownerPid);
		if (left > 0)
		{
			NajemnicyQuery("UPDATE player.najemnicy_vault SET balance=balance-%lld, total_paid=total_paid+%lld, "
					"updated_at=NOW() WHERE owner_pid=%u AND balance>=%lld", left, left, ownerPid, left);
			s_llNajemnicyBilled += left;
		}
		return false;
	}

	// ------------------------------------------------------------------ the census and the clean-up

	void CleanNajemnicyRetired()
	{
		std::unique_ptr<SQLMsg> m(NajemnicyQuery(
				"SELECT n.merc_pid, n.account_id FROM player.najemnicy n LEFT JOIN player.player p ON p.id=n.merc_pid "
				"WHERE n.retired=1 AND n.retired_at < NOW() - INTERVAL %d MINUTE "
				"AND (p.id IS NULL OR p.last_play < NOW() - INTERVAL %d MINUTE) LIMIT 50",
				NAJEMNICY_RETIRED_DELETE_MINUTES, NAJEMNICY_RETIRED_DELETE_MINUTES));
		if (!NajemnicyOk(m) || !m->Get()->pSQLResult)
			return;
		std::vector<std::pair<DWORD, DWORD> > gone;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(m->Get()->pSQLResult)))
		{
			DWORD pid = 0, acc = 0;
			str_to_number(pid, row[0] ? row[0] : "0");
			str_to_number(acc, row[1] ? row[1] : "0");
			if (pid)
				gone.push_back(std::make_pair(pid, acc));
		}
		for (size_t i = 0; i < gone.size(); ++i)
		{
			const DWORD pid = gone[i].first, acc = gone[i].second;
			if (CHARACTER_MANAGER::instance().FindByPID(pid) || P2P_MANAGER::instance().FindByPID(pid) ||
					IsPlayerBotNajemnikPID(pid))
				continue;
			NajemnicyQuery("DELETE FROM player.item WHERE owner_id=%u AND `window` NOT IN ('SAFEBOX','MALL')", pid);
			if (acc)
				NajemnicyQuery("DELETE FROM player.item WHERE owner_id=%u AND `window` IN ('SAFEBOX','MALL')", acc);
			NajemnicyQuery("DELETE FROM player.affect WHERE dwPID=%u", pid);
			NajemnicyQuery("DELETE FROM player.quest WHERE dwPID=%u", pid);
			NajemnicyQuery("DELETE FROM player.player WHERE id=%u AND account_id=%u", pid, acc);
			if (acc)
			{
				NajemnicyQuery("DELETE FROM player.player_index WHERE id=%u", acc);
				NajemnicyQuery("DELETE FROM account.account WHERE id=%u AND login LIKE 'playerbot\\_nj%%' AND password='!'", acc);
			}
			NajemnicyQuery("DELETE FROM player.najemnicy WHERE merc_pid=%u AND retired=1", pid);
			++s_uNajemnicyDeleted;
			sys_log(0, "NAJEMNICY: retired character deleted pid=%u account=%u", pid, acc);
		}
	}

	void LogNajemnicyCensus(DWORD dwNow, bool force)
	{
		if (!force && s_dwNajemnicyNextCensus != 0 && (int)(dwNow - s_dwNajemnicyNextCensus) < 0)
			return;
		s_dwNajemnicyNextCensus = dwNow + NAJEMNICY_CENSUS_MS;
		if (!EnsureNajemnicyTables())
			return;
		long long owners = 0, live = 0, retired = 0, vaults = 0, vaultSum = 0, unlocked = 0;
		{
			std::unique_ptr<SQLMsg> m(NajemnicyQuery(
					"SELECT COUNT(DISTINCT IF(retired=0, owner_pid, NULL)), SUM(retired=0), SUM(retired=1) FROM player.najemnicy"));
			MYSQL_ROW row = NULL;
			if (NajemnicyOk(m) && m->Get()->pSQLResult && (row = mysql_fetch_row(m->Get()->pSQLResult)))
			{
				if (row[0]) str_to_number(owners, row[0]);
				if (row[1]) str_to_number(live, row[1]);
				if (row[2]) str_to_number(retired, row[2]);
			}
		}
		{
			std::unique_ptr<SQLMsg> m(NajemnicyQuery("SELECT COUNT(*), IFNULL(SUM(balance),0) FROM player.najemnicy_vault"));
			MYSQL_ROW row = NULL;
			if (NajemnicyOk(m) && m->Get()->pSQLResult && (row = mysql_fetch_row(m->Get()->pSQLResult)))
			{
				if (row[0]) str_to_number(vaults, row[0]);
				if (row[1]) str_to_number(vaultSum, row[1]);
			}
		}
		unlocked = NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
				"SELECT COUNT(*) FROM player.najemnicy_unlock WHERE tasks>0")), 0);
		unsigned int loading = 0, ready = 0, dead = 0;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
		{
			if (it->second.phase == NAJEMNIK_LOADING)
				++loading;
			else
				++ready;
			if (it->second.deadAt)
				++dead;
		}
		sys_log(0, "NAJEMNICY: census core=ch%u owners=%lld mercs=%lld retired=%lld unlocked=%lld vaults=%lld vault_sum=%lld "
				"here_owners=%u here_loading=%u here_ready=%u here_dead=%u summons=%u dismissals=%u vault_empty=%u "
				"created=%u retired_now=%u deaths=%u deleted=%u billed=%lld deposited=%lld price_h=%lld off=%d free_unlock=%d",
				(unsigned int)g_bChannel, owners, live, retired, unlocked, vaults, vaultSum,
				(unsigned int)s_mapNajemnicyOwner.size(), loading, ready, dead, s_uNajemnicySummons, s_uNajemnicyDismissals,
				s_uNajemnicyEmpty, s_uNajemnicyCreated, s_uNajemnicyRetired, s_uNajemnicyDeaths, s_uNajemnicyDeleted,
				s_llNajemnicyBilled, s_llNajemnicyDeposited, GetNajemnicyPriceH(), IsNajemnicyOff() ? 1 : 0,
				IsNajemnicyFreeUnlock() ? 1 : 0);
		s_uNajemnicySummons = s_uNajemnicyDismissals = s_uNajemnicyEmpty = s_uNajemnicyCreated = s_uNajemnicyRetired = 0;
		s_uNajemnicyDeaths = s_uNajemnicyDeleted = 0;
		s_llNajemnicyBilled = s_llNajemnicyDeposited = 0;
		if (!force)
			CleanNajemnicyRetired();
	}

	// ------------------------------------------------------------------ the module's clock

	// From Update and the world clock (a core no bot has woken): the flags, the loads that never came, the owners
	// who left, the dismissals the tick asked for, the fee, the census.
	void ManagePlayerBotNajemnicy(DWORD dwNow)
	{
		if (s_dwNajemnicyNextTick != 0 && (int)(dwNow - s_dwNajemnicyNextTick) < 0)
			return;
		s_dwNajemnicyNextTick = dwNow + NAJEMNICY_TICK_MS;
		if (s_dwNajemnicyNextFlagPoll == 0 || (int)(dwNow - s_dwNajemnicyNextFlagPoll) >= 0)
		{
			s_dwNajemnicyNextFlagPoll = dwNow + NAJEMNICY_FLAG_POLL_MS;
			std::unique_ptr<SQLMsg> flag(NajemnicyQuery(
					"SELECT szName, lValue FROM player.quest WHERE dwPID=0 AND szName IN "
					"('m2_najemnicy_off','m2_najemnicy_free_unlock','m2_najemnicy_price_h')"));
			bool off = false, freeUnlock = false;
			long long price = 0;
			MYSQL_ROW row;
			if (NajemnicyOk(flag) && flag->Get()->pSQLResult)
				while (NULL != (row = mysql_fetch_row(flag->Get()->pSQLResult)))
				{
					long long v = 0;
					if (row[1])
						str_to_number(v, row[1]);
					if (row[0] && std::strcmp(row[0], "m2_najemnicy_off") == 0)
						off = v != 0;
					else if (row[0] && std::strcmp(row[0], "m2_najemnicy_free_unlock") == 0)
						freeUnlock = v != 0;
					else
						price = v;
				}
			s_bNajemnicyDbOff = off;
			s_bNajemnicyDbFreeUnlock = freeUnlock;
			s_llNajemnicyDbPrice = price;
		}
		LogNajemnicyCensus(dwNow, false);
		ProcessNajemnicyRejoins(dwNow);	// MT2009_PLUS_NAJEMNICY_V3
		if (s_mapNajemnik.empty())
			return;
		const bool off = IsNajemnicyOff();
		std::vector<std::pair<DWORD, std::string> > out;
		for (std::map<DWORD, TNajemnik>::iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
		{
			TNajemnik& n = it->second;
			if (off)
			{
				out.push_back(std::make_pair(n.pid, std::string("module_off")));
				continue;
			}
			if (n.dismiss)
			{
				out.push_back(std::make_pair(n.pid, n.dismissWhy.empty() ? std::string("asked") : n.dismissWhy));
				continue;
			}
			if (n.phase == NAJEMNIK_LOADING)
			{
				if (dwNow - n.askedAt > NAJEMNICY_LOAD_TIMEOUT_MS)
				{
					sys_err("NAJEMNICY: pid=%u login=%s did not load in %u s", n.pid, n.login.c_str(),
							NAJEMNICY_LOAD_TIMEOUT_MS / 1000);
					TellNajemnicy(FindNajemnicyOwnerHere(n.ownerPid), "%s nie dotarl - sprobuj wezwac go jeszcze raz.",
							n.name.c_str());
					out.push_back(std::make_pair(n.pid, std::string("load_timeout")));
				}
				continue;
			}
			if (!CHARACTER_MANAGER::instance().FindByPID(n.pid))
			{
				out.push_back(std::make_pair(n.pid, std::string("gone")));
				continue;
			}
		}
		// The owners: here, or gone for NAJEMNICY_OWNER_GONE_MS (a logout, another core or channel).
		std::set<DWORD> owners;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			owners.insert(it->second.ownerPid);
		for (std::set<DWORD>::const_iterator o = owners.begin(); o != owners.end(); ++o)
		{
			TNajemnicyOwner& rec = s_mapNajemnicyOwner[*o];
			LPCHARACTER owner = FindNajemnicyOwnerHere(*o);
			if (!owner)
			{
				// MT2009_PLUS_NAJEMNICY_V3: the owner is in the world on another core or channel - its mercenaries leave
				// here at once (still summoned) and the core the owner arrived on brings them in (OnNajemnicyOwnerArrived).
				if (P2P_MANAGER::instance().FindByPID(*o))
				{
					for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
						if (it->second.ownerPid == *o)
							out.push_back(std::make_pair(it->first, std::string("owner_moved")));
					continue;
				}
				if (rec.goneSince == 0)
					rec.goneSince = dwNow;
				else if (dwNow - rec.goneSince >= NAJEMNICY_OWNER_GONE_MS)
				{
					// MT2009_PLUS_NAJEMNICY_V3: a logout - the next entry is a login (the owner's "wracaja po zalogowaniu"
					// decides), not a move that brings them back whatever the switch says.
					NajemnicyQuery("UPDATE player.najemnicy_vault SET billed_until=LEAST(billed_until, UNIX_TIMESTAMP()-%d) "
							"WHERE owner_pid=%u", NAJEMNICY_MOVE_GRACE_S + 1, *o);
					for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
						if (it->second.ownerPid == *o)
							out.push_back(std::make_pair(it->first, std::string("owner_gone")));
				}
				continue;
			}
			rec.goneSince = 0;
			AnnounceNajemnicyVids(owner, rec, dwNow);	// MT2009_PLUS_NAJEMNICY_V2
			// The fee, a minute at a time, for the ones in the world (or on their way).
			if (rec.nextBill == 0 || (int)(dwNow - rec.nextBill) < 0)
				continue;
			int count = 0;
			for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
				if (it->second.ownerPid == *o && it->second.phase == NAJEMNIK_READY && !it->second.dismiss)
					++count;
			if (count == 0)
				continue;
			rec.nextBill = dwNow + NAJEMNICY_BILL_MS;
			if (!BillNajemnicyOwner(*o, rec, count, owner))
			{
				++s_uNajemnicyEmpty;
				TellNajemnicy(owner, "Skarbiec najemnikow jest pusty - najemnicy odchodza. Wplac yang i wezwij ich ponownie.");
				sys_log(0, "NAJEMNICY: vault empty owner=%u name=%s summoned=%d", *o, owner->GetName(), count);
				for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
					if (it->second.ownerPid == *o)
						out.push_back(std::make_pair(it->first, std::string("vault_empty")));
			}
		}
		for (size_t i = 0; i < out.size(); ++i)
			if (s_mapNajemnik.find(out[i].first) != s_mapNajemnik.end())
				DespawnNajemnik(out[i].first, out[i].second.c_str());
	}

	// ------------------------------------------------------------------ the commands

	// A small number of the command's: -1 when it is none (empty, not digits, over max).
	int ParseNajemnicyInt(const std::string& s, int max)
	{
		if (s.empty())
			return -1;
		int v = 0;
		for (size_t i = 0; i < s.size(); ++i)
		{
			if (s[i] < '0' || s[i] > '9')
				return -1;
			v = v * 10 + (s[i] - '0');
			if (v > max)
				return -1;
		}
		return v;
	}

	int ParseNajemnicySlot(const std::string& s)
	{
		return MAX(0, ParseNajemnicyInt(s, NAJEMNICY_MAX_SLOTS));
	}

	const TNajemnikRow* FindNajemnikRowBySlot(const std::vector<TNajemnikRow>& rows, int slot)
	{
		for (size_t i = 0; i < rows.size(); ++i)
			if (rows[i].slot == slot)
				return &rows[i];
		return NULL;
	}

	TNajemnik* FindNajemnikSummoned(DWORD ownerPid, int slot)
	{
		for (std::map<DWORD, TNajemnik>::iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
			if (it->second.ownerPid == ownerPid && it->second.slot == slot && !it->second.dismiss)
				return &it->second;
		return NULL;
	}

	void ListNajemnicy(LPCHARACTER ch)
	{
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		const int slots = GetNajemnicySlotsOf(ch);
		TellNajemnicy(ch, "Miejsca: %d, najemnicy: %d, skarbiec: %lld yang, oplata: %lld yang/h za kazdego wezwanego.", slots,
				(int)rows.size(), GetNajemnicyBalance(ch->GetPlayerID()), GetNajemnicyPriceH());
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TNajemnik* s = FindNajemnikSummoned(ch->GetPlayerID(), rows[i].slot);
			TellNajemnicy(ch, "%u. %s - %s %s%s", (unsigned int)rows[i].slot, rows[i].name.c_str(),
					GetNajemnikClassName(rows[i].race), GetNajemnikPathName(rows[i].race, rows[i].group),
					s ? (s->phase == NAJEMNIK_READY ? " (wezwany)" : " (w drodze)") : "");
		}
	}

	void ShowNajemnicyVault(LPCHARACTER ch)
	{
		const long long balance = GetNajemnicyBalance(ch->GetPlayerID());
		const int summoned = CountNajemnicySummonedOf(ch->GetPlayerID());
		const long long perMinute = MAX(1LL, GetNajemnicyPriceH() * MAX(1, summoned) / 60);
		const long long minutes = balance / perMinute;
		TellNajemnicy(ch, "Skarbiec: %lld yang. Wezwanych: %d. Wystarczy na %lld h %lld min (przy %d najemnikach).", balance,
				summoned, minutes / 60, minutes % 60, MAX(1, summoned));
	}

	void CreateNajemnik(LPCHARACTER ch, int race, int group, const std::string& name)
	{
		const int slots = GetNajemnicySlotsOf(ch);
		if (slots <= 0)
		{
			TellNajemnicy(ch, "Najemnicy nie sa jeszcze dla ciebie odblokowani (Kolekcjoner Najemnikow, od 80 poziomu).");
			return;
		}
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		if ((int)rows.size() >= slots)
		{
			TellNajemnicy(ch, "Wszystkie miejsca sa zajete (%d). Wiecej daja zadania Kolekcjonera Najemnikow i poziom.", slots);
			return;
		}
		if (race < 0 || race > 7 || group < 1 || group > 2)
		{
			TellNajemnicy(ch, "Nie ma takiej klasy albo drogi.");
			return;
		}
		if (!IsPlayerBotSidekickNameAllowed(name.c_str()))
		{
			TellNajemnicy(ch, "To imie nie pasuje: od 3 do 16 liter i cyfr, bez polskich znakow, spacji i zakazanych slow.");
			return;
		}
		if (NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery("SELECT COUNT(*) FROM player.player WHERE name='%s'",
				name.c_str())), 1) != 0)
		{
			TellNajemnicy(ch, "To imie jest juz zajete - wybierz inne.");
			return;
		}
		int slot = 0;
		for (int s = 1; s <= slots && !slot; ++s)
			if (!FindNajemnikRowBySlot(rows, s))
				slot = s;
		if (!slot)
			return;
		const DWORD pid = MakeNajemnikIdentity(ch, (BYTE)race, (BYTE)group, (BYTE)slot, name.c_str());
		if (!pid)
		{
			TellNajemnicy(ch, "Nie udalo sie przyjac najemnika - sprobuj za chwile.");
			return;
		}
		++s_uNajemnicyCreated;
		TellNajemnicy(ch, "%s (%s %s) jest twoim najemnikiem na miejscu %d. Wezwij go z listu \"Najemnicy\".", name.c_str(),
				GetNajemnikClassName((BYTE)race), GetNajemnikPathName((BYTE)race, (BYTE)group), slot);
		SyncNajemnicyQuestFlags(ch);
	}

	// MT2009_PLUS_NAJEMNICY_V3: rejoin - the owner arrived and it comes back by itself (no word of "already summoned" or
	// "still leaving": the rejoin tries again; already in the owner's party after a move, it takes no new place there).
	bool SummonNajemnik(LPCHARACTER ch, const TNajemnikRow& r, int alreadyCounted, bool rejoin = false)
	{
		if (FindNajemnikSummoned(ch->GetPlayerID(), r.slot) || IsPlayerBotNajemnikPID(r.pid))
		{
			if (!rejoin)
				TellNajemnicy(ch, "%s juz jest wezwany.", r.name.c_str());
			return false;
		}
		if (CHARACTER_MANAGER::instance().FindByPID(r.pid) || P2P_MANAGER::instance().FindByPID(r.pid))
		{
			if (!rejoin)
				TellNajemnicy(ch, "%s jeszcze odchodzi z poprzedniego miejsca - sprobuj za pol minuty.", r.name.c_str());
			return false;
		}
		LPPARTY party = ch->GetParty();
		const int members = party ? (int)party->GetMemberCount() : 1;
		const bool inParty = party && party->IsMember(r.pid);
		if (!inParty && members + alreadyCounted + 1 > PARTY_MAX_MEMBER)
		{
			TellNajemnicy(ch, "W grupie nie ma miejsca dla %s.", r.name.c_str());
			return false;
		}
		TNajemnik n;
		n.pid = r.pid;
		n.ownerPid = ch->GetPlayerID();
		n.accountId = r.accountId;
		n.slot = r.slot;
		n.race = r.race;
		n.group = r.group;
		n.setupDone = r.setupDone;
		n.login = r.login;
		n.name = r.name;
		n.phase = NAJEMNIK_LOADING;
		n.askedAt = get_dword_time();
		n.order = r.order;		// MT2009_PLUS_NAJEMNICY_V3: its last order and the loot switch
		n.noLoot = r.noLoot;
		n.rejoin = rejoin;
		s_mapNajemnik[r.pid] = n;
		// PVP Fan's spawn of a dedicated identity (its account, the registry's guards stepped over for this pid).
		if (!CPlayerBotManager::instance().SpawnPvpFan(r.pid, ch->GetEmpire(), r.accountId, r.login.c_str()))
		{
			s_mapNajemnik.erase(r.pid);
			TellNajemnicy(ch, "%s nie moze teraz przyjsc - sprobuj za chwile.", r.name.c_str());
			sys_log(0, "NAJEMNICY: spawn refused pid=%u login=%s owner=%u", r.pid, r.login.c_str(), ch->GetPlayerID());
			return false;
		}
		NajemnicyQuery("UPDATE player.najemnicy SET summoned=1 WHERE merc_pid=%u", r.pid);	// MT2009_PLUS_NAJEMNICY_V3
		sys_log(0, "NAJEMNICY: summoned pid=%u name=%s owner=%u owner_name=%s slot=%u map=%ld rejoin=%d", r.pid, r.name.c_str(),
				ch->GetPlayerID(), ch->GetName(), (unsigned int)r.slot, ch->GetMapIndex(), rejoin ? 1 : 0);
		return true;
	}

	void SummonNajemnicy(LPCHARACTER ch, const std::string& which)
	{
		if (IsNajemnicyOff())
		{
			TellNajemnicy(ch, "Najemnicy sa teraz wylaczeni na tym serwerze.");
			return;
		}
		const int slots = GetNajemnicySlotsOf(ch);
		if (slots <= 0)
		{
			TellNajemnicy(ch, "Najemnicy nie sa jeszcze dla ciebie odblokowani (Kolekcjoner Najemnikow, od 80 poziomu).");
			return;
		}
		if (ch->IsDead() || ch->IsObserverMode() || !ch->GetSectree())
			return;
		if (ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN || ch->GetDungeon())
		{
			TellNajemnicy(ch, "W lochu nie mozna wezwac najemnika - wezwij go przed wejsciem, wejdzie z toba.");
			return;
		}
		if (CWarMapManager::instance().IsWarMap(ch->GetMapIndex()))
		{
			TellNajemnicy(ch, "Na mapie wojny gildii nie mozna wezwac najemnika.");
			return;
		}
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		std::vector<const TNajemnikRow*> wanted;
		if (which == "wszyscy" || which == "all")
		{
			for (size_t i = 0; i < rows.size(); ++i)
				if (rows[i].slot <= slots && !FindNajemnikSummoned(ch->GetPlayerID(), rows[i].slot))
					wanted.push_back(&rows[i]);
		}
		else
		{
			const TNajemnikRow* r = FindNajemnikRowBySlot(rows, ParseNajemnicySlot(which));
			if (!r)
			{
				TellNajemnicy(ch, "Nie masz najemnika na tym miejscu.");
				return;
			}
			if (r->slot > slots)
			{
				TellNajemnicy(ch, "To miejsce nie jest jeszcze dostepne (zadania Kolekcjonera Najemnikow i poziom).");
				return;
			}
			wanted.push_back(r);
		}
		if (wanted.empty())
		{
			TellNajemnicy(ch, "Nie ma kogo wezwac.");
			return;
		}
		// At least a minute of everybody summoned then must be in the vault.
		const int after = CountNajemnicySummonedOf(ch->GetPlayerID()) + (int)wanted.size();
		const long long minute = MAX(1LL, GetNajemnicyPriceH() * after / 60);
		const long long balance = GetNajemnicyBalance(ch->GetPlayerID());
		if (balance < minute)
		{
			TellNajemnicy(ch, "W skarbcu jest %lld yang - za malo (minuta %d najemnikow kosztuje %lld). Wplac yang.", balance,
					after, minute);
			return;
		}
		int sent = 0;
		for (size_t i = 0; i < wanted.size(); ++i)
			if (SummonNajemnik(ch, *wanted[i], sent))
				++sent;
		if (sent > 0)
			TellNajemnicy(ch, "Wezwanych: %d. Oplata: %lld yang/h za kazdego, liczona co minute ze skarbca.", sent,
					GetNajemnicyPriceH());
		SyncNajemnicyQuestFlags(ch);
	}

	void DismissNajemnicyCommand(LPCHARACTER ch, const std::string& which)
	{
		if (which == "wszyscy" || which == "all")
		{
			const int n = CountNajemnicySummonedOf(ch->GetPlayerID());
			DespawnNajemnicyOf(ch->GetPlayerID(), "owner");
			TellNajemnicy(ch, "Odwolanych: %d.", n);
		}
		else
		{
			TNajemnik* n = FindNajemnikSummoned(ch->GetPlayerID(), ParseNajemnicySlot(which));
			if (!n)
			{
				TellNajemnicy(ch, "Ten najemnik nie jest wezwany.");
				return;
			}
			const std::string name = n->name;
			DespawnNajemnik(n->pid, "owner");
			TellNajemnicy(ch, "%s odchodzi.", name.c_str());
		}
		SyncNajemnicyQuestFlags(ch);
	}

	// ------------------------------------------------------------------ MT2009_PLUS_NAJEMNICY_V3: the rejoin

	// The arrived owner's summoned mercenaries not in this core's world yet, each tried until it comes (the old core
	// lets it go first: CHARACTER_MANAGER / P2P still know it for a moment) or the window closes.
	void ProcessNajemnicyRejoins(DWORD dwNow)
	{
		if (s_mapNajemnicyRejoin.empty())
			return;
		std::vector<DWORD> done;
		for (std::map<DWORD, TNajemnicyRejoin>::iterator it = s_mapNajemnicyRejoin.begin(); it != s_mapNajemnicyRejoin.end(); ++it)
		{
			TNajemnicyRejoin& rj = it->second;
			if ((int)(dwNow - rj.until) >= 0)
			{
				sys_log(0, "NAJEMNICY: rejoin window closed owner=%u", it->first);
				done.push_back(it->first);
				continue;
			}
			if ((int)(dwNow - rj.nextTry) < 0)
				continue;
			rj.nextTry = dwNow + NAJEMNICY_REJOIN_TRY_MS;
			LPCHARACTER owner = FindNajemnicyOwnerHere(it->first);
			if (!owner)
			{
				if (P2P_MANAGER::instance().FindByPID(it->first))
					done.push_back(it->first);	// on another core already: that core brings them
				continue;
			}
			if (!owner->GetSectree() || owner->IsWarping() || owner->IsDead() || owner->IsObserverMode())
				continue;
			if (IsNajemnicyOff())
			{
				done.push_back(it->first);
				continue;
			}
			// A guild war's map: they wait (still summoned) - the next arrival off it brings them.
			if (CWarMapManager::instance().IsWarMap(owner->GetMapIndex()))
				continue;
			const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(it->first);
			const int slots = GetNajemnicySlotsOf(owner);
			std::vector<const TNajemnikRow*> wanted;
			int waiting = 0;
			for (size_t i = 0; i < rows.size(); ++i)
			{
				const TNajemnikRow& r = rows[i];
				if (!r.summoned || FindNajemnikSummoned(it->first, r.slot) || IsPlayerBotNajemnikPID(r.pid))
					continue;
				if ((int)r.slot > slots)
				{
					NajemnicyQuery("UPDATE player.najemnicy SET summoned=0 WHERE merc_pid=%u", r.pid);
					continue;
				}
				if (CHARACTER_MANAGER::instance().FindByPID(r.pid) || P2P_MANAGER::instance().FindByPID(r.pid))
				{
					++waiting;	// still leaving the old core
					continue;
				}
				wanted.push_back(&r);
			}
			if (!wanted.empty())
			{
				const int after = CountNajemnicySummonedOf(it->first) + (int)wanted.size();
				const long long minute = MAX(1LL, GetNajemnicyPriceH() * after / 60);
				if (GetNajemnicyBalance(it->first) < minute)
				{
					TellNajemnicy(owner, "Skarbiec najemnikow jest pusty - najemnicy nie wracaja. Wplac yang i wezwij ich.");
					NajemnicyQuery("UPDATE player.najemnicy SET summoned=0 WHERE owner_pid=%u", it->first);
					sys_log(0, "NAJEMNICY: rejoin refused owner=%u vault below a minute of %d", it->first, after);
					done.push_back(it->first);
					continue;
				}
				int sent = 0;
				for (size_t i = 0; i < wanted.size(); ++i)
				{
					if (SummonNajemnik(owner, *wanted[i], sent, true))
						++sent;
					else
						++waiting;
				}
				if (sent > 0)
				{
					sys_log(0, "NAJEMNICY: rejoin owner=%u name=%s map=%ld sent=%d waiting=%d login=%d", it->first,
							owner->GetName(), owner->GetMapIndex(), sent, waiting, rj.login ? 1 : 0);
					SyncNajemnicyQuestFlags(owner);
				}
			}
			if (waiting == 0)
				done.push_back(it->first);
		}
		for (size_t i = 0; i < done.size(); ++i)
			s_mapNajemnicyRejoin.erase(done[i]);
	}

	// The owner entered the world on this core (the Najemnicy quest's login: "/najemnicy przybycie") - a login, a warp
	// between two maps of this core, a move from another core or channel. The client hears its mercenaries' VIDs at once
	// (the target board's "Ekwipunek" without the 20 s wait); the summoned ones not here come: always after a move (the
	// paid minute still running - billed_until), after a login unless the owner switched it off in the letter
	// (najemnicy.no_rejoin) or the event flag m2_najemnicy_rejoin_off is on.
	void OnNajemnicyOwnerArrived(LPCHARACTER ch)
	{
		const DWORD dwNow = get_dword_time();
		std::map<DWORD, TNajemnicyOwner>::iterator rec = s_mapNajemnicyOwner.find(ch->GetPlayerID());
		if (rec != s_mapNajemnicyOwner.end())
		{
			rec->second.goneSince = 0;
			rec->second.vidSig.clear();
			AnnounceNajemnicyVids(ch, rec->second, dwNow);
			rec->second.nextVidSend = dwNow + NAJEMNICY_ARRIVAL_VID_MS;	// and once more when the new client stands
		}
		if (IsNajemnicyOff() || !EnsureNajemnicyTables())
			return;
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		int away = 0;
		for (size_t i = 0; i < rows.size(); ++i)
			if (rows[i].summoned && !IsPlayerBotNajemnikPID(rows[i].pid))
				++away;
		if (away == 0)
			return;
		const long long paidLeft = NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
				"SELECT CAST(billed_until AS SIGNED) - CAST(UNIX_TIMESTAMP() AS SIGNED) FROM player.najemnicy_vault WHERE owner_pid=%u",
				ch->GetPlayerID())), -1000000LL);
		const bool move = paidLeft > -NAJEMNICY_MOVE_GRACE_S;
		if (!move)
		{
			if (ch->GetQuestFlag("najemnicy.no_rejoin") != 0 ||
					quest::CQuestManager::instance().GetEventFlag("m2_najemnicy_rejoin_off") != 0)
			{
				NajemnicyQuery("UPDATE player.najemnicy SET summoned=0 WHERE owner_pid=%u", ch->GetPlayerID());
				sys_log(0, "NAJEMNICY: login without the rejoin owner=%u name=%s away=%d", ch->GetPlayerID(), ch->GetName(), away);
				return;
			}
			TellNajemnicy(ch, "Najemnicy wracaja... (%d). Wylaczysz to w liscie \"Najemnicy\" -> Rozkazy.", away);
		}
		TNajemnicyRejoin& rj = s_mapNajemnicyRejoin[ch->GetPlayerID()];
		rj.until = dwNow + NAJEMNICY_REJOIN_WINDOW_MS;
		rj.nextTry = dwNow;
		rj.login = !move;
		sys_log(0, "NAJEMNICY: owner arrived owner=%u name=%s map=%ld away=%d move=%d paid_left=%lld", ch->GetPlayerID(),
				ch->GetName(), ch->GetMapIndex(), away, move ? 1 : 0, paidLeft);
	}

	// "/najemnicy powrot <0|1>": the summoned ones come back by themselves after a login (1, the default) or not.
	void SetNajemnicyRejoin(LPCHARACTER ch, const std::string& value)
	{
		if (value != "0" && value != "1")
		{
			TellNajemnicy(ch, "Powrot po zalogowaniu jest %s. Uzycie: /najemnicy powrot <1 wlacz | 0 wylacz>.",
					ch->GetQuestFlag("najemnicy.no_rejoin") ? "wylaczony" : "wlaczony");
			return;
		}
		ch->SetQuestFlag("najemnicy.no_rejoin", value == "1" ? 0 : 1);
		TellNajemnicy(ch, "%s", value == "1" ? "Po zalogowaniu wezwani najemnicy wracaja do ciebie sami." :
				"Po zalogowaniu najemnicy nie wracaja sami - wezwiesz ich z listu (zmiana rdzenia i kanalu ich nie odwoluje).");
	}

	// ------------------------------------------------------------------ MT2009_PLUS_NAJEMNICY_V3: the orders

	const char* GetNajemnikOrderName(int order)
	{
		switch (order)
		{
			case NAJEMNIK_ORDER_HOLD: return "Stoj tutaj";
			case NAJEMNIK_ORDER_FOCUS: return "Bij moj cel";
			case NAJEMNIK_ORDER_FREE: return "Walcz sam w poblizu";
			default: return "Za mna";
		}
	}

	// "/najemnicy rozkaz <nr|wszyscy> <za_mna|stoj|bij|sam|nie_podnos|podnos>" - the letter's "Rozkazy", the target
	// board's "Rozkazy" (uitarget.py). Kept per mercenary (player.najemnicy.order_mode, no_loot), summoned or not.
	void OrderNajemnicy(LPCHARACTER ch, const std::string& which, const std::string& whatIn)
	{
		std::string what = whatIn;
		for (size_t i = 0; i < what.size(); ++i)
			what[i] = (char)tolower((unsigned char)what[i]);
		int order = -1, loot = -1;
		if (what == "za_mna" || what == "zamna" || what == "follow" || what == "0")
			order = NAJEMNIK_ORDER_FOLLOW;
		else if (what == "stoj" || what == "hold" || what == "1")
			order = NAJEMNIK_ORDER_HOLD;
		else if (what == "bij" || what == "cel" || what == "focus" || what == "2")
			order = NAJEMNIK_ORDER_FOCUS;
		else if (what == "sam" || what == "walcz" || what == "free" || what == "3")
			order = NAJEMNIK_ORDER_FREE;
		else if (what == "nie_podnos" || what == "lup_nie" || what == "noloot")
			loot = 0;
		else if (what == "podnos" || what == "lup" || what == "loot")
			loot = 1;
		const bool all = which == "wszyscy" || which == "all";
		const int slot = all ? 0 : ParseNajemnicySlot(which);
		if ((order < 0 && loot < 0) || (!all && slot <= 0))
		{
			TellNajemnicy(ch, "Uzycie: /najemnicy rozkaz <nr|wszyscy> <za_mna | stoj | bij | sam | nie_podnos | podnos>.");
			return;
		}
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		int changed = 0;
		std::string names;
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TNajemnikRow& r = rows[i];
			if (!all && r.slot != slot)
				continue;
			if (order >= 0)
				NajemnicyQuery("UPDATE player.najemnicy SET order_mode=%d WHERE merc_pid=%u", order, r.pid);
			else
				NajemnicyQuery("UPDATE player.najemnicy SET no_loot=%d WHERE merc_pid=%u", loot ? 0 : 1, r.pid);
			std::map<DWORD, TNajemnik>::iterator it = s_mapNajemnik.find(r.pid);
			if (it != s_mapNajemnik.end())
			{
				TNajemnik& n = it->second;
				if (order >= 0)
				{
					n.order = (BYTE)order;
					n.holdMap = 0;
					LPCHARACTER sk = CHARACTER_MANAGER::instance().FindByPID(r.pid);
					if (order == NAJEMNIK_ORDER_HOLD && sk && sk->GetMapIndex() == ch->GetMapIndex())
					{
						n.holdMap = sk->GetMapIndex();
						n.holdX = sk->GetX();
						n.holdY = sk->GetY();
					}
					if (sk && order != NAJEMNIK_ORDER_FOLLOW && order != NAJEMNIK_ORDER_FREE)
						sk->SetVictim(NULL);	// a new order drops the old fight; the next tick chooses again
				}
				else
				{
					n.noLoot = loot == 0;
					n.lootVid = 0;
				}
			}
			if (!names.empty())
				names += ", ";
			names += r.name;
			++changed;
		}
		if (changed == 0)
		{
			TellNajemnicy(ch, "Nie masz najemnika na tym miejscu.");
			return;
		}
		if (order >= 0)
			TellNajemnicy(ch, "Rozkaz \"%s\": %s.", GetNajemnikOrderName(order), names.c_str());
		else
			TellNajemnicy(ch, "%s: %s.", loot ? "Podnosza lup" : "Nie podnosza lupu", names.c_str());
		sys_log(0, "NAJEMNICY: order owner=%u which=%s order=%d loot=%d changed=%d", ch->GetPlayerID(), which.c_str(), order,
				loot, changed);
		std::map<DWORD, TNajemnicyOwner>::iterator rec = s_mapNajemnicyOwner.find(ch->GetPlayerID());
		if (rec != s_mapNajemnicyOwner.end())
		{
			rec->second.vidSig.clear();	// the client's "Rozkazy" shows the new order at once
			AnnounceNajemnicyVids(ch, rec->second, get_dword_time());
		}
	}

	void DepositNajemnicy(LPCHARACTER ch, const std::string& amountText)
	{
		long long amount = 0;
		for (size_t i = 0; i < amountText.size(); ++i)
		{
			const char c = amountText[i];
			if (c == '.' || c == ' ' || c == '_')
				continue;
			if (c == 'k' || c == 'K')
			{
				amount *= 1000;
				continue;
			}
			if (c < '0' || c > '9' || amount > 100000000000LL)
			{
				TellNajemnicy(ch, "Podaj kwote cyframi, np. 50000000 albo 50kk.");
				return;
			}
			amount = amount * 10 + (c - '0');
		}
		if (amount <= 0)
		{
			TellNajemnicy(ch, "Podaj kwote wieksza od zera.");
			return;
		}
		if (ch->GetGold() < amount)
		{
			TellNajemnicy(ch, "Nie masz tyle yang (masz %lld).", (long long)ch->GetGold());
			return;
		}
		if (!EnsureNajemnicyTables() || ch->GetExchange() || ch->IsDead())
			return;
		PlayerBotChangeGold(ch, -amount);
		std::unique_ptr<SQLMsg> m(NajemnicyQuery(
				"INSERT INTO player.najemnicy_vault (owner_pid, balance, total_paid, total_deposit, updated_at) "
				"VALUES (%u, %lld, 0, %lld, NOW()) ON DUPLICATE KEY UPDATE balance=balance+%lld, "
				"total_deposit=total_deposit+%lld, updated_at=NOW()", ch->GetPlayerID(), amount, amount, amount, amount));
		if (!NajemnicyOk(m))
		{
			PlayerBotChangeGold(ch, amount);
			TellNajemnicy(ch, "Nie udalo sie wplacic - yang wrocil do ciebie.");
			sys_err("NAJEMNICY: deposit failed owner=%u amount=%lld (given back)", ch->GetPlayerID(), amount);
			return;
		}
		s_llNajemnicyDeposited += amount;
		LogManager::instance().CharLog(ch, amount, "NAJEMNICY_WPLATA", "");
		{
			std::map<DWORD, TNajemnicyOwner>::iterator o = s_mapNajemnicyOwner.find(ch->GetPlayerID());
			if (o != s_mapNajemnicyOwner.end())
				o->second.warned = false;
		}
		sys_log(0, "NAJEMNICY: deposit owner=%u name=%s amount=%lld", ch->GetPlayerID(), ch->GetName(), amount);
		TellNajemnicy(ch, "Wplacono %lld yang.", amount);
		ShowNajemnicyVault(ch);
	}

	// The owner's summoned mercenary of a slot in this world, or a word why not.
	LPCHARACTER GetNajemnikHere(LPCHARACTER ch, const std::string& slotText, TNajemnik** out)
	{
		TNajemnik* n = FindNajemnikSummoned(ch->GetPlayerID(), ParseNajemnicySlot(slotText));
		LPCHARACTER sk = n && n->phase == NAJEMNIK_READY ? CHARACTER_MANAGER::instance().FindByPID(n->pid) : NULL;
		if (!sk || !sk->IsItemLoaded())
		{
			TellNajemnicy(ch, "Najpierw wezwij tego najemnika.");
			return NULL;
		}
		if (out)
			*out = n;
		return sk;
	}

	// Stage 1's equipment: one piece from the owner's bag onto the mercenary (worn when it can be).
	void GiveNajemnikItem(LPCHARACTER ch, const std::string& slotText, const std::string& cellText)
	{
		LPCHARACTER sk = GetNajemnikHere(ch, slotText, NULL);
		if (!sk)
			return;
		const int cell = ParseNajemnicyInt(cellText, INVENTORY_MAX_NUM) - 1;
		LPITEM item = cell >= 0 && cell < INVENTORY_MAX_NUM ? ch->GetInventoryItem(cell) : NULL;
		if (!item || item->GetCell() != cell || item->GetWindow() != INVENTORY || item->IsEquipped())
		{
			TellNajemnicy(ch, "Na tym polu ekwipunku nic nie ma (pola licz od 1, rzedami po 5).");
			return;
		}
		const std::string refusal = GetPlayerBotSidekickHandOverRefusal(item);
		if (!refusal.empty())
		{
			TellNajemnicy(ch, "%s", refusal.c_str());
			return;
		}
		const int to = sk->GetEmptyInventory(item->GetSize());
		if (to < 0)
		{
			TellNajemnicy(ch, "Najemnik nie ma miejsca w plecaku.");
			return;
		}
		const std::string pieceName = item->GetName() ? item->GetName() : "";
		HandPlayerBotSidekickItemOver(ch, sk, item, to);
		LogManager::instance().ItemLog(ch, item, "NAJEMNIK_DAJ", sk->GetName());
		bool worn = false;
		if (item->IsEquipable() || item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR)
		{
			PlayerBotResetEquipPulse(sk);
			worn = PlayerBotEquipItem(sk, item, -1) && item->IsEquipped();
		}
		if (worn)
		{
			sk->ComputePoints();
			sk->PointsPacket();
		}
		sys_log(0, "NAJEMNICY: given pid=%u owner=%u item=%u vnum=%u worn=%d", sk->GetPlayerID(), ch->GetPlayerID(),
				item->GetID(), item->GetVnum(), worn ? 1 : 0);
		if (worn)
			TellNajemnicy(ch, "%s nosi teraz: %s.", sk->GetName(), pieceName.c_str());
		else
			TellNajemnicy(ch, "%s ma w plecaku: %s (nie moze tego zalozyc).", sk->GetName(), pieceName.c_str());
	}

	// Everything it carries and wears (and its yang) back into the owner's bag, as far as the bag takes.
	// Returns how many pieces stayed with it.
	int TakeAllFromNajemnik(LPCHARACTER ch, LPCHARACTER sk, int& moved)
	{
		moved = 0;
		int left = 0;
		for (int wear = 0; wear < WEAR_MAX_NUM; ++wear)
		{
			LPITEM worn = sk->GetWear(wear);
			if (!worn || worn->IsDragonSoul() || IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE))
				continue;
			if (sk->GetEmptyInventory(worn->GetSize()) < 0 || !sk->UnequipItem(worn) || worn->IsEquipped())
				++left;
		}
		// MT2009_PLUS_NAJEMNICY_V2: its bag and whatever lies in the extra inventory's storages (from before
		// SweepNajemnikStorage) - everything it holds is its owner's.
		std::vector<LPITEM> all;
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = sk->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && !item->IsEquipped())
				all.push_back(item);
		}
		{
			std::vector<LPITEM> stored;
			CollectPlayerBotEkwStored(sk, stored);
			all.insert(all.end(), stored.begin(), stored.end());
		}
		for (size_t i = 0; i < all.size(); ++i)
		{
			LPITEM item = all[i];
			if (!GetPlayerBotSidekickHandOverRefusal(item).empty())
			{
				++left;
				continue;
			}
			const int to = ch->GetEmptyInventory(item->GetSize());
			if (to < 0)
			{
				++left;
				continue;
			}
			HandPlayerBotSidekickItemOver(sk, ch, item, to);
			LogManager::instance().ItemLog(ch, item, "NAJEMNIK_ZABIERZ", sk->GetName());
			++moved;
		}
		const long long gold = sk->GetGold();
		if (gold > 0 && ch->GetGold() + gold <= GOLD_MAX)
		{
			PlayerBotChangeGold(sk, -gold);
			PlayerBotChangeGold(ch, gold);
			sys_log(0, "NAJEMNICY: yang taken pid=%u owner=%u gold=%lld", sk->GetPlayerID(), ch->GetPlayerID(), gold);
		}
		sk->ComputePoints();
		sk->PointsPacket();
		sk->Save();
		return left;
	}

	void TakeNajemnikItems(LPCHARACTER ch, const std::string& slotText)
	{
		LPCHARACTER sk = GetNajemnikHere(ch, slotText, NULL);
		if (!sk)
			return;
		int moved = 0;
		const int left = TakeAllFromNajemnik(ch, sk, moved);
		sys_log(0, "NAJEMNICY: take all pid=%u owner=%u moved=%d left=%d", sk->GetPlayerID(), ch->GetPlayerID(), moved, left);
		if (left > 0)
			TellNajemnicy(ch, "Zabrano %d przedmiotow, %d zostalo u %s (brak miejsca u ciebie albo nie da sie ich przekazac).",
					moved, left, sk->GetName());
		else
			TellNajemnicy(ch, "Zabrano wszystko od %s (%d przedmiotow).", sk->GetName(), moved);
	}

	// ------------------------------------------------------------------ MT2009_PLUS_NAJEMNICY_V2: the equipment window
	//
	// The Towarzysz's bag window (client root/uisidekickinventory.py: the equipment picture, the four bag pages, the
	// costumes panel), opened for one mercenary: "/najemnicy okno <nr>" (the letter) answers NajemnikEqOpen, and the
	// target board's "Ekwipunek" on a summoned mercenary opens it straight (NajemnikVids tells the owner's client which
	// characters are its mercenaries). The window's orders are the Towarzysz's own, after "/najemnicy eq <nr>":
	//   (nothing) / 1          what changed / the whole picture: NajemnikEqWho, then the Towarzysz's protocol
	//                          (SidekickEqBegin, SidekickEqItem, SidekickEqEmpty, SidekickEqEnd - no Alchemy, no marks)
	//   daj <your cell> <to>   from the owner's bag into its bag (<to> a cell or -1) or onto a slot (1000 + WEAR_*)
	//   wez <from> <your cell> from its bag or a slot into the owner's bag (-1 anywhere)
	//   ruch <from> <to>       inside its gear: a bag cell to another, onto a slot (put on), off a slot (taken off)
	//   wszystko               everything it carries and wears, and its yang, back to the owner (TakeAllFromNajemnik)
	//   yang wez <amount>      its yang (kills' yang lands in its purse) to the owner; it is never given any
	// each answered by SidekickEqResult. Only the owner, only a summoned mercenary in the world, and only within
	// NAJEMNICY_EQ_RANGE of it on its map (the answer "SidekickEqNone 1 3" otherwise). What it wears and carries stays its
	// owner's: it sells, drops, trades and stores nothing, loses nothing at its death, and nothing of the AI touches it.
	// The rules of wearing are the engine's for any character (class, sex, level, stats, a unique's group), checked
	// before a piece leaves the owner's bag (GetPlayerBotSidekickWearRefusal).

	// The Towarzysz's answers in the mercenary's words.
	std::string NajemnikWords(const std::string& in)
	{
		static const char* const pairs[][2] = {
			{ "Towarzyszem", "Najemnikiem" }, { "towarzyszem", "najemnikiem" },
			{ "Towarzysz", "Najemnik" }, { "towarzysz", "najemnik" },
			{ "torbie", "plecaku" }, { "torby", "plecaka" }, { "torbe", "plecak" },
		};
		std::string out = in;
		for (size_t p = 0; p < sizeof(pairs) / sizeof(pairs[0]); ++p)
		{
			const std::string from = pairs[p][0];
			const std::string to = pairs[p][1];
			for (size_t at = out.find(from); at != std::string::npos; at = out.find(from, at + to.size()))
				out.replace(at, from.size(), to);
		}
		return out;
	}

	void AnswerNajemnikEq(LPCHARACTER owner, int code, const std::string& text)
	{
		SendPlayerBotSidekickCommand(owner, "SidekickEqResult %d %s", code,
				EncodePlayerBotSidekickText(NajemnikWords(text).c_str(), 150).c_str());
	}

	// The owner's summoned mercenary of a slot, in reach of the window; reason: 1 not summoned (or not in the world
	// yet), 2 the module off, 3 too far (another map or past NAJEMNICY_EQ_RANGE).
	LPCHARACTER FindNajemnikForWindow(LPCHARACTER owner, int slot, TNajemnik** out, int& reason)
	{
		reason = 1;
		if (IsNajemnicyOff())
		{
			reason = 2;
			return NULL;
		}
		TNajemnik* n = slot > 0 ? FindNajemnikSummoned(owner->GetPlayerID(), slot) : NULL;
		LPCHARACTER sk = n && n->phase == NAJEMNIK_READY ? CHARACTER_MANAGER::instance().FindByPID(n->pid) : NULL;
		if (!sk || !sk->IsItemLoaded() || !n->setupDone)
			return NULL;
		if (sk->GetMapIndex() != owner->GetMapIndex() ||
				DISTANCE_APPROX(sk->GetX() - owner->GetX(), sk->GetY() - owner->GetY()) > NAJEMNICY_EQ_RANGE)
		{
			reason = 3;
			return NULL;
		}
		if (out)
			*out = n;
		return sk;
	}

	// Its bag and worn gear to the owner's window: the whole picture, or only what changed (nothing at all when
	// nothing did) - SendPlayerBotSidekickEq's way, on the mercenary's own runtime.
	void SendNajemnikEq(LPCHARACTER owner, LPCHARACTER sk, TNajemnik& n, bool full)
	{
		TPlayerBotSidekickRuntime& rt = n.rt;
		std::map<int, TPlayerBotSidekickEqEntry> now;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = sk->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell)
				continue;
			TPlayerBotSidekickEqEntry& e = now[(int)cell];
			e.item = item;
			e.flags = 0;
			e.hash = HashPlayerBotSidekickEqItem(item, 0);
		}
		for (int wear = 0; wear < WEAR_MAX_NUM; ++wear)
		{
			LPITEM item = sk->GetWear(wear);
			if (!item)
				continue;
			TPlayerBotSidekickEqEntry& e = now[PLAYERBOT_SIDEKICK_EQ_WEAR_BASE + wear];
			e.item = item;
			e.flags = 0;
			e.hash = HashPlayerBotSidekickEqItem(item, 0);
		}
		const long long gold = (long long)sk->GetGold();
		const bool begin = full || rt.dwEqGen == 0;
		if (!begin)
		{
			bool changed = gold != rt.llEqGoldSent || now.size() != rt.mapEqSent.size();
			for (std::map<int, TPlayerBotSidekickEqEntry>::const_iterator e = now.begin(); !changed && e != now.end(); ++e)
			{
				std::map<int, DWORD>::const_iterator sent = rt.mapEqSent.find(e->first);
				changed = sent == rt.mapEqSent.end() || sent->second != e->second.hash;
			}
			if (!changed)
				return;
		}
		++rt.dwEqGen;
		if (begin)
		{
			rt.mapEqSent.clear();
			// Who the picture is of: the slot, the name (hex), the level and the race - the window's title.
			SendPlayerBotSidekickCommand(owner, "NajemnikEqWho %u %s %d %u", (unsigned int)n.slot,
					EncodePlayerBotSidekickText(sk->GetName(), 24).c_str(), (int)sk->GetLevel(), (unsigned int)n.race);
			SendPlayerBotSidekickCommand(owner, "SidekickEqBegin %d %u %d %d %d %d", PLAYERBOT_SIDEKICK_EQ_PROTOCOL,
					rt.dwEqGen, PLAYERBOT_BAG_CELLS, PLAYERBOT_SIDEKICK_EQ_PAGE_CELLS, 0, 0);
		}
		size_t lines = 0;
		for (std::map<int, DWORD>::iterator sent = rt.mapEqSent.begin(); sent != rt.mapEqSent.end();)
		{
			if (now.find(sent->first) != now.end())
			{
				++sent;
				continue;
			}
			if (lines >= PLAYERBOT_SIDEKICK_EQ_MAX_LINES)
				break;
			SendPlayerBotSidekickCommand(owner, "SidekickEqEmpty %u %d", rt.dwEqGen, sent->first);
			++lines;
			rt.mapEqSent.erase(sent++);
		}
		for (std::map<int, TPlayerBotSidekickEqEntry>::const_iterator e = now.begin(); e != now.end(); ++e)
		{
			std::map<int, DWORD>::iterator sent = rt.mapEqSent.find(e->first);
			if (sent != rt.mapEqSent.end() && sent->second == e->second.hash)
				continue;
			if (lines >= PLAYERBOT_SIDEKICK_EQ_MAX_LINES)
				break;
			SendPlayerBotSidekickEqItem(owner, rt.dwEqGen, e->first, e->second.item, 0);
			++lines;
			rt.mapEqSent[e->first] = e->second.hash;
		}
		SendPlayerBotSidekickCommand(owner, "SidekickEqEnd %u %lld", rt.dwEqGen, gold);
		rt.llEqGoldSent = gold;
	}

	// A piece of its bag put on for the owner, on the slot asked for (-1: where it goes). A blow still landing: worn at
	// the first moment the engine lets it (RetryNajemnikPendingWear).
	int EquipNajemnikPiece(LPCHARACTER owner, LPCHARACTER sk, TPlayerBotAIState& state, TNajemnik& n, LPITEM item,
			int wantWear, std::string& answer)
	{
		if (item->IsEquipped())
		{
			answer = "Najemnik juz to nosi.";
			return 0;
		}
		const int wear = item->FindEquipCell(sk);
		const bool unique = wear == WEAR_UNIQUE1 || wear == WEAR_UNIQUE2;
		const bool uniqueSlot = wantWear == WEAR_UNIQUE1 || wantWear == WEAR_UNIQUE2;
		if (wantWear >= 0 && wear >= 0 && wear != wantWear && !(unique && uniqueSlot))
		{
			answer = "To nie pasuje w to miejsce.";
			return 2;
		}
		const int slot = unique && uniqueSlot ? wantWear : wear;
		LPITEM old = slot >= 0 && slot < WEAR_MAX_NUM ? sk->GetWear(slot) : NULL;
		answer = GetPlayerBotSidekickWearRefusal(sk, item, old);
		if (!answer.empty())
			return 2;
		if (old && IS_SET(old->GetFlag(), ITEM_FLAG_IRREMOVABLE))
		{
			answer = "Tego, co tam nosi, nie da sie zdjac.";
			return 2;
		}
		if (IsPlayerBotSidekickHairstyle(old) && IsPlayerBotSidekickHairstyle(item))
		{
			answer = PLAYERBOT_SIDEKICK_NEEDS_BLEACH_TEXT;
			return 2;
		}
		if (IsPlayerBotGearFrozen(sk))
		{
			answer = "Najemnik jest teraz przemieniony - zmiana sprzetu poczeka do konca przemiany.";
			return 2;
		}
		const bool blowFresh = IsPlayerBotEquipWindowShut(sk, state);
		bool worn = false;
		if (!blowFresh && !item->isLocked() && !item->IsExchanging())
		{
			if (unique && old && old->IsEquipped() && sk->GetEmptyInventory(old->GetSize()) >= 0)
				sk->UnequipItem(old);
			worn = PlayerBotEquipItem(sk, item) && item->IsEquipped();
			if (!worn && old && old->IsEquipped() && sk->GetEmptyInventory(old->GetSize()) >= 0 &&
					sk->UnequipItem(old) && !old->IsEquipped())
				worn = PlayerBotEquipItem(sk, item) && item->IsEquipped();
		}
		if (worn)
		{
			LogManager::instance().ItemLog(sk, item, "NAJEMNIK_ZALOZ", owner->GetName());
			FlushPlayerBotItemRow(item);
			FlushPlayerBotItemRow(old);
			sk->ComputePoints();
			sk->PointsPacket();
			n.pendingWearItem = 0;
			answer = "Zalozone.";
			return 0;
		}
		if (old && sk->GetEmptyInventory(old->GetSize()) < 0)
		{
			answer = "Najemnik nie ma miejsca w plecaku na to, co by zdjal - zabierz najpierw cos z jego plecaka.";
			return 2;
		}
		if (blowFresh)
		{
			n.pendingWearItem = item->GetID();
			n.pendingWearSlot = slot;
			n.pendingWearUntil = get_dword_time() + NAJEMNICY_PENDING_WEAR_MS;
			answer = "Zalozy to, jak tylko skonczy cios.";
			return 0;
		}
		answer = "Nie da sie tego teraz zalozyc - sprobuj za chwile.";
		return 2;
	}

	// A worn piece off into its bag (a cell, or the first that fits).
	int UnequipNajemnikPiece(LPCHARACTER owner, LPCHARACTER sk, int wear, int toCell, std::string& answer)
	{
		LPITEM worn = sk->GetWear(wear);
		if (!worn)
		{
			answer = "Tam nic nie ma.";
			return 3;
		}
		if (IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE) || worn->isLocked())
		{
			answer = "Tego nie da sie zdjac.";
			return 2;
		}
		if (IsPlayerBotGearFrozen(sk))
		{
			answer = "Najemnik jest teraz przemieniony - zmiana sprzetu poczeka do konca przemiany.";
			return 2;
		}
		StopPlayerBotSidekickMountFor(sk, worn);
		bool done = false;
		if (toCell >= 0)
			done = sk->MoveItem(TItemPos(INVENTORY, INVENTORY_MAX_NUM + wear), TItemPos(INVENTORY, toCell),
					worn->GetCount()) && !worn->IsEquipped();
		else
			done = sk->GetEmptyInventory(worn->GetSize()) >= 0 && sk->UnequipItem(worn) && !worn->IsEquipped();
		if (!done)
		{
			answer = sk->GetEmptyInventory(worn->GetSize()) < 0 ? "Najemnik nie ma miejsca w plecaku." :
					IsPlayerBotSidekickHairstyle(worn) ? PLAYERBOT_SIDEKICK_NEEDS_BLEACH_TEXT :
					"Nie da sie tego teraz zdjac - sprobuj za chwile.";
			return 2;
		}
		LogManager::instance().ItemLog(sk, worn, "NAJEMNIK_ZDEJMIJ", owner->GetName());
		FlushPlayerBotItemRow(worn);
		sk->ComputePoints();
		sk->PointsPacket();
		answer = "Zdjete do plecaka najemnika.";
		return 0;
	}

	// From the owner's bag to the mercenary: onto a cell, a stack or a slot (put on). What it could never wear stays
	// with the owner.
	int GiveNajemnikPiece(LPCHARACTER owner, LPCHARACTER sk, TPlayerBotAIState& state, TNajemnik& n, int fromCell, int to,
			std::string& answer)
	{
		LPITEM item = fromCell >= 0 && fromCell < INVENTORY_MAX_NUM ? owner->GetInventoryItem(fromCell) : NULL;
		if (!item || item->GetCell() != fromCell || item->GetWindow() != INVENTORY || item->IsEquipped())
		{
			answer = "Nie ma tego w twoim ekwipunku.";
			return 3;
		}
		answer = GetPlayerBotSidekickHandOverRefusal(item);
		if (!answer.empty())
			return 2;
		const bool toWear = IsPlayerBotSidekickEqWearPos(to);
		const int wantWear = toWear ? to - PLAYERBOT_SIDEKICK_EQ_WEAR_BASE : -1;
		const bool hairTool = wantWear == WEAR_COSTUME_HAIR && IsPlayerBotSidekickHairTool(item);
		if (toWear && !hairTool)
		{
			const int wear = item->FindEquipCell(sk);
			const bool unique = (wear == WEAR_UNIQUE1 || wear == WEAR_UNIQUE2) &&
					(wantWear == WEAR_UNIQUE1 || wantWear == WEAR_UNIQUE2);
			if (wear >= 0 && wear != wantWear && !unique)
			{
				answer = "To nie pasuje w to miejsce.";
				return 2;
			}
			answer = GetPlayerBotSidekickWearRefusal(sk, item, sk->GetWear(wantWear));
			if (!answer.empty())
				return 2;
		}
		const std::string pieceName = item->GetName() ? item->GetName() : "";
		LPITEM stack = IsPlayerBotSidekickEqBagPos(to) ? sk->GetInventoryItem(to) : NULL;
		if (stack && stack->GetCell() == to)
		{
			const DWORD count = (DWORD)item->GetCount();
			const int poured = PourPlayerBotSidekickStack(owner, item, stack, "NAJEMNIK_DAJ");
			if (poured > 0)
			{
				LogManager::instance().ItemLog(owner, stack, "NAJEMNIK_DAJ", sk->GetName());
				char text[160];
				snprintf(text, sizeof(text), "Dolozone do stosu najemnika: %d z %u.", poured, (unsigned int)count);
				answer = text;
				return 0;
			}
			if (poured == 0)
			{
				answer = "Ten stos jest juz pelny.";
				return 2;
			}
		}
		const int cell = FindPlayerBotSidekickHandOverCell(sk, item, IsPlayerBotSidekickEqBagPos(to) ? to : -1);
		if (cell < 0)
		{
			answer = IsPlayerBotSidekickEqBagPos(to) ? "Tam nie ma miejsca." : "Najemnik nie ma miejsca w plecaku.";
			return 2;
		}
		HandPlayerBotSidekickItemOver(owner, sk, item, cell);
		LogManager::instance().ItemLog(owner, item, "NAJEMNIK_DAJ", sk->GetName());
		sys_log(0, "NAJEMNICY: eq given pid=%u owner=%u item=%u vnum=%u cell=%d to=%d", sk->GetPlayerID(),
				owner->GetPlayerID(), item->GetID(), item->GetVnum(), cell, to);
		if (hairTool)
		{
			std::string used;
			const int code = UsePlayerBotSidekickHairTool(owner, sk, n.rt, item, used);
			answer = std::string("Dane: ") + pieceName + ". " + used;
			return code;
		}
		if (toWear)
		{
			std::string worn;
			const int code = EquipNajemnikPiece(owner, sk, state, n, item, wantWear, worn);
			answer = std::string("Dane: ") + pieceName + ". " + worn;
			return code;
		}
		answer = std::string("Dane najemnikowi: ") + pieceName + ".";
		return 0;
	}

	// From the mercenary (its bag or a slot - taken off first) into the owner's bag.
	int TakeNajemnikPiece(LPCHARACTER owner, LPCHARACTER sk, int from, int toCell, std::string& answer)
	{
		const bool fromWear = IsPlayerBotSidekickEqWearPos(from);
		LPITEM item = fromWear ? sk->GetWear(from - PLAYERBOT_SIDEKICK_EQ_WEAR_BASE)
				: (IsPlayerBotSidekickEqBagPos(from) ? sk->GetInventoryItem(from) : NULL);
		if (!item || (!fromWear && item->GetCell() != from))
		{
			answer = "Tam nic nie ma.";
			return 3;
		}
		answer = GetPlayerBotSidekickHandOverRefusal(item);
		if (!answer.empty())
			return 2;
		if (fromWear && IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))
		{
			answer = "Tego nie da sie zdjac.";
			return 2;
		}
		if (fromWear && IsPlayerBotGearFrozen(sk))
		{
			answer = "Najemnik jest teraz przemieniony - zmiana sprzetu poczeka do konca przemiany.";
			return 2;
		}
		const std::string pieceName = item->GetName() ? item->GetName() : "";
		const bool ownerCell = toCell >= 0 && toCell < INVENTORY_MAX_NUM;
		LPITEM stack = ownerCell ? owner->GetInventoryItem(toCell) : NULL;
		if (!fromWear && stack && stack->GetCell() == toCell)
		{
			const DWORD count = (DWORD)item->GetCount();
			const int poured = PourPlayerBotSidekickStack(sk, item, stack, "NAJEMNIK_ZABIERZ");
			if (poured > 0)
			{
				LogManager::instance().ItemLog(owner, stack, "NAJEMNIK_ZABIERZ", sk->GetName());
				char text[160];
				snprintf(text, sizeof(text), "Dolozone do twojego stosu: %d z %u.", poured, (unsigned int)count);
				answer = text;
				return 0;
			}
			if (poured == 0)
			{
				answer = "Twoj stos jest juz pelny.";
				return 2;
			}
		}
		const int cell = FindPlayerBotSidekickHandOverCell(owner, item, ownerCell ? toCell : -1);
		if (cell < 0)
		{
			answer = ownerCell ? "Tam nie ma miejsca." : "Nie masz miejsca w ekwipunku.";
			return 2;
		}
		if (fromWear)
			StopPlayerBotSidekickMountFor(sk, item);
		if (fromWear && (sk->GetEmptyInventory(item->GetSize()) < 0 || !sk->UnequipItem(item) || item->IsEquipped()))
		{
			answer = sk->GetEmptyInventory(item->GetSize()) < 0 ?
					"Najemnik nie ma miejsca w plecaku, zeby to zdjac - zabierz najpierw cos z jego plecaka." :
					IsPlayerBotSidekickHairstyle(item) ? PLAYERBOT_SIDEKICK_NEEDS_BLEACH_TEXT :
					"Nie da sie tego teraz zdjac - sprobuj za chwile.";
			return 2;
		}
		const DWORD id = item->GetID();
		HandPlayerBotSidekickItemOver(sk, owner, item, cell);
		LogManager::instance().ItemLog(owner, item, "NAJEMNIK_ZABIERZ", sk->GetName());
		if (fromWear)
		{
			sk->ComputePoints();
			sk->PointsPacket();
		}
		sys_log(0, "NAJEMNICY: eq taken pid=%u owner=%u item=%u vnum=%u worn=%d cell=%d", sk->GetPlayerID(),
				owner->GetPlayerID(), id, item->GetVnum(), fromWear ? 1 : 0, cell);
		answer = std::string("Zabrane od najemnika: ") + pieceName + ".";
		return 0;
	}

	// "/najemnicy eq <nr> [op a b]" - the window's poll and orders.
	void HandleNajemnikEqCommand(LPCHARACTER owner, const std::string& slotText, const std::string& op,
			const std::string& a, const std::string& b)
	{
		const int slot = ParseNajemnicySlot(slotText);
		TNajemnik* n = NULL;
		int reason = 1;
		LPCHARACTER sk = FindNajemnikForWindow(owner, slot, &n, reason);
		const bool poll = op.empty() || op == "1";
		if (!sk || !n)
		{
			if (!poll)
				AnswerNajemnikEq(owner, 1, reason == 3 ? "Podejdz blizej do najemnika (do 50 m)." : reason == 2 ?
						"Najemnicy sa teraz wylaczeni na tym serwerze." : "Ten najemnik nie jest teraz wezwany.");
			SendPlayerBotSidekickCommand(owner, "SidekickEqNone %d %d", PLAYERBOT_SIDEKICK_EQ_PROTOCOL, reason);
			return;
		}
		if (poll)
		{
			SendNajemnikEq(owner, sk, *n, !op.empty());
			return;
		}
		TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(n->pid);
		if (st == s_mapPlayerBotAIStates.end())
		{
			AnswerNajemnikEq(owner, 1, "Ten najemnik nie jest teraz wezwany.");
			return;
		}
		TPlayerBotAIState& state = st->second;
		const int from = ParsePlayerBotSidekickEqPos(a.c_str());
		const int to = ParsePlayerBotSidekickEqPos(b.c_str());
		std::string answer;
		int code = 9;
		const bool ownerBag = op == "daj" || op == "wez" || op == "wszystko" || op == "yang";
		if (sk->IsDead())
		{
			answer = "Najemnik lezy - poczekaj, az wstanie.";
			code = 2;
		}
		else if (!sk->CanHandleItem())
		{
			answer = "Najemnik jest teraz zajety - sprobuj za chwile.";
			code = 2;
		}
		else if (ownerBag && !owner->CanHandleItem())
		{
			answer = "Zamknij najpierw handel, sklep albo magazyn.";
			code = 2;
		}
		else if (op == "wszystko")
		{
			int moved = 0;
			const int left = TakeAllFromNajemnik(owner, sk, moved);
			char text[160];
			if (left > 0)
				snprintf(text, sizeof(text), "Zabrano %d przedmiotow, %d zostalo (brak miejsca u ciebie albo nie da sie ich "
						"przekazac).", moved, left);
			else
				snprintf(text, sizeof(text), "Zabrano wszystko (%d przedmiotow).", moved);
			answer = text;
			code = left > 0 ? 2 : 0;
			n->pendingWearItem = 0;
			sys_log(0, "NAJEMNICY: eq take all pid=%u owner=%u moved=%d left=%d", sk->GetPlayerID(), owner->GetPlayerID(),
					moved, left);
		}
		else if (op == "yang")
		{
			if (a == "wez")
				code = MovePlayerBotSidekickYang(owner, sk, false, b.c_str(), answer);
			else
			{
				answer = "Najemnik nie potrzebuje yang - niczego nie kupuje.";
				code = 2;
			}
		}
		else if (op == "odepnij")
		{
			answer = "Najemnik sam niczego nie zaklada ani nie zdejmuje - nie ma czego odpinac.";
			code = 0;
		}
		else if (IsPlayerBotSidekickEqDsPos(from) || IsPlayerBotSidekickEqDsPos(to) || to == PLAYERBOT_SIDEKICK_EQ_DS_AUTO)
		{
			answer = "Kamieni smoka nie da sie tu przekazac.";
			code = 2;
		}
		else if (op == "daj")
		{
			if (from < 0 || from == INT_MIN || to == INT_MIN)
				answer = "Zle miejsce.";
			else
				code = GiveNajemnikPiece(owner, sk, state, *n, from, to, answer);
		}
		else if (op == "wez")
		{
			if (from == INT_MIN || from == -1 || !(to == -1 || IsPlayerBotSidekickEqBagPos(to)))
				answer = "Zle miejsce.";
			else
				code = TakeNajemnikPiece(owner, sk, from, to, answer);
		}
		else if (op == "ruch")
		{
			if (from == INT_MIN || to == INT_MIN)
				answer = "Zle miejsce.";
			else if (IsPlayerBotSidekickEqBagPos(from) && IsPlayerBotSidekickEqBagPos(to))
				code = MovePlayerBotSidekickBagItem(sk, from, to, answer);
			else if (IsPlayerBotSidekickEqBagPos(from) && (to == -1 || IsPlayerBotSidekickEqWearPos(to)))
			{
				LPITEM item = sk->GetInventoryItem(from);
				if (!item || item->GetCell() != from)
				{
					answer = "Tam nic nie ma.";
					code = 3;
				}
				else if (IsPlayerBotSidekickHairTool(item) &&
						(to == -1 || to == PLAYERBOT_SIDEKICK_EQ_WEAR_BASE + WEAR_COSTUME_HAIR))
					code = UsePlayerBotSidekickHairTool(owner, sk, n->rt, item, answer);
				else if (to == -1 && !item->IsEquipable())
				{
					answer = "Tego nie da sie zalozyc. Najemnik sam uzywa mikstur i wzmocnien ze swojego plecaka.";
					code = 2;
				}
				else
					code = EquipNajemnikPiece(owner, sk, state, *n, item, to == -1 ? -1 : to - PLAYERBOT_SIDEKICK_EQ_WEAR_BASE,
							answer);
			}
			else if (IsPlayerBotSidekickEqWearPos(from) && (to == -1 || IsPlayerBotSidekickEqBagPos(to)))
				code = UnequipNajemnikPiece(owner, sk, from - PLAYERBOT_SIDEKICK_EQ_WEAR_BASE, to, answer);
			else
				answer = "Przeciagnij to do plecaka najemnika.";
		}
		else
			answer = "Nieznane polecenie okna.";
		sys_log(0, "NAJEMNICY: eq %s owner=%u pid=%u from=%s to=%s code=%d", op.c_str(), owner->GetPlayerID(),
				sk->GetPlayerID(), a.c_str(), b.c_str(), code);
		AnswerNajemnikEq(owner, code, answer);
		SendNajemnikEq(owner, sk, *n, false);
	}

	// "/najemnicy okno <nr>" (the letter): the owner's client opens the window for that mercenary.
	void OpenNajemnikWindow(LPCHARACTER owner, const std::string& slotText)
	{
		const int slot = ParseNajemnicySlot(slotText);
		TNajemnik* n = NULL;
		int reason = 1;
		LPCHARACTER sk = FindNajemnikForWindow(owner, slot, &n, reason);
		if (!sk || !n)
		{
			TellNajemnicy(owner, "%s", reason == 3 ? "Podejdz blizej do najemnika (do 50 m), zeby otworzyc jego ekwipunek." :
					reason == 2 ? "Najemnicy sa teraz wylaczeni na tym serwerze." :
					"Najpierw wezwij tego najemnika - ekwipunek otwiera sie, gdy jest przy tobie.");
			return;
		}
		SendPlayerBotSidekickCommand(owner, "NajemnikEqOpen %u %s", (unsigned int)n->slot,
				EncodePlayerBotSidekickText(sk->GetName(), 24).c_str());
	}

	// The owner's client is told which characters are its mercenaries ("NajemnikVids <slot>:<vid>:<hex name>,...", "-"
	// for none): the target board's "Ekwipunek" button. At every change and every NAJEMNICY_VID_RESEND_MS (a warp makes
	// the client anew).
	void AnnounceNajemnicyVids(LPCHARACTER owner, TNajemnicyOwner& rec, DWORD dwNow)
	{
		std::string sig;
		for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
		{
			if (it->second.ownerPid != owner->GetPlayerID() || it->second.phase != NAJEMNIK_READY || it->second.dismiss)
				continue;
			LPCHARACTER sk = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!sk)
				continue;
			// MT2009_PLUS_NAJEMNICY_V3: and its order and loot switch (the target board's "Rozkazy" shows them).
			char part[160];
			snprintf(part, sizeof(part), "%s%u:%u:%s:%u:%d", sig.empty() ? "" : ",", (unsigned int)it->second.slot,
					(unsigned int)(DWORD)sk->GetVID(), EncodePlayerBotSidekickText(sk->GetName(), 24).c_str(),
					(unsigned int)it->second.order, it->second.noLoot ? 0 : 1);
			sig += part;
		}
		if (sig.empty())
			sig = "-";
		if (sig == rec.vidSig && (int)(dwNow - rec.nextVidSend) < 0)
			return;
		rec.vidSig = sig;
		rec.nextVidSend = dwNow + NAJEMNICY_VID_RESEND_MS;
		SendPlayerBotSidekickCommand(owner, "NajemnikVids %s", sig.c_str());
	}

	void GuildNajemnik(LPCHARACTER ch, const std::string& slotText, bool join)
	{
		LPCHARACTER sk = GetNajemnikHere(ch, slotText, NULL);
		if (!sk)
			return;
		CGuild* g = ch->GetGuild();
		if (!join)
		{
			CGuild* mine = sk->GetGuild();
			if (!mine)
			{
				TellNajemnicy(ch, "%s nie jest w gildii.", sk->GetName());
				return;
			}
			mine->RequestRemoveMember(sk->GetPlayerID());
			TellNajemnicy(ch, "%s wychodzi z gildii %s.", sk->GetName(), mine->GetName());
			sys_log(0, "NAJEMNICY: left the guild pid=%u owner=%u guild=%u", sk->GetPlayerID(), ch->GetPlayerID(), mine->GetID());
			return;
		}
		if (!g)
		{
			TellNajemnicy(ch, "Nie jestes w gildii.");
			return;
		}
		if (sk->GetGuild() == g)
		{
			TellNajemnicy(ch, "%s juz jest w twojej gildii.", sk->GetName());
			return;
		}
		if (sk->GetGuild())
			sk->GetGuild()->RequestRemoveMember(sk->GetPlayerID());
		if (g->GetMemberCount() >= g->GetMaxMemberCount())
		{
			TellNajemnicy(ch, "W gildii nie ma wolnego miejsca.");
			return;
		}
		g->RequestAddMember(sk);
		TellNajemnicy(ch, "%s dolacza do gildii %s.", sk->GetName(), g->GetName());
		sys_log(0, "NAJEMNICY: joined the guild pid=%u owner=%u guild=%u", sk->GetPlayerID(), ch->GetPlayerID(), g->GetID());
	}

	void RetireNajemnik(LPCHARACTER ch, const std::string& slotText, const std::string& confirm)
	{
		const std::vector<TNajemnikRow> rows = LoadNajemnicyOf(ch->GetPlayerID());
		const TNajemnikRow* r = FindNajemnikRowBySlot(rows, ParseNajemnicySlot(slotText));
		if (!r)
		{
			TellNajemnicy(ch, "Nie masz najemnika na tym miejscu.");
			return;
		}
		if (confirm != "tak")
		{
			TellNajemnicy(ch, "Na pewno? Wpisz: /najemnicy zwolnij %u tak", (unsigned int)r->slot);
			return;
		}
		// Summoned: everything comes back first; offline: it must carry nothing.
		TNajemnik* n = FindNajemnikSummoned(ch->GetPlayerID(), r->slot);
		LPCHARACTER sk = n && n->phase == NAJEMNIK_READY ? CHARACTER_MANAGER::instance().FindByPID(n->pid) : NULL;
		if (sk && sk->IsItemLoaded())
		{
			int moved = 0;
			if (TakeAllFromNajemnik(ch, sk, moved) > 0)
			{
				TellNajemnicy(ch, "%s ma jeszcze rzeczy, ktorych nie mozesz wziac - zrob miejsce i sprobuj ponownie.",
						r->name.c_str());
				return;
			}
		}
		else if (n)
		{
			TellNajemnicy(ch, "%s jest w drodze - poczekaj chwile.", r->name.c_str());
			return;
		}
		else
		{
			const long long carried = NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"SELECT (SELECT COUNT(*) FROM player.item WHERE owner_id=%u AND `window` IN ('INVENTORY','EQUIPMENT')) + "
					"(SELECT IF(gold>0,1,0) FROM player.player WHERE id=%u)", r->pid, r->pid)), 1);
			if (carried > 0)
			{
				TellNajemnicy(ch, "%s ma jeszcze przedmioty albo yang - wezwij go i zabierz wszystko (\"Zabierz wszystko\"), "
						"potem go zwolnij.", r->name.c_str());
				return;
			}
		}
		if (n)
			DespawnNajemnik(n->pid, "retired");
		NajemnicyQuery("UPDATE player.najemnicy SET retired=1, retired_at=NOW() WHERE merc_pid=%u AND owner_pid=%u",
				r->pid, ch->GetPlayerID());
		++s_uNajemnicyRetired;
		sys_log(0, "NAJEMNICY: retired pid=%u name=%s owner=%u slot=%u", r->pid, r->name.c_str(), ch->GetPlayerID(),
				(unsigned int)r->slot);
		TellNajemnicy(ch, "%s odchodzi na dobre. Miejsce %u jest wolne.", r->name.c_str(), (unsigned int)r->slot);
		SyncNajemnicyQuestFlags(ch);
	}

	// GM: the collector's tasks done (0..6; the unlock until the Kolekcjoner Najemnikow exists), for a character anywhere.
	void SetNajemnicyUnlock(LPCHARACTER gm, const std::string& name, int tasks)
	{
		tasks = MINMAX(0, tasks, NAJEMNICY_MAX_TASKS);
		const bool unlock = tasks > 0;
		if (!EnsureNajemnicyTables())
			return;
		if (name.empty() || name.size() > 24 || name.find_first_of("'\\\"%;") != std::string::npos)
		{
			TellNajemnicy(gm, "Podaj nick postaci.");
			return;
		}
		DWORD pid = 0;
		LPCHARACTER target = CHARACTER_MANAGER::instance().FindPC(name.c_str());
		if (target && target->GetDesc() && !target->GetDesc()->IsBot())
			pid = target->GetPlayerID();
		else
		{
			target = NULL;
			pid = (DWORD)NajemnicyNumber(std::unique_ptr<SQLMsg>(NajemnicyQuery(
					"SELECT id FROM player.player WHERE name='%s'", name.c_str())), 0);
		}
		if (!pid)
		{
			TellNajemnicy(gm, "Nie ma postaci %s.", name.c_str());
			return;
		}
		NajemnicyQuery("INSERT INTO player.najemnicy_unlock (owner_pid, unlocked, tasks, unlocked_at, source) VALUES (%u, %d, %d, "
				"NOW(), 'gm:%s') ON DUPLICATE KEY UPDATE unlocked=%d, tasks=%d, unlocked_at=NOW(), source='gm:%s'", pid,
				unlock ? 1 : 0, tasks, gm->GetName(), unlock ? 1 : 0, tasks, gm->GetName());
		if (target)
		{
			// The flag follows the row both ways here (GetNajemnicyTasks only ever raises it).
			target->SetQuestFlag("najemnicy.tasks", tasks);
			SyncNajemnicyQuestFlags(target);
			const int slots = GetNajemnicySlotsOf(target);
			if (unlock)
				TellNajemnicy(target, "Zadania Kolekcjonera Najemnikow: %d z %d. Miejsca na najemnikow: %d - zajrzyj do listu "
						"\"Najemnicy\".", tasks, NAJEMNICY_MAX_TASKS, slots);
			else
				TellNajemnicy(target, "%s", "Najemnicy zostali dla ciebie zablokowani.");
			if (slots < CountNajemnicySummonedOf(pid))
				DespawnNajemnicyOf(pid, "locked");
		}
		TellNajemnicy(gm, "%s: zadania Kolekcjonera %d z %d (%s).", name.c_str(), tasks, NAJEMNICY_MAX_TASKS,
				unlock ? "odblokowani" : "zablokowani");
		sys_log(0, "NAJEMNICY: tasks set pid=%u name=%s tasks=%d by=%s", pid, name.c_str(), tasks, gm->GetName());
	}

	void OnPlayerBotNajemnikGuildInvite(CGuild* guild, LPCHARACTER inviter, LPCHARACTER invitee)
	{
		std::map<DWORD, TNajemnik>::const_iterator it = invitee ? s_mapNajemnik.find(invitee->GetPlayerID()) : s_mapNajemnik.end();
		if (it == s_mapNajemnik.end() || !guild || !inviter)
			return;
		// Only its owner's invitation, into the owner's own guild.
		if (inviter->GetPlayerID() != it->second.ownerPid || inviter->GetGuild() != guild)
		{
			TellNajemnicy(inviter, "%s przyjmuje zaproszenie tylko od swojego pracodawcy.", invitee->GetName());
			return;
		}
		if (invitee->GetGuild())
			invitee->GetGuild()->RequestRemoveMember(invitee->GetPlayerID());
		AcceptPlayerBotGuildInvite(invitee, guild, inviter);
		sys_log(0, "NAJEMNICY: accepted the owner's guild invitation pid=%u owner=%u guild=%u", invitee->GetPlayerID(),
				inviter->GetPlayerID(), guild->GetID());
	}
}

// The engine's attack hook (battle.cpp, server-patches/najemnicy): 1 = no blow - a mercenary strikes no character and
// no character strikes it, unless their guilds are at war with each other. Monsters and stones: never its business.
int NajemnicyBlockAttack(LPCHARACTER ch, LPCHARACTER victim)
{
	if (s_mapNajemnik.empty() || !ch || !victim || ch == victim || !ch->IsPC() || !victim->IsPC())
		return 0;
	const bool a = IsPlayerBotNajemnikPID(ch->GetPlayerID());
	const bool v = IsPlayerBotNajemnikPID(victim->GetPlayerID());
	if (!a && !v)
		return 0;
	CGuild* g1 = ch->GetGuild();
	CGuild* g2 = victim->GetGuild();
	if (g1 && g2 && g1 != g2 && g1->UnderWar(g2->GetID()))
		return 0;
	return 1;
}

// CHARACTER::ItemDropPenalty's hook (char_battle.cpp): a mercenary's death drops nothing.
bool NajemnikNoItemDrop(LPCHARACTER ch)
{
	return ch && !s_mapNajemnik.empty() && IsPlayerBotNajemnikPID(ch->GetPlayerID());
}

// MT2009_PLUS_NAJEMNICY_V2: CHARACTER::PickupItem's hook (char_item.cpp, server-patches/najemnicy): a mercenary takes its
// own share of the people's boss loot a dungeon quest left on the ground (game.drop_item_at with people 1), which no other
// bot touches - the quests count it among the people (pc.is_najemnik).
bool NajemnikMayTakePeopleLoot(LPCHARACTER ch)
{
	return ch && !s_mapNajemnik.empty() && IsPlayerBotNajemnikPID(ch->GetPlayerID());
}

// MT2009_PLUS_NAJEMNICY_V2: pc.is_najemnik() (questlua_pc.cpp, server-patches/najemnicy) - the quest's character is a
// player's summoned mercenary: the dungeons' rewards and loot count it as one of the people (its bag; its owner takes
// them from the equipment window).
bool IsNajemnikCharacter(LPCHARACTER ch)
{
	return NajemnikMayTakePeopleLoot(ch);
}

// "/najemnicy" (cmd.cpp, server-patches/najemnicy): the player's commands, which the Najemnicy quest's buttons use, and
// the GM's unlock.
void PlayerBotNajemnicyCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	std::istringstream in(argument ? argument : "");
	std::string cmd, a, b, c, d;
	in >> cmd >> a >> b >> c >> d;
	for (size_t i = 0; i < cmd.size(); ++i)
		cmd[i] = (char)tolower((unsigned char)cmd[i]);
	const bool gm = ch->GetGMLevel() >= GM_HIGH_WIZARD;
	// odblokuj <nick> [zadania 1-6, domyslnie 6]; zadania <nick> <0-6>; zablokuj <nick> (= 0 zadan).
	if (gm && (cmd == "odblokuj" || cmd == "unlock" || cmd == "zadania" || cmd == "tasks"))
	{
		const int tasks = ParseNajemnicyInt(b, NAJEMNICY_MAX_TASKS);
		if ((cmd == "zadania" || cmd == "tasks") && tasks < 0)
		{
			TellNajemnicy(ch, "Uzycie: /najemnicy zadania <nick> <0-6>");
			return;
		}
		SetNajemnicyUnlock(ch, a, tasks < 0 ? NAJEMNICY_MAX_TASKS : tasks);
		return;
	}
	if (gm && (cmd == "zablokuj" || cmd == "lock"))
	{
		SetNajemnicyUnlock(ch, a, 0);
		return;
	}
	if (gm && cmd == "spis")
	{
		LogNajemnicyCensus(get_dword_time(), true);
		TellNajemnicy(ch, "Spis zapisany w syslog (NAJEMNICY: census). Wezwanych na tym rdzeniu: %u.",
				(unsigned int)s_mapNajemnik.size());
		return;
	}
	if (!EnsureNajemnicyTables())
	{
		TellNajemnicy(ch, "Najemnicy nie sa jeszcze gotowi na tym serwerze.");
		return;
	}
	if (cmd == "sync")
	{
		SyncNajemnicyQuestFlags(ch);
		return;
	}
	if (cmd.empty() || cmd == "lista" || cmd == "list")
	{
		ListNajemnicy(ch);
		return;
	}
	if (cmd == "skarbiec")
	{
		ShowNajemnicyVault(ch);
		return;
	}
	if (cmd == "wplac")
	{
		DepositNajemnicy(ch, a);
		return;
	}
	if (cmd == "odwolaj")
	{
		DismissNajemnicyCommand(ch, a);
		return;
	}
	// MT2009_PLUS_NAJEMNICY_V2: the equipment window - "eq <nr> [polecenie a b]" (the window's poll and orders, answered
	// in the Towarzysz's window protocol) and "okno <nr>" (the letter opens the window).
	if (cmd == "eq")
	{
		HandleNajemnikEqCommand(ch, a, b, c, d);
		return;
	}
	if (cmd == "okno")
	{
		OpenNajemnikWindow(ch, a);
		return;
	}
	// MT2009_PLUS_NAJEMNICY_V3: the owner's arrival on this core (the quest's login), the rejoin switch, the orders.
	if (cmd == "przybycie")
	{
		OnNajemnicyOwnerArrived(ch);
		return;
	}
	if (cmd == "powrot")
	{
		SetNajemnicyRejoin(ch, a);
		return;
	}
	if (cmd == "rozkaz")
	{
		OrderNajemnicy(ch, a, b);
		return;
	}
	if (IsNajemnicyOff() && cmd != "zabierz" && cmd != "zwolnij")
	{
		TellNajemnicy(ch, "Najemnicy sa teraz wylaczeni na tym serwerze.");
		return;
	}
	if (cmd == "stworz")
		CreateNajemnik(ch, ParseNajemnicyInt(a, 7), ParseNajemnicyInt(b, 2), c);
	else if (cmd == "wezwij")
		SummonNajemnicy(ch, a);
	else if (cmd == "daj")
		GiveNajemnikItem(ch, a, b);
	else if (cmd == "zabierz")
		TakeNajemnikItems(ch, a);
	else if (cmd == "gildia")
		GuildNajemnik(ch, a, true);
	else if (cmd == "gildia_wyjdz")
		GuildNajemnik(ch, a, false);
	else if (cmd == "zwolnij")
		RetireNajemnik(ch, a, b);
	else
		TellNajemnicy(ch, "Komendy: lista, wezwij <nr|wszyscy>, odwolaj <nr|wszyscy>, rozkaz <nr|wszyscy> <rozkaz>, "
				"powrot <0|1>, wplac <yang>, skarbiec, okno <nr>, daj <nr> <pole>, zabierz <nr>, gildia <nr>, "
				"gildia_wyjdz <nr>, zwolnij <nr> tak.");
}
