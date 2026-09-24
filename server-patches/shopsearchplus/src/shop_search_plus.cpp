// MT2009 PLUS: Target Drop Info and the private shop search (server-patches/shopsearchplus).
#include "stdafx.h"
#include "../../common/CommonDefines.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "desc.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "buffer_manager.h"
#include "shop_search_plus.h"
#ifdef ENABLE_IKASHOP_RENEWAL
#include "ikarus_shop.h"
#include "ikarus_shop_manager.h"
#endif

#include <algorithm>
#include <cctype>
#include <cstring>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace shop_search_plus
{
	enum EState
	{
		STATE_OFF,
		STATE_LOOKING,
		STATE_TRADING,
	};

	static std::map<DWORD, BYTE> s_state;			// player id -> EState
	static std::map<DWORD, DWORD> s_lastDrop;		// player id -> get_dword_time()
	static std::map<DWORD, DWORD> s_lastSearch;

	static bool TooSoon(std::map<DWORD, DWORD>& last, DWORD pid, DWORD ms)
	{
		const DWORD now = get_dword_time();
		auto it = last.find(pid);
		if (it != last.end() && now - it->second < ms)
			return true;
		last[pid] = now;
		return false;
	}

	// The refine family of an item: weapons, armour, jewellery and belts
	// count +0..+9 as ten vnums in a row, so a monster that drops a sword
	// +0, +1 and +3 shows the sword once, at its lowest plus.
	static bool IsRefineFamily(const TItemTable* t)
	{
		if (!t)
			return false;
		if (t->dwFlags & ITEM_FLAG_STACKABLE)	// arrows, quivers
			return false;
		if (t->bType == ITEM_WEAPON)
			return t->bSubType != WEAPON_ARROW;
		return t->bType == ITEM_ARMOR || t->bType == ITEM_BELT;
	}

	void RecvTargetDrop(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc())
			return;

		if (TooSoon(s_lastDrop, ch->GetPlayerID(), 1000))
			return;

		LPCHARACTER target = ch->GetTarget();
		if (!target || target->IsPC() || !(target->IsMonster() || target->IsStone()))
			return;
		if (target->GetMapIndex() != ch->GetMapIndex())
			return;

		std::set<DWORD> possible;
		bool complete = true;
		ITEM_MANAGER::instance().GetPossibleMobDropItems(ch, target, possible, complete);

		std::map<DWORD, DWORD> byFamily;	// vnum / 10 -> lowest vnum, for refine families
		std::set<DWORD> shown;
		for (DWORD vnum : possible)
		{
			const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnum);
			if (IsRefineFamily(t))
			{
				auto it = byFamily.find(vnum / 10);
				if (it == byFamily.end())
					byFamily[vnum / 10] = vnum;
				else
				{
					const TItemTable* other = ITEM_MANAGER::instance().GetTable(it->second);
					if (other && other->bType == t->bType && other->bSubType == t->bSubType)
						it->second = std::min(it->second, vnum);
					else
						shown.insert(vnum);
				}
			}
			else
				shown.insert(vnum);
		}
		for (const auto& it : byFamily)
			shown.insert(it.second);

		TPacketGCTargetDrop p{};
		p.header = HEADER_GC_TARGET_DROP;
		p.raceVnum = static_cast<WORD>(target->GetRaceNum());
		for (DWORD vnum : shown)
		{
			if (p.size >= TARGET_DROP_ITEM_MAX)
				break;
			p.items[p.size++] = vnum;
		}
		ch->GetDesc()->Packet(&p, sizeof(p));
	}

	static bool WindowsOpen(LPCHARACTER ch)
	{
		return ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen();
	}

	bool UseGlass(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !ch->GetDesc())
			return false;
		const DWORD vnum = item->GetVnum();
		if (vnum != SHOP_SEARCH_LOOKING_GLASS && vnum != SHOP_SEARCH_TRADING_GLASS)
			return false;

		if (WindowsOpen(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby uzyc wyszukiwarki sklepow.");
			return true;
		}

		TPacketGCPrivateShopSearchOpen p{};
		p.header = HEADER_GC_PRIVATE_SHOP_SEARCH_OPEN;
		p.bMode = vnum == SHOP_SEARCH_LOOKING_GLASS ? STATE_LOOKING : STATE_TRADING;
		ch->GetDesc()->Packet(&p, sizeof(p));
		s_state[ch->GetPlayerID()] = p.bMode;
		return true;
	}

	void RecvClose(LPCHARACTER ch)
	{
		if (ch)
			s_state.erase(ch->GetPlayerID());
	}

	static BYTE StateOf(LPCHARACTER ch)
	{
		auto it = s_state.find(ch->GetPlayerID());
		return it == s_state.end() ? STATE_OFF : it->second;
	}

	// Case-insensitive "contains" (ASCII letters fold; Polish letters must match).
	static bool NameMatches(const char* name, const char* wanted)
	{
		if (!wanted || !*wanted)
			return true;
		std::string a(name ? name : ""), b(wanted);
		for (auto& c : a) c = static_cast<char>(tolower(static_cast<unsigned char>(c)));
		for (auto& c : b) c = static_cast<char>(tolower(static_cast<unsigned char>(c)));
		return a.find(b) != std::string::npos;
	}

	static int LevelLimit(const TItemTable* t)
	{
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (t->aLimits[i].bType == LIMIT_LEVEL)
				return t->aLimits[i].lValue;
		return 0;
	}

	static bool JobCanUse(const TItemTable* t, BYTE job)
	{
		switch (job)
		{
			case JOB_WARRIOR:  return !(t->dwAntiFlags & ITEM_ANTIFLAG_WARRIOR);
			case JOB_ASSASSIN: return !(t->dwAntiFlags & ITEM_ANTIFLAG_ASSASSIN);
			case JOB_SURA:     return !(t->dwAntiFlags & ITEM_ANTIFLAG_SURA);
			case JOB_SHAMAN:   return !(t->dwAntiFlags & ITEM_ANTIFLAG_SHAMAN);
		}
		return true;
	}

	void RecvSearch(LPCHARACTER ch, const char* data)
	{
		if (!ch || !ch->GetDesc() || !data)
			return;
		if (StateOf(ch) == STATE_OFF)
			return;
		if (TooSoon(s_lastSearch, ch->GetPlayerID(), 2000))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Poczekaj chwile przed kolejnym wyszukiwaniem.");
			return;
		}

		TPacketCGPrivateShopSearch p;
		std::memcpy(&p, data, sizeof(p));
		p.szItemName[ITEM_NAME_MAX_LEN] = '\0';

		static const size_t MAX_RESULTS = (65535 - sizeof(TPacketGCPrivateShopSearch)) / sizeof(TPacketGCPrivateShopSearchItem);
		std::vector<TPacketGCPrivateShopSearchItem> results;

#ifdef ENABLE_IKASHOP_RENEWAL
		for (const auto& entry : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			const auto& shop = entry.second;
			if (!shop || shop->GetDuration() < 1 || shop->IsEditMode())
				continue;
			if (shop->GetOwnerPID() == ch->GetPlayerID())
				continue;

			for (const auto& itemEntry : shop->GetItems())
			{
				const auto& shopItem = itemEntry.second;
				if (!shopItem)
					continue;
				const auto& info = shopItem->GetInfo();
				const TItemTable* t = ITEM_MANAGER::instance().GetTable(info.vnum);
				if (!t)
					continue;

				const int refine = IsRefineFamily(t) ? static_cast<int>(info.vnum % 10) : 0;
				const int level = LevelLimit(t);
				const long long price = shopItem->GetPrice().GetTotalYangAmount();

				if (!NameMatches(t->szLocaleName, p.szItemName))
					continue;
				if (refine < p.iMinRefine || refine > p.iMaxRefine)
					continue;
				if (level < p.iMinLevel || level > p.iMaxLevel)
					continue;
				if (price < p.llMinGold || price > p.llMaxGold)
					continue;
				if (p.bMaskType != ITEM_NONE && p.bMaskType != t->bType)
					continue;
				if (p.iMaskSub != -1 && p.iMaskSub != t->bSubType)
					continue;
				if (!JobCanUse(t, p.bJob))
					continue;

				TPacketGCPrivateShopSearchItem r{};
				r.item.vnum = info.vnum;
				r.item.price = price;
				r.item.count = info.count;
				r.item.display_pos = static_cast<BYTE>(info.pos);
				std::memcpy(r.item.alSockets, info.alSockets, sizeof(r.item.alSockets));
				std::memcpy(r.item.aAttr, info.aAttr, sizeof(r.item.aAttr));
				strlcpy(r.szSellerName, shop->GetOwnerName(), sizeof(r.szSellerName));
				r.dwShopPID = shop->GetOwnerPID();
				r.dwItemID = shopItem->GetID();
#ifdef ENABLE_IKASHOP_ENTITIES
				const auto& spawn = shop->GetSpawn();
				r.lMapIndex = spawn.map;
				r.lX = spawn.x;
				r.lY = spawn.y;
				r.bChannel = spawn.channel;
#endif
				results.push_back(r);
				if (results.size() >= MAX_RESULTS)
					break;
			}
			if (results.size() >= MAX_RESULTS)
				break;
		}
#endif

		TPacketGCPrivateShopSearch pack{};
		pack.header = HEADER_GC_PRIVATE_SHOP_SEARCH;
		pack.size = static_cast<WORD>(sizeof(pack) + sizeof(TPacketGCPrivateShopSearchItem) * results.size());

		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(pack));
		if (!results.empty())
			buf.write(&results[0], sizeof(TPacketGCPrivateShopSearchItem) * results.size());
		ch->GetDesc()->Packet(buf.read_peek(), buf.size());

		if (results.size() >= MAX_RESULTS)
			ch->ChatPacket(CHAT_TYPE_INFO, "Znaleziono wiecej przedmiotow, pokazano pierwsze %d. Zawez wyszukiwanie.", (int) MAX_RESULTS);
	}

	void RecvBuy(LPCHARACTER ch, const char* data)
	{
		if (!ch || !ch->GetDesc() || !data)
			return;

		TPacketCGPrivateShopSearchBuyItem p;
		std::memcpy(&p, data, sizeof(p));

		if (WindowsOpen(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby uzyc wyszukiwarki sklepow.");
			return;
		}

#ifdef ENABLE_IKASHOP_RENEWAL
		auto& manager = ikashop::GetManager();
		auto shop = manager.GetShopByOwnerID(p.dwShopPID);
		if (!shop || shop->GetDuration() < 1 || p.dwShopPID == ch->GetPlayerID())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten sklep juz nie istnieje.");
			return;
		}

		const BYTE state = StateOf(ch);
		if (state == STATE_LOOKING)
		{
			if (ch->CountSpecifyItem(SHOP_SEARCH_LOOKING_GLASS) == 0)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Potrzebujesz Lupy, aby oznaczyc sklep.");
				return;
			}
#ifdef ENABLE_IKASHOP_ENTITIES
			const auto& spawn = shop->GetSpawn();
			if (spawn.map != ch->GetMapIndex() || spawn.channel != g_bChannel || !shop->GetEntity())
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "Sklep jest na innej mapie albo kanale - tam go oznaczysz.");
				return;
			}
			TPacketGCPrivateShopSearchMark mark{};
			mark.header = HEADER_GC_PRIVATE_SHOP_SEARCH_MARK;
			mark.dwShopVID = shop->GetEntity()->GetVID();
			mark.lX = spawn.x;
			mark.lY = spawn.y;
			ch->GetDesc()->Packet(&mark, sizeof(mark));
			ch->ChatPacket(CHAT_TYPE_INFO, "Sklep oznaczony na mapie.");
#endif
			return;
		}

		if (state != STATE_TRADING)
			return;

		if (ch->CountSpecifyItem(SHOP_SEARCH_TRADING_GLASS) == 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Potrzebujesz Lupy Handlarza, aby kupowac z wyszukiwarki.");
			return;
		}
		if (!ch->IkarusShopFloodCheck(ikashop::SHOP_ACTION_WEIGHT_BUY_ITEM))
			return;
		if (shop->IsEditMode() || shop->GetLastEditTime() + 10 > get_global_time())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Wlasciciel wlasnie zmienia ten sklep. Sprobuj za chwile.");
			return;
		}

		auto item = shop->GetItem(p.dwItemID);
		if (!item)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot zostal juz sprzedany.");
			return;
		}
		if (!ch->HasSlotForItem(item->GetVnum()))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie masz miejsca w ekwipunku.");
			return;
		}
		if (!item->CanBuy(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz za malo Yang.");
			return;
		}
		if (item->GetPrice().GetTotalYangAmount() != p.llSeenPrice)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Cena przedmiotu sie zmienila. Wyszukaj jeszcze raz.");
			return;
		}

		// The same locked purchase as buying at the shop: the database locks
		// the item, takes the Yang and hands the item over (ikarus_shop_manager.cpp).
		ch->SetIkarusShopUseTime();
		manager.SendShopLockBuyItemDBPacket(ch, p.dwShopPID, item, p.llSeenPrice);
#endif
	}
}
