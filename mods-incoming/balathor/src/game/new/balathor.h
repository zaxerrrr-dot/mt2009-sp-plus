#pragma once

#ifdef __BALATHOR__
#include "json.hpp"
#include "motion.h"

enum EBalathor
{
	BALATHOR_STAGE_NONE = 0,
	BALATHOR_STAGE_WAITING,
	BALATHOR_STAGE_RUN,
	BALATHOR_STAGE_REWARD,
	BALATHOR_STAGE_CLOSE,

	BALATHOR_FINISH_FAIL_TIME = 0,
	BALATHOR_FINISH_FAIL_BY_GAMEMASTER,
	BALATHOR_FINISH_FAIL,
	BALATHOR_FINISH_SUCCESS,

	BALATHOR_EFF_AREA = 0,
	BALATHOR_EFF_GROUND_DROP,
	BALATHOR_EFF_GROUND_ICE,
	BALATHOR_EFF_EGG_ARROW,
	BALATHOR_EFF_EGG_FLOOD,
	BALATHOR_EFF_EGG_GUARD,
	BALATHOR_EFF_EGG_MOOJUK,
	BALATHOR_EFF_RED_ARROW,
	BALATHOR_EFF_POSITION,
	BALATHOR_EFF_MAX,

	BALATHOR_CINEMA_BOSS_DEAD = 0,
	BALATHOR_CINEMA_BOSS_SPAWN,
	BALATHOR_CINEMA_HIDDEN_BOSS_DEAD,
	BALATHOR_CINEMA_HIDDEN_BOSS_RUNAWAY,
	BALATHOR_CINEMA_HIDDEN_BOSS_SPAWN,
	BALATHOR_CINEMA_HIDDEN_HWATCHA_FIRE,
	BALATHOR_CINEMA_HIDDEN_MAX,

	BALATHOR_EGG_PHASE_NONE = 0,
	BALATHOR_EGG_PHASE_GUARD,
	BALATHOR_EGG_PHASE_FLOOD,

	BALATHOR_TAKE_OFF_FAIL = 0,
	BALATHOR_TAKE_OFF_SUCCESS,

	//BOSS 1 SKILL
	BALATHOR_1_RIGHT_CIRCLE = 0,
	BALATHOR_1_LEFT_CIRCLE,
	BALATHOR_1_BREATH,
	BALATHOR_1_AREA,
	BALATHOR_1_LAND,

	//BOSS 1 ETC
	BALATHOR_1_SPAWN_ROAR = EPublicMotion::MOTION_ETC_1,
	BALATHOR_1_TAKE_DAMAGE = EPublicMotion::MOTION_ETC_2,
	BALATHOR_1_TAKE_OFF = EPublicMotion::MOTION_ETC_3,

	//BOSS 2 SKILL
	BALATHOR_2_BOTH_HAND_CIRCLE = 0,
	BALATHOR_2_RIGHT_CIRCLE,
	BALATHOR_2_FLY_BREATH,
	BALATHOR_2_BREATH,
	BALATHOR_2_AREA,

	// BOSS 2 ETC
	BALATHOR_2_TAKE_OFF = EPublicMotion::MOTION_ETC_1,
	BALATHOR_2_LAND = EPublicMotion::MOTION_ETC_2,

	HWATCHA_FIRE_SKILL_INDEX = 0,

	BALATHOR_RAGE_MAX = 100,
	BALATHOR_REGEN_GROUP_SIZE = 4,

	INFINITE_EFFECT_TIME = (60 * 60 * 2) * 1000,
	BALATHOR_PROCESS_SLEEP_TIME = 500,

	BALATHOR_MAX_REWARD_COUNT = 4,
};

struct SBalathorReward
{
	DWORD	dwVnum;
	DWORD	dwCount;
};

struct SBalathorPosition
{
	long lX;
	long lY;
	long lGX;
	long lGY;
	BYTE bDirection;
};

struct SBalathorConfig
{
	DWORD	dwMapIndex;
	DWORD	dwBossVnum1;
	DWORD	dwBossVnum2;
	DWORD	dwNPCVnum;
	DWORD	dwChestVnum;
	DWORD	dwHwachaVnum;
	DWORD	dwDoorVnum;
	DWORD	dwFrozenEggVnum1;
	DWORD	dwFrozenEggVnum2;
	DWORD	dwFlamingEggVnum;
	DWORD	dwIceCrystalVnum;

	SBalathorPosition	base_pos;
	SBalathorPosition	npc_pos;
	SBalathorPosition	chest_pos;
	SBalathorPosition	door_pos;
	SBalathorPosition	hwacha_pos;

	SBalathorPosition	boss_1_pos;
	SBalathorPosition	boss_2_pos;

	SBalathorPosition	boss_1_door1_pos;
	SBalathorPosition	boss_1_door2_pos;
	SBalathorPosition	boss_1_door3_pos;

	SBalathorPosition	boss_1_egg_pos1;
	SBalathorPosition	boss_1_egg_pos2;

	SBalathorPosition	flaming_egg_pos1;
	SBalathorPosition	flaming_egg_pos2;

	SBalathorPosition	ice_crystal_pos;
	SBalathorPosition	regen_pos;

	DWORD	dwRegenMob[BALATHOR_REGEN_GROUP_SIZE];
	DWORD	dwStoneRegenMob[BALATHOR_REGEN_GROUP_SIZE];

	DWORD	dwWaitingTime;
	DWORD	dwBoss1Time;
	DWORD	dwBoss2Time;
	DWORD	dwSendOutTime;

	BYTE	bRequestGroupKillCount;

	DWORD	dwFireArrowVnum;
	BYTE	bFireArrowDropLuck;

	BYTE	bHwatchaRequiredArrowCount;

	BYTE	bFireEggFailMaxCount;
	DWORD	dwBoss1FakeSkillTime;

	BYTE	bHwatchaDamagePercent;

	DWORD	dwFlamingEggSpawnTime;
	DWORD	dwIceCrystalSpawnPerTime;

	DWORD	dwBoss1RequiredTime;
	DWORD	dwFrozenEggGuardTime;
	DWORD	dwFrozenEggFloodTime;

	DWORD	dwGroundIceDamageCount;
	DWORD	dwGroundIceDamagePerTime;

	DWORD	dwBossSkillPerTime;
	DWORD	dwRaidIncreaseBySec;

	SBalathorPosition	dragon_egg_1_pos;
	SBalathorPosition	dragon_egg_2_pos;
	SBalathorPosition	dragon_egg_3_pos;
	SBalathorPosition	dragon_egg_4_pos;

	DWORD	dwRegenSpawnPerTime;
	DWORD	dwRegenMaxCount;

	DWORD	dwReviveHwatchaRequestSP;

	DWORD	dwEnterMapIndex;
	SBalathorPosition	enter_base_pos;

	BYTE	bRegisterMinLevel;
	BYTE	bRegisterGuildMinLevel;
	BYTE	bRegisterMinMemberCount;
	BYTE	bRegisterMaxMemberCount;
	DWORD	dwRegisterLadderPoint;
	DWORD	dwRegisterTicketVnum;
	DWORD	dwRegisterWaitTime;

	SBalathorReward	fail_rewards[BALATHOR_MAX_REWARD_COUNT];
	SBalathorReward	success_rewards[BALATHOR_MAX_REWARD_COUNT];
};

typedef struct SBalathorEffect
{
	DWORD dwID;
	DWORD dwVID;
	BYTE bEffIndex;
	long lX;
	long lY;
	long lZ;
	long lGX;
	long lGY;
	float fRotation;
	DWORD dwDuration;
	bool bIsMain;
	bool bNeedRemove;
	bool bDamage;
	BYTE bStage;
}TBalathorEffect;

class CBalathor
{
public:
	CBalathor(DWORD dwMapIndex, DWORD dwID);
	DWORD GetMapIndex() { return m_dwMapIndex; }

	void Login(LPCHARACTER ch);
	void Logout(LPCHARACTER ch);

	void Teleport(LPCHARACTER ch);

	void Finish(BYTE bFinishType);
	void Close(bool bInstantClose);
	bool IsDeleted(DWORD dwCurTime);
	void ExitAll();
	void ClearRegen();
	void KillRegen();

	void RunCinema(BYTE bCameraIndex);
	void QuestSay(const std::string& str);
	void ChatPacket(BYTE bChatType, const char* szFormat, ...);

	void SetFlag(std::string szFlag, DWORD dwValue);
	DWORD GetFlag(std::string szFlag);

	void StoneSpawn(LPCHARACTER stone, int iPercent);
	LPCHARACTER SpawnMob(DWORD dwVnum, long local_x, long local_y, BYTE bDirection, bool bSpawnMotion, bool bShow);
	LPCHARACTER SpawnMobLocal(DWORD dwVnum, long local_x, long local_y, BYTE bDirection, bool bSpawnMotion, bool bShow);
	void SpawnGroup(LPCHARACTER stone);

	bool LocalToGlobal(long localX, long localY, long& lX, long& lY);
	bool GlobalToLocal(long globalX, long globalY, long& lX, long& lY);

	void LoadEffects(LPCHARACTER ch);
	bool IsEffIndexExist(BYTE bEffIndex);
	DWORD AddEffect(DWORD dwVID, BYTE bEffIndex, long lX, long lY, long lZ, float fRotation, DWORD dwDuration, bool bIsMain);
	void RemoveEffectByVID(DWORD dwVID);
	void RemoveEffectByID(DWORD dwID);

	void UpdateUI();

	bool UseItem(LPCHARACTER ch, LPITEM item);

	LPCHARACTER SpawnCharacterByFlag(const std::string& str);
	DWORD GetCharacterVIDByFlag(const std::string& str);
	void RemoveCharacterByFlag(const std::string& str);
	LPCHARACTER GetCharacterByFlag(const std::string& str);
	void SetCharacterByFlag(const std::string& str, DWORD dwVID);

	bool IsHwatchaDead();
	bool CanUseHwatcha();
	bool ReviveHwatcha();
	void UseHwatcha();
	void SetHwatchaEffect(bool bStatus);

	void StepProgress(DWORD dwCurTime);
	
	BYTE GetStage() { return m_bStage; }
	void SetStage(BYTE bStage);

	void Process(DWORD dwCurTime);

	void Kill(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, bool bFromStone = false);
	
	void Damage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim);

	void ProcessEffect(DWORD dwCurTime);

	void Motion(LPCHARACTER mob, BYTE bSkill, WORD wMotion);

	void TakeOff(BYTE bTakeOffType, bool is_dead);

	void UnPoly(LPCHARACTER ch);
	void GroundIceDamage(const TBalathorEffect& eff_info);
	void GroundIceSpawn();

	void AreaSkillMake();
	void AreaSkillDamage(LPCHARACTER dragon, const TBalathorEffect& eff_info);

	void GroundDropMake(LPCHARACTER dragon);
	void GroundDropDamage(const TBalathorEffect& eff_info);

	void CircleAttackMake(DWORD dwCurTime);
	void CircleAttackDamage();

	void SetAttackSleepTime(DWORD dwSleepTime);

	void AddRaid(DWORD dwValue);
	void ProcessRaid(DWORD dwCurTime);
	void AttackProcess(DWORD dwCurTime);

	void GetVictims(std::vector<LPCHARACTER>& vecVictims, bool flaming_egg, bool hwatcha);

	BYTE ClaimReward(LPCHARACTER ch);
protected:
	BYTE m_bStage;
	BYTE m_bStepIndex;
	DWORD m_dwStageTime;
	DWORD m_dwGuildID;
	DWORD m_dwMapIndex;
	std::vector<DWORD>	m_vecPlayers;

	DWORD m_dwEffID;
	std::vector<TBalathorEffect> m_vecEffects;

	std::vector<DWORD> m_dwRegenMobs;
	std::map<std::string, DWORD> m_mapFlags;
	std::vector<DWORD> m_vecClaimedRewardsPIDs;

	DWORD m_dwProcessSleepTime;
};

class CBalathorManager : public singleton<CBalathorManager>
{
public:
	CBalathorManager();
	bool LoadPosition(const nlohmann::json& whInfo, const char* key, SBalathorPosition* pos, size_t size, LPSECTREE_MAP pkSectreeMap);
	bool LoadDWORDArray(const nlohmann::json& data, const char* key, DWORD* out, size_t size);
	bool LoadRewards(const nlohmann::json& data, const char* key, SBalathorReward* rewards, size_t maxCount);
	bool Load(bool bIsP2P);
	void Destroy();
	void Process();

	bool IsHwatcha(DWORD dwVnum);
	bool IsDoor(DWORD dwVnum);
	bool IsNoMoveMonster(DWORD dwVnum);
	bool IsBalathorStone(DWORD dwVnum);
	bool IsIceCrystal(DWORD dwVnum);

	CBalathor* FindByMapIndex(DWORD dwMapIndex);
	CBalathor* FindByGID(DWORD dwGID);

	void Login(LPCHARACTER ch);
	void Logout(LPCHARACTER ch);
	void Kill(LPCHARACTER pkAttacker, LPCHARACTER pkVictim);
	void Damage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim);

	BYTE CanCreate(LPCHARACTER ch);
	BYTE Create(LPCHARACTER ch);
	BYTE Close(LPCHARACTER ch);

	bool IsGuildDungeonExist(DWORD dwID);
	void Teleport(LPCHARACTER ch);
	void WarpEnter(LPCHARACTER ch);

	const SBalathorConfig& GetConfig() { return m_data; }
protected:
	SBalathorConfig	m_data;
	std::map<DWORD, CBalathor*>	m_mapBalathors;
};
#endif
