#include "stdafx.h"

#ifdef __BALATHOR__
#include "balathor.h"
#include "char.h"
#include "guild.h"
#include "utils.h"
#include "config.h"
#include "sectree_manager.h"
#include "char_manager.h"
#include "locale_service.h"
#include "packet.h"
#include "questmanager.h"
#include "desc.h"
#include <fstream>

CBalathorManager::CBalathorManager()
{
	Destroy();
}

void CBalathorManager::Destroy()
{
	for (auto& [guild_id, dungeon] : m_mapBalathors)
	{
		dungeon->Close(true);
		M2_DELETE(dungeon);
	}
	m_mapBalathors.clear();
}

void CBalathorManager::Process()
{
	DWORD dwCurTime = get_dword_time();
	
	auto it_balathor = m_mapBalathors.begin();
	while (it_balathor != m_mapBalathors.end())
	{
		CBalathor* pBalathor = it_balathor->second;
		if (pBalathor->IsDeleted(dwCurTime))
		{
			pBalathor->Close(true);
			M2_DELETE(pBalathor);
			it_balathor = m_mapBalathors.erase(it_balathor);
			continue;
		}
		pBalathor->Process(dwCurTime);
		++it_balathor;
	}
}

CBalathor* CBalathorManager::FindByMapIndex(DWORD dwMapIndex)
{
	for (auto& [guild_id, dungeon] : m_mapBalathors)
	{
		if (dungeon->GetMapIndex() == dwMapIndex)
			return dungeon;
	}
	return NULL;
}

void CBalathorManager::WarpEnter(LPCHARACTER ch)
{
	if(m_data.enter_base_pos.lGX != 0 && m_data.enter_base_pos.lGY != 0)
		ch->WarpSet(m_data.enter_base_pos.lGX, m_data.enter_base_pos.lGY);
}
void CBalathorManager::Teleport(LPCHARACTER ch)
{
	CGuild* pGuild = ch->GetGuild();
	if (!pGuild)
		return;
	CBalathor* pBalathor = FindByGID(pGuild->GetID());
	if (pBalathor)
		pBalathor->Teleport(ch);
}
bool CBalathorManager::IsGuildDungeonExist(DWORD dwID)
{
	return FindByGID(dwID) != NULL;
}
CBalathor* CBalathorManager::FindByGID(DWORD dwGID)
{
	const auto it = m_mapBalathors.find(dwGID);
	return (it != m_mapBalathors.end()) ? it->second : NULL;
}

void CBalathorManager::Login(LPCHARACTER ch)
{
	CAffect* pAffect = ch->FindAffect(AFFECT_POLYMORPH);
	if (pAffect && pAffect->lApplyValue == m_data.dwIceCrystalVnum)
		ch->RemoveAffect(pAffect);

	DWORD dwCountItem = ch->CountSpecifyItem(m_data.dwFireArrowVnum);
	if (dwCountItem != 0)
		ch->RemoveSpecifyItem(m_data.dwFireArrowVnum, dwCountItem);

	if (!ch->IsGM() && ch->GetMapIndex() == m_data.dwMapIndex)
	{
		ch->GoHome();
		return;
	}

	CBalathor* pDungeon = FindByMapIndex(ch->GetMapIndex());
	if (pDungeon)
		pDungeon->Login(ch);
}

void CBalathorManager::Logout(LPCHARACTER ch)
{
	CAffect* pAffect = ch->FindAffect(AFFECT_POLYMORPH);
	if (pAffect && pAffect->lApplyValue == m_data.dwIceCrystalVnum)
		ch->RemoveAffect(pAffect);

	DWORD dwCountItem = ch->CountSpecifyItem(m_data.dwFireArrowVnum);
	if (dwCountItem != 0)
		ch->RemoveSpecifyItem(m_data.dwFireArrowVnum, dwCountItem);

	CBalathor* pDungeon = FindByMapIndex(ch->GetMapIndex());
	if (pDungeon)
		pDungeon->Logout(ch);
}

void CBalathorManager::Damage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim)
{
	if (!pkVictim)
		return;

	CBalathor* pDungeon = FindByMapIndex(pkVictim->GetMapIndex());
	if (pDungeon)
		pDungeon->Damage(pkAttacker, pkVictim);
}

void CBalathorManager::Kill(LPCHARACTER pkAttacker, LPCHARACTER pkVictim)
{
	if (!pkVictim)
		return;
	CBalathor* pDungeon = FindByMapIndex(pkVictim->GetMapIndex());
	if (pDungeon)
		pDungeon->Kill(pkAttacker, pkVictim);
}

BYTE CBalathorManager::CanCreate(LPCHARACTER ch)
{
	CGuild* pGuild = ch->GetGuild();
	if (!pGuild)
		return 0;
	const auto it = m_mapBalathors.find(pGuild->GetID());
	if (it != m_mapBalathors.end())
		return 1;
	else if (!map_allow_find(m_data.dwMapIndex))
		return 2;
	return 99;
}

BYTE CBalathorManager::Create(LPCHARACTER ch)
{
	CGuild* pGuild = ch->GetGuild();
	if (!pGuild)
		return 0;

	DWORD dwID = pGuild->GetID();

	const auto it = m_mapBalathors.find(dwID);
	if (it != m_mapBalathors.end())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You already has a balathor map.");
		return 1;
	}

	if (!map_allow_find(m_data.dwMapIndex))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You can't create in this core.");
		return 2;
	}

	DWORD lMapIndex = SECTREE_MANAGER::instance().CreatePrivateMap(m_data.dwMapIndex);
	if (!lMapIndex)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "map create failed.");
		return 3;
	}

	CBalathor* pDungeon = M2_NEW CBalathor(lMapIndex, dwID);
	m_mapBalathors.emplace_hint(it, dwID, pDungeon);
	return 99;
}

BYTE CBalathorManager::Close(LPCHARACTER ch)
{
	CGuild* pGuild = ch->GetGuild();
	if (!pGuild)
		return 0;
	const auto it = m_mapBalathors.find(pGuild->GetID());
	if (it == m_mapBalathors.end())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You don't have a balathor map for close.");
		return 1;
	}
	it->second->Finish(BALATHOR_FINISH_FAIL_BY_GAMEMASTER);
	return 99;
}

bool CBalathorManager::IsBalathorStone(DWORD dwVnum)
{
	if (dwVnum == m_data.dwFrozenEggVnum1 || dwVnum == m_data.dwFrozenEggVnum2 || dwVnum == m_data.dwFlamingEggVnum || dwVnum == m_data.dwIceCrystalVnum || dwVnum == m_data.dwDoorVnum)
		return true;
	return false;
}

bool CBalathorManager::IsIceCrystal(DWORD dwVnum)
{
	if (dwVnum == m_data.dwIceCrystalVnum)
		return true;
	return false;
}

bool CBalathorManager::IsHwatcha(DWORD dwVnum)
{
	if (dwVnum == m_data.dwHwachaVnum)
		return true;
	return false;
}

bool CBalathorManager::IsDoor(DWORD dwVnum)
{
	if (dwVnum == m_data.dwDoorVnum)
		return true;
	return false;
}
bool CBalathorManager::IsNoMoveMonster(DWORD dwVnum)
{
	if (dwVnum == m_data.dwBossVnum1 || dwVnum == m_data.dwBossVnum2 || dwVnum == m_data.dwDoorVnum)
		return true;
	return false;
}

bool CBalathorManager::LoadPosition(const nlohmann::json& whInfo, const char* key, SBalathorPosition* pos, size_t size, LPSECTREE_MAP pkSectreeMap)
{
	if (!whInfo.contains(key))
	{
		sys_err("Balathor: missing key %s", key);
		return false;
	}

	const auto& arr = whInfo[key];

	if (!arr.is_array() || arr.size() != size)
	{
		sys_err("Balathor: key %s must be array [x, y, dir]", key);
		return false;
	}

	try
	{
		pos->lX = arr.at(0).get<long>();
		pos->lY = arr.at(1).get<long>();
		pos->bDirection = arr.at(2).get<BYTE>();

		if (pkSectreeMap)
		{
			pos->lGX = (pos->lX * 100) + pkSectreeMap->m_setting.iBaseX;
			pos->lGY = (pos->lY * 100) + pkSectreeMap->m_setting.iBaseY;
		}
		else
		{
			pos->lGX = pos->lX;
			pos->lGY = pos->lY;
		}
	}
	catch (const std::exception& e)
	{
		sys_err("Balathor: key %s parse error: %s", key, e.what());
		return false;
	}

	return true;
}

bool CBalathorManager::LoadDWORDArray( const nlohmann::json& data, const char* key, DWORD* out, size_t size)
{
	if (!out)
		return false;

	if (!data.contains(key))
	{
		sys_err("Balathor: missing key %s", key);
		return false;
	}

	const auto& arr = data[key];

	if (!arr.is_array() || arr.size() != size)
	{
		sys_err("Balathor: key %s must be array of size %zu", key, size);
		return false;
	}

	try
	{
		for (size_t i = 0; i < size; ++i)
			out[i] = arr.at(i).get<DWORD>();
	}
	catch (const std::exception& e)
	{
		sys_err("Balathor: key %s parse error: %s", key, e.what());
		return false;
	}

	return true;
}

bool CBalathorManager::LoadRewards(const nlohmann::json& data, const char* key, SBalathorReward* rewards, size_t maxCount)
{
	if (!rewards)
		return false;

	if (!data.contains(key))
	{
		sys_err("Balathor: missing key %s", key);
		return false;
	}

	const auto& arr = data[key];

	if (!arr.is_array())
	{
		sys_err("Balathor: key %s must be array", key);
		return false;
	}

	size_t count = min(arr.size(), maxCount);

	try
	{
		for (size_t i = 0; i < count; ++i)
		{
			const auto& reward = arr.at(i);

			if (!reward.is_array() || reward.size() != 2)
			{
				sys_err("Balathor: invalid reward format in %s index %zu", key, i);
				return false;
			}

			rewards[i].dwVnum = reward.at(0).get<DWORD>();
			rewards[i].dwCount = reward.at(1).get<DWORD>();
		}

	}
	catch (const std::exception& e)
	{
		sys_err("Balathor: key %s parse error: %s", key, e.what());
		return false;
	}

	return true;
}

bool CBalathorManager::Load(bool bIsP2P)
{
	char buf[254];
	snprintf(buf, sizeof(buf), "%s/balathor.json", LocaleService_GetBasePath().c_str());

	std::ifstream file(buf);
	if (!file.is_open())
	{
		sys_err("failed to open file", buf);
		return false;
	}

	memset(&m_data, 0, sizeof(SBalathorConfig));

	try
	{
		nlohmann::json jsonData;
		file >> jsonData;
		file.close();

		if (!jsonData.is_object())
		{
			sys_err("File: %s | Error: root is not a JSON object", buf);
			return false;
		}

		m_data.dwMapIndex = jsonData.value("map_index", 0);
		m_data.dwBossVnum1 = jsonData.value("boss_1_vnum", 0);
		m_data.dwBossVnum2 = jsonData.value("boss_2_vnum", 0);
		m_data.dwHwachaVnum = jsonData.value("hwacha_vnum", 0);
		m_data.dwDoorVnum = jsonData.value("door_vnum", 0);
		m_data.dwNPCVnum = jsonData.value("npc_vnum", 0);
		m_data.dwChestVnum = jsonData.value("chest_vnum", 0);
		m_data.dwFrozenEggVnum1 = jsonData.value("frozen_egg_vnum1", 0);
		m_data.dwFrozenEggVnum2 = jsonData.value("frozen_egg_vnum2", 0);
		m_data.dwFlamingEggVnum = jsonData.value("flaming_egg_vnum", 0);
		m_data.dwIceCrystalVnum = jsonData.value("ice_crystal_vnum", 0);

		m_data.dwBoss1Time = jsonData.value("first_boss_time", 0);
		m_data.dwBoss2Time = jsonData.value("second_boss_time", 0);
		m_data.dwWaitingTime = jsonData.value("waiting_full_time", 0);
		m_data.dwSendOutTime = jsonData.value("sendout_time", 0);

		m_data.bRequestGroupKillCount = jsonData.value("request_kill_group_count", 0);

		m_data.dwFireArrowVnum = jsonData.value("fire_arrow_vnum", 0);
		m_data.bFireArrowDropLuck = jsonData.value("fire_arrow_drop_luck", 0);

		m_data.bHwatchaRequiredArrowCount = jsonData.value("hwatcha_required_arrow", 0);

		m_data.bFireEggFailMaxCount = jsonData.value("fire_egg_fail_max_count", 0);

		m_data.dwBoss1FakeSkillTime = jsonData.value("boss_1_spawn_fake_skill_msec_time", 0);

		m_data.dwFlamingEggSpawnTime = jsonData.value("flaming_egg_spawn_msec_time", 0);
		m_data.dwIceCrystalSpawnPerTime = jsonData.value("ice_crystal_spawn_per_msec", 0);
		m_data.dwBoss1RequiredTime = jsonData.value("boss_1_required_msec_time", 0);

		m_data.dwFrozenEggGuardTime = jsonData.value("frozen_egg_guard_time", 0);
		m_data.dwFrozenEggFloodTime = jsonData.value("frozen_egg_flood_time", 0);

		m_data.dwGroundIceDamageCount = jsonData.value("ground_ice_damage_count", 0);
		m_data.dwGroundIceDamagePerTime = jsonData.value("ground_ice_damage_per_msec_time", 0);

		m_data.dwBossSkillPerTime = jsonData.value("boss_skill_per_time", 0);
		m_data.dwRaidIncreaseBySec = jsonData.value("boss_raid_increase_by_sec", 0);

		m_data.dwRegenSpawnPerTime = jsonData.value("regen_spawn_per_msec_time", 0);
		m_data.dwRegenMaxCount = jsonData.value("max_regen_mob_count", 0);

		m_data.dwReviveHwatchaRequestSP = jsonData.value("revive_hwatcha_request_sp", 0);
		
		m_data.dwEnterMapIndex = jsonData.value("enter_map_index", 0);
		m_data.bRegisterMinLevel = jsonData.value("register_min_level", 0);
		m_data.bRegisterGuildMinLevel = jsonData.value("register_min_guild_level", 0);
		m_data.bRegisterMinMemberCount = jsonData.value("register_min_member_count", 0);
		m_data.bRegisterMaxMemberCount = jsonData.value("register_max_member_count", 0);
		m_data.dwRegisterLadderPoint = jsonData.value("register_ladder_point", 0);
		m_data.dwRegisterTicketVnum = jsonData.value("register_ticket_vnum", 0);
		m_data.dwRegisterWaitTime = jsonData.value("register_wait_time", 0);

		m_data.bHwatchaDamagePercent = jsonData.value("hwatcha_damage_hp_percent", 1);
		if (m_data.bHwatchaDamagePercent < 1)
			m_data.bHwatchaDamagePercent = 1;

		LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(m_data.dwMapIndex);

		if (!LoadPosition(jsonData, "base_pos", &m_data.base_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "npc_pos", &m_data.npc_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "door_pos", &m_data.door_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "hwacha_pos", &m_data.hwacha_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_pos", &m_data.boss_1_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_2_pos", &m_data.boss_2_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "chest_pos", &m_data.chest_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_egg_pos1", &m_data.boss_1_egg_pos1, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_egg_pos2", &m_data.boss_1_egg_pos2, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "flaming_egg_pos1", &m_data.flaming_egg_pos1, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "flaming_egg_pos2", &m_data.flaming_egg_pos2, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "ice_crystal_pos", &m_data.ice_crystal_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_door1_pos", &m_data.boss_1_door1_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_door2_pos", &m_data.boss_1_door2_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "boss_1_door3_pos", &m_data.boss_1_door3_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "regen_pos", &m_data.regen_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "dragon_egg_1_pos", &m_data.dragon_egg_1_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "dragon_egg_2_pos", &m_data.dragon_egg_2_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "dragon_egg_3_pos", &m_data.dragon_egg_3_pos, 3, pkSectreeMap))
			return false;
		if (!LoadPosition(jsonData, "dragon_egg_4_pos", &m_data.dragon_egg_4_pos, 3, pkSectreeMap))
			return false;

		LPSECTREE_MAP pkBaseSectreeMap = SECTREE_MANAGER::instance().GetMap(m_data.dwEnterMapIndex);
		if (!LoadPosition(jsonData, "enter_base_pos", &m_data.enter_base_pos, 3, pkBaseSectreeMap))
			return false;

		if (!LoadDWORDArray(jsonData, "regen_group", m_data.dwRegenMob, BALATHOR_REGEN_GROUP_SIZE))
			return false;

		if (!LoadDWORDArray(jsonData, "stone_regen_group", m_data.dwStoneRegenMob, BALATHOR_REGEN_GROUP_SIZE))
			return false;

		if (!LoadRewards(jsonData, "fail_rewards", m_data.fail_rewards, BALATHOR_MAX_REWARD_COUNT))
			return false;

		if (!LoadRewards(jsonData, "success_rewards", m_data.success_rewards, BALATHOR_MAX_REWARD_COUNT))
			return false;
	}
	catch (const nlohmann::json::parse_error& e)
	{
		sys_err("File: %s | JSON parse error: %s", buf, e.what());
		return false;
	}
	catch (const std::exception& e)
	{
		sys_err("File: %s | Exception: %s", buf, e.what());
		return false;
	}
	return true;
}

ACMD(do_balathor)
{
	std::vector<std::string> vecArgs;
	split_argument(argument, vecArgs);
	if (vecArgs.size() < 2) { return; }
	else if (vecArgs[1] == "unpoly")
	{
		CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
		if (pDungeon)
			pDungeon->UnPoly(ch);
	}
	else
	{
		if (!ch->IsGM())
			return;

		if (vecArgs[1] == "create")
		{
			CBalathorManager::Instance().Create(ch);
		}
		else if (vecArgs[1] == "close")
		{
			CBalathorManager::Instance().Close(ch);
		}
		else if (vecArgs[1] == "reload")
		{
			if (CBalathorManager::Instance().Load(true))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "balathor reload success");
			}
			else
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "balathor reload fail");
			}
		}
		else if (vecArgs[1] == "next_fail")
		{
			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
			{
				pDungeon->TakeOff(BALATHOR_TAKE_OFF_FAIL, false);
			}
		}
		else if (vecArgs[1] == "next_success")
		{
			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
			{
				pDungeon->TakeOff(BALATHOR_TAKE_OFF_SUCCESS, false);
			}

		}
		else if (vecArgs[1] == "motion")
		{
			if (vecArgs.size() < 4) { return; }
			BYTE bSkill;
			BYTE bSkill2;

			if (!str_to_number(bSkill, vecArgs[2].c_str()) || !str_to_number(bSkill2, vecArgs[3].c_str()))
				return;

			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
			{
				LPCHARACTER dragon = pDungeon->GetCharacterByFlag("dragon");
				if (dragon)
					pDungeon->Motion(dragon, bSkill, bSkill2);
			}
		}

		else if (vecArgs[1] == "spawn")
		{
			if (vecArgs.size() < 9) { return; }
			DWORD dwVnum;
			long lX, lY;
			BYTE bDirection;
			BYTE bSkill;
			BYTE bSkill2;
			BYTE bSpawnMotion;

			if (!str_to_number(dwVnum, vecArgs[2].c_str()) || !str_to_number(lX, vecArgs[3].c_str()) || !str_to_number(lY, vecArgs[4].c_str()) || !str_to_number(bDirection, vecArgs[5].c_str()) || !str_to_number(bSkill, vecArgs[6].c_str()) || !str_to_number(bSkill2, vecArgs[7].c_str()) || !str_to_number(bSpawnMotion, vecArgs[8].c_str()))
				return;
			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
			{
				LPCHARACTER mob = pDungeon->SpawnMobLocal(dwVnum, lX, lY, bDirection, bSpawnMotion ? true : false, true);

				if (mob)
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "spawn success");
					pDungeon->Motion(mob, bSkill, bSkill2);
				}
				else
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "spawn fail");
				}
			}
		}
		else if (vecArgs[1] == "eff_add")
		{
			if (vecArgs.size() < 9) { return; }

			BYTE bEffectIndex;
			long lX, lY, lZ;
			float fRotation;
			DWORD dwDuration;
			BYTE isMain;

			if (!str_to_number(bEffectIndex, vecArgs[2].c_str()) || !str_to_number(lX, vecArgs[3].c_str()) || !str_to_number(lY, vecArgs[4].c_str()) || !str_to_number(lZ, vecArgs[5].c_str()) || !str_to_number(fRotation, vecArgs[6].c_str()) || !str_to_number(dwDuration, vecArgs[7].c_str()) || !str_to_number(isMain, vecArgs[8].c_str()))
				return;

			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
				pDungeon->AddEffect(0, bEffectIndex, lX, lY, lZ, fRotation, dwDuration, isMain);

		}
		else if (vecArgs[1] == "eff_add_my")
		{
			if (vecArgs.size() < 9) { return; }

			BYTE bEffectIndex;
			long lX, lY, lZ;
			float fRotation;
			DWORD dwDuration;
			BYTE isMain;

			if (!str_to_number(bEffectIndex, vecArgs[2].c_str()) || !str_to_number(lX, vecArgs[3].c_str()) || !str_to_number(lY, vecArgs[4].c_str()) || !str_to_number(lZ, vecArgs[5].c_str()) || !str_to_number(fRotation, vecArgs[6].c_str()) || !str_to_number(dwDuration, vecArgs[7].c_str()) || !str_to_number(isMain, vecArgs[8].c_str()))
				return;

			CBalathor* pDungeon = CBalathorManager::Instance().FindByMapIndex(ch->GetMapIndex());
			if (pDungeon)
				pDungeon->AddEffect(ch->GetVID(), bEffectIndex, lX, lY, lZ, fRotation, dwDuration, isMain);

		}
		else if (vecArgs[1] == "cinema")
		{
			if (vecArgs.size() < 3) { return; }
			BYTE bCameraIndex;
			if (!str_to_number(bCameraIndex, vecArgs[2].c_str()))
				return;

			const std::string cameraFolders[BALATHOR_CINEMA_HIDDEN_MAX] = {
				"locale/common/camera/guild_white_dragonlair/boss_dead.txt",
				"locale/common/camera/guild_white_dragonlair/boss_spawn.txt",
				"locale/common/camera/guild_white_dragonlair/hidden_boss_dead.txt",
				"locale/common/camera/guild_white_dragonlair/hidden_boss_run_away.txt",
				"locale/common/camera/guild_white_dragonlair/hidden_boss_spawn.txt",
				"locale/common/camera/guild_white_dragonlair/singijeon_fire.txt"
			};

			if (bCameraIndex >= BALATHOR_CINEMA_HIDDEN_MAX)
				return;

			std::string folder("[RUN_CINEMA value;" + cameraFolders[bCameraIndex] + "]");

			struct packet_script pack;
			pack.header = HEADER_GC_SCRIPT;
			pack.skin = quest::CQuestManager::QUEST_SKIN_CINEMATIC;
			pack.src_size = folder.size();
			pack.size = pack.src_size + sizeof(struct packet_script);

			ch->GetDesc()->BufferedPacket(&pack, sizeof(struct packet_script));
			ch->GetDesc()->Packet(&folder[0], folder.size());
		}
	}
}
#endif
