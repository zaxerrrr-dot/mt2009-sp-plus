// MT2009_PLUS_SHIP_DEFENSE_V1: Obrona Statku (Hydra) - the ship's waves, server-patches/shipdefense/README.md.
// From Owsap's v6.2.6 defense_wave.cpp (CDefenseWave, Autor: Owsap), rewritten for our engine:
//  - a separate object per private map of 367, not a CDungeon subclass (ours has no virtuals);
//  - one 1-second tick per instance instead of Owsap's event per timer, so the egg's and the
//    intro head's purge no longer share one event slot (Owsap: the second cancelled the first);
//  - the wave-4 "debuff" starts when the Hydra is at or under half HP (Owsap tested
//    m_pDebuffEvent != NULL, so it never started), the portal's "%d minutes" says the real
//    time left (Owsap printed 0), a time limit after the start (Owsap had none);
//  - the mast's HP goes to the people on the ship as the chat command "ShipMastHP <hp> <max>"
//    ("ShipMastHP 0 0": hide) - no new packet, the exe stays as it is; the laser is the
//    existing specific-effect packet (defense_mini_laser.mse), no new SE_* number;
//  - monsters may strike the mast (an NPC) only here, the heads neither strike nor take damage.
// The intro of wave 1 is Owsap's: the full Hydra model (3961) rises behind the ship for four
// seconds and is purged - the left head 3963 has only a "wait" motion, so it is not an intro.
#include "stdafx.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "mob_manager.h"
#include "dungeon.h"
#include "sectree_manager.h"
#include "questmanager.h"
#include "locale_service.h"
#include "desc.h"
#include "affect.h"
#include "cmd.h"
#include "item.h"
#include "playerbot_ship_defense.h"

#include <algorithm>
#include <cstdlib>

using namespace ship_defense;

namespace
{
	const char* const LASER_EFFECT = "d:/ymir work/effect/monster2/defense_mini_laser.mse";

	struct SCfgDefault
	{
		const char* name;
		int value;
	};

	// The defaults. The quest (obrona_statku.quest) reads min_level, party_only, fee, cooldown, daily_limit
	// with dw.cfg(); the rest is the C++ side's timing. The owner's decisions of 13 October 2026
	// (cache/yohara/decyzje.md): level 90, party or alone, 5 000 000 Yang, no rest, 10 entries a day.
	const SCfgDefault s_aCfg[] =
	{
		{ "min_level",		90 },	// wejscie od poziomu (GF: 90)
		{ "party_only",		0 },	// 0: druzyna albo solo, 1: tylko druzyna (Owsap/GF)
		{ "fee",		5000000 },	// oplata w yangach (wlasciciel: 5kk; bez oplaty: flaga -1)
		{ "cooldown",		0 },	// odpoczynek botow po wejsciu, s (wlasciciel: bez przerwy; GF: 30 min)
		{ "daily_limit",	10 },	// wejsc dziennie (wlasciciel: 10; bez limitu: flaga -1)
		{ "max_instances",	8 },	// statkow naraz na rdzen
		{ "idle_destroy",	600 },	// nieuruszony statek znika po, s (Owsap: 10 min)
		{ "time_limit",		1800 },	// limit po starcie, s (Owsap: brak)
		{ "wave1_countdown",	60 },	// odliczanie przed fala 1, s
		{ "wave1_time",		120 },	// fala 1: obrona masztu, s
		{ "wave_countdown",	10 },	// odliczanie przed falami 2-4, s
		{ "between_waves",	6 },	// po Hydrze do przygotowania nastepnej fali, s
		{ "end_time",		300 },	// po zwyciestwie na portal, s
		{ "lose_exit",		10 },	// po porazce do wyjscia, s
		{ "egg_first",		30 },	// pierwsze Jajo Hydry po starcie fali, s
		{ "egg_interval",	40 },	// kolejne Jaja, s
		{ "egg_life",		8 },	// Jajo znika po, s
		{ "spawn_respawn",	30 },	// zabite Potomstwo Hydry wraca po, s
		{ "summon_interval",	30 },	// Potomstwo przywoluje kappy co, s
		{ "summon_cap",		40 },	// najwiecej kapp naraz (Owsap: bez limitu)
		{ "laser_interval",	15 },	// laser Potomstwa co, s
		{ "laser_mast_pct",	0 },	// nieprzechwycony laser zabiera masztowi % PZ (Owsap: 0 - tylko efekt)
		{ "repair_pct",		1 },	// deska naprawia maszt o %
		{ "repair_stun",	5 },	// ogluszenie naprawiajacego, s
		{ "debuff_hp_pct",	50 },	// fala 4: od tylu % PZ Hydry potwory traca wzmocnienia
		{ "debuff_interval",	10 },	// co, s
		{ "chest_uses",		3 },	// MT2009_PLUS_SHIP_DEFENSE_V1 (hydra chest): Skrzynia Hydry (54705) otwiera sie tyle razy
	};

	struct FCollectChars
	{
		std::vector<DWORD> pcs;
		std::vector<DWORD> others;

		void operator() (LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER ch = static_cast<LPCHARACTER>(ent);
			if (ch->IsPC())
				pcs.push_back(ch->GetVID());
			else
				others.push_back(ch->GetVID());
		}
	};

	bool IsHydra(DWORD v) { return v == VNUM_HYDRA_1 || v == VNUM_HYDRA_2 || v == VNUM_HYDRA_3; }
	bool IsSpawn(DWORD v) { return v == VNUM_SPAWN_1 || v == VNUM_SPAWN_2 || v == VNUM_SPAWN_3; }
	bool IsHead(DWORD v) { return v == VNUM_HEAD_LEFT || v == VNUM_HEAD_RIGHT; }
	bool IsPawn(DWORD v) { return v == VNUM_PAWN_1 || v == VNUM_PAWN_2 || v == VNUM_PAWN_3; }

	// Positions, the map's local cells (Owsap's).
	const int MAST_X = 385, MAST_Y = 400;
	const int WHEEL_X = 385, WHEEL_Y = 367;
	const int HYDRA_X = 385, HYDRA_Y = 373;
	const int START_X = 387, START_Y = 359;	// Town.txt
	const int aSpawnPos[SLOT_COUNT][2] = { { 396, 389 }, { 396, 411 }, { 374, 411 }, { 374, 389 } };
	const int aSummonPos[SLOT_COUNT][2] = { { 405, 385 }, { 406, 418 }, { 365, 418 }, { 365, 386 } };
	const int aLaserPos[SLOT_COUNT][2] = { { 390, 394 }, { 390, 405 }, { 379, 405 }, { 379, 394 } };
	const int aWallPos[4][2] = { { 400, 372 }, { 369, 372 }, { 400, 435 }, { 369, 435 } };
	const int aHeadRightPos[3][2] = { { 378, 443 }, { 385, 439 }, { 392, 443 } };

	int SpawnSlotsOfWave(BYTE bWave)
	{
		switch (bWave)
		{
			case WAVE2: return 1;
			case WAVE3: return 2;
			case WAVE4: return 4;
		}
		return 0;
	}

	EVENTINFO(ship_defense_event_info)
	{
		long lMapIndex;

		ship_defense_event_info() : lMapIndex(0) {}
	};

	EVENTFUNC(ship_defense_tick_event)
	{
		ship_defense_event_info* info = dynamic_cast<ship_defense_event_info*>(event->info);
		if (!info)
			return 0;

		CShipDefense* pShip = CShipDefenseManager::instance().Find(info->lMapIndex);
		if (!pShip)
			return 0;

		pShip->Tick();

		// Tick may have ended it; look it up again rather than trust the pointer.
		pShip = CShipDefenseManager::instance().Find(info->lMapIndex);
		if (!pShip)
			return 0;
		if (pShip->GetState() == STATE_CLOSED)
		{
			pShip->m_pTickEvent = NULL;
			return 0;
		}
		return PASSES_PER_SEC(1);
	}
}

int ship_defense::Cfg(const char* name)
{
	int def = 0;
	bool known = false;
	for (size_t i = 0; i < sizeof(s_aCfg) / sizeof(s_aCfg[0]); ++i)
	{
		if (!strcmp(s_aCfg[i].name, name))
		{
			def = s_aCfg[i].value;
			known = true;
			break;
		}
	}
	if (!known)
		sys_err("ship defense: unknown setting %s", name);

	char flag[64];
	snprintf(flag, sizeof(flag), "shipdef_%s", name);
	const int v = quest::CQuestManager::instance().GetEventFlag(flag);
	if (v < 0)
		return 0;
	return v ? v : def;
}

///////////////////////////////////////////////////////////////////////////////////////////
// CShipDefense
///////////////////////////////////////////////////////////////////////////////////////////

CShipDefense::CShipDefense(long lMapIndex, DWORD dwDungeonID)
	: m_pTickEvent(NULL), m_lMapIndex(lMapIndex), m_dwDungeonID(dwDungeonID),
	m_bWave(WAVE0), m_bState(STATE_IDLE), m_bNextWave(WAVE0),
	m_dwMast(0), m_dwWheel(0), m_dwHydra(0), m_dwIntro(0), m_dwEgg(0), m_dwReward(0), m_dwPortal(0),
	m_tCreated(get_global_time()), m_tStarted(0), m_tStateEnd(0), m_tWaveEnd(0),
	m_tIntroPurgeAt(0), m_tNextEgg(0), m_tEggPurgeAt(0), m_tNextSummon(0), m_tNextDebuff(0),
	m_bMastDied(false), m_bHydraDied(false), m_bEggDied(false), m_iLastMastHP(-1), m_iLastNoticePct(101)
{
	for (int i = 0; i < 3; ++i)
		m_adwHeadRight[i] = 0;
	for (int i = 0; i < 4; ++i)
		m_adwWall[i] = 0;
	for (int i = 0; i < SLOT_COUNT; ++i)
	{
		m_adwSpawn[i] = 0;
		m_abLaser[i] = false;
		m_atSpawnAt[i] = 0;
		m_atLaserAt[i] = 0;
	}
}

CShipDefense::~CShipDefense()
{
	event_cancel(&m_pTickEvent);
}

LPDUNGEON CShipDefense::GetDungeon() const
{
	LPDUNGEON pDungeon = CDungeonManager::instance().Find(m_dwDungeonID);
	if (pDungeon && pDungeon->GetMapIndex() == m_lMapIndex)
		return pDungeon;
	return NULL;
}

LPSECTREE_MAP CShipDefense::GetSectreeMap() const
{
	return SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
}

LPCHARACTER CShipDefense::Find(DWORD dwVID) const
{
	if (!dwVID)
		return NULL;
	LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(dwVID);
	if (!ch || ch->IsDead() || ch->GetMapIndex() != m_lMapIndex)
		return NULL;
	return ch;
}

LPCHARACTER CShipDefense::GetMast() const
{
	return Find(m_dwMast);
}

int CShipDefense::GetMastHPPct() const
{
	LPCHARACTER pMast = GetMast();
	return pMast ? pMast->GetHPPct() : 0;
}

// As Owsap's SpawnMob: straight onto the cell - the Hydra, the heads and the mast stand on
// cells the map blocks, where CHARACTER_MANAGER::SpawnMob refuses a monster.
LPCHARACTER CShipDefense::SpawnAt(DWORD dwVnum, int iX, int iY, int iDir, bool bSpawnMotion, bool bFightMast)
{
	LPSECTREE_MAP pMap = GetSectreeMap();
	LPDUNGEON pDungeon = GetDungeon();
	if (!pMap || !pDungeon)
		return NULL;

	const CMob* pMob = CMobManager::instance().Get(dwVnum);
	if (!pMob)
	{
		sys_err("ship defense: no mob_proto row for %u", dwVnum);
		return NULL;
	}

	const long lX = pMap->m_setting.iBaseX + iX * 100;
	const long lY = pMap->m_setting.iBaseY + iY * 100;
	if (!SECTREE_MANAGER::instance().Get(m_lMapIndex, lX, lY))
	{
		sys_err("ship defense: no sectree at %d %d on %ld", iX, iY, m_lMapIndex);
		return NULL;
	}

	LPCHARACTER ch = CHARACTER_MANAGER::instance().CreateCharacter(pMob->m_table.szLocaleName);
	if (!ch)
		return NULL;

	ch->SetProto(pMob);
	ch->SetRotation(static_cast<float>(iDir == 0 ? number(0, 359) : (iDir - 1) * 45));

	if (!ch->Show(m_lMapIndex, lX, lY, 0, bSpawnMotion))
	{
		M2_DESTROY_CHARACTER(ch);
		sys_err("ship defense: cannot show %u at %d %d", dwVnum, iX, iY);
		return NULL;
	}

	ch->SetDungeon(pDungeon);

	if (ch->IsMonster())
	{
		ch->StartStateMachine();
		if (bFightMast)
		{
			LPCHARACTER pMast = GetMast();
			if (pMast && ch->CanBeginFight())
				ch->BeginFight(pMast);
		}
	}
	return ch;
}

void CShipDefense::Purge(DWORD& dwVID)
{
	if (!dwVID)
		return;
	LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(dwVID);
	dwVID = 0;
	if (ch && !ch->IsPC() && ch->GetMapIndex() == m_lMapIndex)
		M2_DESTROY_CHARACTER(ch);
}

void CShipDefense::Notice(BYTE bChatType, const char* szText)
{
	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMap)
		return;
	FCollectChars f;
	pMap->for_each(f);
	for (size_t i = 0; i < f.pcs.size(); ++i)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(f.pcs[i]);
		if (ch && ch->GetDesc())
			ch->ChatPacket(bChatType, "%s", szText);
	}
}

void CShipDefense::SendMastHPTo(LPCHARACTER pChar)
{
	if (!pChar || !pChar->GetDesc())
		return;
	LPCHARACTER pMast = GetMast();
	if (!pMast || !IsStarted() || m_bState == STATE_CLOSED)
		pChar->ChatPacket(CHAT_TYPE_COMMAND, "ShipMastHP 0 0");
	else
		pChar->ChatPacket(CHAT_TYPE_COMMAND, "ShipMastHP %d %d", pMast->GetHP(), pMast->GetMaxHP());
}

// At most once a second, and only when the HP changed. The notices at 30%, 10% and 5..1% (Owsap).
void CShipDefense::SendMastHP(bool bForce)
{
	LPCHARACTER pMast = GetMast();
	const int iHP = pMast ? pMast->GetHP() : 0;
	if (!bForce && iHP == m_iLastMastHP)
		return;
	m_iLastMastHP = iHP;

	LPSECTREE_MAP pMap = GetSectreeMap();
	if (pMap)
	{
		FCollectChars f;
		pMap->for_each(f);
		for (size_t i = 0; i < f.pcs.size(); ++i)
			SendMastHPTo(CHARACTER_MANAGER::instance().Find(f.pcs[i]));
	}

	if (!pMast || m_bState == STATE_CLOSED)
		return;

	static const int aStage[] = { 30, 10, 5, 4, 3, 2, 1 };
	const int iPct = pMast->GetHPPct();
	int iStage = 101;
	for (size_t i = 0; i < sizeof(aStage) / sizeof(aStage[0]); ++i)
		if (iPct <= aStage[i])
			iStage = aStage[i];

	if (iStage < m_iLastNoticePct)
	{
		char buf[256];
		snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: the mast has %d%% HP left!"), iPct);
		Notice(CHAT_TYPE_BIG_NOTICE, buf);
	}
	m_iLastNoticePct = iStage;	// a repair lifts it again, so the notice can come back
}

void CShipDefense::Initialize()
{
	// Not CDungeon uniques: a unique destroyed without dying stays in the dungeon's map as a
	// dangling pointer - the ship keeps its own VIDs (and d.kill_all/d.purge skip them, edits.json).
	LPCHARACTER pMast = SpawnAt(VNUM_MAST, MAST_X, MAST_Y, 1, false, false);
	LPCHARACTER pWheel = SpawnAt(VNUM_WHEEL, WHEEL_X, WHEEL_Y, 1, false, false);
	m_dwMast = pMast ? pMast->GetVID() : 0;
	m_dwWheel = pWheel ? pWheel->GetVID() : 0;
	CreateWalls();

	if (!m_pTickEvent)
	{
		ship_defense_event_info* info = AllocEventInfo<ship_defense_event_info>();
		info->lMapIndex = m_lMapIndex;
		m_pTickEvent = event_create(ship_defense_tick_event, info, PASSES_PER_SEC(1));
	}
	sys_log(0, "SHIP_DEFENSE: instance %ld ready (mast %u wheel %u)", m_lMapIndex, m_dwMast, m_dwWheel);
}

bool CShipDefense::Start()
{
	if (m_bState != STATE_IDLE)
		return false;
	if (!GetMast())
	{
		sys_err("ship defense: %ld has no mast, closing", m_lMapIndex);
		Close(true);
		return false;
	}
	m_tStarted = get_global_time();
	m_iLastMastHP = -1;
	SendMastHP(true);
	PrepareWave(WAVE1);
	sys_log(0, "SHIP_DEFENSE: instance %ld started", m_lMapIndex);
	return true;
}

void CShipDefense::CreateWalls()
{
	for (int i = 0; i < 4; ++i)
	{
		if (Find(m_adwWall[i]))
			continue;
		LPCHARACTER ch = SpawnAt(VNUM_WALL, aWallPos[i][0], aWallPos[i][1], 1, false, false);
		m_adwWall[i] = ch ? ch->GetVID() : 0;
	}
}

void CShipDefense::RemoveBackWalls()
{
	Purge(m_adwWall[0]);
	Purge(m_adwWall[1]);
}

void CShipDefense::RemoveFrontWalls()
{
	Purge(m_adwWall[2]);
	Purge(m_adwWall[3]);
}

void CShipDefense::JumpToStart()
{
	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMap)
		return;
	const long lX = pMap->m_setting.iBaseX + START_X * 100;
	const long lY = pMap->m_setting.iBaseY + START_Y * 100;
	FCollectChars f;
	pMap->for_each(f);
	for (size_t i = 0; i < f.pcs.size(); ++i)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(f.pcs[i]);
		if (!ch || ch->GetMapIndex() != m_lMapIndex)
			continue;
		ch->Show(m_lMapIndex, lX + number(-200, 200), lY + number(-100, 100), 0);
		ch->Stop();
	}
}

// Every monster and stone but the KING rank (the Hydra, the heads, the treasure); with
// bKeepSirenQueen (an egg) the Siren Queen and the repair planks stay as well.
void CShipDefense::ClearMobs(bool bKeepSirenQueen)
{
	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMap)
		return;
	FCollectChars f;
	pMap->for_each(f);
	for (size_t i = 0; i < f.others.size(); ++i)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(f.others[i]);
		if (!ch || ch->IsDead() || ch->GetMapIndex() != m_lMapIndex)
			continue;
		const DWORD v = ch->GetRaceNum();
		if (ch->IsMonster())
		{
			if (ch->GetMobRank() == MOB_RANK_KING)
				continue;
			if (bKeepSirenQueen && v == VNUM_SIREN_QUEEN)
				continue;
		}
		else if (ch->IsStone())
		{
			if (bKeepSirenQueen && v == VNUM_WOOD)
				continue;
		}
		else
			continue;
		ch->DeadNoReward();
	}
}

void CShipDefense::ClearWave()
{
	LPDUNGEON pDungeon = GetDungeon();
	if (pDungeon)
		pDungeon->ClearRegen();
	ClearMobs(false);
	for (int i = 0; i < SLOT_COUNT; ++i)
	{
		m_adwSpawn[i] = 0;
		m_abLaser[i] = false;
		m_atSpawnAt[i] = 0;
		m_atLaserAt[i] = 0;
	}
	m_dwEgg = 0;
	m_tEggPurgeAt = 0;
	m_tNextEgg = 0;
	m_tNextSummon = 0;
	m_tNextDebuff = 0;
}

void CShipDefense::PrepareWave(BYTE bWave)
{
	if (bWave < WAVE1 || bWave > WAVE4)
		return;

	ClearWave();
	m_bNextWave = bWave;
	m_bState = STATE_COUNTDOWN;
	char buf[256];

	if (bWave == WAVE1)
	{
		// Owsap's intro: the Hydra rises behind the ship, plays its third attack and is gone.
		if (!Find(m_dwIntro))
		{
			LPCHARACTER pIntro = SpawnAt(VNUM_HYDRA_2, HYDRA_X, 378, 5, false, false);
			if (pIntro)
			{
				m_dwIntro = pIntro->GetVID();
				pIntro->SendMovePacket(FUNC_MOB_SKILL, 2, pIntro->GetX(), pIntro->GetY(), 0, get_dword_time());
				m_tIntroPurgeAt = get_global_time() + 4;
			}
		}
		for (int i = 0; i < 3; ++i)
		{
			if (Find(m_adwHeadRight[i]))
				continue;
			LPCHARACTER ch = SpawnAt(VNUM_HEAD_RIGHT, aHeadRightPos[i][0], aHeadRightPos[i][1], 5, false, false);
			m_adwHeadRight[i] = ch ? ch->GetVID() : 0;
		}
		Notice(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Ship defense: sea monsters attack us! Get ready to fight!"));
		snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: wave %d - protect the mast for %d sec."), (int)bWave, Cfg("wave1_time"));
		Notice(CHAT_TYPE_BIG_NOTICE, buf);
		m_tStateEnd = get_global_time() + Cfg("wave1_countdown");
	}
	else
	{
		CreateWalls();
		JumpToStart();
		// One right head sinks with each Hydra (Owsap).
		Purge(m_adwHeadRight[bWave - WAVE2]);
		if (!Find(m_dwHydra))
		{
			const DWORD v = bWave == WAVE2 ? VNUM_HYDRA_1 : bWave == WAVE3 ? VNUM_HYDRA_2 : VNUM_HYDRA_3;
			LPCHARACTER pHydra = SpawnAt(v, HYDRA_X, HYDRA_Y, 1, false, false);
			m_dwHydra = pHydra ? pHydra->GetVID() : 0;
		}
		Notice(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Ship defense: they attack again! Ready your weapons!"));
		snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: wave %d - protect the mast and defeat the Hydra."), (int)bWave);
		Notice(CHAT_TYPE_BIG_NOTICE, buf);
		m_tStateEnd = get_global_time() + Cfg("wave_countdown");
	}
}

void CShipDefense::BeginWave(BYTE bWave)
{
	const time_t now = get_global_time();
	RemoveBackWalls();
	m_bWave = bWave;
	m_bState = STATE_RUNNING;

	if (bWave == WAVE1)
		m_tWaveEnd = now + Cfg("wave1_time");
	else
	{
		m_tWaveEnd = 0;
		LPCHARACTER pHydra = Find(m_dwHydra);
		LPCHARACTER pMast = GetMast();
		if (pHydra && pMast)
		{
			pHydra->StartStateMachine();
			pHydra->BeginFight(pMast);
		}
		m_tNextEgg = now + Cfg("egg_first");
		m_tNextSummon = now + 10;
		m_tNextDebuff = 0;
		for (int i = 0; i < SLOT_COUNT; ++i)
		{
			m_adwSpawn[i] = 0;
			m_abLaser[i] = false;
			m_atSpawnAt[i] = i < SpawnSlotsOfWave(bWave) ? now + 1 : 0;
			m_atLaserAt[i] = 0;
		}
	}

	LPDUNGEON pDungeon = GetDungeon();
	if (pDungeon)
	{
		char szRegen[64];
		snprintf(szRegen, sizeof(szRegen), "data/dungeon/defense_wave/wave%d.txt", (int)bWave);
		pDungeon->SpawnRegen(szRegen, false);
		pDungeon->SpawnRegen("data/dungeon/defense_wave/boss.txt", true);
	}
	sys_log(0, "SHIP_DEFENSE: instance %ld wave %d", m_lMapIndex, (int)bWave);
}

void CShipDefense::SpawnEgg()
{
	if (Find(m_dwEgg))
		return;
	LPCHARACTER pMast = GetMast();
	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMast || !pMap)
		return;
	const int px = (pMast->GetX() - pMap->m_setting.iBaseX) / 100;
	const int py = (pMast->GetY() - pMap->m_setting.iBaseY) / 100;
	int x = px, y = py;
	for (int tries = 0; tries < 50; ++tries)
	{
		x = px + number(-8, 8);
		y = py + number(-8, 8);
		if (DISTANCE_APPROX(px - x, py - y) >= 5)
			break;
	}
	LPCHARACTER pEgg = SpawnAt(VNUM_EGG, x, y, 0, true, false);
	if (!pEgg)
		return;
	m_dwEgg = pEgg->GetVID();
	m_tEggPurgeAt = get_global_time() + Cfg("egg_life");
	Notice(CHAT_TYPE_NOTICE, LC_TEXT("Ship defense: a Hydra Egg appeared! Destroy it to sink the monsters."));
}

void CShipDefense::Lose(const char* szWhy)
{
	ClearWave();
	Purge(m_dwHydra);
	Notice(CHAT_TYPE_BIG_NOTICE, szWhy);
	m_bState = STATE_LOST;
	m_tStateEnd = get_global_time() + Cfg("lose_exit");
	sys_log(0, "SHIP_DEFENSE: instance %ld lost in wave %d", m_lMapIndex, (int)m_bWave);
}

void CShipDefense::Win()
{
	RemoveBackWalls();
	RemoveFrontWalls();
	if (!Find(m_dwReward))
	{
		LPCHARACTER ch = SpawnAt(VNUM_REWARD, 385, 416, 1, false, false);
		m_dwReward = ch ? ch->GetVID() : 0;
	}
	if (!Find(m_dwPortal))
	{
		LPCHARACTER ch = SpawnAt(VNUM_PORTAL, 385, 450, 1, false, false);
		m_dwPortal = ch ? ch->GetVID() : 0;
	}
	LPDUNGEON pDungeon = GetDungeon();
	if (pDungeon)
		pDungeon->SetFlag("shipdef_won", 1);

	const int iEnd = Cfg("end_time");
	Notice(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Ship defense: land sighted! You protected the ship - go through the portal."));
	char buf[256];
	snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: hurry, you have %d min. to go through the portal."), MAX(1, iEnd / 60));
	Notice(CHAT_TYPE_INFO, buf);
	m_bState = STATE_WON;
	m_tStateEnd = get_global_time() + iEnd;
	sys_log(0, "SHIP_DEFENSE: instance %ld won in %ld s", m_lMapIndex, (long)(get_global_time() - m_tStarted));
}

void CShipDefense::Close(bool bExitAll)
{
	if (m_bState == STATE_CLOSED)
		return;
	m_bState = STATE_CLOSED;
	m_iLastMastHP = -1;
	SendMastHP(true);	// "ShipMastHP 0 0": the bar goes away

	LPDUNGEON pDungeon = GetDungeon();
	if (pDungeon)
	{
		pDungeon->ClearRegen();
		pDungeon->Purge();
		if (bExitAll)
			pDungeon->ExitAll();
	}
	sys_log(0, "SHIP_DEFENSE: instance %ld closed (wave %d)", m_lMapIndex, (int)m_bWave);
}

void CShipDefense::SkipToWave(BYTE bWave)
{
	if (bWave < WAVE1 || bWave > WAVE4 || m_bState == STATE_CLOSED)
		return;
	if (!m_tStarted)
		m_tStarted = get_global_time();
	Purge(m_dwHydra);
	PrepareWave(bWave);
}

bool CShipDefense::Repair(LPCHARACTER pChar, int iPct)
{
	LPCHARACTER pMast = GetMast();
	if (!pMast || m_bState == STATE_CLOSED || m_bState == STATE_LOST)
		return false;
	const int iAdd = (int)((long long)pMast->GetMaxHP() * iPct / 100);
	pMast->PointChange(POINT_HP, MIN(iAdd, pMast->GetMaxHP() - pMast->GetHP()));

	char buf[256];
	snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: the mast was repaired - %d%% HP."), pMast->GetHPPct());
	Notice(CHAT_TYPE_BIG_NOTICE, buf);
	SendMastHP(false);

	const int iStun = Cfg("repair_stun");
	if (pChar && iStun > 0)
		pChar->AddAffect(AFFECT_STUN, POINT_NONE, 0, AFF_STUN, iStun, 0, true);
	return true;
}

void CShipDefense::TickRunning(time_t now)
{
	char buf[256];

	if (m_bWave == WAVE1)
	{
		const long left = (long)(m_tWaveEnd - now);
		if (left > 0 && (left <= 10 || left == 30))
		{
			snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: the next wave begins in %d sec."), (int)left);
			Notice(CHAT_TYPE_INFO, buf);
		}
		if (left <= 0)
			PrepareWave(WAVE2);
		return;
	}

	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMap)
		return;

	// Eggs.
	if (m_tNextEgg && now >= m_tNextEgg)
	{
		SpawnEgg();
		m_tNextEgg = now + Cfg("egg_interval");
	}

	// The Hydra's spawn: one, two, four of them; a dead one comes back after spawn_respawn.
	const int iSlots = SpawnSlotsOfWave(m_bWave);
	const DWORD dwSpawnVnum = m_bWave == WAVE2 ? VNUM_SPAWN_1 : m_bWave == WAVE3 ? VNUM_SPAWN_2 : VNUM_SPAWN_3;
	for (int i = 0; i < iSlots; ++i)
	{
		if (Find(m_adwSpawn[i]))
			continue;
		m_adwSpawn[i] = 0;
		if (!m_atSpawnAt[i])
			m_atSpawnAt[i] = now + Cfg("spawn_respawn");
		if (now < m_atSpawnAt[i])
			continue;
		LPCHARACTER ch = SpawnAt(dwSpawnVnum, aSpawnPos[i][0], aSpawnPos[i][1], 0, true, true);
		m_adwSpawn[i] = ch ? ch->GetVID() : 0;
		m_atSpawnAt[i] = 0;
		m_abLaser[i] = false;
		m_atLaserAt[i] = now + Cfg("laser_interval");
	}

	// Lasers: a spawn charges one every laser_interval; a person stepping on its field takes it.
	// One still charged at the next interval (nobody took it) strikes the mast for laser_mast_pct.
	const int iLaserPct = Cfg("laser_mast_pct");
	for (int i = 0; i < iSlots; ++i)
	{
		LPCHARACTER pSpawn = Find(m_adwSpawn[i]);
		if (!pSpawn || !m_atLaserAt[i] || now < m_atLaserAt[i])
			continue;
		if (m_abLaser[i] && iLaserPct > 0)
		{
			LPCHARACTER pMast = GetMast();
			if (pMast)
			{
				const int iDam = (int)((long long)pMast->GetMaxHP() * iLaserPct / 100);
				if (pMast->GetHP() <= iDam)
					pMast->Dead(pSpawn);
				else
					pMast->PointChange(POINT_HP, -iDam);
				Notice(CHAT_TYPE_INFO, LC_TEXT("Ship defense: the Hydra's spawn struck the mast with a laser!"));
			}
		}
		m_abLaser[i] = true;
		pSpawn->SpecificEffectPacket(LASER_EFFECT);
		m_atLaserAt[i] = now + Cfg("laser_interval");
	}

	// The spawn's kappas.
	if (m_tNextSummon && now >= m_tNextSummon)
	{
		m_tNextSummon = now + Cfg("summon_interval");
		FCollectChars f;
		pMap->for_each(f);
		int iPawns = 0;
		for (size_t i = 0; i < f.others.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(f.others[i]);
			if (ch && !ch->IsDead() && IsPawn(ch->GetRaceNum()))
				++iPawns;
		}
		const int iCap = Cfg("summon_cap");
		const DWORD dwPawn = m_bWave == WAVE2 ? VNUM_PAWN_1 : m_bWave == WAVE3 ? VNUM_PAWN_2 : VNUM_PAWN_3;
		const int iEach = m_bWave == WAVE4 ? 4 : 3;
		for (int i = 0; i < iSlots; ++i)
		{
			if (!Find(m_adwSpawn[i]))
				continue;
			for (int j = 0; j < iEach && (iCap <= 0 || iPawns < iCap); ++j, ++iPawns)
				SpawnAt(dwPawn, aSummonPos[i][0] + number(-1, 1), aSummonPos[i][1] + number(-1, 1), 0, true, true);
		}
	}

	// Wave 4: from half the Hydra's HP the monsters lose their buffs every few seconds.
	if (m_bWave == WAVE4)
	{
		LPCHARACTER pHydra = Find(m_dwHydra);
		if (pHydra && pHydra->GetHPPct() <= Cfg("debuff_hp_pct") && now >= m_tNextDebuff)
		{
			m_tNextDebuff = now + Cfg("debuff_interval");
			FCollectChars f;
			pMap->for_each(f);
			for (size_t i = 0; i < f.others.size(); ++i)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(f.others[i]);
				if (ch && !ch->IsDead() && (ch->IsMonster() || ch->IsStone()))
					ch->RemoveGoodAffect();
			}
		}
	}
}

void CShipDefense::Tick()
{
	const time_t now = get_global_time();
	if (m_bState == STATE_CLOSED)
		return;
	if (!GetDungeon())
	{
		m_bState = STATE_CLOSED;
		return;
	}

	if (m_tIntroPurgeAt && now >= m_tIntroPurgeAt)
	{
		m_tIntroPurgeAt = 0;
		Purge(m_dwIntro);
	}
	if (m_tEggPurgeAt && now >= m_tEggPurgeAt)
	{
		m_tEggPurgeAt = 0;
		Purge(m_dwEgg);
	}

	const bool bFighting = m_bState == STATE_COUNTDOWN || m_bState == STATE_RUNNING || m_bState == STATE_BETWEEN;

	// The deaths OnDead noted (handled here, not inside CHARACTER::Dead).
	if (m_bMastDied)
	{
		m_bMastDied = false;
		if (bFighting)
		{
			Lose(LC_TEXT("Ship defense: SOS! The mast is smashed and the ship is sinking. You will be taken back to land."));
			SendMastHP(true);
			return;
		}
	}
	if (m_bHydraDied)
	{
		m_bHydraDied = false;
		m_dwHydra = 0;
		if (m_bState == STATE_RUNNING)
		{
			ClearWave();
			if (m_bWave < WAVE4)
			{
				Notice(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Ship defense: you protected the mast. Get ready for the next wave!"));
				m_bNextWave = m_bWave + 1;
				m_bState = STATE_BETWEEN;
				m_tStateEnd = now + Cfg("between_waves");
			}
			else
				Win();
		}
	}
	if (m_bEggDied)
	{
		m_bEggDied = false;
		if (m_bState == STATE_RUNNING)
		{
			ClearMobs(true);
			Notice(CHAT_TYPE_NOTICE, LC_TEXT("Ship defense: the Hydra Egg burst - the monsters sink!"));
		}
	}

	const int iLimit = Cfg("time_limit");
	if (bFighting && m_tStarted && iLimit > 0 && now >= m_tStarted + iLimit)
	{
		Lose(LC_TEXT("Ship defense: the voyage took too long - the ship turns back."));
		return;
	}

	switch (m_bState)
	{
		case STATE_IDLE:
		{
			const int iIdle = Cfg("idle_destroy");
			if (iIdle > 0 && now >= m_tCreated + iIdle)
			{
				Notice(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Ship defense: nobody set sail - the ship stays in port."));
				Close(true);
			}
			break;
		}

		case STATE_COUNTDOWN:
		{
			const long left = (long)(m_tStateEnd - now);
			if (left <= 0)
			{
				BeginWave(m_bNextWave);
				break;
			}
			char buf[256];
			if (m_bNextWave == WAVE1)
			{
				if (left <= 10 || (left % 10 == 0 && left < 60))
				{
					snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: the sea battle starts in %d sec."), (int)left);
					Notice(CHAT_TYPE_INFO, buf);
				}
			}
			else if (left <= 10 || left == 30)
			{
				snprintf(buf, sizeof(buf), LC_TEXT("Ship defense: the next wave begins in %d sec."), (int)left);
				Notice(CHAT_TYPE_INFO, buf);
			}
			break;
		}

		case STATE_RUNNING:
			TickRunning(now);
			break;

		case STATE_BETWEEN:
			if (now >= m_tStateEnd)
				PrepareWave(m_bNextWave);
			break;

		case STATE_WON:
		case STATE_LOST:
			if (now >= m_tStateEnd)
				Close(true);
			break;
	}

	if (m_bState != STATE_CLOSED && IsStarted())
		SendMastHP(false);
}

void CShipDefense::OnDead(LPCHARACTER pChar, LPCHARACTER pKiller)
{
	const DWORD vid = pChar->GetVID();
	if (vid == m_dwMast)
		m_bMastDied = true;
	else if (vid == m_dwHydra)
		m_bHydraDied = true;
	else if (vid == m_dwEgg)
	{
		m_dwEgg = 0;
		m_tEggPurgeAt = 0;
		// Only an egg somebody broke; one a wave's clearing killed (no killer) sinks nothing.
		if (pKiller && m_bState == STATE_RUNNING)
			m_bEggDied = true;
	}
	else
	{
		for (int i = 0; i < SLOT_COUNT; ++i)
		{
			if (vid != m_adwSpawn[i])
				continue;
			m_adwSpawn[i] = 0;
			m_abLaser[i] = false;
			m_atSpawnAt[i] = get_global_time() + Cfg("spawn_respawn");
		}
	}
}

// A person on a laser's field takes the charge (Owsap: a 15 s affect on him, only a picture).
void CShipDefense::OnMove(LPCHARACTER pChar, long x, long y)
{
	if (m_bState != STATE_RUNNING || m_bWave < WAVE2)
		return;
	LPSECTREE_MAP pMap = GetSectreeMap();
	if (!pMap)
		return;
	const long lx = (x - pMap->m_setting.iBaseX) / 100;
	const long ly = (y - pMap->m_setting.iBaseY) / 100;
	for (int i = 0; i < SLOT_COUNT; ++i)
	{
		if (!m_abLaser[i] || lx != aLaserPos[i][0] || ly != aLaserPos[i][1])
			continue;
		m_abLaser[i] = false;
		m_atLaserAt[i] = get_global_time() + Cfg("laser_interval");
		pChar->SpecificEffectPacket(LASER_EFFECT);
		pChar->ChatPacket(CHAT_TYPE_INFO, "%s", LC_TEXT("Ship defense: you caught the laser of the Hydra's spawn."));
	}
}

void CShipDefense::OnEnter(LPCHARACTER pChar)
{
	if (m_bState == STATE_CLOSED)
	{
		if (!pChar->IsGM())
			pChar->ExitToSavedLocation();
		return;
	}
	SendMastHPTo(pChar);
}

bool CShipDefense::IsBlockedDamage(LPCHARACTER pChar) const
{
	const DWORD vid = pChar->GetVID();
	// The Hydra only while its wave runs: one killed in the countdown would leave the wave without it.
	// MT2009_PLUS_HYDRA_WALL_V1: the walls (3970) are doors now (mob_proto type 4, so the client blocks
	// walking through them) and a door can be struck - they take no damage either.
	return IsHead(pChar->GetRaceNum()) || vid == m_dwIntro || vid == m_dwWheel || pChar->GetRaceNum() == VNUM_WALL ||
		(vid == m_dwMast && m_bState == STATE_IDLE) || (vid == m_dwHydra && m_bState != STATE_RUNNING);
}

bool CShipDefense::IsNoAttack(LPCHARACTER pChar) const
{
	return IsHead(pChar->GetRaceNum()) || pChar->GetVID() == m_dwIntro || pChar->GetRaceNum() == VNUM_REWARD;
}

bool CShipDefense::IsProtected(LPCHARACTER pChar) const
{
	if (m_bState == STATE_CLOSED)
		return false;
	const DWORD v = pChar->GetRaceNum();
	return v == VNUM_MAST || v == VNUM_WHEEL || v == VNUM_WALL || IsHead(v) || v == VNUM_PORTAL;
}

///////////////////////////////////////////////////////////////////////////////////////////
// CShipDefenseManager
///////////////////////////////////////////////////////////////////////////////////////////

CShipDefenseManager& CShipDefenseManager::instance()
{
	// Never destroyed: its ships' events must not be cancelled after the event system is gone.
	static CShipDefenseManager* s_pInstance = new CShipDefenseManager;
	return *s_pInstance;
}

CShipDefense* CShipDefenseManager::Find(long lMapIndex) const
{
	if (!IsShipMap(lMapIndex))
		return NULL;
	std::map<long, CShipDefense*>::const_iterator it = m_map.find(lMapIndex);
	return it == m_map.end() ? NULL : it->second;
}

CShipDefense* CShipDefenseManager::Attach(long lMapIndex)
{
	if (!IsShipMap(lMapIndex))
		return NULL;
	CShipDefense* pShip = Find(lMapIndex);
	if (pShip)
		return pShip;
	LPDUNGEON pDungeon = CDungeonManager::instance().FindByMapIndex(lMapIndex);
	if (!pDungeon)
		return NULL;
	pShip = new CShipDefense(lMapIndex, pDungeon->GetId());
	m_map[lMapIndex] = pShip;
	pShip->Initialize();
	return pShip;
}

void CShipDefenseManager::OnDungeonDestroy(long lMapIndex)
{
	std::map<long, CShipDefense*>::iterator it = m_map.find(lMapIndex);
	if (it == m_map.end())
		return;
	CShipDefense* pShip = it->second;
	m_map.erase(it);
	sys_log(0, "SHIP_DEFENSE: instance %ld gone with its dungeon", lMapIndex);
	delete pShip;
}

LPDUNGEON CShipDefenseManager::CreateInstance()
{
	if (!SECTREE_MANAGER::instance().GetMap(MAP_INDEX))
		return NULL;
	return CDungeonManager::instance().Create(MAP_INDEX);
}

///////////////////////////////////////////////////////////////////////////////////////////
// The engine's hooks
///////////////////////////////////////////////////////////////////////////////////////////

void ShipDefense_OnEnter(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return;
	CShipDefense* pShip = CShipDefenseManager::instance().Attach(ch->GetMapIndex());
	if (pShip)
		pShip->OnEnter(ch);
}

void ShipDefense_OnMove(LPCHARACTER ch, long x, long y)
{
	if (!ch || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return;
	// A party's bots come in without a login: the first step on the ship binds it too.
	CShipDefense* pShip = CShipDefenseManager::instance().Attach(ch->GetMapIndex());
	if (pShip)
		pShip->OnMove(ch, x, y);
}

void ShipDefense_OnDead(LPCHARACTER ch, LPCHARACTER pkKiller)
{
	if (!ch || ch->IsPC() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(ch->GetMapIndex());
	if (pShip)
		pShip->OnDead(ch, pkKiller);
}

void ShipDefense_OnDungeonDestroy(long lMapIndex)
{
	if (CShipDefenseManager::IsShipMap(lMapIndex))
		CShipDefenseManager::instance().OnDungeonDestroy(lMapIndex);
}

// A monster of the instance's respawn lines goes for the mast (Owsap's regen.cpp).
void ShipDefense_OnRegenSpawn(LPCHARACTER ch)
{
	if (!ch || !ch->IsMonster() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(ch->GetMapIndex());
	if (!pShip)
		return;
	ch->StartStateMachine();
	LPCHARACTER pMast = pShip->GetMast();
	if (pMast && ch->CanBeginFight())
		ch->BeginFight(pMast);
}

int ShipDefense_DamageRule(LPCHARACTER victim, LPCHARACTER attacker)
{
	if (!victim || !CShipDefenseManager::IsShipMap(victim->GetMapIndex()))
		return 0;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(victim->GetMapIndex());
	if (!pShip)
		return 0;
	if (pShip->IsBlockedDamage(victim))
		return 1;
	if (victim->GetRaceNum() == VNUM_MAST && attacker && attacker->IsPC())
		return 1;
	if (victim->GetRaceNum() == VNUM_WOOD)
		return 2;
	return 0;
}

// MT2009_PLUS_HYDRA_NO_DROP_V1: the Hydra (3960-3964) drops nothing - it dies off the deck, in the sea, where
// nobody can pick its drop up (the owner, 20 October 2026). The reward is the treasure (3965) it leaves on the deck
// and the Skrzynia Hydry (54705) from it. Asked by CHARACTER::Reward (edits.json "(no drop)": the mob's tables, the
// world's extras, yang), RankPointsOnKill (playerbot_rank_points.h) and the aura rune (playerbot_aura.cpp); the
// experience, the quests' kill and the Battle Pass stay.
bool ShipDefense_NoDrop(LPCHARACTER victim)
{
	if (!victim || victim->IsPC() || !CShipDefenseManager::IsShipMap(victim->GetMapIndex()))
		return false;
	const DWORD v = victim->GetRaceNum();
	return IsHydra(v) || IsHead(v);
}

bool ShipDefense_CannotAttack(LPCHARACTER ch)
{
	if (!ch || ch->IsPC() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return false;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(ch->GetMapIndex());
	return pShip && pShip->IsNoAttack(ch);
}

bool ShipDefense_Attackable(LPCHARACTER attacker, LPCHARACTER victim)
{
	if (!attacker || !victim || attacker->IsPC() || !attacker->IsMonster())
		return false;
	if (victim->GetRaceNum() != VNUM_MAST || !CShipDefenseManager::IsShipMap(victim->GetMapIndex()))
		return false;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(victim->GetMapIndex());
	return pShip && pShip->IsStarted() && !pShip->IsNoAttack(attacker);
}

// The Hydra and its spawn keep to the mast whoever strikes them (Owsap).
bool ShipDefense_IgnoreAggro(LPCHARACTER ch)
{
	if (!ch || ch->IsPC() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return false;
	const DWORD v = ch->GetRaceNum();
	return IsHydra(v) || IsSpawn(v);
}

// The instance's monsters keep moving where no person stands near (Owsap's sectree.cpp):
// the Hydra fights the mast from off the deck.
bool ShipDefense_KeepAI(LPCHARACTER ch)
{
	return ch && !ch->IsPC() && CShipDefenseManager::IsShipMap(ch->GetMapIndex()) &&
		CShipDefenseManager::instance().Find(ch->GetMapIndex()) != NULL;
}

bool ShipDefense_Protected(LPCHARACTER ch)
{
	if (!ch || ch->IsPC() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return false;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(ch->GetMapIndex());
	return pShip && pShip->IsProtected(ch);
}

// Owsap's attack ranges in the instance: the Hydra +2000 plus its mob_proto HitRange 2500 (a column
// our mob_proto has not) - it stands on blocked cells off the deck, 2700 from the mast, and the
// people's blows reach it by its range too (battle_melee_attack) - and the rest +300 (the mast is wide).
int ShipDefense_AttackRangeBonus(const CHARACTER* ch)
{
	if (!ch)
		return 0;
	const long lMapIndex = const_cast<CHARACTER*>(ch)->GetMapIndex();
	if (!CShipDefenseManager::IsShipMap(lMapIndex))
		return 0;
	return IsHydra(const_cast<CHARACTER*>(ch)->GetRaceNum()) ? 4500 : 300;
}

// A monster of a running ship with nobody to fight goes back to the mast (Ameria's FindVictimHydra).
LPCHARACTER ShipDefense_FallbackVictim(LPCHARACTER ch)
{
	if (!ch || !ch->IsMonster() || !CShipDefenseManager::IsShipMap(ch->GetMapIndex()))
		return NULL;
	CShipDefense* pShip = CShipDefenseManager::instance().Find(ch->GetMapIndex());
	if (!pShip || pShip->GetState() != STATE_RUNNING || pShip->IsNoAttack(ch))
		return NULL;
	return pShip->GetMast();
}

///////////////////////////////////////////////////////////////////////////////////////////
// GM: /dw create | start | info | wave <1-4> | end
///////////////////////////////////////////////////////////////////////////////////////////

ACMD(do_ship_defense)
{
	char arg1[256], arg2[256];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));

	if (!*arg1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "/dw create | start | info | wave <1-4> | end   (Obrona Statku, map %ld; ships here: %u)",
				MAP_INDEX, (unsigned int)CShipDefenseManager::instance().Count());
		return;
	}

	if (!strcmp(arg1, "create"))
	{
		LPDUNGEON pDungeon = CShipDefenseManager::instance().CreateInstance();
		if (!pDungeon)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: map %ld is not hosted by this core (m2-render-config).", MAP_INDEX);
			return;
		}
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(pDungeon->GetMapIndex());
		if (!pMap)
			return;
		ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: instance %ld made, warping.", pDungeon->GetMapIndex());
		ch->WarpSet(pMap->m_setting.iBaseX + START_X * 100, pMap->m_setting.iBaseY + START_Y * 100, pDungeon->GetMapIndex());
		return;
	}

	CShipDefense* pShip = CShipDefenseManager::instance().Attach(ch->GetMapIndex());
	if (!pShip)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: you are not on a ship (use /dw create).");
		return;
	}

	if (!strcmp(arg1, "start"))
		ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: start %s.", pShip->Start() ? "ok" : "refused (already started?)");
	else if (!strcmp(arg1, "info"))
		ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: instance %ld state %d wave %d mast %d%%",
				pShip->GetMapIndex(), (int)pShip->GetState(), (int)pShip->GetWave(), pShip->GetMastHPPct());
	else if (!strcmp(arg1, "wave"))
	{
		int w = 0;
		str_to_number(w, arg2);
		pShip->SkipToWave((BYTE)w);
		ch->ChatPacket(CHAT_TYPE_INFO, "Ship defense: wave %d prepared.", w);
	}
	else if (!strcmp(arg1, "end"))
		pShip->Close(true);
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "/dw create | start | info | wave <1-4> | end");
}

// MT2009_PLUS_SHIP_DEFENSE_V1 (hydra chest): Skrzynia Hydry (54705) gives one item of its group
// (special_item_group.shipdefense.txt) an opening, chest_uses times (3, the owner's decision of
// 13 October 2026). Called by the giftbox's use after a successful opening (char_item.cpp, edits.json):
// true keeps the chest with one more opening counted in socket 0 (the client's tooltip shows the
// rest), false lets the engine take it (the last opening, or any other box).
// MT2009_PLUS_RZNM_BOSS_DROP_V1: Skrzynia Razadora (50270) and Skrzynia Nemere (50271) open 3 times the
// same way (the owner, 15 October; pl-wiki 17.3: "kazda z nich mozna otworzyc 3 razy"). All three are
// ANTI_STACK (apply.sh), so socket 0 is one chest's count, never a stack's.
// MT2009_PLUS_BERAN_CHEST_V1: Skrzynia Berana-Setaou (54700) 2 times (the owner, 15 October; pl-wiki 17.3:
// "mozna otworzyc 2 razy"), ANTI_STACK the same way.
bool ShipDefense_ChestKeep(LPITEM item)
{
	if (!item)
		return false;
	int iUses;
	if (item->GetVnum() == VNUM_HYDRA_CHEST)
		iUses = MAX(1, Cfg("chest_uses"));
	else if (item->GetVnum() == 50270 || item->GetVnum() == 50271)
		iUses = 3;
	else if (item->GetVnum() == 54700)	// MT2009_PLUS_BERAN_CHEST_V1: Skrzynia Berana-Setaou opens 2 times (pl-wiki 17.3)
		iUses = 2;
	else
		return false;
	const long lUsed = MAX(0L, item->GetSocket(0)) + 1;
	if (lUsed >= iUses)
		return false;
	item->SetSocket(0, lUsed);
	return true;
}

