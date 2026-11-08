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
//   * it leaves when the owner dismisses it, when the owner is out of this core's world for 20 s (a logout, another
//     core or channel - stage 3 brings it back there by itself; a warp between two maps of one core it follows), when
//     the vault is empty or when the module is switched off.
//
// Commands (cmd.cpp "najemnicy", server-patches/najemnicy; the quest's buttons use them): /najemnicy [lista] | sync |
// stworz <rasa 0-7> <droga 1-2> <imie> | wezwij <miejsce|wszyscy> | odwolaj <miejsce|wszyscy> | wplac <yang> |
// skarbiec | daj <miejsce> <pole> | zabierz <miejsce> | gildia <miejsce> | gildia_wyjdz <miejsce> |
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
	const long long NAJEMNICY_DEFAULT_PRICE_H = 5000000LL;
	const int NAJEMNICY_WARN_MINUTES = 10;
	const int NAJEMNICY_MIN_LEVEL = 80;
	const int NAJEMNICY_MAX_SLOTS = 7;
	const int NAJEMNICY_MAX_TASKS = 6;	// the Kolekcjoner Najemnikow's tasks
	const int NAJEMNICY_RETIRED_DELETE_MINUTES = 20;
	const unsigned int NAJEMNICY_MAX_SEQ = 9999;	// playerbot_nj%04u: 16 characters, the account's login column

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
		TPlayerBotSidekickRuntime rt;
	};

	struct TNajemnicyOwner
	{
		DWORD nextBill = 0;
		DWORD goneSince = 0;
		long long carry = 0;	// the fee's remainder (price * n mod 60), carried to the next minute
		bool warned = false;
	};

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
		s_bNajemnicyTables = NajemnicyOk(a) && NajemnicyOk(b) && NajemnicyOk(c) && NajemnicyOk(d);
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
	};

	// The owner's mercenaries in service, by slot.
	std::vector<TNajemnikRow> LoadNajemnicyOf(DWORD ownerPid)
	{
		std::vector<TNajemnikRow> out;
		if (!EnsureNajemnicyTables())
			return out;
		std::unique_ptr<SQLMsg> m(NajemnicyQuery(
				"SELECT merc_pid, account_id, slot, job, skill_group, setup_done, login, name FROM player.najemnicy "
				"WHERE owner_pid=%u AND retired=0 ORDER BY slot", ownerPid));
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
		if (owner->GetDungeon())
			return;	// the engine takes no new member inside a dungeon (PERR_DUNGEON); it was in before or follows outside
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
			sys_log(0, "NAJEMNICY: made a party for owner=%u name=%s", owner->GetPlayerID(), owner->GetName());
		}
		party->Join(ch->GetPlayerID());
		party->Link(ch);
		sys_log(0, "NAJEMNICY: joined the owner's party pid=%u name=%s owner=%u members=%d", ch->GetPlayerID(),
				ch->GetName(), owner->GetPlayerID(), (int)party->GetMemberCount());
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
			if (!item->GetSectree() || item->GetOwner() || IsPlayerBotPeopleOnlyLoot(item))
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
		if (!ch->GetSectree() || IsPlayerBotBagFull(ch))
			return false;
		FNajemnikLoot loot(ch, owner);
		ch->GetSectree()->ForEachAround(loot);
		if (!loot.best)
		{
			n.lootVid = 0;
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

	// The whole tick of a summoned mercenary; true for every mercenary (nothing of the population's runs for it).
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
		UseHealthPotion(ch, state, dwNow);
		UseManaPotion(ch, state, dwNow);
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
		if (otherMap || dist > NAJEMNICY_TELEPORT_DISTANCE)
		{
			if (owner->IsDead() || (int)(dwNow - n.nextCatchUp) < 0)
				return true;
			n.nextCatchUp = dwNow + 3000;
			PlaceNajemnikBesideOwner(ch, state, owner, dwNow, otherMap ? "follow" : "catch_up");
			return true;
		}
		if ((int)(dwNow - n.nextParty) >= 0)
		{
			n.nextParty = dwNow + NAJEMNICY_PARTY_CHECK_MS;
			KeepNajemnikInParty(ch, owner, dwNow);
		}
		// The fight: what the owner fights, what attacks either of them, then what stands near (the Towarzysz's "atakuj").
		int why = PLAYERBOT_SIDEKICK_FOE_NEARBY;
		bool ownerFighting = false;
		LPCHARACTER foe = owner->IsDead() ? NULL
				: FindPlayerBotSidekickFoe(ch, owner, PLAYERBOT_SIDEKICK_STANCE_ATTACK, why, ownerFighting);
		if (foe && !MayNajemnikStrike(ch, foe))
		{
			PlayerBotLogThrottled("najemnicy_no_pvp", dwNow, "NAJEMNICY: leaves a character alone pid=%u name=%s foe=%s "
					"(no guild war of its guild)", n.pid, ch->GetName(), foe->GetName());
			foe = NULL;
		}
		if (foe && why == PLAYERBOT_SIDEKICK_FOE_NEARBY && RunNajemnikLoot(ch, state, n, owner, dwNow))
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
		if (RunNajemnikLoot(ch, state, n, owner, dwNow))
			return true;
		if (dist > NAJEMNICY_FOLLOW_DISTANCE)
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
			o.nextBill = dwNow;
		LPCHARACTER owner = FindNajemnicyOwnerHere(n.ownerPid);
		if (owner)
			TellNajemnicy(owner, "%s jest przy tobie.", ch->GetName());
		sys_log(0, "NAJEMNICY: entered pid=%u name=%s owner=%u slot=%u map=%ld (%ld,%ld)", n.pid, ch->GetName(), n.ownerPid,
				(unsigned int)n.slot, ch->GetMapIndex(), ch->GetX(), ch->GetY());
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
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (ch)
		{
			if (ch->GetExchange())
				ch->GetExchange()->Cancel();
			if (ch->IsDead())
				StandPlayerBotUpHere(ch);
			LeavePlayerBotParty(ch);
			ch->Save();
		}
		CPlayerBotManager::instance().Despawn(pid, playerbot_session_rules::OUT_GM);
		s_mapNajemnik.erase(it);
		++s_uNajemnicyDismissals;
		sys_log(0, "NAJEMNICY: dismissed pid=%u name=%s owner=%u why=%s", pid, name.c_str(), ownerPid, why);
		if (CountNajemnicySummonedOf(ownerPid) == 0)
			s_mapNajemnicyOwner.erase(ownerPid);
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
				"UPDATE player.najemnicy_vault SET balance=balance-%lld, total_paid=total_paid+%lld, updated_at=NOW() "
				"WHERE owner_pid=%u AND balance>=%lld", due, due, ownerPid, due));
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
				if (rec.goneSince == 0)
					rec.goneSince = dwNow;
				else if (dwNow - rec.goneSince >= NAJEMNICY_OWNER_GONE_MS)
				{
					for (std::map<DWORD, TNajemnik>::const_iterator it = s_mapNajemnik.begin(); it != s_mapNajemnik.end(); ++it)
						if (it->second.ownerPid == *o)
							out.push_back(std::make_pair(it->first, std::string("owner_gone")));
				}
				continue;
			}
			rec.goneSince = 0;
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

	bool SummonNajemnik(LPCHARACTER ch, const TNajemnikRow& r, int alreadyCounted)
	{
		if (FindNajemnikSummoned(ch->GetPlayerID(), r.slot) || IsPlayerBotNajemnikPID(r.pid))
		{
			TellNajemnicy(ch, "%s juz jest wezwany.", r.name.c_str());
			return false;
		}
		if (CHARACTER_MANAGER::instance().FindByPID(r.pid) || P2P_MANAGER::instance().FindByPID(r.pid))
		{
			TellNajemnicy(ch, "%s jeszcze odchodzi z poprzedniego miejsca - sprobuj za pol minuty.", r.name.c_str());
			return false;
		}
		LPPARTY party = ch->GetParty();
		const int members = party ? (int)party->GetMemberCount() : 1;
		if (members + alreadyCounted + 1 > PARTY_MAX_MEMBER)
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
		s_mapNajemnik[r.pid] = n;
		// PVP Fan's spawn of a dedicated identity (its account, the registry's guards stepped over for this pid).
		if (!CPlayerBotManager::instance().SpawnPvpFan(r.pid, ch->GetEmpire(), r.accountId, r.login.c_str()))
		{
			s_mapNajemnik.erase(r.pid);
			TellNajemnicy(ch, "%s nie moze teraz przyjsc - sprobuj za chwile.", r.name.c_str());
			sys_log(0, "NAJEMNICY: spawn refused pid=%u login=%s owner=%u", r.pid, r.login.c_str(), ch->GetPlayerID());
			return false;
		}
		sys_log(0, "NAJEMNICY: summoned pid=%u name=%s owner=%u owner_name=%s slot=%u map=%ld", r.pid, r.name.c_str(),
				ch->GetPlayerID(), ch->GetName(), (unsigned int)r.slot, ch->GetMapIndex());
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
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = sk->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped())
				continue;
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

// "/najemnicy" (cmd.cpp, server-patches/najemnicy): the player's commands, which the Najemnicy quest's buttons use, and
// the GM's unlock.
void PlayerBotNajemnicyCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	std::istringstream in(argument ? argument : "");
	std::string cmd, a, b, c;
	in >> cmd >> a >> b >> c;
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
		TellNajemnicy(ch, "Komendy: lista, wezwij <nr|wszyscy>, odwolaj <nr|wszyscy>, wplac <yang>, skarbiec, daj <nr> <pole>, "
				"zabierz <nr>, gildia <nr>, gildia_wyjdz <nr>, zwolnij <nr> tak.");
}
