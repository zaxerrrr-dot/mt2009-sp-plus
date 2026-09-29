#ifndef __INC_METIN2_PLAYERBOT_OCHAO_BOTS_H__
#define __INC_METIN2_PLAYERBOT_OCHAO_BOTS_H__

// MT2009_PLUS_OCHAO_BOTS_V1 - the bots in the Temple of Ochao (Swiatynia
// Ochao, map 209, metin2_map_mt_th_dungeon_01; the map and the En-Tai
// Guardian's clock are playerbot_ochao.h's, the quest is
// temple_of_the_ochao.quest).
//
// What a bot has to know about the place, measured on the map's own files
// (server_attr decoded at 50 units, regen.txt, boss.txt, npc.txt, Town.txt;
// the generator is tools/ochao_bot_map.py):
//
//   * the way in: a bot of PLAYERBOT_OCHAO_MIN_LEVEL (95, the quest's gate)
//     goes to Orc Valley, walks to Straznik Swiatyni (20426, cell 289,1448
//     beside Koe-Pung) and is taken to the temple's gate (Town.txt 89,84),
//     the same warp the quest gives a player;
//   * the map: one walkable piece of 582 236 cells, a square labyrinth of
//     concentric corridors round a hall in the middle - the gate is its
//     top-left corner and the walk from there to the middle is about
//     190 km, against 43 km in a straight line;
//   * where to hunt: PLAYERBOT_OCHAO_HUBS, the spawn lines clustered, and
//     three boss rows - Straznik En-Tai (6400, walks between eleven rooms),
//     the Ochao Bodyguard (6311, three points, hourly) and the Ochao Lord
//     (6390, hourly), each one row because a boss hub follows its boss;
//   * the way out: the Teleporter (9012, npc.txt 400,385) in the middle hall
//     sends a character to its villages, at his outside-the-city price, and
//     for a minute after the Guardian falls his Portal (20415) opens where he
//     fell and leads to Orc Valley beside Koe-Pung. A bot that leaves walks
//     PLAYERBOT_OCHAO_EXIT_TREE - every corner of the shortest walk from any
//     hunting spot, room or the gate to the Teleporter - one straight leg at
//     a time, or takes the Portal when it stands open within reach.
//
// Leaving is the frontier's own decision (ManagePlayerBotWorldTravel): the
// visit clock, a full bag, potions running out, no weapon; only the way out
// is this file's. And a test hook, for the operator: a file
// "playerbot_ochao_test" in the core's directory ("send 150", "leave 30",
// "leaveall", "reset"), plus a position log (playerbot_ochao_track.tsv)
// and OCHAO_BOT lines in syslog.
//
// An implementation fragment in the sense playerbot_types.h describes:
// include it once, after playerbot_ochao.h and before playerbot_travel.h.

namespace
{
	// From playerbot_travel.h, which comes after this file.
	bool TransitionPlayerBotMap(LPCHARACTER ch, TPlayerBotAIState& state,
			long targetMap, long targetX, long targetY, DWORD dwNow, const char* reason);
	bool MovePlayerBotToWorldPortal(LPCHARACTER ch, TPlayerBotAIState& state,
			long portalX, long portalY, long targetMap, long targetX, long targetY,
			DWORD dwNow, const char* reason);
	bool GetPlayerBotFrontierArrivalFor(LPCHARACTER ch, long mapIndex, long& outX, long& outY);
	bool BlocksPlayerBotTravel(LPCHARACTER ch);
	long GetPlayerBotFrontierMapForLevel(LPCHARACTER ch);
	bool IsPlayerBotHumanLedParty(LPPARTY party);

	// Straznik Swiatyni in Orc Valley: the point walked to is where the
	// quest's Portal puts a player down, two steps from him.
	const long PLAYERBOT_OCHAO_GUARDIAN_X = 284700;
	const long PLAYERBOT_OCHAO_GUARDIAN_Y = 810600;
	// The Portal's way out (the quest's pc.warp).
	const long PLAYERBOT_OCHAO_PORTAL_TO_X = 284700;
	const long PLAYERBOT_OCHAO_PORTAL_TO_Y = 810600;
	// A bot takes the open Portal when it stands this near, in a straight
	// line, and the navigation joins the two.
	const int PLAYERBOT_OCHAO_PORTAL_REACH = 7000;
	// A corner of the way out is passed within this many units.
	const int PLAYERBOT_OCHAO_NODE_REACHED = 350;
	// A leg that has not shortened by this much in this long is a stall; after
	// this many stalls the bot walks the rest on the navigation alone.
	const int PLAYERBOT_OCHAO_LEG_PROGRESS = 250;
	const DWORD PLAYERBOT_OCHAO_LEG_TIMEOUT = 15000;
	const int PLAYERBOT_OCHAO_MAX_STALLS = 4;
	// How far a bot looks for a corner of the way out it can see.
	const int PLAYERBOT_OCHAO_NODE_SIGHT = 14000;
	// Monitoring: a bot on the map that has not moved this far in this long,
	// and has fought nothing in the last ten seconds, counts as stuck.
	const int PLAYERBOT_OCHAO_STUCK_DISTANCE = 200;
	const DWORD PLAYERBOT_OCHAO_STUCK_MS = 60000;
	const DWORD PLAYERBOT_OCHAO_TRACK_MS = 15000;
	const char* const PLAYERBOT_OCHAO_TEST_FILE = "playerbot_ochao_test";
	const char* const PLAYERBOT_OCHAO_TRACK_FILE = "playerbot_ochao_track.tsv";

	// The hunting spots: the regen's spawn lines clustered in 3200-unit
	// windows, the densest first, each snapped to a cell with five open cells
	// all round and at least 5000 from the next (22 spots, 293 regen lines).
	const TPlayerBotHuntingHub PLAYERBOT_OCHAO_HUBS[] = {
		{ 877875, 1419175, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 912825, 1416875, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 899625, 1417275, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 853725, 1466875, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 869675, 1423675, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 857975, 1423025, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 851675, 1424575, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 907775, 1441575, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 886525, 1470725, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 911725, 1466175, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 906325, 1458125, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 892575, 1416325, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 890225, 1421975, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 914475, 1427925, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 909625, 1429475, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 892975, 1427775, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 860475, 1434225, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 901775, 1449575, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 867675, 1434075, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 875125, 1444975, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 875975, 1453325, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		{ 890875, 1476625, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 0 },
		// The bosses: a hub is wherever the boss stands (IsPlayerBotBossAlive
		// asks the whole map), so one row each. Straznik En-Tai walks between
		// the eleven rooms (playerbot_ochao.h); the Ochao Bodyguard (6311) and
		// the Ochao Lord (6390) come from boss.txt every hour.
		{ 864100, 1422500, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 6400 },
		{ 899800, 1421800, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 6311 },
		{ 888100, 1416200, PLAYERBOT_OCHAO_MIN_LEVEL, 255, false, 6390 }
	};
	// The way out, as a tree rooted at the Teleporter: every node's next node
	// is the next corner towards him on the shortest walk (Dijkstra on the
	// map's server_attr at 50 units, corridor middles preferred), each edge
	// a straight line with three open cells either side. The leaves are the
	// gate, the eleven rooms, the four boss points and every hunting spot.
	struct TPlayerBotOchaoNode { long x; long y; short next; };
	const TPlayerBotOchaoNode PLAYERBOT_OCHAO_EXIT_TREE[] = {
		{ 884825, 1446525, -1 }, { 884825, 1450975, 0 }, { 885525, 1454125, 1 }, { 889375, 1454425, 2 },
		{ 889875, 1454225, 3 }, { 891025, 1450975, 4 }, { 894275, 1449525, 5 }, { 894525, 1438625, 6 },
		{ 894175, 1437975, 7 }, { 872675, 1437875, 8 }, { 872175, 1438225, 9 }, { 872075, 1457675, 10 },
		{ 872425, 1458325, 11 }, { 879375, 1458425, 12 }, { 881525, 1459525, 13 }, { 881625, 1460775, 14 },
		{ 882725, 1463825, 15 }, { 898175, 1464025, 16 }, { 898825, 1463675, 17 }, { 898925, 1434125, 18 },
		{ 898675, 1433475, 19 }, { 895525, 1432225, 20 }, { 894175, 1427975, 21 }, { 892675, 1427775, 22 },
		{ 890875, 1426575, 23 }, { 890775, 1424725, 24 }, { 889675, 1422575, 25 }, { 884725, 1422375, 26 },
		{ 878175, 1421275, 27 }, { 878075, 1420325, 28 }, { 876825, 1417025, 29 }, { 853725, 1416425, 30 },
		{ 886375, 1437875, 8 }, { 885275, 1436775, 32 }, { 885175, 1435875, 33 }, { 883975, 1432575, 34 },
		{ 868225, 1432475, 35 }, { 867775, 1432725, 36 }, { 867675, 1436925, 37 }, { 866625, 1439675, 38 },
		{ 865725, 1439825, 39 }, { 863275, 1440725, 40 }, { 863175, 1467425, 41 }, { 863375, 1468175, 42 },
		{ 868925, 1469525, 43 }, { 869025, 1472075, 44 }, { 868825, 1472575, 45 }, { 857925, 1472725, 46 },
		{ 857475, 1472475, 47 }, { 857375, 1453425, 48 }, { 856275, 1446875, 49 }, { 854525, 1446775, 50 },
		{ 851975, 1445475, 51 }, { 851875, 1423475, 52 }, { 852225, 1422975, 53 }, { 864125, 1422525, 54 },
		{ 856075, 1422875, 54 }, { 856425, 1423225, 56 }, { 857125, 1429625, 57 }, { 863425, 1468225, 43 },
		{ 867725, 1468325, 59 }, { 876575, 1468425, 60 }, { 877225, 1468075, 61 }, { 877325, 1465425, 62 },
		{ 876975, 1464775, 63 }, { 869825, 1464675, 64 }, { 867675, 1463575, 65 }, { 867225, 1446325, 66 },
		{ 889425, 1463925, 16 }, { 890625, 1465125, 68 }, { 890675, 1468025, 69 }, { 887475, 1469525, 70 },
		{ 887425, 1472425, 71 }, { 890625, 1473925, 72 }, { 890725, 1477675, 73 }, { 890475, 1478125, 74 },
		{ 879625, 1478825, 75 }, { 890575, 1468125, 70 }, { 888675, 1468325, 77 }, { 882325, 1468825, 78 },
		{ 891175, 1450825, 5 }, { 893125, 1450675, 80 }, { 894225, 1451025, 81 }, { 894525, 1458625, 82 },
		{ 894175, 1459125, 83 }, { 887825, 1459625, 84 }, { 882925, 1446525, 0 }, { 881475, 1446275, 86 },
		{ 881375, 1444075, 87 }, { 881975, 1442525, 88 }, { 888275, 1442375, 89 }, { 888775, 1442575, 90 },
		{ 889225, 1446225, 91 }, { 875875, 1432475, 35 }, { 874775, 1431375, 93 }, { 874575, 1428575, 94 },
		{ 874925, 1428075, 95 }, { 883625, 1427525, 96 }, { 898575, 1433375, 20 }, { 896575, 1433275, 98 },
		{ 889425, 1432725, 99 }, { 890775, 1423675, 25 }, { 890775, 1423425, 101 }, { 891225, 1422575, 102 },
		{ 904025, 1421925, 103 }, { 898925, 1451175, 18 }, { 899925, 1450175, 105 }, { 903075, 1448825, 106 },
		{ 904375, 1442125, 107 }, { 908625, 1440675, 108 }, { 909425, 1423225, 109 }, { 893225, 1422475, 103 },
		{ 899275, 1422375, 111 }, { 899825, 1421825, 112 }, { 867575, 1448875, 66 }, { 866925, 1448225, 114 },
		{ 883725, 1478325, 75 }, { 883125, 1478925, 116 }, { 897825, 1422375, 111 }, { 898925, 1421275, 118 },
		{ 899025, 1417925, 119 }, { 898875, 1417075, 120 }, { 888125, 1416225, 121 }, { 878075, 1419375, 29 },
		{ 877875, 1419175, 123 }, { 908675, 1440625, 109 }, { 908825, 1431775, 125 }, { 909975, 1430625, 126 },
		{ 914225, 1429275, 127 }, { 914525, 1417625, 128 }, { 914275, 1416975, 129 }, { 912825, 1416875, 130 },
		{ 899025, 1417875, 120 }, { 899625, 1417275, 132 }, { 857375, 1468075, 48 }, { 856275, 1466975, 134 },
		{ 853725, 1466875, 135 }, { 879275, 1422375, 27 }, { 871625, 1422375, 137 }, { 870175, 1422525, 138 },
		{ 869675, 1423675, 139 }, { 857825, 1422875, 56 }, { 857975, 1423025, 141 }, { 851875, 1424775, 52 },
		{ 851675, 1424575, 143 }, { 904425, 1442075, 108 }, { 907325, 1441975, 145 }, { 907775, 1441575, 146 },
		{ 887375, 1469875, 71 }, { 886525, 1470725, 148 }, { 890725, 1466925, 69 }, { 891875, 1468075, 150 },
		{ 898525, 1469425, 151 }, { 899925, 1472525, 152 }, { 908025, 1472825, 153 }, { 908675, 1472625, 154 },
		{ 909975, 1467125, 155 }, { 911725, 1466175, 156 }, { 892025, 1468225, 151 }, { 897525, 1468425, 158 },
		{ 902575, 1468425, 159 }, { 903225, 1468075, 160 }, { 904175, 1459525, 161 }, { 906325, 1458125, 162 },
		{ 898825, 1417025, 121 }, { 893125, 1416875, 164 }, { 892575, 1416325, 165 }, { 890775, 1423025, 102 },
		{ 890225, 1421975, 167 }, { 914325, 1428075, 128 }, { 914475, 1427925, 169 }, { 908825, 1430275, 126 },
		{ 909625, 1429475, 171 }, { 892975, 1427775, 22 }, { 857375, 1447975, 49 }, { 857375, 1435625, 174 },
		{ 857575, 1435125, 175 }, { 860475, 1434225, 176 }, { 900025, 1450075, 106 }, { 901475, 1449875, 178 },
		{ 901775, 1449575, 179 }, { 867675, 1434075, 37 }, { 881375, 1443375, 88 }, { 880575, 1442575, 182 },
		{ 877125, 1442275, 183 }, { 876275, 1442425, 184 }, { 875125, 1444975, 185 }, { 884825, 1453425, 1 },
		{ 884175, 1454125, 187 }, { 876575, 1454425, 188 }, { 876125, 1454125, 189 }, { 875975, 1453325, 190 },
		{ 890725, 1476475, 73 }, { 890875, 1476625, 192 }
	};

	const size_t PLAYERBOT_OCHAO_HUB_COUNT = sizeof(PLAYERBOT_OCHAO_HUBS) / sizeof(PLAYERBOT_OCHAO_HUBS[0]);
	const int PLAYERBOT_OCHAO_NODE_COUNT = (int)(sizeof(PLAYERBOT_OCHAO_EXIT_TREE) / sizeof(PLAYERBOT_OCHAO_EXIT_TREE[0]));

	// ------------------------------------------------------------ the state

	// A bot on its way in: sent to Orc Valley, walking to the Guardian.
	struct TPlayerBotOchaoCrossing { DWORD dwSince; };
	std::map<DWORD, TPlayerBotOchaoCrossing> s_mapPlayerBotOchaoCrossing;
	// A bot on its way out: the corner it walks to, and how the leg goes.
	struct TPlayerBotOchaoExit
	{
		int iNode;
		DWORD dwStarted;
		DWORD dwLegSince;
		int iLegBest;
		BYTE bStalls;
		bool bNavOnly;
		bool bPortal;
		char szReason[40];
		TPlayerBotOchaoExit() : iNode(-1), dwStarted(0), dwLegSince(0), iLegBest(0),
				bStalls(0), bNavOnly(false), bPortal(false) { szReason[0] = 0; }
	};
	std::map<DWORD, TPlayerBotOchaoExit> s_mapPlayerBotOchaoExit;
	// The operator's test: sent bots hunt here whatever their draw says, and
	// a leave order sends one out through the maze.
	std::set<DWORD> s_setPlayerBotOchaoForced;
	std::set<DWORD> s_setPlayerBotOchaoLeave;

	// What the monitoring keeps per bot.
	struct TPlayerBotOchaoTrack
	{
		DWORD dwEntered;		// first seen on the map this visit
		DWORD dwCrossStart;		// crossing began (0 if unknown)
		DWORD dwKills;
		DWORD dwBossKills;
		unsigned long long ullExp;
		DWORD dwDeaths;
		DWORD dwLastExp;
		DWORD dwLastNext;
		BYTE bLastLevel;
		bool bWasDead;
		long lAnchorX, lAnchorY;
		DWORD dwAnchorSince;
		bool bStuck;
		DWORD dwStuckEpisodes;
		DWORD dwStuckMs;
		TPlayerBotOchaoTrack() : dwEntered(0), dwCrossStart(0), dwKills(0), dwBossKills(0), ullExp(0),
				dwDeaths(0), dwLastExp(0), dwLastNext(0), bLastLevel(0), bWasDead(false),
				lAnchorX(0), lAnchorY(0), dwAnchorSince(0), bStuck(false), dwStuckEpisodes(0), dwStuckMs(0) {}
	};
	std::map<DWORD, TPlayerBotOchaoTrack> s_mapPlayerBotOchaoTrack;

	// The Guardian as the bots see him.
	DWORD s_dwPlayerBotOchaoGuardianVID = 0;
	DWORD s_dwPlayerBotOchaoGuardianSeen = 0;
	DWORD s_dwPlayerBotOchaoGuardianEngaged = 0;
	std::set<DWORD> s_setPlayerBotOchaoGuardianFighters;

	bool IsPlayerBotOchaoBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && s_mapPlayerBotAIStates.find(ch->GetPlayerID()) != s_mapPlayerBotAIStates.end();
	}

	bool IsPlayerBotOchaoForced(LPCHARACTER ch)
	{
		return ch && s_setPlayerBotOchaoForced.count(ch->GetPlayerID()) != 0;
	}

	bool IsPlayerBotOchaoLeaveOrdered(LPCHARACTER ch)
	{
		return ch && s_setPlayerBotOchaoLeave.count(ch->GetPlayerID()) != 0;
	}

	bool IsPlayerBotOchaoHosted()
	{
		return SECTREE_MANAGER::instance().GetMap(PLAYERBOT_MAP_OCHAO) != NULL &&
				SECTREE_MANAGER::instance().GetMap(PLAYERBOT_MAP_ORC_VALLEY) != NULL;
	}

	// The level draw: from ninety-five two bots in three go to the temple;
	// the third keeps the Grotto. A test's sent bot always does.
	bool WantsPlayerBotOchao(LPCHARACTER ch, DWORD draw, bool stoneHunter)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_OCHAO_MIN_LEVEL || !IsPlayerBotOchaoHosted())
			return false;
		if (IsPlayerBotOchaoForced(ch))
			return true;
		return !stoneHunter && (draw % 3U) != 1;
	}

	const TPlayerBotHuntingHub* GetPlayerBotOchaoHubs(size_t& count)
	{
		count = PLAYERBOT_OCHAO_HUB_COUNT;
		return PLAYERBOT_OCHAO_HUBS;
	}

	// ------------------------------------------------------------ the way in

	// Called at the top of TransitionPlayerBotMap. -1: not ours, go on;
	// 0/1: the answer.
	int RoutePlayerBotOchaoTransition(LPCHARACTER ch, TPlayerBotAIState& state,
			long targetMap, long targetX, long targetY, DWORD dwNow, const char* reason)
	{
		if (!ch)
			return -1;
		const DWORD pid = ch->GetPlayerID();
		if (ch->GetMapIndex() == PLAYERBOT_MAP_OCHAO && targetMap != PLAYERBOT_MAP_OCHAO)
		{
			std::map<DWORD, TPlayerBotOchaoTrack>::iterator t = s_mapPlayerBotOchaoTrack.find(pid);
			std::map<DWORD, TPlayerBotOchaoExit>::iterator e = s_mapPlayerBotOchaoExit.find(pid);
			sys_log(0, "OCHAO_BOT: left pid=%u name=%s to=%ld reason=%s via=%s pos=(%ld,%ld) stay_s=%u exit_walk_s=%u stalls=%u kills=%u exp=%llu deaths=%u",
					pid, ch->GetName(), targetMap, reason ? reason : "?",
					e != s_mapPlayerBotOchaoExit.end() ? (e->second.bPortal ? "portal" : (e->second.bNavOnly ? "teleporter_nav" : "teleporter_tree")) : "other",
					ch->GetX(), ch->GetY(),
					t != s_mapPlayerBotOchaoTrack.end() && t->second.dwEntered ? (dwNow - t->second.dwEntered) / 1000 : 0,
					e != s_mapPlayerBotOchaoExit.end() ? (dwNow - e->second.dwStarted) / 1000 : 0,
					e != s_mapPlayerBotOchaoExit.end() ? (unsigned int)e->second.bStalls : 0U,
					t != s_mapPlayerBotOchaoTrack.end() ? t->second.dwKills : 0,
					t != s_mapPlayerBotOchaoTrack.end() ? t->second.ullExp : 0ULL,
					t != s_mapPlayerBotOchaoTrack.end() ? t->second.dwDeaths : 0);
			s_mapPlayerBotOchaoExit.erase(pid);
			s_setPlayerBotOchaoLeave.erase(pid);
			if (t != s_mapPlayerBotOchaoTrack.end())
				t->second.dwEntered = 0;
			return -1;
		}
		if (targetMap != PLAYERBOT_MAP_OCHAO || ch->GetMapIndex() == PLAYERBOT_MAP_OCHAO)
			return -1;
		// The quest's gate, for bots as for players.
		if (ch->GetLevel() < PLAYERBOT_OCHAO_MIN_LEVEL)
		{
			PlayerBotLogThrottled("ochao_level_gate", dwNow,
					"OCHAO_BOT: refused under level %u pid=%u name=%s level=%u reason=%s",
					(unsigned int)PLAYERBOT_OCHAO_MIN_LEVEL, pid, ch->GetName(),
					(unsigned int)ch->GetLevel(), reason ? reason : "?");
			s_mapPlayerBotOchaoCrossing.erase(pid);
			return 0;
		}
		// The Guardian's own warp: through.
		if (reason && strcmp(reason, "ochao_temple_guardian") == 0)
		{
			std::map<DWORD, TPlayerBotOchaoCrossing>::iterator c = s_mapPlayerBotOchaoCrossing.find(pid);
			TPlayerBotOchaoTrack& t = s_mapPlayerBotOchaoTrack[pid];
			t.dwEntered = dwNow;
			t.dwCrossStart = c != s_mapPlayerBotOchaoCrossing.end() ? c->second.dwSince : 0;
			sys_log(0, "OCHAO_BOT: entered pid=%u name=%s level=%u job=%u crossing_s=%u forced=%d",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetJob(),
					c != s_mapPlayerBotOchaoCrossing.end() ? (dwNow - c->second.dwSince) / 1000 : 0,
					IsPlayerBotOchaoForced(ch) ? 1 : 0);
			s_mapPlayerBotOchaoCrossing.erase(pid);
			return -1;
		}
		if (s_mapPlayerBotOchaoCrossing.find(pid) == s_mapPlayerBotOchaoCrossing.end())
		{
			s_mapPlayerBotOchaoCrossing[pid].dwSince = dwNow;
			sys_log(0, "OCHAO_BOT: crossing begins pid=%u name=%s level=%u from=%ld reason=%s",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex(), reason ? reason : "?");
		}
		// Already in the valley: the walk to the Guardian is the travel pass's.
		if (ch->GetMapIndex() == PLAYERBOT_MAP_ORC_VALLEY)
			return 1;
		long valleyX = 0, valleyY = 0;
		GetPlayerBotFrontierArrivalFor(ch, PLAYERBOT_MAP_ORC_VALLEY, valleyX, valleyY);
		return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_ORC_VALLEY, valleyX, valleyY, dwNow,
				"ochao_via_orc_valley") ? 1 : 0;
	}

	// In Orc Valley, from the travel pass: the walk to Straznik Swiatyni.
	// -1: nothing to do here.
	int ManagePlayerBotOchaoCrossing(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->GetMapIndex() != PLAYERBOT_MAP_ORC_VALLEY)
			return -1;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotOchaoCrossing>::iterator c = s_mapPlayerBotOchaoCrossing.find(pid);
		const bool wants = GetPlayerBotFrontierMapForLevel(ch) == PLAYERBOT_MAP_OCHAO;
		if (c == s_mapPlayerBotOchaoCrossing.end())
		{
			// Landed in the valley by its own road (the Portal, a raid) with the
			// temple as its ground: it goes on to him.
			if (!wants || BlocksPlayerBotTravel(ch))
				return -1;
			s_mapPlayerBotOchaoCrossing[pid].dwSince = dwNow;
			sys_log(0, "OCHAO_BOT: crossing begins pid=%u name=%s level=%u from=%ld reason=in_valley",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), ch->GetMapIndex());
		}
		else if (!wants || BlocksPlayerBotTravel(ch))
		{
			sys_log(0, "OCHAO_BOT: crossing dropped pid=%u name=%s wants=%d blocked=%d after_s=%u",
					pid, ch->GetName(), wants ? 1 : 0, BlocksPlayerBotTravel(ch) ? 1 : 0,
					(dwNow - c->second.dwSince) / 1000);
			s_mapPlayerBotOchaoCrossing.erase(c);
			return -1;
		}
		return MovePlayerBotToWorldPortal(ch, state, PLAYERBOT_OCHAO_GUARDIAN_X, PLAYERBOT_OCHAO_GUARDIAN_Y,
				PLAYERBOT_MAP_OCHAO, PLAYERBOT_OCHAO_ARRIVAL_X, PLAYERBOT_OCHAO_ARRIVAL_Y, dwNow,
				"ochao_temple_guardian") ? 1 : 0;
	}

	// ------------------------------------------------------------ the way out

	int ChoosePlayerBotOchaoNode(LPCHARACTER ch)
	{
		CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(PLAYERBOT_MAP_OCHAO);
		if (!nav.Init(PLAYERBOT_MAP_OCHAO))
			return -1;
		std::vector<std::pair<int, int> > order;
		order.reserve(PLAYERBOT_OCHAO_NODE_COUNT);
		for (int i = 0; i < PLAYERBOT_OCHAO_NODE_COUNT; ++i)
			order.push_back(std::make_pair(DISTANCE_APPROX(ch->GetX() - PLAYERBOT_OCHAO_EXIT_TREE[i].x,
					ch->GetY() - PLAYERBOT_OCHAO_EXIT_TREE[i].y), i));
		std::sort(order.begin(), order.end());
		for (size_t k = 0; k < order.size() && order[k].first <= PLAYERBOT_OCHAO_NODE_SIGHT; ++k)
		{
			const int i = order[k].second;
			if (nav.SegmentClearWorld(ch->GetX(), ch->GetY(), PLAYERBOT_OCHAO_EXIT_TREE[i].x, PLAYERBOT_OCHAO_EXIT_TREE[i].y))
			{
				// A corner in sight whose next corner is in sight too: go
				// straight for the next one.
				const int n = PLAYERBOT_OCHAO_EXIT_TREE[i].next;
				if (n >= 0 && nav.SegmentClearWorld(ch->GetX(), ch->GetY(),
						PLAYERBOT_OCHAO_EXIT_TREE[n].x, PLAYERBOT_OCHAO_EXIT_TREE[n].y))
					return n;
				return i;
			}
		}
		return order.empty() ? -1 : order[0].second;
	}

	LPCHARACTER FindPlayerBotOchaoPortal()
	{
		if (!mt2009_ochao::s_dwPortalVID)
			return NULL;
		return mt2009_ochao::FindOnMap(mt2009_ochao::s_dwPortalVID);
	}

	// From the frontier branch of the travel pass, once it has decided the bot
	// leaves the temple for destMap.
	bool MovePlayerBotOutOfOchao(LPCHARACTER ch, TPlayerBotAIState& state,
			long destMap, long destX, long destY, DWORD dwNow, const char* reason)
	{
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotOchaoExit>::iterator it = s_mapPlayerBotOchaoExit.find(pid);
		if (it == s_mapPlayerBotOchaoExit.end())
		{
			it = s_mapPlayerBotOchaoExit.insert(std::make_pair(pid, TPlayerBotOchaoExit())).first;
			it->second.dwStarted = dwNow;
			strlcpy(it->second.szReason, reason ? reason : "?", sizeof(it->second.szReason));
			sys_log(0, "OCHAO_BOT: leaving pid=%u name=%s reason=%s pos=(%ld,%ld) to=%ld ordered=%d",
					pid, ch->GetName(), reason ? reason : "?", ch->GetX(), ch->GetY(), destMap,
					IsPlayerBotOchaoLeaveOrdered(ch) ? 1 : 0);
		}
		TPlayerBotOchaoExit& exit = it->second;
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		// The Guardian's Portal, while it stands and the bot is near it.
		LPCHARACTER portal = FindPlayerBotOchaoPortal();
		if (portal)
		{
			const int d = DISTANCE_APPROX(ch->GetX() - portal->GetX(), ch->GetY() - portal->GetY());
			CPlayerBotNavigation& nav = CPlayerBotNavigation::instance(PLAYERBOT_MAP_OCHAO);
			if (exit.bPortal || (d <= PLAYERBOT_OCHAO_PORTAL_REACH && nav.Init(PLAYERBOT_MAP_OCHAO) &&
					nav.CanReach(ch->GetX(), ch->GetY(), portal->GetX(), portal->GetY())))
			{
				if (!exit.bPortal)
					sys_log(0, "OCHAO_BOT: takes the portal pid=%u name=%s distance=%d", pid, ch->GetName(), d);
				exit.bPortal = true;
				return MovePlayerBotToWorldPortal(ch, state, portal->GetX(), portal->GetY(),
						PLAYERBOT_MAP_ORC_VALLEY, PLAYERBOT_OCHAO_PORTAL_TO_X, PLAYERBOT_OCHAO_PORTAL_TO_Y,
						dwNow, "ochao_portal");
			}
		}
		else if (exit.bPortal)
		{
			// Closed before the bot got there: the Teleporter after all.
			exit.bPortal = false;
			exit.iNode = -1;
			sys_log(0, "OCHAO_BOT: portal closed on the way pid=%u name=%s", pid, ch->GetName());
		}

		// The Teleporter: straight to him from the last corner, or on the
		// navigation alone once the corners have failed.
		if (exit.bNavOnly || exit.iNode == 0)
			return MovePlayerBotToWorldPortal(ch, state, PLAYERBOT_OCHAO_EXIT_X, PLAYERBOT_OCHAO_EXIT_Y,
					destMap, destX, destY, dwNow, reason);

		if (exit.iNode < 0)
		{
			exit.iNode = ChoosePlayerBotOchaoNode(ch);
			exit.dwLegSince = 0;
			if (exit.iNode < 0)
			{
				exit.bNavOnly = true;
				return MovePlayerBotToWorldPortal(ch, state, PLAYERBOT_OCHAO_EXIT_X, PLAYERBOT_OCHAO_EXIT_Y,
						destMap, destX, destY, dwNow, reason);
			}
			ClearPlayerBotRoute(state, true);
		}
		long nodeX = PLAYERBOT_OCHAO_EXIT_TREE[exit.iNode].x;
		long nodeY = PLAYERBOT_OCHAO_EXIT_TREE[exit.iNode].y;
		int distance = DISTANCE_APPROX(ch->GetX() - nodeX, ch->GetY() - nodeY);
		if (distance <= PLAYERBOT_OCHAO_NODE_REACHED)
		{
			exit.iNode = PLAYERBOT_OCHAO_EXIT_TREE[exit.iNode].next;
			exit.dwLegSince = 0;
			ClearPlayerBotRoute(state, true);
			if (exit.iNode <= 0)
			{
				exit.iNode = 0;
				return MovePlayerBotToWorldPortal(ch, state, PLAYERBOT_OCHAO_EXIT_X, PLAYERBOT_OCHAO_EXIT_Y,
						destMap, destX, destY, dwNow, reason);
			}
			nodeX = PLAYERBOT_OCHAO_EXIT_TREE[exit.iNode].x;
			nodeY = PLAYERBOT_OCHAO_EXIT_TREE[exit.iNode].y;
			distance = DISTANCE_APPROX(ch->GetX() - nodeX, ch->GetY() - nodeY);
		}
		if (exit.dwLegSince == 0 || distance + PLAYERBOT_OCHAO_LEG_PROGRESS <= exit.iLegBest)
		{
			exit.dwLegSince = dwNow;
			exit.iLegBest = distance;
		}
		else if (dwNow - exit.dwLegSince >= PLAYERBOT_OCHAO_LEG_TIMEOUT)
		{
			++exit.bStalls;
			sys_log(0, "OCHAO_BOT: exit leg stalled pid=%u name=%s node=%d pos=(%ld,%ld) node_pos=(%ld,%ld) distance=%d stalls=%u",
					pid, ch->GetName(), exit.iNode, ch->GetX(), ch->GetY(), nodeX, nodeY, distance,
					(unsigned int)exit.bStalls);
			exit.dwLegSince = 0;
			exit.iNode = -1;
			ClearPlayerBotRoute(state, true);
			if (exit.bStalls >= PLAYERBOT_OCHAO_MAX_STALLS)
				exit.bNavOnly = true;
			return true;
		}
		MovePlayerBot(ch, nodeX, nodeY, dwNow, 6, true, true, false, true);
		return true;
	}

	// ------------------------------------------------------------ the kills

	void NoteOchaoBotKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || killer->GetMapIndex() != PLAYERBOT_MAP_OCHAO ||
				!IsPlayerBotOchaoBot(killer))
			return;
		TPlayerBotOchaoTrack& t = s_mapPlayerBotOchaoTrack[killer->GetPlayerID()];
		++t.dwKills;
		const DWORD race = victim->GetRaceNum();
		if (race == mt2009_ochao::GUARDIAN_VNUM || race == 6311 || race == 6390)
		{
			++t.dwBossKills;
			const DWORD dwNow = get_dword_time();
			sys_log(0, "OCHAO_BOT: boss killed race=%u name=%s killer=%u pos=(%ld,%ld) fighters=%u since_spawn_s=%u since_engaged_s=%u",
					race, victim->GetName(), killer->GetPlayerID(), victim->GetX(), victim->GetY(),
					race == mt2009_ochao::GUARDIAN_VNUM ? (unsigned int)s_setPlayerBotOchaoGuardianFighters.size() : 0U,
					race == mt2009_ochao::GUARDIAN_VNUM && s_dwPlayerBotOchaoGuardianSeen ? (dwNow - s_dwPlayerBotOchaoGuardianSeen) / 1000 : 0,
					race == mt2009_ochao::GUARDIAN_VNUM && s_dwPlayerBotOchaoGuardianEngaged ? (dwNow - s_dwPlayerBotOchaoGuardianEngaged) / 1000 : 0);
		}
	}

	// ------------------------------------------------------------ the test hook and the watch

	std::vector<DWORD> CollectPlayerBotOchaoCandidates(bool onTemple)
	{
		std::vector<DWORD> out;
		for (TPlayerBotAIStateMap::iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsPC() || ch->IsDead())
				continue;
			if (onTemple != (ch->GetMapIndex() == PLAYERBOT_MAP_OCHAO))
				continue;
			if (!onTemple && (ch->GetLevel() < PLAYERBOT_OCHAO_MIN_LEVEL ||
					(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()))))
				continue;
			out.push_back(it->first);
		}
		return out;
	}

	void RunPlayerBotOchaoTestFile(DWORD dwNow)
	{
		FILE* fp = fopen(PLAYERBOT_OCHAO_TEST_FILE, "r");
		if (!fp)
			return;
		char line[128];
		std::vector<std::string> lines;
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_OCHAO_TEST_FILE);
		rename(PLAYERBOT_OCHAO_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "";
			int n = 0;
			if (sscanf(lines[l].c_str(), "%31s %d", cmd, &n) < 1)
				continue;
			if (!strcmp(cmd, "send"))
			{
				std::vector<DWORD> pids = CollectPlayerBotOchaoCandidates(false);
				int sent = 0, failed = 0;
				for (size_t i = 0; i < pids.size() && sent < n; ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
					TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pids[i]);
					if (!ch || st == s_mapPlayerBotAIStates.end())
						continue;
					s_setPlayerBotOchaoForced.insert(pids[i]);
					s_mapPlayerBotOchaoTrack[pids[i]].dwCrossStart = dwNow;
					if (TransitionPlayerBotMap(ch, st->second, PLAYERBOT_MAP_OCHAO,
							PLAYERBOT_OCHAO_ARRIVAL_X, PLAYERBOT_OCHAO_ARRIVAL_Y, dwNow, "ochao_test_send"))
						++sent;
					else
						++failed;
				}
				sys_log(0, "OCHAO_BOT: test send asked=%d sent=%d failed=%d candidates=%u",
						n, sent, failed, (unsigned int)pids.size());
			}
			else if (!strcmp(cmd, "leave") || !strcmp(cmd, "leaveall"))
			{
				std::vector<DWORD> pids = CollectPlayerBotOchaoCandidates(true);
				int ordered = 0;
				for (size_t i = 0; i < pids.size() && (!strcmp(cmd, "leaveall") || ordered < n); ++i)
				{
					if (s_setPlayerBotOchaoLeave.count(pids[i]))
						continue;
					s_setPlayerBotOchaoLeave.insert(pids[i]);
					s_setPlayerBotOchaoForced.erase(pids[i]);
					++ordered;
				}
				sys_log(0, "OCHAO_BOT: test leave ordered=%d on_map=%u", ordered, (unsigned int)pids.size());
			}
			else if (!strcmp(cmd, "reset"))
			{
				s_setPlayerBotOchaoForced.clear();
				s_setPlayerBotOchaoLeave.clear();
				sys_log(0, "OCHAO_BOT: test reset");
			}
		}
	}

	// Every second from the temple's clock (playerbot_ochao.h).
	void TickPlayerBotOchao()
	{
		const DWORD dwNow = get_dword_time();
		static DWORD s_dwNextFile = 0, s_dwNextTrack = 0;
		if (dwNow >= s_dwNextFile)
		{
			s_dwNextFile = dwNow + 5000;
			RunPlayerBotOchaoTestFile(dwNow);
		}

		// The Guardian: when he appears, when a bot first fights him.
		LPCHARACTER guardian = mt2009_ochao::FindOnMap(mt2009_ochao::s_dwGuardianVID);
		if (guardian && guardian->GetVID() != s_dwPlayerBotOchaoGuardianVID)
		{
			s_dwPlayerBotOchaoGuardianVID = guardian->GetVID();
			s_dwPlayerBotOchaoGuardianSeen = dwNow;
			s_dwPlayerBotOchaoGuardianEngaged = 0;
			s_setPlayerBotOchaoGuardianFighters.clear();
		}

		const bool writeTrack = dwNow >= s_dwNextTrack;
		FILE* out = NULL;
		if (writeTrack)
		{
			s_dwNextTrack = dwNow + PLAYERBOT_OCHAO_TRACK_MS;
			out = fopen(PLAYERBOT_OCHAO_TRACK_FILE, "a");
		}
		const time_t wall = time(0);
		int onMap = 0, crossing = 0;
		for (TPlayerBotAIStateMap::iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			const DWORD pid = it->first;
			const bool isCrossing = s_mapPlayerBotOchaoCrossing.count(pid) != 0;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch)
				continue;
			const bool here = ch->GetMapIndex() == PLAYERBOT_MAP_OCHAO;
			if (!here && !isCrossing)
				continue;
			TPlayerBotAIState& state = it->second;
			TPlayerBotOchaoTrack& t = s_mapPlayerBotOchaoTrack[pid];
			if (here)
			{
				++onMap;
				if (t.dwEntered == 0)
				{
					t.dwEntered = dwNow;
					t.dwAnchorSince = dwNow;
				}
				// Experience, across a level too.
				const DWORD exp = ch->GetExp();
				if (t.bLastLevel == 0)
				{
					t.bLastLevel = ch->GetLevel();
					t.dwLastExp = exp;
					t.dwLastNext = ch->GetNextExp();
				}
				else if (ch->GetLevel() > t.bLastLevel)
				{
					if (t.dwLastNext > t.dwLastExp)
						t.ullExp += t.dwLastNext - t.dwLastExp;
					t.ullExp += exp;
					sys_log(0, "OCHAO_BOT: level up pid=%u name=%s level=%u", pid, ch->GetName(), (unsigned int)ch->GetLevel());
				}
				else if (exp > t.dwLastExp)
					t.ullExp += exp - t.dwLastExp;
				t.bLastLevel = ch->GetLevel();
				t.dwLastExp = exp;
				t.dwLastNext = ch->GetNextExp();
				// Deaths.
				if (ch->IsDead() && !t.bWasDead)
				{
					++t.dwDeaths;
					sys_log(0, "OCHAO_BOT: died pid=%u name=%s pos=(%ld,%ld)", pid, ch->GetName(), ch->GetX(), ch->GetY());
				}
				t.bWasDead = ch->IsDead();
				// The Guardian's fighters.
				if (guardian && (ch->GetVictim() == guardian || guardian->GetVictim() == ch ||
						state.dwTargetVID == guardian->GetVID()))
				{
					if (s_dwPlayerBotOchaoGuardianEngaged == 0)
					{
						s_dwPlayerBotOchaoGuardianEngaged = dwNow;
						sys_log(0, "OCHAO_BOT: guardian engaged first=%u name=%s after_spawn_s=%u pos=(%ld,%ld)",
								pid, ch->GetName(), (dwNow - s_dwPlayerBotOchaoGuardianSeen) / 1000,
								guardian->GetX(), guardian->GetY());
					}
					s_setPlayerBotOchaoGuardianFighters.insert(pid);
				}
				// Stuck: no ground covered for a minute with nothing fought.
				const bool fighting = ch->GetVictim() != NULL ||
						(state.dwLastCombatActionTime != 0 && dwNow - state.dwLastCombatActionTime < 10000);
				if (fighting || ch->IsDead() ||
						DISTANCE_APPROX(ch->GetX() - t.lAnchorX, ch->GetY() - t.lAnchorY) > PLAYERBOT_OCHAO_STUCK_DISTANCE)
				{
					if (t.bStuck)
						sys_log(0, "OCHAO_BOT: unstuck pid=%u name=%s after_s=%u", pid, ch->GetName(), (dwNow - t.dwAnchorSince) / 1000);
					t.bStuck = false;
					t.lAnchorX = ch->GetX();
					t.lAnchorY = ch->GetY();
					t.dwAnchorSince = dwNow;
				}
				else if (!t.bStuck && dwNow - t.dwAnchorSince >= PLAYERBOT_OCHAO_STUCK_MS)
				{
					t.bStuck = true;
					++t.dwStuckEpisodes;
					sys_log(0, "OCHAO_BOT: stuck pid=%u name=%s pos=(%ld,%ld) action=%u route=%u/%u leaving=%d",
							pid, ch->GetName(), ch->GetX(), ch->GetY(), (unsigned int)state.bCurrentAction,
							(unsigned int)state.uRouteIndex, (unsigned int)state.vecRoute.size(),
							s_mapPlayerBotOchaoExit.count(pid) ? 1 : 0);
				}
				if (t.bStuck)
					t.dwStuckMs += 1000;
			}
			else
				++crossing;
			if (out)
			{
				LPCHARACTER victim = ch->GetVictim();
				fprintf(out, "%ld\t%u\t%s\t%u\t%u\t%ld\t%ld\t%ld\t%d\t%u\t%u\t%llu\t%u\t%u\t%d\t%d\t%u\t%u\t%u\n",
						(long)wall, pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)(ch->GetJob() % 4),
						ch->GetMapIndex(), ch->GetX(), ch->GetY(),
						ch->GetMaxHP() > 0 ? (int)(ch->GetHP() * 100LL / ch->GetMaxHP()) : 0,
						(unsigned int)state.bCurrentAction, t.dwKills, t.ullExp, t.dwDeaths, t.dwStuckEpisodes,
						t.bStuck ? 1 : 0, s_mapPlayerBotOchaoExit.count(pid) ? 1 : (isCrossing ? 2 : 0),
						victim ? (unsigned int)victim->GetRaceNum() : 0U, t.dwBossKills, t.dwStuckMs / 1000);
			}
		}
		if (out)
		{
			fprintf(out, "#\t%ld\ton_map=%d\tcrossing=%d\tguardian=%u\tguardian_fighters=%u\tportal=%u\n",
					(long)wall, onMap, crossing, guardian ? (unsigned int)guardian->GetVID() : 0U,
					(unsigned int)s_setPlayerBotOchaoGuardianFighters.size(), (unsigned int)mt2009_ochao::s_dwPortalVID);
			fclose(out);
		}
	}
}

#endif
