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
//
// MT2009_PLUS_BUFFI_V2 (the owner, 21 October 2026: "okno i rozwoj dokladnie jak w Amerii", "do G1 zwykle ksiegi
// szamana przez okno buffi"):
//   - Ameria's four costume slots of the buffi (WEAR_BUFFI_BODY/HEAD/WEAPON/SASH 28-31, the free wear cells under
//     WEAR_MAX 32 - common/length.h, server-patches/buffi (wear)): a costume dragged onto them, or used while the
//     Buffi window is open (Ameria's /buffi_costume_page - here "/buffi page 1|0"), goes onto the buffi: outfit and
//     hairstyle for a woman, a weapon a shaman can hold, any sash. They give their owner nothing (item.cpp (points))
//     and dress the shaman (RefreshLook, Ameria's CheckSupportWear - its sash too);
//   - M1 -> G1: the shaman's own skill books (50300 of Blogoslawienstwo 94, Pomoc Smoka 96, Szybkosc 110,
//     Zwiekszenie Ataku 111) dragged onto the buffi's skill in the window ("/buffi read") - the engine's book
//     reading (chance, 20 000 experience, the wait, Zwoj Egzorcyzmu) on the buffi skill, never on the player's own;
//     G1 -> P stays Kamien Duchowy Buffi 61031 (quest buffi). The books 61035-61038 have no source any more (the
//     General Store's offer is gone) - one still owned is read as before;
//   - Szybkosc and Zwiekszenie Ataku get M1 only once the buffi has a name, as at Ameria (its CheckOwnerSupport).
//
// MT2009_PLUS_BUFFI_V3 (the owner's list of 22 October 2026, cache/yohara/poprawki-runda-2026-10-22.md 1-5):
//   - three costume slots only - outfit, hairstyle, weapon: no sash on the buffi any more (WEAR_BUFFI_SASH stays in
//     the enum, nothing goes onto it, the shaman never shows one); a sash still worn there goes back to its owner at
//     the next login - the bag, or the item mall's storage when the bag is full (ReturnSash);
//   - weaker buffs: the value of every buff (not its time) times GradeFactor - M1-M10 -50%, G1-G4 -35%, G5-G10 -25%,
//     P -18% of Ameria's polys (the owner's ranges, confirmed 21 October 2026). Here, where the value is made - exact
//     per grade (the skill_proto rows 164-167 are not read for it); the client's tooltip polys are cut the same way
//     (tools/buffi/gen_buffi.py, skilldesc / skilltable);
//   - Buffi from the character's level 55 (MIN_LEVEL): the seals, the name scroll, the window's commands and the
//     costume slots refuse below it ("Buffi dostepna od 55 poziomu."); a buffi called before by a lower character is
//     sent away at its login. The starter gift (the seal for good 61026 + Zwoj Imienia 61030) is quest buffi's, at 55.
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
#include "../../libgame/include/grid.h"	// MT2009_PLUS_BUFFI_V3: the item mall's free place (ReturnSash)

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
	const int MIN_LEVEL = 55;				// MT2009_PLUS_BUFFI_V3: Buffi from the character's level 55 (the owner)

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

	// MT2009_PLUS_BUFFI_V2: the owners whose Buffi window is open (Ameria's IsLookingBuffiPage) - a costume used then
	// goes onto the buffi
	std::set<DWORD> s_setLookPage;

	// MT2009_PLUS_BUFFI_V2: the equip under way (CHARACTER::EquipItem / SwapItem set it, CanEquipNow and the sex check
	// read it) - the wear cell the client named, -1 none
	struct SEquip
	{
		DWORD dwPID;
		DWORD dwItemID;
		int iCandidate;
		SEquip() : dwPID(0), dwItemID(0), iCandidate(-1) {}
	};
	SEquip s_equip;

	// MT2009_PLUS_BUFFI_V2: the shaman skill whose ordinary book (50300) trains a buffi skill up to G1
	struct SBook
	{
		DWORD dwBuffiSkill;
		DWORD dwShamanSkill;
	};
	const SBook BOOKS[4] =
	{
		{ 164, 94 },	// Blogoslawienstwo
		{ 165, 96 },	// Pomoc Smoka
		{ 166, 110 },	// Szybkosc
		{ 167, 111 },	// Zwiekszenie Ataku
	};
	const DWORD SKILL_BOOK = 50300;

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

	// MT2009_PLUS_BUFFI_V3: Buffi from level 55 - false (and the owner told so) below it
	bool LevelOk(LPCHARACTER ch, bool bSay = true)
	{
		if (ch && ch->GetLevel() >= MIN_LEVEL)
			return true;
		if (ch && bSay)
			ch->ChatPacket(CHAT_TYPE_INFO, "[Buffi] Buffi dost\xea""pna od %d poziomu.", MIN_LEVEL);
		return false;
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

	// MT2009_PLUS_BUFFI_V2: what the shaman wears - the owner's buffi costume slots (Ameria's CheckSupportWear: the
	// outfit's vnum, the hairstyle's value 3, the weapon's vnum), a transmuted costume with its look; without a costume
	// Ameria's Czarna Szata+9 / Ekstazyjny Wachlarz+9. [0] body, [1] hair, [2] weapon, [3] sash - MT2009_PLUS_BUFFI_V3:
	// always none (the owner: no sash on the buffi; a shaman spawned before still loses its one at RefreshLook).
	DWORD Look(LPITEM item)
	{
		return item->GetTransmutation() ? item->GetTransmutation() : item->GetVnum();
	}

	void LookParts(LPCHARACTER owner, DWORD adwPart[4])
	{
		LPITEM body = owner->GetWear(WEAR_BUFFI_BODY);
		LPITEM hair = owner->GetWear(WEAR_BUFFI_HEAD);
		LPITEM weapon = owner->GetWear(WEAR_BUFFI_WEAPON);
		adwPart[0] = body ? Look(body) : ARMOR;
		adwPart[1] = 0;
		if (hair)
		{
			const TItemTable* look = ITEM_MANAGER::instance().GetTable(Look(hair));
			adwPart[1] = look ? (DWORD) look->alValues[3] : (DWORD) hair->GetValue(3);
		}
		adwPart[2] = weapon ? Look(weapon) : WEAPON;
		adwPart[3] = 0;
	}

	void RefreshLook(LPCHARACTER owner, LPCHARACTER mob)
	{
		DWORD adwPart[4];
		LookParts(owner, adwPart);
		bool bChanged = false;
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		const BYTE abPart[] = { PART_MAIN, PART_HAIR, PART_WEAPON, PART_ACCE };
#else
		const BYTE abPart[] = { PART_MAIN, PART_HAIR, PART_WEAPON };
#endif
		for (size_t i = 0; i < sizeof(abPart) / sizeof(abPart[0]); ++i)
		{
			if (mob->GetPart(abPart[i]) != adwPart[i])
			{
				mob->SetPart(abPart[i], adwPart[i]);
				bChanged = true;
			}
		}
		if (bChanged)
			mob->UpdatePacket();
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
		{
			DWORD adwPart[4];
			LookParts(owner, adwPart);
			mob->SetPart(PART_MAIN, adwPart[0]);
			mob->SetPart(PART_HAIR, adwPart[1]);
			mob->SetPart(PART_WEAPON, adwPart[2]);
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
			mob->SetPart(PART_ACCE, adwPart[3]);
#endif
		}
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

	// MT2009_PLUS_BUFFI_V3 (weaker): the part of Ameria's value a grade keeps (the owner, 22 October 2026: M1-M10
	// -50%, G1-G4 -35%, G5-G10 -25%, P -18%). The client's tooltip polys say the same (gen_buffi.py, CLIENT_FACTOR).
	double GradeFactor(BYTE bLevel)
	{
		if (bLevel >= 40)
			return 0.82;	// P
		if (bLevel >= 34)
			return 0.75;	// G5-G10
		if (bLevel >= 30)
			return 0.65;	// G1-G4
		return 0.50;		// M1-M10
	}

	// Ameria's skill_proto 164-167 (szPointPoly, iq = 226): the point(s) a level gives; MT2009_PLUS_BUFFI_V3: times
	// GradeFactor (the value only - the time stays)
	void Cast(LPCHARACTER owner, LPCHARACTER mob, const SBuff& buff, BYTE bLevel)
	{
		const double k = Power(bLevel);
		const double f = GradeFactor(bLevel);
		const long lDuration = 3600;
		switch (buff.dwSkill)
		{
			case 164:
				owner->AddAffect(buff.dwAffect, POINT_RESIST_NORMAL_DAMAGE, (long) ((226 * 0.2 + 5) * (2 * k + 0.5) / (k + 1.5) * f),
						buff.dwFlag, lDuration, 0, true);
				break;
			case 165:
				owner->AddAffect(buff.dwAffect, POINT_CRITICAL_PCT, (long) ((226 * 0.2 + 5) * (2 * k + 0.5) / (k + 1.5) * f),
						buff.dwFlag, lDuration, 0, true);
				break;
			case 166:
				owner->AddAffect(buff.dwAffect, POINT_MOV_SPEED, (long) ((5 + 35 * k) * f), buff.dwFlag, lDuration, 0, true);
				owner->AddAffect(buff.dwAffect, POINT_CASTING_SPEED, (long) ((3 + 33 * k) * f), AFF_NONE, (long) (60 + 100 * k), 0, true);
				break;
			case 167:
				owner->AddAffect(buff.dwAffect, POINT_ATT_GRADE_BONUS, (long) ((5 + (226 * 0.2 + 15) * k) * f), buff.dwFlag,
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
			// MT2009_PLUS_BUFFI_V3: or the owner under level 55
			if (!Enabled() || !owner || !owner->GetDesc() || !SealOf(owner, b) || !LevelOk(owner, false))
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
			RefreshLook(owner, mob);	// MT2009_PLUS_BUFFI_V2: a costume put onto / taken off the buffi's slots
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
		if (!LevelOk(owner))	// MT2009_PLUS_BUFFI_V3
			return false;
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
		// MT2009_PLUS_BUFFI_V2: Szybkosc and Zwiekszenie Ataku get M1 once the buffi has a name (Ameria)
		for (int i = 0; i < 4; ++i)
			if (owner->GetSkillLevel(BUFFS[i].dwSkill) == 0 && (!BUFFS[i].bNeedsName || !b.stName.empty()))
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
	// <name scrolls> <skill group>" - root/uibuffi.py (MT2009_PLUS_BUFFI_V2: the skill group, 0 = none chosen yet)
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
		Command(ch, "state 1 %d %u %d %s %d %d %d %d %ld %u %d", called ? 1 : 0, seal ? seal->GetVnum() : 0,
				name.empty() ? 0 : 1, name.empty() ? "-" : name.c_str(),
				ch->GetSkillLevel(164), ch->GetSkillLevel(165), ch->GetSkillLevel(166), ch->GetSkillLevel(167),
				aff ? (long) aff->lDuration : 0L, (unsigned int) ch->CountSpecifyItem(NAME_SCROLL), (int) ch->GetSkillGroup());
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
		// MT2009_PLUS_BUFFI_V2: Szybkosc and Zwiekszenie Ataku from M1 now (Ameria gives it at the next cast)
		bool bNew = false;
		for (int i = 0; i < 4; ++i)
			if (BUFFS[i].bNeedsName && ch->GetSkillLevel(BUFFS[i].dwSkill) == 0)
			{
				ch->SetSkillLevel(BUFFS[i].dwSkill, START_LEVEL);
				bNew = true;
			}
		if (bNew)
			ch->SkillLevelPacket();
		Spawn(ch, b);
		Say(ch, "Buffi ma nowe imi\xea. Odblokowane: Szybko\x9c\xe6 i Zwi\xeakszenie Ataku, +10% silny przeciwko bossom na 7 dni.");
	}

	// MT2009_PLUS_BUFFI_V2: "/buffi read <skill> <window> <cell>" - the shaman's ordinary skill book (50300 of the
	// matching shaman skill) dragged onto a buffi skill in the window trains that buffi skill, M1 -> G1, by the
	// engine's own book reading (LearnSkillByBook: the chance, the books a level, 20 000 experience, the wait, Zwoj
	// Egzorcyzmu / Rada Pustelnika) - on the buffi skill 164-167, never on the reader's own skill.
	void ReadBook(LPCHARACTER ch, DWORD dwSkill, int iWindow, int iCell)
	{
		const SBook* book = NULL;
		for (int i = 0; i < 4; ++i)
			if (BOOKS[i].dwBuffiSkill == dwSkill)
				book = &BOOKS[i];
		if (!book || iWindow < 0 || iWindow > 255 || iCell < 0 || iCell > 65535)
			return;
		LPITEM item = ch->GetItem(TItemPos((BYTE) iWindow, (WORD) iCell));
		if (!item || item->GetOwner() != ch || item->IsEquipped() || item->IsExchanging() || item->isLocked())
			return;
		const char* name = "";
		for (int i = 0; i < 4; ++i)
			if (BUFFS[i].dwSkill == dwSkill)
				name = i == 0 ? "B\xb3ogos\xb3""awie\xf1stwo" : i == 1 ? "Pomoc Smoka" : i == 2 ? "Szybko\x9c\xe6" : "Zwi\xea""kszenie Ataku";
		if (item->GetVnum() != SKILL_BOOK || (DWORD) item->GetSocket(0) != book->dwShamanSkill)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "[Buffi] T\xea umiej\xea""tno\x9c\xe6 trenuje Ksi\xea""ga Umiej\xea""tno\x9c""ci: %s (szaman).", name);
			return;
		}
		if (ch->GetSkillGroup() == 0)
		{
			Say(ch, "Najpierw wybierz drog\xea umiej\xea""tno\x9c""ci (Szkolenie).");
			return;
		}
		if (ch->IsPolymorphed())
		{
			Say(ch, "Nie mo\xbfesz czyta\xe6 ksi\xb1g podczas przemiany.");
			return;
		}
		const int iLevel = ch->GetSkillLevel(dwSkill);
		if (iLevel < START_LEVEL)
		{
			Say(ch, BUFFS[dwSkill - SKILL_FIRST].bNeedsName ? "Ta umiej\xea""tno\x9c\xe6 Buffi wymaga imienia (Zw\xf3j Imienia Buffi)."
					: "Najpierw przywo\xb3""aj Buffi - umiej\xea""tno\x9c""ci dostaj\xb9 wtedy M1.");
			return;
		}
		if (iLevel >= 30)
		{
			Say(ch, "Od G1 umiej\xea""tno\x9c\xe6 Buffi trenuje Kamie\xf1 Duchowy Buffi.");
			return;
		}
		if (ch->LearnSkillByBook(dwSkill))
		{
			item->SetCount(item->GetCount() - 1);
			ch->SkillLevelPacket();
		}
	}

	// ------------------------------------------------------------------ MT2009_PLUS_BUFFI_V2: the costume slots

	bool IsBuffiCell(int iWearCell)
	{
		return iWearCell >= WEAR_BUFFI_BODY && iWearCell <= WEAR_BUFFI_SASH;
	}

	// MT2009_PLUS_BUFFI_V3 (sash back): a sash worn on the buffi's old sash slot (V2) goes back to its owner, once - the
	// bag; with a full bag the item mall's storage (a free place of its grid, written as the safebox does it); with
	// both full it waits on the slot (it gives nothing there) for the next login. Idempotent: an empty slot does nothing.
	bool SashToMall(LPCHARACTER ch, LPITEM item)
	{
		if (!ch->GetDesc() || ch->GetMall())
			return false;	// the mall open in this session: its own grid would not know this item
		const DWORD dwAccount = ch->GetDesc()->GetAccountTable().id;
		char query[192];
		snprintf(query, sizeof(query), "SELECT pos, vnum FROM player.item WHERE owner_id = %u AND `window` = 'MALL'", dwAccount);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!dwAccount || !msg.get() || msg->uiSQLErrno != 0 || !msg->Get())
			return false;
		CGrid grid(SAFEBOX_PAGE_WIDTH, SAFEBOX_PAGE_COUNT * SAFEBOX_PAGE_HEIGHT);
		MYSQL_ROW row;
		while (msg->Get()->pSQLResult && (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			int iPos = 0;
			DWORD dwVnum = 0;
			str_to_number(iPos, row[0]);
			str_to_number(dwVnum, row[1]);
			const TItemTable* table = ITEM_MANAGER::instance().GetTable(dwVnum);
			const int iSize = table ? MAX(1, (int) table->bSize) : 1;
			if (iPos >= 0 && grid.IsEmpty(iPos, 1, iSize))
				grid.Put(iPos, 1, iSize);
		}
		const int iFree = grid.FindBlank(1, item->GetSize());
		if (iFree < 0)
			return false;
		item->RemoveFromCharacter();
		item->SetWindow(MALL);
		item->SetCell(ch, (WORD) iFree);
		item->Save();
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		item->SetSkipSave(true);
		M2_DESTROY_ITEM(item->RemoveFromCharacter());
		return true;
	}

	void ReturnSash(LPCHARACTER ch)
	{
		LPITEM sash = ch ? ch->GetWear(WEAR_BUFFI_SASH) : NULL;
		if (!sash)
			return;
		const DWORD dwID = sash->GetID();
		const DWORD dwVnum = sash->GetVnum();
		const int iPos = ch->GetEmptyInventoryEx(sash);
		if (iPos >= 0)
		{
			const BYTE bWindow = (BYTE) sash->GetWindowInventoryEx();
			sash->RemoveFromCharacter();
			sash->AddToCharacter(ch, TItemPos(bWindow, iPos));
			sys_log(0, "BUFFI: %s's sash %u (id %u) from the buffi back to the bag", ch->GetName(), dwVnum, dwID);
			Say(ch, "Buffi nie nosi ju\xbf szarfy - szarfa wr\xf3""ci\xb3""a do twojego ekwipunku.");
			return;
		}
		if (SashToMall(ch, sash))
		{
			sys_log(0, "BUFFI: %s's sash %u (id %u) from the buffi to the item mall's storage", ch->GetName(), dwVnum, dwID);
			Say(ch, "Buffi nie nosi ju\xbf szarfy - ekwipunek jest pe\xb3""ny, szarfa czeka w magazynie przedmiot\xf3w (ItemShop).");
			return;
		}
		Say(ch, "Buffi nie nosi ju\xbf szarfy - zwolnij miejsce w ekwipunku, szarfa wr\xf3""ci przy nast\xea""pnym logowaniu.");
	}

	// the buffi cell of a costume (-1: no costume of the four)
	int CellOf(CItem* item)
	{
		if (!item || item->GetType() != ITEM_COSTUME)
			return -1;
		switch (item->GetSubType())
		{
			case COSTUME_BODY:		return WEAR_BUFFI_BODY;
			case COSTUME_HAIR:		return WEAR_BUFFI_HEAD;
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
			case COSTUME_WEAPON:	return WEAR_BUFFI_WEAPON;
#endif
			// MT2009_PLUS_BUFFI_V3: no sash (the owner) - a sash used with the window open goes onto its owner as ever
		}
		return -1;
	}

	// the buffi cell an equip of this item goes to: -2 not the buffi's (the engine as ever), -1 refused, else the cell
	int TargetCell(LPCHARACTER ch, CItem* item, int iCandidate)
	{
		if (!ch || !item || !ch->IsPC())
			return -2;
		// worn on the buffi already: its own cell (MoveItem, UnequipItem, the safebox ask it)
		if (item->IsEquipped() && item->GetOwner() == ch && IsBuffiCell((int) item->GetCell() - INVENTORY_MAX_NUM))
			return (int) item->GetCell() - INVENTORY_MAX_NUM;
		const bool bAsked = IsBuffiCell(iCandidate);
		if (!bAsked && !(iCandidate < 0 && s_setLookPage.count(ch->GetPlayerID())))
			return -2;
		const int iCell = CellOf(item);
		if (!Counts(ch) || !Enabled() || !LevelOk(ch, false))	// MT2009_PLUS_BUFFI_V3: from level 55
			return bAsked ? -1 : -2;
		if (iCell < 0)
			return bAsked ? -1 : -2;		// the open window does not change where an armour or a mount goes
		if (bAsked && iCell != iCandidate)
			return -1;
		return iCell;
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
	if (!LevelOk(ch))	// MT2009_PLUS_BUFFI_V3: from level 55
		return 0;
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
	if (ch)
		s_setLookPage.erase(ch->GetPlayerID());		// MT2009_PLUS_BUFFI_V2: the window opens closed
	if (!Counts(ch))
		return;
	ReturnSash(ch);		// MT2009_PLUS_BUFFI_V3: whether Buffi is on or not
	if (!Enabled())
		return;
	LPITEM seal = FindSeal(ch, true);
	if (seal && !LevelOk(ch, false))
	{
		SendAway(ch, seal);		// MT2009_PLUS_BUFFI_V3: called before by a character under level 55 - it stays away
		return;
	}
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

// ---------------------------------------------------------------------- MT2009_PLUS_BUFFI_V2: the costume slots'
// hooks (server-patches/buffi (cell), (begin), (swap), (job), (sex), (points))

// item.cpp, CItem::FindEquipCell (its start): the buffi's cell for a costume dragged onto it (the candidate) or used
// while the Buffi window is open, and the cell of one worn on the buffi. -2 not the buffi's, -1 refused, else the cell.
int Mt2009BuffiFindEquipCell(LPCHARACTER ch, CItem* item, int iCandidateCell)
{
	return TargetCell(ch, item, iCandidateCell);
}

// char_item.cpp, CHARACTER::EquipItem (its start) and SwapItem (before its CanEquipNow): the cell the client named,
// for CanEquipNow and the sex check below.
void Mt2009BuffiEquipBegin(LPCHARACTER ch, LPITEM item, int iCandidateCell)
{
	s_equip.dwPID = ch ? ch->GetPlayerID() : 0;
	s_equip.dwItemID = item ? item->GetID() : 0;
	s_equip.iCandidate = iCandidateCell;
}

static int EquipTarget(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item)
		return -2;
	const int iCandidate = (s_equip.dwPID == ch->GetPlayerID() && s_equip.dwItemID == item->GetID()) ? s_equip.iCandidate : -1;
	return TargetCell(ch, item, iCandidate);
}

// char_item.cpp, CHARACTER::CanEquipNow (before the class check): a costume for the buffi is checked against the
// shaman, not against its owner's class (Ameria's IsLookingBuffiPage branch). -1 not for the buffi (the class check
// as ever), 0 refused, 1 allowed (the class check skipped).
int Mt2009BuffiCanEquip(LPCHARACTER ch, LPITEM item)
{
	const int iCell = EquipTarget(ch, item);
	if (iCell == -2)
		return -1;
	if (iCell < 0 && !Enabled())
	{
		Say(ch, "Buffi jest wy\xb3\xb9""czony na tym serwerze.");
		return 0;
	}
	if (iCell < 0 && !LevelOk(ch))	// MT2009_PLUS_BUFFI_V3: from level 55
		return 0;
	// MT2009_PLUS_BUFFI_V3: three slots - no sash
	if (iCell < 0 && s_equip.iCandidate == WEAR_BUFFI_SASH)
	{
		Say(ch, "Buffi nie nosi szarfy - ma tylko kostium, fryzur\xea i nak\xb3""adk\xea na bro\xf1.");
		return 0;
	}
	if (iCell < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "[Buffi] To miejsce Buffi przyjmuje tylko: %s.",
				s_equip.iCandidate == WEAR_BUFFI_BODY ? "kostium (str\xf3j)" : s_equip.iCandidate == WEAR_BUFFI_HEAD ? "kostium fryzury" :
				"kostium broni szamana");
		return 0;
	}
	if (item->GetAntiFlag() & ITEM_ANTIFLAG_SHAMAN)
	{
		Say(ch, "Buffi jest szamank\xb9 - nie mo\xbf""e nosi\xe6 tego kostiumu.");
		return 0;
	}
	return 1;
}

// char_item.cpp, FN_check_item_sex (its start): the buffi is a woman - an outfit or a hairstyle for her must not be a
// man's only (Ameria checks the same at its IsLookingBuffiPage). -1 not for the buffi, 0 refused, 1 allowed.
int Mt2009BuffiCheckSex(LPCHARACTER ch, LPITEM item)
{
	const int iCell = EquipTarget(ch, item);
	if (iCell == -2)
		return -1;
	if (iCell < 0)
		return 0;
	if ((iCell == WEAR_BUFFI_BODY || iCell == WEAR_BUFFI_HEAD) && IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_FEMALE))
		return 0;
	return 1;
}

// item.cpp, CItem::ModifyPoints (its start): a costume worn on the buffi gives its owner nothing - no bonus, no part
// of the owner's look (Ameria: "Buffi Costumes do not offer any bonus"). Whether the buffi is on or not.
bool Mt2009BuffiWornItem(CItem* item)
{
	return item && item->IsEquipped() && IsBuffiCell((int) item->GetCell() - INVENTORY_MAX_NUM);
}

// "/buffi info|toggle|name <name>" - root/uibuffi.py (the P key, the inventory's side bar)
// MT2009_PLUS_BUFFI_V2: "/buffi page 1|0" (the window open / closed - Ameria's /buffi_costume_page) and
// "/buffi read <skill> <window> <cell>" (a shaman's skill book dragged onto a buffi skill)
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
	// MT2009_PLUS_BUFFI_V3: Buffi from level 55 - below it the window's commands are refused (closing it is fine)
	if (!LevelOk(ch, false))
	{
		s_setLookPage.erase(ch->GetPlayerID());
		if (strcmp(sub, "page"))
		{
			LevelOk(ch);
			Command(ch, "low %d", MIN_LEVEL);
		}
		return;
	}
	if (!strcmp(sub, "toggle"))
	{
		LPITEM seal = FindSeal(ch, true);
		if (!seal)
			seal = FindSeal(ch, false);
		if (!seal)
		{
			Say(ch, "Nie masz piecz\xea""ci Buffi (ItemShop; prezent na 55 poziomie).");
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
	if (!strcmp(sub, "page"))
	{
		if (atoi(arg) == 1)
			s_setLookPage.insert(ch->GetPlayerID());
		else
			s_setLookPage.erase(ch->GetPlayerID());
		return;
	}
	if (!strcmp(sub, "read"))
	{
		char szWindow[16] = "", szCell[16] = "";
		const char* more = one_argument(rest, arg, sizeof(arg));
		more = one_argument(more, szWindow, sizeof(szWindow));
		one_argument(more, szCell, sizeof(szCell));
		if (*arg && *szWindow && *szCell)
			ReadBook(ch, (DWORD) atoi(arg), atoi(szWindow), atoi(szCell));
		SendState(ch);
		return;
	}
	SendState(ch);
}
