// MT2009_PLUS_RELIC_V1: Bonus Reliktu - the owner, 29 October 2026: "Add relics according to the wiki" (pl-wiki "Bonus
// Reliktu" and the pages it links). server-patches/relikty/README.md has the whole picture; the engine's hooks are the
// edits of server-patches/relikty (each declares what it calls, with the same signature as here). Base package:
// "Official Passive Attr System" (Best Studio, github.com/ybeststudio) - its vnums (= the GF client's), its window and
// its two relic pages; the rules and the bonuses are the wiki's, the implementation is ours (no new packet, no new
// item type, no new point: the client talks to it with "/relikt ..." and hears "relikt_state ..." - root/uirelikt.py).
//
// The relic: Relikt Duszy 30272-30276 (one a class, ITEM_QUEST). Placed in the window it leaves the bag for a hidden
// cell of the character - page I or II (MT2009_RELIC_SLOT_START + page, window INVENTORY, cells 436-437 in the DB,
// after the second equipment page's store; never a packet, never a client's cell - as server-patches/addeq's store).
//   socket 0  the time left (seconds; it runs only while the relic is active on the selected page)
//   socket 1  its time (rolled once when it is first placed: 1-12 h - the wiki: "od 1 do 12 godzin, w zaleznosci od
//             czasu trwania Reliktu"); Doladuj fills socket 0 up to it
//   socket 2  flags: 1 active, 2 activated once (then taking it out destroys it - the wiki)
//   attributes 0-3: the relic bonuses (type = the bonus id of playerbot_relikty_table.h, value = x of the wiki) -
//             a relic is never worn, so nothing of the engine reads them as points
// Dodaj: one of each soul (Dusza Miecza 30255, Swiatla 30258, Ochrony 30256, Ozdoby 30257) -> a new random bonus of
// the wiki's sixteen not on the relic yet, its level by weight; at most 4, never changed, not while active.
// Doladuj: the four souls -> the time back to full. Aktywuj / dezaktywuj: the selected page's relic only.
// Only the selected page's relic works (the wiki: "dwa okienka" as the Alchemy's decks).
//
// The bonuses (x = the line's value; "ready" = its cooldown is over, the cooldown starts at every roll):
//   1-4  Wola SungMa WIT / SILA / ODP / INT +15 for x s when hit (120 s)       -> affect 760+id on POINT_SUNGMA_*
//   5    x% when hit: 30 s of picking up the own drops around (300 s)           -> PickupNearbyItems every 2 s
//   6/7  in combat (a blow given / taken in 10 s; on the blow and every tick) with HP / SP not full: the elixir
//        of the sun / moon (300 s, from the refill)                              -> the missing HP / SP at once
//   8    x% when a skill is used: every skill's cooldown reset (120 s)          -> char_skill.cpp (relic reset)
//   9    hitting a Metin: +x% damage against Metins for 5 s (120 s)            -> POINT_ATTBONUS_STONE
//   10   hitting a Metin: +x% defence for 5 s (120 s)                          -> POINT_DEF_BONUS
//   11   mounting: +x% damage for 10 s (120 s)                                 -> POINT_ATT_BONUS
//   12   dismounting: +x movement speed for 10 s (120 s)                        -> POINT_MOV_SPEED
//   13   a boss killed: +x% item drop chance, every kill                        -> item_manager.cpp (relic drop)
//   14   x% on death: no death, 30% HP back (600 s)                             -> char_battle.cpp (relic no death)
//   15   x% hitting a monster: every monster around attacks you (cape, 180 s)  -> AggregateMonster
//   16   x% hitting from a mount: trampling for 20 s (120 s) - a mounted hit stuns a monster (not a boss / Metin,
//        not stun-immune) for 2 s; players are never stunned by it
// Commands (root/uirelikt.py):
//   /relikt hello | page <0|1> | put <cell> | take <page> | add <page> | charge <page> | activate <page>
//   /relikt debug [1]   (GM) the selected page's relic, its bonuses and cooldowns (1: the cooldowns cleared)
// Every proc tells the player in the chat and writes "RELIC_PROC: <name> (<pid>) bonus <id> (<value>)" to the syslog
// (players only).
// Answer: "relikt_state <page> (<vnum> <left> <time> <flags> <type value> x4) x2", "relikt_open".
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "affect.h"
#include "cmd.h"
#include "questmanager.h"

#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "playerbot_relikty_table.h"

namespace
{
	enum
	{
		RELIC_SOCKET_LEFT = 0,
		RELIC_SOCKET_TIME = 1,
		RELIC_SOCKET_FLAGS = 2,
		RELIC_FLAG_ACTIVE = 1,
		RELIC_FLAG_USED = 2,
		RELIC_MAX_BONUS = 4,
		RELIC_MIN_HOURS = 1,
		RELIC_MAX_HOURS = 12,
		RELIC_SAVE_EVERY = 30,		// seconds counted before socket 0 is written again
		RELIC_PICKUP_SECONDS = 30,
		RELIC_TRAMPLE_SECONDS = 20,
		RELIC_TRAMPLE_STUN = 2,
		RELIC_NO_DEATH_HP_PCT = 30,
		RELIC_COMBAT_MS = 10000,	// "in combat": a blow given or taken in the last 10 s (the elixirs, 6 / 7)
		AFFECT_RELIC_FIRST = 760,	// + the bonus id (761-776; free: 720/721 Boss Swiata, 1000+ the quests')
		HEADER_GC_SKILL_COOLTIME_END_RELIC = 73,	// the exe's HEADER_GC_SKILL_COOLTIME_END (as playerbot_bonus67.cpp)
	};

	enum EBonusId
	{
		B_SUNGMA_HP = 1, B_SUNGMA_STR = 2, B_SUNGMA_MOVE = 3, B_SUNGMA_IMMUNE = 4, B_PICKUP = 5, B_SUN = 6, B_MOON = 7,
		B_SKILL_RESET = 8, B_METIN_ATT = 9, B_METIN_DEF = 10, B_MOUNT_ATT = 11, B_DISMOUNT_SPEED = 12, B_BOSS_DROP = 13,
		B_NO_DEATH = 14, B_CAPE = 15, B_TRAMPLE = 16,
	};

	const DWORD RELIC_FIRST = 30272;	// + JOB_*: Wojownik, Ninja, Sura, Szaman, Likan
	const DWORD RELIC_LAST = 30276;
	const DWORD SHARD_FIRST = 30280;
	const DWORD SOULS[4] = { 30255, 30258, 30256, 30257 };	// Miecz, Swiatlo, Ochrona, Ozdoba (the window: up, down, left, right)
	const char* const RELIC_FLAG_PAGE = "relikt.page";

	struct TRuntime
	{
		DWORD adwReady[relic_table::BONUS_NUM + 1];
		DWORD dwPickupUntil;
		DWORD dwTrampleUntil;
		DWORD dwCombatUntil;
		int iPending;		// seconds run, not yet in socket 0
		int iPage;			// the page whose relic iPending belongs to
		int iTicks;
		TRuntime() : dwPickupUntil(0), dwTrampleUntil(0), dwCombatUntil(0), iPending(0), iPage(0), iTicks(0)
		{
			for (int i = 0; i <= relic_table::BONUS_NUM; ++i)
				adwReady[i] = 0;
		}
	};

	std::map<DWORD, TRuntime> s_mapRuntime;		// by PID
	std::set<DWORD> s_setTick;					// PIDs with an active relic
	LPEVENT s_pkTick = NULL;

	bool Reached(DWORD dwNow, DWORD dwAt)
	{
		return (int) (dwNow - dwAt) >= 0;
	}

	const relic_table::TBonus* Bonus(int id)
	{
		for (int i = 0; i < relic_table::BONUS_NUM; ++i)
			if (relic_table::s_aBonus[i].bId == id)
				return &relic_table::s_aBonus[i];
		return NULL;
	}

	bool IsRelic(DWORD dwVnum)
	{
		return dwVnum >= RELIC_FIRST && dwVnum <= RELIC_LAST;
	}

	bool IsBot(LPCHARACTER ch)
	{
		return ch && ch->GetDesc() && ch->GetDesc()->IsBot();
	}

	int Page(LPCHARACTER ch)
	{
		return ch->GetQuestFlag(RELIC_FLAG_PAGE) == 1 ? 1 : 0;
	}

	long Flags(LPITEM relic)
	{
		return relic ? relic->GetSocket(RELIC_SOCKET_FLAGS) : 0;
	}

	int BonusCount(LPITEM relic)
	{
		int n = 0;
		for (int i = 0; i < RELIC_MAX_BONUS; ++i)
			if (relic->GetAttributeType(i))
				++n;
		return n;
	}

	int BonusValue(LPITEM relic, int id)
	{
		for (int i = 0; i < RELIC_MAX_BONUS; ++i)
			if (relic->GetAttributeType(i) == id)
				return relic->GetAttributeValue(i);
		return 0;
	}

	TRuntime& Runtime(LPCHARACTER ch)
	{
		return s_mapRuntime[ch->GetPlayerID()];
	}

	// the relic that works now: the selected page's, active, with time left
	LPITEM ActiveRelic(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return NULL;
		if (!ch->Mt2009RelicGetItem(0) && !ch->Mt2009RelicGetItem(1))
			return NULL;
		LPITEM relic = ch->Mt2009RelicGetItem(Page(ch));
		if (!relic || !(Flags(relic) & RELIC_FLAG_ACTIVE))
			return NULL;
		const long left = relic->GetSocket(RELIC_SOCKET_LEFT) - Runtime(ch).iPending;
		return left > 0 ? relic : NULL;
	}

	// socket 0 takes the seconds run so far
	void FlushTime(LPCHARACTER ch)
	{
		std::map<DWORD, TRuntime>::iterator it = s_mapRuntime.find(ch->GetPlayerID());
		if (it == s_mapRuntime.end() || it->second.iPending <= 0)
			return;
		LPITEM relic = ch->Mt2009RelicGetItem(it->second.iPage);
		if (relic)
			relic->SetSocket(RELIC_SOCKET_LEFT, MAX(0L, relic->GetSocket(RELIC_SOCKET_LEFT) - it->second.iPending), false);
		it->second.iPending = 0;
	}

	// a relic placed the first time: its time (1-12 h) and full
	void InitRelic(LPITEM relic)
	{
		if (relic->GetSocket(RELIC_SOCKET_TIME) > 0)
			return;
		const long lTime = number(RELIC_MIN_HOURS, RELIC_MAX_HOURS) * 3600L;
		relic->SetSocket(RELIC_SOCKET_TIME, lTime, false);
		relic->SetSocket(RELIC_SOCKET_LEFT, lTime, false);
	}

	void SendState(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc() || IsBot(ch))
			return;
		std::ostringstream os;
		os << "relikt_state " << Page(ch);
		for (int page = 0; page < MT2009_RELIC_PAGE_NUM; ++page)
		{
			LPITEM relic = ch->Mt2009RelicGetItem(page);
			if (!relic)
			{
				os << " 0 0 0 0 0 0 0 0 0 0 0 0";
				continue;
			}
			long left = relic->GetSocket(RELIC_SOCKET_LEFT);
			if (page == Page(ch))
				left = MAX(0L, left - Runtime(ch).iPending);
			os << ' ' << relic->GetVnum() << ' ' << left << ' ' << relic->GetSocket(RELIC_SOCKET_TIME) << ' '
				<< Flags(relic);
			for (int i = 0; i < RELIC_MAX_BONUS; ++i)
				os << ' ' << (int) relic->GetAttributeType(i) << ' ' << relic->GetAttributeValue(i);
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "%s", os.str().c_str());
	}

	void Info(LPCHARACTER ch, const char* c_pszText)
	{
		if (ch && ch->GetDesc() && !IsBot(ch))
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", c_pszText);
	}

	// ---- the tick: the time of the active relics, the pick-up line ----
	EVENTINFO(relic_tick_info)
	{
		int iDummy;
		relic_tick_info() : iDummy(0) {}
	};

	void StopTick(LPCHARACTER ch);
	void Elixirs(LPCHARACTER ch, LPITEM relic, DWORD dwNow);

	EVENTFUNC(relic_tick_event)
	{
		const DWORD dwNow = get_dword_time();
		std::vector<DWORD> vecGone;
		for (std::set<DWORD>::const_iterator it = s_setTick.begin(); it != s_setTick.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(*it);
			if (!ch)
			{
				vecGone.push_back(*it);
				continue;
			}
			LPITEM relic = ActiveRelic(ch);
			if (!relic)
			{
				vecGone.push_back(*it);
				continue;
			}
			TRuntime& rt = Runtime(ch);
			if (rt.iPending > 0 && rt.iPage != Page(ch))
				FlushTime(ch);
			rt.iPage = Page(ch);
			++rt.iPending;
			++rt.iTicks;
			const long left = relic->GetSocket(RELIC_SOCKET_LEFT) - rt.iPending;
			if (left <= 0)
			{
				FlushTime(ch);
				relic->SetSocket(RELIC_SOCKET_FLAGS, Flags(relic) & ~RELIC_FLAG_ACTIVE, false);
				Info(ch, "Czas Reliktu Duszy si\xea sko\xf1""czy\xb3 - relikt jest nieaktywny. Do\xb3""aduj go duszami.");
				SendState(ch);
				vecGone.push_back(*it);
				continue;
			}
			if (rt.iPending >= RELIC_SAVE_EVERY)
				FlushTime(ch);
			// bonus 5: the own drops around, every 2 s of the 30
			if (rt.dwPickupUntil && !Reached(dwNow, rt.dwPickupUntil) && (rt.iTicks & 1) == 0 && !ch->IsDead() &&
					ch->CanHandleItem(false, false))
				ch->PickupNearbyItems();
			// bonuses 6 / 7: also between the blows while in combat (HP / SP spent by a skill, a potion's wait)
			if (rt.dwCombatUntil && !Reached(dwNow, rt.dwCombatUntil))
				Elixirs(ch, relic, dwNow);
		}
		for (size_t i = 0; i < vecGone.size(); ++i)
			s_setTick.erase(vecGone[i]);
		if (s_setTick.empty())
		{
			s_pkTick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(1);
	}

	void StartTick(LPCHARACTER ch)
	{
		if (!ActiveRelic(ch))
			return;
		s_setTick.insert(ch->GetPlayerID());
		if (!s_pkTick)
		{
			relic_tick_info* info = AllocEventInfo<relic_tick_info>();
			s_pkTick = event_create(relic_tick_event, info, PASSES_PER_SEC(1));
		}
	}

	void StopTick(LPCHARACTER ch)
	{
		FlushTime(ch);
		s_setTick.erase(ch->GetPlayerID());
	}

	// ---- the bonuses ----
	// the bonus's value when it is ready (and its cooldown started now), else 0
	int Roll(LPCHARACTER ch, LPITEM relic, int id, DWORD dwNow)
	{
		const int iValue = BonusValue(relic, id);
		if (iValue <= 0)
			return 0;
		const relic_table::TBonus* b = Bonus(id);
		if (!b)
			return 0;
		TRuntime& rt = Runtime(ch);
		if (rt.adwReady[id] && !Reached(dwNow, rt.adwReady[id]))
			return 0;
		if (b->iCooldown > 0)
			rt.adwReady[id] = dwNow + b->iCooldown * 1000;
		return iValue;
	}

	bool Chance(int iPct)
	{
		return iPct > 0 && number(1, 100) <= iPct;
	}

	// a bonus that worked: the player's line in the chat (every proc tells it - the 3.0.6 tests: the moon elixir's
	// refill was not seen and taken as "never works") and the syslog (players only: the bots proc all day)
	void Proc(LPCHARACTER ch, int id, int iValue, const char* c_pszText)
	{
		if (!ch || IsBot(ch))
			return;
		if (c_pszText && *c_pszText)
			Info(ch, c_pszText);
		sys_log(0, "RELIC_PROC: %s (%u) bonus %d (%d)", ch->GetName(), ch->GetPlayerID(), id, iValue);
	}

	void Buff(LPCHARACTER ch, int id, int iValue, int iSeconds)
	{
		const relic_table::TBonus* b = Bonus(id);
		if (!b || !b->bPoint || iSeconds <= 0)
			return;
		const int iSize = b->iSize ? b->iSize : iValue;
		ch->AddAffect(AFFECT_RELIC_FIRST + id, b->bPoint, iSize, AFF_NONE, iSeconds, 0, true);
		char szText[160];
		snprintf(szText, sizeof(szText), "Relikt Duszy: %s +%d%s na %d sek.", b->szName, iSize,
				b->bKind == relic_table::KIND_SIZE ? "%" : "", iSeconds);
		Proc(ch, id, iValue, szText);
	}

	// 6 / 7: the elixir of the sun / moon - the missing HP / SP at once, while in combat (a blow given or taken in
	// the last RELIC_COMBAT_MS; the tick checks between the blows) and not full; the cooldown starts when it works
	void Elixirs(LPCHARACTER ch, LPITEM relic, DWORD dwNow)
	{
		if (ch->IsDead() || ch->IsStun())
			return;
		if (ch->GetHP() < ch->GetMaxHP() && BonusValue(relic, B_SUN) > 0 && Roll(ch, relic, B_SUN, dwNow))
		{
			const int iAmount = ch->GetMaxHP() - ch->GetHP();
			ch->PointChange(POINT_HP, iAmount);
			ch->EffectPacket(SE_AUTO_HPUP);
			char szText[128];
			snprintf(szText, sizeof(szText), "Relikt Duszy: efekt Eliksiru S\xb3o\xf1""ca - P\xaf uzupe\xb3nione (+%d).", iAmount);
			Proc(ch, B_SUN, iAmount, szText);
		}
		if (ch->GetSP() < ch->GetMaxSP() && BonusValue(relic, B_MOON) > 0 && Roll(ch, relic, B_MOON, dwNow))
		{
			const int iAmount = ch->GetMaxSP() - ch->GetSP();
			ch->PointChange(POINT_SP, iAmount);
			ch->EffectPacket(SE_AUTO_SPUP);
			char szText[128];
			snprintf(szText, sizeof(szText), "Relikt Duszy: efekt Eliksiru Ksi\xea\xbfyca - PE uzupe\xb3nione (+%d).", iAmount);
			Proc(ch, B_MOON, iAmount, szText);
		}
	}

	bool IsBlow(int iType)
	{
		switch (iType)
		{
			case DAMAGE_TYPE_NORMAL:
			case DAMAGE_TYPE_NORMAL_RANGE:
			case DAMAGE_TYPE_MELEE:
			case DAMAGE_TYPE_RANGE:
			case DAMAGE_TYPE_MAGIC:
			case DAMAGE_TYPE_SPECIAL:
				return true;
		}
		return false;
	}

	bool IsBossMonster(LPCHARACTER ch)
	{
		return ch && ch->IsMonster() && !ch->IsStone() && ch->GetMobRank() >= MOB_RANK_BOSS;
	}

	// ---- the store's actions ----
	bool CanAct(LPCHARACTER ch)
	{
		if (!ch->IsPC() || ch->IsDead())
			return false;
		if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen())
		{
			Info(ch, "Zamknij inne okna, aby u\xbfy\xe6 okna Bonusu Reliktu.");
			return false;
		}
		return true;
	}

	bool TakeSouls(LPCHARACTER ch)
	{
		for (int i = 0; i < 4; ++i)
			if (ch->CountSpecifyItem(SOULS[i]) < 1)
				return false;
		for (int i = 0; i < 4; ++i)
			ch->RemoveSpecifyItem(SOULS[i], 1);
		return true;
	}

	bool HasSouls(LPCHARACTER ch)
	{
		for (int i = 0; i < 4; ++i)
			if (ch->CountSpecifyItem(SOULS[i]) < 1)
				return false;
		return true;
	}

	bool Put(LPCHARACTER ch, LPITEM item, int iPage, bool bQuiet)
	{
		if (!item || !IsRelic(item->GetVnum()) || item->GetOwner() != ch)
			return false;
		if (iPage < 0 || iPage >= MT2009_RELIC_PAGE_NUM)
			return false;
		if (item->IsExchanging() || item->isLocked() || item->IsEquipped())
			return false;
		if ((int) (item->GetVnum() - RELIC_FIRST) != (int) ch->GetJob())
		{
			if (!bQuiet)
				Info(ch, "Ten Relikt Duszy jest dla innej klasy postaci.");
			return false;
		}
		if (ch->Mt2009RelicGetItem(iPage))
		{
			if (!bQuiet)
				Info(ch, "To okienko reliktu jest ju\xbf zaj\xea""te.");
			return false;
		}
		if (iPage == Page(ch))
			StopTick(ch);
		InitRelic(item);
		item->RemoveFromCharacter();
		if (!item->AddToCharacter(ch, TItemPos(INVENTORY, MT2009_RELIC_SLOT_START + iPage)))
		{
			sys_err("RELIC: %s could not put %s (%u) on page %d", ch->GetName(), item->GetName(), item->GetID(), iPage);
			return false;
		}
		sys_log(0, "RELIC: %s (%u) put %s (%u) on page %d", ch->GetName(), ch->GetPlayerID(), item->GetName(), item->GetID(),
				iPage + 1);
		StartTick(ch);
		return true;
	}

	void Take(LPCHARACTER ch, int iPage)
	{
		LPITEM relic = ch->Mt2009RelicGetItem(iPage);
		if (!relic)
			return;
		if (Flags(relic) & RELIC_FLAG_ACTIVE)
		{
			Info(ch, "Najpierw dezaktywuj Relikt Duszy.");
			return;
		}
		if (iPage == Page(ch))
			StopTick(ch);
		if (Flags(relic) & RELIC_FLAG_USED)
		{
			sys_log(0, "RELIC: %s (%u) destroyed %s (%u) taking it out of page %d", ch->GetName(), ch->GetPlayerID(),
					relic->GetName(), relic->GetID(), iPage + 1);
			ITEM_MANAGER::instance().RemoveItem(relic, "RELIC_TAKE_OUT");
			Info(ch, "Relikt Duszy by\xb3 ju\xbf aktywowany - przy wyjmowaniu zosta\xb3 zniszczony.");
			return;
		}
		const int iCell = ch->GetEmptyInventory(relic->GetSize());
		if (iCell < 0)
		{
			Info(ch, "Brak miejsca w ekwipunku.");
			return;
		}
		relic->RemoveFromCharacter();
		relic->AddToCharacter(ch, TItemPos(INVENTORY, iCell));
	}

	// a new bonus of the ones the relic lacks, its level by the table's weights
	bool AddBonus(LPITEM relic, int& rId, int& rValue)
	{
		std::vector<const relic_table::TBonus*> vec;
		for (int i = 0; i < relic_table::BONUS_NUM; ++i)
			if (!BonusValue(relic, relic_table::s_aBonus[i].bId))
				vec.push_back(&relic_table::s_aBonus[i]);
		if (vec.empty())
			return false;
		int iSlot = -1;
		for (int i = 0; i < RELIC_MAX_BONUS && iSlot < 0; ++i)
			if (!relic->GetAttributeType(i))
				iSlot = i;
		if (iSlot < 0)
			return false;
		const relic_table::TBonus* b = vec[number(0, (int) vec.size() - 1)];
		int iTotal = 0;
		for (int i = 0; i < b->iLevels; ++i)
			iTotal += b->asWeight[i];
		int iRoll = number(1, MAX(1, iTotal));
		int iLevel = 0;
		for (; iLevel < b->iLevels - 1; ++iLevel)
		{
			iRoll -= b->asWeight[iLevel];
			if (iRoll <= 0)
				break;
		}
		rId = b->bId;
		rValue = b->asValue[iLevel];
		relic->SetForceAttribute(iSlot, (BYTE) rId, (short) rValue);
		return true;
	}

	void Add(LPCHARACTER ch, int iPage)
	{
		LPITEM relic = ch->Mt2009RelicGetItem(iPage);
		if (!relic)
		{
			Info(ch, "Najpierw umie\x9c\xe6 Relikt Duszy w okienku.");
			return;
		}
		if (Flags(relic) & RELIC_FLAG_ACTIVE)
		{
			Info(ch, "Nie mo\xbfna doda\xe6 bonusu do aktywnego reliktu.");
			return;
		}
		if (BonusCount(relic) >= RELIC_MAX_BONUS)
		{
			Info(ch, "Relikt Duszy ma ju\xbf 4 bonusy.");
			return;
		}
		if (!TakeSouls(ch))
		{
			Info(ch, "Potrzebujesz po jednej Duszy Miecza, Ochrony, Ozdoby i \x8cwiat\xb3""a.");
			return;
		}
		int id = 0, value = 0;
		if (!AddBonus(relic, id, value))
			return;
		const relic_table::TBonus* b = Bonus(id);
		sys_log(0, "RELIC: %s (%u) bonus %d (%d) added to %s (%u)", ch->GetName(), ch->GetPlayerID(), id, value,
				relic->GetName(), relic->GetID());
		if (b)
			ch->ChatPacket(CHAT_TYPE_INFO, "Relikt Duszy: nowy bonus - %s (%d).", b->szName, value);
	}

	void Charge(LPCHARACTER ch, int iPage)
	{
		LPITEM relic = ch->Mt2009RelicGetItem(iPage);
		if (!relic)
		{
			Info(ch, "Najpierw umie\x9c\xe6 Relikt Duszy w okienku.");
			return;
		}
		InitRelic(relic);
		if (iPage == Page(ch))
			FlushTime(ch);
		if (relic->GetSocket(RELIC_SOCKET_LEFT) >= relic->GetSocket(RELIC_SOCKET_TIME))
		{
			Info(ch, "Relikt Duszy jest w pe\xb3ni na\xb3""adowany.");
			return;
		}
		if (!TakeSouls(ch))
		{
			Info(ch, "Potrzebujesz po jednej Duszy Miecza, Ochrony, Ozdoby i \x8cwiat\xb3""a.");
			return;
		}
		relic->SetSocket(RELIC_SOCKET_LEFT, relic->GetSocket(RELIC_SOCKET_TIME));
		Info(ch, "Relikt Duszy zosta\xb3 do\xb3""adowany.");
	}

	void Activate(LPCHARACTER ch, int iPage)
	{
		LPITEM relic = ch->Mt2009RelicGetItem(iPage);
		if (!relic)
			return;
		if (iPage != Page(ch))
		{
			Info(ch, "Aktywowa\xe6 mo\xbfna tylko relikt wybranego okienka.");
			return;
		}
		if (Flags(relic) & RELIC_FLAG_ACTIVE)
		{
			StopTick(ch);
			relic->SetSocket(RELIC_SOCKET_FLAGS, Flags(relic) & ~RELIC_FLAG_ACTIVE, false);
			Info(ch, "Relikt Duszy zosta\xb3 dezaktywowany.");
			return;
		}
		if (BonusCount(relic) <= 0)
		{
			Info(ch, "Relikt Duszy nie ma jeszcze \xbf""adnego bonusu.");
			return;
		}
		if (relic->GetSocket(RELIC_SOCKET_LEFT) <= 0)
		{
			Info(ch, "Relikt Duszy nie ma ju\xbf czasu - do\xb3""aduj go duszami.");
			return;
		}
		relic->SetSocket(RELIC_SOCKET_FLAGS, Flags(relic) | RELIC_FLAG_ACTIVE | RELIC_FLAG_USED, false);
		sys_log(0, "RELIC: %s (%u) activated %s (%u), %ld s left", ch->GetName(), ch->GetPlayerID(), relic->GetName(),
				relic->GetID(), relic->GetSocket(RELIC_SOCKET_LEFT));
		StartTick(ch);
		Info(ch, "Relikt Duszy zosta\xb3 aktywowany.");
	}

	// "/relikt debug [1]" (GM): the selected page's relic, its bonuses and their cooldowns; 1 = the cooldowns cleared
	void Debug(LPCHARACTER ch, bool bReset)
	{
		const DWORD dwNow = get_dword_time();
		TRuntime& rt = Runtime(ch);
		if (bReset)
		{
			for (int i = 0; i <= relic_table::BONUS_NUM; ++i)
				rt.adwReady[i] = 0;
			ch->ChatPacket(CHAT_TYPE_INFO, "Relikt debug: odnowienia wyzerowane.");
		}
		const int iPage = Page(ch);
		LPITEM relic = ch->Mt2009RelicGetItem(iPage);
		if (!relic)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Relikt debug: okienko %s puste.", iPage ? "II" : "I");
			return;
		}
		const long lLeft = relic->GetSocket(RELIC_SOCKET_LEFT) - (rt.iPage == iPage ? rt.iPending : 0);
		ch->ChatPacket(CHAT_TYPE_INFO, "Relikt debug: okienko %s, %s (%u), flagi %ld, czas %ld / %ld s, dzia\xb3""a: %s, tik: %s, "
				"walka: %d s", iPage ? "II" : "I", relic->GetName(), relic->GetVnum(), Flags(relic), lLeft,
				relic->GetSocket(RELIC_SOCKET_TIME), ActiveRelic(ch) ? "tak" : "NIE",
				s_setTick.count(ch->GetPlayerID()) ? "tak" : "nie",
				rt.dwCombatUntil && !Reached(dwNow, rt.dwCombatUntil) ? (int) ((rt.dwCombatUntil - dwNow) / 1000) : 0);
		ch->ChatPacket(CHAT_TYPE_INFO, "Relikt debug: P\xaf %d / %d, PE %d / %d, wierzchowiec: %s", (int) ch->GetHP(),
				(int) ch->GetMaxHP(), (int) ch->GetSP(), (int) ch->GetMaxSP(), ch->IsRiding() ? "tak" : "nie");
		for (int i = 0; i < RELIC_MAX_BONUS; ++i)
		{
			const int id = relic->GetAttributeType(i);
			if (!id)
				continue;
			const relic_table::TBonus* b = Bonus(id);
			int iWait = 0;
			if (id <= relic_table::BONUS_NUM && rt.adwReady[id] && !Reached(dwNow, rt.adwReady[id]))
				iWait = (int) ((rt.adwReady[id] - dwNow + 999) / 1000);
			char szWait[32];
			if (iWait)
				snprintf(szWait, sizeof(szWait), "czeka jeszcze %d s", iWait);
			else
				snprintf(szWait, sizeof(szWait), "gotowy");
			ch->ChatPacket(CHAT_TYPE_INFO, "  #%d %s = %d, odnowienie %d s: %s", id, b ? b->szName : "?",
					relic->GetAttributeValue(i), b ? b->iCooldown : 0, szWait);
		}
	}

	void SetPage(LPCHARACTER ch, int iPage)
	{
		iPage = iPage ? 1 : 0;
		if (iPage == Page(ch))
			return;
		StopTick(ch);
		ch->SetQuestFlag(RELIC_FLAG_PAGE, iPage);
		StartTick(ch);
	}
}

// ---- the store (CHARACTER methods, char.h - server-patches/relikty) ----

LPITEM CHARACTER::Mt2009RelicGetItem(int iPage) const
{
	if (!m_PlayerSlots || iPage < 0 || iPage >= MT2009_RELIC_PAGE_NUM)
		return NULL;
	return m_PlayerSlots->pRelicItems[iPage];
}

// CHARACTER::SetItem of a relic cell (INVENTORY, MT2009_RELIC_SLOT_START..END): no packet - the client never sees it
void CHARACTER::Mt2009RelicSetItem(WORD wCell, LPITEM pItem)
{
	if (!m_PlayerSlots || !Mt2009RelicIsCell(wCell))
		return;

	LPITEM& slot = m_PlayerSlots->pRelicItems[wCell - MT2009_RELIC_SLOT_START];
	if (pItem && slot && slot != pItem)
		sys_err("RELIC: %s cell %u taken by %s (%u), %s (%u) put over it", GetName(), wCell, slot->GetName(), slot->GetID(),
			pItem->GetName(), pItem->GetID());
	slot = pItem;

	if (pItem)
	{
		pItem->SetCell(this, wCell);
		pItem->SetWindow(INVENTORY);
#ifdef ENABLE_ITEM_SAFE_FLUSH
		m_PlayerSlots->setTouchedItems.emplace(pItem->GetID());
#endif
	}
}

void CHARACTER::Mt2009RelicFlushItems()
{
	if (!m_PlayerSlots)
		return;
	FlushTime(this);
	for (LPITEM item : m_PlayerSlots->pRelicItems)
		if (item)
			ITEM_MANAGER::instance().FlushDelayedSave(item);
}

// ClearItem: as the bag's items (the time run so far written first)
void CHARACTER::Mt2009RelicClearItems()
{
	if (!m_PlayerSlots)
		return;
	if (IsPC())
	{
		FlushTime(this);
		s_setTick.erase(GetPlayerID());
	}
	for (size_t i = 0; i < m_PlayerSlots->pRelicItems.size(); ++i)
	{
		LPITEM item = m_PlayerSlots->pRelicItems[i];
		if (!item)
			continue;
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		item->SetSkipSave(true);
		item->RemoveFromCharacter();
		M2_DESTROY_ITEM(item);
		m_PlayerSlots->pRelicItems[i] = NULL;
	}
}

// ---- the engine's hooks (server-patches/relikty) ----

// CHARACTER::UseItemEx: a relic goes into the window (the selected page, else the other free one); -1 not a relic
int Mt2009RelicUseItem(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || !IsRelic(item->GetVnum()))
		return -1;
	if (!CanAct(ch))
		return 0;
	int iPage = Page(ch);
	if (ch->Mt2009RelicGetItem(iPage))
		iPage = 1 - iPage;
	if (ch->Mt2009RelicGetItem(iPage))
	{
		Info(ch, "Oba okienka reliktu s\xb9 zaj\xea""te.");
		if (ch->GetDesc() && !IsBot(ch))
			ch->ChatPacket(CHAT_TYPE_COMMAND, "relikt_open");
		SendState(ch);
		return 0;
	}
	const bool bOk = Put(ch, item, iPage, false);
	SendState(ch);
	if (ch->GetDesc() && !IsBot(ch))
		ch->ChatPacket(CHAT_TYPE_COMMAND, "relikt_open");
	return bOk ? 1 : 0;
}

// CHARACTER::Damage (after the 6th/7th bonuses): the bonuses a blow starts - dam unchanged (the buffs work on the
// next blows, as the wiki's "na x sekund").
int Mt2009RelicOnDamage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iType, int iDam)
{
	if (!pkVictim || !pkAttacker || iDam <= 0 || !IsBlow(iType))
		return iDam;
	const DWORD dwNow = get_dword_time();

	// the one hit
	if (pkVictim->IsPC())
	{
		LPITEM relic = ActiveRelic(pkVictim);
		if (relic)
		{
			StartTick(pkVictim);
			Runtime(pkVictim).dwCombatUntil = dwNow + RELIC_COMBAT_MS;
			static const int s_aiSungma[4] = { B_SUNGMA_HP, B_SUNGMA_STR, B_SUNGMA_MOVE, B_SUNGMA_IMMUNE };
			for (int i = 0; i < 4; ++i)
			{
				const int iSec = Roll(pkVictim, relic, s_aiSungma[i], dwNow);
				if (iSec > 0)
					Buff(pkVictim, s_aiSungma[i], 15, iSec);
			}
			const int iPickup = Roll(pkVictim, relic, B_PICKUP, dwNow);
			if (Chance(iPickup))
			{
				Runtime(pkVictim).dwPickupUntil = dwNow + RELIC_PICKUP_SECONDS * 1000;
				Proc(pkVictim, B_PICKUP, iPickup, "Relikt Duszy: przez 30 sek. zbierasz automatycznie przedmioty w pobli\xbfu.");
			}
			Elixirs(pkVictim, relic, dwNow);
		}
	}

	// the one hitting
	if (pkAttacker->IsPC() && pkVictim != pkAttacker)
	{
		LPITEM relic = ActiveRelic(pkAttacker);
		if (relic)
		{
			StartTick(pkAttacker);
			Runtime(pkAttacker).dwCombatUntil = dwNow + RELIC_COMBAT_MS;
			Elixirs(pkAttacker, relic, dwNow);
			if (pkVictim->IsStone())
			{
				const int iAtt = Roll(pkAttacker, relic, B_METIN_ATT, dwNow);
				if (iAtt > 0)
					Buff(pkAttacker, B_METIN_ATT, iAtt, Bonus(B_METIN_ATT)->iEffect);
				const int iDef = Roll(pkAttacker, relic, B_METIN_DEF, dwNow);
				if (iDef > 0)
					Buff(pkAttacker, B_METIN_DEF, iDef, Bonus(B_METIN_DEF)->iEffect);
			}
			else if (pkVictim->IsMonster())
			{
				const int iCape = Roll(pkAttacker, relic, B_CAPE, dwNow);
				if (Chance(iCape))
				{
					pkAttacker->AggregateMonster();
					Proc(pkAttacker, B_CAPE, iCape, "Relikt Duszy: potwory wok\xf3\xb3 ruszaj\xb9 na ciebie.");
				}
			}
			if (pkAttacker->IsRiding())
			{
				TRuntime& rt = Runtime(pkAttacker);
				const int iTrample = Roll(pkAttacker, relic, B_TRAMPLE, dwNow);
				if (Chance(iTrample))
				{
					rt.dwTrampleUntil = dwNow + RELIC_TRAMPLE_SECONDS * 1000;
					Proc(pkAttacker, B_TRAMPLE, iTrample, "Relikt Duszy: przez 20 sek. tratujesz przeciwnik\xf3w.");
				}
				if (rt.dwTrampleUntil && !Reached(dwNow, rt.dwTrampleUntil) && pkVictim->IsMonster() &&
						!IsBossMonster(pkVictim) && !pkVictim->IsDead() && !pkVictim->IsAffectFlag(AFF_STUN) &&
						!pkVictim->IsImmune(IMMUNE_STUN))
					pkVictim->AddAffect(AFFECT_STUN, POINT_NONE, 0, AFF_STUN, RELIC_TRAMPLE_STUN, 0, true);
			}
		}
	}
	return iDam;
}

// CHARACTER::Damage, HP at 0 before the stun of death: true = the death is undone (30% HP back)
bool Mt2009RelicNoDeath(LPCHARACTER ch, LPCHARACTER pkAttacker)
{
	if (!ch || !ch->IsPC())
		return false;
	LPITEM relic = ActiveRelic(ch);
	if (!relic)
		return false;
	const int iPct = Roll(ch, relic, B_NO_DEATH, get_dword_time());
	if (!Chance(iPct))
		return false;
	const int iHp = MAX(1, ch->GetMaxHP() * RELIC_NO_DEATH_HP_PCT / 100);
	ch->PointChange(POINT_HP, iHp - ch->GetHP());
	ch->EffectPacket(SE_AUTO_HPUP);
	Proc(ch, B_NO_DEATH, iPct, "Relikt Duszy uchroni\xb3 ci\xea przed \x9cmierci\xb9.");
	sys_log(0, "RELIC: %s (%u) escaped death (%s)", ch->GetName(), ch->GetPlayerID(), pkAttacker ? pkAttacker->GetName() : "-");
	return true;
}

// CHARACTER::UseSkill (after the cooldown is set): true = every skill's cooldown is reset (the engine clears them and
// ends the client's with Mt2009RelicCooltimeEnd)
bool Mt2009RelicSkillReset(LPCHARACTER ch, unsigned int dwVnum)
{
	if (!ch || !ch->IsPC())
		return false;
	LPITEM relic = ActiveRelic(ch);
	if (!relic)
		return false;
	const int iPct = Roll(ch, relic, B_SKILL_RESET, get_dword_time());
	if (!Chance(iPct))
		return false;
	Proc(ch, B_SKILL_RESET, iPct, "Relikt Duszy: czas odnowienia umiej\xeatno\x9c""ci zresetowany.");
	return true;
}

#pragma pack(push, 1)
struct TPacketGCSkillCoolTimeEndRelic
{
	BYTE header;
	BYTE bSkill;
};
#pragma pack(pop)

void Mt2009RelicCooltimeEnd(LPCHARACTER ch, int iSkill)
{
	if (!ch || !ch->GetDesc() || IsBot(ch) || iSkill <= 0 || iSkill > 255)
		return;
	TPacketGCSkillCoolTimeEndRelic p;
	p.header = HEADER_GC_SKILL_COOLTIME_END_RELIC;
	p.bSkill = (BYTE) iSkill;
	ch->GetDesc()->Packet(&p, sizeof(p));
}

// ITEM_MANAGER::GetDropPct: a boss killed - "+x% to the drop" of the killer's relic (every kill, no cooldown)
int Mt2009RelicBossDropBonus(LPCHARACTER pkKiller, unsigned char bMobRank, bool bStone)
{
	if (!pkKiller || !pkKiller->IsPC() || bStone || bMobRank < MOB_RANK_BOSS)
		return 0;
	LPITEM relic = ActiveRelic(pkKiller);
	return relic ? BonusValue(relic, B_BOSS_DROP) : 0;
}

// CHARACTER::MountVnum: on a mount (bMount) / off it
void Mt2009RelicOnMount(LPCHARACTER ch, bool bMount)
{
	if (!ch || !ch->IsPC())
		return;
	LPITEM relic = ActiveRelic(ch);
	if (!relic)
		return;
	const DWORD dwNow = get_dword_time();
	if (bMount)
	{
		const int iAtt = Roll(ch, relic, B_MOUNT_ATT, dwNow);
		if (iAtt > 0)
			Buff(ch, B_MOUNT_ATT, iAtt, Bonus(B_MOUNT_ATT)->iEffect);
	}
	else
	{
		const int iSpeed = Roll(ch, relic, B_DISMOUNT_SPEED, dwNow);
		if (iSpeed > 0)
			Buff(ch, B_DISMOUNT_SPEED, iSpeed, Bonus(B_DISMOUNT_SPEED)->iEffect);
		Runtime(ch).dwTrampleUntil = 0;
	}
}

ACMD(do_relikt)
{
	if (!ch || !ch->GetDesc() || IsBot(ch) || !ch->IsPC())
		return;

	std::istringstream is(argument ? argument : "");
	std::string sub;
	int a = -1;
	is >> sub;
	is >> a;

	if (sub == "hello" || sub.empty())
	{
		StartTick(ch);
		SendState(ch);
		return;
	}
	if (sub == "page")
	{
		SetPage(ch, a);
		SendState(ch);
		return;
	}
	if (sub == "debug")
	{
		if (ch->GetGMLevel() > GM_PLAYER)
			Debug(ch, a == 1);
		return;
	}
	if (!CanAct(ch))
	{
		SendState(ch);
		return;
	}
	if (sub == "put")
	{
		if (a >= 0 && a < INVENTORY_MAX_NUM)
		{
			int iPage = -1;
			is >> iPage;
			Put(ch, ch->GetInventoryItem(a), iPage >= 0 ? iPage : Page(ch), false);
		}
	}
	else if (a < 0 || a >= MT2009_RELIC_PAGE_NUM)
		;
	else if (sub == "take")
		Take(ch, a);
	else if (sub == "add")
		Add(ch, a);
	else if (sub == "charge")
		Charge(ch, a);
	else if (sub == "activate")
		Activate(ch, a);
	SendState(ch);
}

// ---- the bots (playerbot_manager.cpp: the tick beside the shop aids; playerbot_shop_aids.h: the V3 goal) ----
// A bot of level 120 on the new continent does the missions as a player does (their dailies: a shard and each soul,
// 60% a day; the first shard 100%), makes its relic at once, puts it on page I, adds bonuses with the souls it has
// and asks the ItemShop V3 for the missing ones (a goal, never urgent), activates it with four bonuses and charges
// it when its time is over.
namespace
{
	const int BOT_RELIC_LEVEL = 120;
	const DWORD BOT_RELIC_STEP_MS = 5 * 60 * 1000;
	const int BOT_RELIC_DAY = 24 * 60 * 60;
	const int BOT_RELIC_DAILY_PCT = 60;
	const char* const BOT_RELIC_DAY_FLAG = "relikt.bot_day";
	const char* const BOT_RELIC_FIRST_FLAG = "relikt.bot_first";
	std::map<DWORD, DWORD> s_mapBotNext;

	bool BotOnYohara(LPCHARACTER ch)
	{
		long idx = ch->GetMapIndex();
		if (idx >= 10000)
			idx /= 10000;
		return (idx >= 373 && idx <= 391 && idx != 375 && idx != 392) || (idx >= 393 && idx <= 396);
	}

	LPITEM BotBagRelic(LPCHARACTER ch)
	{
		const DWORD dwVnum = RELIC_FIRST + ch->GetJob();
		for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = ch->GetInventoryItem(i);
			if (item && item->GetVnum() == dwVnum && !item->IsExchanging() && !item->isLocked())
				return item;
		}
		return NULL;
	}
}

void Mt2009RelicBotTick(LPCHARACTER ch, DWORD dwNow)
{
	if (!ch || !ch->IsPC() || !IsBot(ch) || ch->GetLevel() < BOT_RELIC_LEVEL || ch->IsDead())
		return;
	if (quest::CQuestManager::instance().GetEventFlag("m2_bot_relic_off"))
		return;
	DWORD& next = s_mapBotNext[ch->GetPlayerID()];
	if (next && !Reached(dwNow, next))
		return;
	next = dwNow + BOT_RELIC_STEP_MS + number(0, 60000);

	// the dailies of Dongan (a shard; each soul) - where the players do them
	const int iNow = get_global_time();
	if (BotOnYohara(ch) && iNow - ch->GetQuestFlag(BOT_RELIC_DAY_FLAG) >= BOT_RELIC_DAY)
	{
		ch->SetQuestFlag(BOT_RELIC_DAY_FLAG, iNow);
		const bool bFirst = ch->GetQuestFlag(BOT_RELIC_FIRST_FLAG) == 0;
		ch->SetQuestFlag(BOT_RELIC_FIRST_FLAG, 1);
		if (bFirst || number(1, 100) <= BOT_RELIC_DAILY_PCT)
			ch->AutoGiveItem(SHARD_FIRST + ch->GetJob(), 1, -1, false);
		for (int i = 0; i < 4; ++i)
			if (bFirst || number(1, 100) <= BOT_RELIC_DAILY_PCT)
				ch->AutoGiveItem(SOULS[i], 1, -1, false);
	}

	// Chaegirab: a relic of a shard, when the bot has none
	const DWORD dwShard = SHARD_FIRST + ch->GetJob();
	if (!ch->Mt2009RelicGetItem(0) && !ch->Mt2009RelicGetItem(1) && !BotBagRelic(ch) && ch->CountSpecifyItem(dwShard) > 0 &&
			ch->GetEmptyInventory(1) >= 0)
	{
		ch->RemoveSpecifyItem(dwShard, 1);
		ch->AutoGiveItem(RELIC_FIRST + ch->GetJob(), 1, -1, false);
		sys_log(0, "RELIC_BOT: %s (%u) made its relic", ch->GetName(), ch->GetPlayerID());
	}

	// page I
	if (Page(ch) != 0)
		SetPage(ch, 0);
	if (!ch->Mt2009RelicGetItem(0))
	{
		LPITEM bag = BotBagRelic(ch);
		if (bag)
			Put(ch, bag, 0, true);
	}
	LPITEM relic = ch->Mt2009RelicGetItem(0);
	if (!relic)
		return;

	const bool bActive = (Flags(relic) & RELIC_FLAG_ACTIVE) != 0;
	if (!bActive)
	{
		while (BonusCount(relic) < RELIC_MAX_BONUS && HasSouls(ch))
		{
			int id = 0, value = 0;
			if (!TakeSouls(ch) || !AddBonus(relic, id, value))
				break;
			sys_log(0, "RELIC_BOT: %s (%u) bonus %d (%d)", ch->GetName(), ch->GetPlayerID(), id, value);
		}
		if (BonusCount(relic) >= RELIC_MAX_BONUS)
		{
			InitRelic(relic);
			if (relic->GetSocket(RELIC_SOCKET_LEFT) <= 0 && TakeSouls(ch))
				relic->SetSocket(RELIC_SOCKET_LEFT, relic->GetSocket(RELIC_SOCKET_TIME));
			if (relic->GetSocket(RELIC_SOCKET_LEFT) > 0)
			{
				relic->SetSocket(RELIC_SOCKET_FLAGS, Flags(relic) | RELIC_FLAG_ACTIVE | RELIC_FLAG_USED, false);
				StartTick(ch);
				sys_log(0, "RELIC_BOT: %s (%u) activated its relic", ch->GetName(), ch->GetPlayerID());
			}
		}
	}
	else
		StartTick(ch);
}

// playerbot_economy.h IsPlayerBotJunkItem / playerbot_town.h ScorePlayerBotShopStockRules: a bot never sells or stalls the
// souls (30255-30258), Pakiet Dusz (30263), relics (30272-30276) and shards (30280-30284)
bool Mt2009RelicIsKeptVnum(DWORD dwVnum)
{
	return (dwVnum >= SOULS[0] && dwVnum <= 30258) || dwVnum == 30263 || IsRelic(dwVnum) ||
		(dwVnum >= SHARD_FIRST && dwVnum < SHARD_FIRST + 5);
}

// the ItemShop V3 goal: the first soul missing for the bot's next step (a bonus to add, or a charge) - 1 piece
int Mt2009RelicBotSoulNeed(LPCHARACTER ch, DWORD& dwVnum)
{
	dwVnum = 0;
	if (!ch || !IsBot(ch) || ch->GetLevel() < BOT_RELIC_LEVEL)
		return 0;
	if (quest::CQuestManager::instance().GetEventFlag("m2_bot_relic_off"))
		return 0;
	LPITEM relic = ch->Mt2009RelicGetItem(0);
	if (!relic)
		return 0;
	const bool bActive = (Flags(relic) & RELIC_FLAG_ACTIVE) != 0;
	const bool bWants = !bActive && (BonusCount(relic) < RELIC_MAX_BONUS || relic->GetSocket(RELIC_SOCKET_LEFT) <= 0);
	if (!bWants)
		return 0;
	for (int i = 0; i < 4; ++i)
	{
		if (ch->CountSpecifyItem(SOULS[i]) < 1)
		{
			dwVnum = SOULS[i];
			return 1;
		}
	}
	return 0;
}
