#ifndef __INC_METIN2_PLAYERBOT_RANK_POINTS_H__
#define __INC_METIN2_PLAYERBOT_RANK_POINTS_H__

// Punkty Rangi - the extra ranks raised by eating fruits (MT2009_PLUS_RANK_POINTS_V1).
//
// Arezzo's "dodatkowe rangi" (its fruits 80050-80054, their icons and names, the
// rank names and their colours come from the Arezzo client), with the owner's
// numbers (6 October):
//
//   * Fruits: Metins and bosses drop 1-2 pieces at 30%, the fruit of the KILLED
//     monster's level band: Jablko 1-53 (to the Orc Valley), Gruszka 54-74,
//     Winogrono 75-99, Arbuz 100-109, Ananas 110 and up. A player's on the
//     ground for the killer (two minutes), a bot's into its bag (a full bag
//     gets nothing). Log [RANGA_DROP].
//   * A fruit works only in its range of rank points: Jablko 0-20 000 (+50),
//     Gruszka 20 000-40 000 (+50), Winogrono 40 000-80 000 (+100), Arbuz
//     80 000-120 000 (+100), Ananas 120 000-200 000 (+100); 200 000 is the cap.
//     Out of its range it is refused with the fruit wanted now. Log [RANGA_USE].
//   * The rank's bonus by the points, one tier at a time (not added up), on
//     hidden affects of type AFFECT_RANK_POINTS (580; 500-599 survive a death),
//     put right at login, after every fruit and every few seconds while the
//     affects are not loaded yet:
//         21 000 Waleczny    +10% monsters, +10% people,                           +1000 HP
//         31 000 Mocarny     +12% / +12%,                                          +1500 HP
//         41 000 Potezny     +15% / +15%,                                          +1900 HP
//         51 000 Wladca      +18% / +18%,                                          +2200 HP
//         81 000 Arcymistrz  +18% / +18%, +10% Metins,                             +2900 HP
//        101 000 Legenda     +18% / +18%, +15% Metins, +10% bosses,                +3500 HP
//        121 000 Legenda     +18% / +18%, +15% Metins, +15% bosses,                +4000 HP
//        200 000 Legenda     +20% / +20%, +18% Metins, +18% bosses, +10% average   +5000 HP
//     (POINT_ATTBONUS_MONSTER, _HUMAN, _STONE, _BOSS, POINT_NORMAL_HIT_DAMAGE_BONUS
//     - "srednie obrazenia" - and POINT_MAX_HP).
//   * The title: from 21 000 the rank's name, in its colour, stands where the
//     alignment title stood. The client hears "RANGA tail <vid> <tier>" when a
//     character comes into its view (char.cpp, EncodeInsertPacket) and around
//     a character whose tier changes; "RANGA self <points> <tier>" tells the
//     player its own points (the character window's alignment tooltip). Tier 0:
//     the alignment title as before. Client: root/rankpoints.py; the exe's
//     chrmgr.SetRankTitle (client-patches/exe, ENABLE_RANK_TITLE), with an
//     older exe the title is put back over the alignment's every half second.
//   * Storage: player.mt2009_rank_points (pid, points), read at login (a bot:
//     at its first look on this core), written after every change.
//   * /ranga: the player's points, rank, bonus and the fruit wanted now. A GM
//     (GM_HIGH_WIZARD): /ranga ustaw <nick> <points>.
//   * Bots: their kills' fruits into the bag; one that fits their range is
//     eaten at their next look (ManagePlayerBotRankPoints), any other goes on
//     their counter at the tier's price (GetPlayerBotRankFruitPrice) or to the
//     merchant from a bot with no counter (playerbot_economy.h / _town.h).
//   * M2_RANK_POINTS=0 (the game container's environment) switches the system
//     off: no drops, the fruits do nothing, the bonuses and titles come off at
//     the next login.
//
// The engine's calls are server-patches/rankpoints (edits.json).

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <set>
#include <string>

namespace mt2009_rankp
{
	const DWORD AFFECT_RANK_POINTS = 580;
	const int POINTS_MAX = 200000;
	const int DROP_PERCENT = 30;
	const int SYNC_TICK_SEC = 5;

	struct SFruit
	{
		DWORD vnum;
		const char* name;		// CP1250
		int maxLevel;			// the killed monster's level band's top
		int from, to;			// the range of points it works in: from <= points < to
		int gain;
	};

	const SFruit FRUITS[] =
	{
		{ 80050, "Jab" "\xb3" "ko",    53,      0,  20000,  50 },
		{ 80051, "Gruszka",   74,  20000,  40000,  50 },
		{ 80052, "Winogrono", 99,  40000,  80000, 100 },
		{ 80053, "Arbuz",    109,  80000, 120000, 100 },
		{ 80054, "Ananas",  1000, 120000, 200000, 100 },
	};
	const int FRUIT_COUNT = (int)(sizeof(FRUITS) / sizeof(FRUITS[0]));

	enum EBonus { B_MONSTER, B_HUMAN, B_STONE, B_BOSS, B_NORMAL_HIT, B_HP, B_COUNT };
	const BYTE BONUS_POINTS[B_COUNT] =
	{
		POINT_ATTBONUS_MONSTER, POINT_ATTBONUS_HUMAN, POINT_ATTBONUS_STONE, POINT_ATTBONUS_BOSS,
		POINT_NORMAL_HIT_DAMAGE_BONUS, POINT_MAX_HP
	};

	struct STier
	{
		int from;
		const char* name;		// CP1250
		long bonus[B_COUNT];
	};

	// Tier 0: under 21 000, nothing.
	const STier TIERS[] =
	{
		{      0, "",            {  0,  0,  0,  0,  0,    0 } },
		{  21000, "Waleczny",    { 10, 10,  0,  0,  0, 1000 } },
		{  31000, "Mocarny",     { 12, 12,  0,  0,  0, 1500 } },
		{  41000, "Pot" "\xea" "\xbf" "ny",     { 15, 15,  0,  0,  0, 1900 } },
		{  51000, "W" "\xb3" "adca",      { 18, 18,  0,  0,  0, 2200 } },
		{  81000, "Arcymistrz",  { 18, 18, 10,  0,  0, 2900 } },
		{ 101000, "Legenda",     { 18, 18, 15, 10,  0, 3500 } },
		{ 121000, "Legenda",     { 18, 18, 15, 15,  0, 4000 } },
		{ 200000, "Legenda",     { 20, 20, 18, 18, 10, 5000 } },
	};
	const int TIER_COUNT = (int)(sizeof(TIERS) / sizeof(TIERS[0]));

	// The players' texts, CP1250 as escapes (a hex digit never follows one -
	// the literals are split there).
	const char* const MSG_DISABLED = "Punkty Rangi s" "\xb9" " wy" "\xb3" "\xb9" "czone na tym serwerze.";
	const char* const MSG_MAX = "Masz ju" "\xbf" " maksymaln" "\xb9" " liczb" "\xea" " Punkt" "\xf3" "w Rangi (200 000).";
	const char* const MSG_WRONG = "Ten owoc teraz nie zadzia" "\xb3" "a. Masz %d Punkt" "\xf3" "w Rangi - teraz potrzebujesz: %s (od %d do %d punkt" "\xf3" "w).";
	const char* const MSG_GAIN = "Punkty Rangi: +%d (masz %d / 200 000).";
	const char* const MSG_TIER_UP = "Awansujesz na rang" "\xea" ": %s!";
	const char* const MSG_INFO = "Ranga: %s, Punkty Rangi: %d / 200 000.";
	const char* const MSG_INFO_NONE = "Ranga: brak (pierwsza ranga - Waleczny - od 21 000 punkt" "\xf3" "w). Punkty Rangi: %d / 200 000.";
	const char* const MSG_NEXT = "Nast" "\xea" "pna ranga: %s od %d punkt" "\xf3" "w. Teraz jedz: %s (+%d za sztuk" "\xea" ").";
	const char* const MSG_NEXT_MAX = "To najwy" "\xbf" "sza ranga.";
	const char* const MSG_FRUITS = "Owoce wypadaj" "\xb9" " z Metin" "\xf3" "w i boss" "\xf3" "w (30%%, 1-2 szt.): Jab" "\xb3" "ko do 53 poz., Gruszka 54-74, Winogrono 75-99, Arbuz 100-109, Ananas od 110.";
	const char* const MSG_BONUS_HEAD = "Bonus rangi:";
	const char* const MSG_SET_USAGE = "U" "\xbf" "ycie: /ranga ustaw <nick> <punkty>";
	const char* const MSG_SET_NOBODY = "Nie ma takiej postaci na tym rdzeniu.";
	const char* const MSG_SET_DONE = "%s: Punkty Rangi = %d.";

	// ---------------------------------------------------------------- the switch

	// M2_RANK_POINTS in the game container's environment, read once: on unless
	// "0", "off", "no" or "false".
	bool Enabled()
	{
		static int s_enabled = -1;
		if (s_enabled < 0)
		{
			const char* value = getenv("M2_RANK_POINTS");
			s_enabled = 1;
			if (value && (!strcmp(value, "0") || !strcasecmp(value, "off") || !strcasecmp(value, "no") || !strcasecmp(value, "false")))
				s_enabled = 0;
			sys_log(0, "RANK_POINTS: %s (M2_RANK_POINTS=%s)", s_enabled ? "on" : "off", value ? value : "");
		}
		return s_enabled != 0;
	}

	// ---------------------------------------------------------------- tables

	const SFruit* FruitByVnum(DWORD vnum)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (FRUITS[i].vnum == vnum)
				return &FRUITS[i];
		return NULL;
	}

	// The fruit that works at these points (NULL at the cap).
	const SFruit* FruitForPoints(int points)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (points >= FRUITS[i].from && points < FRUITS[i].to)
				return &FRUITS[i];
		return NULL;
	}

	const SFruit* FruitForLevel(int level)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (level <= FRUITS[i].maxLevel)
				return &FRUITS[i];
		return &FRUITS[FRUIT_COUNT - 1];
	}

	int TierOf(int points)
	{
		int tier = 0;
		for (int i = 1; i < TIER_COUNT; ++i)
			if (points >= TIERS[i].from)
				tier = i;
		return tier;
	}

	// ---------------------------------------------------------------- the points

	struct SEntry
	{
		int points;
		const void* who;		// the CHARACTER read for: a bot is read again when it comes back as another
		SEntry() : points(0), who(NULL) {}
	};

	std::map<DWORD, SEntry> s_points;		// pid -> points, characters read on this core
	std::map<DWORD, int> s_needSync;		// pids whose bonuses wait for their affects -> since when
	LPEVENT s_pkTick = NULL;

	bool IsBot(LPCHARACTER ch)
	{
		return CPlayerBotManager::instance().IsManaged(ch->GetPlayerID());
	}

	bool Counts(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetPlayerID() != 0;
	}

	void EnsureTable()
	{
		static bool s_done = false;
		if (s_done)
			return;
		s_done = true;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.mt2009_rank_points ("
				"pid INT UNSIGNED NOT NULL PRIMARY KEY, "
				"points INT NOT NULL DEFAULT 0, "
				"updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
				") ENGINE=InnoDB"));
	}

	// The character's points from the table (synchronous: at login, or a bot's first look).
	int Load(LPCHARACTER ch)
	{
		EnsureTable();
		int points = 0;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT points FROM player.mt2009_rank_points WHERE pid=%u", ch->GetPlayerID()));
		if (msg.get() && msg->Get() && msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
			if (row && row[0])
				points = atoi(row[0]);
		}
		points = std::max(0, std::min(points, POINTS_MAX));
		SEntry& e = s_points[ch->GetPlayerID()];
		e.points = points;
		e.who = ch;
		return points;
	}

	bool Known(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return it != s_points.end() && it->second.who == ch;
	}

	int Points(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return (it != s_points.end() && it->second.who == ch) ? it->second.points : Load(ch);
	}

	// The points of a character in view, without asking the table (0 when not read yet).
	int KnownPoints(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return it != s_points.end() ? it->second.points : 0;
	}

	void Save(LPCHARACTER ch, int points)
	{
		DBManager::instance().Query("REPLACE INTO player.mt2009_rank_points (pid, points) VALUES (%u, %d)",
				ch->GetPlayerID(), points);
	}

	// ---------------------------------------------------------------- the bonus

	void EnsureTick();

	// The tier's bonus on the character's affects: put on, changed or taken off.
	void SyncBonuses(LPCHARACTER ch)
	{
		if (!ch->IsLoadedAffect())
		{
			s_needSync.insert(std::make_pair(ch->GetPlayerID(), (int)get_global_time()));
			EnsureTick();
			return;
		}
		s_needSync.erase(ch->GetPlayerID());
		const int tier = Enabled() ? TierOf(KnownPoints(ch)) : 0;
		for (int i = 0; i < B_COUNT; ++i)
		{
			const long want = TIERS[tier].bonus[i];
			CAffect* aff = ch->FindAffect(AFFECT_RANK_POINTS, BONUS_POINTS[i]);
			if (want <= 0)
			{
				if (aff)
					ch->RemoveAffect(aff);
				continue;
			}
			if (aff && aff->lApplyValue == want)
				continue;
			ch->AddAffect(AFFECT_RANK_POINTS, BONUS_POINTS[i], want, 0, INFINITE_AFFECT_DURATION, 0, true, true);
		}
	}

	// ---------------------------------------------------------------- to the client

	void SendSelf(LPCHARACTER ch)
	{
		if (!ch->GetDesc() || IsBot(ch))
			return;
		const int points = Enabled() ? KnownPoints(ch) : 0;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "RANGA self %d %d", points, TierOf(points));
	}

	// "RANGA tail <vid> <tier>" to everyone who sees ch, ch itself too.
	void SendTailAround(LPCHARACTER ch)
	{
		if (!ch->GetSectree())
			return;
		const int tier = Enabled() ? TierOf(KnownPoints(ch)) : 0;
		char command[64];
		int len = snprintf(command, sizeof(command), "RANGA tail %u %d", (unsigned int)ch->GetVID(), tier);
		if (len <= 0 || len >= (int)sizeof(command))
			return;
		++len;   // the trailing NUL every chat packet carries
		TPacketGCChat pack;
		pack.header = HEADER_GC_CHAT;
		pack.size = sizeof(TPacketGCChat) + len;
		pack.type = CHAT_TYPE_COMMAND;
		pack.id = 0;
		pack.bEmpire = 0;
		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(TPacketGCChat));
		buf.write(command, len);
		ch->PacketAround(buf.read_peek(), buf.size());
	}

	// ---------------------------------------------------------------- the points change

	// New points for ch: saved, the bonus and the title put right. Returns the new tier.
	int SetPoints(LPCHARACTER ch, int points, bool tell)
	{
		points = std::max(0, std::min(points, POINTS_MAX));
		SEntry& e = s_points[ch->GetPlayerID()];
		const int before = (e.who == ch) ? TierOf(e.points) : TierOf(Points(ch));
		e.points = points;
		e.who = ch;
		Save(ch, points);
		const int tier = TierOf(points);
		SyncBonuses(ch);
		SendSelf(ch);
		if (tier != before)
		{
			SendTailAround(ch);
			if (tell && tier > before)
				ch->ChatPacket(CHAT_TYPE_INFO, MSG_TIER_UP, TIERS[tier].name);
			sys_log(0, "[RANGA_TIER] pid=%u name=%s points=%d tier=%d->%d bot=%d",
					ch->GetPlayerID(), ch->GetName(), points, before, tier, IsBot(ch) ? 1 : 0);
		}
		return tier;
	}

	// One fruit eaten: false when it does not fit the points (nothing changes).
	bool Eat(LPCHARACTER ch, const SFruit& fruit, bool tell)
	{
		const int points = Points(ch);
		if (points < fruit.from || points >= fruit.to)
			return false;
		const int now = std::min(points + fruit.gain, POINTS_MAX);
		SetPoints(ch, now, tell);
		if (tell)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_GAIN, now - points, now);
		sys_log(0, "[RANGA_USE] pid=%u name=%s vnum=%u points=%d->%d bot=%d",
				ch->GetPlayerID(), ch->GetName(), fruit.vnum, points, now, IsBot(ch) ? 1 : 0);
		return true;
	}

	// ---------------------------------------------------------------- the waiting affects

	EVENTINFO(rank_points_tick_info)
	{
		int dummy;
	};

	EVENTFUNC(rank_points_tick)
	{
		const std::map<DWORD, int> pids(s_needSync);
		const int now = (int)get_global_time();
		for (std::map<DWORD, int>::const_iterator it = pids.begin(); it != pids.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || now - it->second > 600)	// gone, or ten minutes without its affects
				s_needSync.erase(it->first);
			else if (ch->IsLoadedAffect())
				SyncBonuses(ch);
		}
		if (s_needSync.empty())
		{
			s_pkTick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(SYNC_TICK_SEC);
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		rank_points_tick_info* info = AllocEventInfo<rank_points_tick_info>();
		s_pkTick = event_create(rank_points_tick, info, PASSES_PER_SEC(SYNC_TICK_SEC));
	}

	// ---------------------------------------------------------------- the drop

	void Drop(LPCHARACTER killer, LPCHARACTER victim)
	{
		const SFruit* fruit = FruitForLevel(victim->GetLevel());
		const int roll = number(1, 100);
		const bool win = roll <= DROP_PERCENT;
		const int count = number(1, 2);
		sys_log(0, "[RANGA_DROP] mob_vnum=%u mob_lv=%d killer=%s killer_pid=%u roll=%d win=%d vnum=%u count=%d",
				victim->GetRaceNum(), victim->GetLevel(), killer->GetName(), killer->GetPlayerID(), roll, win ? 1 : 0,
				fruit->vnum, count);
		if (!win)
			return;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(fruit->vnum, count);
		if (!item)
			return;
		if (IsBot(killer))
		{
			if (killer->GetEmptyInventory(item->GetSize()) >= 0)
				killer->AutoGiveItem(item);
			else
				M2_DESTROY_ITEM(item);
			return;
		}
		PIXEL_POSITION pos;
		pos.x = victim->GetX() + number(-100, 100);
		pos.y = victim->GetY() + number(-100, 100);
		item->SetOwnership(killer, 120);
		if (!item->AddToGround(victim->GetMapIndex(), pos))
		{
			M2_DESTROY_ITEM(item);
			return;
		}
		item->StartDestroyEvent();
	}

	// ---------------------------------------------------------------- /ranga

	void BonusLines(LPCHARACTER ch, int tier)
	{
		const long* b = TIERS[tier].bonus;
		char line[256];
		int len = snprintf(line, sizeof(line), "%s", MSG_BONUS_HEAD);
		static const char* const labels[B_COUNT] =
		{
			" silny przeciwko potworom +%ld%%,", " silny przeciwko ludziom +%ld%%,", " silny przeciwko Metinom +%ld%%,",
			" silny przeciwko bossom +%ld%%,", " " "\x9c" "rednie obra" "\xbf" "enia +%ld%%,", " max. P" "\xaf" " +%ld"
		};
		for (int i = 0; i < B_COUNT && len > 0 && len < (int)sizeof(line); ++i)
			if (b[i] > 0)
				len += snprintf(line + len, sizeof(line) - len, labels[i], b[i]);
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", line);
	}

	void Info(LPCHARACTER ch)
	{
		const int points = Points(ch);
		const int tier = TierOf(points);
		if (tier)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_INFO, TIERS[tier].name, points);
			BonusLines(ch, tier);
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_INFO_NONE, points);
		const SFruit* fruit = FruitForPoints(points);
		if (tier + 1 < TIER_COUNT && fruit)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_NEXT, TIERS[tier + 1].name, TIERS[tier + 1].from, fruit->name, fruit->gain);
		else if (!fruit)
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_NEXT_MAX);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_FRUITS);
	}
}

// ---------------------------------------------------------------- the bots

namespace
{
	DWORD ScalePlayerBotIwakuraPrice(DWORD base);

	bool IsPlayerBotRankFruit(DWORD vnum)
	{
		return mt2009_rankp::FruitByVnum(vnum) != NULL;
	}

	// A piece on a counter, by the fruit's tier: 5 000 / 10 000 / 25 000 /
	// 50 000 / 100 000 yang before the sheet's scaling (the merchant pays a
	// fifth - item_proto, apply.sh).
	DWORD GetPlayerBotRankFruitPrice(DWORD vnum)
	{
		static const DWORD prices[] = { 5000, 10000, 25000, 50000, 100000 };
		for (int i = 0; i < mt2009_rankp::FRUIT_COUNT; ++i)
			if (mt2009_rankp::FRUITS[i].vnum == vnum)
				return std::max<DWORD>(100, ScalePlayerBotIwakuraPrice(prices[i]) / 100 * 100);
		return 0;
	}

	// The fruit that fits the bot's points now: its own, eaten at its next look.
	bool IsPlayerBotKeptRankFruit(LPCHARACTER ch, LPITEM item)
	{
		using namespace mt2009_rankp;
		if (!ch || !item || !Enabled())
			return false;
		const SFruit* fruit = FruitByVnum(item->GetVnum());
		if (!fruit)
			return false;
		const int points = KnownPoints(ch);
		return points >= fruit->from && points < fruit->to;
	}

	std::map<DWORD, DWORD> s_mapPlayerBotRankNextLook;

	// A look every 20-40 s: the points read on this core, the bonus on, the
	// fitting fruits eaten (up to 40 a look).
	void ManagePlayerBotRankPoints(LPCHARACTER ch, DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (!ch || ch->IsDead() || !Enabled())
			return;
		DWORD& next = s_mapPlayerBotRankNextLook[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return;
		next = dwNow + number(20000, 40000);
		if (!Known(ch))
		{
			Load(ch);
			SyncBonuses(ch);
			if (TierOf(KnownPoints(ch)) > 0)
				SendTailAround(ch);
		}
		if (ch->GetExchange() || ch->GetMyShop())
			return;
		for (int eaten = 0; eaten < 40; ++eaten)
		{
			const SFruit* fruit = FruitForPoints(KnownPoints(ch));
			if (!fruit || ch->CountSpecifyItem(fruit->vnum) <= 0)
				break;
			ch->RemoveSpecifyItem(fruit->vnum, 1);
			if (!Eat(ch, *fruit, false))
				break;
		}
	}
}

// ---------------------------------------------------------------- the engine's calls (server-patches/rankpoints)

// char_item.cpp, UseItemEx: -1 = not a fruit, 0 = a fruit not eaten, 1 = eaten.
int RankPointsUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace mt2009_rankp;
	const SFruit* fruit = item ? FruitByVnum(item->GetVnum()) : NULL;
	if (!fruit || !Counts(ch))
		return -1;
	if (!Enabled())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_DISABLED);
		return 0;
	}
	const int points = Points(ch);
	if (points >= POINTS_MAX)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_MAX);
		return 0;
	}
	if (!Eat(ch, *fruit, true))
	{
		const SFruit* want = FruitForPoints(points);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_WRONG, points, want ? want->name : "-", want ? want->from : 0, want ? want->to : 0);
		return 0;
	}
	item->SetCount(item->GetCount() - 1);
	return 1;
}

// char_battle.cpp, after the Monster Cards' call: a Metin's or a boss's fruit.
void RankPointsOnKill(LPCHARACTER killer, LPCHARACTER victim)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !Counts(killer) || !victim || victim->IsPC())
		return;
	if (!victim->IsStone() && victim->GetMobRank() < MOB_RANK_BOSS)
		return;
	Drop(killer, victim);
}

// input_login.cpp, entering the game: the points read again, the bonus and the title.
void RankPointsOnLogin(LPCHARACTER ch)
{
	using namespace mt2009_rankp;
	if (!Counts(ch))
		return;
	Load(ch);
	SyncBonuses(ch);
	SendSelf(ch);
	if (Enabled() && TierOf(KnownPoints(ch)) > 0)
		SendTailAround(ch);
}

// char.cpp, EncodeInsertPacket: a character with a rank coming into a player's view.
void RankPointsOnInsert(LPCHARACTER shown, LPCHARACTER viewer)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !shown || !viewer || !shown->IsPC() || !viewer->GetDesc())
		return;
	const int tier = TierOf(KnownPoints(shown));
	if (tier > 0)
		viewer->ChatPacket(CHAT_TYPE_COMMAND, "RANGA tail %u %d", (unsigned int)shown->GetVID(), tier);
}

// item_manager.cpp, the drop wiki: the fruit of a monster's level (0: none).
DWORD RankPointsWikiFruit(bool metinOrBoss, int level)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !metinOrBoss)
		return 0;
	return FruitForLevel(level)->vnum;
}

int RankPointsWikiPercent()
{
	return mt2009_rankp::DROP_PERCENT;
}

// "/ranga": the player's points; a GM's "/ranga ustaw <nick> <points>".
ACMD(do_rank_points)
{
	using namespace mt2009_rankp;
	if (!Counts(ch))
		return;
	if (!Enabled())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_DISABLED);
		return;
	}
	char a1[256], a2[256], a3[256];
	const char* rest = one_argument(argument, a1, sizeof(a1));
	if (*a1 && !strcmp(a1, "ustaw") && ch->GetGMLevel() >= GM_HIGH_WIZARD)
	{
		rest = one_argument(rest, a2, sizeof(a2));
		one_argument(rest, a3, sizeof(a3));
		if (!*a2 || !*a3 || !isdigit((unsigned char)a3[0]))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_SET_USAGE);
			return;
		}
		LPCHARACTER target = CHARACTER_MANAGER::instance().FindPC(a2);
		if (!target || !Counts(target))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_SET_NOBODY);
			return;
		}
		Points(target);
		const int points = SetPoints(target, atoi(a3), true);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_SET_DONE, target->GetName(), KnownPoints(target));
		sys_log(0, "[RANGA_SET] gm=%s target=%s points=%d tier=%d", ch->GetName(), target->GetName(), KnownPoints(target), points);
		return;
	}
	Info(ch);
}

#endif
