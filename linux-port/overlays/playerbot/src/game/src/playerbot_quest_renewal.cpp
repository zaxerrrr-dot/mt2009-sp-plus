// MT2009_PLUS_QUEST_RENEWAL_V1: the renewed quest window (QUEST_RENEWAL 1.0.0.6, (C) 2019 Owsap Productions) - the
// server half. The package sends a quest's category in every quest-info packet (packet_quest_info.c_index, a changed
// packet that needs a matching exe); here the client's root gets the same thing without any packet change: at the
// login the core sends its quest index -> category map as "QuestCategory <part> <index>:<category>,..." command lines
// (root questrenewal.py). An old client ignores the command, a new root without it files every quest under its
// default category; the bots (their desc reads nothing) are passed by. Hook: server-patches/questren (input_login.cpp, Entergame).
//
// Categories (the package's / the official window's order, root questrenewal.py's labels):
//   0 main story   1 side quests   2 hunting   3 events   4 Biologist / herbs   5 other (game, systems: the client's
//   default - not sent)   6 quest scrolls   7 daily / repeatable
// The table below files our quests (the stock ones with a letter/title, ours from linux-port/docker/game/quest);
// <quest dir>/questcategory.txt (the package's file: "<category><tab><quest name>" per line) may add or change entries
// without a rebuild - it is read at every login, a missing file is fine.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "questmanager.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <string>

namespace
{
	enum
	{
		QR_MAIN = 0,
		QR_SUB = 1,
		QR_HUNT = 2,
		QR_EVENT = 3,
		QR_COLLECT = 4,
		QR_SYSTEM = 5,	// the client's default: never sent
		QR_SCROLL = 6,
		QR_DAILY = 7,
		QR_MAX = 8,
	};

	struct SQuestRenewalName
	{
		const char* name;
		int category;
	};

	// one name each
	const SQuestRenewalName s_aNames[] =
	{
		// the story
		{ "find_squareguard", QR_MAIN }, { "find_brother_article", QR_MAIN }, { "find_senior_soldier", QR_MAIN },
		{ "patrol_townaround", QR_MAIN },
		// side quests (and the regions' own stories)
		{ "desert_first_quest", QR_SUB }, { "desert_second_quest", QR_SUB }, { "desert_third_quest", QR_SUB },
		{ "orcvalley_first_quest", QR_SUB }, { "hwang_introduction", QR_SUB }, { "new_quest_premium_lv4", QR_SUB },
		{ "zaklety_las", QR_SUB }, { "zodiac_prism_mission", QR_SUB }, { "zodiac_emergency_mission", QR_SUB },
		// hunting
		{ "hunting", QR_HUNT }, { "desert_reputation_kill", QR_HUNT }, { "orc_valley_rep_kill", QR_HUNT },
		// events
		{ "harvest_festival", QR_EVENT }, { "pre_event_heavens_cave", QR_EVENT }, { "beta_server", QR_EVENT },
		{ "christmas_santa", QR_EVENT }, { "christmas_tree", QR_EVENT }, { "event_easter", QR_EVENT },
		{ "event_easter_2012", QR_EVENT }, { "event_easter_2013", QR_EVENT }, { "event_halloween_hair", QR_EVENT },
		{ "new_christmas_2012", QR_EVENT }, { "new_christmas_2012_nog", QR_EVENT }, { "new_christmas_2012_sock", QR_EVENT },
		{ "new_christmas_gift_box", QR_EVENT }, { "new_christmas_nog_quest", QR_EVENT },
		{ "new_christmas_quest", QR_EVENT }, { "new_christmas_sock_quest", QR_EVENT }, { "new_easter_gift_box", QR_EVENT },
		{ "new_easter_gift_box_gf", QR_EVENT }, { "valentine_event2025", QR_EVENT }, { "oxevent_manager", QR_EVENT },
		// quest scrolls
		{ "quest_book_kill", QR_SCROLL }, { "qbook_manage", QR_SCROLL },
		// daily / repeatable
		{ "heavens_cave_keyquest", QR_DAILY },
	};

	// numbered families: <prefix><n> for n in [from, to]
	struct SQuestRenewalFamily
	{
		const char* prefix;
		int from;
		int to;
		int category;
	};

	const SQuestRenewalFamily s_aFamilies[] =
	{
		{ "main_quest_lv", 1, 120, QR_MAIN },
		{ "subquest_", 1, 80, QR_SUB },
		{ "new_quest_lv", 1, 120, QR_SUB },
		{ "collect_quest_lv", 1, 130, QR_COLLECT },
		{ "collect_quest_cz", 1, 40, QR_COLLECT },
		{ "make_herb_lv", 1, 40, QR_COLLECT },
	};

	// <quest dir>/questcategory.txt: "<category> <quest name>" (tab or spaces), # comments
	void ReadOverrides(std::map<std::string, int>& names)
	{
		std::ifstream inf((g_stQuestDir + "/questcategory.txt").c_str());
		if (!inf.is_open())
			return;

		std::string line;
		while (std::getline(inf, line))
		{
			const size_t first = line.find_first_not_of(" \t\r");
			if (first == std::string::npos || line[first] == '#')
				continue;
			char* end = NULL;
			const long category = strtol(line.c_str() + first, &end, 10);
			if (!end || end == line.c_str() + first)
				continue;
			std::string name(end);
			const size_t b = name.find_first_not_of(" \t\r\"");
			const size_t e = name.find_last_not_of(" \t\r\"");
			if (b == std::string::npos)
				continue;
			name = name.substr(b, e - b + 1);
			if (category < 0 || category >= QR_MAX)
			{
				sys_err("QUEST_RENEWAL questcategory.txt: %s has category %ld (0-%d)", name.c_str(), category, QR_MAX - 1);
				continue;
			}
			names[name] = (int) category;
		}
	}
}

// the quest index -> category map of this core (only what is not the client's default)
static void QuestRenewalBuildMap(std::map<unsigned int, int>& out)
{
	quest::CQuestManager& q = quest::CQuestManager::instance();
	std::map<std::string, int> names;

	for (size_t i = 0; i < sizeof(s_aFamilies) / sizeof(s_aFamilies[0]); ++i)
	{
		const SQuestRenewalFamily& f = s_aFamilies[i];
		char buf[64];
		for (int n = f.from; n <= f.to; ++n)
		{
			snprintf(buf, sizeof(buf), "%s%d", f.prefix, n);
			names[buf] = f.category;
		}
	}
	for (size_t i = 0; i < sizeof(s_aNames) / sizeof(s_aNames[0]); ++i)
		names[s_aNames[i].name] = s_aNames[i].category;

	ReadOverrides(names);

	for (std::map<std::string, int>::const_iterator it = names.begin(); it != names.end(); ++it)
	{
		if (it->second == QR_SYSTEM)
			continue;
		const unsigned int idx = q.GetQuestIndexByName(it->first);	// 0: no such quest on this core
		if (idx)
			out[idx] = it->second;
	}
}

// input_login.cpp (Entergame): the map to the client, in lines of at most ~300 characters. Part 0 clears the client's
// map first (a warp to another core, a /reload q).
void QuestRenewalOnLogin(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())	// a bot's desc goes nowhere
		return;

	std::map<unsigned int, int> m;
	QuestRenewalBuildMap(m);

	int part = 0;
	std::string line;
	for (std::map<unsigned int, int>::const_iterator it = m.begin(); it != m.end(); ++it)
	{
		char buf[32];
		snprintf(buf, sizeof(buf), "%s%u:%d", line.empty() ? "" : ",", it->first, it->second);
		line += buf;
		if (line.size() >= 300)
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "QuestCategory %d %s", part++, line.c_str());
			line.clear();
		}
	}
	if (!line.empty() || part == 0)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "QuestCategory %d %s", part, line.empty() ? "-" : line.c_str());
}
