// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: Kolekcjoner Najemnikow - the mercenaries' unlock (the owner, 8 November 2026,
// /opt/metin2/cache/yohara/najemnicy-plan.md: "Odblokowanie: Kolekcjoner Najemnikow" and "Stale bonusy za zadania
// Kolekcjonera"). server-patches/kolekcjoner/README.md has the whole picture; the engine's hooks are the edits of
// server-patches/kolekcjoner (each declares what it calls, with the same signature as here).
//
// A port of the Arezzo "Collections System" (CollectionsSystem.cpp/.hpp: categories and items from two tables, a hand-in
// with a chance, "/do_add_collect_item <cat> <slot> <all>", RECV_Collection* chat commands, a reward when every item of a
// category is in) - rewritten where it was wrong or did not fit:
//   * the chance is the SUCCESS chance (Arezzo rolled "number(1,100) <= percent" as a failure);
//   * the item leaves the bag at EVERY hand-in, success or not (Arezzo kept it on a failure of a single hand-in) - as the
//     Biologist; a failure does not count;
//   * a hand-in may take a pack (Cor Draconis 10, Odlamki Energii 100, Malze 10) and an item may have to be unopened
//     (Skrzynia Nemere: socket 0 = the openings used, ShipDefense_ChestKeep - only 0 = 3/3 left is taken);
//   * any number of items a task (the window pages them; Arezzo had 15 fixed slots);
//   * the reward is PERMANENT: the completed task is a row of player.najemnicy_kolekcjoner_complete and its points are
//     added at every CHARACTER::ComputePoints (char.cpp, "compute") - no affect, no expiry, nothing to remove, so it
//     survives logouts, warps, channel and core changes (Arezzo gave 365-day affects 303-309 and re-gave them once);
//   * progress is in our own tables (not quest flags), the protocol is one command "KNAJ <word> ..." with every format
//     checked (Arezzo's "RECV_Collection %d %s %d %d" had three arguments for four placeholders);
//   * a completed task raises the mercenaries' tasks count (playerbot_najemnicy.h): the quest flag najemnicy.tasks and
//     player.najemnicy_unlock.tasks (GREATEST - a GM's higher count stays), then "/najemnicy sync" for the letter.
// No scroll (Arezzo's 50% "percent_up" scroll item is not ported), no bots (a bot's command is ignored and a bot never
// loads a state, so nothing of this reaches the mercenaries either).
//
// Tables (linux-port/docker/mariadb/playerbot/kolekcjoner_najemnikow.sql, also made here when missing):
//   najemnicy_kolekcjoner_categories (collection_index, name, percent)      the tasks (1..6)
//   najemnicy_kolekcjoner_items (collection_index, item_index, item_vnum, item_count, pack, unopened)
//   najemnicy_kolekcjoner_rewards (collection_index, point_name, value)    s_aKnPoints names
//   najemnicy_kolekcjoner_progress (pid, collection_index, item_index, count, tries)
//   najemnicy_kolekcjoner_complete (pid, collection_index, nr, completed_at)    nr = 1..: the order of completion
// The definitions are read once (GM "przeladuj" again); a character's state is read at its first ComputePoints on this
// core (a new character instance = a new VID = read again - after a login, a warp, a core change), so the first
// recompute of a login already has the bonuses (no max HP clamped below them).
//
// Commands ("/kolekcja_najemnikow", cmd.cpp; the client's window root/uinajemnicykolekcjoner.py and the Najemnicy letter):
//   open                           everything, and the window opens
//   lista                          everything, the window only refreshes
//   oddaj <task> <item> [all]      one hand-in (one pack), or with "all" as many as the bag allows (Ctrl+click)
//   GM (GM_HIGH_WIZARD): przeladuj | ukoncz <task> (own character) | wyczysc (own character: progress and tasks gone)
// Answers (CHAT_TYPE_COMMAND):
//   KNAJ begin <tasks done> <tasks>
//   KNAJ task <task> <percent> <nr|0> <POINT:value,...|->
//   KNAJ item <task> <item> <vnum> <need> <given> <pack> <unopened> <have>
//   KNAJ end <open 0|1>
//   KNAJ res <task> <item> <code> <successes> <failures> <units used>      (EKnResult)
//   KNAJ done <task> <nr> <tasks done>
//   KNAJ tier <nr> <slots> <level>                                     (V2, after begin: every tier)
//   KNAJ info <task> <hex title|-> <min level> <sort>                   (V2, after its task line; CP1250 hex)
//   KNAJ desc <task> <hex description|->                                (V2)
//   res code 10 (V2): the character's level is below the task's min_level
// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2 (the owner, 10 November 2026): the tasks are the Seban panel's
// ("Wydarzenia -> Najemnicy -> Kolekcjoner", kolekcjoner_config.py): title, description, min_level and sort_order of a
// task, sort_order of an item (item_index stays the progress' key), any reward of s_aKnPoints, and the tiers table
// najemnicy_kolekcjoner_tiers (the n-th task done -> slots from a level; playerbot_najemnicy.h counts the slots from it).
// The panel writes the event flag m2_kolekcjoner_najemnikow_ver at every change; KnReady reads it at most every 30 s
// and reads the definitions again (every character's state too) - no restart. A changed reward reaches an online
// character at its next recompute of points (a level, an item, a warp).
// Switch: event flag m2_kolekcjoner_najemnikow_off = 1 - no hand-ins (the window and the bonuses stay).
// Logs: "KOLEKCJONER_NAJ:" lines in the syslog, item log "KOLEKCJONER_NAJ" (vnum, hint task/item/units/ok/fail).
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "db.h"
#include "log.h"
#include "questmanager.h"

#include <algorithm>
#include <climits>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

// The engine's hooks (server-patches/kolekcjoner).
void KolekcjonerNajemnikowCommand(LPCHARACTER ch, const char* argument);
void KolekcjonerNajemnikowComputePoints(LPCHARACTER ch);
// The mercenaries' command (playerbot_najemnicy.h): "sync" sets the Najemnicy letter's flags again.
void PlayerBotNajemnicyCommand(LPCHARACTER ch, const char* argument);

namespace
{
	const DWORD KN_RETRY_MS = 60 * 1000;		// tables / definitions / a state that could not be read: again after
	const DWORD KN_HANDIN_GAP_MS = 120;		// one hand-in command a player, at most this often
	const size_t KN_CACHE_PRUNE = 3000;		// states kept before the ones of characters gone are dropped
	const int KN_TIER_FIRST_LEVEL = 80;		// the n-th task: n + 1 mercenaries from level 75 + 5n (najemnicy)
	const int KN_TIER_LEVEL_STEP = 5;

	enum EKnResult
	{
		KN_OK = 0,
		KN_NO_ITEM = 1,		// fewer than one pack in the bag (and the extra inventory)
		KN_ITEM_DONE = 2,	// this item is all in
		KN_TASK_DONE = 3,	// the task is completed
		KN_BUSY = 4,		// a trade, shop, storage, cube or refine open
		KN_DEAD = 5,
		KN_OFF = 6,		// m2_kolekcjoner_najemnikow_off
		KN_BAD = 7,		// no such task / item
		KN_TOO_FAST = 8,
		KN_NOT_READY = 9,	// the tables or the character's state could not be read
		KN_LEVEL = 10,		// V2: the character's level is below the task's min_level
	};
	const DWORD KN_VERSION_POLL_MS = 30 * 1000;	// V2: the panel's reload flag (m2_kolekcjoner_najemnikow_ver), at most this often
	const int KN_MAX_TIER_TASKS = 16;

	// The bonuses a task may give (najemnicy_kolekcjoner_rewards.point_name) and how a notice names them (one %d).
	struct TKnPoint
	{
		const char* name;
		int point;
		const char* label;
	};

	const TKnPoint s_aKnPoints[] =
	{
		{ "MAX_HP", POINT_MAX_HP, "Max P\xaf +%d" },
		{ "MAX_SP", POINT_MAX_SP, "Max PE +%d" },
		{ "MAX_HP_PCT", POINT_MAX_HP_PCT, "Max P\xaf +%d%%" },
		{ "ATT_GRADE_BONUS", POINT_ATT_GRADE_BONUS, "Warto\x9c\xe6 ataku +%d" },
		{ "MAGIC_ATT_GRADE_BONUS", POINT_MAGIC_ATT_GRADE_BONUS, "Warto\x9c\xe6 ataku magicznego +%d" },
		{ "DEF_GRADE_BONUS", POINT_DEF_GRADE_BONUS, "Obrona +%d" },
		{ "MAGIC_DEF_GRADE_BONUS", POINT_MAGIC_DEF_GRADE_BONUS, "Obrona magiczna +%d" },
		{ "ATTBONUS_MONSTER", POINT_ATTBONUS_MONSTER, "Silny przeciwko potworom +%d%%" },
		{ "ATTBONUS_BOSS", POINT_ATTBONUS_BOSS, "Silny przeciwko bossom +%d%%" },
		{ "ATTBONUS_STONE", POINT_ATTBONUS_STONE, "Silny przeciwko kamieniom Metin +%d%%" },
		{ "ATTBONUS_HUMAN", POINT_ATTBONUS_HUMAN, "Silny przeciwko ludziom +%d%%" },
		{ "CRITICAL_PCT", POINT_CRITICAL_PCT, "Szansa na krytyczne uderzenie +%d%%" },
		{ "PENETRATE_PCT", POINT_PENETRATE_PCT, "Szansa na przeszywaj\xb9" "ce uderzenie +%d%%" },
		{ "RESIST_FIRE", POINT_RESIST_FIRE, "Odporno\x9c\xe6 na ogie\xf1 +%d%%" },
		{ "RESIST_ICE", POINT_RESIST_ICE, "Odporno\x9c\xe6 na l\xf3" "d +%d%%" },
		{ "RESIST_ELEC", POINT_RESIST_ELEC, "Odporno\x9c\xe6 na b\xb3yskawice +%d%%" },
		{ "RESIST_WIND", POINT_RESIST_WIND, "Odporno\x9c\xe6 na wiatr +%d%%" },
		{ "RESIST_EARTH", POINT_RESIST_EARTH, "Odporno\x9c\xe6 na ziemi\xea +%d%%" },
		{ "RESIST_DARK", POINT_RESIST_DARK, "Odporno\x9c\xe6 na ciemno\x9c\xe6 +%d%%" },
		// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2: the Seban panel's choice (the same list and order as its
		// kolekcjoner_config.py POINTS and the client's uinajemnicykolekcjoner.py POINTS).
		{ "ATT_SPEED", POINT_ATT_SPEED, "Szybko\x9c\xe6 ataku +%d%%" },
		{ "MOV_SPEED", POINT_MOV_SPEED, "Szybko\x9c\xe6 ruchu +%d%%" },
		{ "CASTING_SPEED", POINT_CASTING_SPEED, "Szybko\x9c\xe6 zakl\xea\xe6 +%d%%" },
		{ "HP_REGEN", POINT_HP_REGEN, "Regeneracja P\xaf +%d%%" },
		{ "SP_REGEN", POINT_SP_REGEN, "Regeneracja PE +%d%%" },
		{ "STEAL_HP", POINT_STEAL_HP, "Absorpcja P\xaf +%d%%" },
		{ "STEAL_SP", POINT_STEAL_SP, "Absorpcja PE +%d%%" },
		{ "ATTBONUS_ANIMAL", POINT_ATTBONUS_ANIMAL, "Silny przeciwko zwierz\xeatom +%d%%" },
		{ "ATTBONUS_ORC", POINT_ATTBONUS_ORC, "Silny przeciwko orkom +%d%%" },
		{ "ATTBONUS_MILGYO", POINT_ATTBONUS_MILGYO, "Silny przeciwko mistykom +%d%%" },
		{ "ATTBONUS_UNDEAD", POINT_ATTBONUS_UNDEAD, "Silny przeciwko nieumar\xb3ym +%d%%" },
		{ "ATTBONUS_DEVIL", POINT_ATTBONUS_DEVIL, "Silny przeciwko diab\xb3om +%d%%" },
		{ "ATTBONUS_WARRIOR", POINT_ATTBONUS_WARRIOR, "Silny przeciwko wojownikom +%d%%" },
		{ "ATTBONUS_ASSASSIN", POINT_ATTBONUS_ASSASSIN, "Silny przeciwko ninja +%d%%" },
		{ "ATTBONUS_SURA", POINT_ATTBONUS_SURA, "Silny przeciwko surom +%d%%" },
		{ "ATTBONUS_SHAMAN", POINT_ATTBONUS_SHAMAN, "Silny przeciwko szamanom +%d%%" },
		{ "RESIST_WARRIOR", POINT_RESIST_WARRIOR, "Odporno\x9c\xe6 na wojownik\xf3w +%d%%" },
		{ "RESIST_ASSASSIN", POINT_RESIST_ASSASSIN, "Odporno\x9c\xe6 na ninja +%d%%" },
		{ "RESIST_SURA", POINT_RESIST_SURA, "Odporno\x9c\xe6 na sury +%d%%" },
		{ "RESIST_SHAMAN", POINT_RESIST_SHAMAN, "Odporno\x9c\xe6 na szaman\xf3w +%d%%" },
		{ "BLOCK", POINT_BLOCK, "Szansa na blok +%d%%" },
		{ "DODGE", POINT_DODGE, "Szansa na unik strza\xb3 +%d%%" },
		{ "RESIST_SWORD", POINT_RESIST_SWORD, "Odporno\x9c\xe6 na miecze +%d%%" },
		{ "RESIST_TWOHAND", POINT_RESIST_TWOHAND, "Odporno\x9c\xe6 na bro\xf1 dwur\xea" "czn\xb9 +%d%%" },
		{ "RESIST_DAGGER", POINT_RESIST_DAGGER, "Odporno\x9c\xe6 na sztylety +%d%%" },
		{ "RESIST_BELL", POINT_RESIST_BELL, "Odporno\x9c\xe6 na dzwony +%d%%" },
		{ "RESIST_FAN", POINT_RESIST_FAN, "Odporno\x9c\xe6 na wachlarze +%d%%" },
		{ "RESIST_BOW", POINT_RESIST_BOW, "Odporno\x9c\xe6 na strza\xb3y +%d%%" },
		{ "RESIST_MAGIC", POINT_RESIST_MAGIC, "Odporno\x9c\xe6 na magi\xea +%d%%" },
		{ "RESIST_CRITICAL", POINT_RESIST_CRITICAL, "Odporno\x9c\xe6 na krytyczne uderzenia +%d%%" },
		{ "RESIST_PENETRATE", POINT_RESIST_PENETRATE, "Odporno\x9c\xe6 na przeszywaj\xb9" "ce uderzenia +%d%%" },
		{ "NORMAL_HIT_DAMAGE_BONUS", POINT_NORMAL_HIT_DAMAGE_BONUS, "\x8cr" "ednie obra\xbf" "enia +%d%%" },
		{ "SKILL_DAMAGE_BONUS", POINT_SKILL_DAMAGE_BONUS, "Obra\xbf" "enia umiej\xeatno\x9c" "ci +%d%%" },
		{ "NORMAL_HIT_DEFEND_BONUS", POINT_NORMAL_HIT_DEFEND_BONUS, "Odporno\x9c\xe6 na \x9cr" "ednie obra\xbf" "enia +%d%%" },
		{ "SKILL_DEFEND_BONUS", POINT_SKILL_DEFEND_BONUS, "Odporno\x9c\xe6 na obra\xbf" "enia umiej\xeatno\x9c" "ci +%d%%" },
		{ "POISON_PCT", POINT_POISON_PCT, "Szansa na otrucie +%d%%" },
		{ "STUN_PCT", POINT_STUN_PCT, "Szansa na omdlenie +%d%%" },
		{ "SLOW_PCT", POINT_SLOW_PCT, "Szansa na spowolnienie +%d%%" },
		{ "EXP_DOUBLE_BONUS", POINT_EXP_DOUBLE_BONUS, "Szansa na podw\xf3jne do\x9cwiadczenie +%d%%" },
		{ "GOLD_DOUBLE_BONUS", POINT_GOLD_DOUBLE_BONUS, "Szansa na podw\xf3jny yang +%d%%" },
		{ "ITEM_DROP_BONUS", POINT_ITEM_DROP_BONUS, "Szansa na podw\xf3jny drop +%d%%" },
	};

	// The six elements: a task giving all six the same value is named once ("each element").
	const char* const s_apszKnElements[] = { "RESIST_FIRE", "RESIST_ICE", "RESIST_ELEC", "RESIST_WIND", "RESIST_EARTH",
		"RESIST_DARK" };

	// The tasks' Polish names for the notices (the client has its own); another index uses the table's name.
	const char* const s_apszKnTaskNames[] = { "", "Skrzynie boss\xf3w", "Kamienie Duszy", "Cor Draconis", "Od\xb3" "amki Energii",
		"Per\xb3y i ma\xb3\xbf" "e", "Bossowie loch\xf3w" };

	struct TKnItem
	{
		int pos = 0;
		DWORD vnum = 0;
		int need = 1;
		int pack = 1;
		bool unopened = false;
	};

	struct TKnReward
	{
		std::string name;
		int point = 0;
		int value = 0;
	};

	struct TKnTask
	{
		int index = 0;
		std::string name;
		int percent = 95;
		std::vector<TKnItem> items;
		std::vector<TKnReward> rewards;
		// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2 (the Seban panel): the Polish title and description (CP1250; empty = the
		// built-in ones), the level a hand-in needs (0 = none) and the window's order.
		std::string title;
		std::string description;
		int minLevel = 0;
		int sort = 0;
	};

	// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2: the n-th completed task -> so many mercenaries from a level
	// (player.najemnicy_kolekcjoner_tiers; playerbot_najemnicy.h reads the same table for the slots).
	struct TKnTier
	{
		int nr = 0;
		int slots = 0;
		int level = 0;
	};

	struct TKnPlayer
	{
		DWORD vid = 0;			// the character instance the state was read for
		bool loaded = false;
		DWORD failedAt = 0;
		DWORD lastHandIn = 0;
		std::map<int, int> given;	// task * 256 + item -> units counted
		std::map<int, int> tries;	// task * 256 + item -> hand-ins made
		std::map<int, int> done;	// task -> nr
	};

	bool s_bKnTables = false;
	DWORD s_dwKnTablesTriedAt = 0;
	bool s_bKnDefs = false;
	DWORD s_dwKnDefsTriedAt = 0;
	std::vector<TKnTask> s_vecKnTasks;
	std::map<DWORD, TKnPlayer> s_mapKnPlayer;
	std::vector<TKnTier> s_vecKnTiers;
	long long s_llKnVersion = LLONG_MIN;	// V2: the reload flag last seen (LLONG_MIN: not read yet)
	DWORD s_dwKnVersionAt = 0;

	std::unique_ptr<SQLMsg> KnQuery(const char* fmt, ...) __attribute__((format(printf, 1, 2)));
	std::unique_ptr<SQLMsg> KnQuery(const char* fmt, ...)
	{
		char buf[2048];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		return AccountDB::instance().DirectQuery(buf);
	}

	bool KnOk(const std::unique_ptr<SQLMsg>& m)
	{
		return m.get() && m->uiSQLErrno == 0 && m->Get();
	}

	// A chat line to the player, its format checked by the compiler.
	void KnTell(LPCHARACTER ch, BYTE type, const char* fmt, ...) __attribute__((format(printf, 3, 4)));
	void KnTell(LPCHARACTER ch, BYTE type, const char* fmt, ...)
	{
		if (!ch)
			return;
		char buf[512];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		ch->ChatPacket(type, "%s", buf);
	}

	int KnInt(const char* s, int fallback)
	{
		if (!s || !*s)
			return fallback;
		int v = fallback;
		str_to_number(v, s);
		return v;
	}

	// V2: a HEX() column back to its bytes (the title and description in CP1250 whatever the connection's charset).
	std::string KnUnhex(const char* hex)
	{
		std::string out;
		if (!hex)
			return out;
		for (const char* p = hex; p[0] && p[1]; p += 2)
		{
			int v = 0;
			for (int k = 0; k < 2; ++k)
			{
				const char c = p[k];
				v = v * 16 + (c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ?
						c - 'A' + 10 : 0);
			}
			out += (char)(v < 32 ? '?' : v);
		}
		return out;
	}

	// V2: bytes to the client's lowercase hex ("-" for none), at most maxBytes of them.
	std::string KnHex(const std::string& text, size_t maxBytes)
	{
		static const char kDigits[] = "0123456789abcdef";
		std::string out;
		for (size_t i = 0; i < text.size() && i < maxBytes; ++i)
		{
			const unsigned char c = (unsigned char)text[i];
			out += kDigits[c >> 4];
			out += kDigits[c & 15];
		}
		return out.empty() ? std::string("-") : out;
	}

	int KnKey(int task, int pos)
	{
		return task * 256 + pos;
	}

	const TKnPoint* KnFindPoint(const std::string& name)
	{
		for (size_t i = 0; i < sizeof(s_aKnPoints) / sizeof(s_aKnPoints[0]); ++i)
			if (name == s_aKnPoints[i].name)
				return &s_aKnPoints[i];
		return NULL;
	}

	const char* KnTaskName(const TKnTask& task)
	{
		if (!task.title.empty())	// V2: the panel's title
			return task.title.c_str();
		const int n = (int)(sizeof(s_apszKnTaskNames) / sizeof(s_apszKnTaskNames[0]));
		if (task.index >= 1 && task.index < n)
			return s_apszKnTaskNames[task.index];
		return task.name.c_str();
	}

	// The tables, as kolekcjoner_najemnikow.sql makes them (the migration runs before the cores; this is the net for a
	// world whose migration has not run - then there are no tasks and the window says so).
	bool KnEnsureTables()
	{
		if (s_bKnTables)
			return true;
		const DWORD now = get_dword_time();
		if (s_dwKnTablesTriedAt && now - s_dwKnTablesTriedAt < KN_RETRY_MS)
			return false;
		s_dwKnTablesTriedAt = now;
		std::unique_ptr<SQLMsg> a(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_categories ("
				"collection_index TINYINT UNSIGNED NOT NULL PRIMARY KEY, name VARCHAR(48) NOT NULL DEFAULT '', "
				"percent TINYINT UNSIGNED NOT NULL DEFAULT 95) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> b(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_items ("
				"collection_index TINYINT UNSIGNED NOT NULL, item_index TINYINT UNSIGNED NOT NULL, "
				"item_vnum INT UNSIGNED NOT NULL, item_count INT UNSIGNED NOT NULL DEFAULT 1, "
				"pack INT UNSIGNED NOT NULL DEFAULT 1, unopened TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"PRIMARY KEY (collection_index, item_index)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> c(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_rewards ("
				"collection_index TINYINT UNSIGNED NOT NULL, point_name VARCHAR(32) NOT NULL, value INT NOT NULL DEFAULT 0, "
				"PRIMARY KEY (collection_index, point_name)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> d(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_progress ("
				"pid INT UNSIGNED NOT NULL, collection_index TINYINT UNSIGNED NOT NULL, item_index TINYINT UNSIGNED NOT NULL, "
				"count INT UNSIGNED NOT NULL DEFAULT 0, tries INT UNSIGNED NOT NULL DEFAULT 0, updated_at DATETIME NULL, "
				"PRIMARY KEY (pid, collection_index, item_index)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> e(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_complete ("
				"pid INT UNSIGNED NOT NULL, collection_index TINYINT UNSIGNED NOT NULL, nr TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"completed_at DATETIME NULL, PRIMARY KEY (pid, collection_index)) ENGINE=InnoDB"));
		// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2: the Seban panel's columns and the tiers (kolekcjoner_najemnikow.sql).
		std::unique_ptr<SQLMsg> f(KnQuery("ALTER TABLE player.najemnicy_kolekcjoner_categories "
				"ADD COLUMN IF NOT EXISTS title VARCHAR(64) NOT NULL DEFAULT '', "
				"ADD COLUMN IF NOT EXISTS description VARCHAR(200) NOT NULL DEFAULT '', "
				"ADD COLUMN IF NOT EXISTS min_level SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
				"ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0"));
		std::unique_ptr<SQLMsg> g(KnQuery("ALTER TABLE player.najemnicy_kolekcjoner_items "
				"ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0"));
		std::unique_ptr<SQLMsg> h(KnQuery("CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_tiers ("
				"nr TINYINT UNSIGNED NOT NULL, slots TINYINT UNSIGNED NOT NULL DEFAULT 2, "
				"level SMALLINT UNSIGNED NOT NULL DEFAULT 80, PRIMARY KEY (nr)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> i(KnQuery("INSERT IGNORE INTO player.najemnicy_kolekcjoner_tiers (nr, slots, level) "
				"SELECT * FROM (SELECT 1, 2, 80 UNION ALL SELECT 2, 3, 85 UNION ALL SELECT 3, 4, 90 UNION ALL SELECT 4, 5, 95 "
				"UNION ALL SELECT 5, 6, 100 UNION ALL SELECT 6, 7, 105) seed WHERE NOT EXISTS "
				"(SELECT 1 FROM player.najemnicy_kolekcjoner_tiers)"));
		s_bKnTables = KnOk(a) && KnOk(b) && KnOk(c) && KnOk(d) && KnOk(e) && KnOk(f) && KnOk(g) && KnOk(h) && KnOk(i);
		if (!s_bKnTables)
			sys_err("KOLEKCJONER_NAJ: the tables cannot be made (kolekcjoner_najemnikow.sql)");
		return s_bKnTables;
	}

	bool KnLoadDefinitions()
	{
		if (!KnEnsureTables())
			return false;
		std::unique_ptr<SQLMsg> mc(KnQuery("SELECT collection_index, name, percent, HEX(CONVERT(title USING cp1250)), "
				"HEX(CONVERT(description USING cp1250)), min_level, sort_order FROM player.najemnicy_kolekcjoner_categories "
				"ORDER BY sort_order, collection_index"));
		std::unique_ptr<SQLMsg> mi(KnQuery("SELECT collection_index, item_index, item_vnum, item_count, pack, unopened "
				"FROM player.najemnicy_kolekcjoner_items ORDER BY collection_index, sort_order, item_index"));
		std::unique_ptr<SQLMsg> mt(KnQuery("SELECT nr, slots, level FROM player.najemnicy_kolekcjoner_tiers ORDER BY nr"));
		std::unique_ptr<SQLMsg> mr(KnQuery("SELECT collection_index, point_name, value FROM player.najemnicy_kolekcjoner_rewards "
				"ORDER BY collection_index, point_name"));
		if (!KnOk(mc) || !KnOk(mi) || !KnOk(mr) || !mc->Get()->pSQLResult)
		{
			sys_err("KOLEKCJONER_NAJ: the definitions cannot be read");
			return false;
		}
		std::vector<TKnTask> tasks;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(mc->Get()->pSQLResult)))
		{
			TKnTask t;
			t.index = KnInt(row[0], 0);
			t.name = row[1] ? row[1] : "";
			t.percent = MINMAX(1, KnInt(row[2], 95), 100);
			t.title = KnUnhex(row[3]);
			t.description = KnUnhex(row[4]);
			t.minLevel = MAX(0, KnInt(row[5], 0));
			t.sort = KnInt(row[6], 0);
			if (t.index > 0 && t.index < 256)
				tasks.push_back(t);
		}
		std::map<int, size_t> byIndex;
		for (size_t i = 0; i < tasks.size(); ++i)
			byIndex[tasks[i].index] = i;
		if (mi->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(mi->Get()->pSQLResult)))
			{
				const int task = KnInt(row[0], 0);
				std::map<int, size_t>::const_iterator f = byIndex.find(task);
				if (f == byIndex.end())
				{
					sys_err("KOLEKCJONER_NAJ: an item of the unknown task %d", task);
					continue;
				}
				TKnItem it;
				it.pos = KnInt(row[1], 0);
				it.vnum = (DWORD)std::max(0, KnInt(row[2], 0));
				it.need = MAX(1, KnInt(row[3], 1));
				it.pack = MINMAX(1, KnInt(row[4], 1), it.need);
				it.unopened = KnInt(row[5], 0) != 0;
				if (it.vnum == 0 || it.pos < 0 || it.pos > 255)
				{
					sys_err("KOLEKCJONER_NAJ: task %d item %d is not valid (vnum %u)", task, it.pos, it.vnum);
					continue;
				}
				tasks[f->second].items.push_back(it);
			}
		if (mr->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(mr->Get()->pSQLResult)))
			{
				const int task = KnInt(row[0], 0);
				std::map<int, size_t>::const_iterator f = byIndex.find(task);
				const std::string name = row[1] ? row[1] : "";
				const TKnPoint* p = KnFindPoint(name);
				if (f == byIndex.end() || !p)
				{
					sys_err("KOLEKCJONER_NAJ: the reward %s of task %d is not known", name.c_str(), task);
					continue;
				}
				TKnReward r;
				r.name = name;
				r.point = p->point;
				r.value = KnInt(row[2], 0);
				if (r.value)
					tasks[f->second].rewards.push_back(r);
			}
		// a task without items could never be completed - left out
		std::vector<TKnTask> kept;
		for (size_t i = 0; i < tasks.size(); ++i)
			if (!tasks[i].items.empty())
				kept.push_back(tasks[i]);
			else
				sys_err("KOLEKCJONER_NAJ: task %d has no items - left out", tasks[i].index);
		s_vecKnTasks.swap(kept);
		// V2: the tiers (none read - the owner's table of 8 November 2026)
		std::vector<TKnTier> tiers;
		if (KnOk(mt) && mt->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(mt->Get()->pSQLResult)))
			{
				TKnTier t;
				t.nr = KnInt(row[0], 0);
				t.slots = KnInt(row[1], 0);
				t.level = KnInt(row[2], 0);
				if (t.nr >= 1 && t.nr <= KN_MAX_TIER_TASKS && t.slots >= 1 && t.slots <= 7)
					tiers.push_back(t);
			}
		if (tiers.empty())
			for (int n = 1; n <= 6; ++n)
			{
				TKnTier t;
				t.nr = n;
				t.slots = n + 1;
				t.level = KN_TIER_FIRST_LEVEL + (n - 1) * KN_TIER_LEVEL_STEP;
				tiers.push_back(t);
			}
		s_vecKnTiers.swap(tiers);
		size_t items = 0;
		for (size_t i = 0; i < s_vecKnTasks.size(); ++i)
			items += s_vecKnTasks[i].items.size();
		sys_log(0, "KOLEKCJONER_NAJ: %u task(s), %u item(s), %u tier(s) read", (unsigned int)s_vecKnTasks.size(),
				(unsigned int)items, (unsigned int)s_vecKnTiers.size());
		return true;
	}

	// V2: the Seban panel's reload flag (player.quest dwPID 0, m2_kolekcjoner_najemnikow_ver = the change's unix time).
	long long KnReadVersion()
	{
		std::unique_ptr<SQLMsg> m(KnQuery("SELECT lValue FROM player.quest WHERE dwPID=0 AND "
				"szName='m2_kolekcjoner_najemnikow_ver' LIMIT 1"));
		MYSQL_ROW row = NULL;
		if (!KnOk(m) || !m->Get()->pSQLResult || !(row = mysql_fetch_row(m->Get()->pSQLResult)) || !row[0])
			return 0;
		long long v = 0;
		str_to_number(v, row[0]);
		return v;
	}

	// The definitions again (GM "przeladuj", the panel's flag): every state is read again at its next use.
	void KnForgetDefinitions()
	{
		s_bKnDefs = false;
		s_dwKnDefsTriedAt = 0;
		for (std::map<DWORD, TKnPlayer>::iterator it = s_mapKnPlayer.begin(); it != s_mapKnPlayer.end(); ++it)
			it->second.vid = 0;
	}

	bool KnReady()
	{
		const DWORD now = get_dword_time();
		// V2: a change in the Seban panel is read within KN_VERSION_POLL_MS (no restart, no GM command).
		if (s_llKnVersion == LLONG_MIN || (int)(now - s_dwKnVersionAt) >= (int)KN_VERSION_POLL_MS)
		{
			s_dwKnVersionAt = now;
			const long long v = KnReadVersion();
			if (s_llKnVersion != LLONG_MIN && v != s_llKnVersion && s_bKnDefs)
			{
				sys_log(0, "KOLEKCJONER_NAJ: the panel changed the definitions (version %lld -> %lld), reading again",
						s_llKnVersion, v);
				KnForgetDefinitions();
			}
			s_llKnVersion = v;
		}
		if (s_bKnDefs)
			return true;
		if (s_dwKnDefsTriedAt && now - s_dwKnDefsTriedAt < KN_RETRY_MS)
			return false;
		s_dwKnDefsTriedAt = now;
		s_bKnDefs = KnLoadDefinitions();
		return s_bKnDefs;
	}

	const TKnTask* KnFindTask(int index)
	{
		for (size_t i = 0; i < s_vecKnTasks.size(); ++i)
			if (s_vecKnTasks[i].index == index)
				return &s_vecKnTasks[i];
		return NULL;
	}

	const TKnItem* KnFindItem(const TKnTask& task, int pos)
	{
		for (size_t i = 0; i < task.items.size(); ++i)
			if (task.items[i].pos == pos)
				return &task.items[i];
		return NULL;
	}

	bool KnIsPerson(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot() && ch->GetPlayerID();
	}

	// The states of characters no longer on this core go when the cache is large (a state is read again anyway for a
	// new character instance).
	void KnPrune()
	{
		if (s_mapKnPlayer.size() < KN_CACHE_PRUNE)
			return;
		for (std::map<DWORD, TKnPlayer>::iterator it = s_mapKnPlayer.begin(); it != s_mapKnPlayer.end(); )
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first))
				s_mapKnPlayer.erase(it++);
			else
				++it;
		}
	}

	// The character's state, read for this character instance; NULL when it cannot be read (again in a minute).
	TKnPlayer* KnState(LPCHARACTER ch)
	{
		if (!KnIsPerson(ch) || !KnReady())
			return NULL;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TKnPlayer>::iterator f = s_mapKnPlayer.find(pid);
		if (f != s_mapKnPlayer.end() && f->second.vid == (DWORD)ch->GetVID())
		{
			if (f->second.loaded)
				return &f->second;
			if (get_dword_time() - f->second.failedAt < KN_RETRY_MS)
				return NULL;
		}
		if (f == s_mapKnPlayer.end())
			KnPrune();
		TKnPlayer& p = s_mapKnPlayer[pid];
		p = TKnPlayer();
		p.vid = (DWORD)ch->GetVID();
		std::unique_ptr<SQLMsg> mg(KnQuery("SELECT collection_index, item_index, count, tries FROM "
				"player.najemnicy_kolekcjoner_progress WHERE pid=%u", pid));
		std::unique_ptr<SQLMsg> md(KnQuery("SELECT collection_index, nr FROM player.najemnicy_kolekcjoner_complete WHERE pid=%u",
				pid));
		if (!KnOk(mg) || !KnOk(md))
		{
			p.failedAt = get_dword_time();
			sys_err("KOLEKCJONER_NAJ: the state of pid %u cannot be read", pid);
			return NULL;
		}
		MYSQL_ROW row;
		if (mg->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(mg->Get()->pSQLResult)))
			{
				const int key = KnKey(KnInt(row[0], 0), KnInt(row[1], 0));
				p.given[key] = MAX(0, KnInt(row[2], 0));
				p.tries[key] = MAX(0, KnInt(row[3], 0));
			}
		if (md->Get()->pSQLResult)
			while (NULL != (row = mysql_fetch_row(md->Get()->pSQLResult)))
				p.done[KnInt(row[0], 0)] = KnInt(row[1], 0);
		p.loaded = true;
		return &p;
	}

	// The n-th task done: "2. miejsce najemnika od 80 poziomu" (the first one: the 1st and 2nd).
	std::string KnTierText(int nr)
	{
		// V2: from the tiers - the slots this tier adds over the ones before it, from its level.
		int slots = 0, level = 0, before = 0;
		bool found = false;
		for (size_t i = 0; i < s_vecKnTiers.size(); ++i)
		{
			if (s_vecKnTiers[i].nr == nr)
			{
				slots = s_vecKnTiers[i].slots;
				level = s_vecKnTiers[i].level;
				found = true;
			}
			else if (s_vecKnTiers[i].nr < nr)
				before = MAX(before, s_vecKnTiers[i].slots);
		}
		char buf[128];
		if (!found || slots <= before)
			snprintf(buf, sizeof(buf), "%s", "bez nowego miejsca najemnika");
		else if (before == 0 && slots == 2)
			snprintf(buf, sizeof(buf), "1. i 2. miejsce najemnika (od %d poziomu)", level);
		else if (slots > before + 1)
			snprintf(buf, sizeof(buf), "%d.-%d. miejsce najemnika (od %d poziomu)", before + 1, slots, level);
		else
			snprintf(buf, sizeof(buf), "%d. miejsce najemnika (od %d poziomu)", slots, level);
		return buf;
	}

	std::string KnRewardText(const TKnTask& task)
	{
		std::string out;
		int elementValue = 0;
		int elements = 0;
		for (size_t e = 0; e < sizeof(s_apszKnElements) / sizeof(s_apszKnElements[0]); ++e)
			for (size_t i = 0; i < task.rewards.size(); ++i)
				if (task.rewards[i].name == s_apszKnElements[e] && (elements == 0 || task.rewards[i].value == elementValue))
				{
					elementValue = task.rewards[i].value;
					++elements;
				}
		const bool allElements = elements == (int)(sizeof(s_apszKnElements) / sizeof(s_apszKnElements[0]));
		char buf[128];
		if (allElements)
		{
			snprintf(buf, sizeof(buf), "+%d%% odporno\x9c" "ci na ka\xbf" "dy \xbfywio\xb3", elementValue);
			out = buf;
		}
		for (size_t i = 0; i < task.rewards.size(); ++i)
		{
			if (allElements && task.rewards[i].name.compare(0, 7, "RESIST_") == 0)
			{
				bool element = false;
				for (size_t e = 0; e < sizeof(s_apszKnElements) / sizeof(s_apszKnElements[0]); ++e)
					element = element || task.rewards[i].name == s_apszKnElements[e];
				if (element)
					continue;
			}
			const TKnPoint* p = KnFindPoint(task.rewards[i].name);
			if (!p)
				continue;
			snprintf(buf, sizeof(buf), p->label, task.rewards[i].value);
			if (!out.empty())
				out += ", ";
			out += buf;
		}
		return out.empty() ? std::string("-") : out;
	}

	std::string KnRewardWire(const TKnTask& task)
	{
		std::string out;
		for (size_t i = 0; i < task.rewards.size(); ++i)
		{
			char buf[64];
			snprintf(buf, sizeof(buf), "%s%s:%d", out.empty() ? "" : ",", task.rewards[i].name.c_str(), task.rewards[i].value);
			out += buf;
		}
		return out.empty() ? std::string("-") : out;
	}

	bool KnIsHandable(LPITEM item, const TKnItem& want)
	{
		if (!item || item->GetVnum() != want.vnum || item->isLocked() || item->IsExchanging() || item->IsEquipped())
			return false;
		if (want.unopened && item->GetSocket(0) != 0)
			return false;	// a chest opened at least once (ShipDefense_ChestKeep counts the openings in socket 0)
		return true;
	}

	// Every item of the bag and of the extra inventory's storages (MT2009_PLUS_EKWIPUNEK_V1), at its own cell.
	template <typename F>
	void KnForEachItem(LPCHARACTER ch, F f)
	{
		const int bag = ch->GetInventoryMaxCount();
		for (int i = 0; i < bag; ++i)
			if (LPITEM item = ch->GetInventoryItem((WORD)i))
				if (!f(item))
					return;
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
			for (WORD i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
				if (LPITEM item = ch->Mt2009SpecialGetItem(w, i))
					if (!f(item))
						return;
	}

	int KnAvailable(LPCHARACTER ch, const TKnItem& want)
	{
		if (!want.unopened)
			return (int)std::min<long long>((long long)ch->CountSpecifyItem(want.vnum), INT_MAX);
		long long n = 0;
		KnForEachItem(ch, [&](LPITEM item) -> bool
		{
			if (KnIsHandable(item, want))
				n += item->GetCount();
			return true;
		});
		return (int)std::min<long long>(n, INT_MAX);
	}

	// One pack out of the bag (the bag first, then the storages - RemoveSpecifyItem's order); false when it is not all
	// there (nothing taken then).
	bool KnTake(LPCHARACTER ch, const TKnItem& want)
	{
		if (KnAvailable(ch, want) < want.pack)
			return false;
		if (!want.unopened)
		{
			ch->RemoveSpecifyItem(want.vnum, (ITEM_COUNT)want.pack);
			return true;
		}
		int left = want.pack;
		while (left > 0)
		{
			LPITEM found = NULL;
			KnForEachItem(ch, [&](LPITEM item) -> bool
			{
				if (!KnIsHandable(item, want))
					return true;
				found = item;
				return false;
			});
			if (!found)
				break;
			const int n = MIN(left, (int)found->GetCount());
			found->SetCount(found->GetCount() - (ITEM_COUNT)n);
			left -= n;
		}
		if (left > 0)
			sys_err("KOLEKCJONER_NAJ: %s: %d of vnum %u could not be taken", ch->GetName(), left, want.vnum);
		return true;
	}

	bool KnTaskFull(const TKnPlayer& p, const TKnTask& task)
	{
		for (size_t i = 0; i < task.items.size(); ++i)
		{
			std::map<int, int>::const_iterator f = p.given.find(KnKey(task.index, task.items[i].pos));
			if (f == p.given.end() || f->second < task.items[i].need)
				return false;
		}
		return true;
	}

	int KnDoneNr(const TKnPlayer& p, int task)
	{
		std::map<int, int>::const_iterator f = p.done.find(task);
		return f == p.done.end() ? 0 : MAX(1, f->second);
	}

	void KnSendTask(LPCHARACTER ch, const TKnPlayer& p, const TKnTask& task)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ task %d %d %d %s", task.index, task.percent, KnDoneNr(p, task.index),
				KnRewardWire(task).c_str());
		// V2: the panel's title, level and order; the description on a line of its own (the chat line's 512 bytes).
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ info %d %s %d %d", task.index, KnHex(task.title, 64).c_str(), task.minLevel,
				task.sort);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ desc %d %s", task.index, KnHex(task.description, 200).c_str());
		for (size_t i = 0; i < task.items.size(); ++i)
		{
			const TKnItem& it = task.items[i];
			std::map<int, int>::const_iterator f = p.given.find(KnKey(task.index, it.pos));
			const int given = f == p.given.end() ? 0 : MIN(f->second, it.need);
			ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ item %d %d %u %d %d %d %d %d", task.index, it.pos, it.vnum, it.need, given,
					it.pack, it.unopened ? 1 : 0, KnAvailable(ch, it));
		}
	}

	void KnSendAll(LPCHARACTER ch, const TKnPlayer& p, bool open)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ begin %d %d", (int)p.done.size(), (int)s_vecKnTasks.size());
		for (size_t i = 0; i < s_vecKnTiers.size(); ++i)	// V2: the tiers (the window's "od N poziomu", the next slot)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ tier %d %d %d", s_vecKnTiers[i].nr, s_vecKnTiers[i].slots,
					s_vecKnTiers[i].level);
		for (size_t i = 0; i < s_vecKnTasks.size(); ++i)
			KnSendTask(ch, p, s_vecKnTasks[i]);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ end %d", open ? 1 : 0);
	}

	void KnResult(LPCHARACTER ch, int task, int pos, int code, int ok, int fail, int used)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ res %d %d %d %d %d %d", task, pos, code, ok, fail, used);
	}

	void KnSaveProgress(LPCHARACTER ch, const TKnPlayer& p, int task, int pos)
	{
		const int key = KnKey(task, pos);
		std::map<int, int>::const_iterator g = p.given.find(key);
		std::map<int, int>::const_iterator t = p.tries.find(key);
		std::unique_ptr<SQLMsg> m(KnQuery("INSERT INTO player.najemnicy_kolekcjoner_progress (pid, collection_index, item_index, "
				"count, tries, updated_at) VALUES (%u, %d, %d, %d, %d, NOW()) ON DUPLICATE KEY UPDATE count=VALUES(count), "
				"tries=VALUES(tries), updated_at=NOW()", ch->GetPlayerID(), task, pos, g == p.given.end() ? 0 : g->second,
				t == p.tries.end() ? 0 : t->second));
		if (!KnOk(m))
			sys_err("KOLEKCJONER_NAJ: %s (pid %u): the progress of task %d item %d was not saved", ch->GetName(),
					ch->GetPlayerID(), task, pos);
	}

	// The task's last item is in: the permanent bonus, the mercenaries' count, the notice.
	void KnComplete(LPCHARACTER ch, TKnPlayer& p, const TKnTask& task, const char* why)
	{
		if (p.done.count(task.index))
			return;
		const int nr = (int)p.done.size() + 1;
		p.done[task.index] = nr;
		const DWORD pid = ch->GetPlayerID();
		std::unique_ptr<SQLMsg> m(KnQuery("INSERT IGNORE INTO player.najemnicy_kolekcjoner_complete (pid, collection_index, nr, "
				"completed_at) VALUES (%u, %d, %d, NOW())", pid, task.index, nr));
		if (!KnOk(m))
			sys_err("KOLEKCJONER_NAJ: %s (pid %u): the completed task %d was not saved", ch->GetName(), pid, task.index);
		const int tasks = (int)p.done.size();

		// The mercenaries (playerbot_najemnicy.h): the higher of the flag and the row counts, so both are raised - never
		// lowered (a GM's higher count stays).
		std::unique_ptr<SQLMsg> u(KnQuery("INSERT INTO player.najemnicy_unlock (owner_pid, unlocked, tasks, unlocked_at, source) "
				"VALUES (%u, 1, %d, NOW(), 'kolekcjoner') ON DUPLICATE KEY UPDATE unlocked=1, tasks=GREATEST(tasks, VALUES(tasks)), "
				"unlocked_at=IFNULL(unlocked_at, NOW())", pid, tasks));
		if (!KnOk(u))
			sys_err("KOLEKCJONER_NAJ: %s (pid %u): player.najemnicy_unlock was not raised to %d", ch->GetName(), pid, tasks);
		if (ch->GetQuestFlag("najemnicy.tasks") < tasks)
			ch->SetQuestFlag("najemnicy.tasks", tasks);
		PlayerBotNajemnicyCommand(ch, "sync");

		ch->ComputePoints();

		const std::string reward = KnRewardText(task);
		const std::string tier = KnTierText(nr);
		KnTell(ch, CHAT_TYPE_BIG_NOTICE, "Kolekcjoner Najemnik\xf3w: uko\xf1" "czone zadanie %s!", KnTaskName(task));
		KnTell(ch, CHAT_TYPE_INFO, "Kolekcjoner Najemnik\xf3w: zadanie %s uko\xf1" "czone. Sta\xb3y bonus: %s.", KnTaskName(task),
				reward.c_str());
		KnTell(ch, CHAT_TYPE_INFO, "Uko\xf1" "czone zadania: %d z %d. Odblokowuje: %s.", tasks, (int)s_vecKnTasks.size(),
				tier.c_str());
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KNAJ done %d %d %d", task.index, nr, tasks);
		sys_log(0, "KOLEKCJONER_NAJ: complete pid=%u name=%s task=%d nr=%d tasks=%d level=%d why=%s", pid, ch->GetName(),
				task.index, nr, tasks, ch->GetLevel(), why);
	}

	bool KnIsOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_kolekcjoner_najemnikow_off") != 0;
	}

	void KnHandIn(LPCHARACTER ch, int taskIndex, int pos, bool all)
	{
		TKnPlayer* pp = KnState(ch);
		if (!pp)
		{
			KnResult(ch, taskIndex, pos, KN_NOT_READY, 0, 0, 0);
			return;
		}
		TKnPlayer& p = *pp;
		const TKnTask* task = KnFindTask(taskIndex);
		const TKnItem* it = task ? KnFindItem(*task, pos) : NULL;
		if (!task || !it)
		{
			KnResult(ch, taskIndex, pos, KN_BAD, 0, 0, 0);
			return;
		}
		if (KnIsOff())
		{
			KnResult(ch, taskIndex, pos, KN_OFF, 0, 0, 0);
			return;
		}
		if (ch->IsDead())
		{
			KnResult(ch, taskIndex, pos, KN_DEAD, 0, 0, 0);
			return;
		}
		if (!ch->CanHandleItem() || ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() ||
				ch->IsCubeOpen())
		{
			KnResult(ch, taskIndex, pos, KN_BUSY, 0, 0, 0);
			return;
		}
		if (p.done.count(task->index))
		{
			KnResult(ch, taskIndex, pos, KN_TASK_DONE, 0, 0, 0);
			return;
		}
		if (task->minLevel > 0 && ch->GetLevel() < task->minLevel)	// V2: the panel's level of the task
		{
			KnResult(ch, taskIndex, pos, KN_LEVEL, 0, 0, 0);
			return;
		}
		const int key = KnKey(task->index, it->pos);
		int& given = p.given[key];
		if (given >= it->need)
		{
			KnResult(ch, taskIndex, pos, KN_ITEM_DONE, 0, 0, 0);
			return;
		}
		const DWORD now = get_dword_time();
		if (p.lastHandIn && now - p.lastHandIn < KN_HANDIN_GAP_MS)
		{
			KnResult(ch, taskIndex, pos, KN_TOO_FAST, 0, 0, 0);
			return;
		}
		p.lastHandIn = now;

		int ok = 0, fail = 0, used = 0;
		while (given < it->need)
		{
			if (!KnTake(ch, *it))
				break;
			used += it->pack;
			++p.tries[key];
			// MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: percent is the SUCCESS chance (Arezzo rolled it as the failure).
			if (number(1, 100) <= task->percent)
			{
				given = MIN(it->need, given + it->pack);
				++ok;
			}
			else
				++fail;
			if (!all)
				break;
		}
		if (!used)
		{
			KnSendTask(ch, p, *task);
			KnResult(ch, taskIndex, pos, KN_NO_ITEM, 0, 0, 0);
			return;
		}
		KnSaveProgress(ch, p, task->index, it->pos);
		char hint[128];
		snprintf(hint, sizeof(hint), "task %d item %d units %d ok %d fail %d now %d/%d", task->index, it->pos, used, ok, fail,
				given, it->need);
		LogManager::instance().ItemLog(ch, 0, (int)it->vnum, "KOLEKCJONER_NAJ", hint);
		sys_log(0, "KOLEKCJONER_NAJ: hand-in pid=%u name=%s task=%d item=%d vnum=%u units=%d ok=%d fail=%d given=%d/%d",
				ch->GetPlayerID(), ch->GetName(), task->index, it->pos, it->vnum, used, ok, fail, given, it->need);
		KnSendTask(ch, p, *task);
		KnResult(ch, taskIndex, pos, KN_OK, ok, fail, used);
		if (KnTaskFull(p, *task))
			KnComplete(ch, p, *task, "hand-in");
	}

	// GM, on the own character: the task completed at once (its items counted full).
	void KnGmComplete(LPCHARACTER ch, int taskIndex)
	{
		TKnPlayer* p = KnState(ch);
		const TKnTask* task = KnFindTask(taskIndex);
		if (!p || !task)
		{
			KnTell(ch, CHAT_TYPE_INFO, "Uzycie: /kolekcja_najemnikow ukoncz <zadanie 1-%d>", (int)s_vecKnTasks.size());
			return;
		}
		for (size_t i = 0; i < task->items.size(); ++i)
		{
			p->given[KnKey(task->index, task->items[i].pos)] = task->items[i].need;
			KnSaveProgress(ch, *p, task->index, task->items[i].pos);
		}
		KnComplete(ch, *p, *task, "gm");
		KnSendAll(ch, *p, false);
	}

	// GM, on the own character: every hand-in and completed task gone (the bonuses with them; the mercenaries' count stays -
	// "/najemnicy zadania" sets that one).
	void KnGmWipe(LPCHARACTER ch)
	{
		const DWORD pid = ch->GetPlayerID();
		std::unique_ptr<SQLMsg> a(KnQuery("DELETE FROM player.najemnicy_kolekcjoner_progress WHERE pid=%u", pid));
		std::unique_ptr<SQLMsg> b(KnQuery("DELETE FROM player.najemnicy_kolekcjoner_complete WHERE pid=%u", pid));
		s_mapKnPlayer.erase(pid);
		ch->ComputePoints();
		TKnPlayer* p = KnState(ch);
		if (p)
			KnSendAll(ch, *p, false);
		KnTell(ch, CHAT_TYPE_INFO, "Kolekcjoner Najemnikow: postep i zadania wyczyszczone (%s).", KnOk(a) && KnOk(b) ? "ok" : "blad bazy");
		sys_log(0, "KOLEKCJONER_NAJ: wiped pid=%u name=%s", pid, ch->GetName());
	}
}

// char.cpp, CHARACTER::ComputePoints ("compute"): the completed tasks' bonuses on the character's points - every recompute,
// so they are permanent and never removable. Read for a new character instance here, before its first points are counted.
void KolekcjonerNajemnikowComputePoints(LPCHARACTER ch)
{
	if (!KnIsPerson(ch))
		return;
	TKnPlayer* p = KnState(ch);
	if (!p || p->done.empty())
		return;
	for (std::map<int, int>::const_iterator d = p->done.begin(); d != p->done.end(); ++d)
	{
		const TKnTask* task = KnFindTask(d->first);
		if (!task)
			continue;
		for (size_t i = 0; i < task->rewards.size(); ++i)
			ch->PointChange((WORD)task->rewards[i].point, task->rewards[i].value);
	}
}

// "/kolekcja_najemnikow" (cmd.cpp, server-patches/kolekcjoner): the client's window and the Najemnicy letter.
void KolekcjonerNajemnikowCommand(LPCHARACTER ch, const char* argument)
{
	if (!KnIsPerson(ch))
		return;
	std::istringstream in(argument ? argument : "");
	std::string cmd, a, b, c;
	in >> cmd >> a >> b >> c;
	for (size_t i = 0; i < cmd.size(); ++i)
		cmd[i] = (char)tolower((unsigned char)cmd[i]);
	const bool gm = ch->GetGMLevel() >= GM_HIGH_WIZARD;

	if (gm && cmd == "przeladuj")
	{
		KnForgetDefinitions();	// every state is read again at the next use (the tasks' items may have changed)
		const bool ok = KnReady();
		KnTell(ch, CHAT_TYPE_INFO, "Kolekcjoner Najemnikow: %s (%u zadan).", ok ? "definicje wczytane" : "blad bazy",
				(unsigned int)s_vecKnTasks.size());
		return;
	}
	TKnPlayer* p = KnState(ch);
	if (!p)
	{
		KnResult(ch, 0, 0, KN_NOT_READY, 0, 0, 0);
		return;
	}
	if (gm && cmd == "ukoncz")
	{
		KnGmComplete(ch, KnInt(a.c_str(), 0));
		return;
	}
	if (gm && cmd == "wyczysc")
	{
		KnGmWipe(ch);
		return;
	}
	if (cmd == "oddaj")
	{
		KnHandIn(ch, KnInt(a.c_str(), 0), KnInt(b.c_str(), -1), c == "all" || c == "wszystko" || c == "1");
		return;
	}
	KnSendAll(ch, *p, cmd != "lista" && cmd != "sync");
}
