#include "stdafx.h"

#ifdef __BALATHOR__
#include "balathor.h"
#include "char.h"
#include "desc.h"
#include "char_manager.h"
#include "utils.h"
#include "sectree_manager.h"
#include "party.h"
#include "packet.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "motion.h"
#include "packet.h"
#include "vector.h"
#include "guild.h"
#include "guild_manager.h"

CBalathor::CBalathor(DWORD dwMapIndex, DWORD dwID)
{
	m_dwEffID = 1;
	m_bStepIndex = 0;
	m_dwGuildID = dwID;
	m_dwMapIndex = dwMapIndex;
	m_dwProcessSleepTime = 0;
	SetStage(BALATHOR_STAGE_WAITING);
}

void CBalathor::Login(LPCHARACTER ch)
{
	if (m_bStage == BALATHOR_STAGE_NONE)
		return;

	if (std::find(m_vecPlayers.begin(), m_vecPlayers.end(), ch->GetPlayerID()) == m_vecPlayers.end())
		m_vecPlayers.emplace_back(ch->GetPlayerID());

	LoadEffects(ch);
}

void CBalathor::Logout(LPCHARACTER ch)
{
	UnPoly(ch);

	if (m_bStage == BALATHOR_STAGE_NONE)
		return;

	auto it = std::find(m_vecPlayers.begin(), m_vecPlayers.end(), ch->GetPlayerID());
	if (it != m_vecPlayers.end())
		m_vecPlayers.erase(it);
}

void CBalathor::Teleport(LPCHARACTER ch)
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	if (ch->GetMapIndex() != m_dwMapIndex)
	{
		//ch->SaveExitLocation();
		ch->WarpSet(config.base_pos.lGX, config.base_pos.lGY, m_dwMapIndex);
	}
	else
	{
		ch->Show(m_dwMapIndex, config.base_pos.lGX, config.base_pos.lGY);
	}
}

void CBalathor::Finish(BYTE bFinishType)
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	switch (bFinishType)
	{
		case BALATHOR_FINISH_FAIL_TIME:
			ChatPacket(CHAT_TYPE_NOTICE, "Balathor fail by time, you will send out in %s sec.", SecToTime(config.dwSendOutTime / 1000).c_str());
			break;
		case BALATHOR_FINISH_SUCCESS:
			ChatPacket(CHAT_TYPE_NOTICE, "Balathor success and leaves his treasure behind.");
			break;
		case BALATHOR_FINISH_FAIL:
			ChatPacket(CHAT_TYPE_NOTICE, "Balathor flees and leaves his treasure behind.");
			break;
		case BALATHOR_FINISH_FAIL_BY_GAMEMASTER:
			ChatPacket(CHAT_TYPE_NOTICE, "Balathor give up, you will send out in %s sec.", SecToTime(config.dwSendOutTime / 1000).c_str());
			break;
	}
	SetStage(BALATHOR_STAGE_CLOSE);
	CGuildManager::Instance().SetFlag(m_dwGuildID, "balathor_channel", 0);
}

void CBalathor::Close(bool bInstantClose)
{
	if (!bInstantClose)
	{
		m_bStage = BALATHOR_STAGE_NONE;
		m_dwStageTime = get_dword_time() + 3000;
	}

	ExitAll();
	ClearRegen();

	if (bInstantClose)
	{
		if (m_dwMapIndex != 0)
		{
			if (SECTREE_MANAGER::instance().GetMap(m_dwMapIndex))
				SECTREE_MANAGER::instance().DestroyPrivateMap(m_dwMapIndex);

			m_dwMapIndex = 0;
		}
	}
}

bool CBalathor::IsDeleted(DWORD dwCurTime)
{
	if (m_bStage == BALATHOR_STAGE_NONE && m_dwStageTime < dwCurTime)
		return true;
	return false;
}

void CBalathor::ExitAll()
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	for (const auto& pid : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(pid);
		if (ch)
			//ch->ExitToSavedLocation();
			ch->WarpSet(config.enter_base_pos.lGX, config.enter_base_pos.lGY);
	}
	m_vecPlayers.clear();
}

void CBalathor::KillRegen()
{
	for (const auto& vid : m_dwRegenMobs)
	{
		LPCHARACTER mob = CHARACTER_MANAGER::Instance().Find(vid);
		if (mob)
			mob->Dead();
	}
	m_dwRegenMobs.clear();
}

void CBalathor::ClearRegen()
{
	auto it = m_mapFlags.begin();
	while (it != m_mapFlags.end())
	{
		if (it->first.find("?_") != std::string::npos)
		{
			LPCHARACTER mob = CHARACTER_MANAGER::Instance().Find(it->second);
			if (mob)
				M2_DESTROY_CHARACTER(mob);
			it = m_mapFlags.erase(it);
			continue;
		}
		++it;
	}

	for (const auto& vid : m_dwRegenMobs)
	{
		LPCHARACTER mob = CHARACTER_MANAGER::Instance().Find(vid);
		if (mob)
			M2_DESTROY_CHARACTER(mob);
	}
	m_dwRegenMobs.clear();
}

void CBalathor::RunCinema(BYTE bCameraIndex)
{
	if (m_vecPlayers.empty())
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

	for (const auto& pid : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(pid);
		LPDESC d = ch ? ch->GetDesc() : NULL;

		if (d)
		{
			d->BufferedPacket(&pack, sizeof(struct packet_script));
			d->Packet(folder.c_str(), folder.size());
		}
	}
}

void CBalathor::QuestSay(const std::string& str)
{
	if (m_vecPlayers.empty())
		return;

	const std::string new_str(str + "[DONE]");
	//const std::string new_str("[ENTER]" + str + "[DONE]");

	struct packet_script pack;
	pack.header = HEADER_GC_SCRIPT;
	pack.skin = quest::CQuestManager::QUEST_SKIN_NORMAL;
	pack.src_size = new_str.size();
	pack.size = pack.src_size + sizeof(struct packet_script);

	for (const auto& pid : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(pid);
		LPDESC d = ch ? ch->GetDesc() : NULL;
		if (d)
		{
			d->BufferedPacket(&pack, sizeof(struct packet_script));
			d->Packet(new_str.c_str(), new_str.size());
		}
	}
}

void CBalathor::ChatPacket(BYTE bChatType, const char* szFormat, ...)
{
	char szBuf[CHAT_MAX_LEN + 1];
	va_list args;
	va_start(args, szFormat);
	vsnprintf(szBuf, sizeof(szBuf), szFormat, args);
	va_end(args);

	for (const auto& pid : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(pid);
		if (ch)
			ch->ChatPacket(bChatType, szBuf);
	}
}

DWORD CBalathor::GetFlag(std::string szFlag)
{
	const auto it = m_mapFlags.find(szFlag);
	return (it != m_mapFlags.end()) ? it->second : 0;
}

void CBalathor::SetFlag(std::string szFlag, DWORD dwValue)
{
	auto it = m_mapFlags.find(szFlag);
	if (it == m_mapFlags.end())
		m_mapFlags.emplace_hint(it, szFlag, dwValue);
	else
		it->second = dwValue;
}

void CBalathor::StoneSpawn(LPCHARACTER stone, int iPercent)
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
	DWORD dwRaceNum = stone->GetRaceNum();

	if (config.dwFlamingEggVnum == dwRaceNum || config.dwDoorVnum == dwRaceNum)
		return;

	int iSP = stone->GetMaxSP();
	BYTE bSpawnCount = 0;
	if (iPercent <= 10 && iSP < 10)
	{
		iSP = 10;
		bSpawnCount = 3;
	}
	//else if (iPercent <= 20 && iSP < 9)
	//{
	//	iSP = 9;
	//	bSpawnCount = 3;
	//}
	//else if (iPercent <= 30 && iSP < 8)
	//{
	//	iSP = 8;
	//	bSpawnCount = 3;
	//}
	else if (iPercent <= 40 && iSP < 7)
	{
		iSP = 7;
		bSpawnCount = 3;
	}
	//else if (iPercent <= 50 && iSP < 6)
	//{
	//	iSP = 6;
	//	bSpawnCount = 2;
	//}
	//else if (iPercent <= 60 && iSP < 5)
	//{
	//	iSP = 5;
	//	bSpawnCount = 2;
	//}
	else if (iPercent <= 70 && iSP < 4)
	{
		iSP = 4;
		bSpawnCount = 2;
	}
	//else if (iPercent <= 80 && iSP < 3)
	//{
	//	iSP = 3;
	//	bSpawnCount = 1;
	//}
	//else if (iPercent <= 90 && iSP < 2)
	//{
	//	iSP = 2;
	//	bSpawnCount = 1;
	//}
	//else if (iPercent <= 99 && iSP < 1)
	//{
	//	iSP = 1;
	//	bSpawnCount = 1;
	//}

	if (bSpawnCount != 0)
	{
		stone->SetMaxSP(iSP);
		stone->SendMovePacket(FUNC_ATTACK, 0, stone->GetX(), stone->GetY(), 0);
		for (BYTE i = 0; i < bSpawnCount; ++i)
			SpawnGroup(stone);
	}
}

LPCHARACTER CBalathor::SpawnMob(DWORD dwVnum, long lX, long lY, BYTE bDirection, bool bSpawnMotion, bool bShow)
{
	return CHARACTER_MANAGER::Instance().SpawnMob(dwVnum, m_dwMapIndex, lX, lY, 0, bSpawnMotion, bDirection == 0 ? number(0, 7) * 45 : (bDirection - 1) * 45, bShow);
}

LPCHARACTER CBalathor::SpawnMobLocal(DWORD dwVnum, long local_x, long local_y, BYTE bDirection, bool bSpawnMotion, bool bShow)
{
	long lX, lY;
	if (!LocalToGlobal(local_x, local_y, lX, lY))
		return 0;
	return SpawnMob(dwVnum, lX, lY, bDirection, bSpawnMotion, bShow);
}

void CBalathor::SpawnGroup(LPCHARACTER pStone)
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	CHARACTER_MANAGER& chrMngr = CHARACTER_MANAGER::Instance();

	long sx, sy, ex, ey;
	if (pStone)
	{
		sx = pStone->GetX() - number(0, 249);
		sy = pStone->GetY() - number(250, 500);
		ex = pStone->GetX() + number(0, 249);
		ey = pStone->GetY() + number(250, 500);
	}
	else
	{
		if (m_bStepIndex >= 3 && m_bStepIndex <= 5)
		{
			sx = config.hwacha_pos.lGX - number(0, 249);
			sy = config.hwacha_pos.lGY - number(250, 500);
			ex = config.hwacha_pos.lGX + number(0, 249);
			ey = config.hwacha_pos.lGY + number(250, 500);
		}
		else if (m_bStepIndex == 6)
		{
			sx = config.boss_2_pos.lGX - number(0, 249);
			sy = config.boss_2_pos.lGY - number(250, 500);
			ex = config.boss_2_pos.lGX + number(0, 249);
			ey = config.boss_2_pos.lGY + number(250, 500);
		}
		else
		{
			sx = config.regen_pos.lGX - number(0, 249);
			sy = config.regen_pos.lGY - number(250, 500);
			ex = config.regen_pos.lGX + number(0, 249);
			ey = config.regen_pos.lGY + number(250, 500);
		}
	}

	LPPARTY pkParty = NULL;
	for (BYTE i = 0; i < BALATHOR_REGEN_GROUP_SIZE; ++i)
	{
		DWORD dwMobVnum = pStone ? config.dwStoneRegenMob[i] : config.dwRegenMob[i];
		LPCHARACTER tch = chrMngr.SpawnMobRange(dwMobVnum, m_dwMapIndex, sx, sy, ex, ey, true, true);

		if (!tch)
			continue;

		tch->SetAggressive();

		sx = tch->GetX() - number(0, 249);
		sy = tch->GetY() - number(250, 500);
		ex = tch->GetX() + number(0, 249);
		ey = tch->GetY() + number(250, 500);

		if (pStone)
			tch->SetStone(pStone);
		else
		{
			if (pkParty)
			{
				pkParty->Join(tch->GetVID());
				pkParty->Link(tch);
			}
			else if (!pkParty)
			{
				pkParty = CPartyManager::instance().CreateParty(tch);
			}
		}
		m_dwRegenMobs.emplace_back(tch->GetVID());
	}
}

bool CBalathor::GlobalToLocal(long globalX, long globalY, long& lX, long& lY)
{
	if (!m_dwMapIndex)
		return false;
	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(m_dwMapIndex);
	if (!pkSectreeMap)
		return false;
	lX = (globalX - pkSectreeMap->m_setting.iBaseX) / 100;
	lY = (globalY - pkSectreeMap->m_setting.iBaseY) / 100;
	return true;
}

bool CBalathor::LocalToGlobal(long localX, long localY, long& lX, long& lY)
{
	if (!m_dwMapIndex)
		return false;
	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(m_dwMapIndex);
	if (!pkSectreeMap)
		return false;
	lX = (localX * 100) + pkSectreeMap->m_setting.iBaseX;
	lY = (localY * 100) + pkSectreeMap->m_setting.iBaseY;
	return true;
}

void CBalathor::RemoveEffectByID(DWORD dwID)
{
	auto it = m_vecEffects.begin();
	while (it != m_vecEffects.end())
	{
		if (it->dwID == dwID || !dwID)
		{
			ChatPacket(CHAT_TYPE_COMMAND, "BalathorEffectRemove %u", it->dwID);
			it = m_vecEffects.erase(it);
			break;
		}
		++it;
	}
}
void CBalathor::RemoveEffectByVID(DWORD dwVID)
{
	auto it = m_vecEffects.begin();
	while (it != m_vecEffects.end())
	{
		if (it->dwVID == dwVID)
		{
			ChatPacket(CHAT_TYPE_COMMAND, "BalathorEffectRemove %u", it->dwID);
			it = m_vecEffects.erase(it);
			continue;
		}
		++it;
	}
}

bool CBalathor::IsEffIndexExist(BYTE bEffIndex)
{
	for (const auto& effectInfo : m_vecEffects)
	{
		if (effectInfo.bEffIndex == bEffIndex)
			return true;
	}
	return false;
}

DWORD CBalathor::AddEffect(DWORD dwVID, BYTE bEffIndex, long lX, long lY, long lZ, float fRotation, DWORD dwDuration, bool bIsMain)
{
	for (const auto& effect : m_vecEffects)
	{
		if (effect.dwVID == dwVID && effect.bEffIndex == bEffIndex && effect.lX == lX && effect.lY == lY)
			return effect.dwID;
	}

	long lGX, lGY;
	if (!LocalToGlobal(lX, lY, lGX, lGY))
		return 0;

	TBalathorEffect effectInfo;
	effectInfo.dwID = ++m_dwEffID;
	effectInfo.dwVID = dwVID;
	effectInfo.bEffIndex = bEffIndex;
	effectInfo.lX = lX;
	effectInfo.lY = lY;
	effectInfo.lZ = lZ;
	effectInfo.lGX = lGX;
	effectInfo.lGY = lGY;
	effectInfo.fRotation = fRotation;
	effectInfo.bIsMain = bIsMain;
	effectInfo.bNeedRemove = false;
	effectInfo.bDamage = false;
	effectInfo.bStage = 0;
	effectInfo.dwDuration = get_dword_time() + dwDuration;
	m_vecEffects.emplace_back(effectInfo);

	ChatPacket(CHAT_TYPE_COMMAND, "BalathorEffectAdd %u %u %u %ld %ld %ld %.01f %u", effectInfo.dwID, dwVID, bEffIndex, lX, lY, lZ, fRotation, bIsMain);

	return effectInfo.dwID;
}

void CBalathor::LoadEffects(LPCHARACTER ch)
{
	for (const auto& effectInfo : m_vecEffects)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BalathorEffectAdd %u %u %u %ld %ld %ld %.01f %u",
			effectInfo.dwID, effectInfo.dwVID, effectInfo.bEffIndex, effectInfo.lX, effectInfo.lY, effectInfo.lZ, effectInfo.fRotation, effectInfo.bIsMain);
}

void CBalathor::UpdateUI()
{
	if (m_vecPlayers.empty())
		return;

	int iBalathorHP = 0;
	int iBalathorMaxHP = 0;

	LPCHARACTER pBalathor = GetCharacterByFlag("dragon");
	if (pBalathor)
	{
		iBalathorHP = pBalathor->GetHP();
		iBalathorMaxHP = pBalathor->GetMaxHP();
	}

	int iHwatchaHP = 0;
	int iHwatchaMaxHP = 0;

	LPCHARACTER pHwatcha = GetCharacterByFlag("hwatcha");
	if (pHwatcha)
	{
		iHwatchaHP = pHwatcha->GetHP();
		iHwatchaMaxHP = pHwatcha->GetMaxHP();
	}

	ChatPacket(CHAT_TYPE_COMMAND, "SetBalathor %d %d %u %u %u %u %d %d", iBalathorHP, iBalathorMaxHP, GetFlag("balathor_rage"), BALATHOR_RAGE_MAX, GetFlag("fail_egg_count"), GetFlag("fire_arrow_count"), iHwatchaHP, iHwatchaMaxHP);
}

bool CBalathor::UseItem(LPCHARACTER ch, LPITEM item)
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
	if (config.dwFireArrowVnum == item->GetVnum())
	{
		DWORD dwNewArrowCount = GetFlag("fire_arrow_count") + 1;
		SetFlag("fire_arrow_count", dwNewArrowCount);
		item->SetCount(item->GetCount() - 1);

		ChatPacket(CHAT_TYPE_NOTICE, "The Hwacha is currently loaded with %u Fire Arrows.", dwNewArrowCount);

		if (dwNewArrowCount >= config.bHwatchaRequiredArrowCount)
			SetHwatchaEffect(true);

		UpdateUI();
		return true;
	}
	return false;
}

LPCHARACTER CBalathor::SpawnCharacterByFlag(const std::string& str)
{
	if (GetCharacterVIDByFlag(str))
		return GetCharacterByFlag(str);

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	if (str == "chest")
	{
		LPCHARACTER chest = SpawnMob(config.dwChestVnum, config.chest_pos.lGX, config.chest_pos.lGY, config.chest_pos.bDirection, false, true);
		if (chest)
		{
			SetCharacterByFlag("chest", chest->GetVID());
			return chest;
		}
	}
	else if (str == "npc")
	{
		LPCHARACTER npc = SpawnMob(config.dwNPCVnum, config.npc_pos.lGX, config.npc_pos.lGY, config.npc_pos.bDirection, false, true);
		if (npc)
		{
			SetCharacterByFlag("npc", npc->GetVID());
			return npc;
		}
	}
	else if (str == "enter_door")
	{
		LPCHARACTER door = SpawnMob(config.dwDoorVnum, config.door_pos.lGX, config.door_pos.lGY, config.door_pos.bDirection, false, true);
		if (door)
		{
			SetCharacterByFlag("enter_door", door->GetVID());
			return door;
		}
	}
	else if (str == "ice_crystal")
	{
		LPCHARACTER ice_crystal = SpawnMob(config.dwIceCrystalVnum, config.ice_crystal_pos.lGX, config.ice_crystal_pos.lGY, config.ice_crystal_pos.bDirection, false, true);
		if (ice_crystal)
		{
			SetCharacterByFlag("ice_crystal", ice_crystal->GetVID());
			return ice_crystal;
		}
	}
	else if (str == "dragon_1")
	{
		LPCHARACTER dragon = SpawnMob(config.dwBossVnum1, config.boss_1_pos.lGX, config.boss_1_pos.lGY, config.boss_1_pos.bDirection, true, true);
		if (dragon)
		{
			dragon->SetBalathor(true);
			SetCharacterByFlag("dragon", dragon->GetVID());
			return dragon;
		}
	}
	else if (str == "dragon_2")
	{
		LPCHARACTER dragon = SpawnMob(config.dwBossVnum2, config.boss_2_pos.lGX, config.boss_2_pos.lGY, config.boss_2_pos.bDirection, true, true);
		if (dragon)
		{
			dragon->SetBalathor(true);
			SetCharacterByFlag("dragon", dragon->GetVID());
			return dragon;
		}
	}
	else if (str == "hwatcha")
	{
		LPCHARACTER hwatcha = SpawnMob(config.dwHwachaVnum, config.hwacha_pos.lGX, config.hwacha_pos.lGY, config.hwacha_pos.bDirection, false, true);
		if (hwatcha)
		{
			SetCharacterByFlag("hwatcha", hwatcha->GetVID());
			return hwatcha;
		}
	}
	else if (str == "flaming_egg_1")
	{
		LPCHARACTER flaming_egg = SpawnMob(config.dwFlamingEggVnum, config.flaming_egg_pos1.lGX, config.flaming_egg_pos1.lGY, config.flaming_egg_pos1.bDirection, false, true);
		if (flaming_egg)
		{
			SetCharacterByFlag("flaming_egg_1", flaming_egg->GetVID());
			AddEffect(0, BALATHOR_EFF_EGG_ARROW, config.boss_1_egg_pos1.lX, config.boss_1_egg_pos1.lY, 100, 0.0f, INFINITE_EFFECT_TIME, false);
			return flaming_egg;
		}
	}
	else if (str == "flaming_egg_2")
	{
		LPCHARACTER flaming_egg = SpawnMob(config.dwFlamingEggVnum, config.flaming_egg_pos2.lGX, config.flaming_egg_pos2.lGY, config.flaming_egg_pos2.bDirection, false, true);
		if (flaming_egg)
		{
			SetCharacterByFlag("flaming_egg_2", flaming_egg->GetVID());
			AddEffect(0, BALATHOR_EFF_EGG_ARROW, config.boss_1_egg_pos2.lX, config.boss_1_egg_pos2.lY, 100, 0.0f, INFINITE_EFFECT_TIME, false);
			return flaming_egg;
		}
	}
	else if (str == "dragon_egg_1")
	{
		LPCHARACTER dragon_egg = SpawnMob(config.dwFrozenEggVnum1, config.boss_1_egg_pos1.lGX, config.boss_1_egg_pos1.lGY, config.boss_1_egg_pos1.bDirection, false, true);
		if (dragon_egg)
		{
			dragon_egg->SetBalathorEgg(true);
			SetCharacterByFlag("dragon_egg_1", dragon_egg->GetVID());
			return dragon_egg;
		}
	}
	else if (str == "dragon_egg_2")
	{
		LPCHARACTER dragon_egg = SpawnMob(config.dwFrozenEggVnum1, config.boss_1_egg_pos2.lGX, config.boss_1_egg_pos2.lGY, config.boss_1_egg_pos2.bDirection, false, true);
		if (dragon_egg)
		{
			dragon_egg->SetBalathorEgg(true);
			SetCharacterByFlag("dragon_egg_2", dragon_egg->GetVID());
			return dragon_egg;
		}
	}
	else if (str == "dragon_egg_wave_1")
	{
		LPCHARACTER dragon_wave_egg = SpawnMob(config.dwFrozenEggVnum2, config.dragon_egg_1_pos.lGX, config.dragon_egg_1_pos.lGY, config.dragon_egg_1_pos.bDirection, false, true);
		if (dragon_wave_egg)
		{
			dragon_wave_egg->SetBalathorEgg(true);
			AddEffect(dragon_wave_egg->GetVID(), BALATHOR_EFF_EGG_FLOOD, 0, 0, 0, 0.0f, 10000, 0);
			SetCharacterByFlag("dragon_egg_wave", dragon_wave_egg->GetVID());
			return dragon_wave_egg;
		}
	}
	else if (str == "dragon_egg_wave_2")
	{
		LPCHARACTER dragon_wave_egg = SpawnMob(config.dwFrozenEggVnum2, config.dragon_egg_2_pos.lGX, config.dragon_egg_2_pos.lGY, config.dragon_egg_2_pos.bDirection, false, true);
		if (dragon_wave_egg)
		{
			dragon_wave_egg->SetBalathorEgg(true);
			AddEffect(dragon_wave_egg->GetVID(), BALATHOR_EFF_EGG_FLOOD, 0, 0, 0, 0.0f, 10000, 0);
			SetCharacterByFlag("dragon_egg_wave", dragon_wave_egg->GetVID());
			return dragon_wave_egg;
		}
	}
	else if (str == "dragon_egg_wave_3")
	{
		LPCHARACTER dragon_wave_egg = SpawnMob(config.dwFrozenEggVnum2, config.dragon_egg_3_pos.lGX, config.dragon_egg_3_pos.lGY, config.dragon_egg_3_pos.bDirection, false, true);
		if (dragon_wave_egg)
		{
			dragon_wave_egg->SetBalathorEgg(true);
			AddEffect(dragon_wave_egg->GetVID(), BALATHOR_EFF_EGG_FLOOD, 0, 0, 0, 0.0f, 10000, 0);
			SetCharacterByFlag("dragon_egg_wave", dragon_wave_egg->GetVID());
			return dragon_wave_egg;
		}
	}
	else if (str == "dragon_egg_wave_4")
	{
		LPCHARACTER dragon_wave_egg = SpawnMob(config.dwFrozenEggVnum2, config.dragon_egg_4_pos.lGX, config.dragon_egg_4_pos.lGY, config.dragon_egg_4_pos.bDirection, false, true);
		if (dragon_wave_egg)
		{
			dragon_wave_egg->SetBalathorEgg(true);
			AddEffect(dragon_wave_egg->GetVID(), BALATHOR_EFF_EGG_FLOOD, 0, 0, 0, 0.0f, 10000, 0);
			SetCharacterByFlag("dragon_egg_wave", dragon_wave_egg->GetVID());
			return dragon_wave_egg;
		}
	}


	return NULL;
}

DWORD CBalathor::GetCharacterVIDByFlag(const std::string& str)
{
	return GetFlag("?_" + str);
}

void CBalathor::RemoveCharacterByFlag(const std::string& str)
{
	DWORD dwVID = GetFlag("?_" + str);
	if (dwVID != 0)
	{
		SetFlag("?_" + str, 0);
		LPCHARACTER mob = CHARACTER_MANAGER::Instance().Find(dwVID);
		if (mob)
			M2_DESTROY_CHARACTER(mob);
	}

}
LPCHARACTER CBalathor::GetCharacterByFlag(const std::string& str)
{
	DWORD dwVID = GetFlag("?_" + str);
	if (!dwVID)
		return NULL;
	return CHARACTER_MANAGER::Instance().Find(dwVID);
}

void CBalathor::SetCharacterByFlag(const std::string& str, DWORD dwVID)
{
	SetFlag("?_" + str, dwVID);
}

bool CBalathor::ReviveHwatcha()
{
	LPCHARACTER pHwatcha = GetCharacterByFlag("hwatcha");
	if (!pHwatcha || !pHwatcha->IsDead())
		return false;

	pHwatcha->SetPosition(POS_STANDING);
	pHwatcha->PointChange(POINT_HP, pHwatcha->GetMaxHP() - pHwatcha->GetHP());
	pHwatcha->Show(pHwatcha->GetMapIndex(), pHwatcha->GetX(), pHwatcha->GetY(), 0, true);

	UpdateUI();
	return true;
}

bool CBalathor::IsHwatchaDead()
{
	LPCHARACTER pHwatcha = GetCharacterByFlag("hwatcha");
	if (pHwatcha)
		return pHwatcha->IsDead();
	return false;
}

bool CBalathor::CanUseHwatcha()
{
	if (IsEffIndexExist(BALATHOR_EFF_AREA))
		return false;

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	CGuild* pGuild = CGuildManager::Instance().FindGuild(m_dwGuildID);
	if (pGuild)
	{
		if (pGuild->GetSP() < config.dwReviveHwatchaRequestSP)
			return false;
	}

	return GetFlag("fire_arrow_count") >= config.bHwatchaRequiredArrowCount;
}

void CBalathor::UseHwatcha()
{
	LPCHARACTER pHwatcha = GetCharacterByFlag("hwatcha");
	if (!pHwatcha)
		return;

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
	DWORD dwArrowCount = GetFlag("fire_arrow_count");
	if (dwArrowCount < config.bHwatchaRequiredArrowCount)
		return;
	dwArrowCount -= config.bHwatchaRequiredArrowCount;
	SetFlag("fire_arrow_count", dwArrowCount);

	UpdateUI();

	if(dwArrowCount < config.bHwatchaRequiredArrowCount)
		SetHwatchaEffect(false);
	else
		SetHwatchaEffect(true);

	CGuild* pGuild = CGuildManager::Instance().FindGuild(m_dwGuildID);
	if (pGuild)
	{
		int iValue = static_cast<long>(config.dwReviveHwatchaRequestSP);
		pGuild->SendDBSkillUpdate(-iValue);
	}

	DWORD dwCurTime = get_dword_time();

	SetFlag("hwatcha_skill_time", dwCurTime + 300);
	SetFlag("hwatcha_dead_check", dwCurTime + 4000);
	SetFlag("hwatcha_skill_percent", 4);

	SetAttackSleepTime(5000);
	Motion(pHwatcha, HWATCHA_FIRE_SKILL_INDEX, 255);
	RunCinema(BALATHOR_CINEMA_HIDDEN_HWATCHA_FIRE);

	LPCHARACTER dragon_egg_1 = GetCharacterByFlag("dragon_egg_1");
	if (dragon_egg_1 && dragon_egg_1->GetBlockStatus())
	{
		dragon_egg_1->SetBlockStatus(false);
		RemoveEffectByVID(dragon_egg_1->GetVID());

		//SetFlag("dragon_egg_1_time", dwCurTime);
	}

	LPCHARACTER dragon_egg_2 = GetCharacterByFlag("dragon_egg_2");
	if (dragon_egg_2 && dragon_egg_2->GetBlockStatus())
	{
		dragon_egg_2->SetBlockStatus(false);
		RemoveEffectByVID(dragon_egg_2->GetVID());

		//SetFlag("dragon_egg_2_time", dwCurTime);
	}
}

void CBalathor::SetHwatchaEffect(bool bStatus)
{
	DWORD dwEffectIndex = GetFlag("!_hwatcha_eff");
	if (bStatus)
	{
		if (dwEffectIndex != 0)
			return;
		const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
		SetFlag("!_hwatcha_eff", AddEffect(0, BALATHOR_EFF_RED_ARROW, config.hwacha_pos.lX, config.hwacha_pos.lY, 180, 0.0f, INFINITE_EFFECT_TIME, false));
	}
	else
	{
		if (dwEffectIndex != 0)
		{
			RemoveEffectByID(dwEffectIndex);
			SetFlag("!_hwatcha_eff", 0);
		}
	}
}

void CBalathor::AddRaid(DWORD dwValue)
{
	SetFlag("raid_extra_value", dwValue);
}

void CBalathor::ProcessRaid(DWORD dwCurTime)
{
	if (!(m_bStepIndex >= 5 && m_bStepIndex <= 6))
		return;

	DWORD dwLeftTime = GetFlag("raid_last_update");
	if (dwLeftTime != 0 && dwLeftTime > dwCurTime)
		return;
	SetFlag("raid_last_update", dwCurTime + 1000);

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	DWORD dwRaidExtraValue = GetFlag("raid_extra_value");
	if(dwRaidExtraValue != 0)
		SetFlag("raid_extra_value", 0);

	DWORD dwRaidValue = GetFlag("balathor_rage") + config.dwRaidIncreaseBySec + dwRaidExtraValue;
	if (dwRaidValue > BALATHOR_RAGE_MAX)
		dwRaidValue = BALATHOR_RAGE_MAX;

	if (dwRaidValue == BALATHOR_RAGE_MAX)
	{
		SetFlag("raid_last_update", dwCurTime + 6000);
		SetFlag("raid_attack", dwCurTime + 3000);
	}

	SetFlag("balathor_rage", dwRaidValue);
	UpdateUI();
	if (dwRaidValue == BALATHOR_RAGE_MAX)
	{
		SetFlag("balathor_rage", 0);
	}
}

void CBalathor::Process(DWORD dwCurTime)
{
	if (m_bStage == BALATHOR_STAGE_RUN)
		ProcessEffect(dwCurTime);

	if (m_dwProcessSleepTime > dwCurTime)
		return;
	m_dwProcessSleepTime = dwCurTime + BALATHOR_PROCESS_SLEEP_TIME;

	if (m_bStage == BALATHOR_STAGE_CLOSE)
	{
		if (m_dwStageTime < dwCurTime)
		{
			Close(false);
		}
	}
	else if (m_bStage == BALATHOR_STAGE_WAITING)
	{
		if (m_dwStageTime < dwCurTime)
		{
			Finish(BALATHOR_FINISH_FAIL_TIME);
		}
	}
	else if (m_bStage == BALATHOR_STAGE_RUN)
	{
		StepProgress(dwCurTime);
	}
}

void CBalathor::SetStage(BYTE bStage)
{
	m_bStage = bStage;

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
	switch (bStage)
	{
		case BALATHOR_STAGE_CLOSE:
		{
			m_dwStageTime = get_dword_time() + config.dwSendOutTime;
		}
		break;
		case BALATHOR_STAGE_WAITING:
		{
			m_dwStageTime = get_dword_time() + config.dwWaitingTime;

			SpawnCharacterByFlag("npc");

			LPCHARACTER enter_door = SpawnCharacterByFlag("enter_door");
			if (enter_door)
			{
				enter_door->SetBlockRotation(true);
				enter_door->SetBlockStatus(true);
			}
		}
		break;
		case BALATHOR_STAGE_RUN:
		{
			m_bStepIndex = 1;

			m_dwStageTime = get_dword_time();

			LPCHARACTER enter_door = GetCharacterByFlag("enter_door");
			if (enter_door)
				enter_door->SetBlockStatus(false);
		}
		break;
	}
}

void CBalathor::Damage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim)
{
	if (m_bStepIndex != 6)
		return;

	LPCHARACTER dragon = GetCharacterByFlag("dragon");
	if (dragon == pkVictim)
	{
		int iPercent = 0;
		if (dragon->GetMaxHP() >= 0)
			iPercent = (dragon->GetHP() * 100) / dragon->GetMaxHP();

		if (GetFlag("egg_wave_failtime") != 0 || GetFlag("egg_wave_lefttime") != 0)
			return;

		if (iPercent < 10 && GetFlag("step6_wave") == 2)
		{
			ChatPacket(CHAT_TYPE_NOTICE, "In 10 seconds, Balathor's Dragon Egg will appear and you can initiate a targetted attack.");
			SetFlag("egg_wave_lefttime", get_dword_time() + 10000);
			SetFlag("step6_wave", 3);
		}
		else if (iPercent < 25 && GetFlag("step6_wave") == 1)
		{
			ChatPacket(CHAT_TYPE_NOTICE, "In 10 seconds, Balathor's Dragon Egg will appear and you can initiate a targetted attack.");
			SetFlag("egg_wave_lefttime", get_dword_time() + 10000);
			SetFlag("step6_wave", 2);
		}
		else if (iPercent < 50 && GetFlag("step6_wave") == 0)
		{
			ChatPacket(CHAT_TYPE_NOTICE, "In 10 seconds, Balathor's Dragon Egg will appear and you can initiate a targetted attack.");
			SetFlag("egg_wave_lefttime", get_dword_time() + 10000);
			SetFlag("step6_wave", 1);
		}
		return;
	}

	LPCHARACTER dragon_egg_wave = GetCharacterByFlag("dragon_egg_wave");
	if (dragon_egg_wave == pkVictim)
	{
		RemoveEffectByVID(dragon_egg_wave->GetVID());
		dragon_egg_wave->Dead();
		SetCharacterByFlag("dragon_egg_wave", 0);

		ChatPacket(CHAT_TYPE_NOTICE, "You have successfully warded off the ice cold.");

		SetFlag("egg_wave_failtime_count", 0);
		SetFlag("egg_wave_failtime", 0);

		AddRaid(25);

		if (GetFlag("dragon_egg_wave_index") == 4)
		{
			ChatPacket(CHAT_TYPE_NOTICE, "More damage will be needed for the next attack.");
			SetFlag("egg_wave_lefttime", 0);
			SetFlag("dragon_egg_wave_index", 0);
		}
		else
		{
			ChatPacket(CHAT_TYPE_NOTICE, "In 10 seconds, Balathor's Dragon Egg will appear and you can initiate a targetted attack.");
			SetFlag("egg_wave_lefttime", get_dword_time() + 10000);
		}
	}
}

void CBalathor::Kill(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, bool bFromStone)
{
	if (pkVictim->IsPC())
	{
		UnPoly(pkVictim);
	}
	else
	{
		if (!pkAttacker)
			return;

		const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

		DWORD dwCurTime = get_dword_time();
		DWORD dwVictimVID = pkVictim->GetVID();

		if (pkVictim->IsStone() && pkAttacker->IsPC())
		{
			CHARACTER_SET& stoneMobs = pkVictim->GetStoneMobs();
			for (auto mob : stoneMobs)
				Kill(pkAttacker, mob, true);
		}

		const auto it = std::find(m_dwRegenMobs.begin(), m_dwRegenMobs.end(), dwVictimVID);
		if (it != m_dwRegenMobs.end())
			m_dwRegenMobs.erase(it);

		if (!bFromStone)
		{
			if (pkVictim->IsMonster() && pkVictim->GetMobRank() < MOB_RANK_BOSS && m_bStepIndex >= 3 && m_bStepIndex <= 5)
			{
				if (number(0, 100) <= config.bFireArrowDropLuck)
				{
					LPITEM item = ITEM_MANAGER::instance().CreateItem(config.dwFireArrowVnum);
					if (item)
					{
						PIXEL_POSITION pos;
						pos.x = pkVictim->GetX() + number(-200, 200);
						pos.y = pkVictim->GetY() + number(-200, 200);
						item->AddToGround(pkVictim->GetMapIndex(), pos);
						item->StartDestroyEvent();
					}
				}
			}
		}

		if (m_bStepIndex == 1)
		{
			if (GetCharacterVIDByFlag("enter_door") == dwVictimVID)
			{
				SetCharacterByFlag("enter_door", 0);

				m_bStepIndex = 2;

				SpawnGroup(NULL);

				SetFlag("regen_count", config.bRequestGroupKillCount - 1);

				ChatPacket(CHAT_TYPE_NOTICE, "Defeat all nearby monsters.");
				QuestSay("Defeat all nearby monsters.");
			}
		}
		else if (m_bStepIndex == 2)
		{
			if (m_dwRegenMobs.empty())
			{
				DWORD dwRegenCount = GetFlag("regen_count");

				if (!dwRegenCount)
				{
					m_bStepIndex = 3;
					SpawnCharacterByFlag("ice_crystal");
				}
				else
				{
					SetFlag("regen_count", dwRegenCount - 1);
					SpawnGroup(NULL);
				}
			}
		}
		else if (m_bStepIndex == 3)
		{
			if (GetCharacterVIDByFlag("ice_crystal") == dwVictimVID)
			{
				SetCharacterByFlag("ice_crystal", 0);

				m_bStepIndex = 4;

				ChatPacket(CHAT_TYPE_NOTICE, "Destroy the Solid Ice Wall which protects the[ENTER]Dragon Eggs!");
				QuestSay("Destroy the Solid Ice Wall which protects the[ENTER]Dragon Eggs!");

				for (BYTE i = 1; i <= 2; ++i)
				{
					LPCHARACTER egg = NULL;

					if (i == 1)
						egg = SpawnMob(config.dwFrozenEggVnum1, config.boss_1_egg_pos1.lGX, config.boss_1_egg_pos1.lGY, config.boss_1_egg_pos1.bDirection, false, true);
					else if (i == 2)
						egg = SpawnMob(config.dwFrozenEggVnum1, config.boss_1_egg_pos2.lGX, config.boss_1_egg_pos2.lGY, config.boss_1_egg_pos2.bDirection, false, true);

					if (egg)
						m_dwRegenMobs.emplace_back(egg->GetVID());
				}

				for (BYTE i = 1; i <= 3; ++i)
				{
					LPCHARACTER door = NULL;
					if (i == 1)
						door = SpawnMob(config.dwDoorVnum, config.boss_1_door1_pos.lGX, config.boss_1_door1_pos.lGY, config.boss_1_door1_pos.bDirection, false, true);
					else if (i == 2)
						door = SpawnMob(config.dwDoorVnum, config.boss_1_door2_pos.lGX, config.boss_1_door2_pos.lGY, config.boss_1_door2_pos.bDirection, false, true);
					else if (i == 3)
						door = SpawnMob(config.dwDoorVnum, config.boss_1_door3_pos.lGX, config.boss_1_door3_pos.lGY, config.boss_1_door3_pos.bDirection, false, true);

					if (door)
					{
						door->SetBlockRotation(true);
						m_dwRegenMobs.emplace_back(door->GetVID());
					}
				}
			}
		}
		else if (m_bStepIndex == 4)
		{
			if (m_dwRegenMobs.empty())
			{
				m_bStepIndex = 5;

				SpawnCharacterByFlag("dragon_1");
				RunCinema(BALATHOR_CINEMA_BOSS_SPAWN);
				SetFlag("cinema_fake_skill", dwCurTime + config.dwBoss1FakeSkillTime);

				SetFlag("regen_group", get_dword_time() + 25000);

				SetAttackSleepTime(dwCurTime + config.dwBoss1FakeSkillTime);
				SetFlag("raid_attack", dwCurTime + config.dwBoss1FakeSkillTime + 2000);

				SetFlag("fail_egg_count", config.bFireEggFailMaxCount);
				SetFlag("flaming_egg_spawn", dwCurTime + config.dwFlamingEggSpawnTime);
			}
		}
		else if (m_bStepIndex == 5)
		{
			if (GetCharacterVIDByFlag("ice_crystal") == dwVictimVID)
			{
				SetCharacterByFlag("ice_crystal", 0);
				SetFlag("ice_crystal_spawn", dwCurTime + config.dwIceCrystalSpawnPerTime);
			}

			if (GetCharacterVIDByFlag("dragon_egg_1") == dwVictimVID || GetCharacterVIDByFlag("dragon_egg_2") == dwVictimVID)
			{
				if (GetCharacterVIDByFlag("dragon_egg_1") == dwVictimVID)
					SetCharacterByFlag("dragon_egg_1", 0);
				else
					SetCharacterByFlag("dragon_egg_2", 0);

				if (GetCharacterVIDByFlag("dragon_egg_1") == 0 && GetCharacterVIDByFlag("dragon_egg_2") == 0)
				{
					if(GetFlag("ice_crystal_spawn") == 0)
						SpawnCharacterByFlag("ice_crystal");

					SetFlag("flaming_egg_spawn", dwCurTime + config.dwFlamingEggSpawnTime);
				}
			}

			if (GetCharacterVIDByFlag("flaming_egg_1") == dwVictimVID || GetCharacterVIDByFlag("flaming_egg_2") == dwVictimVID)
			{
				bool is_first_egg = GetCharacterVIDByFlag("flaming_egg_1") == dwVictimVID;
				
				if(is_first_egg)
					SetCharacterByFlag("flaming_egg_1", 0);
				else
					SetCharacterByFlag("flaming_egg_2", 0);

				DWORD dwLeftFailEggCount = GetFlag("fail_egg_count");
				if (!dwLeftFailEggCount)
				{
					TakeOff(BALATHOR_TAKE_OFF_FAIL, false);
				}
				else
				{
					SetFlag("fail_egg_count", dwLeftFailEggCount - 1);
					if (is_first_egg)
						SpawnCharacterByFlag("flaming_egg_1");
					else
						SpawnCharacterByFlag("flaming_egg_2");
				}
				UpdateUI();
			}
		}
		else if (m_bStepIndex == 6)
		{
			if (GetCharacterVIDByFlag("dragon") == dwVictimVID)
			{
				TakeOff(BALATHOR_TAKE_OFF_SUCCESS, true);
			}
		}

	}
}

void CBalathor::StepProgress(DWORD dwCurTime)
{
	ProcessRaid(dwCurTime);
	AttackProcess(dwCurTime);

	DWORD dwLeftTime = GetFlag("balathor_finish_fail");
	if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
	{
		SetFlag("balathor_fail_finish", 0);
		Finish(BALATHOR_FINISH_FAIL);
		SpawnCharacterByFlag("chest");
	}

	if (m_bStepIndex >= 3 && m_bStepIndex <= 6)
	{
		dwLeftTime = GetFlag("regen_group");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
			SetFlag("regen_group", dwCurTime + config.dwRegenSpawnPerTime);
			
			if (m_dwRegenMobs.size() < config.dwRegenMaxCount)
				SpawnGroup(NULL);
		}
	}

	dwLeftTime = GetFlag("balathor_finish_vid_time");
	if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
	{
		SetFlag("balathor_finish_vid_time", 0);

		DWORD dwDragonVID = GetFlag("balathor_finish_vid");
		if (dwDragonVID != 0)
		{
			SetFlag("balathor_finish_vid", 0);
			LPCHARACTER dragon = CHARACTER_MANAGER::Instance().Find(dwDragonVID);
			if (dragon)
				M2_DESTROY_CHARACTER(dragon);
		}
	}

	dwLeftTime = GetFlag("balathor_finish_success");
	if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
	{
		SetFlag("balathor_finish_success", 0);
		Finish(BALATHOR_FINISH_SUCCESS);
		SpawnCharacterByFlag("chest");
	}

	if (m_bStepIndex == 6)
	{
		dwLeftTime = GetFlag("egg_wave_lefttime");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			SetFlag("egg_wave_lefttime", 0);

			DWORD dwDragonEggIndex = GetFlag("dragon_egg_wave_index");

			if(dwDragonEggIndex == 0)
				SpawnCharacterByFlag("dragon_egg_wave_1");
			else if (dwDragonEggIndex == 1)
				SpawnCharacterByFlag("dragon_egg_wave_2");
			else if (dwDragonEggIndex == 2)
				SpawnCharacterByFlag("dragon_egg_wave_3");
			else if (dwDragonEggIndex == 3)
				SpawnCharacterByFlag("dragon_egg_wave_4");

			ChatPacket(CHAT_TYPE_NOTICE, "One of Balathor's Dragon Eggs is summoning ice cold! Focus your attacks to stop it.");

			SetFlag("egg_wave_failtime", dwCurTime + 1000);
			SetFlag("egg_wave_failtime_count", 0);
			SetFlag("dragon_egg_wave_index", dwDragonEggIndex + 1);
		}

		dwLeftTime = GetFlag("egg_wave_failtime");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			DWORD dwNewCount = 10 - GetFlag("egg_wave_failtime_count");

			if (dwNewCount == 0)
			{
				SetFlag("egg_wave_failtime", 0);
				TakeOff(BALATHOR_TAKE_OFF_FAIL, false);
			}
			else
			{
				SetFlag("egg_wave_failtime", dwCurTime + 1000);
				SetFlag("egg_wave_failtime_count", GetFlag("egg_wave_failtime_count") + 1);
				ChatPacket(CHAT_TYPE_NOTICE, "Concentrate on the Frozen Dragon Egg before it disappears in %d seconds.", dwNewCount);
			}
		}
	}
	else if (m_bStepIndex == 5)
	{
		//Delayed Cinema Dragon Skill
		dwLeftTime = GetFlag("cinema_fake_skill");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			SetFlag("cinema_fake_skill", 0);

			Motion(GetCharacterByFlag("dragon"), 255, BALATHOR_1_SPAWN_ROAR);
		}

		// Ice Crystal Spawn
		dwLeftTime = GetFlag("ice_crystal_spawn");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			SetFlag("ice_crystal_spawn", 0);
			SpawnCharacterByFlag("ice_crystal");
		}

		dwLeftTime = GetFlag("ground_ice_lefttime");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
			SetFlag("ground_ice_lefttime", dwCurTime + config.dwGroundIceDamagePerTime);
			GroundIceSpawn();
		}

		// Flaming Egg Spawn Time
		dwLeftTime = GetFlag("flaming_egg_spawn");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			SetFlag("flaming_egg_spawn", 0);
			SpawnCharacterByFlag("flaming_egg_1");
			SpawnCharacterByFlag("flaming_egg_2");
			ChatPacket(CHAT_TYPE_NOTICE, "A Flaming Dragon Egg has appeared.");
			ChatPacket(CHAT_TYPE_NOTICE, "A Flaming Dragon Egg has appeared.");

			if (GetFlag("ground_ice_lefttime") == 0)
			{
				const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
				SetFlag("ground_ice_lefttime", dwCurTime + config.dwGroundIceDamagePerTime);
			}

			UpdateUI();
		}

		/*
		// Frozen dragon egg raid method
		for (BYTE i = 1; i <= 2; ++i)
		{
			dwLeftTime = GetFlag("frozen_egg"+std::to_string(i)+"_guard_time");
			if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
			{
				LPCHARACTER dragon_egg = GetCharacterByFlag("dragon_egg_" + std::to_string(i));
				if (dragon_egg)
				{
					SetFlag("frozen_egg" + std::to_string(i) + "_guard_time", 0);

					RemoveEffectByVID(dragon_egg->GetVID());
					dragon_egg->SetBlockStatus(true);
					AddEffect(dragon_egg->GetVID(), BALATHOR_EFF_EGG_GUARD, 0, 0, 0, 0.0f, INFINITE_EFFECT_TIME, false);
				}
			}

			dwLeftTime = GetFlag("frozen_egg" + std::to_string(i) + "_flood_time");
			if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
			{
				LPCHARACTER dragon_egg = GetCharacterByFlag("dragon_egg_" + std::to_string(i));
				if (dragon_egg)
				{
					SetFlag("frozen_egg" + std::to_string(i) + "_flood_time", 0);
					RemoveEffectByVID(dragon_egg->GetVID());
					AddEffect(dragon_egg->GetVID(), BALATHOR_EFF_EGG_FLOOD, 0, 0, 0, 0.0f, INFINITE_EFFECT_TIME, false);
				}
			}
		}
		*/

		// Hwatcha Skill Balathor HP Calculate
		
		dwLeftTime = GetFlag("hwatcha_dead_check");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			SetFlag("hwatcha_dead_check", 0);

			LPCHARACTER dragon = GetCharacterByFlag("dragon");
			if (dragon)
			{
				int iPercent = 0;
				if (dragon->GetMaxHP() >= 0)
					iPercent = (dragon->GetHP() * 100) / dragon->GetMaxHP();
				if (!iPercent)
				{
					const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
					if (dwCurTime - m_dwStageTime < config.dwBoss1RequiredTime)
						TakeOff(BALATHOR_TAKE_OFF_FAIL, true);
					else
						TakeOff(BALATHOR_TAKE_OFF_SUCCESS, true);
				}
			}
		}

		dwLeftTime = GetFlag("hwatcha_skill_time");
		if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
		{
			DWORD dwHwatchaPercent = GetFlag("hwatcha_skill_percent");
			if (dwHwatchaPercent == 0)
				dwHwatchaPercent = 1;

			bool bBalathorDead = false;

			LPCHARACTER dragon = GetCharacterByFlag("dragon");
			if (dragon)
			{
				const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

				int iCutHP = (config.bHwatchaDamagePercent / 4) * (dragon->GetMaxHP() / 100);
				dragon->PointChange(POINT_HP, -iCutHP);

				int iPercent = 0;
				if (dragon->GetMaxHP() >= 0)
					iPercent = (dragon->GetHP() * 100) / dragon->GetMaxHP();

				if (!iPercent)
					bBalathorDead = true;
				else
					Motion(dragon, 255, BALATHOR_1_TAKE_DAMAGE);
			}

			dwHwatchaPercent -= 1;

			if (!dwHwatchaPercent || bBalathorDead)
			{
				SetFlag("hwatcha_skill_time", 0);
				SetFlag("hwatcha_skill_percent", 0);
			}
			else
			{
				SetFlag("hwatcha_skill_time", dwCurTime + 500);
				SetFlag("hwatcha_skill_percent", dwHwatchaPercent);
			}
			UpdateUI();
		}
	}
}

void CBalathor::TakeOff(BYTE bTakeOffType, bool is_dead)
{
	if (m_bStepIndex == 5)
	{
		RemoveCharacterByFlag("hwatcha");
		RemoveCharacterByFlag("ice_crystal");
		RemoveCharacterByFlag("flaming_egg_1");
		RemoveCharacterByFlag("flaming_egg_2");
		RemoveCharacterByFlag("dragon_egg_1");
		RemoveCharacterByFlag("dragon_egg_2");
		RemoveCharacterByFlag("dragon_egg_wave");

		RemoveEffectByID(0);

		LPCHARACTER dragon = GetCharacterByFlag("dragon");
		if(dragon)
		{
			SetCharacterByFlag("dragon", 0);
			m_mapFlags.clear();

			if (bTakeOffType == BALATHOR_TAKE_OFF_FAIL)
			{
				dragon->Dead();
				RunCinema(BALATHOR_CINEMA_BOSS_DEAD);

				SetFlag("balathor_finish_fail", get_dword_time() + 3000);

				m_bStepIndex = 88;
			}
			else // BALATHOR_1_TAKE_OFF_SUCCESS
			{

				dragon->Dead();
				RunCinema(BALATHOR_CINEMA_HIDDEN_BOSS_SPAWN);

				SetFlag("regen_group", get_dword_time() + 25000);
				SetAttackSleepTime(25000);
				SpawnCharacterByFlag("dragon_2");
				m_bStepIndex = 6;
			}
		}
		else
		{
			m_mapFlags.clear();
			SetFlag("balathor_finish_fail", get_dword_time() + 3000);
		}
	}
	else if (m_bStepIndex == 6)
	{
		KillRegen();

		LPCHARACTER dragon = GetCharacterByFlag("dragon");
		if (dragon)
		{
			SetCharacterByFlag("dragon", 0);
			m_mapFlags.clear();

			if (bTakeOffType == BALATHOR_TAKE_OFF_FAIL)
			{
				RunCinema(BALATHOR_CINEMA_HIDDEN_BOSS_RUNAWAY);
				Motion(dragon, 255, BALATHOR_2_TAKE_OFF);
				
				m_bStepIndex = 88;
				SetFlag("balathor_finish_vid", dragon->GetVID());
				SetFlag("balathor_finish_vid_time", get_dword_time() + 2000);
				SetFlag("balathor_finish_fail", get_dword_time() + 3000);
			}
			else // BALATHOR_1_TAKE_OFF_SUCCESS
			{
				dragon->Dead();
				RunCinema(BALATHOR_CINEMA_HIDDEN_BOSS_DEAD);
				SetFlag("balathor_finish_success", get_dword_time() + 3000);
				m_bStepIndex = 99;
			}
		}
		else
		{
			m_mapFlags.clear();
			SetFlag("balathor_finish_fail", get_dword_time() + 3000);
		}
	}
}

void CBalathor::Motion(LPCHARACTER mob, BYTE bSkill, WORD wMotion)
{
	if (!mob)
		return;

	if (bSkill != 255)
	{
		mob->SendMovePacket(FUNC_MOB_SKILL, bSkill, mob->GetX(), mob->GetY(), 0, get_dword_time());
	}

	if (wMotion != 255)
	{
		struct packet_motion packet;
		packet.header = HEADER_GC_MOTION;
		packet.motion = wMotion;
		packet.victim_vid = mob->GetVID();

		for (const auto& pid : m_vecPlayers)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(pid);
			LPDESC d = ch ? ch->GetDesc() : NULL;
			if (d)
			{
				packet.vid = ch->GetVID();
				d->Packet(&packet, sizeof(struct packet_motion));
			}
		}		
	}
}

void CBalathor::GetVictims(std::vector<LPCHARACTER>& vecVictims, bool flaming_egg, bool hwatcha)
{
	for (const auto& dwPID : m_vecPlayers)
	{
		LPCHARACTER victim = CHARACTER_MANAGER::Instance().FindByPID(dwPID);
		if (!victim || victim->IsDead())// && ch->HasArmada())
			continue;
		vecVictims.emplace_back(victim);
	}

	if (flaming_egg)
	{
		LPCHARACTER flaming_egg = GetCharacterByFlag("flaming_egg_1");
		if (flaming_egg)
			vecVictims.emplace_back(flaming_egg);

		flaming_egg = GetCharacterByFlag("flaming_egg_2");
		if (flaming_egg)
			vecVictims.emplace_back(flaming_egg);
	}

	if (hwatcha)
	{
		LPCHARACTER hwatcha = GetCharacterByFlag("hwatcha");
		if (hwatcha && !hwatcha->IsDead())
			vecVictims.emplace_back(hwatcha);
	}
}

void CBalathor::UnPoly(LPCHARACTER ch)
{
	if (ch->FindAffect(AFFECT_POLYMORPH))
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "SetBalathorEffect 0");
		ch->SetPolymorph(0);
		ch->RemoveAffect(AFFECT_POLYMORPH);
	}
}

void CBalathor::GroundIceDamage(const TBalathorEffect& eff_info)
{
	for (const auto& dwPID : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(dwPID);
		if (ch)
		{
			float fDist = DISTANCE_APPROX(ch->GetX() - eff_info.lGX, ch->GetY() - eff_info.lGY);
			if (fDist < 700.0f)
			{
				ch->ChatPacket(CHAT_TYPE_COMMAND, "SetBalathorEffect 4");
				const int iDam = ch->GetMaxHP() / 4;
				ch->Damage(ch, iDam, DAMAGE_TYPE_ICE);

				if (!ch->FindAffect(AFFECT_POLYMORPH))
				{
					const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
					ch->AddAffect(AFFECT_POLYMORPH, POINT_POLYMORPH, config.dwIceCrystalVnum, AFF_POLYMORPH, 60, 0, true);
				}
			}
		}
	}
}

bool FSortByDistance(const std::pair<LPCHARACTER, float>& a, const std::pair<LPCHARACTER, float>& b)
{
	return a.second < b.second;
}
void CBalathor::GroundIceSpawn()
{
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	LPCHARACTER dragon = GetCharacterByFlag("dragon");
	if (!dragon)
		return;

	std::vector<std::pair<LPCHARACTER, float>> m_vecNearestPlayer;

	for (const auto& dwPID : m_vecPlayers)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(dwPID);
		if (ch && !ch->IsDead())
			m_vecNearestPlayer.emplace_back(ch, DISTANCE_APPROX(ch->GetX() - dragon->GetX(), ch->GetY() - dragon->GetY()));
	}

	if (m_vecNearestPlayer.empty())
		return;

	if (m_vecNearestPlayer.size() > 1)
		std::stable_sort(m_vecNearestPlayer.begin(), m_vecNearestPlayer.end(), FSortByDistance);

	std::vector<LPCHARACTER> validTargets;

	DWORD dwIceCount = config.dwGroundIceDamageCount;
	if (dwIceCount > m_vecNearestPlayer.size())
		dwIceCount = m_vecNearestPlayer.size();

	for (size_t i = 0; i < m_vecNearestPlayer.size(); ++i)
	{
		LPCHARACTER ch = m_vecNearestPlayer[i].first;

		bool is_valid = true;

		for (auto valid_ch : validTargets)
		{
			float fDist = DISTANCE_APPROX(ch->GetX() - valid_ch->GetX(), ch->GetY() - valid_ch->GetY());
			if (fDist < 700.0f)
			{
				is_valid = false;
				break;
			}
		}

		if (is_valid)
		{
			validTargets.emplace_back(ch);
			if (validTargets.size() == dwIceCount)
				break;
		}
	}

	long lX = 0, lY = 0;
	for (auto ch : validTargets)
	{
		GlobalToLocal(ch->GetX(), ch->GetY(), lX, lY);
		AddEffect(0, BALATHOR_EFF_GROUND_ICE, lX, lY, 50, 0.0f, 4000, false);
	}
}

void CBalathor::ProcessEffect(DWORD dwCurTime)
{
	auto it = m_vecEffects.begin();
	while (it != m_vecEffects.end())
	{
		bool is_deleted = false;
		if (it->dwDuration < dwCurTime || it->bNeedRemove)
		{
			ChatPacket(CHAT_TYPE_COMMAND, "BalathorEffectRemove %u", it->dwID);
			it = m_vecEffects.erase(it);
			continue;
		}

		TBalathorEffect& eff_info = *it;
		if (eff_info.bEffIndex == BALATHOR_EFF_EGG_ARROW)
		{
			for (BYTE i = 1; i <= 2; ++i)
			{
				std::string number_str(std::to_string(i));

				LPCHARACTER flaming_egg = GetCharacterByFlag("flaming_egg_" + number_str);
				if (!flaming_egg)
					continue;
				
				float fDist = DISTANCE_APPROX(eff_info.lGX - flaming_egg->GetX(), eff_info.lGY - flaming_egg->GetY());
				if (fDist > 200.0f)
					continue;

				LPCHARACTER dragon_egg = SpawnCharacterByFlag("dragon_egg_" + number_str);
				if (!dragon_egg)
					continue;

				it->bNeedRemove = true;
				dragon_egg->SetBlockStatus(true);

				M2_DESTROY_CHARACTER(flaming_egg);
				SetCharacterByFlag("flaming_egg_" + number_str, 0);

				if (GetCharacterVIDByFlag("flaming_egg_1") == 0 && GetCharacterVIDByFlag("flaming_egg_2") == 0)
				{
					if(SpawnCharacterByFlag("hwatcha"))
						UpdateUI();
				}

				AddEffect(dragon_egg->GetVID(), BALATHOR_EFF_EGG_MOOJUK, 0, 0, 0, 0.0f, INFINITE_EFFECT_TIME, false);
				return;
			}
		}
		else if (eff_info.bEffIndex == BALATHOR_EFF_GROUND_ICE)
		{
			DWORD dwLeftTime = eff_info.dwDuration - dwCurTime;
			if (dwLeftTime <= 2000 && !eff_info.bDamage)
			{
				GroundIceDamage(eff_info);
				eff_info.bDamage = true;
			}
		}
		else if (eff_info.bEffIndex == BALATHOR_EFF_GROUND_DROP)
		{
			DWORD dwLeftTime = eff_info.dwDuration - dwCurTime;
			if (dwLeftTime <= 2500 && !eff_info.bDamage)
			{
				GroundDropDamage(eff_info);
				eff_info.bDamage = true;
			}
		}
		else if (eff_info.bEffIndex == BALATHOR_EFF_AREA)
		{
			const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

			DWORD dwLeftTime = eff_info.dwDuration - dwCurTime;

			LPCHARACTER dragon = GetCharacterByFlag("dragon");
			if (dragon)
			{
				if (dragon->GetRaceNum() == config.dwBossVnum1)
				{
					if (eff_info.bStage == 0)
					{
						Motion(dragon, 255, BALATHOR_1_TAKE_OFF);
						eff_info.bStage = 1;
					}
					else if (eff_info.bStage == 1 && dwLeftTime <= 2700)
					{
						dragon->SetRotation(4 * 45);
						dragon->Show(dragon->GetMapIndex(), eff_info.lGX, eff_info.lGY, 0, false);
						Motion(dragon, BALATHOR_1_AREA, 255);
						eff_info.bStage = 2;
					}
					else if (eff_info.bStage == 2 && dwLeftTime <= 1700)
					{
						AreaSkillDamage(dragon, eff_info);
						eff_info.bStage = 3;
					}
					else if (eff_info.bStage == 3 && dwLeftTime <= 1300)
					{
						dragon->SetRotation(0);
						dragon->Show(dragon->GetMapIndex(), config.boss_1_pos.lGX, config.boss_1_pos.lGY, 0, false);
						Motion(dragon, BALATHOR_1_LAND, 255);
						eff_info.bStage = 4;
					}
				}
				else
				{
					if (eff_info.bStage == 0)
					{
						Motion(dragon, 255, BALATHOR_2_TAKE_OFF);
						eff_info.bStage = 1;
					}
					else if (eff_info.bStage == 1 && dwLeftTime <= 2700)
					{
						dragon->SetRotation(4 * 45);
						dragon->Show(dragon->GetMapIndex(), eff_info.lGX, eff_info.lGY, 0, false);
						Motion(dragon, BALATHOR_2_AREA, 255);
						eff_info.bStage = 2;
					}
					else if (eff_info.bStage == 2 && dwLeftTime <= 1800)
					{
						AreaSkillDamage(dragon, eff_info);
						eff_info.bStage = 3;
					}
					else if (eff_info.bStage == 3 && dwLeftTime <= 1400)
					{
						dragon->SetRotation(4 * 45);
						dragon->Show(dragon->GetMapIndex(), config.boss_2_pos.lGX, config.boss_2_pos.lGY, 0, false);
						Motion(dragon, 255, BALATHOR_2_LAND);
						eff_info.bStage = 4;
					}
				}
			}
		}
		++it;
	}
}

bool FSortByCount(const SBalathorPosition& a, const SBalathorPosition& b)
{
	return a.bDirection > b.bDirection;
}

void CBalathor::AreaSkillMake()
{
	if (m_vecPlayers.empty())
		return;

	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(m_dwMapIndex);
	if (!pkSectreeMap)
		return;
	int iBaseX = pkSectreeMap->m_setting.iBaseX;
	int iBaseY = pkSectreeMap->m_setting.iBaseY;

	std::vector<SBalathorPosition> vecAreaPositions = {
		{225, 255, (225 * 100) + iBaseX, (255 * 100) + iBaseY, 0},
		{255, 255, (255 * 100) + iBaseX, (255 * 100) + iBaseY, 0},
		{285, 255, (285 * 100) + iBaseX, (255 * 100) + iBaseY, 0}
	};

	for (auto& position : vecAreaPositions)
	{
		long lx1 = position.lGX - (15 * 100);
		long lx2 = lx1 + (30 * 100);

		long ly1 = position.lGY - (80 * 100);
		long ly2 = ly1 + (135 * 100);

		std::vector<LPCHARACTER> vecVictims;
		GetVictims(vecVictims, false, true);

		for (auto victim : vecVictims)
		{
			long lX = victim->GetX();
			long lY = victim->GetY();
			if (lX >= lx1 && lX <= lx2 && lY >= ly1 && lY <= ly2)
				position.bDirection += 1;
		}
	}

	std::stable_sort(vecAreaPositions.begin(), vecAreaPositions.end(), FSortByCount);

	const SBalathorPosition& pos_info = vecAreaPositions[0];
	if (pos_info.bDirection > 0)
		AddEffect(0, BALATHOR_EFF_AREA, pos_info.lX, pos_info.lY, 0, 0.0f, 4000, false);
}

void CBalathor::AreaSkillDamage(LPCHARACTER dragon, const TBalathorEffect& eff_info)
{
	long lx1 = eff_info.lGX - (15 * 100);
	long lx2 = lx1 + (30 * 100);

	long ly1 = eff_info.lGY - (80 * 100);
	long ly2 = ly1 + (135 * 100);

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	std::vector<LPCHARACTER> vecVictims;
	GetVictims(vecVictims, false, true);
	for (auto victim : vecVictims)
	{
		long lX = victim->GetX();
		long lY = victim->GetY();
		if (lX >= lx1 && lX <= lx2 && lY >= ly1 && lY <= ly2)
		{
			if (victim->GetRaceNum() == config.dwHwachaVnum)
			{
				const int iDam = victim->GetMaxHP() / 5;
				victim->Damage(victim, iDam, DAMAGE_TYPE_ICE);
			}
			else
			{
				victim->Dead(dragon);
			}
			
			
		}
	}
}

void CBalathor::GroundDropMake(LPCHARACTER dragon)
{
	PIXEL_POSITION center = dragon->GetXYZ();
	float baseRotation = dragon->GetRotation();

	const int rows = 3;
	const int perRow = 5;

	long lX = 0, lY = 0;
	const float rowSpacing = 2000.0f;
	const float sideSpacing = 1000.0f;

	for (int r = 1; r <= rows; ++r)
	{
		for (int i = 0; i < perRow; ++i)
		{
			int sideIndex = i - (perRow / 2); // -2 -1 0 +1 +2

			float fxForward = 0.0f, fyForward = 0.0f;
			float fxSide = 0.0f, fySide = 0.0f;

			GetDeltaByDegree(baseRotation, rowSpacing * r, &fxForward, &fyForward);

			GetDeltaByDegree(baseRotation + 90.0f, sideSpacing * sideIndex, &fxSide, &fySide);

			long posX = center.x + (long)(fxForward + fxSide);
			long posY = center.y + (long)(fyForward + fySide);

			GlobalToLocal(posX, posY, lX, lY);
			AddEffect(0, BALATHOR_EFF_GROUND_DROP, lX, lY, 0, 0.0f, 4000, false);
		}
	}
}
void CBalathor::GroundDropDamage(const TBalathorEffect& eff_info)
{
	std::vector<LPCHARACTER> vecVictims;
	GetVictims(vecVictims, false, false);

	for (auto victim : vecVictims)
	{
		float fDist = DISTANCE_APPROX(eff_info.lGX - victim->GetX(), eff_info.lGY - victim->GetY());
		if (fDist < 250.0f)
		{
			const int iDam = victim->GetMaxHP() / 5;
			victim->Damage(victim, iDam, DAMAGE_TYPE_ICE);
		}
	}
}

void CBalathor::CircleAttackMake(DWORD dwCurTime)
{
	if (m_vecPlayers.empty())
		return;

	LPCHARACTER dragon = GetCharacterByFlag("dragon");
	if (!dragon)
		return;

	DWORD dwMotionIndex = 255;
	DWORD dwDistance = 2500;
	DWORD dwPoly = 0;
	DWORD dwDamageCooldown = 1000;
	DWORD dwCrush = 0;

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	if (dragon->GetRaceNum() == config.dwBossVnum1)
	{
		int iAnimationType = number(0, 2);
		if (iAnimationType == 0)
		{
			dwMotionIndex = BALATHOR_1_RIGHT_CIRCLE;
			dwDistance = 2500;
			dwCrush = 1;
		}
		else if (iAnimationType == 1)
		{
			dwMotionIndex = BALATHOR_1_LEFT_CIRCLE;
			dwDistance = 2500;
			dwCrush = 1;
		}
		else if (iAnimationType == 2)
		{
			dwMotionIndex = BALATHOR_1_BREATH;
			dwDistance = 2500;
			dwPoly = 1;
		}

		if (number(0, 1) == 0)
		{
			GroundDropMake(dragon);
		}
	}
	else
	{
		int iAnimationType = number(0, 1);
		
		if (iAnimationType == 0)
		{
			dwMotionIndex = BALATHOR_2_FLY_BREATH;
			dwDistance = 2500;
		}
		else if (iAnimationType == 1)
		{
			dwMotionIndex = BALATHOR_2_BREATH;
			dwDistance = 1000;
			dwPoly = 1;
		}
	}

	Motion(dragon, dwMotionIndex, 255);
	SetFlag("circle_attack_motion", dwMotionIndex);
	SetFlag("circle_attack_distance", dwDistance);
	SetFlag("circle_attack_poly", dwPoly);
	SetFlag("circle_attack_crush", dwCrush);
	SetFlag("circle_attack_damage", dwCurTime + dwDamageCooldown);
}

void CBalathor::CircleAttackDamage()
{
	if (m_vecPlayers.empty())
		return;

	LPCHARACTER dragon = GetCharacterByFlag("dragon");
	if (!dragon)
		return;

	DWORD dwMotionIndex = GetFlag("circle_attack_motion");
	DWORD dwDistance = GetFlag("circle_attack_distance");
	DWORD dwPoly = GetFlag("circle_attack_poly");
	DWORD dwCrush = GetFlag("circle_attack_crush");

	PIXEL_POSITION center = dragon->GetXYZ();
	float baseRotation = dragon->GetRotation();

	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
	std::vector<LPCHARACTER> vecVictims;
	GetVictims(vecVictims, true, true);

	for (auto victim : vecVictims)
	{
		PIXEL_POSITION victim_center = victim->GetXYZ();

		int dx = victim_center.x - center.x;
		int dy = victim_center.y - center.y;

		float playerDistance = DISTANCE_APPROX(dx, dy);

		if (playerDistance > dwDistance)
			continue;

		float angleToPlayer = GetDegreeFromPosition(dx, dy);

		float angleDiff = fabs(angleToPlayer - baseRotation);

		if (angleDiff > 180.0f)
			angleDiff = 360.0f - angleDiff;

		if (angleDiff <= 60.0f)
		{
			if (dwCrush != 0 && victim->GetRaceNum() == config.dwFlamingEggVnum)
			{
				float fCrushSlidingLength = victim->IsPC() ? 200 : 400;
				float fx, fy;
				float degree = GetDegreeFromPositionXY(center.x, center.y, victim_center.x, victim_center.y);
				GetDeltaByDegree(degree, fCrushSlidingLength, &fx, &fy);
				long tx = (long)(victim_center.x + fx);
				long ty = (long)(victim_center.y + fy);

				while (victim->GetSectree()->GetAttribute(tx, ty) & (ATTR_BLOCK | ATTR_OBJECT) && fCrushSlidingLength > 0)
				{
					if (fCrushSlidingLength >= 10)
						fCrushSlidingLength -= 10;
					else
						fCrushSlidingLength = 0;
					GetDeltaByDegree(degree, fCrushSlidingLength, &fx, &fy);
					tx = (long)(victim->GetX() + fx);
					ty = (long)(victim->GetY() + fy);
				}
				victim->Sync(tx, ty);
				victim->Goto(tx, ty);
				victim->CalculateMoveDuration();
				victim->SyncPacket();
			}

			int iDamage = 10 * (victim->GetMaxHP() / 100);
			victim->Damage(dragon, iDamage, DAMAGE_TYPE_MAGIC);
		}
	}
}

void CBalathor::SetAttackSleepTime(DWORD dwSleepTime)
{
	SetFlag("attack_sleep", get_dword_time() + dwSleepTime);
}

void CBalathor::AttackProcess(DWORD dwCurTime)
{
	DWORD dwLeftTime = GetFlag("circle_attack_damage");
	if (dwLeftTime != 0 && dwLeftTime < dwCurTime)
	{
		SetFlag("circle_attack_damage", 0);
		CircleAttackDamage();
	}

	DWORD dwRaidLeftTime = GetFlag("raid_attack");
	if (dwRaidLeftTime != 0 && dwRaidLeftTime < dwCurTime)
	{
		SetFlag("raid_attack", 0);

		AreaSkillMake();
		SetAttackSleepTime(4500);
	}

	dwLeftTime = GetFlag("attack_sleep");
	if (dwLeftTime != 0)
	{
		if (dwLeftTime > dwCurTime)
			return;
		SetFlag("attack_sleep", 0);
	}

	DWORD dwCircleAttackStatus = GetFlag("circle_attack_status");
	if (dwCircleAttackStatus != 0 && dwCircleAttackStatus < dwCurTime)
	{
		SetFlag("circle_attack_status", 0);
		CircleAttackMake(dwCurTime);
		SetAttackSleepTime(3000);
	}

	if (dwCircleAttackStatus == 0 && dwRaidLeftTime == 0)
	{
		const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
		SetFlag("circle_attack_status", dwCurTime + config.dwBossSkillPerTime);
	}
}

BYTE CBalathor::ClaimReward(LPCHARACTER ch)
{
	if (std::find(m_vecClaimedRewardsPIDs.begin(), m_vecClaimedRewardsPIDs.end(), ch->GetPlayerID()) != m_vecClaimedRewardsPIDs.end())
		return 0;
	else if (m_bStepIndex != 88 && m_bStepIndex != 99)
		return 1;
	const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();

	if (m_bStepIndex == 88)
	{
		for (BYTE i = 0; i < BALATHOR_MAX_REWARD_COUNT; ++i)
		{
			const SBalathorReward& reward = config.fail_rewards[i];
			if (reward.dwVnum != 0)
				ch->AutoGiveItem(reward.dwVnum, reward.dwCount);
		}
	}
	else if (m_bStepIndex == 99)
	{
		for (BYTE i = 0; i < BALATHOR_MAX_REWARD_COUNT; ++i)
		{
			const SBalathorReward& reward = config.success_rewards[i];
			if (reward.dwVnum != 0)
				ch->AutoGiveItem(reward.dwVnum, reward.dwCount);
		}
	}
	m_vecClaimedRewardsPIDs.emplace_back(ch->GetPlayerID());
	return 99;
}
#endif
