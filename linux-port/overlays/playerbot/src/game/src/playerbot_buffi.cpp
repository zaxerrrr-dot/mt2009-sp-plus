// MT2009_PLUS_BUFFI_V1: Buffi - the support shaman of Ameria Project (srcs/server/game/buffi.cpp, char_state.cpp
// StateBuffi, questlua_pc.cpp pc.set_buffi_name, quest __buffi__), ported for Yohara 3.0 in place of the companion
// (the owner, 21 October 2026: "W zamian za towarzysza dodaj system buffi z Amerii. Pod tym samym skrotem
// klawiszowym"). server-patches/buffi/README.md has the whole picture; the engine's hooks are server-patches/buffi
// (edits.json) and call the free functions at the end of this file (declared again at each hook, as the other patches
// do).
//
// Ameria's mechanics and numbers:
//   - the seal Buffi (7 dni) 61025 / Buffi 61026: a use calls the support shaman (mob 65000) or sends it away; one
//     buffi a character; the seal's socket 1 says "called" and brings it back at the next login / map change;
//   - every 3 seconds it casts on its owner the first buff the owner lacks: Blogoslawienstwo (Hosin), Pomoc Smoka
//     (Gicheon), and with a name also Szybkosc (Kwaesok) and Zwiekszenie Ataku (Jeungryeok) - Ameria's skill_proto
//     rows 164-167: iq 226 * 0.2, k = the skill power of the level (the mob table, as Ameria's buffi casts it),
//     3600 s (Szybkosc's casting speed 60+100*k s); never over the same buff of a real shaman;
//   - its skills are the owner's skills 164-167, M1 (20) at the first call; the books 61035-61038 (M1 -> G1, the
//     engine's book reading - server-patches/buffi (learnable)) and Kamien Duszy Buffi 61031 (G1 -> P, quest buffi);
//   - the name scroll 61030: names the buffi of the seal (a name per seal, Ameria's SAVE_WITH_ITEM_ID), unlocks
//     Szybkosc and Zwiekszenie Ataku, and +10% against bosses for 7 days (Ameria's AFFECT_NAME_BUFFI); not while
//     that bonus still lasts (Ameria returns there too);
//   - its looks: Czarna Szata+9 (11899) and Ekstazyjny Wachlarz+9 (7159) on a female shaman, Ameria's defaults.
//     Ameria's four costume slots for the buffi are the exe's (new equipment cells) - not here.
//
// Without an exe change: the buffi is an NPC on the server (a pet: no AI of its own, nobody can attack it) and is
// shown to the clients as a female shaman (race 3, type PC) - BuffiInsertLook in CHARACTER::EncodeInsertPacket; its
// casting is the move packet of a skill (FUNC_SKILL | the skill's motion), which the client plays like a player's; the
// window is root/uibuffi.py over "/buffi" and the chat command "BUFFI ...".
//
// The switch M2_BUFFI (docker-compose.yml, the game container's environment; default 1): 0, "off", "no" or "false"
// switches the buffi off - nobody's is called, a called one goes, the seal says so; the seals, names and skills stay.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "affect.h"
#include "skill.h"
#include "skill_power.h"
#include "db.h"
#include "cmd.h"
#include "vector.h"

#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <set>
#include <string>

namespace mt2009_buffi
{
	const DWORD SEAL_7D = 61025;			// Buffi (7 dni) - Ameria's starter chest
	const DWORD SEAL = 61026;				// Buffi - Ameria's ItemShop
	const DWORD NAME_SCROLL = 61030;		// Zwoj Imienia Buffi
	const DWORD MOB = 65000;				// the support shaman (world.mob_proto, buffi.sql)
	const DWORD SKILL_FIRST = 164;			// Ameria's SKILL_BUFFI_1..4
	const DWORD SKILL_LAST = 167;
	const DWORD AFFECT_NAME = 640;			// Ameria's AFFECT_NAME_BUFFI: +10% against bosses, 7 days
	const long NAME_BONUS = 10;
	const long NAME_BONUS_SECONDS = 7 * 24 * 3600;
	const BYTE START_LEVEL = 20;			// M1, Ameria's first call
	const DWORD CAST_MS = 3000;				// Ameria's m_dwSkillNextTime
	const DWORD RESPAWN_MS = 3000;
	const DWORD ARMOR = 11899;				// Czarna Szata+9
	const DWORD WEAPON = 7159;				// Ekstazyjny Wachlarz+9
	const DWORD LOOK_RACE = 3;				// MAIN_RACE_SHAMAN_W
	const BYTE LOOK_TYPE = CHAR_TYPE_PC;
	const float FOLLOW_DISTANCE = 200.0f;	// Ameria's StateBuffi
	const float RUN_DISTANCE = 300.0f;
	const float RESPAWN_DISTANCE = 3000.0f;
	const int APPROACH = 200;

	// The four buffs: the skill, the real shaman skill whose affect it is (the type, so the client shows its icon and
	// a real shaman's same buff is the same affect), the flag, the client's motion (skilldesc's motion index) and
	// the name for the window and the chat.
	struct SBuff
	{
		DWORD dwSkill;
		DWORD dwAffect;
		DWORD dwFlag;
		BYTE bMotion;
		bool bNeedsName;
	};
	const SBuff BUFFS[4] =
	{
		{ 164, 94,  AFF_SKILL_BLESSING,   4,  false },	// Blogoslawienstwo (Hosin)
		{ 165, 96,  AFF_SKILL_DRAGON_HELP, 6, false },	// Pomoc Smoka (Gicheon)
		{ 166, 110, AFF_SKILL_SWIFTNESS,  20, true },	// Szybkosc (Kwaesok)
		{ 167, 111, AFF_SKILL_ATTACK_UP,  21, true },	// Zwiekszenie Ataku (Jeungryeok)
	};

	struct SBuffi
	{
		DWORD dwItemID;			// the seal
		DWORD dwVID;			// the shaman in the world, 0 none
		DWORD dwNextCast;
		DWORD dwNextSpawn;
		std::string stName;		// "" = no name (Ameria: two buffs only)
		SBuffi() : dwItemID(0), dwVID(0), dwNextCast(0), dwNextSpawn(0) {}
	};

	std::map<DWORD, SBuffi> s_mapBuffi;		// owner pid -> its buffi
	std::set<DWORD> s_setVid;				// the shamans' vids, for the insert packet
	LPEVENT s_pkTick = NULL;
	bool s_bTable = false;

	bool Enabled()
	{
		static int s_enabled = -1;
		if (s_enabled < 0)
		{
			const char* value = getenv("M2_BUFFI");
			s_enabled = 1;
			if (value && (!strcmp(value, "0") || !strcasecmp(value, "off") || !strcasecmp(value, "no") || !strcasecmp(value, "false")))
				s_enabled = 0;
			sys_log(0, "BUFFI: %s (M2_BUFFI=%s)", s_enabled ? "on" : "off", value ? value : "");
		}
		return s_enabled != 0;
	}

	bool Counts(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	bool IsSeal(DWORD dwVnum)
	{
		return dwVnum == SEAL_7D || dwVnum == SEAL;
	}

	bool IsBuffiSkill(DWORD dwVnum)
	{
		return dwVnum >= SKILL_FIRST && dwVnum <= SKILL_LAST;
	}

	void Command(LPCHARACTER ch, const char* fmt, ...)
	{
		char buf[512];
		va_list args;
		va_start(args, fmt);
		vsnprintf(buf, sizeof(buf), fmt, args);
		va_end(args);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BUFFI %s", buf);
	}

	void Say(LPCHARACTER ch, const char* text)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "[Buffi] %s", text);
	}

	// ------------------------------------------------------------------ the names (a name per seal, Ameria's file
	// share/buffi_name/<item id> - here the table player.mt2009_buffi_name, also made by apply.sh)

	bool EnsureTable()
	{
		if (s_bTable)
			return true;
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.mt2009_buffi_name ("
				"item_id INT UNSIGNED NOT NULL PRIMARY KEY, "
				"owner_pid INT UNSIGNED NOT NULL DEFAULT 0, "
				"name VARCHAR(24) NOT NULL DEFAULT '', "
				"named_at DATETIME NOT NULL) ENGINE=InnoDB"));
		s_bTable = msg.get() && msg->uiSQLErrno == 0;
		if (!s_bTable)
			sys_err("BUFFI: the table player.mt2009_buffi_name cannot be made");
		return s_bTable;
	}

	std::string LoadName(DWORD dwItemID)
	{
		if (!dwItemID || !EnsureTable())
			return "";
		char query[128];
		snprintf(query, sizeof(query), "SELECT name FROM player.mt2009_buffi_name WHERE item_id = %u", dwItemID);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || msg->Get()->uiNumRows == 0)
			return "";
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		return row && row[0] ? std::string(row[0]) : std::string();
	}

	bool SaveName(DWORD dwItemID, DWORD dwOwner, const char* name)
	{
		if (!EnsureTable())
			return false;
		char query[256];
		snprintf(query, sizeof(query), "REPLACE INTO player.mt2009_buffi_name (item_id, owner_pid, name, named_at) "
				"VALUES (%u, %u, '%s', NOW())", dwItemID, dwOwner, name);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		return msg.get() && msg->uiSQLErrno == 0;
	}

	// a name check_name lets through: letters and digits only, so it goes into the query as it is
	bool NameAllowed(const char* name)
	{
		const size_t len = name ? strlen(name) : 0;
		if (len < 2 || len > 16)
			return false;
		for (size_t i = 0; i < len; ++i)
			if (!isalnum((unsigned char) name[i]))
				return false;
		return check_name && check_name(name);
	}

	// ------------------------------------------------------------------ the shaman

	LPCHARACTER Shaman(const SBuffi& b)
	{
		return b.dwVID ? CHARACTER_MANAGER::instance().Find(b.dwVID) : NULL;
	}

	void Dismiss(SBuffi& b)
	{
		LPCHARACTER mob = Shaman(b);
		s_setVid.erase(b.dwVID);
		b.dwVID = 0;
		if (mob)
			M2_DESTROY_CHARACTER(mob);
	}

	std::string ShownName(LPCHARACTER owner, const SBuffi& b)
	{
		std::string name = b.stName.empty() ? std::string("Buffi ") + owner->GetName() : b.stName;
		if (name.length() > CHARACTER_NAME_MAX_LEN)
			name.resize(CHARACTER_NAME_MAX_LEN);
		return name;
	}

	bool Spawn(LPCHARACTER owner, SBuffi& b)
	{
		Dismiss(b);
		if (!owner->GetSectree())
			return false;
		const long x = owner->GetX() + number(-100, 100);
		const long y = owner->GetY() + number(-100, 100);
		LPCHARACTER mob = CHARACTER_MANAGER::instance().SpawnMob(MOB, owner->GetMapIndex(), x, y, owner->GetZ(), false,
				(int) (owner->GetRotation() + 180), false);
		if (!mob)
		{
			sys_err("BUFFI: mob %u cannot be spawned (world.mob_proto, buffi.sql)", MOB);
			return false;
		}
		mob->SetPet();
		mob->SetEmpire(owner->GetEmpire());
		mob->SetName(ShownName(owner, b));
		mob->SetPart(PART_MAIN, ARMOR);
		mob->SetPart(PART_WEAPON, WEAPON);
		mob->SetPart(PART_HAIR, 0);
		b.dwVID = (DWORD) mob->GetVID();
		s_setVid.insert(b.dwVID);	// before Show: its insert packet already says "female shaman"
		if (!mob->Show(owner->GetMapIndex(), x, y, owner->GetZ()))
		{
			sys_err("BUFFI: mob %u cannot be shown at %ld %ld (map %ld)", MOB, x, y, owner->GetMapIndex());
			Dismiss(b);
			return false;
		}
		b.dwNextCast = get_dword_time() + 1000;
		return true;
	}

	// ------------------------------------------------------------------ the buffs (Ameria's CheckOwnerSupport)

	double Power(BYTE bLevel)
	{
		return CTableBySkill::instance().GetSkillPowerByLevelFromType(0, 0, MINMAX(0, (int) bLevel, SKILL_MAX_LEVEL), true) / 100.0;
	}

	int Grade(BYTE bLevel)
	{
		return bLevel >= 40 ? 3 : bLevel >= 30 ? 2 : bLevel >= 20 ? 1 : 0;
	}

	// Ameria's skill_proto 164-167 (szPointPoly, iq = 226): the point(s) a level gives
	void Cast(LPCHARACTER owner, LPCHARACTER mob, const SBuff& buff, BYTE bLevel)
	{
		const double k = Power(bLevel);
		const long lDuration = 3600;
		switch (buff.dwSkill)
		{
			case 164:
				owner->AddAffect(buff.dwAffect, POINT_RESIST_NORMAL_DAMAGE, (long) ((226 * 0.2 + 5) * (2 * k + 0.5) / (k + 1.5)),
						buff.dwFlag, lDuration, 0, true);
				break;
			case 165:
				owner->AddAffect(buff.dwAffect, POINT_CRITICAL_PCT, (long) ((226 * 0.2 + 5) * (2 * k + 0.5) / (k + 1.5)),
						buff.dwFlag, lDuration, 0, true);
				break;
			case 166:
				owner->AddAffect(buff.dwAffect, POINT_MOV_SPEED, (long) (5 + 35 * k), buff.dwFlag, lDuration, 0, true);
				owner->AddAffect(buff.dwAffect, POINT_CASTING_SPEED, (long) (3 + 33 * k), AFF_NONE, (long) (60 + 100 * k), 0, true);
				break;
			case 167:
				owner->AddAffect(buff.dwAffect, POINT_ATT_GRADE_BONUS, (long) (5 + (226 * 0.2 + 15) * k), buff.dwFlag,
						lDuration, 0, true);
				break;
		}
		// the cast for the eyes: the skill's motion of its grade (the client's GradeData, motion + grade * 25),
		// facing the owner - the move packet a player's skill comes in
		mob->SetRotationToXY(owner->GetX(), owner->GetY());
		mob->SendMovePacket(FUNC_SKILL | (BYTE) (buff.bMotion + Grade(bLevel) * 25), 1, mob->GetX(), mob->GetY(), 0, 0);
	}

	void Support(LPCHARACTER owner, LPCHARACTER mob, SBuffi& b, DWORD dwNow)
	{
		if (dwNow < b.dwNextCast)
			return;
		b.dwNextCast = dwNow + CAST_MS;
		if (!owner->IsLoadedAffect() || owner->IsDead() || owner->GetSkillGroup() == 0)
			return;
		for (int i = 0; i < 4; ++i)
		{
			const SBuff& buff = BUFFS[i];
			if (buff.bNeedsName && b.stName.empty())
				continue;
			BYTE bLevel = (BYTE) owner->GetSkillLevel(buff.dwSkill);
			if (bLevel == 0)
			{
				owner->SetSkillLevel(buff.dwSkill, START_LEVEL);
				owner->SkillLevelPacket();
				return;
			}
			if (owner->IsAffectFlag(buff.dwFlag) || owner->FindAffect(buff.dwAffect))
				continue;
			Cast(owner, mob, buff, bLevel);
			return;
		}
	}

	// Ameria's StateBuffi: back beside the owner from afar, after the owner when it walks away
	void Follow(LPCHARACTER owner, LPCHARACTER mob)
	{
		if (mob->GetMapIndex() != owner->GetMapIndex())
		{
			mob->Show(owner->GetMapIndex(), owner->GetX(), owner->GetY());
			return;
		}
		const float fDist = DISTANCE_APPROX(mob->GetX() - owner->GetX(), mob->GetY() - owner->GetY());
		if (fDist >= RESPAWN_DISTANCE)
		{
			const float fRot = owner->GetRotation() * 3.141592f / 180.f;
			mob->Show(owner->GetMapIndex(), owner->GetX() + (long) (-APPROACH * cos(fRot)), owner->GetY() + (long) (-APPROACH * sin(fRot)));
			return;
		}
		if (fDist < FOLLOW_DISTANCE)
			return;
		mob->SetNowWalking(fDist <= RUN_DISTANCE);
		mob->SetRotationToXY(owner->GetX(), owner->GetY());
		float fx, fy;
		GetDeltaByDegree(mob->GetRotation(), fDist - APPROACH, &fx, &fy);
		if (mob->Goto((long) (mob->GetX() + fx + 0.5f), (long) (mob->GetY() + fy + 0.5f)))
			mob->SendMovePacket(FUNC_WAIT, 0, 0, 0, 0, 0);
	}

	LPITEM SealOf(LPCHARACTER owner, const SBuffi& b)
	{
		LPITEM item = b.dwItemID ? ITEM_MANAGER::instance().Find(b.dwItemID) : NULL;
		if (!item || item->GetOwner() != owner || !IsSeal(item->GetVnum()) || item->GetSocket(1) != 1)
			return NULL;
		return item;
	}

	EVENTINFO(buffi_tick_info)
	{
		int unused;
		buffi_tick_info() : unused(0) {}
	};

	void TickAll()
	{
		const DWORD dwNow = get_dword_time();
		for (std::map<DWORD, SBuffi>::iterator it = s_mapBuffi.begin(); it != s_mapBuffi.end();)
		{
			SBuffi& b = it->second;
			LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(it->first);
			// the owner gone (logout, warp, another core), the seal gone or put away, the system off: the
			// shaman goes; the seal's socket brings it back at the next login
			if (!Enabled() || !owner || !owner->GetDesc() || !SealOf(owner, b))
			{
				Dismiss(b);
				s_mapBuffi.erase(it++);
				continue;
			}
			LPCHARACTER mob = Shaman(b);
			if (!mob)
			{
				// a dungeon's purge or a map's end took it: called again after a moment
				s_setVid.erase(b.dwVID);
				b.dwVID = 0;
				if (owner->GetSectree() && dwNow >= b.dwNextSpawn)
				{
					b.dwNextSpawn = dwNow + RESPAWN_MS;
					Spawn(owner, b);
				}
				++it;
				continue;
			}
			if (!owner->GetSectree() || owner->IsDead())
			{
				++it;
				continue;
			}
			Follow(owner, mob);
			Support(owner, mob, b, dwNow);
			++it;
		}
	}

	EVENTFUNC(buffi_tick_event)
	{
		TickAll();
		if (s_mapBuffi.empty())
		{
			s_pkTick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(1) / 4 ? PASSES_PER_SEC(1) / 4 : 1;
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		buffi_tick_info* info = AllocEventInfo<buffi_tick_info>();
		s_pkTick = event_create(buffi_tick_event, info, PASSES_PER_SEC(1) / 4 ? PASSES_PER_SEC(1) / 4 : 1);
	}

	// ------------------------------------------------------------------ calling / sending away (Ameria's
	// BUFFI_MANAGER::Summon)

	bool Call(LPCHARACTER owner, LPITEM seal)
	{
		std::map<DWORD, SBuffi>::iterator it = s_mapBuffi.find(owner->GetPlayerID());
		if (it != s_mapBuffi.end() && it->second.dwItemID != seal->GetID() && SealOf(owner, it->second))
		{
			Say(owner, "Masz ju\xbf przywo\xb3""anego Buffi. Najpierw odwo\xb3""aj tamtego.");
			return false;
		}
		SBuffi& b = s_mapBuffi[owner->GetPlayerID()];
		b.dwItemID = seal->GetID();
		b.stName = LoadName(seal->GetID());
		seal->SetSocket(1, 1);
		for (int i = 0; i < 4; ++i)
			if (owner->GetSkillLevel(BUFFS[i].dwSkill) == 0)
				owner->SetSkillLevel(BUFFS[i].dwSkill, START_LEVEL);
		owner->SkillLevelPacket();
		b.dwNextSpawn = 0;
		if (!Spawn(owner, b))
			b.dwNextSpawn = get_dword_time() + RESPAWN_MS;
		EnsureTick();
		return true;
	}

	void SendAway(LPCHARACTER owner, LPITEM seal)
	{
		std::map<DWORD, SBuffi>::iterator it = s_mapBuffi.find(owner->GetPlayerID());
		if (it != s_mapBuffi.end() && (!seal || it->second.dwItemID == seal->GetID()))
		{
			Dismiss(it->second);
			s_mapBuffi.erase(it);
		}
		if (seal && seal->GetSocket(1) == 1)
			seal->SetSocket(1, 0);
	}

	LPITEM FindSeal(LPCHARACTER ch, bool bCalledOnly)
	{
		LPITEM first = NULL;
		for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = ch->GetInventoryItem(i);
			if (!item || !IsSeal(item->GetVnum()))
				continue;
			if (item->GetSocket(1) == 1)
				return item;
			if (!first)
				first = item;
		}
		return bCalledOnly ? NULL : first;
	}

	LPITEM FindItem(LPCHARACTER ch, DWORD dwVnum)
	{
		for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
		{
			LPITEM item = ch->GetInventoryItem(i);
			if (item && item->GetVnum() == dwVnum)
				return item;
		}
		return NULL;
	}

	// "BUFFI state <on> <called> <seal vnum> <named> <name|-> <lv164> <lv165> <lv166> <lv167> <boss bonus seconds>
	// <name scrolls>" - root/uibuffi.py
	void SendState(LPCHARACTER ch)
	{
		if (!Enabled())
		{
			Command(ch, "off");
			return;
		}
		LPITEM called = FindSeal(ch, true);
		LPITEM seal = called ? called : FindSeal(ch, false);
		std::map<DWORD, SBuffi>::const_iterator it = s_mapBuffi.find(ch->GetPlayerID());
		std::string name = it != s_mapBuffi.end() ? it->second.stName : (seal ? LoadName(seal->GetID()) : std::string());
		const CAffect* aff = ch->FindAffect(AFFECT_NAME);
		Command(ch, "state 1 %d %u %d %s %d %d %d %d %ld %u", called ? 1 : 0, seal ? seal->GetVnum() : 0,
				name.empty() ? 0 : 1, name.empty() ? "-" : name.c_str(),
				ch->GetSkillLevel(164), ch->GetSkillLevel(165), ch->GetSkillLevel(166), ch->GetSkillLevel(167),
				aff ? (long) aff->lDuration : 0L, (unsigned int) ch->CountSpecifyItem(NAME_SCROLL));
	}

	void Rename(LPCHARACTER ch, const char* name)
	{
		std::map<DWORD, SBuffi>::iterator it = s_mapBuffi.find(ch->GetPlayerID());
		if (it == s_mapBuffi.end() || !SealOf(ch, it->second))
		{
			Say(ch, "Najpierw przywo\xb3""aj Buffi - imi\xea dostaje Buffi przywo\xb3""any z piecz\xea""ci.");
			return;
		}
		LPITEM scroll = FindItem(ch, NAME_SCROLL);
		if (!scroll)
		{
			Say(ch, "Nie masz Zwoju Imienia Buffi.");
			return;
		}
		if (ch->FindAffect(AFFECT_NAME))
		{
			Say(ch, "Bonus poprzedniego Zwoju Imienia jeszcze trwa - nowe imi\xea nadasz, gdy minie.");
			return;
		}
		if (!NameAllowed(name))
		{
			Say(ch, "To imi\xea jest niedozwolone. U\xbfyj od 2 do 16 liter lub cyfr, bez spacji.");
			return;
		}
		SBuffi& b = it->second;
		if (!SaveName(b.dwItemID, ch->GetPlayerID(), name))
		{
			Say(ch, "Nie uda\xb3o si\xea zapisa\xe6 imienia. Spr\xf3""buj ponownie.");
			return;
		}
		scroll->SetCount(scroll->GetCount() - 1);
		b.stName = name;
		ch->AddAffect(AFFECT_NAME, POINT_ATTBONUS_BOSS, NAME_BONUS, AFF_NONE, NAME_BONUS_SECONDS, 0, false);
		Spawn(ch, b);
		Say(ch, "Buffi ma nowe imi\xea. Odblokowane: Szybko\x9c\xe6 i Zwi\xeakszenie Ataku, +10% silny przeciwko bossom na 7 dni.");
	}
}

using namespace mt2009_buffi;

// ---------------------------------------------------------------------- the engine's hooks (server-patches/buffi)

// char_item.cpp, UseItemEx (after the Monster Cards): the seals and the name scroll. -1 not a buffi item, 0 refused,
// 1 used.
int BuffiUseItem(LPCHARACTER ch, LPITEM item)
{
	if (!item || (!IsSeal(item->GetVnum()) && item->GetVnum() != NAME_SCROLL))
		return -1;
	if (!Counts(ch))
		return 0;
	if (!Enabled())
	{
		Say(ch, "Buffi jest wy\xb3\xb9""czony na tym serwerze.");
		return 0;
	}
	if (item->GetVnum() == NAME_SCROLL)
	{
		std::map<DWORD, SBuffi>::iterator it = s_mapBuffi.find(ch->GetPlayerID());
		if (it == s_mapBuffi.end() || !SealOf(ch, it->second))
		{
			Say(ch, "Najpierw przywo\xb3""aj Buffi.");
			return 0;
		}
		Command(ch, "askname");
		return 0;
	}
	// Ameria's one second between two uses of a seal
	static std::map<DWORD, DWORD> s_mapNextUse;
	const DWORD dwNow = get_dword_time();
	DWORD& next = s_mapNextUse[ch->GetPlayerID()];
	if (dwNow < next)
	{
		Say(ch, "Nie tak szybko - spr\xf3""buj za chwil\xea.");
		return 0;
	}
	next = dwNow + 1000;
	if (item->GetSocket(1) == 1)
	{
		SendAway(ch, item);
		Say(ch, "Buffi odwo\xb3""any.");
	}
	else if (Call(ch, item))
		Say(ch, "Buffi przywo\xb3""any.");
	SendState(ch);
	return 0;		// the seal stays
}

// char_skill.cpp, IsLearnableSkill: the buffi's skills 164-167 for every class (Ameria's CanLearn), with a path, from
// M1 up to P; -1 for every other skill.
int BuffiLearnable(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsBuffiSkill(dwVnum))
		return -1;
	if (!ch || !ch->IsPC() || !Enabled() || ch->GetSkillGroup() == 0)
		return 0;
	// from M1 (the first call sets it), never by skill points
	const int iLevel = ch->GetSkillLevel(dwVnum);
	return iLevel >= START_LEVEL && iLevel < SKILL_MAX_LEVEL ? 1 : 0;
}

// input_login.cpp, entering the game (after the Monster Cards): a seal called before brings its buffi back.
void BuffiOnLogin(LPCHARACTER ch)
{
	if (!Counts(ch) || !Enabled())
		return;
	LPITEM seal = FindSeal(ch, true);
	if (seal)
		Call(ch, seal);
}

// char.cpp, EncodeInsertPacket: a buffi is shown as a female shaman (type PC, race 3) - its parts follow in the
// additional info as for any NPC. False for everybody else.
bool BuffiInsertLook(LPCHARACTER ch, BYTE& bType, DWORD& dwRace)
{
	if (!ch || ch->IsPC() || s_setVid.empty() || !s_setVid.count((DWORD) ch->GetVID()))
		return false;
	bType = LOOK_TYPE;
	dwRace = LOOK_RACE;
	return true;
}

// char.cpp, EncodeInsertPacket's additional info: no level over a buffi's head.
bool BuffiIsShaman(LPCHARACTER ch)
{
	return ch && !ch->IsPC() && !s_setVid.empty() && s_setVid.count((DWORD) ch->GetVID());
}

// "/buffi info|toggle|name <name>" - root/uibuffi.py (the P key, the inventory's side bar)
ACMD(do_buffi)
{
	if (!Counts(ch))
		return;
	if (!Enabled())
	{
		Command(ch, "off");
		return;
	}
	char sub[32] = "";
	char arg[64] = "";
	const char* rest = one_argument(argument ? argument : "", sub, sizeof(sub));
	one_argument(rest, arg, sizeof(arg));
	if (!strcmp(sub, "toggle"))
	{
		LPITEM seal = FindSeal(ch, true);
		if (!seal)
			seal = FindSeal(ch, false);
		if (!seal)
		{
			Say(ch, "Nie masz piecz\xea""ci Buffi (ItemShop, Skrzynia Ucznia).");
			SendState(ch);
			return;
		}
		BuffiUseItem(ch, seal);
		return;
	}
	if (!strcmp(sub, "name"))
	{
		Rename(ch, arg);
		SendState(ch);
		return;
	}
	SendState(ch);
}
