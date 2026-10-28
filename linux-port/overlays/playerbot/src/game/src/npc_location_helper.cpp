// MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC (Autor: Best Studio; ported to MT2009 Plus, see npc_location_helper.h).
//
// Changes against the package:
//  - the files: locale/poland/npc_location_helper/npc_location_helper.txt and <map_dir>_point.txt there (our maps,
//    tools/npcloc/gen_npcloc_data.py); no singleton object in main.cpp - the manager is made and the files are read
//    on first use;
//  - the teleport goes to the map's GLOBAL position (map base + the point), next to the NPC on a cell the map lets
//    you walk on when this core hosts the map (the generator checked every point against server_attr);
//  - "some core of this channel hosts the map" (CMapLocation) instead of map_allow_find (only this core's maps);
//  - the same checks as the teleport map under TAB (quest mapa_tab) and the saved positions: not dead, not riding,
//    not in a duel or arena, no trade / shop / storage / cube open (IsBusy, CanWarp), not out of a dungeon instance,
//    the wedding, the duel and OX maps, empire war, the GM maps or the guild war arena while the guild is at war;
//    Dolina Cyklopow / Pustkowie Faraona only while the Arezzo module is on;
//  - to another map only where nobody pays or shows anything at the entrance (IsOpenTargetMap - the kingdoms, the
//    neutral lands, the fields of Yohara and the teleport ring's places); on the map itself every NPC; never to a
//    portal (icon 1 - landing beside it would take the player through);
//  - the STATUS packet carries the character's map index (the client has none of its own);
//  - the bound stone (79669) is spent before the tradeable one (79668);
//  - MT2009_PLUS_NPC_LOCATION_HELPER_V2 (the owner, 28 October 2026 - "as the wiki"): every character has the
//    improved map from the start - no quest flag, the Lokalizator NPC item (79667) is not needed any more (using
//    one only says so and keeps it); the wiki's checks on top of ours: the target map's level (min_level of
//    npc_location_helper.txt = our gates: Port 90, Smocze Ziemie 90, Ochao 95, Grota 75, Yohara 120 ...), the
//    Champion level 1 for the lands of Yohara (categories 6 / 7, as the wiki and the Teleportation Ring's Dongan)
//    and no NPC of an enemy kingdom (the map's empire);
//  - a map piece unlocks nothing yet: a map with show_atlas 2 is a target only with the quest flag
//    npc_location_helper.unlocked_map.<index> (none of our maps has 2 - the owner decides).
#include "stdafx.h"
#include <algorithm>
#include <fstream>
#include <sstream>
#include <ctime>
#include "../../common/stl.h"
#include "../../common/tables.h"
#include "char.h"
#include "item.h"
#include "desc.h"
#include "guild.h"
#include "pvp.h"
#include "questmanager.h"
#include "questpc.h"
#include "locale_service.h"
#include "sectree_manager.h"
#include "map_location.h"
#include "npc_location_helper.h"

namespace
{
	std::vector<std::string> NlhSplit(const std::string& line)
	{
		std::istringstream iss(line);
		std::vector<std::string> out;
		std::string token;
		while (iss >> token)
			out.push_back(token);
		return out;
	}

	bool NlhIsCommentOrEmpty(const std::string& line)
	{
		for (size_t i = 0; i < line.size(); ++i)
		{
			if (line[i] == '#')
				return true;
			if (!isspace(static_cast<unsigned char>(line[i])))
				return false;
		}
		return true;
	}

	std::string NlhFlag(const char* name)
	{
		return std::string("npc_location_helper.") + name;
	}

	std::string NlhUnlockedMapFlag(long mapIndex)
	{
		char buf[64];
		snprintf(buf, sizeof(buf), "unlocked_map.%ld", mapIndex);
		return NlhFlag(buf);
	}

	quest::PC* NlhPC(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC())
			return NULL;
		return quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
	}
}

CNpcLocationHelperManager& CNpcLocationHelperManager::Instance()
{
	static CNpcLocationHelperManager s_instance;
	return s_instance;
}

CNpcLocationHelperManager::CNpcLocationHelperManager()
	: m_bLoaded(false), m_bLoadTried(false)
{
}

bool CNpcLocationHelperManager::Load()
{
	if (m_bLoadTried)
		return m_bLoaded;
	m_bLoadTried = true;

	const std::string base = LocaleService_GetBasePath() + "/npc_location_helper/";
	if (!LoadMapInfo(base + "npc_location_helper.txt"))
	{
		sys_err("NPC_LOCATION_HELPER: cannot load %snpc_location_helper.txt - the teleport to NPCs is off", base.c_str());
		return false;
	}

	for (std::map<long, SMapInfo>::const_iterator it = m_mapInfo.begin(); it != m_mapInfo.end(); ++it)
		LoadPointFile(base + it->second.mapDir + "_point.txt", it->second);

	m_bLoaded = true;
	sys_log(0, "NPC_LOCATION_HELPER: %u maps, %u npc points", static_cast<unsigned>(m_mapInfo.size()), static_cast<unsigned>(m_vecNpcInfo.size()));
	return true;
}

bool CNpcLocationHelperManager::LoadMapInfo(const std::string& filename)
{
	std::ifstream file(filename.c_str());
	if (!file.is_open())
		return false;

	m_mapInfo.clear();
	std::string line;
	bool inMapInfo = false;
	while (std::getline(file, line))
	{
		if (!line.empty() && line[line.size() - 1] == '\r')
			line.erase(line.size() - 1);

		if (!inMapInfo)
		{
			if (line.find("Group") != std::string::npos && line.find("MapInfo") != std::string::npos)
				inMapInfo = true;
			continue;
		}
		if (NlhIsCommentOrEmpty(line) || line.find('{') != std::string::npos)
			continue;
		if (line.find('}') != std::string::npos)
			break;

		const std::vector<std::string> tokens = NlhSplit(line);
		if (tokens.size() < 13)
			continue;

		SMapInfo info;
		info.mapIndex = atol(tokens[0].c_str());
		info.mapDir = tokens[2];
		info.category = atoi(tokens[3].c_str());
		info.minLevel = atoi(tokens[4].c_str());
		info.minConquerorLevel = atoi(tokens[5].c_str());
		info.empire = atoi(tokens[8].c_str());
		info.showAtlas = atoi(tokens[9].c_str());
		info.showNpcList = atoi(tokens[10].c_str());
		info.warpNeedYang = atoll(tokens[11].c_str());
		info.warpNeedItemVnum = 0;
		info.warpNeedItemCount = 0;

		const size_t commaPos = tokens[12].find(',');
		if (commaPos != std::string::npos)
		{
			info.warpNeedItemVnum = static_cast<DWORD>(atol(tokens[12].substr(0, commaPos).c_str()));
			info.warpNeedItemCount = atoi(tokens[12].substr(commaPos + 1).c_str());
		}

		// the client's map name - "season2/metin2_map_skipia_dungeon_01" keeps its point file in a sub folder
		if (info.mapIndex <= 0 || info.mapIndex >= 10000 || info.mapDir.empty() || info.mapDir.find("..") != std::string::npos
			|| info.mapDir[0] == '/')
			continue;

		m_mapInfo[info.mapIndex] = info;
	}

	return !m_mapInfo.empty();
}

void CNpcLocationHelperManager::LoadPointFile(const std::string& filename, const SMapInfo& mapInfo)
{
	std::ifstream file(filename.c_str());
	if (!file.is_open())
		return;

	std::string line;
	while (std::getline(file, line))
	{
		if (NlhIsCommentOrEmpty(line))
			continue;

		// index  x  y  npc_vnum  enable_helper  icon  (x, y: the map's local position in cm)
		const std::vector<std::string> tokens = NlhSplit(line);
		if (tokens.size() < 6)
			continue;
		if (atoi(tokens[4].c_str()) == 0)
			continue;

		SNpcInfo npc;
		npc.mapIndex = mapInfo.mapIndex;
		npc.x = atol(tokens[1].c_str()) / 100;
		npc.y = atol(tokens[2].c_str()) / 100;
		npc.vnum = static_cast<DWORD>(atol(tokens[3].c_str()));
		npc.icon = atoi(tokens[5].c_str());
		if (npc.x <= 0 || npc.y <= 0 || npc.vnum == 0)
			continue;
		m_vecNpcInfo.push_back(npc);
	}
}

const CNpcLocationHelperManager::SMapInfo* CNpcLocationHelperManager::FindMap(long mapIndex) const
{
	std::map<long, SMapInfo>::const_iterator it = m_mapInfo.find(mapIndex);
	return it == m_mapInfo.end() ? NULL : &it->second;
}

bool CNpcLocationHelperManager::FindNpc(long mapIndex, DWORD vnum, long x, long y, SNpcInfo& out) const
{
	for (std::vector<SNpcInfo>::const_iterator it = m_vecNpcInfo.begin(); it != m_vecNpcInfo.end(); ++it)
	{
		const SNpcInfo& npc = *it;
		if (npc.mapIndex != mapIndex || npc.vnum != vnum)
			continue;
		if (labs(npc.x - x) > 3 || labs(npc.y - y) > 3)
			continue;

		out = npc;
		return true;
	}

	return false;
}

bool CNpcLocationHelperManager::IsActive(CHARACTER* ch) const
{
	// MT2009_PLUS_NPC_LOCATION_HELPER_V2: on for every character (the old quest flag "active" is not read)
	return ch && ch->IsPC();
}

bool CNpcLocationHelperManager::UseActivator(CHARACTER* ch, CItem* item)
{
	if (!ch || !item || !ch->GetDesc())
		return false;

	// MT2009_PLUS_NPC_LOCATION_HELPER_V2: every character has the improved map - the item is not needed and stays
	// "Lokalizator NPC jest wlaczony dla kazdej postaci - ten przedmiot nie jest juz potrzebny."
	ch->ChatPacket(CHAT_TYPE_INFO, "Lokalizator NPC jest w\xb3\xb9" "czony dla ka\xbfdej postaci - ten przedmiot nie jest ju\xbf potrzebny.");
	SendStatus(ch);
	return false;
}

DWORD CNpcLocationHelperManager::GetCooldownRemain(CHARACTER* ch) const
{
	quest::PC* pc = NlhPC(ch);
	if (!pc)
		return 0;

	const int lastTime = pc->GetFlag(NlhFlag("last_warp_time"));
	if (lastTime <= 0)
		return 0;
	const int elapsed = static_cast<int>(time(0)) - lastTime;
	if (elapsed < 0)
		return 0;
	return elapsed >= WARP_COOLDOWN_SEC ? 0 : WARP_COOLDOWN_SEC - elapsed;
}

void CNpcLocationHelperManager::SendStatus(CHARACTER* ch) const
{
	SendPacket(ch, NPC_LOCATION_HELPER_GC_STATUS, RESULT_OK);
}

void CNpcLocationHelperManager::SendPacket(CHARACTER* ch, BYTE subheader, BYTE result, const SNpcInfo* npc) const
{
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;

	// only to a client that sent this packet on this connection: an older exe does not know header 196 and would
	// drop the connection on it (e.g. when the activator is used from such a client)
	if (m_setClientHandles.find(ch->GetDesc()->GetHandle()) == m_setClientHandles.end())
		return;

	TPacketGCNPCLocationHelper packet;
	memset(&packet, 0, sizeof(packet));
	packet.header = HEADER_GC_NPC_LOCATION_HELPER;
	packet.subheader = subheader;
	packet.result = result;
	packet.active = IsActive(ch) ? 1 : 0;
	packet.cooldownRemain = GetCooldownRemain(ch);
	if (npc)
	{
		packet.mapIndex = npc->mapIndex;
		packet.vnum = npc->vnum;
		packet.x = npc->x;
		packet.y = npc->y;
	}
	else
	{
		// the client has no map index of its own: STATUS tells it where the character is (an instance: its base map)
		const long mapIndex = ch->GetMapIndex();
		packet.mapIndex = mapIndex >= 10000 ? mapIndex / 10000 : mapIndex;
	}
	ch->GetDesc()->Packet(&packet, sizeof(packet));
}

int CNpcLocationHelperManager::GetStoneCost(long fromMapIndex, long toMapIndex) const
{
	if (fromMapIndex == toMapIndex)
		return 1;

	return (fromMapIndex / 10 == toMapIndex / 10) ? 2 : 3;
}

void CNpcLocationHelperManager::ConsumeWarpStones(CHARACTER* ch, int count) const
{
	if (!ch || count <= 0)
		return;

	int remain = count;
	const int bound = static_cast<int>(ch->CountSpecifyItem(ITEM_WARP_STONE));
	const int takeBound = std::min(bound, remain);
	if (takeBound > 0)
	{
		ch->RemoveSpecifyItem(ITEM_WARP_STONE, takeBound);
		remain -= takeBound;
	}

	if (remain > 0)
		ch->RemoveSpecifyItem(ITEM_WARP_STONE_PLUS, remain);
}

bool CNpcLocationHelperManager::IsOpenTargetMap(const SMapInfo& mapInfo) const
{
	// Our maps keep their own entrances: Krolestwo Zywiolow (378-381) costs 50 000 000 Yang (yohara_mapy3), Tajemnicza
	// Instancja (396) a ticket each time, Plaskowyz Iluzji (397) the Ksiazka Przebudzenia, Grota Wygnancow (72) level 75
	// + Krwisty Kamien and 73 only from 72 (teleport_ring), the dungeons of Yohara / Erebus / Sung Ma their quests. So
	// from another map the teleport goes only to the kingdoms (category 1), the neutral lands (2) and the fields of
	// Yohara (6), and from the rest to what the teleport ring already offers (Loch Pajakow 1, Swiatynia Ochao, the four
	// lands of the Evil Dragon) and the Port (368). On the target map itself every NPC is a target.
	switch (mapInfo.category)
	{
		case 1: case 2:	// no Yohara (category 6) from another map - the owner, 28 Oct 2026
			return true;
	}
	switch (mapInfo.mapIndex)
	{
		case 104: case 209: case 301: case 302: case 303: case 304: case 368:
			return true;
	}
	return false;
}

bool CNpcLocationHelperManager::IsBlockedSourceMap(CHARACTER* ch, long mapIndex) const
{
	// as mapa_tab.blocked_from: wedding, duel, OX, empire war, the GM maps; the guild war arena while at war
	switch (mapIndex)
	{
		case 81: case 112: case 113: case 181: case 182: case 183: case 200: case 250:
			return true;
		case 110: case 111:
			return ch->GetGuild() && ch->GetGuild()->UnderAnyWar() != 0;
	}
	return false;
}

void CNpcLocationHelperManager::HandlePacket(CHARACTER* ch, const TPacketCGNPCLocationHelper& packet)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;

	// this connection's client knows the packet (it asks for the status when it enters the game)
	if (m_setClientHandles.size() > 100000)
		m_setClientHandles.clear();
	m_setClientHandles.insert(ch->GetDesc()->GetHandle());

	Load();

	switch (packet.subheader)
	{
		case NPC_LOCATION_HELPER_CG_REQUEST_STATUS:
		case NPC_LOCATION_HELPER_CG_USE_TICKET:
			SendStatus(ch);
			break;
		case NPC_LOCATION_HELPER_CG_WARP_TO_NPC:
			WarpToNPC(ch, packet);
			break;
		case NPC_LOCATION_HELPER_CG_REQUEST_GUILD_LAND:
			SendPacket(ch, NPC_LOCATION_HELPER_GC_GUILD_LAND, RESULT_OK);
			break;
		default:
			SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
			break;
	}
}

void CNpcLocationHelperManager::WarpToNPC(CHARACTER* ch, const TPacketCGNPCLocationHelper& packet)
{
	const long curMap = ch->GetMapIndex();
	if (!m_bLoaded || ch->IsDead() || ch->IsRiding() || ch->IsPolymorphed() || ch->IsWarping() || !ch->CanWarp()
		|| ch->IsBusy() || ch->GetArena() || CPVPManager::instance().IsFighting(ch->GetPlayerID())
		|| curMap >= 10000 || IsBlockedSourceMap(ch, curMap))
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_CANNOT_USE);
		return;
	}

	if (GetCooldownRemain(ch) > 0)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_COOLDOWN);
		return;
	}

	const SMapInfo* mapInfo = FindMap(packet.mapIndex);
	if (!mapInfo || mapInfo->showAtlas == 0 || mapInfo->showNpcList == 0)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	// Dolina Cyklopow (360) / Pustkowie Faraona (361): only while the Arezzo module is on (as mapa_tab)
	if ((packet.mapIndex == 360 || packet.mapIndex == 361) && quest::CQuestManager::instance().GetEventFlag("mt2009_arezzo_closed") != 0)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	quest::PC* pc = NlhPC(ch);
	if (mapInfo->showAtlas == 2 && (!pc || pc->GetFlag(NlhUnlockedMapFlag(packet.mapIndex)) <= 0))
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	SNpcInfo npc;
	if (!FindNpc(packet.mapIndex, packet.vnum, packet.x, packet.y, npc))
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	// a portal: landing next to it would take the player through it - no teleport to a portal
	if (npc.icon == ROLE_PORTAL)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	// another map only when it is open ground anyone walks into (no fee, ticket or quest at its entrance)
	if (packet.mapIndex != curMap && !IsOpenTargetMap(*mapInfo))
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	// MT2009_PLUS_NPC_LOCATION_HELPER_V2 (the wiki): below the target map's level - and the lands of Yohara
	// (categories 6 / 7) only for a Champion (Poziom Czempiona 1+)
	const int minConquerorLevel = (mapInfo->category == 6 || mapInfo->category == 7)
		? std::max(1, mapInfo->minConquerorLevel) : mapInfo->minConquerorLevel;
	if (ch->GetLevel() < mapInfo->minLevel || ch->GetConquerorLevel() < minConquerorLevel)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_LEVEL_LIMIT);
		return;
	}

	// the wiki: no NPC of an enemy kingdom (the kingdom maps and their guild lands carry their empire)
	if (mapInfo->empire != 0 && mapInfo->empire != ch->GetEmpire())
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_EMPIRE_LIMIT);
		return;
	}

	// the target's global position, next to the NPC on walkable ground when this core hosts the map
	PIXEL_POSITION base;
	if (!SECTREE_MANAGER::instance().GetMapBasePositionByMapIndex(npc.mapIndex, base))
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}
	long destX = base.x + npc.x * 100;
	long destY = base.y + npc.y * 100;
	if (SECTREE_MANAGER::instance().GetMap(npc.mapIndex))
	{
		static const int s_aOffset[][2] = { { 200, 0 }, { 0, 200 }, { -200, 0 }, { 0, -200 }, { 150, 150 }, { -150, 150 }, { 150, -150 }, { -150, -150 }, { 0, 0 } };
		for (size_t i = 0; i < sizeof(s_aOffset) / sizeof(s_aOffset[0]); ++i)
		{
			const long tx = destX + s_aOffset[i][0];
			const long ty = destY + s_aOffset[i][1];
			if (SECTREE_MANAGER::instance().IsMovablePosition(npc.mapIndex, tx, ty))
			{
				destX = tx;
				destY = ty;
				break;
			}
		}
	}

	long lLocMapIndex = 0, lAddr = 0;
	WORD wPort = 0;
	if (!CMapLocation::instance().Get(destX, destY, lLocMapIndex, lAddr, wPort) || lLocMapIndex != npc.mapIndex)
	{
		// no core of this channel hosts the map (e.g. 3 Loch Pajakow switched off)
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_INVALID_TARGET);
		return;
	}

	if (mapInfo->warpNeedYang > 0 && static_cast<long long>(ch->GetGold()) < mapInfo->warpNeedYang)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_NEED_YANG);
		return;
	}

	if (mapInfo->warpNeedItemVnum > 0 && static_cast<int>(ch->CountSpecifyItem(mapInfo->warpNeedItemVnum)) < mapInfo->warpNeedItemCount)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_NEED_ITEM);
		return;
	}

	const int stoneCost = GetStoneCost(curMap, packet.mapIndex);
	if (static_cast<int>(ch->CountSpecifyItem(ITEM_WARP_STONE) + ch->CountSpecifyItem(ITEM_WARP_STONE_PLUS)) < stoneCost)
	{
		SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_NEED_ITEM);
		return;
	}

	if (mapInfo->warpNeedYang > 0)
		ch->PointChange(POINT_GOLD, -static_cast<int>(mapInfo->warpNeedYang));
	if (mapInfo->warpNeedItemVnum > 0 && mapInfo->warpNeedItemCount > 0)
		ch->RemoveSpecifyItem(mapInfo->warpNeedItemVnum, mapInfo->warpNeedItemCount);
	ConsumeWarpStones(ch, stoneCost);

	if (pc)
		pc->SetFlag(NlhFlag("last_warp_time"), static_cast<int>(time(0)));

	sys_log(0, "NPC_LOCATION_HELPER: %s (%u) map %ld -> map %ld npc %u (%ld, %ld), %d stone(s)",
		ch->GetName(), ch->GetPlayerID(), curMap, npc.mapIndex, npc.vnum, destX, destY, stoneCost);
	SendPacket(ch, NPC_LOCATION_HELPER_GC_WARP_RESULT, RESULT_OK, &npc);
	ch->WarpSet(destX, destY);
}

void NpcLocationHelperPacket(CHARACTER* ch, const char* data)
{
	if (!ch || !data)
		return;

	TPacketCGNPCLocationHelper packet;
	memcpy(&packet, data, sizeof(packet));
	CNpcLocationHelperManager::Instance().HandlePacket(ch, packet);
}

bool NpcLocationHelperUseItem(CHARACTER* ch, CItem* item)
{
	if (!ch || !item || !ch->IsPC())
		return false;

	if (item->GetVnum() == CNpcLocationHelperManager::ITEM_ACTIVATOR)
		return CNpcLocationHelperManager::Instance().UseActivator(ch, item);

	return false;
}
