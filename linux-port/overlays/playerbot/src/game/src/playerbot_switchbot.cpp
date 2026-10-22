// MT2009_PLUS_SWITCHBOT_V1: Bonus Switcher - Ameria Project's switchbot (srcs/server/game/new_switchbot.cpp/.h,
// char_item.cpp SetSwitchbotItem / ItemLoadSwitchbot / ItemSaveSwitchbot / MoveItem / UseItem under ENABLE_SWITCHBOT and
// ENABLE_SWITCHBOT_RENEWAL; client srcs/client/UserInterface/PythonSwitchbot.cpp, root/uiswitchbot.py), replacing our
// own window of 6 October (MT2009_PLUS_BONUS_SWITCH_V1, playerbot_bonus_switch.h - removed). The owner, 21 October 2026:
// "Zamien bonus switcher z naszej wersji na ten z Amerii, zastosuj nowy kod po stronie serwera jak i klienta".
// server-patches/switchbot/README.md has the whole picture; the engine's hooks are server-patches/switchbot (edits.json).
//
// Ameria's rules, kept:
//   * five slots (SWITCHBOT_SLOT_COUNT), each one item of the bag: a weapon, or an armour of the body, head, shield,
//     wrist, feet, neck or ear (SwitchbotHelper::IsValidItem) - no costume, no glove, no talisman;
//   * an item put in stays in its bag cell, locked (CItem::Lock) - it cannot be moved, put on, sold, traded or stored
//     while it is in a slot; the slot shows it (an item of the window SWITCHBOT, the client's player.SWITCHBOT);
//   * per slot up to five alternatives (SWITCHBOT_ALTERNATIVE_COUNT) of up to five wanted bonuses with a minimal value
//     each - a slot is done when the item has every bonus of one configured alternative (CSwitchbot::CheckItem); the
//     client offers two alternatives (Ameria's premium switchbot unlocked the other three - left out, see README);
//   * one change of every running slot every 0.2 s (c_fSpeed), the engine's own CItem::ChangeAttribute();
//   * a change costs one Zaczarowanie Przedmiotu: 39028, then 71084, 76014, 71151 (c_arSwitchingItems, first one
//     the player has; 71151 only on a weapon / body armour up to level 40, as by hand) - out of them, the switchbot stops;
//   * it stops by itself when an alternative is reached (a whisper from "[Switchbot]" with the slot and the number of
//     changes), and pauses while the player is busy (dead, trading, shop / safebox / cube open, a quest running, warping);
//   * the running switchbot follows the player to another core (HEADER_GG_SWITCHBOT, as Ameria's P2PSendSwitchbot).
// Ours instead of Ameria's: the slots' bag cells are kept in player.switchbot (apply.sh) instead of Ameria's text files
// local_database/switchbot/pid_<pid>.txt (a container's file system is not kept); Ameria's Zodiac branch (its own change
// item 94912 for its Zodiac weapons - here 94912 is a talisman) is left out: Zodiac items use the same change items, as
// by hand; a slot's item without bonuses or with none to change stops the slot (ChangeAttribute would leave it flagged
// "changing" - as by hand, which refuses it); every change is in the item log (CHANGE_ATTRIBUTE, as by hand); a real
// logout stops the slots (Ameria kept running them in memory); the packets carry fixed-size fields (WORD size, DWORD
// vnum). Only a real player whose client said so ("/switchbot hello", root/uiswitchbot.py with the 3.0 exe that knows the
// window SWITCHBOT and the packets 170/171) - an old exe would close on the unknown header 171. Bots never.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "buffer_manager.h"
#include "p2p.h"
#include "log.h"
#include "db.h"
#include "questmanager.h"
#include "cmd.h"
#include "packet.h"

#include <map>
#include <set>
#include <vector>
#include <cstring>
#include "playerbot_mlodzi.h"

namespace
{
	const float c_fSpeed = 0.20f;

	// Ameria's c_arSwitchingItems (common/length.h): the first the player has is used.
	const DWORD c_arSwitchingItems[4] =
	{
		39028,
		71084,
		76014,
		71151,
	};

	enum
	{
		SWITCHBOT_PRICE_AMOUNT = 1,
	};

	bool ValidPosition(DWORD wCell)
	{
		return wCell < SWITCHBOT_SLOT_COUNT;
	}

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	// Ameria keeps these in the character (m_playerData->m_wSwitchbotCell / m_dwSwitchbotUsed): the slot's bag cell + 1
	// (0 = empty) and the changes made in it.
	struct TSwitchbotPlayerData
	{
		WORD wCell[SWITCHBOT_SLOT_COUNT];
		DWORD dwUsed[SWITCHBOT_SLOT_COUNT];
		bool bLoaded;

		TSwitchbotPlayerData() : bLoaded(false)
		{
			memset(wCell, 0, sizeof(wCell));
			memset(dwUsed, 0, sizeof(dwUsed));
		}
	};

	std::map<DWORD, TSwitchbotPlayerData> s_mapPlayerData;	// pid
	std::set<DWORD> s_setHello;							// pid: this core's clients that know the window

	bool HasHello(LPCHARACTER ch)
	{
		return ch && s_setHello.find(ch->GetPlayerID()) != s_setHello.end();
	}

	TSwitchbotPlayerData& PlayerData(DWORD pid)
	{
		return s_mapPlayerData[pid];
	}

	bool QueryOk(const std::unique_ptr<SQLMsg>& m)
	{
		return m.get() && m->uiSQLErrno == 0 && m->Get();
	}

	// Ameria's ItemSaveSwitchbot, a slot at a time (player.switchbot, apply.sh).
	void SaveSlot(DWORD pid, BYTE slot)
	{
		if (!ValidPosition(slot))
			return;

		const TSwitchbotPlayerData& d = PlayerData(pid);
		if (d.wCell[slot] == 0)
			DBManager::instance().DirectQuery("DELETE FROM player.switchbot WHERE pid = %u AND slot = %u", pid, (unsigned int)slot);
		else
			DBManager::instance().DirectQuery("REPLACE INTO player.switchbot (pid, slot, cell, used) VALUES (%u, %u, %u, %u)",
				pid, (unsigned int)slot, (unsigned int)d.wCell[slot], (unsigned int)d.dwUsed[slot]);
	}

	void SendItemSet(LPCHARACTER ch, BYTE slot, LPITEM pItem)
	{
		LPDESC d = ch ? ch->GetDesc() : NULL;
		if (!d)
			return;

		if (pItem)
		{
			TPacketGCItemSet pack;
			pack.header = HEADER_GC_ITEM_SET;
			pack.Cell = TItemPos(SWITCHBOT, slot);
			pack.count = pItem->GetCount();
			pack.vnum = pItem->GetVnum();
			pack.flags = pItem->GetFlag();
			pack.anti_flags = pItem->GetAntiFlag();
			pack.highlight = false;
			thecore_memcpy(pack.alSockets, pItem->GetSockets(), sizeof(pack.alSockets));
			thecore_memcpy(pack.aAttr, pItem->GetAttributes(), sizeof(pack.aAttr));
#ifdef ENABLE_CHANGELOOK_SYSTEM
			pack.dwTransmutation = pItem->GetTransmutation();
#endif
			d->Packet(&pack, sizeof(TPacketGCItemSet));
		}
		else
		{
			TPacketGCItemDelDeprecated pack;
			pack.header = HEADER_GC_ITEM_DEL;
			pack.Cell = TItemPos(SWITCHBOT, slot);
			pack.count = 0;
			pack.vnum = 0;
			memset(pack.alSockets, 0, sizeof(pack.alSockets));
			memset(pack.aAttr, 0, sizeof(pack.aAttr));
#ifdef ENABLE_CHANGELOOK_SYSTEM
			pack.dwTransmutation = 0;
#endif
			d->Packet(&pack, sizeof(TPacketGCItemDelDeprecated));
		}
	}
}

class SwitchbotHelper
{
public:
	static bool IsValidItem(LPITEM pkItem);
};

class CSwitchbot
{
public:
	CSwitchbot();
	~CSwitchbot();

	void SetTable(const TSwitchbotTable& table);
	TSwitchbotTable GetTable();

	void SetPlayerId(DWORD player_id);

	void RegisterItem(WORD wCell, DWORD item_id);
	void UnregisterItem(WORD wCell);
	void SetAttributes(BYTE slot, const std::vector<TSwitchbotAttributeAlternativeTable>& vec_alternatives);

	void SetActive(BYTE slot, bool active);
	bool IsActive(BYTE slot);
	bool HasActiveSlots();
	bool IsSwitching();
	bool IsWarping();
	void SetIsWarping(bool warping);
	bool HasItem(DWORD item_id);

	void Start();
	void Stop();
	void Pause();

	void SwitchItems();
	bool CheckItem(LPITEM pkItem, BYTE slot);

	void SendItemUpdate(LPCHARACTER ch, BYTE slot, LPITEM item);

	bool CanContinueSwitch(LPCHARACTER pChar);

protected:
	TSwitchbotTable m_table;
	LPEVENT m_pkSwitchEvent;
	bool m_isWarping;
};

class CSwitchbotManager
{
public:
	static CSwitchbotManager& Instance()
	{
		static CSwitchbotManager s_instance;
		return s_instance;
	}

	CSwitchbotManager();
	~CSwitchbotManager();

	void Initialize();
	void RegisterItem(DWORD player_id, DWORD item_id, WORD wCell);
	void UnregisterItem(DWORD player_id, WORD wCell);
	void Start(DWORD player_id, BYTE slot, const std::vector<TSwitchbotAttributeAlternativeTable>& vec_alternatives);
	void Stop(DWORD player_id, BYTE slot);

	bool IsActive(DWORD player_id, BYTE slot);
	bool IsWarping(DWORD player_id);
	void SetIsWarping(DWORD player_id, bool warping);

	CSwitchbot* FindSwitchbot(DWORD player_id);
	void Remove(DWORD player_id);

	void P2PSendSwitchbot(DWORD player_id, WORD wTargetPort);
	void P2PReceiveSwitchbot(const TSwitchbotTable& table);

	void SendItemAttributeInformations(LPCHARACTER ch);
	void SendSwitchbotUpdate(DWORD player_id);

	void EnterGame(LPCHARACTER ch);
	bool IsItemIDInSwitchbot(DWORD dwPID, DWORD dwItemID);

protected:
	std::map<DWORD, CSwitchbot*> m_map_Switchbots;
};

// Ameria's CHARACTER::Get/SetSwitchbotItemSwitcherUsed, SetSwitchbotItem, ItemLoadSwitchbot - free functions here.
static DWORD GetSwitchbotItemSwitcherUsed(LPCHARACTER ch, WORD wCell)
{
	if (!ch || !ValidPosition(wCell))
		return 0;
	return PlayerData(ch->GetPlayerID()).dwUsed[wCell];
}

static void SetSwitchbotItemSwitcherUsed(LPCHARACTER ch, WORD wCell, DWORD dwCount)
{
	if (!ch || !ValidPosition(wCell))
		return;
	PlayerData(ch->GetPlayerID()).dwUsed[wCell] = dwCount;
}

static void SetSwitchbotItem(LPCHARACTER ch, WORD wCell, WORD wCellInven);

bool SwitchbotHelper::IsValidItem(LPITEM pkItem)
{
	if (!pkItem)
	{
		return false;
	}

	// MT2009_PLUS_MLODZI_BOHATEROWIE_V1 (switchbot): a young heroes' weapon takes no bonus changes
	if (MlodziIsWeaponVnum(pkItem->GetVnum()))
	{
		return false;
	}

	switch (pkItem->GetType())
	{
	case ITEM_WEAPON:
		return pkItem->GetSubType() != WEAPON_ARROW
#ifdef ENABLE_QUIVER_SYSTEM
			&& pkItem->GetSubType() != WEAPON_QUIVER
#endif
			;

	case ITEM_ARMOR:
		switch (pkItem->GetSubType())
		{
		case ARMOR_BODY:
		case ARMOR_HEAD:
		case ARMOR_SHIELD:
		case ARMOR_WRIST:
		case ARMOR_FOOTS:
		case ARMOR_NECK:
		case ARMOR_EAR:
			return true;
		}
		return false;

	default:
		return false;
	}
}

CSwitchbot::CSwitchbot()
{
	m_pkSwitchEvent = nullptr;
	m_table = TSwitchbotTable();
	m_isWarping = false;
}

CSwitchbot::~CSwitchbot()
{
	if (m_pkSwitchEvent)
	{
		event_cancel(&m_pkSwitchEvent);
		m_pkSwitchEvent = nullptr;
	}

	m_isWarping = false;
}

void CSwitchbot::SetTable(const TSwitchbotTable& table)
{
	m_table = table;
}

TSwitchbotTable CSwitchbot::GetTable()
{
	return m_table;
}

void CSwitchbot::SetPlayerId(DWORD player_id)
{
	m_table.player_id = player_id;
}

void CSwitchbot::RegisterItem(WORD wCell, DWORD item_id)
{
	if (!ValidPosition(wCell))
	{
		return;
	}

	m_table.items[wCell] = item_id;
}

void CSwitchbot::UnregisterItem(WORD wCell)
{
	if (!ValidPosition(wCell))
	{
		return;
	}

	m_table.items[wCell] = 0;
	m_table.active[wCell] = false;
	m_table.finished[wCell] = false;
	memset(&m_table.alternatives[wCell], 0, sizeof(m_table.alternatives[wCell]));
}

void CSwitchbot::SetAttributes(BYTE slot, const std::vector<TSwitchbotAttributeAlternativeTable>& vec_alternatives)
{
	if (!ValidPosition(slot) || vec_alternatives.size() < SWITCHBOT_ALTERNATIVE_COUNT)
	{
		return;
	}

	for (BYTE alternative = 0; alternative < SWITCHBOT_ALTERNATIVE_COUNT; ++alternative)
	{
		for (BYTE attrIdx = 0; attrIdx < SWITCHBOT_ATTR_COUNT; ++attrIdx)
		{
			m_table.alternatives[slot][alternative].attributes[attrIdx].bType = vec_alternatives[alternative].attributes[attrIdx].bType;
			m_table.alternatives[slot][alternative].attributes[attrIdx].sValue = vec_alternatives[alternative].attributes[attrIdx].sValue;
		}
	}
}

void CSwitchbot::SetActive(BYTE slot, bool active)
{
	if (!ValidPosition(slot))
	{
		return;
	}

	if (!active)
	{
		LPCHARACTER pkOwner = CHARACTER_MANAGER::Instance().FindByPID(m_table.player_id);
		if (pkOwner)
			SetSwitchbotItemSwitcherUsed(pkOwner, slot, 0);
	}

	m_table.active[slot] = active;
	m_table.finished[slot] = false;
}

EVENTINFO(TSwitchbotEventInfo)
{
	CSwitchbot* pkSwitchbot;

	TSwitchbotEventInfo() : pkSwitchbot(nullptr)
	{
	}
};

EVENTFUNC(switchbot_event)
{
	TSwitchbotEventInfo* info = dynamic_cast<TSwitchbotEventInfo*>(event->info);

	if (info == NULL)
	{
		sys_err("switchbot_event> <Factor> Info Null pointer");
		return 0;
	}

	if (!info->pkSwitchbot)
	{
		sys_err("switchbot_event> <Factor> Switchbot Null pointer");
		return 0;
	}

	info->pkSwitchbot->SwitchItems();

	return PASSES_PER_SEC(c_fSpeed);
}

void CSwitchbot::Start()
{
	if (m_pkSwitchEvent)
		return;

	TSwitchbotEventInfo* info = AllocEventInfo<TSwitchbotEventInfo>();
	info->pkSwitchbot = this;

	m_pkSwitchEvent = event_create(switchbot_event, info, PASSES_PER_SEC(c_fSpeed));

	CSwitchbotManager::Instance().SendSwitchbotUpdate(m_table.player_id);
}

void CSwitchbot::Stop()
{
	if (m_pkSwitchEvent)
	{
		event_cancel(&m_pkSwitchEvent);
		m_pkSwitchEvent = nullptr;
	}

	memset(&m_table.active, 0, sizeof(m_table.active));

	LPCHARACTER pkOwnerW = CHARACTER_MANAGER::Instance().FindByPID(m_table.player_id);

	for (BYTE bSlot = 0; bSlot < SWITCHBOT_SLOT_COUNT; ++bSlot)
	{
		if (pkOwnerW)
			SetSwitchbotItemSwitcherUsed(pkOwnerW, bSlot, 0);
	}

	CSwitchbotManager::Instance().SendSwitchbotUpdate(m_table.player_id);
}

void CSwitchbot::Pause()
{
	if (m_pkSwitchEvent)
	{
		event_cancel(&m_pkSwitchEvent);
		m_pkSwitchEvent = nullptr;
	}
}

bool CSwitchbot::IsActive(BYTE slot)
{
	if (!ValidPosition(slot))
	{
		return false;
	}

	return m_table.active[slot];
}

bool CSwitchbot::HasActiveSlots()
{
	for (const auto& it : m_table.active)
	{
		if (it)
		{
			return true;
		}
	}

	return false;
}

bool CSwitchbot::IsSwitching()
{
	return m_pkSwitchEvent != nullptr;
}

bool CSwitchbot::IsWarping()
{
	return m_isWarping;
}

void CSwitchbot::SetIsWarping(bool warping)
{
	m_isWarping = warping;
}

bool CSwitchbot::HasItem(DWORD item_id)
{
	if (!item_id)
		return false;

	for (BYTE bSlot = 0; bSlot < SWITCHBOT_SLOT_COUNT; ++bSlot)
	{
		if (m_table.items[bSlot] == item_id)
			return true;
	}

	return false;
}

// Ameria's 71151 / 76023 rule (CHECK_LIMITED_ITEM, as the engine by hand): a weapon or a body armour up to level 40.
static bool CanUseSwitcherOn(DWORD dwSwitcherVnum, LPITEM pkItem)
{
	if (dwSwitcherVnum != 71151 && dwSwitcherVnum != 76023)
		return true;

	if (!((pkItem->GetType() == ITEM_WEAPON) || (pkItem->GetType() == ITEM_ARMOR && pkItem->GetSubType() == ARMOR_BODY)))
		return false;

	for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
	{
		if (pkItem->GetLimitType(i) == LIMIT_LEVEL && pkItem->GetLimitValue(i) > 40)
			return false;
	}

	return true;
}

void CSwitchbot::SwitchItems()
{
	for (BYTE bSlot = 0; bSlot < SWITCHBOT_SLOT_COUNT; ++bSlot)
	{
		if (!m_table.active[bSlot])
		{
			continue;
		}

		m_table.finished[bSlot] = false;

		const DWORD item_id = m_table.items[bSlot];

		LPITEM pkItem = ITEM_MANAGER::Instance().Find(item_id);
		if (!pkItem
			 || pkItem->IsExchanging())
		{
			continue;
		}

		LPCHARACTER pkOwner = pkItem->GetOwner();
		if (!CanContinueSwitch(pkOwner))
		{
			return;
		}

		if (pkOwner->GetPlayerID() != m_table.player_id)
		{
			continue;
		}

		if (CheckItem(pkItem, bSlot))
		{
			LPDESC desc = pkOwner->GetDesc();
			if (desc)
			{
				char buf[255];
				int len = snprintf(buf, sizeof(buf), "Zmiana bonusow %s zakonczona (miejsce %d, uzyto zaczarowan: %u).",
					pkItem->GetName(), bSlot + 1, GetSwitchbotItemSwitcherUsed(pkOwner, bSlot));
				if (len < 0)
					len = 0;
				if (len >= (int)sizeof(buf))
					len = sizeof(buf) - 1;

				TPacketGCWhisper pack;
				pack.bHeader = HEADER_GC_WHISPER;
				pack.bType = WHISPER_TYPE_SYSTEM;
				pack.wSize = sizeof(TPacketGCWhisper) + len;
				strlcpy(pack.szNameFrom, "[Switchbot]", sizeof(pack.szNameFrom));
				desc->BufferedPacket(&pack, sizeof(pack));
				desc->Packet(buf, len);
			}

			SetActive(bSlot, false);
			SaveSlot(m_table.player_id, bSlot);

			m_table.finished[bSlot] = true;

			if (!HasActiveSlots())
			{
				Stop();
			}
			else
			{
				CSwitchbotManager::Instance().SendSwitchbotUpdate(m_table.player_id);
			}
		}
		else
		{
			// Ours: an item the engine would not change by hand (no bonuses, no attribute set) stops the slot -
			// CItem::ChangeAttribute on it would clear nothing and leave it flagged "changing".
			if (pkItem->GetAttributeSetIndex() == -1 || pkItem->GetAttributeCount() == 0)
			{
				pkOwner->ChatPacket(CHAT_TYPE_INFO, "Switchbot: tego przedmiotu nie mozna zaczarowac (brak bonusow).");
				SetActive(bSlot, false);
				if (!HasActiveSlots())
					Stop();
				else
					CSwitchbotManager::Instance().SendSwitchbotUpdate(m_table.player_id);
				continue;
			}

			DWORD dwUseVnum = 0;
			for (const auto& itemVnum : c_arSwitchingItems)
			{
				if (!CanUseSwitcherOn(itemVnum, pkItem))
					continue;

				if (pkOwner->CountSpecifyItem(itemVnum) >= SWITCHBOT_PRICE_AMOUNT)
				{
					dwUseVnum = itemVnum;
					break;
				}
			}

			if (!dwUseVnum)
			{
				Stop();
				pkOwner->ChatPacket(CHAT_TYPE_INFO, "Switchbot zatrzymany. Brak Zaczarowan Przedmiotu.");
				return;
			}

			// as by hand (char_item.cpp): the change item's vnum, the changed item's id
			LogManager::instance().ItemLog(pkOwner, (int)pkItem->GetID(), (int)dwUseVnum, "CHANGE_ATTRIBUTE", "switchbot");

			pkOwner->RemoveSpecifyItem(dwUseVnum, SWITCHBOT_PRICE_AMOUNT);

			pkItem->ChangeAttribute();

			SetSwitchbotItemSwitcherUsed(pkOwner, bSlot, GetSwitchbotItemSwitcherUsed(pkOwner, bSlot) + 1);

			SendItemUpdate(pkOwner, bSlot, pkItem);
		}
	}
}

bool CSwitchbot::CheckItem(LPITEM pkItem, BYTE slot)
{
	if (!ValidPosition(slot))
	{
		return false;
	}

	if (!pkItem)
	{
		return false;
	}

	bool checked = 0;

	for (const auto& alternative : m_table.alternatives[slot])
	{
		if (!alternative.IsConfigured())
		{
			continue;
		}

		BYTE configuredAttrCount = 0;
		BYTE correctAttrCount = 0;

		for (const auto& destAttr : alternative.attributes)
		{
			if (!destAttr.bType || !destAttr.sValue)
			{
				continue;
			}

			++configuredAttrCount;

			for (BYTE attrIdx = 0; attrIdx < SWITCHBOT_ATTR_COUNT; ++attrIdx)
			{
				const TPlayerItemAttribute& curAttr = pkItem->GetAttribute(attrIdx);

				if (curAttr.bType != destAttr.bType || curAttr.sValue < destAttr.sValue)
				{
					continue;
				}

				++correctAttrCount;
				break;
			}
		}

		checked = true;

		if (configuredAttrCount == correctAttrCount)
		{
			return true;
		}
	}

	if (!checked)
	{
		return true;
	}

	return false;
}

void CSwitchbot::SendItemUpdate(LPCHARACTER ch, BYTE slot, LPITEM item)
{
	LPDESC desc = ch->GetDesc();
	if (!desc || !HasHello(ch))
	{
		return;
	}

	TPacketGCSwitchbot pack;
	pack.header = HEADER_GC_SWITCHBOT;
	pack.subheader = SUBHEADER_GC_SWITCHBOT_UPDATE_ITEM;
	pack.size = sizeof(TPacketGCSwitchbot) + sizeof(TSwitchbotUpdateItem);
	pack.slot = slot;

	TSwitchbotUpdateItem update = {};
	update.slot = slot;
	update.vnum = item->GetVnum();
	update.count = item->GetCount();
	update.CellInven = item->GetCell();

	for (int i = 0; i < ITEM_SOCKET_MAX_NUM; ++i)
		update.alSockets[i] = item->GetSocket(i);
	std::memcpy(update.aAttr, item->GetAttributes(), sizeof(update.aAttr));

	desc->BufferedPacket(&pack, sizeof(pack));
	desc->Packet(&update, sizeof(TSwitchbotUpdateItem));
}

bool CSwitchbot::CanContinueSwitch(LPCHARACTER ch)
{
	LPDESC d = ch ? ch->GetDesc() : nullptr;
	if (!d)
	{
		return false;
	}

	if (ch->m_pkTimedEvent
		 || ch->IsDead()
		 || ch->IsWarping()
		 || !ch->CanWarp()
		 || ch->GetSafebox()
	)
	{
		return false;
	}

	quest::PC* pPC = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
	if (!pPC
		 || pPC->IsRunning())
	{
		return false;
	}

	return true;
}

CSwitchbotManager::CSwitchbotManager()
{
	Initialize();
}

CSwitchbotManager::~CSwitchbotManager()
{
	// the process ends: the events go with the event system
	m_map_Switchbots.clear();
}

void CSwitchbotManager::Initialize()
{
	m_map_Switchbots.clear();
}

void CSwitchbotManager::RegisterItem(DWORD player_id, DWORD item_id, WORD wCell)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		pkSwitchbot = new CSwitchbot();
		pkSwitchbot->SetPlayerId(player_id);
		m_map_Switchbots.insert(std::make_pair(player_id, pkSwitchbot));
	}

	if (pkSwitchbot->IsWarping())
	{
		return;
	}

	pkSwitchbot->RegisterItem(wCell, item_id);
	SendSwitchbotUpdate(player_id);
}

void CSwitchbotManager::UnregisterItem(DWORD player_id, WORD wCell)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return;
	}

	if (pkSwitchbot->IsWarping())
	{
		return;
	}

	pkSwitchbot->UnregisterItem(wCell);
	SendSwitchbotUpdate(player_id);
}

void CSwitchbotManager::Start(DWORD player_id, BYTE slot, const std::vector<TSwitchbotAttributeAlternativeTable>& vec_alternatives)
{
	if (!ValidPosition(slot))
	{
		return;
	}

	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		sys_err("No Switchbot found for player_id %d slot %d", player_id, slot);
		return;
	}

	if (pkSwitchbot->IsActive(slot))
	{
		sys_err("Switchbot slot %d already running for player_id %d", slot, player_id);
		return;
	}

	if (!pkSwitchbot->GetTable().items[slot])
	{
		return;
	}

	pkSwitchbot->SetActive(slot, true);
	pkSwitchbot->SetAttributes(slot, vec_alternatives);

	if (pkSwitchbot->HasActiveSlots() && !pkSwitchbot->IsSwitching())
	{
		pkSwitchbot->Start();
	}
	else
	{
		SendSwitchbotUpdate(player_id);
	}
}

void CSwitchbotManager::Stop(DWORD player_id, BYTE slot)
{
	if (!ValidPosition(slot))
	{
		return;
	}

	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		sys_err("No Switchbot found for player_id %d slot %d", player_id, slot);
		return;
	}

	if (!pkSwitchbot->IsActive(slot))
	{
		return;
	}

	pkSwitchbot->SetActive(slot, false);

	if (!pkSwitchbot->HasActiveSlots() && pkSwitchbot->IsSwitching())
	{
		pkSwitchbot->Stop();
	}
	else
	{
		SendSwitchbotUpdate(player_id);
	}
}

bool CSwitchbotManager::IsActive(DWORD player_id, BYTE slot)
{
	if (!ValidPosition(slot))
	{
		return false;
	}

	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return false;
	}

	return pkSwitchbot->IsActive(slot);
}

bool CSwitchbotManager::IsWarping(DWORD player_id)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return false;
	}

	return pkSwitchbot->IsWarping();
}

void CSwitchbotManager::SetIsWarping(DWORD player_id, bool warping)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return;
	}

	pkSwitchbot->SetIsWarping(warping);
}

CSwitchbot* CSwitchbotManager::FindSwitchbot(DWORD player_id)
{
	const auto& it = m_map_Switchbots.find(player_id);
	if (it == m_map_Switchbots.end())
	{
		return nullptr;
	}

	return it->second;
}

void CSwitchbotManager::Remove(DWORD player_id)
{
	auto it = m_map_Switchbots.find(player_id);
	if (it == m_map_Switchbots.end())
		return;

	CSwitchbot* pkSwitchbot = it->second;
	m_map_Switchbots.erase(it);
	delete pkSwitchbot;
}

void CSwitchbotManager::P2PSendSwitchbot(DWORD player_id, WORD wTargetPort)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return;
	}

	pkSwitchbot->Pause();

	TPacketGGSwitchbot pack;
	pack.bHeader = HEADER_GG_SWITCHBOT;
	pack.wPort = wTargetPort;
	pack.table = pkSwitchbot->GetTable();

	P2P_MANAGER::Instance().Send(&pack, sizeof(pack));

	Remove(player_id);
}

void CSwitchbotManager::P2PReceiveSwitchbot(const TSwitchbotTable& table)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(table.player_id);
	if (!pkSwitchbot)
	{
		pkSwitchbot = new CSwitchbot();
		m_map_Switchbots.insert(std::make_pair(table.player_id, pkSwitchbot));
	}

	pkSwitchbot->Pause();
	pkSwitchbot->SetTable(table);
	pkSwitchbot->SetIsWarping(true);
}

void CSwitchbotManager::SendItemAttributeInformations(LPCHARACTER ch)
{
	if (!ch)
	{
		return;
	}

	LPDESC desc = ch->GetDesc();
	if (!desc || !HasHello(ch))
	{
		return;
	}

	TPacketGCSwitchbot pack;
	pack.header = HEADER_GC_SWITCHBOT;
	pack.subheader = SUBHEADER_GC_SWITCHBOT_SEND_ATTRIBUTE_INFORMATION;
	pack.size = sizeof(TPacketGCSwitchbot);
	pack.slot = 0;

	TEMP_BUFFER buf;
	for (BYTE bAttributeSet = 0; bAttributeSet < ATTRIBUTE_SET_MAX_NUM; ++bAttributeSet)
	{
		for (const auto& it : g_map_itemAttr)
		{
			const TItemAttrTable& r = it.second;

			BYTE max = r.bMaxLevelBySet[bAttributeSet];
			if (max > 0 && max <= ITEM_ATTRIBUTE_MAX_LEVEL)
			{
				TSwitchbotAttributeInfo table = {};
				table.attribute_set = bAttributeSet;
				table.apply_num = it.first;
				table.max_value = r.lValues[max - 1];

				buf.write(&table, sizeof(table));
			}
		}
	}

	if (buf.size())
	{
		pack.size += buf.size();
		desc->BufferedPacket(&pack, sizeof(pack));
		desc->Packet(buf.read_peek(), buf.size());
	}
	else
	{
		desc->Packet(&pack, sizeof(pack));
	}
}

void CSwitchbotManager::SendSwitchbotUpdate(DWORD player_id)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(player_id);
	if (!pkSwitchbot)
	{
		return;
	}

	LPCHARACTER ch = CHARACTER_MANAGER::Instance().FindByPID(player_id);
	if (!ch || !HasHello(ch))
	{
		return;
	}

	LPDESC desc = ch->GetDesc();
	if (!desc)
	{
		return;
	}

	TSwitchbotTable table = pkSwitchbot->GetTable();

	TPacketGCSwitchbot pack;
	pack.header = HEADER_GC_SWITCHBOT;
	pack.subheader = SUBHEADER_GC_SWITCHBOT_UPDATE;
	pack.size = sizeof(TPacketGCSwitchbot) + sizeof(TSwitchbotTable);
	pack.slot = 0;

	desc->BufferedPacket(&pack, sizeof(pack));
	desc->Packet(&table, sizeof(table));
}

bool CSwitchbotManager::IsItemIDInSwitchbot(DWORD dwPID, DWORD dwItemID)
{
	CSwitchbot* pkSwitchbot = FindSwitchbot(dwPID);
	if (!pkSwitchbot)
		return false;

	return pkSwitchbot->HasItem(dwItemID);
}

void CSwitchbotManager::EnterGame(LPCHARACTER ch)
{
	SendItemAttributeInformations(ch);
	SetIsWarping(ch->GetPlayerID(), false);
	SendSwitchbotUpdate(ch->GetPlayerID());

	CSwitchbot* pkSwitchbot = FindSwitchbot(ch->GetPlayerID());
	if (pkSwitchbot && pkSwitchbot->HasActiveSlots() && !pkSwitchbot->IsSwitching())
	{
		pkSwitchbot->Start();
	}
}

// Ameria's CHARACTER::SetSwitchbotItem: wCellInven = the bag cell + 1, 0 takes the slot's item out.
static void SetSwitchbotItem(LPCHARACTER ch, WORD wCell, WORD wCellInven)
{
	if (!ch || !ch->GetDesc() || !ValidPosition(wCell))
	{
		return;
	}

	TSwitchbotPlayerData& data = PlayerData(ch->GetPlayerID());

	LPITEM pItem = nullptr;
	if (wCellInven > 0) // 0==NONE_POS
		pItem = ch->GetInventoryItem(wCellInven - 1);

	// the old item of the slot, if another one comes in
	if (data.wCell[wCell] != 0 && data.wCell[wCell] != wCellInven)
	{
		LPITEM pOld = ch->GetInventoryItem(data.wCell[wCell] - 1);
		if (pOld && CSwitchbotManager::Instance().IsItemIDInSwitchbot(ch->GetPlayerID(), pOld->GetID()))
			pOld->Lock(false);
	}

	// Refresh Window
	if (pItem && SwitchbotHelper::IsValidItem(pItem))
	{
		pItem->Lock(true);

		SendItemSet(ch, (BYTE)wCell, pItem);

		data.wCell[wCell] = wCellInven;
		data.dwUsed[wCell] = 0;

		CSwitchbotManager::Instance().RegisterItem(ch->GetPlayerID(), pItem->GetID(), wCell);
	}
	else
	{
		SendItemSet(ch, (BYTE)wCell, NULL);

		// UNLOCK_ITEM
		WORD wCellInvenOld = data.wCell[wCell];
		if (wCellInvenOld != 0)
		{
			pItem = ch->GetInventoryItem(wCellInvenOld - 1);
			if (pItem)
				pItem->Lock(false);
		}

		data.wCell[wCell] = 0;
		data.dwUsed[wCell] = 0;

		CSwitchbotManager::Instance().UnregisterItem(ch->GetPlayerID(), wCell);
	}

	SaveSlot(ch->GetPlayerID(), (BYTE)wCell);
}

// Ameria's CHARACTER::ItemLoadSwitchbot (from player.switchbot instead of its text file).
static void ItemLoadSwitchbot(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
	{
		return;
	}

	const DWORD pid = ch->GetPlayerID();
	TSwitchbotPlayerData& data = PlayerData(pid);

	if (!data.bLoaded)
	{
		std::unique_ptr<SQLMsg> m(DBManager::instance().DirectQuery("SELECT slot, cell, used FROM player.switchbot WHERE pid = %u", pid));
		if (QueryOk(m) && m->Get()->pSQLResult)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(m->Get()->pSQLResult)))
			{
				int value1 = 0, value2 = 0;
				unsigned int value3 = 0;
				str_to_number(value1, row[0]);
				str_to_number(value2, row[1]);
				str_to_number(value3, row[2]);

				if (value1 >= 0 && value1 < SWITCHBOT_SLOT_COUNT && value2 >= 0 && value2 <= INVENTORY_MAX_NUM)
				{
					data.wCell[value1] = value2;
					data.dwUsed[value1] = value3;
				}
			}
		}
		data.bLoaded = true;
	}

	CSwitchbot* pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(pid);

	for (int i = 0; i < SWITCHBOT_SLOT_COUNT; ++i)
	{
		WORD wCell = i;
		WORD wCellInven = data.wCell[i];
		if (wCellInven == 0)
		{
			data.dwUsed[wCell] = 0;
			if (pkSwitchbot && pkSwitchbot->GetTable().items[wCell])
				pkSwitchbot->UnregisterItem(wCell);
			SendItemSet(ch, (BYTE)wCell, NULL);
			continue;
		}

		LPITEM pItem = ch->GetInventoryItem(wCellInven - 1);
		if (pItem && SwitchbotHelper::IsValidItem(pItem))
		{
			pItem->Lock(true);

			SendItemSet(ch, (BYTE)wCell, pItem);

			// a switchbot that came from the other core already knows its item (and its run); RegisterItem refuses while
			// it is "warping" - set the item id straight
			if (pkSwitchbot)
				pkSwitchbot->RegisterItem(wCell, pItem->GetID());
			else
			{
				CSwitchbotManager::Instance().RegisterItem(pid, pItem->GetID(), wCell);
				pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(pid);
			}
		}
		else
		{
			SendItemSet(ch, (BYTE)wCell, NULL);

			if (pkSwitchbot)
				pkSwitchbot->UnregisterItem(wCell);
			data.wCell[wCell] = 0;
			data.dwUsed[wCell] = 0;
			SaveSlot(pid, (BYTE)wCell);
		}
	}
}

// ---------------------------------------------------------------- the engine's hooks (server-patches/switchbot)

// input_main.cpp, HEADER_CG_SWITCHBOT (Ameria's CInputMain::Switchbot): the extra bytes read, or -1.
int Mt2009SwitchbotPacket(LPCHARACTER ch, const char* data, size_t uiBytes)
{
	const TPacketCGSwitchbot* p = reinterpret_cast<const TPacketCGSwitchbot*>(data);

	if (uiBytes < sizeof(TPacketCGSwitchbot))
	{
		return -1;
	}

	const char* c_pData = data + sizeof(TPacketCGSwitchbot);
	uiBytes -= sizeof(TPacketCGSwitchbot);

	switch (p->subheader)
	{
	case SUBHEADER_CG_SWITCHBOT_START:
	{
		size_t extraLen = sizeof(TSwitchbotAttributeAlternativeTable) * SWITCHBOT_ALTERNATIVE_COUNT;
		if (uiBytes < extraLen)
		{
			return -1;
		}

		if (!Eligible(ch) || !HasHello(ch))
			return extraLen;

		std::vector<TSwitchbotAttributeAlternativeTable> vec_alternatives;

		for (BYTE alternative = 0; alternative < SWITCHBOT_ALTERNATIVE_COUNT; ++alternative)
		{
			const TSwitchbotAttributeAlternativeTable* pAttr = reinterpret_cast<const TSwitchbotAttributeAlternativeTable*>(c_pData);
			c_pData += sizeof(TSwitchbotAttributeAlternativeTable);

			vec_alternatives.emplace_back(*pAttr);
		}

		if (!ch->CanHandleItem())
			return extraLen;

		CSwitchbotManager::Instance().Start(ch->GetPlayerID(), p->slot, vec_alternatives);
		return extraLen;
	}

	case SUBHEADER_CG_SWITCHBOT_STOP:
	{
		if (Eligible(ch) && HasHello(ch))
			CSwitchbotManager::Instance().Stop(ch->GetPlayerID(), p->slot);
		return 0;
	}
	}

	return 0;
}

// input_main.cpp ItemMove: an item into or out of a switchbot slot (Ameria's MoveItem, IsSwitchbotPosition). True when
// the move was the switchbot's (done or refused).
bool Mt2009SwitchbotItemMove(LPCHARACTER ch, const TItemPos& Cell, const TItemPos& DestCell)
{
	if (!ch)
		return false;

	if (Cell.window_type != SWITCHBOT && DestCell.window_type != SWITCHBOT)
	{
		// Ameria's "Remove item from switchbot first!" (the engine refuses a locked item without a word)
		if (Cell.IsDefaultInventoryPosition())
		{
			LPITEM item = ch->GetInventoryItem(Cell.cell);
			if (item && item->isLocked() && CSwitchbotManager::Instance().IsItemIDInSwitchbot(ch->GetPlayerID(), item->GetID()))
				ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw wyjmij przedmiot ze Switchbota.");
		}
		return false;
	}

	if (!Eligible(ch) || !HasHello(ch))
		return true;

	if (Cell.window_type == SWITCHBOT) // remove item from switchbot
	{
		if (!ValidPosition(Cell.cell))
			return true;

		CSwitchbot* pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(ch->GetPlayerID());
		if (pkSwitchbot && pkSwitchbot->IsActive(Cell.cell))
		{
			return true;
		}

		SetSwitchbotItem(ch, Cell.cell, 0);
		return true;
	}

	// into a slot: from the bag only
	if (!ValidPosition(DestCell.cell) || !Cell.IsDefaultInventoryPosition() || Cell.cell >= ch->GetInventoryMaxCount())
		return true;

	LPITEM item = ch->GetInventoryItem(Cell.cell);
	if (!item)
		return true;

	if (item->IsExchanging())
		return true;

	if (item->isLocked())
	{
		if (CSwitchbotManager::Instance().IsItemIDInSwitchbot(ch->GetPlayerID(), item->GetID()))
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten przedmiot jest juz w Switchbocie.");
		return true;
	}

	if (!ch->CanHandleItem())
		return true;

	CSwitchbot* pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(ch->GetPlayerID());
	if (pkSwitchbot && pkSwitchbot->IsActive(DestCell.cell))
	{
		return true;
	}

	if (item->IsEquipped())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie mozna przeniesc zalozonego przedmiotu do Switchbota.");
		return true;
	}

	if (!SwitchbotHelper::IsValidItem(item))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Tego przedmiotu nie mozna dodac do Switchbota.");
		return true;
	}

	if ((item->GetVnum() >= 11901 && item->GetVnum() <= 11904) || item->GetVnum() == 50201 || item->GetVnum() == 50202) // wedding items, as by hand
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Tego przedmiotu nie mozna dodac do Switchbota.");
		return true;
	}

	SetSwitchbotItem(ch, DestCell.cell, Cell.cell + 1);
	return true;
}

// input_main.cpp ItemUse: a use (right click) of a switchbot slot takes its item out (Ameria's UseItem).
bool Mt2009SwitchbotItemUse(LPCHARACTER ch, const TItemPos& Cell)
{
	if (!ch || Cell.window_type != SWITCHBOT)
		return false;

	if (!Eligible(ch) || !HasHello(ch) || !ValidPosition(Cell.cell))
		return true;

	if (!ch->CanHandleItem())
		return true;

	CSwitchbot* pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(ch->GetPlayerID());
	if (pkSwitchbot && pkSwitchbot->IsActive(Cell.cell))
	{
		return true;
	}

	SetSwitchbotItem(ch, Cell.cell, 0);
	return true;
}

// char_item.cpp CanEquipNow (Ameria's): an item in a slot cannot be put on.
bool Mt2009SwitchbotRefuseEquip(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || !item->isLocked())
		return false;

	if (CSwitchbotManager::Instance().IsItemIDInSwitchbot(ch->GetPlayerID(), item->GetID()))
		ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw wyjmij przedmiot ze Switchbota.");

	return true;
}

// input_p2p.cpp, HEADER_GG_SWITCHBOT: a running switchbot of a player coming to this core.
void Mt2009SwitchbotP2P(const char* c_pData)
{
	const TPacketGGSwitchbot* p = reinterpret_cast<const TPacketGGSwitchbot*>(c_pData);
	if (p->wPort != mother_port)
		return;

	CSwitchbotManager::Instance().P2PReceiveSwitchbot(p->table);
}

// char.cpp WarpSet / ChangeChannel, before the warp packet (Ameria's).
void Mt2009SwitchbotWarp(LPCHARACTER ch, WORD wPort)
{
	if (!ch || !ch->IsPC())
		return;

	CSwitchbotManager::Instance().SetIsWarping(ch->GetPlayerID(), true);

	if (wPort != mother_port)
	{
		CSwitchbotManager::Instance().P2PSendSwitchbot(ch->GetPlayerID(), wPort);
	}
}

// char.cpp Disconnect (Ameria's ItemSaveSwitchbot): the slots' counters saved; a real logout stops the slots.
void Mt2009SwitchbotDisconnect(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;

	const DWORD pid = ch->GetPlayerID();
	s_setHello.erase(pid);

	auto itData = s_mapPlayerData.find(pid);
	if (itData != s_mapPlayerData.end())
	{
		for (BYTE i = 0; i < SWITCHBOT_SLOT_COUNT; ++i)
			if (itData->second.wCell[i])
				SaveSlot(pid, i);
	}

	CSwitchbot* pkSwitchbot = CSwitchbotManager::Instance().FindSwitchbot(pid);
	if (pkSwitchbot && pkSwitchbot->IsWarping())
	{
		pkSwitchbot->Pause();
		if (itData != s_mapPlayerData.end())
			itData->second.bLoaded = false;
		return;
	}

	CSwitchbotManager::Instance().Remove(pid);
	if (itData != s_mapPlayerData.end())
		s_mapPlayerData.erase(itData);
}

// "/switchbot hello" (root/uiswitchbot.py, after every login and teleport, only with the exe that has the window):
// from now on this client gets the switchbot's packets - Ameria's ItemLoadSwitchbot + CSwitchbotManager::EnterGame.
ACMD(do_switchbot)
{
	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));

	if (!Eligible(ch))
		return;

	if (!strcmp(arg1, "hello"))
	{
		s_setHello.insert(ch->GetPlayerID());
		ItemLoadSwitchbot(ch);
		CSwitchbotManager::Instance().EnterGame(ch);
		return;
	}
}
