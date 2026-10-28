#pragma once
// MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC, the improved world map (Autor: Best Studio; ported to MT2009 Plus).
//
// The client's big map shows every NPC of a map by category, marks the chosen one, draws an arrow under the character
// and can teleport the player next to it for Kamien Teleportacji (79669, bound) / Kamien Teleportacji+ (79668); a
// monster guide lists the map's monsters and their drops. The lists come from the client's own data files; the
// server knows the same NPC points (locale/poland/npc_location_helper/, generated from our maps by
// tools/npcloc/gen_npcloc_data.py) and checks every teleport against them - the client never sends a coordinate
// the server takes on trust.
//
// Packets (both 196, a range of their own - "Community" and the other systems use other numbers): 18 + 1 sequence
// byte client -> server, 24 server -> client. A bot has no client: it never sends this packet and nothing is sent
// to a character without a desc.
#include <map>
#include <set>
#include <string>
#include <vector>
#include <stdint.h>

enum
{
	HEADER_CG_NPC_LOCATION_HELPER = 196,
	HEADER_GC_NPC_LOCATION_HELPER = 196,
};

enum ENPCLocationHelperCGSubHeader
{
	NPC_LOCATION_HELPER_CG_REQUEST_STATUS,
	NPC_LOCATION_HELPER_CG_WARP_TO_NPC,
	NPC_LOCATION_HELPER_CG_USE_TICKET,
	NPC_LOCATION_HELPER_CG_REQUEST_GUILD_LAND,
};

enum ENPCLocationHelperGCSubHeader
{
	NPC_LOCATION_HELPER_GC_STATUS,
	NPC_LOCATION_HELPER_GC_WARP_RESULT,
	NPC_LOCATION_HELPER_GC_GUILD_LAND,
};

#pragma pack(push, 1)
typedef struct command_npc_location_helper_cg
{
	uint8_t		header;
	uint8_t		subheader;
	int32_t		mapIndex;
	uint32_t	vnum;
	int32_t		x;		// local metres (the point file's value / 100)
	int32_t		y;
} TPacketCGNPCLocationHelper;

typedef struct command_npc_location_helper_gc
{
	uint8_t		header;
	uint8_t		subheader;
	uint8_t		result;
	uint8_t		active;
	uint32_t	cooldownRemain;
	int32_t		mapIndex;
	uint32_t	vnum;
	int32_t		x;
	int32_t		y;
} TPacketGCNPCLocationHelper;
#pragma pack(pop)

static_assert(sizeof(TPacketCGNPCLocationHelper) == 18, "NPC location helper CG packet: 18 bytes on both sides");
static_assert(sizeof(TPacketGCNPCLocationHelper) == 24, "NPC location helper GC packet: 24 bytes on both sides");

class CHARACTER;
class CItem;

class CNpcLocationHelperManager
{
public:
	enum EResult
	{
		RESULT_OK,
		RESULT_NOT_ACTIVE,
		RESULT_CANNOT_USE,
		RESULT_COOLDOWN,
		RESULT_INVALID_TARGET,
		RESULT_LEVEL_LIMIT,
		RESULT_EMPIRE_LIMIT,
		RESULT_NEED_ITEM,
		RESULT_NEED_YANG,
	};

	enum
	{
		ITEM_ACTIVATOR = 79667,
		ITEM_WARP_STONE_PLUS = 79668,
		ITEM_WARP_STONE = 79669,
		WARP_COOLDOWN_SEC = 300,
		ROLE_PORTAL = 1,	// the point file's icon 1: a portal
	};

	// No singleton object in main.cpp: made on first use (the files are read then too).
	static CNpcLocationHelperManager& Instance();

	void HandlePacket(CHARACTER* ch, const TPacketCGNPCLocationHelper& packet);
	bool UseActivator(CHARACTER* ch, CItem* item);
	bool IsActive(CHARACTER* ch) const;
	void SendStatus(CHARACTER* ch) const;

private:
	CNpcLocationHelperManager();

	struct SMapInfo
	{
		long mapIndex;
		std::string mapDir;
		int category;
		int minLevel;
		int minConquerorLevel;
		int empire;
		int showAtlas;
		int showNpcList;
		long long warpNeedYang;
		DWORD warpNeedItemVnum;
		int warpNeedItemCount;
	};

	struct SNpcInfo
	{
		long mapIndex;
		DWORD vnum;
		long x;		// local metres
		long y;
		int icon;	// the role icon (1 portal ... 19 other NPC)
	};

	bool Load();
	bool LoadMapInfo(const std::string& filename);
	void LoadPointFile(const std::string& filename, const SMapInfo& mapInfo);
	bool FindNpc(long mapIndex, DWORD vnum, long x, long y, SNpcInfo& out) const;
	const SMapInfo* FindMap(long mapIndex) const;
	void WarpToNPC(CHARACTER* ch, const TPacketCGNPCLocationHelper& packet);
	void SendPacket(CHARACTER* ch, BYTE subheader, BYTE result, const SNpcInfo* npc = NULL) const;
	DWORD GetCooldownRemain(CHARACTER* ch) const;
	int GetStoneCost(long fromMapIndex, long toMapIndex) const;
	void ConsumeWarpStones(CHARACTER* ch, int count) const;
	bool IsBlockedSourceMap(CHARACTER* ch, long mapIndex) const;
	bool IsOpenTargetMap(const SMapInfo& mapInfo) const;

	std::map<long, SMapInfo> m_mapInfo;
	std::vector<SNpcInfo> m_vecNpcInfo;
	std::set<DWORD> m_setClientHandles;	// DESC handles whose client sent HEADER_CG_NPC_LOCATION_HELPER
	bool m_bLoaded;
	bool m_bLoadTried;
};

// Called by input_main.cpp (HEADER_CG_NPC_LOCATION_HELPER) and char_item.cpp (USE_SPECIAL 79667).
void NpcLocationHelperPacket(CHARACTER* ch, const char* data);
bool NpcLocationHelperUseItem(CHARACTER* ch, CItem* item);
