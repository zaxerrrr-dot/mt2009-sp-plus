// MT2009_PLUS_WEAPON_ELEMENT_V1 - Zaczarowanie Zywiolu Broni (the owner, 29 October 2026; server-patches/zywiolbroni,
// README.md). Based on the "[System] Elemental Spell" package (WorldArd), rewritten for our engine; the change window
// and the graphics are the GF client's.
//
// pl-wiki "Zaczarowanie Zywiolu Broni": a scroll of an element (56002-56007, Straznik Medali) dragged onto a weapon
// refined to +7 or more (sword, two-handed, dagger, bow, bell, fan, claw) gives it that element or raises its level,
// up to +3, only with the same element; each level adds a random Sila Zywiolu (POINT_ENCHANT_ELECT..DARK 178-183 - the
// talismans' points, the same formula) and a random Wartosc Ataku (added to the attack as the weapon's value5 is,
// battle.cpp); an attempt may fail (the scroll and the fee go, the weapon stays). Zwoj Klatwy (56008) lowers the level
// by 1, Zwoj Zmiany (56009) changes the element keeping the level and the values - both always work. The effect: +3 on
// a weapon with its "stars" (and, transmuted, only when the look's weapon has them too).
//
// Everything is checked here on the server (the package trusted the client - the analysis' 16 bugs): the weapon and
// the scroll are remembered by their ITEM IDS when the scroll is dragged (char_item.cpp UseItemEx), the client only
// says "/welem ok|change <type>|close"; at the confirmation both are looked up again (still the player's, in the
// inventory, not worn, not in a trade) and every rule is checked again before the Yang and the scroll are taken.
//
// The data: player.item_element (id -> element, level, the values each level rolled; zywiol_broni.sql), read when a
// weapon / sash is loaded (ITEM_MANAGER::CreateItem), written when it changes; player.item and the item packets are not
// touched (as ysets' item_yextra). The client hears it by "WELEM <window> <cell> <packed>" (1 inventory / equipment,
// 3 storehouse, 4 / 5 the trade's own / other side; 0 = forget all; cell -1 = forget the window):
//   packed: bits 0-2 the element (1 Blyskawica, 2 Ogien, 3 Lod, 4 Wiatr, 5 Ziemia, 6 Mrok = point 177 + element),
//   bits 3-4 the level, level i (0..2): the attack value in bits 8+8i..11+8i, the power in bits 12+8i..15+8i.
// The windows: "WELEMOPEN <mode> <weapon cell> <scroll cell> <fee> <element> <new level> <packed> <att min> <att max>
// <pow min> <pow max>" (mode 1 add / raise, 2 curse, 3 change), "WELEMCLOSE", "WELEMRESULT <mode> <ok> <element>".
// The effect the others see: "WELEMFX <vid> <element>" (0 none) - the 3.x exe's chrmgr draws it (root/welemfx.py).
//
// Every number is game/zywiolbroni/weapon_element.txt's (locale/poland/weapon_element.txt; "/welem_reload").
// Bots do not use the system (the owner): a bot's use, buy and confirmation are refused.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "db.h"
#include "log.h"
#include "guild.h"
#include "packet.h"
#include "buffer_manager.h"
#include "locale_service.h"
#include "exchange.h"
#include "utils.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace welem
{
	enum
	{
		MAX_GRADE = 3,
		SCROLL_FIRST = 56002,	// 56002-56007 the elements
		SCROLL_LAST_ELEMENT = 56007,
		SCROLL_CURSE = 56008,
		SCROLL_CHANGE = 56009,
		MODE_UPGRADE = 1,
		MODE_CURSE = 2,
		MODE_CHANGE = 3,
		POINT_FIRST = 178,		// POINT_ENCHANT_ELECT; element t -> point 177 + t
	};

	// the element of each element scroll (by the official vnums; value0 of the proto is the point and wins when valid)
	static const BYTE s_abScrollElement[6] = { 2, 3, 1, 4, 5, 6 };	// 56002 Ognia .. 56007 Mroku
	static const char* s_aszName[7] = { "", "B\263yskawica", "Ogie\361", "L\363d", "Wiatr", "Ziemia", "Mrok" };
	static const char* s_aszPower[7] = { "", "Si\263a B\263yskawic", "Si\263a Ognia", "Si\263a Lodu", "Si\263a Wiatru",
			"Si\263a Ziemi", "Si\263a Mroku" };

	struct TData
	{
		BYTE type;
		BYTE grade;
		BYTE att[MAX_GRADE];
		BYTE pow[MAX_GRADE];
	};

	struct TConfig
	{
		bool loaded;
		bool enabled;
		long long priceElement, priceCurse, priceChange;
		long long feeElement, feeCurse, feeChange;
		int guildElement, guildSpecial;
		int minRefine;
		int chance[MAX_GRADE];
		int effectGrade;
		std::vector<std::pair<int, int> > power[MAX_GRADE];	// (value, weight)
		std::vector<std::pair<int, int> > attack[MAX_GRADE];
	};

	struct TPending
	{
		BYTE mode;
		DWORD weaponId;
		DWORD scrollId;
		DWORD scrollVnum;
	};

	static std::map<DWORD, TData> s_mapData;		// item id -> its enchant (only items that have one)
	static std::map<DWORD, TPending> s_mapPending;	// player id -> the window it has open
	static std::map<DWORD, BYTE> s_mapShown;		// vid -> the effect the others were told
	static TConfig s_cfg;

	// --- the config -----------------------------------------------------------------------------------------------
	static void Defaults(TConfig& c)
	{
		c.enabled = true;
		c.priceElement = 9000000; c.priceCurse = 10000000; c.priceChange = 30000000;
		c.feeElement = 3000000; c.feeCurse = 0; c.feeChange = 10000000;
		c.guildElement = 21; c.guildSpecial = 24;
		c.minRefine = 7;
		c.effectGrade = 3;
		static const int aPow[MAX_GRADE][5][2] = {
			{ { 1, 30 }, { 2, 40 }, { 4, 18 }, { 6, 8 }, { 8, 4 } },
			{ { 1, 20 }, { 2, 25 }, { 4, 35 }, { 6, 14 }, { 8, 6 } },
			{ { 1, 12 }, { 2, 18 }, { 4, 25 }, { 6, 35 }, { 8, 10 } } };
		static const int aAtt[MAX_GRADE][5][2] = {
			{ { 2, 30 }, { 4, 40 }, { 6, 18 }, { 8, 8 }, { 12, 4 } },
			{ { 2, 20 }, { 4, 25 }, { 6, 35 }, { 8, 14 }, { 12, 6 } },
			{ { 2, 12 }, { 4, 18 }, { 6, 25 }, { 8, 35 }, { 12, 10 } } };
		for (int g = 0; g < MAX_GRADE; ++g)
		{
			c.chance[g] = 50;
			c.power[g].clear();
			c.attack[g].clear();
			for (int i = 0; i < 5; ++i)
			{
				c.power[g].push_back(std::make_pair(aPow[g][i][0], aPow[g][i][1]));
				c.attack[g].push_back(std::make_pair(aAtt[g][i][0], aAtt[g][i][1]));
			}
		}
	}

	static bool ReadTable(std::istringstream& in, std::vector<std::pair<int, int> >& out)
	{
		std::vector<std::pair<int, int> > v;
		std::string tok;
		while (in >> tok)
		{
			int value = 0, weight = 0;
			if (sscanf(tok.c_str(), "%d:%d", &value, &weight) != 2 || value < 1 || value > 15 || weight < 0)
				return false;
			if (weight > 0)
				v.push_back(std::make_pair(value, weight));
		}
		if (v.empty())
			return false;
		out.swap(v);
		return true;
	}

	static int Load(std::string* pReport = NULL)
	{
		TConfig c;
		Defaults(c);
		const std::string path = LocaleService_GetBasePath() + "/weapon_element.txt";
		std::ifstream f(path.c_str());
		int lines = 0, bad = 0;
		std::string line;
		while (f && std::getline(f, line))
		{
			const size_t hash = line.find('#');
			if (hash != std::string::npos)
				line.erase(hash);
			std::istringstream in(line);
			std::string key;
			if (!(in >> key))
				continue;
			++lines;
			long long v = 0;
			bool ok = true;
			if (key == "power" || key == "attack")
			{
				int g = 0;
				ok = (in >> g) && g >= 1 && g <= MAX_GRADE && ReadTable(in, key == "power" ? c.power[g - 1] : c.attack[g - 1]);
			}
			else if (key == "chance")
			{
				for (int g = 0; g < MAX_GRADE && ok; ++g)
					ok = (in >> c.chance[g]) && c.chance[g] >= 0 && c.chance[g] <= 100;
			}
			else if (!(in >> v) || v < 0)
				ok = false;
			else if (key == "enabled") c.enabled = v != 0;
			else if (key == "price_element") c.priceElement = v;
			else if (key == "price_curse") c.priceCurse = v;
			else if (key == "price_change") c.priceChange = v;
			else if (key == "fee_element") c.feeElement = v;
			else if (key == "fee_curse") c.feeCurse = v;
			else if (key == "fee_change") c.feeChange = v;
			else if (key == "guild_level_element") c.guildElement = (int) v;
			else if (key == "guild_level_special") c.guildSpecial = (int) v;
			else if (key == "min_refine") c.minRefine = (int) v;
			else if (key == "effect_grade") c.effectGrade = (int) v;
			else
				ok = false;
			if (!ok)
			{
				++bad;
				sys_err("WEAPON_ELEMENT: %s: a bad line: %s", path.c_str(), line.c_str());
			}
		}
		c.loaded = true;
		s_cfg = c;
		sys_log(0, "WEAPON_ELEMENT: %s - %d line(s), %d bad; %s, chance %d/%d/%d, fees %lld/%lld/%lld, scrolls %lld/%lld/%lld",
				path.c_str(), lines, bad, c.enabled ? "on" : "OFF", c.chance[0], c.chance[1], c.chance[2],
				c.feeElement, c.feeCurse, c.feeChange, c.priceElement, c.priceCurse, c.priceChange);
		if (pReport)
		{
			char buf[256];
			snprintf(buf, sizeof(buf), "weapon_element.txt: %d linii, %d b\263\352dnych; %s, szansa %d/%d/%d%%",
					lines, bad, c.enabled ? "w\263\261czone" : "WY\243\244CZONE", c.chance[0], c.chance[1], c.chance[2]);
			*pReport = buf;
		}
		return bad;
	}

	static const TConfig& Cfg()
	{
		if (!s_cfg.loaded)
			Load();
		return s_cfg;
	}

	static int Roll(const std::vector<std::pair<int, int> >& table)
	{
		int sum = 0;
		for (size_t i = 0; i < table.size(); ++i)
			sum += table[i].second;
		if (sum <= 0)
			return table.empty() ? 1 : table[0].first;
		int r = number(1, sum);
		for (size_t i = 0; i < table.size(); ++i)
		{
			r -= table[i].second;
			if (r <= 0)
				return table[i].first;
		}
		return table.back().first;
	}

	static void Range(const std::vector<std::pair<int, int> >& table, int& lo, int& hi)
	{
		lo = hi = 0;
		for (size_t i = 0; i < table.size(); ++i)
		{
			if (!lo || table[i].first < lo) lo = table[i].first;
			if (table[i].first > hi) hi = table[i].first;
		}
	}

	// --- the items ------------------------------------------------------------------------------------------------
	static bool IsEnchantableWeapon(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_WEAPON)
			return false;
		switch (item->GetSubType())
		{
			case WEAPON_SWORD:
			case WEAPON_DAGGER:
			case WEAPON_BOW:
			case WEAPON_TWO_HANDED:
			case WEAPON_BELL:
			case WEAPON_FAN:
#ifdef ENABLE_WOLFMAN_CHARACTER
			case WEAPON_CLAW:
#endif
				return true;
		}
		return false;
	}

	static bool IsSash(LPITEM item)
	{
		return item && item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_ACCE;
	}

	static const TData* Find(LPITEM item)
	{
		if (!item || !item->GetID())
			return NULL;
		std::map<DWORD, TData>::const_iterator it = s_mapData.find(item->GetID());
		return it == s_mapData.end() ? NULL : &it->second;
	}

	static DWORD Pack(const TData* d)
	{
		if (!d || !d->type || !d->grade)
			return 0;
		DWORD p = (d->type & 7) | ((d->grade & 3) << 3);
		for (int i = 0; i < MAX_GRADE && i < d->grade; ++i)
			p |= (DWORD) ((d->att[i] & 15) | ((d->pow[i] & 15) << 4)) << (8 + 8 * i);
		return p;
	}

	static void Sums(const TData* d, int& att, int& pow)
	{
		att = pow = 0;
		for (int i = 0; d && i < d->grade && i < MAX_GRADE; ++i)
		{
			att += d->att[i];
			pow += d->pow[i];
		}
	}

	static void Save(DWORD id, const TData* d)
	{
		if (!id)
			return;
		if (d && d->type && d->grade)
			DBManager::instance().DirectQuery("REPLACE INTO item_element (id, type, grade, att0, att1, att2, pow0, pow1, pow2) "
					"VALUES (%u, %u, %u, %u, %u, %u, %u, %u, %u)", id, d->type, d->grade, d->att[0], d->att[1], d->att[2],
					d->pow[0], d->pow[1], d->pow[2]);
		else
			DBManager::instance().DirectQuery("DELETE FROM item_element WHERE id = %u", id);
	}

	static void Notify(LPCHARACTER ch, int window, int cell, DWORD packed)
	{
		if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsPhase(PHASE_GAME) || ch->GetDesc()->IsBot())
			return;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WELEM %d %d %u", window, cell, packed);
	}

	static void NotifyItem(LPITEM item)
	{
		LPCHARACTER owner = item ? item->GetOwner() : NULL;
		if (owner && (item->GetWindow() == INVENTORY || item->GetWindow() == EQUIPMENT))
			Notify(owner, 1, item->GetCell(), Pack(Find(item)));
	}

	// a change of the data of an item; one worn has its points taken off and given again
	static void Set(LPITEM item, const TData* d)
	{
		if (!item || !item->GetID())
			return;
		LPCHARACTER owner = item->GetOwner();
		const bool worn = owner && item->IsEquipped();
		if (worn)
			item->ModifyPoints(false);
		if (d && d->type && d->grade)
			s_mapData[item->GetID()] = *d;
		else
			s_mapData.erase(item->GetID());
		if (worn)
		{
			item->ModifyPoints(true);
			owner->ComputeBattlePoints();
			owner->UpdatePacket();
		}
		Save(item->GetID(), d);
		NotifyItem(item);
	}

	// --- the effect (wiki): +3 and the weapon's "stars" -------------------------------------------------------------
	static int RefineOf(const TItemTable* t)
	{
		if (!t)
			return 0;
		const char* p = strrchr(t->szName, '+');
		if (!p)
			p = strrchr(t->szLocaleName, '+');
		return p ? atoi(p + 1) : 0;
	}

	static bool HasStars(DWORD vnum)
	{
		const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnum);
		if (!t || t->bType != ITEM_WEAPON)
			return false;
		int level = 0;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (t->aLimits[i].bType == LIMIT_LEVEL)
				level = t->aLimits[i].lValue;
		int need = level < 30 ? 9 : (level < 45 ? 8 : 7);
		if (vnum >= 5110 && vnum <= 5119)	// Antyczny Dzwon: from +7 (wiki)
			need = 7;
		return RefineOf(t) >= need;
	}

	static BYTE ShownType(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return 0;
		LPITEM w = ch->GetWear(WEAR_WEAPON);
		const TData* d = Find(w);
		if (!d || d->grade < Cfg().effectGrade || !IsEnchantableWeapon(w))
			return 0;
		if (!HasStars(w->GetVnum()))
			return 0;
		if (w->GetTransmutation() && !HasStars(w->GetTransmutation()))	// wiki case 2: the look's weapon without stars
			return 0;
		return d->type;
	}

	static void SendAround(LPCHARACTER ch, BYTE type)
	{
		if (!ch->GetSectree())
			return;
		char command[64];
		int len = snprintf(command, sizeof(command), "WELEMFX %u %u", (unsigned int) ch->GetVID(), (unsigned int) type);
		if (len <= 0 || len >= (int) sizeof(command))
			return;
		++len;	// the trailing NUL every chat packet carries
		TPacketGCChat pack;
		pack.header = HEADER_GC_CHAT;
		pack.size = sizeof(TPacketGCChat) + len;
		pack.type = CHAT_TYPE_COMMAND;
		pack.id = 0;
		pack.bEmpire = 0;
		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(TPacketGCChat));
		buf.write(command, len);
		ch->PacketAround(buf.read_peek(), buf.size());
	}

	// --- the rules ------------------------------------------------------------------------------------------------
	static BYTE ScrollElement(LPITEM scroll)
	{
		const long v0 = scroll->GetValue(0);
		if (v0 >= POINT_FIRST && v0 < POINT_FIRST + 6)
			return (BYTE) (v0 - POINT_FIRST + 1);
		return s_abScrollElement[scroll->GetVnum() - SCROLL_FIRST];
	}

	static BYTE ModeOf(DWORD vnum)
	{
		if (vnum >= SCROLL_FIRST && vnum <= SCROLL_LAST_ELEMENT)
			return MODE_UPGRADE;
		if (vnum == SCROLL_CURSE)
			return MODE_CURSE;
		if (vnum == SCROLL_CHANGE)
			return MODE_CHANGE;
		return 0;
	}

	static long long FeeOf(BYTE mode)
	{
		const TConfig& c = Cfg();
		return mode == MODE_UPGRADE ? c.feeElement : (mode == MODE_CURSE ? c.feeCurse : c.feeChange);
	}

	// NULL when the scroll may work on the weapon, else the reason (Polish, the official texts where there are some)
	static const char* Check(LPCHARACTER ch, LPITEM scroll, LPITEM weapon, BYTE changeTo, char* buf, size_t len)
	{
		const TConfig& c = Cfg();
		const BYTE mode = ModeOf(scroll->GetVnum());
		if (!c.enabled)
			return "Zaczarowanie \277ywio\263u broni jest teraz wy\263\261czone.";
		if (!weapon || weapon == scroll || weapon->GetOwner() != ch || weapon->GetWindow() != INVENTORY)
			return "Przeci\261gnij zw\363j na bro\361 w ekwipunku.";
		if (weapon->IsEquipped())
			return "Zdejmij bro\361, zanim j\261 zaczarujesz.";
		if (weapon->IsExchanging() || scroll->IsExchanging() || weapon->isLocked() || scroll->isLocked())
			return "Nie mo\277na teraz u\277y\346 tego przedmiotu.";
		if (!IsEnchantableWeapon(weapon))
			return "Nie mo\277na u\277ywa\346 z tym przedmiotem.";
		if (weapon->GetRefineLevel() < c.minRefine)
		{
			snprintf(buf, len, "Zaczarowanie \277ywio\263u jest dost\352pne tylko dla broni +%d lub wy\277szej.", c.minRefine);
			return buf;
		}
		const TData* d = Find(weapon);
		const int grade = d ? d->grade : 0;
		if (mode == MODE_UPGRADE)
		{
			if (grade && d->type != ScrollElement(scroll))
				return "Przedmiot posiada ju\277 inny \277ywio\263.";
			if (grade >= MAX_GRADE)
				return "Maksymalny poziom zaczarowania \277ywio\263u zosta\263 ju\277 osi\261gni\352ty.";
		}
		else if (!grade)
			return "Ta bro\361 nie ma Zaczarowania \277ywio\263u.";
		else if (mode == MODE_CHANGE)
		{
#ifdef MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1
			if (weapon->IsAccountBound())
				return "\257ywio\263u przedmiotu przypisanego do konta nie mo\277na zmieni\346.";
#endif
			if (changeTo && (changeTo > 6 || changeTo == d->type))
				return "Wybierz inny \277ywio\263.";
		}
		if (ch->GetGold() < FeeOf(mode))
			return "Za ma\263o Yang.";
		return NULL;
	}

	static bool BusyElsewhere(LPCHARACTER ch)
	{
		return ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen() ||
				!ch->CanHandleItem();
	}

	static void Close(LPCHARACTER ch)
	{
		s_mapPending.erase(ch->GetPlayerID());
		if (ch->GetDesc() && !ch->GetDesc()->IsBot())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WELEMCLOSE");
	}

	static std::string ValuesText(const TData& d, int level)
	{
		char buf[160];
		snprintf(buf, sizeof(buf), "%s +%d: %s +%d%%, Warto\234\346 Ataku +%d", s_aszName[d.type], level,
				s_aszPower[d.type], d.pow[level - 1], d.att[level - 1]);
		return buf;
	}

	// the element scroll's element by its vnum (the scroll may be gone - its last piece was used)
	static BYTE ScrollElement2(DWORD vnum)
	{
		const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnum);
		if (t && t->alValues[0] >= POINT_FIRST && t->alValues[0] < POINT_FIRST + 6)
			return (BYTE) (t->alValues[0] - POINT_FIRST + 1);
		return s_abScrollElement[vnum - SCROLL_FIRST];
	}

	static void Confirm(LPCHARACTER ch, BYTE changeTo)
	{
		std::map<DWORD, TPending>::iterator it = s_mapPending.find(ch->GetPlayerID());
		if (it == s_mapPending.end())
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WELEMCLOSE");
			return;
		}
		const TPending p = it->second;
		s_mapPending.erase(it);
		if (BusyElsewhere(ch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna (handel, sklep, magazyn, kostk\352) i spr\363buj jeszcze raz.");
			Close(ch);
			return;
		}
		LPITEM weapon = ITEM_MANAGER::instance().Find(p.weaponId);
		LPITEM scroll = ITEM_MANAGER::instance().Find(p.scrollId);
		if (!scroll || scroll->GetOwner() != ch || scroll->GetVnum() != p.scrollVnum ||
				scroll->GetCount() < 1 || !weapon)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zw\363j albo bro\361 nie le\277y ju\277 w ekwipunku.");
			Close(ch);
			return;
		}
		if (p.mode == MODE_CHANGE && !changeTo)
		{
			Close(ch);
			return;
		}
		char reason[160];
		const char* why = Check(ch, scroll, weapon, p.mode == MODE_CHANGE ? changeTo : 0, reason, sizeof(reason));
		if (why)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", why);
			Close(ch);
			return;
		}
		const TConfig& c = Cfg();
		const long long fee = FeeOf(p.mode);
		const DWORD scrollVnum = scroll->GetVnum();
		TData d;
		memset(&d, 0, sizeof(d));
		if (const TData* old = Find(weapon))
			d = *old;
		const BYTE oldType = d.type, oldGrade = d.grade;

		if (fee > 0)
		{
			ch->ChangeGold(-fee);
			DBManager::instance().SendMoneyLog(MONEY_LOG_REFINE, weapon->GetVnum(), -fee);
		}
		scroll->SetCount(scroll->GetCount() - 1);	// 0 removes it

		bool ok = true;
		std::string text;
		if (p.mode == MODE_UPGRADE)
		{
			const int g = d.grade;		// the level being reached is g + 1
			ok = number(1, 100) <= c.chance[g];
			if (ok)
			{
				d.type = ScrollElement2(scrollVnum);
				d.grade = g + 1;
				d.att[g] = (BYTE) Roll(c.attack[g]);
				d.pow[g] = (BYTE) Roll(c.power[g]);
				Set(weapon, &d);
				ch->ChatPacket(CHAT_TYPE_INFO, "Zaczarowanie \277ywio\263u powiod\263o si\352! %s.", ValuesText(d, d.grade).c_str());
			}
			else
				ch->ChatPacket(CHAT_TYPE_INFO, "Zaczarowanie \277ywio\263u nie powiod\263o si\352! Bro\361 pozosta\263a bez zmian.");
		}
		else if (p.mode == MODE_CURSE)
		{
			d.grade -= 1;
			d.att[d.grade] = d.pow[d.grade] = 0;
			if (!d.grade)
				d.type = 0;
			Set(weapon, &d);
			ch->ChatPacket(CHAT_TYPE_INFO, d.grade ? "Zosta\263 zmniejszony poziom zaczarowania \277ywio\263u: %s +%d."
					: "Zosta\263 zmniejszony poziom zaczarowania \277ywio\263u: bro\361 nie ma ju\277 \277ywio\263u (%s).",
					s_aszName[d.grade ? d.type : oldType], (int) d.grade);
		}
		else
		{
			d.type = changeTo;
			Set(weapon, &d);
			ch->ChatPacket(CHAT_TYPE_INFO, "%s posiada teraz \277ywio\263: %s!", weapon->GetName(), s_aszName[d.type]);
		}
		char hint[192];
		snprintf(hint, sizeof(hint), "mode %u ok %d scroll %u fee %lld type %u->%u grade %u->%u att %u/%u/%u pow %u/%u/%u",
				p.mode, ok ? 1 : 0, scrollVnum, fee, oldType, d.type, oldGrade, d.grade, d.att[0], d.att[1], d.att[2],
				d.pow[0], d.pow[1], d.pow[2]);
		LogManager::instance().ItemLog(ch, weapon, "WEAPON_ELEMENT", hint);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WELEMRESULT %u %d %u", p.mode, ok ? 1 : 0, (unsigned int) (ok ? d.type : oldType));
	}
}

using namespace welem;

// ITEM_MANAGER::CreateItem: a loaded weapon / sash gets its enchant back (a new item has none)
void Mt2009WElemCreate(LPITEM item, bool bIsNewItem)
{
	if (!item || bIsNewItem || !item->GetID() || (!IsEnchantableWeapon(item) && !IsSash(item)))
		return;
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"SELECT type, grade, att0, att1, att2, pow0, pow1, pow2 FROM item_element WHERE id = %u", item->GetID()));
	SQLResult* pRes = pMsg ? pMsg->Get() : NULL;
	MYSQL_ROW row = (pRes && pRes->uiNumRows > 0) ? mysql_fetch_row(pRes->pSQLResult) : NULL;
	if (!row)
	{
		s_mapData.erase(item->GetID());	// this core's copy of an older state (the item came back from another core)
		return;
	}
	TData d;
	int v[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };
	for (int i = 0; i < 8; ++i)
		if (row[i])
			str_to_number(v[i], row[i]);
	d.type = (BYTE) v[0];
	d.grade = (BYTE) std::min(v[1], (int) MAX_GRADE);
	for (int i = 0; i < MAX_GRADE; ++i)
	{
		d.att[i] = (BYTE) MINMAX(0, v[2 + i], 15);
		d.pow[i] = (BYTE) MINMAX(0, v[5 + i], 15);
	}
	if (d.type >= 1 && d.type <= 6 && d.grade)
		s_mapData[item->GetID()] = d;
	else
		s_mapData.erase(item->GetID());
}

// CItem::CopyAttributeTo: a refine (the blacksmith, over9) keeps the enchant on the new weapon; a sash absorbing a weapon
// (char.cpp, the absorption's CopyAttributeTo) takes it over - and a sash made from a sash keeps it
void Mt2009WElemCopy(LPITEM pFrom, LPITEM pTo)
{
	if (!pFrom || !pTo || pFrom == pTo || !pTo->GetID())
		return;
	const TData* d = Find(pFrom);
	if (!d || (!IsEnchantableWeapon(pTo) && !IsSash(pTo)))
		return;
	const TData copy = *d;
	Set(pTo, &copy);
}

// char.cpp, USE_DETACHMENT on a sash: the absorbed weapon goes, its enchant with it
void Mt2009WElemClear(LPITEM item)
{
	if (Find(item))
		Set(item, NULL);
}

// CItem::ModifyPoints: the weapon's power of its element; a sash with an absorbed enchanted weapon: its share of the
// power and of the attack value (as the absorbed weapon's attack: POINT_ATT_GRADE_BONUS) - Owsap's char_acce rule
void Mt2009WElemItemPoints(LPITEM item, LPCHARACTER owner, bool bAdd)
{
	const TData* d = Find(item);
	if (!owner || !d || d->type < 1 || d->type > 6)
		return;
	int att, pow;
	Sums(d, att, pow);
	if (IsSash(item))
	{
		pow = item->CalcAcceBonus(pow);
		att = item->CalcAcceBonus(att);
		if (att)
			owner->PointChange(POINT_ATT_GRADE_BONUS, bAdd ? att : -att);
	}
	else if (!IsEnchantableWeapon(item))
		return;
	if (pow)
		owner->PointChange(POINT_FIRST + d->type - 1, bAdd ? pow : -pow);
}

// battle.cpp: the weapon's enchant attack value, added as its value5 (x 2)
int Mt2009WElemAttack(LPITEM weapon)
{
	const TData* d = Find(weapon);
	int att, pow;
	Sums(d, att, pow);
	return att;
}

// CHARACTER::UseItemEx: -1 not a scroll of this system; else the use's result (the window opens - nothing used yet)
int Mt2009WElemUseItem(LPCHARACTER ch, LPITEM item, TItemPos DestCell)
{
	if (!ch || !item || item->GetType() != ITEM_USE || !ModeOf(item->GetVnum()))
		return -1;
	if (!ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return 0;
	if (!ch->IsValidItemPosition(DestCell) || DestCell.window_type != INVENTORY)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Przeci\261gnij zw\363j na bro\361 w ekwipunku.");
		return 0;
	}
	if (BusyElsewhere(ch))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna (handel, sklep, magazyn, kostk\352) i spr\363buj jeszcze raz.");
		return 0;
	}
	LPITEM weapon = ch->GetItem(DestCell);
	char reason[160];
	const char* why = Check(ch, item, weapon, 0, reason, sizeof(reason));
	if (why)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", why);
		return 0;
	}
	const BYTE mode = ModeOf(item->GetVnum());
	const TConfig& c = Cfg();
	const TData* d = Find(weapon);
	const int grade = d ? d->grade : 0;
	TPending p;
	p.mode = mode;
	p.weaponId = weapon->GetID();
	p.scrollId = item->GetID();
	p.scrollVnum = item->GetVnum();
	s_mapPending[ch->GetPlayerID()] = p;
	int attLo = 0, attHi = 0, powLo = 0, powHi = 0;
	BYTE type = d ? d->type : 0;
	int newGrade = grade;
	if (mode == MODE_UPGRADE)
	{
		type = ScrollElement(item);
		newGrade = grade + 1;
		Range(c.attack[grade], attLo, attHi);
		Range(c.power[grade], powLo, powHi);
	}
	else if (mode == MODE_CURSE)
		newGrade = grade - 1;
	ch->ChatPacket(CHAT_TYPE_COMMAND, "WELEMOPEN %u %u %u %lld %u %d %u %d %d %d %d", mode, (unsigned int) weapon->GetCell(),
			(unsigned int) item->GetCell(), FeeOf(mode), type, newGrade, Pack(d), attLo, attHi, powLo, powHi);
	return 0;
}

// "/welem ok" | "/welem change <element>" | "/welem close"
void Mt2009WElemCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	char arg1[32], arg2[32];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	if (!strcmp(arg1, "ok"))
		Confirm(ch, 0);
	else if (!strcmp(arg1, "change"))
	{
		int t = 0;
		str_to_number(t, arg2);
		Confirm(ch, (BYTE) MINMAX(0, t, 7));
	}
	else
		s_mapPending.erase(ch->GetPlayerID());
}

// the client's copy: one cell of the inventory / equipment changed (CHARACTER::SetItem) - only when the new or the old
// item has an enchant
void Mt2009WElemCellNotify(LPCHARACTER ch, int iCell, LPITEM pNow, LPITEM pOld)
{
	const TData* now = Find(pNow);
	if (now || (pOld && pOld != pNow && Find(pOld)))
		Notify(ch, 1, iCell, Pack(now));
}

// CItem::AddToCharacter, the storehouse (3)
void Mt2009WElemNotifyItem(LPCHARACTER ch, int iWindow, int iCell, LPITEM item, bool bRemoved)
{
	const TData* d = Find(item);
	if (d)
		Notify(ch, iWindow, iCell, bRemoved ? 0 : Pack(d));
}

// the trade: its windows are forgotten when it starts; an item put in is told to both sides (4 own, 5 the other's)
void Mt2009WElemExchangeStart(LPCHARACTER a, LPCHARACTER b)
{
	Notify(a, 4, -1, 0);
	Notify(a, 5, -1, 0);
	Notify(b, 4, -1, 0);
	Notify(b, 5, -1, 0);
}

void Mt2009WElemExchangeAdd(LPCHARACTER owner, LPCHARACTER company, int iDisplayPos, LPITEM item)
{
	const TData* d = Find(item);
	if (!d)
		return;
	Notify(owner, 4, iDisplayPos, Pack(d));
	Notify(company, 5, iDisplayPos, Pack(d));
}

// entergame: everything again (the client forgets what it heard before - a warp is a new login)
void Mt2009WElemSendAll(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	s_mapPending.erase(ch->GetPlayerID());
	Notify(ch, 0, 0, 0);
	for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetInventoryItem(i);
		if (item && item->GetCell() == i && Find(item))
			Notify(ch, 1, i, Pack(Find(item)));
	}
	for (int i = 0; i < WEAR_MAX_NUM; ++i)
	{
		LPITEM item = ch->GetWear(i);
		if (item && Find(item))
			Notify(ch, 1, INVENTORY_MAX_NUM + i, Pack(Find(item)));
	}
}

// "/welem_sync": the client asks again (at most once a second a character)
void Mt2009WElemResend(LPCHARACTER ch)
{
	static std::map<DWORD, DWORD> s_mapLast;
	if (!ch || !ch->IsPC())
		return;
	const DWORD now = get_dword_time();
	DWORD& last = s_mapLast[ch->GetPlayerID()];
	if (last && now - last < 1000)
		return;
	last = now;
	Mt2009WElemSendAll(ch);
}

// "/welem_reload" (GM): weapon_element.txt again
void Mt2009WElemReload(LPCHARACTER ch)
{
	std::string report;
	Load(&report);
	if (ch)
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", report.c_str());
}

// CShop::Buy / the shop's item list: Straznik Medali's scrolls cost the config's price (no empire mark-up; the scroll
// prices live in weapon_element.txt alone)
bool Mt2009WElemShopPrice(DWORD vnum, int count, YANG& price)
{
	if (!ModeOf(vnum))
		return false;
	const TConfig& c = Cfg();
	const long long one = ModeOf(vnum) == MODE_UPGRADE ? c.priceElement : (vnum == SCROLL_CURSE ? c.priceCurse : c.priceChange);
	price = (YANG) (one * std::max(1, count));
	return true;
}

// CShop::Buy: the wiki's guild level (21 the element scrolls, 24 Klatwa / Zmiana); bots never buy them
bool Mt2009WElemShopCanBuy(LPCHARACTER ch, DWORD vnum)
{
	if (!ModeOf(vnum))
		return true;
	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return false;
	const TConfig& c = Cfg();
	const int need = ModeOf(vnum) == MODE_UPGRADE ? c.guildElement : c.guildSpecial;
	if (need > 0 && (!ch->GetGuild() || ch->GetGuild()->GetLevel() < need))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ten zw\363j sprzedaj\352 tylko cz\263onkom gildii co najmniej na %d. poziomie.", need);
		return false;
	}
	return true;
}

// CHARACTER::UpdatePacket: the effect the others see, sent around once per change (worn, taken off, enchanted)
void Mt2009WElemOnUpdatePacket(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;
	const BYTE type = ShownType(ch);
	const DWORD vid = (DWORD) ch->GetVID();
	std::map<DWORD, BYTE>::iterator it = s_mapShown.find(vid);
	const BYTE before = it == s_mapShown.end() ? 0 : it->second;
	if (before == type)
		return;
	if (s_mapShown.size() > 50000)	// the VIDs of characters long gone
		s_mapShown.clear();
	if (type)
		s_mapShown[vid] = type;
	else if (it != s_mapShown.end())
		s_mapShown.erase(it);
	SendAround(ch, type);
}

// CHARACTER::EncodeInsertPacket: a character with the effect coming into a player's view (the player too)
void Mt2009WElemOnInsert(LPCHARACTER shown, LPCHARACTER viewer)
{
	if (!shown || !viewer || !shown->IsPC() || !viewer->GetDesc() || viewer->GetDesc()->IsBot())
		return;
	const BYTE type = ShownType(shown);
	if (type)
		viewer->ChatPacket(CHAT_TYPE_COMMAND, "WELEMFX %u %u", (unsigned int) shown->GetVID(), (unsigned int) type);
}
