// MT2009_PLUS_GLOVES_V1 / MT2009_PLUS_PRECISION_V1 / MT2009_PLUS_JADE_BRACELET_V2: the Yohara gear of the second 3.x
// exe round (server-patches/rekawice, precyzja, obreczjadeitu2 - their README.md):
//   * Rekawice Sung Ma (23000-23039): the glove slot (WEAR_GLOVE, ENABLE_GLOVE_SYSTEM), the glove's Sung Ma Will - its
//     base attribute (MT2009_PLUS_GLOVE_BASE_V1: the item's yextra, not a bonus slot; the wiki's range of the level,
//     carried by a refine; the 6th and 7th bonus slots are the 6/7 system's), Kamienie (Mocy) Demonow (METIN_SUNGMA) in
//     its three sockets - a random Will of the stone's value, kept in the socket as Owsap's number
//     apply * 10000 + stone level * 1000 + stone kind * 100 + value;
//   * Obrecze Jadeitu (14580-14619), Kolie Jadeitu (16580-16619) and Klipsy Jadeitu (17570-17609,
//     MT2009_PLUS_JADE_JEWELLERY_V1): two random base lines (Precyzja, the Will of the jade) with the wiki's ranges of
//     each kind, carried by a refine; the jade in the Diamond's sockets (up to 3) adds the wiki's per-socket values;
//   * Precyzja (POINT_HIT_PCT, 197) and the Sung Ma per cent bonuses (POINT_SUNGMA_PER_*, 193-196): the effective
//     Sung Ma stat a map's requirement is checked against.
// The engine's hooks declare what they call (the edits of the three patches); this header is for the overlay itself.
#ifndef MT2009_PLUS_PLAYERBOT_YOHARA_GEAR_H
#define MT2009_PLUS_PLAYERBOT_YOHARA_GEAR_H

class CHARACTER;
class CItem;
typedef CHARACTER* LPCHARACTER;
typedef CItem* LPITEM;

namespace yohara_gear
{
	enum
	{
		GLOVE_VNUM_FIRST = 23000,			// Rekawice Mocy+0 .. Ochronne Rekawice+9
		GLOVE_VNUM_LAST = 23039,
		SUNGMA_SOCKET_MIN = 1000000,		// a socket at or above it is a Sung Ma stone's number, not a vnum
		JADE_SOCKET_MAX = 3,
	};

	// The effective Sung Ma stat: the point (spent points + items + affects) raised by its per cent bonus
	// (POINT_SUNGMA_PER_*, GF's "Wola SungMa +x%"). bPoint is POINT_SUNGMA_STR..IMMUNE.
	int SungmaEffective(const CHARACTER* ch, unsigned char bPoint);
	// A Sung Ma stone's socket number: its Will (POINT_SUNGMA_*) and value; false for any other socket.
	bool DecodeSungmaSocket(long lSocket, unsigned char& bPoint, int& iValue);
}

// MT2009_PLUS_GLOVE_BASE_V1: a glove's Will as worn (its base attribute raised by its "Atrybuty podstawowe rekawic +x%"
// lines) and its kind (POINT_SUNGMA_*); 0 for any other item.
int Mt2009GloveBaseWill(LPITEM item, unsigned char& bWillType);

// MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1 / MT2009_PLUS_BOT_YOHARA_G0_V1 (playerbot_yohara_g0.cpp): the account-bound items of the
// bots' G0 package - bound (the engine's flag, server-patches/g0bind: no drop, trade, merchant or shop), marked with
// their row (player.item_account_bound), read back at load, carried by a refine, moved to another bot by a sale.
bool Mt2009AccountBoundFamily(unsigned int dwVnum);
bool Mt2009AccountBound(LPITEM item);
bool Mt2009AccountBoundMark(LPITEM item, unsigned int dwPID, const char* szWhy);
void Mt2009AccountBoundOwner(LPITEM item, unsigned int dwPID);
void Mt2009AccountBoundLoad(LPITEM item, bool bIsNewItem);
void Mt2009AccountBoundCarry(LPITEM pOld, LPITEM pNew);

#endif
