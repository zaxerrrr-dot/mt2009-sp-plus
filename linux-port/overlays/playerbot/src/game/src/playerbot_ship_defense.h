// MT2009_PLUS_SHIP_DEFENSE_V1: Obrona Statku (Hydra, "defense wave") - port of Owsap's v6.2.6
// defense_wave.cpp (CDefenseWave) onto our r40250 dungeons, server-patches/shipdefense/README.md.
//
// Our CDungeon has no virtual methods and CDungeonManager::Create takes no type, so the ship is
// not a CDungeon subclass (Owsap): it is a separate object kept per private map index, bound to
// the dungeon instance d.new_jump_pids (or the GM command) made on map 367, attached when the
// first person enters the instance and dropped when the dungeon is destroyed. Everything timed
// runs from one 1-second event per instance (Owsap had ~15 events, two of them sharing one slot).
// The engine hooks (edits.json) call the free functions at the end of this header; each returns
// at once outside 3670000-3679999.
//
// Gameplay numbers the owner has not decided yet are event flags "shipdef_<name>" (0/unset =
// the default below, a negative value = 0) - the quest reads them through dw.cfg("<name>").
#ifndef MT2009_PLUS_SHIP_DEFENSE_H
#define MT2009_PLUS_SHIP_DEFENSE_H

#include <map>
#include <string>
#include <vector>

namespace ship_defense
{
	// The ship's map (metin2_map_defensewave; Owsap's 358 is our Zodiac temple). Its private
	// copies are 3670000-3679999. The port (Owsap 359) would be 368 - not ported yet.
	const long MAP_INDEX = 367;

	// Monsters and NPCs (the official vnums, as Owsap and the client's npclist.txt).
	const DWORD VNUM_PORTAL = 3949;
	const DWORD VNUM_PAWN_1 = 3950, VNUM_PAWN_2 = 3951, VNUM_PAWN_3 = 3952;
	const DWORD VNUM_SIREN_QUEEN = 3956;
	const DWORD VNUM_SPAWN_1 = 3957, VNUM_SPAWN_2 = 3958, VNUM_SPAWN_3 = 3959;	// Potomstwo Hydry
	const DWORD VNUM_HYDRA_1 = 3960, VNUM_HYDRA_2 = 3961, VNUM_HYDRA_3 = 3962;
	const DWORD VNUM_HEAD_LEFT = 3963, VNUM_HEAD_RIGHT = 3964;
	const DWORD VNUM_REWARD = 3965;	// Skarb Hydry
	const DWORD VNUM_WALL = 3970;
	const DWORD VNUM_EGG = 20432;
	const DWORD VNUM_MAST = 20434;
	const DWORD VNUM_WHEEL = 20436;
	const DWORD VNUM_WOOD = 20437;	// Deska (each hit takes 1 HP - Owsap's COUNT flag, which our mob_proto has not)
	const DWORD VNUM_HYDRA_CHEST = 54705;	// Skrzynia Hydry: chest_uses openings (ShipDefense_ChestKeep)
	const DWORD VNUM_MAGIC_STONE = 25042;	// MT2009_PLUS_MAGIC_STONE_REFINE_V1: Magiczny Kamien (our vnum; official 25041)

	enum EWave { WAVE0, WAVE1, WAVE2, WAVE3, WAVE4 };
	enum EState
	{
		STATE_IDLE,		// made, waiting for the wheel ("Rozpocznij obrone")
		STATE_COUNTDOWN,	// a wave is prepared, its countdown runs
		STATE_RUNNING,		// a wave runs
		STATE_BETWEEN,		// a Hydra died, the next wave is prepared in a few seconds
		STATE_WON,		// the last Hydra died: treasure and portal
		STATE_LOST,		// the mast broke (or the time ran out): everyone out in a few seconds
		STATE_CLOSED		// over; the dungeon instance dies when its last person leaves
	};
	enum { SLOT_COUNT = 4 };

	// Config: event flag "shipdef_<name>", 0 = the default here, < 0 = 0.
	int Cfg(const char* name);
}

class CShipDefense
{
public:
	CShipDefense(long lMapIndex, DWORD dwDungeonID);
	~CShipDefense();

	long GetMapIndex() const { return m_lMapIndex; }
	DWORD GetDungeonID() const { return m_dwDungeonID; }
	BYTE GetWave() const { return m_bWave; }
	BYTE GetState() const { return m_bState; }
	bool IsStarted() const { return m_bState != ship_defense::STATE_IDLE; }

	void Initialize();		// mast, wheel, walls, the idle timer, the 1 s tick
	bool Start();			// the wheel's "Rozpocznij": wave 1's countdown
	void Close(bool bExitAll);	// end: clear, (warp everyone out), stop ticking
	void Tick();			// every second
	bool Repair(LPCHARACTER pChar, int iPct);	// a plank on the mast
	void SkipToWave(BYTE bWave);	// GM test

	void OnDead(LPCHARACTER pChar, LPCHARACTER pKiller);
	void OnMove(LPCHARACTER pChar, long x, long y);
	void OnEnter(LPCHARACTER pChar);

	bool IsBlockedDamage(LPCHARACTER pChar) const;	// heads and the intro Hydra take no damage
	bool IsNoAttack(LPCHARACTER pChar) const;	// heads and the intro Hydra do not attack
	bool IsProtected(LPCHARACTER pChar) const;	// d.kill_all / d.purge leave it alone
	LPCHARACTER GetMast() const;
	int GetMastHPPct() const;

	LPEVENT m_pTickEvent;

private:
	LPDUNGEON GetDungeon() const;
	LPSECTREE_MAP GetSectreeMap() const;
	LPCHARACTER Find(DWORD dwVID) const;
	LPCHARACTER SpawnAt(DWORD dwVnum, int iX, int iY, int iDir, bool bSpawnMotion, bool bFightMast);
	void Purge(DWORD& dwVID);
	void Notice(BYTE bChatType, const char* szText);
	void SendMastHP(bool bForce);
	void SendMastHPTo(LPCHARACTER pChar);

	void PrepareWave(BYTE bWave);
	void BeginWave(BYTE bWave);
	void ClearWave();
	void ClearMobs(bool bKeepSirenQueen);
	void JumpToStart();
	void CreateWalls();
	void RemoveBackWalls();
	void RemoveFrontWalls();
	void Lose(const char* szWhy);
	void Win();
	void SpawnEgg();
	void TickRunning(time_t now);

	long m_lMapIndex;
	DWORD m_dwDungeonID;
	BYTE m_bWave;
	BYTE m_bState;
	BYTE m_bNextWave;

	DWORD m_dwMast, m_dwWheel, m_dwHydra, m_dwIntro, m_dwEgg, m_dwReward, m_dwPortal;
	DWORD m_adwHeadRight[3];
	DWORD m_adwWall[4];	// back left, back right, front left, front right
	DWORD m_adwSpawn[ship_defense::SLOT_COUNT];
	bool m_abLaser[ship_defense::SLOT_COUNT];
	time_t m_atSpawnAt[ship_defense::SLOT_COUNT];
	time_t m_atLaserAt[ship_defense::SLOT_COUNT];

	time_t m_tCreated, m_tStarted, m_tStateEnd, m_tWaveEnd;
	time_t m_tIntroPurgeAt, m_tNextEgg, m_tEggPurgeAt, m_tNextSummon, m_tNextDebuff;
	bool m_bMastDied, m_bHydraDied, m_bEggDied;
	int m_iLastMastHP;
	int m_iLastNoticePct;
};

class CShipDefenseManager
{
public:
	static CShipDefenseManager& instance();

	static bool IsShipMap(long lMapIndex)
	{
		return lMapIndex >= ship_defense::MAP_INDEX * 10000 && lMapIndex < (ship_defense::MAP_INDEX + 1) * 10000;
	}

	CShipDefense* Find(long lMapIndex) const;
	CShipDefense* Attach(long lMapIndex);		// find, or bind a new one to the dungeon of that instance
	void OnDungeonDestroy(long lMapIndex);
	size_t Count() const { return m_map.size(); }
	LPDUNGEON CreateInstance();			// a new dungeon instance of 367 on this core (GM test)

private:
	std::map<long, CShipDefense*> m_map;
};

// The engine's hooks (server-patches/shipdefense/edits.json declare them where they call).
void ShipDefense_OnEnter(LPCHARACTER ch);
void ShipDefense_OnMove(LPCHARACTER ch, long x, long y);
void ShipDefense_OnDead(LPCHARACTER ch, LPCHARACTER pkKiller);
void ShipDefense_OnDungeonDestroy(long lMapIndex);
void ShipDefense_OnRegenSpawn(LPCHARACTER ch);
int ShipDefense_DamageRule(LPCHARACTER victim, LPCHARACTER attacker);	// 0 normal, 1 blocked, 2 one point
bool ShipDefense_CannotAttack(LPCHARACTER ch);
bool ShipDefense_Attackable(LPCHARACTER attacker, LPCHARACTER victim);
bool ShipDefense_IgnoreAggro(LPCHARACTER ch);
bool ShipDefense_KeepAI(LPCHARACTER ch);
bool ShipDefense_Protected(LPCHARACTER ch);
int ShipDefense_AttackRangeBonus(const CHARACTER* ch);
LPCHARACTER ShipDefense_FallbackVictim(LPCHARACTER ch);
bool ShipDefense_ChestKeep(LPITEM item);		// MT2009_PLUS_SHIP_DEFENSE_V1 (hydra chest)
bool MagicStoneRefineFree(LPITEM scroll);	// MT2009_PLUS_MAGIC_STONE_REFINE_V1

#endif
