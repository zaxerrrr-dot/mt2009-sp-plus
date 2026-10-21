#pragma once
// MT2009_PLUS_WORLDBOSS_V1: Boss Swiata - the World Boss event (the owner, 21
// October 2026: "exactly per the Polish wiki"; the pages are saved in
// /opt/metin2/cache/yohara/wiki/worldboss/, what was built and what differs:
// /opt/metin2/cache/yohara/boss-swiata.md).
//
// The wiki, as this file does it:
//  - "Boss świata pojawia się w dowolnym czasie podczas trwania eventu" - while
//    the event runs (worldboss_config.mode: 1 always, 2 only while the panels'
//    scheduler kind "worldboss" runs, 0 off) one of the six bosses (4429 ...
//    4479, worldboss.txt) appears at a spot of one of the four maps (Dolina
//    Seungryong 64, Pustynia Yongbi 63, Doyyumhwan 62, Gora Sohan 61) with a
//    notice naming the area it terrorises. MT2009_PLUS_WORLDBOSS_ICON_V1 (the
//    owner, 21 October 2026: "Boss Świata niech będzie co 120 minut"): the
//    next one appears break_min..break_max minutes (120..120 by default) after
//    the last one APPEARED - a boss every two hours whether he fell in ten
//    minutes or escaped - but never sooner than NEXT_GAP_MIN minutes after the
//    last one fell or escaped (a break shorter than the fight).
//  - every blow a character (a player or, the owner's word of 21 October, a
//    bot) of min_level or more deals to it is added up; a character who
//    leaves the map (or the game) loses what he dealt (the it-wiki),
//    "musicie znajdować się nadal na tej samej mapie, gdy boss padnie".
//  - at 75, 50 and 25 % of its health it calls groups of its five men around it.
//  - it escapes after fight_minutes: "licznik obrażeń zostanie zresetowany i
//    nikt na serwerze nie otrzyma nagrody" (the boss and its men vanish).
//  - when it falls, the characters with min_damage or more are ranked by damage:
//    places 1-10 loot tier I, 11-25 II, 26-100 III, past 100 IV, each with its
//    items and drop buff (worldboss.txt "tier"); the rank points 10/5/2/1 go to
//    the character and to its guild of the moment (the season's ranking per
//    kingdom). "Pokonaj Bossa Świata" - 100 000 damage (mission_damage) to a
//    defeated boss gives +20 % attack value for 3 h, once a day.
//  - the rewards wait in the window ("Odbierz nagrodę") until the next boss
//    appears: "W przeciwnym razie nagroda przepadnie".
//  - the season, 8 weeks: the top 25 characters and the top 3 guilds of every
//    kingdom get its prizes (the guild's to every member who earned it at least
//    one point and is still in it), collected in the same window.
//  - the bosses and their men give no experience and drop nothing (mob_proto
//    and WorldBossNoDrop, the it-/ro-wiki).
//
// One core runs the boss: the one of worldboss_config.channel that hosts the
// maps (game1 of that channel under both layouts). It keeps the damage in
// memory and writes player.worldboss_state, worldboss_damage, worldboss_reward
// and worldboss_points; every other core reads the state for the window, and a
// reward is given by whichever core its player stands on - one conditional
// UPDATE (state 0 -> 1) decides, as Kolo Fortuny's spins.
//
// Bots: they raid the boss when worldboss_config.bots is 1
// (PLAYERBOT_WORLD_BOSSES rows of playerbot_boss_raid.h, WorldBossBotsAllowed)
// - a level-120 king of millions of health is no fight for one player.
// MT2009_PLUS_WORLDBOSS_ICON_V1 (the owner, 21 October 2026: "W rankingach
// również boty. Nagrody również dla botów."): a bot's damage ranks like a
// player's - the loot tiers, the mission, the rank points of the character
// and its guild, the season's prizes - and as a bot cannot click "Odbierz
// nagrode", every core gives its bots their waiting rewards itself
// (BotClaims, every BOT_CLAIM_MS, when the bag has room).
//
// To the client (game.py "WB", root/uiworldboss.py):
//   WB info <state> <boss vnum> <map> <fight left s> <next left s> <my damage>
//           <min damage> <rewards waiting> <my tier> <my place> <season points>
//           <event on> <channel>
//   WB where <map> <area ...>
//   WB rbegin <serial> <boss vnum> <count> / WB r <place> <tier> <empire> <damage>
//           <name> <guild|-> / WB rme <...the same, place 0 = not ranked> / WB rend
//   WB sbegin <season> <seconds left> <empire> / WB s <place> <points> <name>
//           <guild|-> / WB sg <place> <points> <guild> / WB sme <place> <points>
//           / WB send
//   WB claimok
//   WB mark <x> <y> <local x> <local y> <boss vnum> - MT2009_PLUS_WORLDBOSS_ICON_V1: the standing boss's
//           place (global and map-local units), every MARK_MS to the players on his map - the client draws
//           his icon on the atlas and the minimap (root/uiworldboss.py)
//   WB unmark - he fell or escaped: the icon goes
// From the client: "/worldboss info|ranking|sezon <empire>|odbierz"; a game
// master also "spawn [boss 1-6] [map]", "ucieczka", "przeladuj", "stan".
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, after playerbot_catchking.h; ticked from playerbot_events.h.
#include "locale_service.h"
#include "questmanager.h"
#include "guild.h"
#include <ctime>
#include <cmath>

bool InGameEventIsActive(const char* key);

namespace mt2009_worldboss
{
	const DWORD AFFECT_DROP = 720;		// the loot tier's drop buff (WorldBossDropBonus, item_manager.cpp)
	const DWORD AFFECT_ATTACK = 721;	// "Pokonaj Bossa Świata": POINT_MALL_ATTBONUS
	const DWORD CONFIG_RELOAD_MS = 30 * 1000;
	const DWORD STATE_READ_MS = 5 * 1000;	// a core that does not run the boss
	const DWORD STATE_SAVE_MS = 30 * 1000;
	const DWORD REMINDER_MS = 10 * 60 * 1000;
	const DWORD COMMAND_GAP_MS = 700;
	const DWORD MAP_CHECK_MS = 3000;
	const DWORD BOOT_DELAY_MS = 3 * 60 * 1000;
	const DWORD MARK_MS = 3000;		// MT2009_PLUS_WORLDBOSS_ICON_V1: the map icon's position
	const DWORD BOT_CLAIM_MS = 30 * 1000;	// MT2009_PLUS_WORLDBOSS_ICON_V1: the bots' rewards
	const int NEXT_GAP_MIN = 5;		// the least break after a fall/escape
	const int SPOT_SPREAD = 600;		// a spot's spawn square, +- units
	const int MEN_SPREAD = 1500;		// the men around the boss
	const int RANK_LIST_MAX = 200;		// the ranking sent to a window
	const char* const EVENT_FLAG = "worldboss_event";

	enum EState { ST_WAIT = 0, ST_STANDING = 1, ST_DEFEATED = 2, ST_ESCAPED = 3 };
	enum EKind { KIND_TIER = 0, KIND_SEASON_CHAR = 1, KIND_SEASON_GUILD = 2, KIND_MISSION = 3 };

	struct TItem { DWORD vnum; int count; int days; };
	struct TBoss { DWORD vnum; std::vector<DWORD> men; std::string name; };
	struct TSpot { long map; long x, y; std::string area; };
	struct TTier { int n, first, last, points, drop, seconds; std::vector<TItem> items; };
	struct TPrize { int first, last; std::vector<TItem> items; };

	struct TData
	{
		bool loaded;
		std::vector<TBoss> bosses;
		std::vector<TSpot> spots;
		std::vector<TTier> tiers;
		int missionPct, missionSeconds;
		std::vector<TPrize> seasonChar, seasonGuild;
		int seasonWeeks;
		TData() : loaded(false), missionPct(20), missionSeconds(10800), seasonWeeks(8) {}
	};

	struct TConfig
	{
		int mode, channel, breakMin, breakMax, fightMinutes;
		DWORD minDamage, missionDamage;
		int minLevel;
		DWORD hpFull;
		int hpStart, hpStep, groups, bots, seasonWeeks;
		DWORD forceAt, forceBoss, forceMap, escapeNow, seasonEndNow;
		// MT2009_PLUS_WORLDBOSS_ICON_V1: a boss every 120 minutes (break_min = break_max = 120)
		TConfig() : mode(1), channel(1), breakMin(120), breakMax(120), fightMinutes(45), minDamage(250000),
			missionDamage(100000), minLevel(30), hpFull(8000000), hpStart(30), hpStep(5), groups(6), bots(1),
			seasonWeeks(8), forceAt(0), forceBoss(0), forceMap(0), escapeNow(0), seasonEndNow(0) {}
	};

	struct TState
	{
		DWORD serial, state, bossVnum, map;
		long x, y;
		std::string area;
		DWORD channel, spawnedAt, fightEnd, endedAt, nextAt, falls, hpMax, hpPct, season, seasonEnd;
		TState() : serial(0), state(ST_WAIT), bossVnum(0), map(0), x(0), y(0), channel(1), spawnedAt(0), fightEnd(0),
			endedAt(0), nextAt(0), falls(0), hpMax(0), hpPct(0), season(1), seasonEnd(0) {}
	};

	struct TDamage
	{
		long long damage;
		std::string name;
		BYTE empire;
		BYTE level;
		DWORD guildId;
		std::string guildName;
		TDamage() : damage(0), empire(0), level(0), guildId(0) {}
	};

	TData s_data;
	TConfig s_cfg;
	TState s_state;
	bool s_bConfigRead = false;
	bool s_bStateRead = false;
	DWORD s_dwNextConfig = 0;
	DWORD s_dwNextStateRead = 0;
	DWORD s_dwNextSave = 0;
	DWORD s_dwNextReminder = 0;
	DWORD s_dwNextMapCheck = 0;
	DWORD s_dwNextSecond = 0;
	DWORD s_dwNextMark = 0;		// MT2009_PLUS_WORLDBOSS_ICON_V1
	DWORD s_dwNextBotClaim = 0;	// MT2009_PLUS_WORLDBOSS_ICON_V1
	bool s_bOwnerKnown = false;
	bool s_bOwner = false;
	// the boss this core runs
	DWORD s_dwBossVID = 0;
	bool s_bBossFell = false;
	int s_iCalls = 0;				// 75/50/25 % calls done (0-3)
	std::vector<DWORD> s_vecMen;
	std::map<DWORD, TDamage> s_mapDamage;	// pid -> what a player dealt
	DWORD s_dwLastBossIndex = 999;
	std::map<DWORD, DWORD> s_mapLastCommand;	// pid -> get_dword_time()

	// ------------------------------------------------------------ helpers

	std::unique_ptr<SQLMsg> Query(const char* fmt, ...)
	{
		char buf[4096];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		return std::unique_ptr<SQLMsg>(DBManager::instance().DirectQuery("%s", buf));
	}

	bool Ok(const std::unique_ptr<SQLMsg>& m)
	{
		return m.get() && m->uiSQLErrno == 0 && m->Get();
	}

	DWORD Num(const char* s)
	{
		DWORD v = 0;
		if (s)
			str_to_number(v, s);
		return v;
	}

	std::string Escape(const std::string& s)
	{
		char buf[256];
		DBManager::instance().EscapeString(buf, sizeof(buf), s.c_str(), std::min<size_t>(s.size(), 100));
		return buf;
	}

	bool IsPlayer(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	// A name or guild with no spaces for a chat-command line.
	std::string Token(const std::string& s)
	{
		if (s.empty())
			return "-";
		std::string out(s);
		for (size_t i = 0; i < out.size(); ++i)
			if (out[i] == ' ' || out[i] == '\t')
				out[i] = '_';
		return out;
	}

	const TBoss* FindBoss(DWORD vnum)
	{
		for (size_t i = 0; i < s_data.bosses.size(); ++i)
			if (s_data.bosses[i].vnum == vnum)
				return &s_data.bosses[i];
		return NULL;
	}

	bool IsMan(DWORD vnum)
	{
		for (size_t i = 0; i < s_data.bosses.size(); ++i)
			for (size_t j = 0; j < s_data.bosses[i].men.size(); ++j)
				if (s_data.bosses[i].men[j] == vnum)
					return true;
		return false;
	}

	const char* BossName(DWORD vnum)
	{
		const CMob* mob = CMobManager::instance().Get(vnum);
		if (mob)
			return mob->m_table.szLocaleName;
		const TBoss* b = FindBoss(vnum);
		return b ? b->name.c_str() : "Boss Swiata";
	}

	const char* TierName(int tier)
	{
		switch (tier)
		{
			case 1: return "I";
			case 2: return "II";
			case 3: return "III";
			case 4: return "IV";
		}
		return "-";
	}

	DWORD Today()
	{
		const time_t now = time(NULL);
		struct tm t;
		localtime_r(&now, &t);
		return (DWORD)((t.tm_year + 1900) * 10000 + (t.tm_mon + 1) * 100 + t.tm_mday);
	}

	void ParseItems(const char* text, std::vector<TItem>& out)
	{
		const char* p = text;
		while (p && *p)
		{
			unsigned int vnum = 0, days = 0;
			int count = 1;
			const int n = sscanf(p, "%u:%d:%u", &vnum, &count, &days);
			if (n >= 1 && vnum)
			{
				TItem it;
				it.vnum = vnum;
				it.count = n >= 2 ? std::max(1, count) : 1;
				it.days = n >= 3 ? (int)days : 0;
				out.push_back(it);
			}
			p = strchr(p, ',');
			if (p)
				++p;
		}
	}

	std::string FormatItems(const std::vector<TItem>& items)
	{
		std::string out;
		for (size_t i = 0; i < items.size(); ++i)
		{
			char part[48];
			snprintf(part, sizeof(part), "%s%u:%d:%d", out.empty() ? "" : ",", items[i].vnum, items[i].count, items[i].days);
			out += part;
		}
		return out;
	}

	// ------------------------------------------------------------ the data file

	bool LoadData()
	{
		TData d;
		const std::string path = LocaleService_GetBasePath() + "/worldboss.txt";
		FILE* fp = fopen(path.c_str(), "r");
		if (!fp)
		{
			sys_err("WORLDBOSS: %s not found - the event is off", path.c_str());
			s_data = d;
			return false;
		}
		char line[1024];
		while (fgets(line, sizeof(line), fp))
		{
			size_t n = strlen(line);
			while (n && (line[n - 1] == '\n' || line[n - 1] == '\r'))
				line[--n] = 0;
			if (!n || line[0] == '#')
				continue;
			std::vector<std::string> f;
			char* save = NULL;
			for (char* t = strtok_r(line, "\t", &save); t; t = strtok_r(NULL, "\t", &save))
				f.push_back(t);
			if (f.empty())
				continue;
			if (f[0] == "boss" && f.size() >= 4)
			{
				TBoss b;
				b.vnum = Num(f[1].c_str());
				std::vector<TItem> men;
				ParseItems(f[2].c_str(), men);
				for (size_t i = 0; i < men.size(); ++i)
					b.men.push_back(men[i].vnum);
				b.name = f[3];
				if (b.vnum)
					d.bosses.push_back(b);
			}
			else if (f[0] == "spot" && f.size() >= 5)
			{
				TSpot s;
				s.map = (long)Num(f[1].c_str());
				s.x = (long)Num(f[2].c_str());
				s.y = (long)Num(f[3].c_str());
				s.area = f[4];
				d.spots.push_back(s);
			}
			else if (f[0] == "tier" && f.size() >= 8)
			{
				TTier t;
				t.n = (int)Num(f[1].c_str());
				t.first = (int)Num(f[2].c_str());
				t.last = (int)Num(f[3].c_str());
				t.points = (int)Num(f[4].c_str());
				t.drop = (int)Num(f[5].c_str());
				t.seconds = (int)Num(f[6].c_str());
				ParseItems(f[7].c_str(), t.items);
				d.tiers.push_back(t);
			}
			else if (f[0] == "mission" && f.size() >= 3)
			{
				d.missionPct = (int)Num(f[1].c_str());
				d.missionSeconds = (int)Num(f[2].c_str());
			}
			else if ((f[0] == "season_char" || f[0] == "season_guild") && f.size() >= 4)
			{
				TPrize p;
				p.first = (int)Num(f[1].c_str());
				p.last = (int)Num(f[2].c_str());
				ParseItems(f[3].c_str(), p.items);
				(f[0] == "season_char" ? d.seasonChar : d.seasonGuild).push_back(p);
			}
			else if (f[0] == "season_weeks" && f.size() >= 2)
				d.seasonWeeks = std::max(1, (int)Num(f[1].c_str()));
		}
		fclose(fp);
		d.loaded = !d.bosses.empty() && !d.spots.empty() && !d.tiers.empty();
		s_data = d;
		sys_log(0, "WORLDBOSS: %s - %u bosses, %u spots, %u tiers, %u+%u season rows%s", path.c_str(),
				(unsigned)d.bosses.size(), (unsigned)d.spots.size(), (unsigned)d.tiers.size(),
				(unsigned)d.seasonChar.size(), (unsigned)d.seasonGuild.size(), d.loaded ? "" : " - INCOMPLETE, the event is off");
		return d.loaded;
	}

	// ------------------------------------------------------------ the database

	void ReadConfig()
	{
		std::unique_ptr<SQLMsg> m(Query("SELECT mode, channel, break_min, break_max, fight_minutes, min_damage, mission_damage, "
				"min_level, hp_full, hp_start_pct, hp_step_pct, groups_per_call, bots, season_weeks, force_at, force_boss, "
				"force_map, escape_now, season_end_now FROM player.worldboss_config WHERE id = 1"));
		if (!Ok(m) || !m->Get()->pSQLResult || !m->Get()->uiNumRows)
			return;
		MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
		if (!r)
			return;
		TConfig c;
		c.mode = (int)Num(r[0]);
		c.channel = std::max(1, (int)Num(r[1]));
		c.breakMin = std::max(1, (int)Num(r[2]));
		c.breakMax = std::max(c.breakMin, (int)Num(r[3]));
		c.fightMinutes = std::max(1, (int)Num(r[4]));
		c.minDamage = Num(r[5]);
		c.missionDamage = Num(r[6]);
		c.minLevel = (int)Num(r[7]);
		c.hpFull = std::max<DWORD>(1000, Num(r[8]));
		c.hpStart = MINMAX(1, (int)Num(r[9]), 100);
		c.hpStep = MINMAX(0, (int)Num(r[10]), 100);
		c.groups = MINMAX(0, (int)Num(r[11]), 20);
		c.bots = (int)Num(r[12]);
		c.seasonWeeks = std::max(1, (int)Num(r[13]));
		c.forceAt = Num(r[14]);
		c.forceBoss = Num(r[15]);
		c.forceMap = Num(r[16]);
		c.escapeNow = Num(r[17]);
		c.seasonEndNow = Num(r[18]);
		s_cfg = c;
		s_bConfigRead = true;
	}

	bool ReadState()
	{
		std::unique_ptr<SQLMsg> m(Query("SELECT serial, state, boss_vnum, map_index, pos_x, pos_y, area, channel, spawned_at, "
				"fight_end, ended_at, next_at, falls, hp_max, hp_pct, season, season_end FROM player.worldboss_state WHERE id = 1"));
		if (!Ok(m) || !m->Get()->pSQLResult || !m->Get()->uiNumRows)
			return false;
		MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
		if (!r)
			return false;
		TState s;
		s.serial = Num(r[0]);
		s.state = Num(r[1]);
		s.bossVnum = Num(r[2]);
		s.map = Num(r[3]);
		s.x = (long)atol(r[4] ? r[4] : "0");
		s.y = (long)atol(r[5] ? r[5] : "0");
		s.area = r[6] ? r[6] : "";
		s.channel = Num(r[7]);
		s.spawnedAt = Num(r[8]);
		s.fightEnd = Num(r[9]);
		s.endedAt = Num(r[10]);
		s.nextAt = Num(r[11]);
		s.falls = Num(r[12]);
		s.hpMax = Num(r[13]);
		s.hpPct = Num(r[14]);
		s.season = std::max<DWORD>(1, Num(r[15]));
		s.seasonEnd = Num(r[16]);
		s_state = s;
		s_bStateRead = true;
		return true;
	}

	void SaveState()
	{
		const TState& s = s_state;
		Query("UPDATE player.worldboss_state SET serial = %u, state = %u, boss_vnum = %u, map_index = %u, pos_x = %ld, "
				"pos_y = %ld, area = '%s', channel = %u, spawned_at = %u, fight_end = %u, ended_at = %u, next_at = %u, "
				"falls = %u, hp_max = %u, hp_pct = %u, season = %u, season_end = %u, updated_at = UNIX_TIMESTAMP() WHERE id = 1",
				s.serial, s.state, s.bossVnum, s.map, s.x, s.y, Escape(s.area).c_str(), s.channel, s.spawnedAt, s.fightEnd,
				s.endedAt, s.nextAt, s.falls, s.hpMax, s.hpPct, s.season, s.seasonEnd);
		s_dwNextSave = get_dword_time() + STATE_SAVE_MS;
	}

	// ------------------------------------------------------------ who runs it

	bool HostsAnySpot()
	{
		for (size_t i = 0; i < s_data.spots.size(); ++i)
			if (SECTREE_MANAGER::instance().GetMap(s_data.spots[i].map))
				return true;
		return false;
	}

	bool IsOwner()
	{
		return s_data.loaded && !g_bAuthServer && g_bChannel == (BYTE)s_cfg.channel && HostsAnySpot();
	}

	// The event as the operator set it (mode) and, for mode 2, the scheduler.
	bool EventOn()
	{
		if (s_cfg.mode == 1)
			return true;
		if (s_cfg.mode == 2)
			return s_aPlayerBotEventStatus[playerbot_events::KIND_WORLDBOSS].active;
		return false;
	}

	LPCHARACTER Boss()
	{
		if (!s_dwBossVID)
			return NULL;
		LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(s_dwBossVID);
		if (!ch || ch->IsPC() || ch->GetRaceNum() != s_state.bossVnum)
			return NULL;
		return ch;
	}

	void DestroyMen()
	{
		for (size_t i = 0; i < s_vecMen.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(s_vecMen[i]);
			if (ch && !ch->IsPC() && IsMan(ch->GetRaceNum()) && !ch->IsDead())
				M2_DESTROY_CHARACTER(ch);
		}
		s_vecMen.clear();
	}

	// Somebody's leftovers after a crash or a restart: a boss of the event
	// standing with no state that knows him (a core that ran him died).
	void DestroyStrays(long mapIndex)
	{
		std::vector<LPCHARACTER> gone;
		for (auto& kv : CHARACTER_MANAGER::instance().GetCharacterVIDMap())
		{
			LPCHARACTER ch = kv.second;
			if (!ch || ch->IsPC() || ch->IsDead() || (mapIndex && ch->GetMapIndex() != mapIndex))
				continue;
			if ((FindBoss(ch->GetRaceNum()) || IsMan(ch->GetRaceNum())) && (DWORD)ch->GetVID() != s_dwBossVID)
				gone.push_back(ch);
		}
		for (size_t i = 0; i < gone.size(); ++i)
			M2_DESTROY_CHARACTER(gone[i]);
		if (!gone.empty())
			sys_log(0, "WORLDBOSS: %u stray event monster(s) removed", (unsigned)gone.size());
	}

	int HpPercentFor(DWORD falls)
	{
		return std::min(100, s_cfg.hpStart + (int)falls * s_cfg.hpStep);
	}

	// MT2009_PLUS_WORLDBOSS_ICON_V1: the break runs from the last boss's
	// appearance ("co 120 minut"), at least NEXT_GAP_MIN minutes from now.
	void PlanNext(DWORD now)
	{
		const int minutes = number(s_cfg.breakMin, s_cfg.breakMax);
		const DWORD from = s_state.spawnedAt && s_state.spawnedAt <= now ? s_state.spawnedAt : now;
		s_state.nextAt = std::max(from + (DWORD)minutes * 60, now + (DWORD)NEXT_GAP_MIN * 60);
		if (s_cfg.forceAt > now)
			s_state.nextAt = s_cfg.forceAt;
		sys_log(0, "WORLDBOSS: the next boss in %d min (epoch %u)", (int)(s_state.nextAt - now) / 60, s_state.nextAt);
	}

	// ------------------------------------------------------------ the spawn

	bool Spawn(DWORD now, int forceBoss, long forceMap)
	{
		std::vector<size_t> spots;
		for (size_t i = 0; i < s_data.spots.size(); ++i)
			if (SECTREE_MANAGER::instance().GetMap(s_data.spots[i].map) && (!forceMap || s_data.spots[i].map == forceMap))
				spots.push_back(i);
		if (spots.empty() || s_data.bosses.empty())
		{
			sys_err("WORLDBOSS: no spot hosted here%s", forceMap ? " on that map" : "");
			return false;
		}
		size_t bi;
		if (forceBoss >= 1 && forceBoss <= (int)s_data.bosses.size())
			bi = (size_t)(forceBoss - 1);
		else
		{
			bi = (size_t)number(0, (int)s_data.bosses.size() - 1);
			if (bi == s_dwLastBossIndex && s_data.bosses.size() > 1)
				bi = (bi + 1 + (size_t)number(0, (int)s_data.bosses.size() - 2)) % s_data.bosses.size();
		}
		const TBoss& boss = s_data.bosses[bi];
		const TSpot& spot = s_data.spots[spots[(size_t)number(0, (int)spots.size() - 1)]];
		const LPSECTREE_MAP map = SECTREE_MANAGER::instance().GetMap(spot.map);
		const long cx = map->m_setting.iBaseX + spot.x * 100;
		const long cy = map->m_setting.iBaseY + spot.y * 100;
		DestroyStrays(0);
		LPCHARACTER ch = CHARACTER_MANAGER::instance().SpawnMobRange(boss.vnum, spot.map, cx - SPOT_SPREAD, cy - SPOT_SPREAD,
				cx + SPOT_SPREAD, cy + SPOT_SPREAD, true, true, false);
		if (!ch)
		{
			sys_err("WORLDBOSS: spawn of %u on map %ld at %ld,%ld failed", boss.vnum, spot.map, spot.x, spot.y);
			return false;
		}
		// the health of the moment: weak first ("na początku bossowie są słabi"), growing a fall
		const int pct = HpPercentFor(s_state.falls);
		long long hp = (long long)s_cfg.hpFull * pct / 100;
		if (hp < 1000)
			hp = 1000;
		if (hp > INT_MAX)
			hp = INT_MAX;
		ch->SetRealPoint(POINT_MAX_HP, (int)hp);
		ch->PointChange(POINT_MAX_HP, 0);
		ch->SetHP(ch->GetMaxHP());
		ch->BroadcastTargetPacket();

		// the rewards of the last boss nobody collected are lost now
		Query("UPDATE player.worldboss_reward SET state = 2 WHERE state = 0 AND kind IN (%d, %d)", KIND_TIER, KIND_MISSION);

		s_dwBossVID = (DWORD)ch->GetVID();
		s_bBossFell = false;
		s_iCalls = 0;
		s_vecMen.clear();
		s_mapDamage.clear();
		s_dwLastBossIndex = bi;
		TState& s = s_state;
		++s.serial;
		s.state = ST_STANDING;
		s.bossVnum = boss.vnum;
		s.map = (DWORD)spot.map;
		s.x = ch->GetX();
		s.y = ch->GetY();
		s.area = spot.area;
		s.channel = g_bChannel;
		s.spawnedAt = now;
		s.fightEnd = now + (DWORD)s_cfg.fightMinutes * 60;
		s.endedAt = 0;
		s.nextAt = 0;
		s.hpMax = (DWORD)ch->GetMaxHP();
		s.hpPct = 100;
		SaveState();
		s_dwNextReminder = get_dword_time() + REMINDER_MS;

		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "Boss Swiata %s terroryzuje: %s (kanal %d)! Pokonajcie go w ciagu %d min - nagrody za ranking obrazen.",
				BossName(boss.vnum), spot.area.c_str(), (int)g_bChannel, s_cfg.fightMinutes);
		BroadcastNotice(msg, CHAT_TYPE_BIG_NOTICE);
		BroadcastNotice(msg);
		sys_log(0, "WORLDBOSS: spawned serial=%u %s (%u) map=%ld spot=%ld,%ld at=%ld,%ld hp=%d (%d%%, falls %u) fight until %u",
				s.serial, BossName(boss.vnum), boss.vnum, spot.map, spot.x, spot.y, s.x, s.y, ch->GetMaxHP(), pct, s.falls, s.fightEnd);
		return true;
	}

	// ------------------------------------------------------------ the men

	void CallMen(LPCHARACTER boss)
	{
		const TBoss* b = FindBoss(boss->GetRaceNum());
		if (!b || b->men.empty())
			return;
		int spawned = 0;
		for (int g = 0; g < s_cfg.groups; ++g)
		{
			// a group a step around the boss
			const int ang = g * 360 / std::max(1, s_cfg.groups) + number(0, 30);
			const long gx = boss->GetX() + (long)(MEN_SPREAD * cos(ang * M_PI / 180.0));
			const long gy = boss->GetY() + (long)(MEN_SPREAD * sin(ang * M_PI / 180.0));
			for (size_t i = 0; i < b->men.size(); ++i)
			{
				LPCHARACTER m = CHARACTER_MANAGER::instance().SpawnMobRange(b->men[i], boss->GetMapIndex(), gx - 300, gy - 300,
						gx + 300, gy + 300, true, true, true);
				if (m)
				{
					s_vecMen.push_back((DWORD)m->GetVID());
					++spawned;
				}
			}
		}
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "%s wzywa swoich sluzacych!", BossName(boss->GetRaceNum()));
		SendNoticeMap(msg, boss->GetMapIndex(), false);
		sys_log(0, "WORLDBOSS: call %d at %d%% - %d men", s_iCalls, boss->GetMaxHP() > 0 ? (int)((long long)boss->GetHP() * 100 / boss->GetMaxHP()) : 0, spawned);
	}

	// ------------------------------------------------------------ the map icon

	// MT2009_PLUS_WORLDBOSS_ICON_V1: "Dodaj ikonkę bossa na mapie" - the players
	// on the boss's map learn where he stands (root/uiworldboss.py draws his
	// icon on the atlas and the minimap); "WB unmark" when he is gone.
	void SendMarks(LPCHARACTER boss)
	{
		long lx = boss->GetX(), ly = boss->GetY();
		const LPSECTREE_MAP map = SECTREE_MANAGER::instance().GetMap(boss->GetMapIndex());
		if (map)
		{
			lx -= map->m_setting.iBaseX;
			ly -= map->m_setting.iBaseY;
		}
		const DESC_MANAGER::DESC_SET& descs = DESC_MANAGER::instance().GetClientSet();
		for (DESC_MANAGER::DESC_SET::const_iterator d = descs.begin(); d != descs.end(); ++d)
		{
			LPCHARACTER ch = (*d)->GetCharacter();
			if (IsPlayer(ch) && ch->GetMapIndex() == boss->GetMapIndex())
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB mark %ld %ld %ld %ld %u", boss->GetX(), boss->GetY(), lx, ly,
						(unsigned)boss->GetRaceNum());
		}
	}

	void SendUnmark(long mapIndex)
	{
		const DESC_MANAGER::DESC_SET& descs = DESC_MANAGER::instance().GetClientSet();
		for (DESC_MANAGER::DESC_SET::const_iterator d = descs.begin(); d != descs.end(); ++d)
		{
			LPCHARACTER ch = (*d)->GetCharacter();
			if (IsPlayer(ch) && ch->GetMapIndex() == mapIndex)
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB unmark");
		}
	}

	// ------------------------------------------------------------ the end

	void BossEscaped(DWORD now, const char* why)
	{
		LPCHARACTER boss = Boss();
		const DWORD vnum = s_state.bossVnum;
		if (boss && !boss->IsDead())
			M2_DESTROY_CHARACTER(boss);
		DestroyMen();
		s_dwBossVID = 0;
		s_mapDamage.clear();
		SendUnmark((long)s_state.map);	// MT2009_PLUS_WORLDBOSS_ICON_V1
		s_state.state = ST_ESCAPED;
		s_state.endedAt = now;
		PlanNext(now);
		SaveState();
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "Boss Swiata %s uciekl! Licznik obrazen zostal zresetowany - nikt nie otrzyma nagrody.", BossName(vnum));
		BroadcastNotice(msg);
		sys_log(0, "WORLDBOSS: serial=%u %u escaped (%s)", s_state.serial, vnum, why);
	}

	struct TRanked
	{
		DWORD pid;
		TDamage d;
	};

	bool ByDamage(const TRanked& a, const TRanked& b)
	{
		if (a.d.damage != b.d.damage)
			return a.d.damage > b.d.damage;
		return a.pid < b.pid;
	}

	const TTier* TierOf(int pos)
	{
		for (size_t i = 0; i < s_data.tiers.size(); ++i)
		{
			const TTier& t = s_data.tiers[i];
			if (pos >= t.first && (t.last == 0 || pos <= t.last))
				return &t;
		}
		return NULL;
	}

	void Fell(DWORD now)
	{
		const DWORD vnum = s_state.bossVnum;
		const long map = (long)s_state.map;
		DestroyMen();
		s_dwBossVID = 0;
		SendUnmark(map);	// MT2009_PLUS_WORLDBOSS_ICON_V1
		// the characters (players and bots alike - MT2009_PLUS_WORLDBOSS_ICON_V1) still on the map with the least
		// damage or more
		std::vector<TRanked> ranked;
		int below = 0;
		for (std::map<DWORD, TDamage>::const_iterator it = s_mapDamage.begin(); it != s_mapDamage.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || ch->GetMapIndex() != map)
				continue;
			if (it->second.damage < (long long)s_cfg.minDamage)
			{
				++below;
				if (IsPlayer(ch))
					ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: zadales %lld obrazen - za malo na nagrode (potrzeba %u).",
							it->second.damage, s_cfg.minDamage);
				continue;
			}
			TRanked r;
			r.pid = it->first;
			r.d = it->second;
			ranked.push_back(r);
		}
		std::sort(ranked.begin(), ranked.end(), ByDamage);
		const DWORD day = Today();
		for (size_t i = 0; i < ranked.size(); ++i)
		{
			const int pos = (int)i + 1;
			const TTier* t = TierOf(pos);
			const int tier = t ? t->n : 0;
			const TDamage& d = ranked[i].d;
			const std::string name = Escape(d.name), guild = Escape(d.guildName);
			Query("REPLACE INTO player.worldboss_damage (serial, pid, pos, tier, damage, name, guild_id, guild_name, empire, level, "
					"boss_vnum, at) VALUES (%u, %u, %d, %d, %lld, '%s', %u, '%s', %u, %u, %u, %u)",
					s_state.serial, ranked[i].pid, pos, tier, d.damage, name.c_str(), d.guildId, guild.c_str(),
					(unsigned)d.empire, (unsigned)d.level, vnum, now);
			if (t)
			{
				Query("INSERT INTO player.worldboss_reward (pid, kind, serial, season, tier, pos, items, buff_drop, created) VALUES "
						"(%u, %d, %u, %u, %d, %d, '%s', %d, %u)", ranked[i].pid, KIND_TIER, s_state.serial, s_state.season, tier, pos,
						FormatItems(t->items).c_str(), t->drop, now);
				if (t->points > 0)
					Query("INSERT INTO player.worldboss_points (season, pid, guild_id, name, guild_name, empire, points) VALUES "
							"(%u, %u, %u, '%s', '%s', %u, %d) ON DUPLICATE KEY UPDATE points = points + %d, name = VALUES(name), "
							"guild_name = VALUES(guild_name), empire = VALUES(empire)",
							s_state.season, ranked[i].pid, d.guildId, name.c_str(), guild.c_str(), (unsigned)d.empire, t->points, t->points);
			}
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(ranked[i].pid);
			if (IsPlayer(ch))
				ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: %d. miejsce, poziom lupu %s (%lld obrazen, +%d pkt rangi). Odbierz nagrode w oknie Bossa Swiata, zanim pojawi sie kolejny boss.",
						pos, TierName(tier), d.damage, t ? t->points : 0);
		}
		// "Pokonaj Bossa Świata": once a day, mission_damage to a defeated boss
		int missions = 0;
		for (std::map<DWORD, TDamage>::const_iterator it = s_mapDamage.begin(); it != s_mapDamage.end(); ++it)
		{
			if (it->second.damage < (long long)s_cfg.missionDamage || !s_cfg.missionDamage)
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || ch->GetMapIndex() != map)
				continue;
			std::unique_ptr<SQLMsg> m(Query("INSERT INTO player.worldboss_reward (pid, kind, serial, season, buff_attack, created, day) "
					"SELECT %u, %d, %u, %u, %d, %u, %u FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM player.worldboss_reward "
					"WHERE pid = %u AND kind = %d AND day = %u)", it->first, KIND_MISSION, s_state.serial, s_state.season,
					s_data.missionPct, now, day, it->first, KIND_MISSION, day));
			if (Ok(m) && m->Get()->uiAffectedRows == 1)
			{
				++missions;
				if (IsPlayer(ch))
					ch->ChatPacket(CHAT_TYPE_INFO, "Misja \"Pokonaj Bossa Swiata\" wykonana - premia +%d%% wartosci ataku na %d h czeka w oknie Bossa Swiata.",
							s_data.missionPct, s_data.missionSeconds / 3600);
			}
		}
		s_mapDamage.clear();
		s_state.state = ST_DEFEATED;
		s_state.endedAt = now;
		++s_state.falls;
		s_state.hpPct = 0;
		PlanNext(now);
		SaveState();
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "Boss Swiata %s zostal pokonany! Nagrody (%d postaci w rankingu) czekaja w oknie Bossa Swiata - odbierzcie je przed pojawieniem sie kolejnego bossa.",
				BossName(vnum), (int)ranked.size());
		BroadcastNotice(msg);
		sys_log(0, "WORLDBOSS: serial=%u %u defeated - ranked %d, below the least %d, missions %d", s_state.serial, vnum,
				(int)ranked.size(), below, missions);
	}

	// ------------------------------------------------------------ the season

	void EndSeason(DWORD now)
	{
		const DWORD season = s_state.season;
		int given = 0;
		for (int empire = 1; empire <= 3; ++empire)
		{
			// the characters: points of every guild they earned them in
			std::unique_ptr<SQLMsg> m(Query("SELECT pid, SUM(points) AS p FROM player.worldboss_points WHERE season = %u AND empire = %d "
					"GROUP BY pid HAVING p > 0 ORDER BY p DESC, pid ASC LIMIT 100", season, empire));
			if (Ok(m) && m->Get()->pSQLResult)
			{
				MYSQL_ROW r;
				int pos = 0;
				while ((r = mysql_fetch_row(m->Get()->pSQLResult)))
				{
					++pos;
					for (size_t i = 0; i < s_data.seasonChar.size(); ++i)
					{
						const TPrize& p = s_data.seasonChar[i];
						if (pos < p.first || pos > p.last)
							continue;
						Query("INSERT INTO player.worldboss_reward (pid, kind, season, pos, items, created) VALUES (%u, %d, %u, %d, '%s', %u)",
								Num(r[0]), KIND_SEASON_CHAR, season, pos, FormatItems(p.items).c_str(), now);
						++given;
					}
				}
			}
			// the guilds: every member now in the guild who earned it a point
			std::unique_ptr<SQLMsg> g(Query("SELECT guild_id, SUM(points) AS p FROM player.worldboss_points WHERE season = %u AND empire = %d "
					"AND guild_id > 0 GROUP BY guild_id HAVING p > 0 ORDER BY p DESC, guild_id ASC LIMIT 10", season, empire));
			if (Ok(g) && g->Get()->pSQLResult)
			{
				MYSQL_ROW r;
				int pos = 0;
				std::vector<std::pair<DWORD, int> > guilds;
				while ((r = mysql_fetch_row(g->Get()->pSQLResult)))
					guilds.push_back(std::make_pair(Num(r[0]), ++pos));
				for (size_t k = 0; k < guilds.size(); ++k)
					for (size_t i = 0; i < s_data.seasonGuild.size(); ++i)
					{
						const TPrize& p = s_data.seasonGuild[i];
						if (guilds[k].second < p.first || guilds[k].second > p.last)
							continue;
						std::unique_ptr<SQLMsg> ins(Query("INSERT INTO player.worldboss_reward (pid, kind, season, pos, items, created) "
								"SELECT p.pid, %d, %u, %d, '%s', %u FROM player.worldboss_points p JOIN player.guild_member gm "
								"ON gm.pid = p.pid AND gm.guild_id = p.guild_id WHERE p.season = %u AND p.guild_id = %u AND p.points > 0",
								KIND_SEASON_GUILD, season, guilds[k].second, FormatItems(p.items).c_str(), now, season, guilds[k].first));
						if (Ok(ins))
							given += (int)ins->Get()->uiAffectedRows;
					}
			}
		}
		s_state.season = season + 1;
		s_state.seasonEnd = now + (DWORD)s_cfg.seasonWeeks * 7 * 24 * 3600;
		SaveState();
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "Sezon Bossa Swiata %u zakonczony! Nagrody rankingowe (%d) czekaja w oknie Bossa Swiata. Zaczyna sie sezon %u.",
				season, given, s_state.season);
		BroadcastNotice(msg);
		sys_log(0, "WORLDBOSS: season %u ended - %d prize rows; season %u until %u", season, given, s_state.season, s_state.seasonEnd);
	}

	// ------------------------------------------------------------ the owner's second

	void SyncEventFlag()
	{
		int want = 0;
		if (s_cfg.mode == 1)
			want = 1;
		else if (s_cfg.mode == 2)
			want = s_aPlayerBotEventStatus[playerbot_events::KIND_WORLDBOSS].active ? 1 : 0;
		if (quest::CQuestManager::instance().GetEventFlag(EVENT_FLAG) != want)
			quest::CQuestManager::instance().RequestSetEventFlag(EVENT_FLAG, want);
	}

	void OwnerSecond(DWORD now)
	{
		TState& s = s_state;
		if (!s.seasonEnd)
		{
			s.seasonEnd = now + (DWORD)s_cfg.seasonWeeks * 7 * 24 * 3600;
			SaveState();
		}
		if ((s.seasonEnd && now >= s.seasonEnd) || (s_cfg.seasonEndNow && s_cfg.seasonEndNow <= now &&
				s_cfg.seasonEndNow > s.seasonEnd - (DWORD)s_cfg.seasonWeeks * 7 * 24 * 3600))
		{
			Query("UPDATE player.worldboss_config SET season_end_now = 0 WHERE id = 1");
			s_cfg.seasonEndNow = 0;
			EndSeason(now);
		}

		if (s.state == ST_STANDING)
		{
			LPCHARACTER boss = Boss();
			if (!s_dwBossVID && s.serial)
			{
				// a restart while he stood: he is gone with the old core
				sys_log(0, "WORLDBOSS: serial=%u was standing when this core started - counted as escaped", s.serial);
				BossEscaped(now, "restart");
				return;
			}
			if (s_bBossFell || (boss && boss->IsDead()))
			{
				Fell(now);
				return;
			}
			if (!boss)
			{
				BossEscaped(now, "vanished");
				return;
			}
			if (now >= s.fightEnd || (s_cfg.escapeNow && s_cfg.escapeNow <= now && s_cfg.escapeNow >= s.spawnedAt))
			{
				if (s_cfg.escapeNow)
				{
					Query("UPDATE player.worldboss_config SET escape_now = 0 WHERE id = 1");
					s_cfg.escapeNow = 0;
				}
				BossEscaped(now, now >= s.fightEnd ? "time" : "operator");
				return;
			}
			const int pct = boss->GetMaxHP() > 0 ? (int)((long long)boss->GetHP() * 100 / boss->GetMaxHP()) : 100;
			s.hpPct = (DWORD)std::max(0, pct);
			static const int CALL_AT[3] = { 75, 50, 25 };
			while (s_iCalls < 3 && pct <= CALL_AT[s_iCalls])
			{
				++s_iCalls;
				CallMen(boss);
			}
			// a character who left the map lost what he dealt
			if (get_dword_time() >= s_dwNextMapCheck)
			{
				s_dwNextMapCheck = get_dword_time() + MAP_CHECK_MS;
				for (std::map<DWORD, TDamage>::iterator it = s_mapDamage.begin(); it != s_mapDamage.end();)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
					if (!ch || ch->GetMapIndex() != boss->GetMapIndex())
						s_mapDamage.erase(it++);
					else
						++it;
				}
			}
			if (get_dword_time() >= s_dwNextMark)
			{
				s_dwNextMark = get_dword_time() + MARK_MS;
				SendMarks(boss);	// MT2009_PLUS_WORLDBOSS_ICON_V1
			}
			if (get_dword_time() >= s_dwNextReminder)
			{
				s_dwNextReminder = get_dword_time() + REMINDER_MS;
				char msg[CHAT_MAX_LEN + 1];
				snprintf(msg, sizeof(msg), "Boss Swiata %s wciaz terroryzuje: %s (kanal %d) - ma %d%% zycia, ucieknie za %d min.",
						BossName(s.bossVnum), s.area.c_str(), (int)g_bChannel, pct, (int)(s.fightEnd - now) / 60);
				BroadcastNotice(msg);
			}
			if (get_dword_time() >= s_dwNextSave)
				SaveState();
			return;
		}

		// waiting: the operator's "next boss at" (the panel, "/worldboss spawn" - also while the event is off), or
		// the drawn break
		if (s_cfg.forceAt && s_cfg.forceAt != s.nextAt && s_cfg.forceAt > s.endedAt)
		{
			s.nextAt = s_cfg.forceAt;
			SaveState();
			sys_log(0, "WORLDBOSS: the operator set the next boss at %u", s.nextAt);
		}
		if (!EventOn() && !(s_cfg.forceAt && s_cfg.forceAt <= now))
			return;
		if (!s.nextAt)
		{
			// the first after the event began: a short wait
			s.nextAt = now + (DWORD)number(1, std::max(1, s_cfg.breakMin / 2)) * 60;
			SaveState();
			sys_log(0, "WORLDBOSS: the event runs - the first boss at %u", s.nextAt);
		}
		// not in the first minutes of a core's life: the world (and its bots) comes up first
		static const DWORD s_dwBoot = get_dword_time();
		if (now >= s.nextAt && get_dword_time() - s_dwBoot >= BOOT_DELAY_MS)
		{
			const bool forced = s_cfg.forceAt && s_cfg.forceAt <= now;
			if (!Spawn(now, forced ? (int)s_cfg.forceBoss : 0, forced ? (long)s_cfg.forceMap : 0))
			{
				s.nextAt = now + 300;
				SaveState();
			}
			if (forced)
			{
				Query("UPDATE player.worldboss_config SET force_at = 0, force_boss = 0, force_map = 0 WHERE id = 1");
				s_cfg.forceAt = s_cfg.forceBoss = s_cfg.forceMap = 0;
			}
		}
	}

	// ------------------------------------------------------------ to the client

	void SendInfo(LPCHARACTER ch)
	{
		const TState& s = s_state;
		const DWORD now = (DWORD)time(NULL);
		long long mine = 0;
		int myTier = 0, myPos = 0;
		if (s.state == ST_STANDING && s_bOwner)
		{
			std::map<DWORD, TDamage>::const_iterator it = s_mapDamage.find(ch->GetPlayerID());
			if (it != s_mapDamage.end())
				mine = it->second.damage;
		}
		// my place on the last defeated boss (the serial of the state, or the one before a new spawn)
		{
			std::unique_ptr<SQLMsg> m(Query("SELECT pos, tier, damage FROM player.worldboss_damage WHERE pid = %u AND serial = "
					"(SELECT MAX(serial) FROM player.worldboss_damage)", ch->GetPlayerID()));
			if (Ok(m) && m->Get()->pSQLResult && m->Get()->uiNumRows)
			{
				MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
				if (r)
				{
					myPos = (int)Num(r[0]);
					myTier = (int)Num(r[1]);
					if (s.state != ST_STANDING)
						mine = (long long)strtoll(r[2] ? r[2] : "0", NULL, 10);
				}
			}
		}
		int waiting = 0;
		{
			std::unique_ptr<SQLMsg> m(Query("SELECT COUNT(*) FROM player.worldboss_reward WHERE pid = %u AND state = 0", ch->GetPlayerID()));
			if (Ok(m) && m->Get()->pSQLResult)
			{
				MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
				if (r)
					waiting = (int)Num(r[0]);
			}
		}
		DWORD points = 0;
		{
			std::unique_ptr<SQLMsg> m(Query("SELECT COALESCE(SUM(points), 0) FROM player.worldboss_points WHERE season = %u AND pid = %u",
					s.season, ch->GetPlayerID()));
			if (Ok(m) && m->Get()->pSQLResult)
			{
				MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
				if (r)
					points = Num(r[0]);
			}
		}
		const int fightLeft = s.state == ST_STANDING && s.fightEnd > now ? (int)(s.fightEnd - now) : 0;
		const int nextLeft = s.state != ST_STANDING && s.nextAt > now ? (int)(s.nextAt - now) : 0;
		const bool on = s_cfg.mode == 1 || (s_cfg.mode == 2 && InGameEventIsActive("worldboss"));
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB info %u %u %u %d %d %lld %u %d %d %d %u %d %u", s.state, s.bossVnum, s.map,
				fightLeft, nextLeft, mine, s_cfg.minDamage, waiting, myTier, myPos, points, on ? 1 : 0, s.channel ? s.channel : (DWORD)s_cfg.channel);
		if (s.bossVnum)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WB where %u %s", s.map, s.area.c_str());
	}

	void SendRanking(LPCHARACTER ch)
	{
		DWORD serial = 0, vnum = 0;
		{
			std::unique_ptr<SQLMsg> m(Query("SELECT serial, boss_vnum FROM player.worldboss_damage ORDER BY serial DESC LIMIT 1"));
			if (Ok(m) && m->Get()->pSQLResult && m->Get()->uiNumRows)
			{
				MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
				if (r)
				{
					serial = Num(r[0]);
					vnum = Num(r[1]);
				}
			}
		}
		std::unique_ptr<SQLMsg> m(Query("SELECT pos, tier, empire, damage, name, guild_name, pid FROM player.worldboss_damage WHERE serial = %u "
				"ORDER BY pos LIMIT %d", serial, RANK_LIST_MAX));
		const int count = Ok(m) && m->Get()->pSQLResult ? (int)m->Get()->uiNumRows : 0;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB rbegin %u %u %d", serial, vnum, count);
		bool meSent = false;
		if (count)
		{
			MYSQL_ROW r;
			while ((r = mysql_fetch_row(m->Get()->pSQLResult)))
			{
				const std::string name = Token(r[4] ? r[4] : ""), guild = Token(r[5] ? r[5] : "");
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB r %s %s %s %s %s %s", r[0], r[1], r[2], r[3], name.c_str(), guild.c_str());
				if (Num(r[6]) == ch->GetPlayerID())
				{
					ch->ChatPacket(CHAT_TYPE_COMMAND, "WB rme %s %s %s %s %s %s", r[0], r[1], r[2], r[3], name.c_str(), guild.c_str());
					meSent = true;
				}
			}
		}
		if (!meSent)
		{
			std::unique_ptr<SQLMsg> me(Query("SELECT pos, tier, empire, damage, name, guild_name FROM player.worldboss_damage WHERE serial = %u AND pid = %u",
					serial, ch->GetPlayerID()));
			MYSQL_ROW r = Ok(me) && me->Get()->pSQLResult ? mysql_fetch_row(me->Get()->pSQLResult) : NULL;
			if (r)
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB rme %s %s %s %s %s %s", r[0], r[1], r[2], r[3], Token(r[4] ? r[4] : "").c_str(),
						Token(r[5] ? r[5] : "").c_str());
			else
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB rme 0 0 %u 0 %s %s", (unsigned)ch->GetEmpire(), Token(ch->GetName()).c_str(),
						Token(ch->GetGuild() ? ch->GetGuild()->GetName() : "").c_str());
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB rend");
	}

	void SendSeason(LPCHARACTER ch, int empire)
	{
		if (empire < 1 || empire > 3)
			empire = ch->GetEmpire();
		const DWORD now = (DWORD)time(NULL);
		const DWORD season = s_state.season;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB sbegin %u %d %d", season, s_state.seasonEnd > now ? (int)(s_state.seasonEnd - now) : 0, empire);
		std::unique_ptr<SQLMsg> m(Query("SELECT pid, SUM(points) AS p, MAX(name), MAX(guild_name) FROM player.worldboss_points "
				"WHERE season = %u AND empire = %d GROUP BY pid HAVING p > 0 ORDER BY p DESC, pid ASC LIMIT 25", season, empire));
		if (Ok(m) && m->Get()->pSQLResult)
		{
			MYSQL_ROW r;
			int pos = 0;
			while ((r = mysql_fetch_row(m->Get()->pSQLResult)))
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB s %d %s %s %s", ++pos, r[1], Token(r[2] ? r[2] : "").c_str(), Token(r[3] ? r[3] : "").c_str());
		}
		std::unique_ptr<SQLMsg> g(Query("SELECT guild_id, SUM(points) AS p, MAX(guild_name) FROM player.worldboss_points WHERE season = %u "
				"AND empire = %d AND guild_id > 0 GROUP BY guild_id HAVING p > 0 ORDER BY p DESC, guild_id ASC LIMIT 3", season, empire));
		if (Ok(g) && g->Get()->pSQLResult)
		{
			MYSQL_ROW r;
			int pos = 0;
			while ((r = mysql_fetch_row(g->Get()->pSQLResult)))
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WB sg %d %s %s", ++pos, r[1], Token(r[2] ? r[2] : "").c_str());
		}
		// my place in my kingdom
		std::unique_ptr<SQLMsg> me(Query("SELECT COALESCE(SUM(points), 0) FROM player.worldboss_points WHERE season = %u AND pid = %u",
				season, ch->GetPlayerID()));
		DWORD mine = 0;
		MYSQL_ROW r = Ok(me) && me->Get()->pSQLResult ? mysql_fetch_row(me->Get()->pSQLResult) : NULL;
		if (r)
			mine = Num(r[0]);
		int myPos = 0;
		if (mine && ch->GetEmpire() == empire)
		{
			std::unique_ptr<SQLMsg> above(Query("SELECT COUNT(*) FROM (SELECT pid, SUM(points) AS p FROM player.worldboss_points WHERE season = %u "
					"AND empire = %d GROUP BY pid HAVING p > %u) t", season, empire, mine));
			MYSQL_ROW a = Ok(above) && above->Get()->pSQLResult ? mysql_fetch_row(above->Get()->pSQLResult) : NULL;
			if (a)
				myPos = (int)Num(a[0]) + 1;
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB sme %d %u", myPos, mine);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WB send");
	}

	// ------------------------------------------------------------ the claim

	void GiveItems(LPCHARACTER ch, const std::vector<TItem>& items)
	{
		const DWORD now = (DWORD)time(NULL);
		for (size_t i = 0; i < items.size(); ++i)
		{
			LPITEM item = ch->AutoGiveItem(items[i].vnum, (ITEM_COUNT)items[i].count);
			if (!item || items[i].days <= 0 || !item->GetProto())
				continue;
			// the wiki's "(60d)" on an item whose time runs from now
			for (int l = 0; l < ITEM_LIMIT_MAX_NUM; ++l)
				if (item->GetProto()->aLimits[l].bType == LIMIT_REAL_TIME)
				{
					item->SetSocket(0, (long)(now + (DWORD)items[i].days * 24 * 3600));
					break;
				}
		}
	}

	// bot: MT2009_PLUS_WORLDBOSS_ICON_V1 - a bot's rewards, given by BotClaims (no chat, no window lines).
	void Claim(LPCHARACTER ch, bool bot = false)
	{
		if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen())
		{
			if (!bot)
				ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: zamknij inne okna (handel, sklep, magazyn), zanim odbierzesz nagrode.");
			return;
		}
		std::unique_ptr<SQLMsg> m(Query("SELECT id, kind, tier, pos, items, buff_drop, buff_attack, season FROM player.worldboss_reward "
				"WHERE pid = %u AND state = 0 ORDER BY id LIMIT 20", ch->GetPlayerID()));
		if (!Ok(m) || !m->Get()->pSQLResult || !m->Get()->uiNumRows)
		{
			if (!bot)
				ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: nie masz nagrody do odebrania.");
			return;
		}
		struct TRow { DWORD id; int kind, tier, pos, drop, attack; DWORD season; std::vector<TItem> items; };
		std::vector<TRow> rows;
		int needSlots = 0;
		MYSQL_ROW r;
		while ((r = mysql_fetch_row(m->Get()->pSQLResult)))
		{
			TRow t;
			t.id = Num(r[0]);
			t.kind = (int)Num(r[1]);
			t.tier = (int)Num(r[2]);
			t.pos = (int)Num(r[3]);
			ParseItems(r[4] ? r[4] : "", t.items);
			t.drop = (int)Num(r[5]);
			t.attack = (int)Num(r[6]);
			t.season = Num(r[7]);
			needSlots += (int)t.items.size();
			rows.push_back(t);
		}
		if (needSlots > 0 && ch->GetEmptyInventory(1) < 0)
		{
			if (!bot)
				ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: brak miejsca w ekwipunku - zwolnij miejsce i sprobuj ponownie.");
			return;
		}
		int given = 0;
		for (size_t i = 0; i < rows.size(); ++i)
		{
			const TRow& t = rows[i];
			std::unique_ptr<SQLMsg> u(Query("UPDATE player.worldboss_reward SET state = 1, taken_at = UNIX_TIMESTAMP() WHERE id = %u AND state = 0", t.id));
			if (!Ok(u) || u->Get()->uiAffectedRows != 1)
				continue;
			GiveItems(ch, t.items);
			if (t.drop > 0)
			{
				int seconds = 2 * 3600;
				for (size_t k = 0; k < s_data.tiers.size(); ++k)
					if (s_data.tiers[k].n == t.tier && s_data.tiers[k].seconds > 0)
						seconds = s_data.tiers[k].seconds;
				ch->RemoveAffect(AFFECT_DROP);
				ch->AddAffect(AFFECT_DROP, POINT_NONE, t.drop, AFF_NONE, seconds, 0, true);
			}
			if (t.attack > 0)
			{
				ch->RemoveAffect(AFFECT_ATTACK);
				ch->AddAffect(AFFECT_ATTACK, POINT_MALL_ATTBONUS, t.attack, AFF_NONE, s_data.missionSeconds, 0, true);
			}
			switch (bot ? -1 : t.kind)
			{
				case KIND_TIER:
					ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: odebrano nagrode za %d. miejsce (poziom lupu %s)%s.", t.pos, TierName(t.tier),
							t.drop > 0 ? " i premie do dropu" : "");
					break;
				case KIND_MISSION:
					ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: premia misji - wartosc ataku +%d%% na %d h.", t.attack, s_data.missionSeconds / 3600);
					break;
				case KIND_SEASON_CHAR:
					ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: nagroda sezonu %u za %d. miejsce w rankingu postaci.", t.season, t.pos);
					break;
				case KIND_SEASON_GUILD:
					ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata: nagroda sezonu %u za %d. miejsce Twojej gildii.", t.season, t.pos);
					break;
			}
			sys_log(0, "WORLDBOSS: reward id=%u kind=%d tier=%d pos=%d items=%s drop=%d attack=%d given to %s%s (%u)", t.id, t.kind, t.tier,
					t.pos, FormatItems(t.items).c_str(), t.drop, t.attack, bot ? "the bot " : "", ch->GetName(), ch->GetPlayerID());
			++given;
		}
		if (bot)
			return;
		if (given)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WB claimok");
		SendInfo(ch);
	}

	// MT2009_PLUS_WORLDBOSS_ICON_V1: "Nagrody również dla botów" - the waiting
	// rewards of this core's bots (a loot tier, the mission, the season's
	// prizes) go straight to them; one waiting for a bag with room waits as a
	// player's does (a loot tier until the next boss).
	void BotClaims()
	{
		std::unique_ptr<SQLMsg> m(Query("SELECT DISTINCT pid FROM player.worldboss_reward WHERE state = 0 LIMIT 2000"));
		if (!Ok(m) || !m->Get()->pSQLResult)
			return;
		std::vector<DWORD> pids;
		MYSQL_ROW r;
		while ((r = mysql_fetch_row(m->Get()->pSQLResult)))
			pids.push_back(Num(r[0]));
		for (size_t i = 0; i < pids.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
			if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded() || ch->IsDead())
				continue;
			Claim(ch, true);
		}
	}

	bool TooSoon(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
		if (last && now - last < COMMAND_GAP_MS)
			return true;
		last = now;
		return false;
	}
}

// ------------------------------------------------------------ the engine's hooks

// char_battle.cpp CHARACTER::Damage (server-patches/worldboss): a blow that took health.
void WorldBossOnDamage(LPCHARACTER victim, LPCHARACTER attacker, int dam)
{
	using namespace mt2009_worldboss;
	if (!s_dwBossVID || !victim || (DWORD)victim->GetVID() != s_dwBossVID || dam <= 0)
		return;
	// MT2009_PLUS_WORLDBOSS_ICON_V1: a bot's blow counts as a player's ("W rankingach również boty")
	if (!attacker || !attacker->IsPC() || !attacker->GetDesc() || attacker->GetLevel() < s_cfg.minLevel ||
			attacker->GetMapIndex() != victim->GetMapIndex())
		return;
	TDamage& d = s_mapDamage[attacker->GetPlayerID()];
	d.damage += dam;
	d.name = attacker->GetName();
	d.empire = attacker->GetEmpire();
	d.level = (BYTE)attacker->GetLevel();
	CGuild* g = attacker->GetGuild();
	d.guildId = g ? g->GetID() : 0;
	d.guildName = g ? g->GetName() : "";
}

// char_battle.cpp CHARACTER::Reward: the event's monsters drop nothing; the boss's
// death is noted here (the owner's next second ranks it).
bool WorldBossNoDrop(LPCHARACTER victim)
{
	using namespace mt2009_worldboss;
	if (!victim || victim->IsPC())
		return false;
	const DWORD race = victim->GetRaceNum();
	if (race < 4420 || race > 4479)
		return false;
	if (s_dwBossVID && (DWORD)victim->GetVID() == s_dwBossVID)
		s_bBossFell = true;
	return FindBoss(race) || IsMan(race);
}

// item_manager.cpp CreateDropItem: the loot tier's drop buff.
int WorldBossDropBonus(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return 0;
	CAffect* a = ch->FindAffect(mt2009_worldboss::AFFECT_DROP);
	return a ? (int)a->lApplyValue : 0;
}

// playerbot_boss_raid.h: the bots raid the event's bosses only when the operator lets them.
bool WorldBossBotsAllowed()
{
	return mt2009_worldboss::s_cfg.bots != 0;
}

bool WorldBossStandsOn(DWORD race, long lMap)
{
	using namespace mt2009_worldboss;
	return s_dwBossVID && s_state.state == ST_STANDING && s_state.bossVnum == race && (long)s_state.map == lMap;
}

bool IsWorldBossEventRace(DWORD race)
{
	return mt2009_worldboss::FindBoss(race) != NULL;
}

// playerbot_events.h, once a pass (every core).
void WorldBossTick(DWORD dwNow)
{
	using namespace mt2009_worldboss;
	if (dwNow < s_dwNextSecond)
		return;
	s_dwNextSecond = dwNow + 1000;
	if (!s_data.loaded)
	{
		static DWORD s_dwNextLoad = 0;
		if (dwNow < s_dwNextLoad)
			return;
		s_dwNextLoad = dwNow + 10 * 60 * 1000;
		if (!LoadData())
			return;
	}
	if (dwNow >= s_dwNextConfig)
	{
		s_dwNextConfig = dwNow + CONFIG_RELOAD_MS;
		ReadConfig();
		const bool owner = s_bConfigRead && IsOwner();
		if (owner != s_bOwner || !s_bOwnerKnown)
		{
			s_bOwnerKnown = true;
			s_bOwner = owner;
			sys_log(0, "WORLDBOSS: this core %s the boss (channel %d, config channel %d, mode %d)", owner ? "runs" : "does not run",
					(int)g_bChannel, s_cfg.channel, s_cfg.mode);
			if (owner)
			{
				ReadState();
				DestroyStrays(0);
			}
		}
		if (s_bOwner)
			SyncEventFlag();
	}
	// MT2009_PLUS_WORLDBOSS_ICON_V1: the bots' rewards, on every core (wherever the bot stands)
	if (dwNow >= s_dwNextBotClaim && !g_bAuthServer)
	{
		s_dwNextBotClaim = dwNow + BOT_CLAIM_MS;
		BotClaims();
	}
	if (!s_bOwner)
	{
		if (dwNow >= s_dwNextStateRead)
		{
			s_dwNextStateRead = dwNow + STATE_READ_MS;
			ReadState();
		}
		return;
	}
	if (!s_bStateRead && !ReadState())
		return;
	OwnerSecond((DWORD)time(NULL));
}

// "/worldboss" (cmd.cpp, server-patches/worldboss).
void WorldBossCommand(LPCHARACTER ch, const char* argument)
{
	using namespace mt2009_worldboss;
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	char sub[32], arg[32], arg2[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	rest = one_argument(rest, arg, sizeof(arg));
	one_argument(rest, arg2, sizeof(arg2));
	const bool gm = ch->GetGMLevel() >= GM_HIGH_WIZARD;
	if (!gm && TooSoon(ch))
		return;
	if (!s_data.loaded)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Boss Swiata jest chwilowo niedostepny.");
		return;
	}
	if (!s_bOwner && get_dword_time() + STATE_READ_MS - 1000 > s_dwNextStateRead)
	{
		ReadState();
		s_dwNextStateRead = get_dword_time() + STATE_READ_MS;
	}
	if (!*sub || !strcmp(sub, "info"))
		SendInfo(ch);
	else if (!strcmp(sub, "ranking"))
		SendRanking(ch);
	else if (!strcmp(sub, "sezon"))
		SendSeason(ch, (int)Num(arg));
	else if (!strcmp(sub, "odbierz"))
		Claim(ch);
	else if (gm && !strcmp(sub, "spawn"))
	{
		// "/worldboss spawn [boss 1-6] [map]": through the config, so the core that runs the boss spawns it
		Query("UPDATE player.worldboss_config SET force_at = UNIX_TIMESTAMP(), force_boss = %u, force_map = %u WHERE id = 1", Num(arg), Num(arg2));
		s_dwNextConfig = 0;
		ch->ChatPacket(CHAT_TYPE_INFO, "WORLDBOSS: the next boss now (boss %u, map %u; 0 = drawn) - the core of channel %d spawns it within 30 s.",
				Num(arg), Num(arg2), s_cfg.channel);
	}
	else if (gm && !strcmp(sub, "ucieczka"))
	{
		Query("UPDATE player.worldboss_config SET escape_now = UNIX_TIMESTAMP() WHERE id = 1");
		s_dwNextConfig = 0;
		ch->ChatPacket(CHAT_TYPE_INFO, "WORLDBOSS: the standing boss escapes within 30 s.");
	}
	else if (gm && !strcmp(sub, "przeladuj"))
	{
		LoadData();
		s_dwNextConfig = 0;
		ch->ChatPacket(CHAT_TYPE_INFO, "WORLDBOSS: worldboss.txt read again (%u bosses, %u spots).", (unsigned)s_data.bosses.size(),
				(unsigned)s_data.spots.size());
	}
	else if (gm && !strcmp(sub, "stan"))
	{
		const TState& s = s_state;
		ch->ChatPacket(CHAT_TYPE_INFO, "WORLDBOSS: owner=%d mode=%d channel=%d serial=%u state=%u boss=%u map=%u hp=%u%% next=%u fight_end=%u falls=%u season=%u end=%u damage_rows=%u",
				s_bOwner ? 1 : 0, s_cfg.mode, s_cfg.channel, s.serial, s.state, s.bossVnum, s.map, s.hpPct, s.nextAt, s.fightEnd, s.falls,
				s.season, s.seasonEnd, (unsigned)s_mapDamage.size());
	}
}
