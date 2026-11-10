// MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych (server-patches/pety/README.md): the game's part.
//
// The official growth pet as the wiki describes it (pl first, tr where pl is silent), on the layout of the Anka2
// port (growth_pet.cpp there) but written anew for this engine and with Anka2's faults fixed (its revive trusted the
// client's stack counts and could dereference an empty slot; eggs past its hatch table read out of bounds; no skill
// proto data). Summary:
//   - an egg (55401-55414) is hatched for 100 000 Yang and a name (4-20 letters) into a seal (55701-55714); the pet's
//     id is socket 2 of the seal (and of the Klatka Transportowa it may travel in), its row is player.growth_pet;
//   - levels 1-105 from the owner's kill experience (the red bars, 90 %) and from items (the blue bar, 10 %), never
//     above the owner's level; evolutions Mlody -> Dziki (40) -> Dzielny (80) -> Bohaterski (81+; no age needed) ->
//     Przebudzony (105, champion level 1) -> Mocny (champion level 14 -> 15), champion levels 1-30 from champion
//     experience on the Sung Ma maps (never above the owner's champion level);
//   - type 1-8 (rolled 1-6 at the hatching; Zaczaruj zwierzaka 1-8, 1-6 for three species), the owner's max HP /
//     defence / max SP bonuses growing with the levels, the champion's Wola SungMa (ODP) / Przebicie bloku /
//     Precyzja growing with the champion levels, plus the age bonus;
//   - 3 skill slots (1-3 open by species), 23 skills from books (from Bohaterski), levels 1-20 for 2 000 000 Yang
//     each; two potential slots of a champion pet filled with eggs;
//   - life: random per species, Odzywka refills it, eggs and other seals add 3-5 %; dead: Odzywka (50 %, the age
//     from 1 day) or Boska Odzywka (100 %, 80 % of the age kept).
// The pets live in this core's memory while a character here holds their seals or cages; the db core caches and
// writes them (growth_pet_db.cpp). A pet is saved on every important change and its experience at most every
// SAVE_DELAY seconds; the character's logout / warp saves the rest.

#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "desc.h"
#include "desc_client.h"
#include "desc_manager.h"
#include "packet.h"
#include "db.h"
#include "banword.h"
#include "sectree_manager.h"
#include "mob_manager.h"
#include "affect.h"
#include "safebox.h"
#include "vector.h"
#include "growth_pet.h"
#include "growth_pet_data.h"
#include "questmanager.h"

#include <map>
#include <set>
#include <string>
#include <vector>

extern int passes_per_sec;
extern bool battle_is_attackable(LPCHARACTER ch, LPCHARACTER victim);

namespace growth_pet
{
	using namespace growth_pet_data;

	// libthecore's MIN / MAX / MINMAX (utils.h) take and return int: a 64-bit value given to them is cut to int first
	// (MIN(0ULL, 0xFFFFFFFFULL) == -1 - the 4.294.967.295 exp of a new pet in 3.0.13). Every 64-bit min / max here goes
	// through these.
	template <typename T> inline T Min64(T a, T b) { return b < a ? b : a; }
	template <typename T> inline T Max64(T a, T b) { return a < b ? b : a; }
	template <typename T> inline T Clamp64(T lo, T v, T hi) { return v < lo ? lo : (hi < v ? hi : v); }
	typedef unsigned long long U64;
	typedef long long S64;

	enum
	{
		STAGE_YOUNG = 1, STAGE_WILD = 2, STAGE_VALIANT = 3, STAGE_HEROIC = 4, STAGE_AWAKENED = 5, STAGE_MIGHTY = 6,
		SKILL_OPEN_STAGE = STAGE_HEROIC,
		DAY = 24 * 60 * 60,
		SAVE_DELAY = 60,
		BAG_VNUM = 55002,
		FEED_VNUM = 55001,
		PREMIUM_FEED_VNUM = 55100,
		SKILL_HEAL = 10, SKILL_INVINCIBLE = 17, SKILL_REMOVAL = 18, SKILL_FEATHER = 23,
		SKILL_COUNT = 23,
		FEATHER_MAX_DAMAGE = 1400,
	};
	const long long HATCH_PRICE = 100000;
	const long long RENAME_PRICE = 100000;
	const long long SKILL_UPGRADE_PRICE = 2000000;
	const long long BAG_SECONDS = 30LL * DAY;

	struct Pet
	{
		TGrowthPet d;
		DWORD holder;			// the pid holding its seal or cage on this core
		DWORD mobVid;			// the summoned mob
		bool dirty;
		time_t lastSave;
		DWORD potentialCooltime[GROWTH_PET_POTENTIAL_SLOTS];
		time_t featherUntil;	// Lekkie jak Piorko: the dash's end
		int featherMin;
		Pet() : holder(0), mobVid(0), dirty(false), lastSave(0), featherUntil(0), featherMin(0)
		{
			memset(&d, 0, sizeof(d));
			memset(potentialCooltime, 0, sizeof(potentialCooltime));
		}
	};

	struct Owner
	{
		DWORD summoned;			// pet id
		time_t invincibleUntil;
		bool pendingAsked;
		std::string skillLog;	// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1: the last logged bonus line (a log only on change)
		time_t skillLogAt;
		Owner() : summoned(0), invincibleUntil(0), pendingAsked(false), skillLogAt(0) {}
	};

	std::map<DWORD, Pet> s_pets;
	std::map<DWORD, Owner> s_owners;
	std::map<DWORD, DWORD> s_mobToPet;	// summoned mob vid -> pet id
	std::vector<TGrowthPetSkillTable> s_skills;
	std::map<unsigned long long, size_t> s_skillIndex;	// (seal << 8 | skill) -> s_skills index
	LPEVENT s_tick = NULL;

	// ---- small helpers -------------------------------------------------------------------------------------------

	time_t Now()
	{
		return (time_t)get_global_time();
	}

	void Say(LPCHARACTER ch, const char* text)
	{
		if (ch && ch->GetDesc() && !ch->GetDesc()->IsBot())
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", text);
	}

	void Sayf(LPCHARACTER ch, const char* fmt, ...)
	{
		if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
			return;
		char text[512];
		va_list args;
		va_start(args, fmt);
		vsnprintf(text, sizeof(text), fmt, args);
		va_end(args);
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", text);
	}

	const Species* FindSpeciesBySeal(DWORD seal)
	{
		for (size_t i = 0; i < SPECIES_COUNT; ++i)
			if (SPECIES[i].seal == seal)
				return &SPECIES[i];
		return NULL;
	}

	const Species* FindSpeciesByEgg(DWORD egg)
	{
		for (size_t i = 0; i < SPECIES_COUNT; ++i)
			if (SPECIES[i].egg == egg)
				return &SPECIES[i];
		return NULL;
	}

	bool IsPetItem(LPITEM item)
	{
		return item && item->GetType() == ITEM_PET;
	}

	bool IsSeal(LPITEM item)
	{
		return IsPetItem(item) && item->GetSubType() == PET_UPBRINGING && FindSpeciesBySeal(item->GetVnum()) != NULL;
	}

	bool IsBag(LPITEM item)
	{
		return IsPetItem(item) && item->GetSubType() == PET_BAG && item->GetVnum() == BAG_VNUM;
	}

	bool IsEgg(LPITEM item)
	{
		return IsPetItem(item) && item->GetSubType() == PET_EGG && FindSpeciesByEgg(item->GetVnum()) != NULL;
	}

	Pet* FindPet(DWORD id)
	{
		std::map<DWORD, Pet>::iterator it = s_pets.find(id);
		return it == s_pets.end() ? NULL : &it->second;
	}

	Owner& GetOwner(LPCHARACTER ch)
	{
		return s_owners[ch->GetPlayerID()];
	}

	// The item is in one of ch's bags (not the storeroom, not a shop, not a trade window).
	bool IsHeldBy(LPITEM item, LPCHARACTER ch)
	{
		if (!item || !ch || item->GetOwner() != ch || item->IsExchanging())
			return false;
		const BYTE w = item->GetWindow();
		return w == INVENTORY || Mt2009IsSpecialWindow(w);
	}

	LPITEM FindHeldItemByPos(LPCHARACTER ch, const TItemPos& pos)
	{
		if (!ch || !pos.IsValidItemPosition())
			return NULL;
		if (pos.window_type != INVENTORY && !Mt2009IsSpecialWindow(pos.window_type))
			return NULL;
		LPITEM item = ch->GetItem(pos);
		return IsHeldBy(item, ch) ? item : NULL;
	}

	// The seal of a pet in ch's bags.
	LPITEM FindSealOf(LPCHARACTER ch, DWORD petId)
	{
		const int cells = ch->GetInventoryMaxCount();
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (IsSeal(item) && (DWORD)item->GetSocket(2) == petId)
				return item;
		}
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
			for (WORD c = 0; c < SPECIAL_INVENTORY_MAX_NUM; ++c)
			{
				LPITEM item = ch->Mt2009SpecialGetItem(w, c);
				if (IsSeal(item) && (DWORD)item->GetSocket(2) == petId)
					return item;
			}
		return NULL;
	}

	int AgeDays(const Pet& p)
	{
		const long long age = (long long)Now() - p.d.llBirthday;
		return age > 0 ? (int)(age / DAY) : 0;
	}

	bool IsAlive(const Pet& p)
	{
		return p.d.llEndTime > (long long)Now();
	}

	int Stage(const Pet& p)
	{
		return MINMAX(1, (int)p.d.bEvolution, (int)STAGE_MIGHTY);
	}

	bool IsChampion(const Pet& p)
	{
		return Stage(p) >= STAGE_AWAKENED;
	}

	unsigned long long NeedMobExpOf(int level)
	{
		return level >= 1 && level <= GROWTH_PET_MAX_LEVEL ? EXP[level - 1][0] : 0ULL;
	}

	unsigned long long NeedItemExpOf(int level)
	{
		return level >= 1 && level <= GROWTH_PET_MAX_LEVEL ? EXP[level - 1][1] : 0ULL;
	}

	unsigned long long NeedChampionExpOf(int cl)
	{
		return cl >= 1 && cl <= GROWTH_PET_CHAMPION_MAX_LEVEL ? CHAMPION_EXP[cl - 1][0] : 0ULL;
	}

	unsigned long long NeedChampionItemExpOf(int cl)
	{
		return cl >= 1 && cl <= GROWTH_PET_CHAMPION_MAX_LEVEL ? CHAMPION_EXP[cl - 1][1] : 0ULL;
	}

	// The highest level the pet's stage allows (champion level for 5/6).
	int StageCap(const Pet& p)
	{
		switch (Stage(p))
		{
			case STAGE_YOUNG: return 40;
			case STAGE_WILD: return 80;
			case STAGE_VALIANT:
			case STAGE_HEROIC: return GROWTH_PET_MAX_LEVEL;
			case STAGE_AWAKENED: return 14;
			default: return GROWTH_PET_CHAMPION_MAX_LEVEL;
		}
	}

	int OpenSkillSlots(const Pet& p)
	{
		int n = 0;
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			n += p.d.aSkill[i].bLocked ? 0 : 1;
		return n;
	}

	int OpenPotentialSlots(const Pet& p)
	{
		if (!IsChampion(p))
			return 0;
		return p.d.dwChampionLevel >= 15 ? 2 : (p.d.dwChampionLevel >= 1 ? 1 : 0);
	}

	// ---- the skill proto -----------------------------------------------------------------------------------------

	const TGrowthPetSkillTable* SkillProto(DWORD seal, BYTE skill)
	{
		std::map<unsigned long long, size_t>::const_iterator it = s_skillIndex.find(((unsigned long long)seal << 8) | skill);
		if (it == s_skillIndex.end())
			it = s_skillIndex.find(skill);
		return it == s_skillIndex.end() ? NULL : &s_skills[it->second];
	}

	const TGrowthPetSkillTable* BaseSkillProto(BYTE skill)
	{
		std::map<unsigned long long, size_t>::const_iterator it = s_skillIndex.find(skill);
		return it == s_skillIndex.end() ? NULL : &s_skills[it->second];
	}

	bool IsAutoSkill(BYTE skill)
	{
		const TGrowthPetSkillTable* t = BaseSkillProto(skill);
		return t && t->bType == GROWTH_PET_SKILL_USE_AUTO;
	}

	// One unit of a skill's value table (one per cent / one metre; Niesmiertelnosc 0.1 s).
	int SkillUnit(const TGrowthPetSkillTable* t)
	{
		if (!t)
			return 10;
		if (!strcmp(t->szUnit, "hp") || !strcmp(t->szUnit, "dmg") || !strcmp(t->szUnit, "s10"))
			return 1;
		return 10;
	}

	// The value of a skill at skill level k for this pet (its species, type and level); potential skills (champion
	// pets) take the base table at their level.
	int SkillValue(const Pet& p, BYTE skill, int k, bool potential)
	{
		k = MINMAX(1, k, (int)GROWTH_PET_SKILL_LEVEL_MAX);
		const TGrowthPetSkillTable* base = BaseSkillProto(skill);
		if (!base)
			return 0;
		const long long baseK = base->adwCurve[k - 1];
		if (potential)
			return (int)baseK;
		const TGrowthPetSkillTable* t = SkillProto(p.d.dwVnum, skill);
		const int type = MINMAX(1, (int)p.d.bType, 8);
		const long long base20 = base->adwCurve[GROWTH_PET_SKILL_LEVEL_MAX - 1];
		const long long v20 = t ? t->adwValue[type - 1] : base20;
		long long vk = base20 > 0 ? baseK * v20 / base20 : baseK;
		if (k == GROWTH_PET_SKILL_LEVEL_MAX)
			vk = v20;
		const int level = IsChampion(p) ? GROWTH_PET_MAX_LEVEL : MINMAX(1, (int)p.d.dwLevel, (int)GROWTH_PET_MAX_LEVEL);
		if (level >= GROWTH_PET_MAX_LEVEL || v20 <= 0)
			return (int)vk;
		const BYTE* grow = t ? t->abGrowLevel : base->abGrowLevel;
		long long v20AtLevel;
		if (!grow[0])
			v20AtLevel = v20 * (800 + 200 * MAX(0, level - 81) / 24) / 1000;	// continuous: 80 % at 81, 100 % at 105
		else
		{
			int ticks = 0;
			for (int i = 0; i < 8 && grow[i]; ++i)
				if (grow[i] > level)
					++ticks;
			v20AtLevel = v20 - (long long)ticks * SkillUnit(t ? t : base);
		}
		long long v = vk * Max64<S64>(0, v20AtLevel) / v20;
		const int unit = SkillUnit(t ? t : base);
		if (unit > 1 && v20 % unit == 0)
			v -= v % unit;
		return (int)Max64<S64>(0, v);
	}

	int SkillActivatePct(const Pet& p, BYTE skill, int k, int value)
	{
		k = MINMAX(1, k, (int)GROWTH_PET_SKILL_LEVEL_MAX);
		if (skill == SKILL_REMOVAL)
			return value / 10;
		const TGrowthPetSkillTable* t = SkillProto(p.d.dwVnum, skill);
		return t ? t->abActivate[k - 1] : 0;
	}

	int SkillDuration(const Pet& p, BYTE skill, int k, int value)
	{
		k = MINMAX(1, k, (int)GROWTH_PET_SKILL_LEVEL_MAX);
		if (skill == SKILL_INVINCIBLE)
			return value;
		const TGrowthPetSkillTable* t = SkillProto(p.d.dwVnum, skill);
		return t ? t->abDuration[k - 1] : 0;
	}

	int PotentialLevel(const Pet& p, int slot)
	{
		const int cl = (int)p.d.dwChampionLevel;
		int lv = cl >= 30 ? 6 : cl >= 25 ? 5 : cl >= 20 ? 4 : cl >= 15 ? 3 : 1;
		// tr/de: the full potential needs both slots filled; with the second slot open and empty at most 2
		if (OpenPotentialSlots(p) >= 2 && !p.d.aPotential[slot ^ 1].dwEggVnum)
			lv = MIN(lv, 2);
		return lv;
	}

	bool PotentialActive(const Pet& p, int slot)
	{
		return slot < OpenPotentialSlots(p) && p.d.aPotential[slot].dwEggVnum && p.d.aPotential[slot].bSkill &&
				(time_t)p.d.aPotential[slot].dwEndTime > Now();
	}

	// ---- packets to the owner ------------------------------------------------------------------------------------

	LPCHARACTER HolderChar(const Pet& p)
	{
		return p.holder ? CHARACTER_MANAGER::instance().FindByPID(p.holder) : NULL;
	}

	bool HasClient(LPCHARACTER ch)
	{
		return ch && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	DWORD PointOf(const Pet& p, int i)
	{
		switch (i)
		{
			case POINT_UPBRINGING_PET_LEVEL: return p.d.dwLevel;
			case POINT_UPBRINGING_PET_EXP: return (DWORD)Min64<U64>(p.d.ullExp, 0xFFFFFFFFULL);
			case POINT_UPBRINGING_PET_ITEM_EXP: return (DWORD)Min64<U64>(p.d.ullItemExp, 0xFFFFFFFFULL);
			case POINT_UPBRINGING_PET_NEXT_EXP:
				return (DWORD)Min64<U64>(NeedMobExpOf(p.d.dwLevel) + NeedItemExpOf(p.d.dwLevel), 0xFFFFFFFFULL);
			case POINT_UPBRINGING_PET_EVOL_LEVEL: return Stage(p);
			case POINT_UPBRINGING_PET_HP: return p.d.dwHP;
			case POINT_UPBRINGING_PET_DEF_GRADE: return p.d.dwDef;
			case POINT_UPBRINGING_PET_SP: return p.d.dwSP;
			case POINT_UPBRINGING_DURATION: return (DWORD)Max64<S64>(0, p.d.llEndTime);
			case POINT_UPBRINGING_MAX_DURATION: return (DWORD)Max64<S64>(0, p.d.llMaxTime);
			case POINT_UPBRINGING_BIRTHDAY: return (DWORD)Max64<S64>(0, p.d.llBirthday);
			case POINT_UPBRINGING_CHAMPION_LEVEL: return p.d.dwChampionLevel;
			case POINT_UPBRINGING_CHAMPION_EXP: return (DWORD)Min64<U64>(p.d.ullChampionExp, 0xFFFFFFFFULL);
			case POINT_UPBRINGING_CHAMPION_ITEM_EXP: return (DWORD)Min64<U64>(p.d.ullChampionItemExp, 0xFFFFFFFFULL);
			case POINT_UPBRINGING_CHAMPION_NEXT_EXP:
				return (DWORD)Min64<U64>(NeedChampionExpOf(p.d.dwChampionLevel) + NeedChampionItemExpOf(p.d.dwChampionLevel), 0xFFFFFFFFULL);
			case POINT_UPBRINGING_CHAMPION_RES: return p.d.dwChampionRes;
			case POINT_UPBRINGING_CHAMPION_BLOCK_PEN: return p.d.dwChampionBlockPen;
			case POINT_UPBRINGING_CHAMPION_PRECISION: return p.d.dwChampionPrecision;
			case POINT_UPBRINGING_TYPE: return p.d.bTypeKnown ? p.d.bType : 0;
			case POINT_UPBRINGING_SKILL_SLOTS: return OpenSkillSlots(p);
		}
		return 0;
	}

	void FillSet(const Pet& p, TPacketGCPetSet& pack, BYTE header)
	{
		memset(&pack, 0, sizeof(pack));
		pack.header = header;
		pack.dwID = p.d.dwID;
		pack.dwSummonItemVnum = p.d.dwVnum;
		strlcpy(pack.szName, p.d.szName, sizeof(pack.szName));
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
		{
			pack.aSkill[i].bLocked = p.d.aSkill[i].bLocked;
			pack.aSkill[i].bSkill = p.d.aSkill[i].bSkill;
			pack.aSkill[i].bLevel = p.d.aSkill[i].bLevel;
			pack.aSkill[i].dwCooltime = p.d.aSkill[i].dwCooltime;
		}
		for (int i = 0; i < POINT_UPBRINGING_MAX_NUM; ++i)
			pack.dwPoints[i] = PointOf(p, i);
	}

	void SendSkills(LPCHARACTER ch, const Pet& p);
	void SendPotential(LPCHARACTER ch, const Pet& p);

	void SendSet(LPCHARACTER ch, const Pet& p)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetSet pack;
		FillSet(p, pack, HEADER_GC_PET_SET);
		ch->GetDesc()->Packet(&pack, sizeof(pack));
		SendSkills(ch, p);
		SendPotential(ch, p);
	}

	void SendDelete(LPCHARACTER ch, DWORD id)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetDelete pack;
		pack.header = HEADER_GC_PET_DEL;
		pack.dwID = id;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendPoint(LPCHARACTER ch, const Pet& p, int point)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetPointUpdate pack;
		pack.header = HEADER_GC_PET_POINT_CHANGE;
		pack.dwID = p.d.dwID;
		pack.bPoint = (BYTE)point;
		pack.dwValue = PointOf(p, point);
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendSub(LPCHARACTER ch, BYTE sub)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPet pack;
		pack.header = HEADER_GC_PET;
		pack.subheader = sub;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendSummon(LPCHARACTER ch, DWORD id)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetSummon pack;
		pack.header = HEADER_GC_PET_SUMMON;
		pack.dwID = id;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendSkills(LPCHARACTER ch, const Pet& p)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetSkillUpdate pack;
		memset(&pack, 0, sizeof(pack));
		pack.header = HEADER_GC_PET_SKILL_UPDATE;
		pack.dwID = p.d.dwID;
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
		{
			TGrowthPetSkillUpdate& s = pack.aSkill[i];
			s.bLocked = p.d.aSkill[i].bLocked;
			s.bSkill = p.d.aSkill[i].bSkill;
			s.bLevel = p.d.aSkill[i].bLevel;
			s.dwCooltime = p.d.aSkill[i].dwCooltime;
			if (!s.bSkill)
				continue;
			for (int k = 1; k <= GROWTH_PET_SKILL_LEVEL_MAX; ++k)
			{
				const int v = SkillValue(p, s.bSkill, k, false);
				s.wSkillFormula2[k - 1] = (WORD)MINMAX(0, v, 65535);
				s.bSkillFormula1[k - 1] = (BYTE)MINMAX(0, SkillActivatePct(p, s.bSkill, k, v), 100);
				s.bSkillFormula3[k - 1] = (BYTE)MINMAX(0, SkillDuration(p, s.bSkill, k, v), 255);
			}
		}
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendPotential(LPCHARACTER ch, const Pet& p)
	{
		if (!HasClient(ch))
			return;
		TPacketGCPetPotential pack;
		memset(&pack, 0, sizeof(pack));
		pack.header = HEADER_GC_PET_POTENTIAL;
		pack.dwID = p.d.dwID;
		pack.bOpenSlots = (BYTE)OpenPotentialSlots(p);
		for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
		{
			pack.aSlot[i].dwEggVnum = p.d.aPotential[i].dwEggVnum;
			pack.aSlot[i].bSkill = p.d.aPotential[i].bSkill;
			pack.aSlot[i].bLevel = (BYTE)(p.d.aPotential[i].bSkill ? PotentialLevel(p, i) : 0);
			pack.aSlot[i].dwEndTime = p.d.aPotential[i].dwEndTime;
		}
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	// ---- saving ----------------------------------------------------------------------------------------------------

	void SaveNow(Pet& p)
	{
		if (!p.d.dwID)
			return;
		p.d.dwOwner = p.d.bState == GROWTH_PET_STATE_BAG ? 0 : p.holder;
		db_clientdesc->DBPacket(HEADER_GD_GROWTH_PET_SAVE, 0, &p.d, sizeof(p.d));
		p.dirty = false;
		p.lastSave = Now();
	}

	void MarkDirty(Pet& p)
	{
		p.dirty = true;
	}

	void DeleteRow(DWORD id)
	{
		TPacketGDGrowthPetDelete pack;
		pack.dwID = id;
		db_clientdesc->DBPacket(HEADER_GD_GROWTH_PET_DELETE, 0, &pack, sizeof(pack));
	}

	void AskLoad(LPCHARACTER ch, BYTE reason, DWORD param, const std::vector<DWORD>& ids)
	{
		if (!ch || !ch->GetDesc())
			return;
		size_t i = 0;
		do
		{
			TPacketGDGrowthPetLoad pack;
			memset(&pack, 0, sizeof(pack));
			pack.dwPID = ch->GetPlayerID();
			pack.bReason = reason;
			pack.dwParam = param;
			for (; i < ids.size() && pack.bCount < GROWTH_PET_LOAD_MAX; ++i)
				pack.adwID[pack.bCount++] = ids[i];
			if (!pack.bCount && reason != GROWTH_PET_LOAD_PENDING)
				return;
			db_clientdesc->DBPacket(HEADER_GD_GROWTH_PET_LOAD, ch->GetDesc()->GetHandle(), &pack, sizeof(pack));
		} while (i < ids.size());
	}

	// ---- stats -----------------------------------------------------------------------------------------------------

	int AgeBonus(const Pet& p)
	{
		return MIN((int)AGE_BONUS_MAX_DAYS, AgeDays(p));	// +0.001 % a day
	}

	DWORD Roll(int a, int b)
	{
		return (DWORD)number(MIN(a, b), MAX(a, b));
	}

	// The gains of one level (stat k: 0 HP, 1 DEF, 2 SP).
	void LevelGains(Pet& p, int level, DWORD gain[3])
	{
		const int type = MINMAX(1, (int)p.d.bType, 8);
		const DWORD applies[3] = { p.d.dwHPApply, p.d.dwDefApply, p.d.dwSPApply };
		for (int k = 0; k < 3; ++k)
		{
			gain[k] = 0;
			const WORD every = TYPE_GAIN[type - 1][k][0];
			if (level < STAT_FIRST_LEVEL || !every || level % every)
				continue;
			const DWORD base = (type % 2 == 0) ? applies[k] : Roll(TYPE_GAIN[type - 1][k][1], TYPE_GAIN[type - 1][k][2]);
			gain[k] = base + AgeBonus(p);
		}
	}

	void ChampionGains(Pet& p, int cl, DWORD gain[3])
	{
		const int type = MINMAX(1, (int)p.d.bType, 8);
		// MT2009_PLUS_PET_CHAMPION_GAIN_FIX_V1 (player report, 10 November 2026): the apply fields keep the champion start values in
		// their high 16 bits (<< 16, see the start helpers below) - only the low 16 bits are the even types' fixed gain;
		// adding the whole field gave e.g. 39 x (100 + 65276) / 100 ~ 25496 at a champion level-up.
		const DWORD applies[3] = { p.d.dwChampionResApply & 0xFFFF, p.d.dwChampionBlockPenApply & 0xFFFF, p.d.dwChampionPrecisionApply & 0xFFFF };
		for (int k = 0; k < 3; ++k)
		{
			gain[k] = 0;
			const WORD every = CHAMPION_TYPE_GAIN[type - 1][k][0];
			if (cl < 1 || !every || cl % every)
				continue;
			const DWORD base = (type % 2 == 0) ? applies[k] : Roll(CHAMPION_TYPE_GAIN[type - 1][k][1], CHAMPION_TYPE_GAIN[type - 1][k][2]);
			gain[k] = base + AgeBonus(p);
		}
	}

	void AddLevelGains(Pet& p, int level)
	{
		DWORD g[3];
		LevelGains(p, level, g);
		p.d.dwHP += g[0];
		p.d.dwDef += g[1];
		p.d.dwSP += g[2];
	}

	void AddChampionGains(Pet& p, int cl)
	{
		DWORD g[3];
		ChampionGains(p, cl, g);
		p.d.dwChampionRes += g[0];
		p.d.dwChampionBlockPen += g[1];
		p.d.dwChampionPrecision += g[2];
	}

	// The even types' fixed gains (rolled with the type).
	void RollApplies(Pet& p)
	{
		const int type = MINMAX(1, (int)p.d.bType, 8);
		p.d.dwHPApply = Roll(TYPE_GAIN[type - 1][0][1], TYPE_GAIN[type - 1][0][2]);
		p.d.dwDefApply = Roll(TYPE_GAIN[type - 1][1][1], TYPE_GAIN[type - 1][1][2]);
		p.d.dwSPApply = Roll(TYPE_GAIN[type - 1][2][1], TYPE_GAIN[type - 1][2][2]);
		p.d.dwChampionResApply = Roll(CHAMPION_TYPE_GAIN[type - 1][0][1], CHAMPION_TYPE_GAIN[type - 1][0][2]);
		p.d.dwChampionBlockPenApply = Roll(CHAMPION_TYPE_GAIN[type - 1][1][1], CHAMPION_TYPE_GAIN[type - 1][1][2]);
		p.d.dwChampionPrecisionApply = Roll(CHAMPION_TYPE_GAIN[type - 1][2][1], CHAMPION_TYPE_GAIN[type - 1][2][2]);
	}

	// HP/DEF/SP (and the champion stats) from their starting values over every level again: the type changed
	// (Zaczaruj zwierzaka) or the pet was made (an old pet). The starting values never change (tr/de); they are kept in
	// dwAgeApply (HP), adwStart below... the row has room for them in the champion "Apply" fields of a non-champion -
	// no: they live in the pet's own start fields (see StartStats).
	struct StartStats
	{
		DWORD hp, def, sp, res, blockPen, precision;
	};

	// The starting values are stored packed in dwAgeApply (HP 11 bits, DEF 11 bits, SP 10 bits: 0..2047 / 0..1023
	// thousandths, the wiki's 0.1-2.0 %) and in the high bits of the champion level (unused bits) - simpler: the start
	// values are derived from the hatch roll kept in dwAgeApply and dwSize (champion starts, 3 x 9 bits in bSize? no).
	// The champion starts are kept in the upper 16 bits of the three champion apply fields (their gains fit 16 bits).
	StartStats GetStart(const Pet& p)
	{
		StartStats s;
		s.hp = p.d.dwAgeApply & 0x7FF;
		s.def = (p.d.dwAgeApply >> 11) & 0x7FF;
		s.sp = (p.d.dwAgeApply >> 22) & 0x3FF;
		s.res = p.d.dwChampionResApply >> 16;
		s.blockPen = p.d.dwChampionBlockPenApply >> 16;
		s.precision = p.d.dwChampionPrecisionApply >> 16;
		return s;
	}

	void SetStart(Pet& p, const StartStats& s)
	{
		p.d.dwAgeApply = (MIN(s.hp, 2047u)) | (MIN(s.def, 2047u) << 11) | (MIN(s.sp, 1023u) << 22);
		p.d.dwChampionResApply = (p.d.dwChampionResApply & 0xFFFF) | (MIN(s.res, 65535u) << 16);
		p.d.dwChampionBlockPenApply = (p.d.dwChampionBlockPenApply & 0xFFFF) | (MIN(s.blockPen, 65535u) << 16);
		p.d.dwChampionPrecisionApply = (p.d.dwChampionPrecisionApply & 0xFFFF) | (MIN(s.precision, 65535u) << 16);
	}

	void RollStart(Pet& p, bool champion)
	{
		StartStats s = GetStart(p);
		if (!champion)
		{
			s.hp = Roll(START_STAT_MIN, START_STAT_MAX);
			s.def = Roll(START_STAT_MIN, START_STAT_MAX);
			s.sp = Roll(START_STAT_MIN, MIN((int)START_STAT_MAX, 1023));
		}
		else
		{
			s.res = Roll(CHAMPION_START_MIN, CHAMPION_START_MAX);
			s.blockPen = Roll(CHAMPION_START_MIN, CHAMPION_START_MAX);
			s.precision = Roll(CHAMPION_START_MIN, CHAMPION_START_MAX);
		}
		SetStart(p, s);
	}

	// RollApplies keeps the start bits of the champion applies.
	void RollAppliesKeepStart(Pet& p)
	{
		const StartStats s = GetStart(p);
		RollApplies(p);
		p.d.dwChampionResApply &= 0xFFFF;
		p.d.dwChampionBlockPenApply &= 0xFFFF;
		p.d.dwChampionPrecisionApply &= 0xFFFF;
		SetStart(p, s);
	}

	void RecalcStats(Pet& p)
	{
		const StartStats s = GetStart(p);
		p.d.dwHP = s.hp;
		p.d.dwDef = s.def;
		p.d.dwSP = s.sp;
		const int level = MINMAX(1, (int)p.d.dwLevel, (int)GROWTH_PET_MAX_LEVEL);
		for (int l = 2; l <= level; ++l)
			AddLevelGains(p, l);
		if (IsChampion(p))
		{
			p.d.dwChampionRes = s.res;
			p.d.dwChampionBlockPen = s.blockPen;
			p.d.dwChampionPrecision = s.precision;
			for (int cl = 2; cl <= (int)p.d.dwChampionLevel; ++cl)
				AddChampionGains(p, cl);
		}
		else
			p.d.dwChampionRes = p.d.dwChampionBlockPen = p.d.dwChampionPrecision = 0;
	}

	void RollSkillSlots(Pet& p, const Species* sp)
	{
		int n = sp ? (int)Roll(sp->slotMin, sp->slotMax) : 1;
		n = MINMAX(1, n, (int)GROWTH_PET_SKILL_SLOTS);
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			p.d.aSkill[i].bLocked = i < n ? 0 : 1;
	}

	bool HasLearnedSkill(const Pet& p)
	{
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			if (p.d.aSkill[i].bSkill)
				return true;
		return false;
	}

	// A pet without a type (an old-system pet, state 3 or packed): rolled as at a hatching, its stats for its level.
	void Finalise(Pet& p)
	{
		if (p.d.bType)
			return;
		const Species* sp = FindSpeciesBySeal(p.d.dwVnum);
		p.d.bType = (BYTE)Roll(1, 6);
		p.d.bTypeKnown = 0;
		p.d.dwLevel = MINMAX(1, (int)p.d.dwLevel, (int)GROWTH_PET_MAX_LEVEL);
		p.d.bEvolution = (BYTE)MINMAX(1, (int)p.d.bEvolution, (int)STAGE_HEROIC);
		if (Stage(p) >= STAGE_VALIANT && p.d.dwLevel < 81)
			p.d.bEvolution = STAGE_WILD;
		RollApplies(p);
		RollStart(p, false);
		RecalcStats(p);
		RollSkillSlots(p, sp);
		const int days = sp ? (int)Roll(sp->hatchMin, sp->hatchMax) : 7;
		p.d.llMaxTime = (long long)days * DAY;
		p.d.llEndTime = (long long)Now() + p.d.llMaxTime;
		if (p.d.llBirthday <= 0 || p.d.llBirthday > (long long)Now())
			p.d.llBirthday = Now();
		p.d.ullExp = p.d.ullItemExp = 0;
	}

	// ---- the mob ---------------------------------------------------------------------------------------------------

	LPCHARACTER PetMob(Pet& p)
	{
		if (!p.mobVid)
			return NULL;
		LPCHARACTER mob = CHARACTER_MANAGER::instance().Find(p.mobVid);
		if (!mob)
		{
			s_mobToPet.erase(p.mobVid);
			p.mobVid = 0;
		}
		return mob;
	}

	DWORD MobVnum(const Pet& p)
	{
		const Species* sp = FindSpeciesBySeal(p.d.dwVnum);
		if (!sp)
			return 0;
		const int stage = Stage(p);
		return stage >= STAGE_AWAKENED ? sp->mob[2] : (stage == STAGE_HEROIC ? sp->mob[1] : sp->mob[0]);
	}

	WORD ScalePct(const Pet& p)
	{
		// tr/de: about +20 % a step up to Dzielny; Bohaterski and the champion stages are their own models
		switch (Stage(p))
		{
			case STAGE_YOUNG: return 100;
			case STAGE_WILD: return 120;
			case STAGE_VALIANT: return 140;
			default: return 100;
		}
	}

	void DestroyMob(Pet& p)
	{
		LPCHARACTER mob = PetMob(p);
		if (mob)
		{
			s_mobToPet.erase(p.mobVid);
			p.mobVid = 0;
			M2_DESTROY_CHARACTER(mob);
		}
		p.mobVid = 0;
		p.featherUntil = 0;
	}

	void EnsureTick();

	bool SpawnMob(LPCHARACTER ch, Pet& p)
	{
		DestroyMob(p);
		const DWORD vnum = MobVnum(p);
		if (!vnum || !CMobManager::instance().Get(vnum))
		{
			sys_err("GROWTH_PET: no mob_proto row %u for pet %u (seal %u)", vnum, p.d.dwID, p.d.dwVnum);
			Say(ch, "Tego zwierzaka nie mo\xbfna teraz przywo\xb3" "a\xe6.");
			return false;
		}
		const long x = ch->GetX() + number(-100, 100);
		const long y = ch->GetY() + number(-100, 100);
		LPCHARACTER mob = CHARACTER_MANAGER::instance().SpawnMob(vnum, ch->GetMapIndex(), x, y, ch->GetZ(), false,
				(int)(ch->GetRotation() + 180), false);
		if (!mob)
		{
			sys_err("GROWTH_PET: SpawnMob %u failed for %s", vnum, ch->GetName());
			return false;
		}
		mob->SetPet();
		mob->SetEmpire(ch->GetEmpire());
		mob->SetName(p.d.szName);
		mob->SetLevel((BYTE)MINMAX(1, (int)p.d.dwLevel, 250));
		p.mobVid = mob->GetVID();
		s_mobToPet[p.mobVid] = p.d.dwID;
		mob->Show(ch->GetMapIndex(), x, y, ch->GetZ());
		EnsureTick();
		return true;
	}

	// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1 (summon kept): the summoned pet's id in a quest flag, so a warp, a map change
	// or a relog (OnDestroy keeps it) brings the pet out again with its bonuses (OnLoaded); a sent-away, dead, traded
	// or stored pet clears it (Unsummon).
	const char* const SUMMON_FLAG = "growth_pet.summoned";

	void RememberSummon(LPCHARACTER ch, DWORD id)
	{
		if (!ch || !ch->IsPC())
			return;
		// MT2009_PLUS_PET_SUMMON_KEEP_V2: GetPCForce - GetPC also moves the quest manager's current pc / character
		quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
		if (pc && (DWORD)pc->GetFlag(SUMMON_FLAG) != id)
			pc->SetFlag(SUMMON_FLAG, (int)id);
	}

	DWORD RememberedSummon(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return 0;
		quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
		return pc ? (DWORD)pc->GetFlag(SUMMON_FLAG) : 0;
	}

	// MT2009_PLUS_PET_SUMMON_KEEP_V2: the quest flags come from the db's asynchronous quest query (QID_QUEST), the
	// pets from its direct query answering the game's load sent at the item load - after a warp, a channel change or
	// a relog the pets were mostly answered first, the flag was still 0 then and the pet stayed in its seal. So the
	// restore waits for the quest flags (quest::PC::IsLoaded) - at once when they are in, else every 250 ms up to 15 s.
	bool QuestFlagsLoaded(LPCHARACTER ch)
	{
		quest::PC* pc = ch ? quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID()) : NULL;
		return pc && pc->IsLoaded();
	}

	Pet* SummonedPet(LPCHARACTER ch);
	bool Summon(LPCHARACTER ch, Pet& p, LPITEM seal, bool quiet = false);

	// true: done (restored, nothing to restore or the flag cleared); false: not yet (the quest flags not loaded)
	bool RestoreSummon(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return true;
		if (!QuestFlagsLoaded(ch))
			return false;
		if (SummonedPet(ch))
			return true;
		const DWORD id = RememberedSummon(ch);
		Pet* p = id ? FindPet(id) : NULL;
		LPITEM seal = p ? FindSealOf(ch, id) : NULL;
		if (p && seal && p->holder == ch->GetPlayerID() && p->d.bState == GROWTH_PET_STATE_UPBRINGING)
		{
			if (!IsAlive(*p) || (int)p->d.dwLevel > ch->GetLevel())
				RememberSummon(ch, 0);
			else if (!Summon(ch, *p, seal, true))
				sys_log(0, "GROWTH_PET: %s pet %u not brought out again after the login", ch->GetName(), id);
		}
		return true;
	}

	EVENTINFO(growth_pet_restore_info)
	{
		DWORD pid;
		int tries;
		growth_pet_restore_info() : pid(0), tries(0) {}
	};

	EVENTFUNC(growth_pet_restore)
	{
		growth_pet_restore_info* info = dynamic_cast<growth_pet_restore_info*>(event->info);
		if (!info)
			return 0;
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(info->pid);
		if (!ch)
			return 0;
		if (RestoreSummon(ch) || ++info->tries >= 60)
			return 0;
		return PASSES_PER_SEC(1) / 4;
	}

	void RestoreSummonLater(LPCHARACTER ch)
	{
		if (RestoreSummon(ch))
			return;
		growth_pet_restore_info* info = AllocEventInfo<growth_pet_restore_info>();
		info->pid = ch->GetPlayerID();
		event_create(growth_pet_restore, info, PASSES_PER_SEC(1) / 4);
	}

	void Unsummon(LPCHARACTER ch, Pet& p, bool bMessage)
	{
		Owner& o = GetOwner(ch);
		DestroyMob(p);
		if (o.summoned == p.d.dwID)
		{
			o.summoned = 0;
			o.invincibleUntil = 0;
			RememberSummon(ch, 0);
			SendSub(ch, SUBHEADER_PET_UNSUMMON);
			if (bMessage)
				Sayf(ch, "Tw\xf3j zwierzak %s wraca do piecz\xea" "ci.", p.d.szName);
			ch->ComputePoints();
		}
		if (p.dirty)
			SaveNow(p);
	}

	Pet* SummonedPet(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		std::map<DWORD, Owner>::iterator it = s_owners.find(ch->GetPlayerID());
		if (it == s_owners.end() || !it->second.summoned)
			return NULL;
		Pet* p = FindPet(it->second.summoned);
		if (!p || p->holder != ch->GetPlayerID())
		{
			it->second.summoned = 0;
			return NULL;
		}
		return p;
	}

	bool Summon(LPCHARACTER ch, Pet& p, LPITEM seal, bool quiet)
	{
		if (!IsAlive(p))
		{
			Sayf(ch, "Zwierzak %s nie \xbfyje. O\xbfyw go Od\xbfywk\xb9 albo Bosk\xb9 Od\xbfywk\xb9.", p.d.szName);
			return false;
		}
		if ((int)p.d.dwLevel > ch->GetLevel())
		{
			Say(ch, "Poziom zwierzaka nie mo\xbf" "e by\xe6 wy\xbfszy ni\xbf poziom jego w\xb3" "a\x9c" "ciciela.");
			return false;
		}
		if (ch->GetExchange() || ch->IsOpenSafebox() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsCubeOpen())
		{
			Say(ch, "Zamknij inne okna, aby przywo\xb3" "a\xe6 zwierzaka.");
			return false;
		}
		Pet* cur = SummonedPet(ch);
		if (cur && cur != &p)
			Unsummon(ch, *cur, false);
		if (!SpawnMob(ch, p))
			return false;
		Owner& o = GetOwner(ch);
		o.summoned = p.d.dwID;
		// the seal shows the life it has
		if (seal)
		{
			seal->SetSocket(0, (long)p.d.llEndTime);
			seal->SetSocket(1, (long)p.d.llMaxTime);
		}
		SendSummon(ch, p.d.dwID);
		SendSet(ch, p);
		if (!quiet)
			Sayf(ch, "Przywo\xb3" "ano zwierzaka %s.", p.d.szName);
		RememberSummon(ch, p.d.dwID);
		ch->ComputePoints();
		return true;
	}

	// ---- experience ------------------------------------------------------------------------------------------------

	void SendLevelUp(LPCHARACTER ch, Pet& p)
	{
		LPCHARACTER mob = PetMob(p);
		if (mob)
		{
			mob->SetLevel((BYTE)MINMAX(1, (int)p.d.dwLevel, 250));
			TPacketGCPointChange pack;
			pack.header = HEADER_GC_CHARACTER_POINT_CHANGE;
			pack.dwVID = mob->GetVID();
			pack.type = POINT_LEVEL;
			pack.value = p.d.dwLevel;
			pack.amount = 0;
			mob->PacketAround(&pack, sizeof(pack));
		}
	}

	// Both bars full and the level allowed: one level up (more while both stay full).
	bool TryLevelUp(LPCHARACTER ch, Pet& p)
	{
		bool any = false;
		for (int guard = 0; guard < 4; ++guard)
		{
			if (IsChampion(p))
			{
				const int cl = (int)p.d.dwChampionLevel;
				if (cl < 1 || cl >= StageCap(p) || cl >= (int)ch->GetConquerorLevel())
					break;
				const unsigned long long nm = NeedChampionExpOf(cl), ni = NeedChampionItemExpOf(cl);
				if (p.d.ullChampionExp < nm || p.d.ullChampionItemExp < ni)
					break;
				p.d.ullChampionExp = 0;
				p.d.ullChampionItemExp -= ni;
				p.d.ullChampionItemExp = Min64<U64>(p.d.ullChampionItemExp, NeedChampionItemExpOf(cl + 1));
				p.d.dwChampionLevel = cl + 1;
				AddChampionGains(p, cl + 1);
				Sayf(ch, "Tw\xf3j zwierzak %s osi\xb9gn\xb9\xb3 poziom czempiona %d.", p.d.szName, cl + 1);
			}
			else
			{
				const int level = (int)p.d.dwLevel;
				if (level >= StageCap(p) || level >= ch->GetLevel())
					break;
				const unsigned long long nm = NeedMobExpOf(level), ni = NeedItemExpOf(level);
				if (p.d.ullExp < nm || p.d.ullItemExp < ni)
					break;
				p.d.ullExp = 0;
				p.d.ullItemExp -= ni;
				p.d.ullItemExp = Min64<U64>(p.d.ullItemExp, NeedItemExpOf(level + 1));	// the excess item exp is kept (en)
				p.d.dwLevel = level + 1;
				AddLevelGains(p, level + 1);
				Sayf(ch, "Tw\xf3j zwierzak %s osi\xb9gn\xb9\xb3 poziom %d.", p.d.szName, level + 1);
			}
			any = true;
		}
		if (any)
		{
			SendLevelUp(ch, p);
			SendSet(ch, p);
			SaveNow(p);
			ch->ComputePoints();
		}
		return any;
	}

	// Why the pet's bars cannot grow any more (a message once a level).
	void ExpBlockedMessage(LPCHARACTER ch, Pet& p)
	{
		if (IsChampion(p))
		{
			if ((int)p.d.dwChampionLevel >= (int)ch->GetConquerorLevel())
				Say(ch, "Poziom czempiona zwierzaka nie mo\xbf" "e by\xe6 wy\xbfszy ni\xbf tw\xf3j.");
			else if ((int)p.d.dwChampionLevel >= StageCap(p))
				Say(ch, "Zwierzak potrzebuje rozwoju, aby rosn\xb9\xe6 dalej.");
			return;
		}
		if ((int)p.d.dwLevel >= ch->GetLevel())
			Say(ch, "Poziom zwierzaka nie mo\xbf" "e by\xe6 wy\xbfszy ni\xbf poziom jego w\xb3" "a\x9c" "ciciela.");
		else if ((int)p.d.dwLevel >= StageCap(p))
			Say(ch, "Zwierzak potrzebuje rozwoju, aby rosn\xb9\xe6 dalej.");
	}

	// Mob experience (the red bars; champion experience for a champion pet).
	void AddMobExp(LPCHARACTER ch, Pet& p, unsigned long long exp, bool champion)
	{
		if (!exp || !IsAlive(p))
			return;
		if (champion != IsChampion(p))
			return;
		unsigned long long& cur = champion ? p.d.ullChampionExp : p.d.ullExp;
		const unsigned long long need = champion ? NeedChampionExpOf(p.d.dwChampionLevel) : NeedMobExpOf(p.d.dwLevel);
		if (!need || cur >= need)
		{
			TryLevelUp(ch, p);
			return;
		}
		cur = Min64<U64>(need, cur + exp);
		MarkDirty(p);
		SendPoint(ch, p, champion ? POINT_UPBRINGING_CHAMPION_EXP : POINT_UPBRINGING_PET_EXP);
		if (cur >= need && !TryLevelUp(ch, p))
		{
			const unsigned long long ni = champion ? NeedChampionItemExpOf(p.d.dwChampionLevel) : NeedItemExpOf(p.d.dwLevel);
			const unsigned long long ci = champion ? p.d.ullChampionItemExp : p.d.ullItemExp;
			if (ci < ni)
				Say(ch, "Zwierzak potrzebuje do\x9cwiadczenia z przedmiot\xf3w (okno \x84Przedmiot EXP\x94).");
			else
				ExpBlockedMessage(ch, p);
		}
	}

	// Item experience (the blue bar): what is over the level's need is kept for the next level (en).
	unsigned long long AddItemExp(LPCHARACTER ch, Pet& p, unsigned long long exp)
	{
		if (!exp)
			return 0;
		const bool champion = IsChampion(p);
		unsigned long long& cur = champion ? p.d.ullChampionItemExp : p.d.ullItemExp;
		const int lv = champion ? (int)p.d.dwChampionLevel : (int)p.d.dwLevel;
		const unsigned long long need = champion ? NeedChampionItemExpOf(lv) : NeedItemExpOf(lv);
		const unsigned long long next = champion ? NeedChampionItemExpOf(lv + 1) : NeedItemExpOf(lv + 1);
		const unsigned long long cap = need + next;
		if (cur >= cap)
			return 0;
		const unsigned long long add = Min64<U64>(exp, cap - cur);
		cur += add;
		MarkDirty(p);
		SendPoint(ch, p, champion ? POINT_UPBRINGING_CHAMPION_ITEM_EXP : POINT_UPBRINGING_PET_ITEM_EXP);
		TryLevelUp(ch, p);
		return add;
	}

	// ---- evolution -------------------------------------------------------------------------------------------------

	const Evolution* EvolutionTo(int stage)
	{
		for (size_t i = 0; i < sizeof(EVOLUTION) / sizeof(EVOLUTION[0]); ++i)
			if (EVOLUTION[i].stage == stage)
				return &EVOLUTION[i];
		return NULL;
	}

	// 0 = ready (materials not checked); otherwise why not (a message for ch when ch is given).
	int EvolveBlock(LPCHARACTER ch, Pet& p, bool bSay)
	{
		const int stage = Stage(p);
		if (stage >= STAGE_MIGHTY)
		{
			if (bSay)
				Say(ch, "Zwierzak osi\xb9gn\xb9\xb3 ju\xbf najwy\xbfszy stopie\xf1.");
			return 1;
		}
		const Evolution* e = EvolutionTo(stage + 1);
		if (!e)
			return 1;
		if (stage + 1 == STAGE_MIGHTY)
		{
			if ((int)p.d.dwChampionLevel < e->level || p.d.ullChampionExp < NeedChampionExpOf(p.d.dwChampionLevel) ||
					p.d.ullChampionItemExp < NeedChampionItemExpOf(p.d.dwChampionLevel))
			{
				if (bSay)
					Sayf(ch, "Zwierzak potrzebuje poziomu czempiona %d i pe\xb3nego do\x9cwiadczenia.", e->level);
				return 2;
			}
		}
		else if (stage + 1 == STAGE_HEROIC)
		{
			if ((int)p.d.dwLevel < e->level)
			{
				if (bSay)
					Sayf(ch, "Zwierzak potrzebuje poziomu %d.", e->level);
				return 2;
			}
		}
		else
		{
			if ((int)p.d.dwLevel < e->level || p.d.ullExp < NeedMobExpOf(p.d.dwLevel) || p.d.ullItemExp < NeedItemExpOf(p.d.dwLevel))
			{
				if (bSay)
					Sayf(ch, "Zwierzak potrzebuje poziomu %d i pe\xb3nego do\x9cwiadczenia.", e->level);
				return 2;
			}
		}
		// (no age check: the owner's Yohara list 3.0.14, item 8 - the wiki's 30 days are old information; EVOLUTION's
		// ageDays is 0 everywhere and no longer read)
		if (stage + 1 <= STAGE_VALIANT && (int)p.d.dwLevel >= ch->GetLevel())
		{
			if (bSay)
				Say(ch, "Poziom zwierzaka nie mo\xbf" "e by\xe6 wy\xbfszy ni\xbf poziom jego w\xb3" "a\x9c" "ciciela.");
			return 4;
		}
		if (stage + 1 == STAGE_MIGHTY && (int)p.d.dwChampionLevel >= (int)ch->GetConquerorLevel())
		{
			if (bSay)
				Say(ch, "Poziom czempiona zwierzaka nie mo\xbf" "e by\xe6 wy\xbfszy ni\xbf tw\xf3j.");
			return 4;
		}
		return 0;
	}

	bool DoEvolve(LPCHARACTER ch, Pet& p)
	{
		if (EvolveBlock(ch, p, true))
			return false;
		const int to = Stage(p) + 1;
		const Evolution* e = EvolutionTo(to);
		for (int i = 0; i < 9 && e->items[i][0]; ++i)
			if ((int)ch->CountSpecifyItem(e->items[i][0]) < (int)e->items[i][1])
			{
				const TItemTable* t = ITEM_MANAGER::instance().GetTable(e->items[i][0]);
				Sayf(ch, "Brakuje: %s x%u.", t ? t->szLocaleName : "?", e->items[i][1]);
				return false;
			}
		for (int i = 0; i < 9 && e->items[i][0]; ++i)
			ch->RemoveSpecifyItem(e->items[i][0], e->items[i][1]);
		p.d.bEvolution = (BYTE)to;
		switch (to)
		{
			case STAGE_WILD:
			case STAGE_VALIANT:
				p.d.ullExp = 0;
				p.d.ullItemExp = 0;
				p.d.dwLevel += 1;
				AddLevelGains(p, p.d.dwLevel);
				break;
			case STAGE_AWAKENED:
				p.d.dwChampionLevel = 1;
				p.d.ullChampionExp = 0;
				p.d.ullChampionItemExp = 0;
				RollStart(p, true);
				{
					const StartStats s = GetStart(p);
					p.d.dwChampionRes = s.res;
					p.d.dwChampionBlockPen = s.blockPen;
					p.d.dwChampionPrecision = s.precision;
				}
				break;
			case STAGE_MIGHTY:
				p.d.dwChampionLevel += 1;
				p.d.ullChampionExp = 0;
				p.d.ullChampionItemExp = 0;
				AddChampionGains(p, p.d.dwChampionLevel);
				break;
		}
		Sayf(ch, "Zwierzak %s osi\xb9gn\xb9\xb3 stopie\xf1 \x84%s\x94.", p.d.szName, STAGE_NAMES[to]);
		SaveNow(p);
		if (PetMob(p))
			SpawnMob(ch, p);	// the new model and scale
		SendSet(ch, p);
		SendSub(ch, SUBHEADER_PET_EVOLVE_SUCCESS);
		ch->ComputePoints();
		return true;
	}

	// ---- life ------------------------------------------------------------------------------------------------------

	void SyncSeal(LPCHARACTER ch, Pet& p)
	{
		LPITEM seal = ch ? FindSealOf(ch, p.d.dwID) : NULL;
		if (seal)
		{
			seal->SetSocket(0, (long)p.d.llEndTime);
			seal->SetSocket(1, (long)p.d.llMaxTime);
		}
	}

	void Revive(LPCHARACTER ch, Pet& p, bool premium)
	{
		const long long now = Now();
		if (premium)
		{
			const long long age = Max64<S64>(0, now - p.d.llBirthday);
			p.d.llEndTime = now + p.d.llMaxTime;
			p.d.llBirthday = now - age * 8 / 10;	// 80 % of the age kept
		}
		else
		{
			p.d.llEndTime = now + p.d.llMaxTime / 2;	// 50 % of the life
			p.d.llBirthday = now - DAY;				// the age from 1 day (pl)
			Say(ch, "Zwierzak \xbfyje, ale jego wiek liczy si\xea od nowa.");
		}
		SaveNow(p);
		SyncSeal(ch, p);
		SendSet(ch, p);
	}

	// ---- skills ----------------------------------------------------------------------------------------------------

	struct PointName
	{
		const char* name;
		WORD point;
	};

	const PointName POINT_NAMES[] = {
		{ "RESIST_WARRIOR", POINT_RESIST_WARRIOR }, { "RESIST_SURA", POINT_RESIST_SURA },
		{ "RESIST_ASSASSIN", POINT_RESIST_ASSASSIN }, { "RESIST_SHAMAN", POINT_RESIST_SHAMAN },
#ifdef ENABLE_WOLFMAN_CHARACTER
		{ "RESIST_WOLFMAN", POINT_RESIST_WOLFMAN },
#endif
		{ "MELEE_MAGIC_ATT_BONUS_PER", POINT_MELEE_MAGIC_ATT_BONUS_PER }, { "ANTI_RESIST_MAGIC", POINT_ANTI_RESIST_MAGIC },
		{ "CASTING_SPEED", POINT_CASTING_SPEED }, { "PENETRATE_PCT", POINT_PENETRATE_PCT },
		{ "STEAL_HP", POINT_STEAL_HP }, { "STEAL_SP", POINT_STEAL_SP }, { "BLOCK", POINT_BLOCK },
		{ "REFLECT_MELEE", POINT_REFLECT_MELEE }, { "GOLD_DOUBLE_BONUS", POINT_GOLD_DOUBLE_BONUS },
		{ "BOW_DISTANCE", POINT_BOW_DISTANCE }, { "POTION_BONUS", POINT_POTION_BONUS },
		{ "ATTBONUS_MONSTER", POINT_ATTBONUS_MONSTER }, { "MALL_EXPBONUS", POINT_MALL_EXPBONUS },
		{ "KILL_HP_RECOVERY", POINT_KILL_HP_RECOVERY },
	};

	WORD PointOn(const TGrowthPetSkillTable* t)
	{
		if (!t || !t->szPointOn[0])
			return POINT_NONE;
		for (size_t i = 0; i < sizeof(POINT_NAMES) / sizeof(POINT_NAMES[0]); ++i)
			if (!strcasecmp(POINT_NAMES[i].name, t->szPointOn))
				return POINT_NAMES[i].point;
		return POINT_NONE;
	}

	// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1: the whole units added (0: nothing - not passive, no point, below one unit).
	int ApplyPassive(LPCHARACTER ch, const Pet& p, BYTE skill, int value)
	{
		const TGrowthPetSkillTable* t = BaseSkillProto(skill);
		if (!t || t->bType != GROWTH_PET_SKILL_USE_PASSIVE)
			return 0;
		const WORD point = PointOn(t);
		const int v = value / 10;	// tenths of a per cent / of a metre -> whole units
		if (point == POINT_NONE || v <= 0)
			return 0;
		ch->PointChange(point, v);
		return v;
	}

	void SetCooltime(LPCHARACTER ch, Pet& p, int slot, DWORD until)
	{
		p.d.aSkill[slot].dwCooltime = until;
		if (!HasClient(ch))
			return;
		TPacketGCPetSkillCooltime pack;
		pack.header = HEADER_GC_PET_SKILL_COOLTIME;
		pack.dwID = p.d.dwID;
		pack.bSlot = (BYTE)slot;
		pack.dwCooltime = until;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void FeatherHit(LPCHARACTER ch, Pet& p);

	// One auto skill's trigger check (slot < 3: a learned skill; 3/4: a potential slot).
	void AutoSkill(LPCHARACTER ch, Pet& p, int slot, BYTE skill, int k, int value, bool potential)
	{
		const time_t now = Now();
		DWORD& cool = potential ? p.potentialCooltime[slot - GROWTH_PET_SKILL_SLOTS] : p.d.aSkill[slot].dwCooltime;
		if ((time_t)cool > now)
			return;
		bool trigger = false;
		switch (skill)
		{
			case SKILL_HEAL:
				trigger = ch->GetHP() > 0 && ch->GetHP() < ch->GetMaxHP() / 5;
				break;
			case SKILL_INVINCIBLE:
				trigger = ch->GetHP() > 0 && ch->GetHP() < ch->GetMaxHP() / 10;
				break;
			case SKILL_REMOVAL:
				trigger = ch->IsAffectFlag(AFF_POISON) || ch->IsAffectFlag(AFF_SLOW)
#ifdef ENABLE_WOLFMAN_CHARACTER
						|| ch->IsAffectFlag(AFF_BLEEDING)
#endif
						;
				break;
			case SKILL_FEATHER:
				trigger = ch->GetVictim() != NULL && ch->GetVictim()->IsMonster();
				break;
		}
		if (!trigger)
			return;
		const TGrowthPetSkillTable* t = BaseSkillProto(skill);
		const DWORD until = (DWORD)now + (t ? t->dwCooldown : 300);
		if (potential)
			cool = until;
		else
			SetCooltime(ch, p, slot, until);
		const int pct = potential ? (skill == SKILL_REMOVAL ? value / 10 : (t ? t->abActivate[MINMAX(1, k, 20) - 1] : 0))
				: SkillActivatePct(p, skill, k, value);
		if (number(1, 100) > pct)
			return;
		const TGrowthPetSkillTable* nameRow = SkillProto(p.d.dwVnum, skill);
		const char* skillName = nameRow ? nameRow->szName : "";
		switch (skill)
		{
			case SKILL_HEAL:
				ch->PointChange(POINT_HP, value);
				ch->EffectPacket(SE_HPUP_RED);
				Sayf(ch, "%s: +%d P\xaf.", skillName, value);
				break;
			case SKILL_INVINCIBLE:
				GetOwner(ch).invincibleUntil = (time_t)(get_dword_time() + (DWORD)value * 100);	// dword ms
				Sayf(ch, "%s: nie\x9cmiertelno\x9c\xe6 na %d.%d s.", skillName, value / 10, value % 10);
				break;
			case SKILL_REMOVAL:
				ch->RemoveAffect(AFFECT_POISON);
				ch->RemoveAffect(AFFECT_SLOW);
#ifdef ENABLE_WOLFMAN_CHARACTER
				ch->RemoveAffect(AFFECT_BLEEDING);
#endif
				Sayf(ch, "%s: z\xb3" "e efekty usuni\xeate.", skillName);
				break;
			case SKILL_FEATHER:
				p.featherUntil = now + MAX(1, SkillDuration(p, skill, k, value) / 10);
				p.featherMin = MAX(1, value);
				Sayf(ch, "%s: zwierzak %s rusza do ataku!", skillName, p.d.szName);
				FeatherHit(ch, p);
				break;
		}
	}

	struct FFeatherBoom
	{
		LPCHARACTER owner;
		long x, y;
		int damageMin;
		void operator()(LPENTITY ent)
		{
			if (!ent->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER v = (LPCHARACTER)ent;
			if (v == owner || v->IsPC() || v->IsPet() || v->IsDead() || !(v->IsMonster() || v->IsStone()))
				return;
			if (DISTANCE_APPROX(x - v->GetX(), y - v->GetY()) > 300)
				return;
			if (!battle_is_attackable(owner, v))
				return;
			v->Damage(owner, number(MIN(damageMin, (int)FEATHER_MAX_DAMAGE), (int)FEATHER_MAX_DAMAGE), DAMAGE_TYPE_SPECIAL);
		}
	};

	void FeatherHit(LPCHARACTER ch, Pet& p)
	{
		LPCHARACTER mob = PetMob(p);
		LPCHARACTER target = ch->GetVictim();
		if (!mob || !target || !target->GetSectree() || target->GetMapIndex() != ch->GetMapIndex())
			return;
		char effect[128] = "d:/ymir work/effect/hit/gyeonggong_boom.mse";
		mob->SpecificEffectPacket(effect);
		FFeatherBoom f;
		f.owner = ch;
		f.x = target->GetX();
		f.y = target->GetY();
		f.damageMin = p.featherMin;
		target->GetSectree()->ForEachAround(f);
	}

	// ---- the tick: following, auto skills, life, potentials, saves -------------------------------------------------

	void Follow(LPCHARACTER ch, Pet& p)
	{
		LPCHARACTER mob = PetMob(p);
		if (!mob)
			return;
		LPCHARACTER target = ch;
		if (p.featherUntil > Now() && ch->GetVictim() && ch->GetVictim()->GetMapIndex() == ch->GetMapIndex())
			target = ch->GetVictim();
		if (mob->GetMapIndex() != ch->GetMapIndex())
		{
			SpawnMob(ch, p);
			return;
		}
		const float dist = DISTANCE_APPROX(mob->GetX() - target->GetX(), mob->GetY() - target->GetY());
		if (dist >= 4500.0f)
		{
			const float rot = target->GetRotation() * 3.141592f / 180.f;
			mob->Show(target->GetMapIndex(), target->GetX() - (long)(200 * cos(rot)), target->GetY() - (long)(200 * sin(rot)));
			return;
		}
		const float approach = target == ch ? 200.0f : 50.0f;
		if (dist < 300.0f && target == ch)
		{
			mob->SendMovePacket(FUNC_WAIT, 0, 0, 0, 0);
			return;
		}
		mob->SetNowWalking(dist < 900.0f && target == ch);
		const float fd = DISTANCE_SQRT(target->GetX() - mob->GetX(), target->GetY() - mob->GetY());
		if (fd <= approach)
			return;
		mob->SetRotationToXY(target->GetX(), target->GetY());
		float fx, fy;
		GetDeltaByDegree(mob->GetRotation(), fd - approach, &fx, &fy);
		if (mob->Goto((long)(mob->GetX() + fx + 0.5f), (long)(mob->GetY() + fy + 0.5f)))
			mob->SendMovePacket(FUNC_WAIT, 0, 0, 0, 0);
	}

	void TickOwner(LPCHARACTER ch, Owner& o)
	{
		Pet* p = FindPet(o.summoned);
		if (!p || p->holder != ch->GetPlayerID())
		{
			o.summoned = 0;
			return;
		}
		// the seal must stay in the owner's bags
		if (!FindSealOf(ch, p->d.dwID))
		{
			Unsummon(ch, *p, true);
			return;
		}
		if (!IsAlive(*p))
		{
			Sayf(ch, "Zwierzak %s umar\xb3. O\xbfyw go Od\xbfywk\xb9 albo Bosk\xb9 Od\xbfywk\xb9.", p->d.szName);
			Unsummon(ch, *p, false);
			SendSet(ch, *p);
			return;
		}
		if (!ch->GetSectree() || ch->IsObserverMode())
			return;
		if (!PetMob(*p))
			SpawnMob(ch, *p);
		Follow(ch, *p);
		if (ch->IsDead())
			return;
		// auto skills (from Bohaterski); potential skills of a champion pet
		if (Stage(*p) >= SKILL_OPEN_STAGE)
			for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			{
				const BYTE s = p->d.aSkill[i].bSkill;
				if (s && IsAutoSkill(s))
					AutoSkill(ch, *p, i, s, p->d.aSkill[i].bLevel, SkillValue(*p, s, p->d.aSkill[i].bLevel, false), false);
			}
		for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
		{
			if (p->d.aPotential[i].dwEggVnum && (time_t)p->d.aPotential[i].dwEndTime <= Now())
			{
				Sayf(ch, "Umiej\xeatno\x9c\xe6 potencja\xb3u zwierzaka %s wygas\xb3" "a razem z jajem.", p->d.szName);
				memset(&p->d.aPotential[i], 0, sizeof(p->d.aPotential[i]));
				SaveNow(*p);
				SendPotential(ch, *p);
				ch->ComputePoints();
				continue;
			}
			if (PotentialActive(*p, i) && IsAutoSkill(p->d.aPotential[i].bSkill))
			{
				const int k = PotentialLevel(*p, i);
				AutoSkill(ch, *p, GROWTH_PET_SKILL_SLOTS + i, p->d.aPotential[i].bSkill, k,
						SkillValue(*p, p->d.aPotential[i].bSkill, k, true), true);
			}
		}
		if (p->featherUntil > Now())
			FeatherHit(ch, *p);
		if (p->dirty && Now() - p->lastSave >= SAVE_DELAY)
			SaveNow(*p);
	}

	EVENTINFO(growth_pet_tick_info)
	{
		int unused;
		growth_pet_tick_info() : unused(0) {}
	};

	EVENTFUNC(growth_pet_tick)
	{
		std::vector<DWORD> pids;
		for (std::map<DWORD, Owner>::iterator it = s_owners.begin(); it != s_owners.end(); ++it)
			if (it->second.summoned)
				pids.push_back(it->first);
		for (size_t i = 0; i < pids.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pids[i]);
			std::map<DWORD, Owner>::iterator it = s_owners.find(pids[i]);
			if (it == s_owners.end())
				continue;
			if (!ch)
			{
				Pet* p = FindPet(it->second.summoned);
				if (p)
					DestroyMob(*p);
				it->second.summoned = 0;
				continue;
			}
			TickOwner(ch, it->second);
		}
		return PASSES_PER_SEC(1) / 2;
	}

	void EnsureTick()
	{
		if (s_tick)
			return;
		growth_pet_tick_info* info = AllocEventInfo<growth_pet_tick_info>();
		s_tick = event_create(growth_pet_tick, info, PASSES_PER_SEC(1) / 2);
	}

	// ---- items of ch -------------------------------------------------------------------------------------------------

	void CollectIds(LPCHARACTER ch, std::vector<DWORD>& ids)
	{
		const int cells = ch->GetInventoryMaxCount();
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if ((IsSeal(item) || IsBag(item)) && item->GetSocket(2))
				ids.push_back((DWORD)item->GetSocket(2));
		}
		for (BYTE w = UPGRADE_INVENTORY; w <= CHEST_INVENTORY; ++w)
			for (WORD c = 0; c < SPECIAL_INVENTORY_MAX_NUM; ++c)
			{
				LPITEM item = ch->Mt2009SpecialGetItem(w, c);
				if ((IsSeal(item) || IsBag(item)) && item->GetSocket(2))
					ids.push_back((DWORD)item->GetSocket(2));
			}
	}

	bool ValidName(const char* name)
	{
		const size_t len = strnlen(name, GROWTH_PET_NAME_MAX + 1);
		if (len < GROWTH_PET_NAME_MIN || len > GROWTH_PET_NAME_MAX)
			return false;
		if (!check_name || !check_name(name))
			return false;
		return !CBanwordManager::instance().CheckString(name, len);
	}

	// ---- the cage ----------------------------------------------------------------------------------------------------

	bool Pack(LPCHARACTER ch, LPITEM cage, LPITEM seal)
	{
		if (!IsBag(cage) || !IsSeal(seal) || cage->GetSocket(2))
			return false;
		Pet* p = FindPet((DWORD)seal->GetSocket(2));
		if (!p || p->holder != ch->GetPlayerID())
		{
			Say(ch, "Dane zwierzaka jeszcze si\xea wczytuj\xb9 - spr\xf3" "buj za chwil\xea.");
			return false;
		}
		if (!IsAlive(*p))
		{
			Say(ch, "Martwego zwierzaka nie mo\xbfna w\xb3o\xbfy\xe6 do klatki.");
			return false;
		}
		if (SummonedPet(ch) == p)
			Unsummon(ch, *p, false);
		if (cage->GetCount() > 1)
		{
			// one cage of a stack: a fresh one for the pet
			LPITEM one = ITEM_MANAGER::instance().CreateItem(BAG_VNUM, 1);
			if (!one)
				return false;
			const int cell = ch->GetEmptyInventory(one->GetSize());
			if (cell < 0)
			{
				M2_DESTROY_ITEM(one);
				Say(ch, "Brak miejsca w ekwipunku.");
				return false;
			}
			cage->SetCount(cage->GetCount() - 1);
			one->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			cage = one;
		}
		const long long now = Now();
		cage->SetSocket(0, (long)(now + BAG_SECONDS));
		cage->SetSocket(1, (long)now);
		cage->SetSocket(2, (long)p->d.dwID);
		p->d.bState = GROWTH_PET_STATE_BAG;
		SaveNow(*p);
		ITEM_MANAGER::instance().RemoveItem(seal, "GROWTH_PET_PACK");
		SendSet(ch, *p);
		Sayf(ch, "Zwierzak %s jest w klatce (30 dni).", p->d.szName);
		return true;
	}

	bool Unpack(LPCHARACTER ch, LPITEM cage)
	{
		const DWORD id = (DWORD)cage->GetSocket(2);
		Pet* p = FindPet(id);
		if (!p)
		{
			std::vector<DWORD> ids(1, id);
			AskLoad(ch, GROWTH_PET_LOAD_UNPACK, cage->GetID(), ids);
			return true;
		}
		if ((long long)cage->GetSocket(0) < (long long)Now())
		{
			Say(ch, "Klatka straci\xb3" "a wa\xbfno\x9c\xe6. Przeci\xb9gnij na ni\xb9 now\xb9 Klatk\xea Transportow\xb9.");
			return false;
		}
		const int cell = ch->GetEmptyInventory(1);
		if (cell < 0)
		{
			Say(ch, "Brak miejsca w ekwipunku.");
			return false;
		}
		LPITEM seal = ITEM_MANAGER::instance().CreateItem(p->d.dwVnum, 1);
		if (!seal)
			return false;
		Finalise(*p);
		const long long now = Now();
		const long long packed = Max64<S64>(0, now - (long long)cage->GetSocket(1));
		p->d.llBirthday += packed;				// no ageing in the cage
		p->d.llEndTime = now + p->d.llMaxTime;	// the life refilled (tr/de)
		p->d.bState = GROWTH_PET_STATE_UPBRINGING;
		p->holder = ch->GetPlayerID();
		seal->SetSocket(0, (long)p->d.llEndTime);
		seal->SetSocket(1, (long)p->d.llMaxTime);
		seal->SetSocket(2, (long)p->d.dwID);
		ITEM_MANAGER::instance().RemoveItem(cage, "GROWTH_PET_UNPACK");
		seal->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
		SaveNow(*p);
		SendSet(ch, *p);
		Sayf(ch, "Zwierzak %s wyszed\xb3 z klatki.", p->d.szName);
		return true;
	}

	bool Rebag(LPCHARACTER ch, LPITEM emptyCage, LPITEM fullCage)
	{
		if (!IsBag(emptyCage) || !IsBag(fullCage) || emptyCage->GetSocket(2) || !fullCage->GetSocket(2))
			return false;
		fullCage->SetSocket(0, (long)(Now() + BAG_SECONDS));
		if (emptyCage->GetCount() > 1)
			emptyCage->SetCount(emptyCage->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(emptyCage, "GROWTH_PET_REBAG");
		Say(ch, "Klatka znowu jest wa\xbfna przez 30 dni.");
		return true;
	}

	// ---- feeding -----------------------------------------------------------------------------------------------------

	// An egg or another pet's seal eaten by the summoned pet: 3-5 % of its life (en).
	bool FeedLifeItem(LPCHARACTER ch, Pet& p, LPITEM food)
	{
		if (!food || (!IsEgg(food) && !IsSeal(food)))
			return false;
		if (IsSeal(food) && (DWORD)food->GetSocket(2) == p.d.dwID)
			return false;
		const long long now = Now();
		const long long left = Max64<S64>(0, p.d.llEndTime - now);
		if (left >= p.d.llMaxTime)
			return false;
		const long long add = p.d.llMaxTime * number(3, 5) / 100;
		p.d.llEndTime = now + Min64<S64>(p.d.llMaxTime, left + add);
		if (IsSeal(food))
		{
			const DWORD eaten = (DWORD)food->GetSocket(2);
			Pet* other = FindPet(eaten);
			if (other)
			{
				if (SummonedPet(ch) == other)
					Unsummon(ch, *other, false);
				DestroyMob(*other);
				s_pets.erase(eaten);
			}
			if (eaten)
			{
				DeleteRow(eaten);
				SendDelete(ch, eaten);
			}
			ITEM_MANAGER::instance().RemoveItem(food, "GROWTH_PET_FEED_SEAL");
		}
		else if (food->GetCount() > 1)
			food->SetCount(food->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(food, "GROWTH_PET_FEED_EGG");
		return true;
	}

	unsigned long long ItemExpOf(LPCHARACTER ch, Pet& p, LPITEM item, int count)
	{
		if (!item || count <= 0)
			return 0;
		switch (item->GetType())
		{
			case ITEM_WEAPON:
			case ITEM_ARMOR:
				if (item->IsEquipped())
					return 0;
				return (unsigned long long)Max64<S64>(0, (S64)item->GetShopBuyPrice()) * count / 2;
			case ITEM_PET:
				if (item->GetSubType() == PET_EXPFOOD && item->GetValue(2) == 0)
					return (unsigned long long)Max64<S64>(0, item->GetValue(0)) * count;	// Smakolyk: 80 000 item exp
				if (item->GetSubType() == PET_EXPFOOD_PER)
				{
					const bool champion = IsChampion(p);
					const unsigned long long need = champion ? NeedChampionItemExpOf(p.d.dwChampionLevel) : NeedItemExpOf(p.d.dwLevel);
					return need * (U64)Max64<S64>(1, item->GetValue(0)) / 100 * count;	// Smakolyk+: 5 % of the need
				}
				return 0;
		}
		return 0;
	}

	// ---- hatching ----------------------------------------------------------------------------------------------------

	bool DoHatch(LPCHARACTER ch, LPITEM egg, const char* rawName, bool bAnswer)
	{
		const Species* sp = egg ? FindSpeciesByEgg(egg->GetVnum()) : NULL;
		if (!sp || !IsEgg(egg))
		{
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER);
			return false;
		}
		if ((long long)egg->GetSocket(0) > 0 && (long long)egg->GetSocket(0) < (long long)Now())
		{
			Say(ch, "To jajo jest ju\xbf zbyt stare, aby si\xea wyklu\xe6.");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER);
			return false;
		}
		char name[GROWTH_PET_NAME_MAX + 1];
		strlcpy(name, rawName && *rawName ? rawName : "", sizeof(name));
		if (!name[0])
			strlcpy(name, sp->name, sizeof(name));	// the default name (en)
		if (!ValidName(name))
		{
			Say(ch, "Prosz\xea wybra\xe6 inn\xb9 nazw\xea (4-20 liter, bez spacji i znak\xf3w specjalnych).");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_BECAUSE_NAME);
			return false;
		}
		const long long price = egg->GetValue(3) > 0 ? egg->GetValue(3) : HATCH_PRICE;
		if ((long long)ch->GetGold() < price)
		{
			Say(ch, "Nie masz wystarczaj\xb9" "co du\xbfo Yang.");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER);
			return false;
		}
		if (!ITEM_MANAGER::instance().GetTable(sp->seal))
		{
			sys_err("GROWTH_PET: no item_proto for the seal %u (egg %u)", sp->seal, egg->GetVnum());
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER);
			return false;
		}
		const int cell = ch->GetEmptyInventory(1);
		if (cell < 0)
		{
			Say(ch, "Brak miejsca w ekwipunku.");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER);
			return false;
		}
		LPITEM seal = ITEM_MANAGER::instance().CreateItem(sp->seal, 1);
		if (!seal)
			return false;
		ch->ChangeGold(-(YANG)price);	// MT2009_PLUS_GOLD_CHANGE_FIX_V1
		if (egg->GetCount() > 1)
			egg->SetCount(egg->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(egg, "GROWTH_PET_HATCH");

		Pet& p = s_pets[seal->GetID()];
		p = Pet();
		p.d.dwID = seal->GetID();
		p.d.dwVnum = sp->seal;
		p.d.bState = GROWTH_PET_STATE_UPBRINGING;
		strlcpy(p.d.szName, name, sizeof(p.d.szName));
		p.d.dwLevel = 1;
		p.d.bEvolution = STAGE_YOUNG;
		p.d.bType = (BYTE)Roll(1, 6);	// 1-6 at the hatching; 7/8 only through Zaczaruj zwierzaka
		RollApplies(p);
		RollStart(p, false);
		RecalcStats(p);
		RollSkillSlots(p, sp);
		const int days = (int)Roll(sp->hatchMin, sp->hatchMax);
		p.d.llMaxTime = (long long)days * DAY;
		p.d.llBirthday = Now();
		p.d.llEndTime = p.d.llBirthday + p.d.llMaxTime;
		p.holder = ch->GetPlayerID();
		seal->SetSocket(0, (long)p.d.llEndTime);
		seal->SetSocket(1, (long)p.d.llMaxTime);
		seal->SetSocket(2, (long)p.d.dwID);
		seal->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
		SaveNow(p);
		SendSet(ch, p);
		if (bAnswer)
			SendSub(ch, SUBHEADER_PET_EGG_USE_SUCCESS);
		Sayf(ch, "Wykluto zwierzaka: %s (%s).", p.d.szName, sp->name);
		return true;
	}

	// ---- the window's packets ----------------------------------------------------------------------------------------

	void PacketFeed(LPCHARACTER ch, const TPacketCGPetFeed* pk)
	{
		Pet* p = SummonedPet(ch);
		if (!p)
		{
			Say(ch, "Najpierw przywo\xb3" "aj zwierzaka.");
			SendSub(ch, SUBHEADER_PET_FEED_FAILED);
			return;
		}
		bool ok = false;
		switch (pk->index)
		{
			case FEED_LIFE_TIME_EVENT:
			{
				std::set<DWORD> used;
				for (int i = 0; i < GROWTH_PET_FEED_SLOTS; ++i)
				{
					LPITEM item = FindHeldItemByPos(ch, pk->pos[i]);
					if (!item || !used.insert(item->GetID()).second)
						continue;
					if (FeedLifeItem(ch, *p, item))
						ok = true;
				}
				if (ok)
				{
					SaveNow(*p);
					SyncSeal(ch, *p);
					SendSet(ch, *p);
				}
				else
					Say(ch, "Zwierzak nie chce teraz je\x9c\xe6 (czas trwania jest pe\xb3ny albo przedmiot si\xea nie nadaje).");
				break;
			}
			case FEED_EXP_EVENT:
			{
				std::set<DWORD> used;
				unsigned long long total = 0;
				for (int i = 0; i < GROWTH_PET_FEED_SLOTS; ++i)
				{
					if (!pk->count[i])
						continue;
					LPITEM item = FindHeldItemByPos(ch, pk->pos[i]);
					if (!item || !used.insert(item->GetID()).second)
						continue;
					const int count = MIN((int)pk->count[i], (int)item->GetCount());
					const unsigned long long exp = ItemExpOf(ch, *p, item, count);
					if (!exp)
						continue;
					const unsigned long long got = AddItemExp(ch, *p, exp);
					if (!got)
					{
						Say(ch, "Do\x9cwiadczenie z przedmiot\xf3w jest ju\xbf pe\xb3ne.");
						break;
					}
					total += got;
					ok = true;
					if ((int)item->GetCount() > count)
						item->SetCount(item->GetCount() - count);
					else
						ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_FEED_EXP");
				}
				if (ok)
				{
					Sayf(ch, "Zwierzak otrzyma\xb3 %llu PD przedmiotu.", total);
					SaveNow(*p);
				}
				break;
			}
			case FEED_EVOL_EVENT:
				ok = DoEvolve(ch, *p);
				break;
		}
		SendSub(ch, ok ? SUBHEADER_PET_FEED_SUCCESS : SUBHEADER_PET_FEED_FAILED);
	}

	void PacketRevive(LPCHARACTER ch, const TPacketCGPetRevive* pk)
	{
		// the dead pet's seal goes into the revive tab of another, living, summoned pet (pl)
		Pet* active = SummonedPet(ch);
		LPITEM seal = FindHeldItemByPos(ch, pk->upBringingPos);
		Pet* dead = IsSeal(seal) ? FindPet((DWORD)seal->GetSocket(2)) : NULL;
		if (!active || !dead || dead == active || dead->holder != ch->GetPlayerID() || IsAlive(*dead))
		{
			if (!active)
				Say(ch, "U\xbfyj zak\xb3" "adki wskrzeszania w oknie innego, \xbfywego zwierzaka.");
			SendSub(ch, SUBHEADER_PET_REVIVE_FAILED);
			return;
		}
		const int need = MAX(1, AgeDays(*dead) / 10);	// pl: age 1-19 -> 1, 20-29 -> 2, ...
		// the real counts of distinct Boska Odzywka stacks the window names
		std::vector<std::pair<LPITEM, int> > take;
		std::set<DWORD> used;
		int have = 0;
		for (int i = 0; i < GROWTH_PET_REVIVE_SLOTS && have < need; ++i)
		{
			if (!pk->count[i])
				continue;
			LPITEM item = FindHeldItemByPos(ch, pk->pos[i]);
			if (!item || item->GetVnum() != PREMIUM_FEED_VNUM || !used.insert(item->GetID()).second)
				continue;
			const int n = MIN(MIN((int)pk->count[i], (int)item->GetCount()), need - have);
			if (n <= 0)
				continue;
			take.push_back(std::make_pair(item, n));
			have += n;
		}
		if (have < need)
		{
			Sayf(ch, "Potrzebujesz %d szt. Boskiej Od\xbfywki.", need);
			SendSub(ch, SUBHEADER_PET_REVIVE_FAILED);
			return;
		}
		for (size_t i = 0; i < take.size(); ++i)
		{
			LPITEM item = take[i].first;
			if ((int)item->GetCount() > take[i].second)
				item->SetCount(item->GetCount() - take[i].second);
			else
				ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_REVIVE");
		}
		Revive(ch, *dead, true);
		SendSub(ch, SUBHEADER_PET_REVIVE_SUCCESS);
		Sayf(ch, "Zwierzak %s znowu \xbfyje.", dead->d.szName);
	}

	void PacketAttrChange(LPCHARACTER ch, const TPacketCGPetAttrChange* pk)
	{
		LPITEM seal = FindHeldItemByPos(ch, pk->upBringingPos);
		LPITEM item = FindHeldItemByPos(ch, pk->attrChangePos);
		Pet* p = IsSeal(seal) ? FindPet((DWORD)seal->GetSocket(2)) : NULL;
		if (!p || p->holder != ch->GetPlayerID() || !item || item->GetType() != ITEM_PET || item->GetSubType() != PET_ATTR_CHANGE)
			return;
		const Species* sp = FindSpeciesBySeal(p->d.dwVnum);
		p->d.bType = (BYTE)Roll(1, sp ? sp->maxType : 8);
		RollAppliesKeepStart(*p);
		RecalcStats(*p);	// the starting values stay (tr/de); every level again with the age bonus
		const int days = sp ? (int)Roll(sp->enchantMin, sp->enchantMax) : 14;
		p->d.llMaxTime = (long long)days * DAY;
		p->d.llEndTime = (long long)Now() + p->d.llMaxTime;
		const bool slots = !HasLearnedSkill(*p);
		if (slots)
			RollSkillSlots(*p, sp);
		if (item->GetCount() > 1)
			item->SetCount(item->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_ATTR_CHANGE");
		SaveNow(*p);
		SyncSeal(ch, *p);
		SendSet(ch, *p);
		if (HasClient(ch))
		{
			TPacketGCPetAttrChangeResult pack;
			pack.header = HEADER_GC_PET_ATTR_CHANGE_RESULT;
			pack.type = p->d.bType;
			pack.pos = seal->GetItemPos();
			ch->GetDesc()->Packet(&pack, sizeof(pack));
		}
		Say(ch, "Zwierzak zosta\xb3 zaczarowany.");
		if (SummonedPet(ch) == p)
			ch->ComputePoints();
	}

	void PacketDetermine(LPCHARACTER ch, const TPacketCGPetDetermine* pk)
	{
		LPITEM item = FindHeldItemByPos(ch, pk->determinePos);
		Pet* p = SummonedPet(ch);
		if (!item || item->GetType() != ITEM_PET || item->GetSubType() != PET_ATTR_DETERMINE)
			return;
		if (!p)
		{
			Say(ch, "Najpierw przywo\xb3" "aj zwierzaka.");
			return;
		}
		p->d.bTypeKnown = 1;
		if (item->GetCount() > 1)
			item->SetCount(item->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_DETERMINE");
		SaveNow(*p);
		SendPoint(ch, *p, POINT_UPBRINGING_TYPE);
		if (HasClient(ch))
		{
			TPacketGCPetDetermineResult pack;
			pack.header = HEADER_GC_PET_DETERMINE_RESULT;
			pack.type = p->d.bType;
			ch->GetDesc()->Packet(&pack, sizeof(pack));
		}
	}

	void PacketNameChange(LPCHARACTER ch, const TPacketCGPetNameChange* pk)
	{
		TPacketGCPetNameChangeResult res;
		memset(&res, 0, sizeof(res));
		res.header = HEADER_GC_PET_NAME_CHANGE_RESULT;
		res.subheader = SUBHEADER_PET_NAME_CHANGE_FAILED;
		LPITEM scroll = FindHeldItemByPos(ch, pk->changeNamePos);
		LPITEM seal = FindHeldItemByPos(ch, pk->upBringingPos);
		Pet* p = IsSeal(seal) ? FindPet((DWORD)seal->GetSocket(2)) : NULL;
		char name[GROWTH_PET_NAME_MAX + 1];
		strlcpy(name, pk->name, sizeof(name));
		if (!p || p->holder != ch->GetPlayerID() || !scroll || scroll->GetType() != ITEM_PET || scroll->GetSubType() != PET_NAME_CHANGE)
		{
			if (HasClient(ch))
				ch->GetDesc()->Packet(&res, sizeof(res));
			return;
		}
		res.dwID = p->d.dwID;
		if (!ValidName(name))
		{
			Say(ch, "Prosz\xea wybra\xe6 inn\xb9 nazw\xea (4-20 liter, bez spacji i znak\xf3w specjalnych).");
			ch->GetDesc()->Packet(&res, sizeof(res));
			return;
		}
		if ((long long)ch->GetGold() < RENAME_PRICE)
		{
			Say(ch, "Nie masz wystarczaj\xb9" "co du\xbfo Yang.");
			ch->GetDesc()->Packet(&res, sizeof(res));
			return;
		}
		ch->ChangeGold(-(YANG)RENAME_PRICE);	// MT2009_PLUS_GOLD_CHANGE_FIX_V1
		if (scroll->GetCount() > 1)
			scroll->SetCount(scroll->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(scroll, "GROWTH_PET_RENAME");
		strlcpy(p->d.szName, name, sizeof(p->d.szName));
		SaveNow(*p);
		if (PetMob(*p))
			SpawnMob(ch, *p);
		res.subheader = SUBHEADER_PET_NAME_CHANGE_SUCCESS;
		strlcpy(res.szName, p->d.szName, sizeof(res.szName));
		if (HasClient(ch))
			ch->GetDesc()->Packet(&res, sizeof(res));
		SendSet(ch, *p);
	}

	bool DoLearn(LPCHARACTER ch, Pet& p, int slot, LPITEM book)
	{
		if (Stage(p) < SKILL_OPEN_STAGE)
		{
			Say(ch, "Umiej\xeatno\x9c" "ci zwierzak poznaje od stopnia \x84" "Bohaterski\x94.");
			return false;
		}
		if (slot < 0 || slot >= GROWTH_PET_SKILL_SLOTS || p.d.aSkill[slot].bLocked || p.d.aSkill[slot].bSkill)
			return false;
		if (!book || book->GetType() != ITEM_PET || book->GetSubType() != PET_SKILL)
			return false;
		const int skill = (int)book->GetValue(0);
		if (skill < 1 || skill > SKILL_COUNT || !BaseSkillProto((BYTE)skill))
			return false;
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			if (p.d.aSkill[i].bSkill == skill)
			{
				Say(ch, "Zwierzak zna ju\xbf t\xea umiej\xeatno\x9c\xe6.");
				return false;
			}
		p.d.aSkill[slot].bSkill = (BYTE)skill;
		p.d.aSkill[slot].bLevel = 1;
		p.d.aSkill[slot].dwCooltime = 0;
		if (book->GetCount() > 1)
			book->SetCount(book->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(book, "GROWTH_PET_LEARN");
		SaveNow(p);
		SendSkills(ch, p);
		SendSet(ch, p);
		Say(ch, "Zwierzak pozna\xb3 now\xb9 umiej\xeatno\x9c\xe6.");
		ch->ComputePoints();
		return true;
	}

	bool DoUpgrade(LPCHARACTER ch, Pet& p, int slot)
	{
		if (Stage(p) < SKILL_OPEN_STAGE || slot < 0 || slot >= GROWTH_PET_SKILL_SLOTS || !p.d.aSkill[slot].bSkill)
			return false;
		if (p.d.aSkill[slot].bLevel >= GROWTH_PET_SKILL_LEVEL_MAX)
		{
			Say(ch, "Ta umiej\xeatno\x9c\xe6 ma ju\xbf najwy\xbfszy poziom.");
			return false;
		}
		if ((long long)ch->GetGold() < SKILL_UPGRADE_PRICE)
		{
			Say(ch, "Nie masz wystarczaj\xb9" "co du\xbfo Yang (2.000.000).");
			return false;
		}
		ch->ChangeGold(-(YANG)SKILL_UPGRADE_PRICE);	// MT2009_PLUS_GOLD_CHANGE_FIX_V1
		p.d.aSkill[slot].bLevel += 1;
		SaveNow(p);
		SendSkills(ch, p);
		SendSet(ch, p);
		Sayf(ch, "Umiej\xeatno\x9c\xe6 zwierzaka ma teraz poziom %d.", p.d.aSkill[slot].bLevel);
		ch->ComputePoints();
		return true;
	}

	// A potential slot of a champion pet filled with an egg held by ch (the window's add; the bots call it too -
	// MT2009_PLUS_BOT_PET_GROW_V1). bAnswer: the window's answer packets.
	bool DoPotential(LPCHARACTER ch, Pet& p, int slot, LPITEM egg, bool bAnswer)
	{
		if (!IsChampion(p) || slot < 0 || slot >= OpenPotentialSlots(p))
			return false;
		const Species* sp = egg && IsEgg(egg) && IsHeldBy(egg, ch) ? FindSpeciesByEgg(egg->GetVnum()) : NULL;
		if (!sp || PotentialActive(p, slot))
		{
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_POTENTIAL_FAILED);
			return false;
		}
		const long long end = (long long)egg->GetSocket(0);
		if (end <= (long long)Now())
		{
			Say(ch, "To jajo jest ju\xbf zbyt stare.");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_POTENTIAL_FAILED);
			return false;
		}
		// a random skill of the egg's species list; the same potential skill never twice
		std::vector<BYTE> pool;
		const BYTE other = p.d.aPotential[slot ^ 1].dwEggVnum ? p.d.aPotential[slot ^ 1].bSkill : 0;
		for (int i = 0; i < 8 && POTENTIAL[sp->idx][i]; ++i)
			if (POTENTIAL[sp->idx][i] != other)
				pool.push_back(POTENTIAL[sp->idx][i]);
		if (pool.empty())
		{
			Say(ch, "To jajo nie da nowej umiej\xeatno\x9c" "ci potencja\xb3u.");
			if (bAnswer)
				SendSub(ch, SUBHEADER_PET_POTENTIAL_FAILED);
			return false;
		}
		TGrowthPetPotential& pot = p.d.aPotential[slot];
		pot.dwEggVnum = egg->GetVnum();
		pot.bSkill = pool[number(0, (int)pool.size() - 1)];
		pot.dwEndTime = (DWORD)end;
		p.potentialCooltime[slot] = 0;
		if (egg->GetCount() > 1)
			egg->SetCount(egg->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(egg, "GROWTH_PET_POTENTIAL");
		SaveNow(p);
		SendPotential(ch, p);
		if (bAnswer)
			SendSub(ch, SUBHEADER_PET_POTENTIAL_SUCCESS);
		const TGrowthPetSkillTable* t = BaseSkillProto(pot.bSkill);
		Sayf(ch, "Nowa umiej\xeatno\x9c\xe6 potencja\xb3u: %s.", t ? t->szName : "?");
		ch->ComputePoints();
		return true;
	}

	void PacketPotential(LPCHARACTER ch, const TPacketCGPetPotential* pk)
	{
		Pet* p = SummonedPet(ch);
		const int slot = pk->slot;
		if (!p || !IsChampion(*p) || slot < 0 || slot >= OpenPotentialSlots(*p))
		{
			Say(ch, "Miejsca potencja\xb3u ma tylko przywo\xb3" "any zwierzak czempiona.");
			SendSub(ch, SUBHEADER_PET_POTENTIAL_FAILED);
			return;
		}
		if (pk->action == PET_POTENTIAL_REMOVE)
		{
			memset(&p->d.aPotential[slot], 0, sizeof(p->d.aPotential[slot]));
			SaveNow(*p);
			SendPotential(ch, *p);
			SendSub(ch, SUBHEADER_PET_POTENTIAL_SUCCESS);
			ch->ComputePoints();
			return;
		}
		DoPotential(ch, *p, slot, FindHeldItemByPos(ch, pk->eggPos), true);
	}

	// ---- DG 185: pets from the db core -------------------------------------------------------------------------------

	void GivePending(LPCHARACTER ch, Pet& p)
	{
		// MT2009_PLUS_GROWTH_PET_ID_FIX_V1: the seal's socket 2 is a 32-bit long in this engine (-m32) and the item
		// table's socket2 is unsigned - an id over 0x7FFFFFFF went into the db core negative and came back 0 (605 seals
		// without their pet on the test world, 6 November 2026; pety.sql pety:id_fix_v1 moved the old system's pets
		// under it). Such a pet waits for that fix instead of getting a seal that loses it at the next save.
		if (p.d.dwID > 0x7FFFFFFFU)
		{
			sys_err("GROWTH_PET: pending pet %u of pid %u has an id a seal cannot hold (pety:id_fix_v1 not applied?)",
					p.d.dwID, ch->GetPlayerID());
			return;
		}
		const int cell = ch->GetEmptyInventory(1);
		if (cell < 0)
		{
			Say(ch, "Tw\xf3j zwierzak z dawnego systemu czeka na miejsce w ekwipunku - zwolnij je i zaloguj si\xea ponownie.");
			return;
		}
		LPITEM seal = ITEM_MANAGER::instance().CreateItem(p.d.dwVnum, 1);
		if (!seal)
			return;
		Finalise(p);
		p.d.bState = GROWTH_PET_STATE_UPBRINGING;
		p.holder = ch->GetPlayerID();
		seal->SetSocket(0, (long)p.d.llEndTime);
		seal->SetSocket(1, (long)p.d.llMaxTime);
		seal->SetSocket(2, (long)p.d.dwID);
		seal->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
		SaveNow(p);
		SendSet(ch, p);
		Sayf(ch, "Tw\xf3j zwierzak %s przeszed\xb3 do nowego systemu zwierz\xb9t domowych (poziom %u). Jego piecz\xea\xe6 jest w "
				"ekwipunku.", p.d.szName, p.d.dwLevel);
	}

	// MT2009_PLUS_PET_CHAMPION_GAIN_FIX_V1: a pet already inflated by the old gain (the start << 16 added on a level-up)
	// gets its champion values back at load - the excess is a multiple of the start field, the rest is the real value.
	void FixChampionStats(Pet& p)
	{
		if (!IsChampion(p))
			return;
		DWORD* vals[3] = { &p.d.dwChampionRes, &p.d.dwChampionBlockPen, &p.d.dwChampionPrecision };
		const DWORD applies[3] = { p.d.dwChampionResApply, p.d.dwChampionBlockPenApply, p.d.dwChampionPrecisionApply };
		bool fixed = false;
		for (int k = 0; k < 3; ++k)
		{
			const DWORD u = applies[k] & 0xFFFF0000u;	// the start << 16
			if (u && *vals[k] >= u)
			{
				*vals[k] %= u;
				fixed = true;
			}
		}
		if (fixed)
		{
			MarkDirty(p);
			sys_log(0, "GROWTH_PET champion fix: pet %u: res %u blockpen %u precision %u", p.d.dwID,
				p.d.dwChampionRes, p.d.dwChampionBlockPen, p.d.dwChampionPrecision);
		}
	}

	void OnLoaded(LPCHARACTER ch, const TPacketDGGrowthPetLoad* head, const TGrowthPet* pets)
	{
		for (WORD i = 0; i < head->wCount; ++i)
		{
			const TGrowthPet& row = pets[i];
			if (!row.dwID)
				continue;
			Pet* known = FindPet(row.dwID);
			Pet& p = known ? *known : s_pets[row.dwID];
			if (!known)
			{
				p = Pet();
				p.d = row;
				for (int k = 0; k < GROWTH_PET_SKILL_SLOTS; ++k)
					p.d.aSkill[k].dwCooltime = 0;
				FixChampionStats(p);
			}
			p.holder = ch->GetPlayerID();
			if (head->bReason == GROWTH_PET_LOAD_PENDING)
			{
				if (p.d.bState == GROWTH_PET_STATE_PENDING)
					GivePending(ch, p);
				continue;
			}
			if (p.d.bState == GROWTH_PET_STATE_UPBRINGING)
				SyncSeal(ch, p);
			SendSet(ch, p);
		}
		// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1 (summon kept): the pet out before the warp / logout comes out again
		// (MT2009_PLUS_PET_SUMMON_KEEP_V2: once the quest flags are loaded too - RestoreSummonLater)
		if (head->bReason == GROWTH_PET_LOAD_ITEMS && !SummonedPet(ch))
			RestoreSummonLater(ch);
		if (head->bReason == GROWTH_PET_LOAD_UNPACK)
		{
			LPITEM cage = ITEM_MANAGER::instance().Find(head->dwParam);
			if (cage && IsHeldBy(cage, ch) && IsBag(cage) && FindPet((DWORD)cage->GetSocket(2)))
				Unpack(ch, cage);
			else if (cage && IsBag(cage))
				Say(ch, "Nie znaleziono zwierzaka tej klatki.");
		}
	}

	void LoadSkillTable(const char* data)
	{
		const WORD size = *(const WORD*)data;
		const WORD count = *(const WORD*)(data + sizeof(WORD));
		if (size != sizeof(TGrowthPetSkillTable))
		{
			sys_err("GROWTH_PET: skill table size %u != %u (db and game built from different trees)", size,
					(unsigned)sizeof(TGrowthPetSkillTable));
			return;
		}
		const TGrowthPetSkillTable* t = (const TGrowthPetSkillTable*)(data + 2 * sizeof(WORD));
		s_skills.assign(t, t + count);
		// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1: a db core built before the fix sends the ENUM's 1-based index ("type+0":
		// NONE 1, PASSIVE 2, AUTO 3) - every passive skill then looked like an auto one and no auto skill was one, so
		// no pet skill ever did anything. A type past AUTO can only come from that: the whole table is shifted back.
		bool oneBased = false;
		for (size_t i = 0; i < s_skills.size(); ++i)
			if (s_skills[i].bType > GROWTH_PET_SKILL_USE_AUTO)
				oneBased = true;
		if (oneBased)
		{
			for (size_t i = 0; i < s_skills.size(); ++i)
				if (s_skills[i].bType > 0)
					--s_skills[i].bType;
			sys_err("GROWTH_PET: skill proto types came 1-based (old db core) - shifted to PASSIVE 1 / AUTO 2");
		}
		{
			int passive = 0, autos = 0;
			for (size_t i = 0; i < s_skills.size(); ++i)
			{
				if (s_skills[i].bType == GROWTH_PET_SKILL_USE_PASSIVE)
					++passive;
				else if (s_skills[i].bType == GROWTH_PET_SKILL_USE_AUTO)
					++autos;
			}
			sys_log(0, "GROWTH_PET: skill proto %d passive, %d auto rows", passive, autos);
		}
		s_skillIndex.clear();
		for (size_t i = 0; i < s_skills.size(); ++i)
			s_skillIndex[((unsigned long long)s_skills[i].dwPetVnum << 8) | s_skills[i].bSkill] = i;
		sys_log(0, "GROWTH_PET: %u skill proto rows", (unsigned)count);
	}
}

// ==== the public functions ==========================================================================================

namespace growth_pet
{
	bool IsSealVnum(DWORD vnum) { return FindSpeciesBySeal(vnum) != NULL; }
	bool IsEggVnum(DWORD vnum) { return FindSpeciesByEgg(vnum) != NULL; }

	DWORD SealOfEgg(DWORD egg)
	{
		const Species* sp = FindSpeciesByEgg(egg);
		return sp ? sp->seal : 0;
	}

	const char* SpeciesName(DWORD vnum)
	{
		const Species* sp = FindSpeciesBySeal(vnum);
		if (!sp)
			sp = FindSpeciesByEgg(vnum);
		return sp ? sp->name : "";
	}

	unsigned long long NeedMobExp(int level) { return NeedMobExpOf(level); }
	unsigned long long NeedItemExp(int level) { return NeedItemExpOf(level); }

	void FillView(const Pet& p, PetView& v)
	{
		v.id = p.d.dwID;
		v.vnum = p.d.dwVnum;
		v.state = p.d.bState;
		v.name = p.d.szName;
		v.level = (int)p.d.dwLevel;
		v.evolution = Stage(p);
		v.championLevel = (int)p.d.dwChampionLevel;
		v.type = p.d.bType;
		v.alive = IsAlive(p);
		v.lifeLeft = Max64<S64>(0, p.d.llEndTime - (long long)Now());
		v.lifeMax = p.d.llMaxTime;
		v.ageDays = AgeDays(p);
		if (IsChampion(p))
		{
			v.exp = p.d.ullChampionExp;
			v.needExp = NeedChampionExpOf(p.d.dwChampionLevel);
			v.itemExp = p.d.ullChampionItemExp;
			v.needItemExp = NeedChampionItemExpOf(p.d.dwChampionLevel);
		}
		else
		{
			v.exp = p.d.ullExp;
			v.needExp = NeedMobExpOf(p.d.dwLevel);
			v.itemExp = p.d.ullItemExp;
			v.needItemExp = NeedItemExpOf(p.d.dwLevel);
		}
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
		{
			v.skill[i] = p.d.aSkill[i].bSkill;
			v.skillLevel[i] = p.d.aSkill[i].bLevel;
			v.skillLocked[i] = p.d.aSkill[i].bLocked != 0;
		}
		v.summoned = p.mobVid != 0;
		// MT2009_PLUS_BOT_PET_GROW_V1: the champion's potential slots
		v.potentialOpen = OpenPotentialSlots(p);
		for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
			v.potentialActive[i] = PotentialActive(p, i);
	}

	bool GetPet(DWORD id, PetView& out)
	{
		Pet* p = FindPet(id);
		if (!p)
			return false;
		FillView(*p, out);
		return true;
	}

	DWORD GetSummonedPetId(CHARACTER* ch)
	{
		Pet* p = SummonedPet(ch);
		return p ? p->d.dwID : 0;
	}

	void ListPets(CHARACTER* ch, std::vector<PetView>& out)
	{
		out.clear();
		if (!ch)
			return;
		std::vector<DWORD> ids;
		CollectIds(ch, ids);
		for (size_t i = 0; i < ids.size(); ++i)
		{
			Pet* p = FindPet(ids[i]);
			if (!p || p->d.bState != GROWTH_PET_STATE_UPBRINGING)
				continue;
			PetView v;
			FillView(*p, v);
			out.push_back(v);
		}
	}

	bool CanEvolve(DWORD id, CHARACTER* ch, int& toStage)
	{
		Pet* p = FindPet(id);
		if (!p || !ch)
			return false;
		toStage = Stage(*p) + 1;
		return EvolveBlock(ch, *p, false) == 0;
	}

	bool GetEvolutionMaterials(int toStage, std::vector<std::pair<DWORD, int> >& out)
	{
		out.clear();
		const Evolution* e = EvolutionTo(toStage);
		if (!e)
			return false;
		for (int i = 0; i < 9 && e->items[i][0]; ++i)
			out.push_back(std::make_pair(e->items[i][0], (int)e->items[i][1]));
		return true;
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: the level (the champion level for stage 6) the evolution to toStage asks (0: none).
	int EvolutionLevel(int toStage)
	{
		const Evolution* e = EvolutionTo(toStage);
		return e ? (int)e->level : 0;
	}

	bool Hatch(CHARACTER* ch, CItem* egg, const char* name)
	{
		return ch && DoHatch(ch, egg, name, false);
	}

	bool ToggleSummon(CHARACTER* ch, CItem* seal)
	{
		if (!ch || !IsSeal(seal) || !IsHeldBy(seal, ch))
			return false;
		Pet* p = FindPet((DWORD)seal->GetSocket(2));
		if (!p || p->holder != ch->GetPlayerID())
		{
			std::vector<DWORD> ids(1, (DWORD)seal->GetSocket(2));
			AskLoad(ch, GROWTH_PET_LOAD_ITEMS, 0, ids);
			Say(ch, "Dane zwierzaka si\xea wczytuj\xb9 - spr\xf3" "buj za chwil\xea.");
			return false;
		}
		if (SummonedPet(ch) == p)
		{
			Unsummon(ch, *p, true);
			return true;
		}
		return Summon(ch, *p, seal);
	}

	// MT2009_PLUS_BOT_PET_FEED_V1: the feed window's life feed (FEED_LIFE_TIME_EVENT) for one egg on the pet of a seal
	// held by ch - +3-5% of its life, never past its maximum; the seal-eats-a-seal case is the window's alone.
	bool FeedLifeWithEgg(CHARACTER* ch, CItem* egg, CItem* seal)
	{
		if (!ch || !egg || !IsEgg(egg) || !IsSeal(seal) || !IsHeldBy(seal, ch) || !IsHeldBy(egg, ch))
			return false;
		Pet* p = FindPet((DWORD)seal->GetSocket(2));
		if (!p || p->holder != ch->GetPlayerID() || !IsAlive(*p))
			return false;
		if (!FeedLifeItem(ch, *p, egg))
			return false;
		SaveNow(*p);
		SyncSeal(ch, *p);
		SendSet(ch, *p);
		return true;
	}

	bool FeedLife(CHARACTER* ch, CItem* odzywka, CItem* seal)
	{
		if (!ch || !odzywka || !IsSeal(seal) || !IsHeldBy(seal, ch))
			return false;
		Pet* p = FindPet((DWORD)seal->GetSocket(2));
		if (!p || p->holder != ch->GetPlayerID())
			return false;
		if (!IsAlive(*p))
			Revive(ch, *p, false);
		else
		{
			if (p->d.llEndTime - (long long)Now() >= p->d.llMaxTime - 60)
			{
				Say(ch, "Zwierzak jest najedzony.");
				return false;
			}
			p->d.llEndTime = (long long)Now() + p->d.llMaxTime;	// 100 %
			SaveNow(*p);
			SyncSeal(ch, *p);
			SendSet(ch, *p);
			Sayf(ch, "Zwierzak %s zjad\xb3 Od\xbfywk\xea.", p->d.szName);
		}
		if (odzywka->GetCount() > 1)
			odzywka->SetCount(odzywka->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(odzywka, "GROWTH_PET_FEEDSTUFF");
		return true;
	}

	bool FeedItemExp(CHARACTER* ch, CItem* item, int count)
	{
		Pet* p = SummonedPet(ch);
		if (!p || !item || !IsHeldBy(item, ch))
			return false;
		count = MIN(count, (int)item->GetCount());
		const unsigned long long exp = ItemExpOf(ch, *p, item, count);
		if (!exp || !AddItemExp(ch, *p, exp))
			return false;
		if ((int)item->GetCount() > count)
			item->SetCount(item->GetCount() - count);
		else
			ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_FEED_EXP");
		return true;
	}

	bool UseTastyTreat(CHARACTER* ch, CItem* item)
	{
		Pet* p = SummonedPet(ch);
		if (!p)
		{
			Say(ch, "Najpierw przywo\xb3" "aj zwierzaka.");
			return false;
		}
		const bool champion = IsChampion(*p);
		const unsigned long long exp = (unsigned long long)Max64<S64>(0, champion ? item->GetValue(1) : item->GetValue(0));
		const unsigned long long before = champion ? p->d.ullChampionExp : p->d.ullExp;
		const int lvBefore = champion ? (int)p->d.dwChampionLevel : (int)p->d.dwLevel;
		AddMobExp(ch, *p, exp, champion);
		const unsigned long long after = champion ? p->d.ullChampionExp : p->d.ullExp;
		const int lvAfter = champion ? (int)p->d.dwChampionLevel : (int)p->d.dwLevel;
		if (after == before && lvAfter == lvBefore)
		{
			Say(ch, "Zwierzak nie mo\xbf" "e teraz otrzyma\xe6 do\x9cwiadczenia.");
			return false;
		}
		if (item->GetCount() > 1)
			item->SetCount(item->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_TASTY_TREAT");
		SaveNow(*p);
		return true;
	}

	bool Evolve(CHARACTER* ch)
	{
		Pet* p = SummonedPet(ch);
		return p && DoEvolve(ch, *p);
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: an egg into a potential slot of ch's summoned champion pet (the window's add).
	bool FillPotential(CHARACTER* ch, int slot, CItem* egg)
	{
		Pet* p = ch ? SummonedPet(ch) : NULL;
		return p && DoPotential(ch, *p, slot, egg, false);
	}

	bool LearnSkill(CHARACTER* ch, int slot, CItem* book)
	{
		Pet* p = SummonedPet(ch);
		return p && book && IsHeldBy(book, ch) && DoLearn(ch, *p, slot, book);
	}

	bool UpgradeSkill(CHARACTER* ch, int slot)
	{
		Pet* p = SummonedPet(ch);
		return p && DoUpgrade(ch, *p, slot);
	}

	// char_item.cpp UseItemEx (MT2009_PLUS_GROWTH_PET_V1 (use)): -1 = not a growth pet item.
	int UseItem(CHARACTER* ch, CItem* item, TItemPos dest)
	{
		if (!ch || !item || item->GetType() != ITEM_PET || !ch->IsPC())
			return -1;
		const BYTE sub = item->GetSubType();
		if (sub == PET_PAY)
			return -1;
		if (sub == PET_UPBRINGING && !IsSeal(item))
			return -1;	// an ItemShop pet's seal
		if (!IsHeldBy(item, ch))
			return 0;
		LPITEM target = dest.IsValidItemPosition() ? ch->GetItem(dest) : NULL;
		if (target == item || (target && !IsHeldBy(target, ch)))
			target = NULL;
		switch (sub)
		{
			case PET_EGG:
				Say(ch, "Jajo wykluwa okno inkubatora (prawy przycisk myszy na jaju).");
				return 0;
			case PET_UPBRINGING:
				if (target && IsBag(target))
					return Pack(ch, target, item) ? 1 : 0;
				return ToggleSummon(ch, item) ? 1 : 0;
			case PET_BAG:
				if (!IsBag(item))
					return 0;
				if (target && IsSeal(target))
					return Pack(ch, item, target) ? 1 : 0;
				if (target && IsBag(target))
					return Rebag(ch, item, target) ? 1 : 0;
				if (item->GetSocket(2))
					return Unpack(ch, item) ? 1 : 0;
				Say(ch, "Przeci\xb9gnij piecz\xea\xe6 zwierzaka na klatk\xea.");
				return 0;
			case PET_FEEDSTUFF:
				if (target && IsSeal(target))
					return FeedLife(ch, item, target) ? 1 : 0;
				Say(ch, "Przeci\xb9gnij Od\xbfywk\xea na piecz\xea\xe6 zwierzaka.");
				return 0;
			case PET_EXPFOOD:
				if (item->GetValue(2) == 1)
					return UseTastyTreat(ch, item) ? 1 : 0;
				Say(ch, "Ten przedmiot daje si\xea zwierzakowi w oknie \x84Przedmiot EXP\x94.");
				return 0;
			default:
				Say(ch, "Tego przedmiotu u\xbfywa si\xea w oknie zwierzaka (klawisz U).");
				return 0;
		}
	}

	void OnItemLoad(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC())
			return;
		std::vector<DWORD> ids;
		CollectIds(ch, ids);
		if (!ids.empty())
			AskLoad(ch, GROWTH_PET_LOAD_ITEMS, 0, ids);
		Owner& o = GetOwner(ch);
		if (!o.pendingAsked)
		{
			o.pendingAsked = true;
			std::vector<DWORD> none;
			AskLoad(ch, GROWTH_PET_LOAD_PENDING, 0, none);
		}
	}

	void OnSafeboxLoad(CHARACTER* ch)
	{
		if (!ch || !ch->GetSafebox())
			return;
		std::vector<DWORD> ids;
		for (int i = 0; i < SAFEBOX_MAX_NUM; ++i)
		{
			LPITEM item = ch->GetSafebox()->Get(i);
			if ((IsSeal(item) || IsBag(item)) && item->GetSocket(2) && !FindPet((DWORD)item->GetSocket(2)))
				ids.push_back((DWORD)item->GetSocket(2));
		}
		if (!ids.empty())
			AskLoad(ch, GROWTH_PET_LOAD_ITEMS, 0, ids);
	}

	// CItem::AddToCharacter: a seal or cage that came to ch after the login (a trade, the storeroom, a shop).
	void OnItemAdd(CHARACTER* ch, CItem* item)
	{
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || !(IsSeal(item) || IsBag(item)) || !item->GetSocket(2))
			return;
		const DWORD id = (DWORD)item->GetSocket(2);
		Pet* p = FindPet(id);
		if (!p)
		{
			std::vector<DWORD> ids(1, id);
			AskLoad(ch, GROWTH_PET_LOAD_ITEMS, 0, ids);
			return;
		}
		if (p->holder != ch->GetPlayerID())
		{
			LPCHARACTER old = HolderChar(*p);
			if (old)
			{
				Pet* s = SummonedPet(old);
				if (s == p)
					Unsummon(old, *p, false);
				SendDelete(old, id);
			}
			p->holder = ch->GetPlayerID();
			MarkDirty(*p);
		}
		SendSet(ch, *p);
	}

	void OnDestroy(CHARACTER* ch)
	{
		if (!ch)
			return;
		if (!ch->IsPC())
		{
			std::map<DWORD, DWORD>::iterator it = s_mobToPet.find(ch->GetVID());
			if (it != s_mobToPet.end())
			{
				Pet* p = FindPet(it->second);
				if (p && p->mobVid == ch->GetVID())
					p->mobVid = 0;
				s_mobToPet.erase(it);
			}
			return;
		}
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, Owner>::iterator o = s_owners.find(pid);
		for (std::map<DWORD, Pet>::iterator it = s_pets.begin(); it != s_pets.end(); )
		{
			Pet& p = it->second;
			if (p.holder != pid)
			{
				++it;
				continue;
			}
			DestroyMob(p);
			if (p.dirty)
				SaveNow(p);
			s_pets.erase(it++);
		}
		if (o != s_owners.end())
			s_owners.erase(o);
	}

	// char_battle.cpp GiveExp (MT2009_PLUS_GROWTH_PET_V1 (exp)): the owner's kill experience (with his experience
	// bonuses, en; before the player's own caps) - the summoned pet's too (nothing is taken from the owner).
	void OnKillExp(CHARACTER* victim, CHARACTER* to, long long exp)
	{
		if (!to || !to->IsPC() || exp <= 0)
			return;
		Pet* p = SummonedPet(to);
		if (!p || IsChampion(*p))
			return;
		LPCHARACTER mob = PetMob(*p);
		AddMobExp(to, *p, (unsigned long long)exp, false);
		if (victim && mob)
			victim->CreateFly(FLY_EXP, mob);
	}

	// playerbot_champion.cpp champion::GiveExp: the champion experience of a Sung Ma map's monster - a champion pet's
	// too (en: champion pets grow only in the Yohara regions).
	void OnChampionExp(CHARACTER* victim, CHARACTER* to, unsigned long long exp)
	{
		if (!to || !to->IsPC() || !exp)
			return;
		Pet* p = SummonedPet(to);
		if (!p || !IsChampion(*p))
			return;
		AddMobExp(to, *p, exp, true);
		LPCHARACTER mob = PetMob(*p);
		if (victim && mob)
			victim->CreateFly(FLY_CONQUEROR_EXP, mob);
	}

	// A Sung Ma map's monster of rank 1-4 died (the "alternative drop" of Yohara, en/tr): Smaczny Smakolyk 55042.
	void OnSungmaKill(CHARACTER* victim, CHARACTER* killer)
	{
		if (!victim || !killer || !killer->IsPC() || victim->IsPC())
			return;
		const int rank = victim->GetMobRank();
		if (rank < MOB_RANK_S_PAWN || rank > MOB_RANK_BOSS)
			return;
		if (number(1, 1000) > 10)	// 1 % (the wiki gives no rate)
			return;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(55042, 1);
		if (!item)
			return;
		PIXEL_POSITION pos;
		pos.x = victim->GetX() + number(-50, 50);
		pos.y = victim->GetY() + number(-50, 50);
		pos.z = victim->GetZ();
		item->AddToGround(victim->GetMapIndex(), pos);
		item->SetOwnership(killer);
		item->StartDestroyEvent();
	}

	// char_battle.cpp DeathPenalty (MT2009_PLUS_GROWTH_PET_V1 (death)): the summoned pet loses experience together
	// with its owner (pl) - the same share of its level's mob experience.
	void OnOwnerExpLoss(CHARACTER* ch, long long loss, long long levelNeed)
	{
		Pet* p = SummonedPet(ch);
		if (!p || loss <= 0 || levelNeed <= 0)
			return;
		const bool champion = IsChampion(*p);
		unsigned long long& cur = champion ? p->d.ullChampionExp : p->d.ullExp;
		const unsigned long long need = champion ? NeedChampionExpOf(p->d.dwChampionLevel) : NeedMobExpOf(p->d.dwLevel);
		const unsigned long long lost = need * (unsigned long long)Min64<S64>(loss, levelNeed) / (unsigned long long)levelNeed;
		cur = cur > lost ? cur - lost : 0;
		MarkDirty(*p);
		SendPoint(ch, *p, champion ? POINT_UPBRINGING_CHAMPION_EXP : POINT_UPBRINGING_PET_EXP);
	}

	// char.cpp ComputePoints (the old MT2009_PLUS_NEW_PET_V1 (points) hook): the summoned pet's bonuses.
	// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1 (log): one line when the summoned pet's skill bonuses change (summon, send away,
	// learn, upgrade, forget, death), at most one every 5 s a character - ComputePoints runs often.
	void LogSkillBonuses(CHARACTER* ch, const Pet* p, const std::string& line)
	{
		std::map<DWORD, Owner>::iterator it = s_owners.find(ch->GetPlayerID());
		if (it == s_owners.end())
			return;
		Owner& o = it->second;
		const time_t now = Now();
		if (o.skillLog == line || now - o.skillLogAt < 5)
			return;
		o.skillLog = line;
		o.skillLogAt = now;
		if (p)
			sys_log(0, "GROWTH_PET_SKILLS: %s pet %u (seal %u evo %d lv %u cl %u type %u) bonuses:%s", ch->GetName(), p->d.dwID,
					p->d.dwVnum, Stage(*p), p->d.dwLevel, p->d.dwChampionLevel, (unsigned)p->d.bType,
					line.empty() ? " none" : line.c_str());
		else
			sys_log(0, "GROWTH_PET_SKILLS: %s no pet out - no skill bonuses", ch->GetName());
	}

	// The point name of a passive skill (the proto's point_on), "" for an auto one.
	const char* PointOnName(BYTE skill)
	{
		const TGrowthPetSkillTable* t = BaseSkillProto(skill);
		return t && t->bType == GROWTH_PET_SKILL_USE_PASSIVE ? t->szPointOn : "";
	}

	void ApplyPoints(CHARACTER* ch)
	{
		Pet* p = SummonedPet(ch);
		if (!p || !IsAlive(*p))
		{
			if (s_owners.find(ch->GetPlayerID()) != s_owners.end())
				LogSkillBonuses(ch, NULL, "-");
			return;
		}
		const long long hp = (long long)ch->GetRealPoint(POINT_MAX_HP) * p->d.dwHP / 100000;
		const long long sp = (long long)ch->GetRealPoint(POINT_MAX_SP) * p->d.dwSP / 100000;
		const long long def = (long long)ch->GetPoint(POINT_DEF_GRADE) * p->d.dwDef / 100000;
		if (hp > 0)
			ch->PointChange(POINT_MAX_HP, (int)Min64<S64>(hp, 2000000000LL));
		if (sp > 0)
			ch->PointChange(POINT_MAX_SP, (int)Min64<S64>(sp, 2000000000LL));
		if (def > 0)
			ch->PointChange(POINT_DEF_GRADE, (int)Min64<S64>(def, 2000000000LL));
		if (IsChampion(*p))
		{
			if (p->d.dwChampionRes >= 1000)
				ch->PointChange(POINT_SUNGMA_PER_IMMUNE, (int)(p->d.dwChampionRes / 1000));
			if (p->d.dwChampionPrecision >= 1000)
				ch->PointChange(POINT_HIT_PCT, (int)(p->d.dwChampionPrecision / 1000));
		}
		std::string line;
		char part[96];
		if (Stage(*p) >= SKILL_OPEN_STAGE)
			for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
				if (p->d.aSkill[i].bSkill)
				{
					const BYTE sk = p->d.aSkill[i].bSkill;
					const int v = ApplyPassive(ch, *p, sk, SkillValue(*p, sk, p->d.aSkill[i].bLevel, false));
					if (v > 0)
					{
						snprintf(part, sizeof(part), " s%u/%u %s+%d", (unsigned)sk, (unsigned)p->d.aSkill[i].bLevel, PointOnName(sk), v);
						line += part;
					}
				}
		for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
			if (PotentialActive(*p, i))
			{
				const BYTE sk = p->d.aPotential[i].bSkill;
				const int v = ApplyPassive(ch, *p, sk, SkillValue(*p, sk, PotentialLevel(*p, i), true));
				if (v > 0)
				{
					snprintf(part, sizeof(part), " pot%d s%u/%d %s+%d", i, (unsigned)sk, PotentialLevel(*p, i), PointOnName(sk), v);
					line += part;
				}
			}
		LogSkillBonuses(ch, p, line);
	}

	// char.cpp EncodeInsertPacket: a growth pet's scale for the viewer (GC 235).
	void EncodeInsert(CHARACTER* pet, DESC* d)
	{
		if (!pet || !d || pet->IsPC())
			return;
		std::map<DWORD, DWORD>::const_iterator it = s_mobToPet.find(pet->GetVID());
		if (it == s_mobToPet.end())
			return;
		Pet* p = FindPet(it->second);
		if (!p)
			return;
		TPacketGCPetLook pack;
		pack.header = HEADER_GC_PET_LOOK;
		pack.dwVID = pet->GetVID();
		pack.wScalePct = ScalePct(*p);
		pack.bEvolution = (BYTE)Stage(*p);
		pack.bType78 = p->d.bType >= 7 ? 1 : 0;
		d->Packet(&pack, sizeof(pack));
	}

	// exchange.cpp CExchange::AddItem: a cage's pet for the trade partner's tooltip (GC 226).
	void OnExchangeItem(CHARACTER* from, CHARACTER* to, CItem* item)
	{
		if (!from || !to || !IsBag(item) || !item->GetSocket(2) || !HasClient(to))
			return;
		Pet* p = FindPet((DWORD)item->GetSocket(2));
		if (!p)
			return;
		TPacketGCPetSet pack;
		FillSet(*p, pack, HEADER_GC_PET_SET_EXCHANGE);
		to->GetDesc()->Packet(&pack, sizeof(pack));
	}

	bool IsInvincible(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC())
			return false;
		std::map<DWORD, Owner>::const_iterator it = s_owners.find(ch->GetPlayerID());
		return it != s_owners.end() && it->second.invincibleUntil && (DWORD)(get_dword_time() - (DWORD)it->second.invincibleUntil) > 0x80000000UL;
	}

	int BlockPenetration(CHARACTER* attacker)
	{
		Pet* p = attacker && attacker->IsPC() ? SummonedPet(attacker) : NULL;
		return p && IsChampion(*p) && IsAlive(*p) ? (int)(p->d.dwChampionBlockPen / 1000) : 0;
	}

	bool IsGrowthPetChar(CHARACTER* ch)
	{
		return ch && s_mobToPet.find(ch->GetVID()) != s_mobToPet.end();
	}

	void Packet(CHARACTER* ch, BYTE header, const char* data)
	{
		if (!ch || !ch->GetDesc() || !ch->IsPC())
			return;
		switch (header)
		{
			case HEADER_CG_PET_HATCH:
			{
				const TPacketCGPetHatch* pk = (const TPacketCGPetHatch*)data;
				char name[GROWTH_PET_NAME_MAX + 1];
				strlcpy(name, pk->name, sizeof(name));
				DoHatch(ch, FindHeldItemByPos(ch, pk->eggPos), name, true);
				break;
			}
			case HEADER_CG_PET_WINDOW:
				break;	// the hatching / renaming window opened or closed: nothing to keep
			case HEADER_CG_PET_WINDOW_TYPE:
			{
				const TPacketCGPetWindowType* pk = (const TPacketCGPetWindowType*)data;
				if (pk->type <= PET_WINDOW_PRIMIUM_FEEDSTUFF)
					SendSub(ch, (BYTE)(SUBHEADER_PET_WINDOW_TYPE_INFO + pk->type));
				break;
			}
			case HEADER_CG_PET_NAME_CHANGE:
				PacketNameChange(ch, (const TPacketCGPetNameChange*)data);
				break;
			case HEADER_CG_PET_FEED:
				PacketFeed(ch, (const TPacketCGPetFeed*)data);
				break;
			case HEADER_CG_PET_DETERMINE:
				PacketDetermine(ch, (const TPacketCGPetDetermine*)data);
				break;
			case HEADER_CG_PET_ATTR_CHANGE:
				PacketAttrChange(ch, (const TPacketCGPetAttrChange*)data);
				break;
			case HEADER_CG_PET_REVIVE:
				PacketRevive(ch, (const TPacketCGPetRevive*)data);
				break;
			case HEADER_CG_PET_LEARN_SKILL:
			{
				const TPacketCGPetLearnSkill* pk = (const TPacketCGPetLearnSkill*)data;
				Pet* p = SummonedPet(ch);
				if (!p)
					Say(ch, "Najpierw przywo\xb3" "aj zwierzaka.");
				else
					DoLearn(ch, *p, pk->slotIndex, FindHeldItemByPos(ch, pk->learnSkillPos));
				break;
			}
			case HEADER_CG_PET_SKILL_UPGRADE:
			{
				const TPacketCGPetSkillUpgrade* pk = (const TPacketCGPetSkillUpgrade*)data;
				Pet* p = SummonedPet(ch);
				if (p)
					DoUpgrade(ch, *p, pk->slotIndex);
				break;
			}
			case HEADER_CG_PET_DELETE_SKILL:
			{
				const TPacketCGPetDeleteSkill* pk = (const TPacketCGPetDeleteSkill*)data;
				Pet* p = SummonedPet(ch);
				LPITEM item = FindHeldItemByPos(ch, pk->deleteSkillPos);
				if (!p || pk->slotIndex >= GROWTH_PET_SKILL_SLOTS || !p->d.aSkill[pk->slotIndex].bSkill || !item ||
						item->GetType() != ITEM_PET || item->GetSubType() != PET_SKILL_DEL_BOOK)
					break;
				p->d.aSkill[pk->slotIndex].bSkill = 0;
				p->d.aSkill[pk->slotIndex].bLevel = 0;
				p->d.aSkill[pk->slotIndex].dwCooltime = 0;
				if (item->GetCount() > 1)
					item->SetCount(item->GetCount() - 1);
				else
					ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_SKILL_DEL");
				SaveNow(*p);
				SendSkills(ch, *p);
				SendSet(ch, *p);
				ch->ComputePoints();
				Say(ch, "Umiej\xeatno\x9c\xe6 zwierzaka zosta\xb3" "a usuni\xeata.");
				break;
			}
			case HEADER_CG_PET_DELETE_ALL_SKILL:
			{
				const TPacketCGPetDeleteAllSkill* pk = (const TPacketCGPetDeleteAllSkill*)data;
				Pet* p = SummonedPet(ch);
				LPITEM item = FindHeldItemByPos(ch, pk->deleteAllSkillPos);
				if (!p || !HasLearnedSkill(*p) || !item || item->GetType() != ITEM_PET || item->GetSubType() != PET_SKILL_ALL_DEL_BOOK)
					break;
				for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
				{
					p->d.aSkill[i].bSkill = 0;
					p->d.aSkill[i].bLevel = 0;
					p->d.aSkill[i].dwCooltime = 0;
				}
				if (item->GetCount() > 1)
					item->SetCount(item->GetCount() - 1);
				else
					ITEM_MANAGER::instance().RemoveItem(item, "GROWTH_PET_SKILL_DEL_ALL");
				SaveNow(*p);
				SendSkills(ch, *p);
				SendSet(ch, *p);
				ch->ComputePoints();
				Say(ch, "Wszystkie umiej\xeatno\x9c" "ci zwierzaka zosta\xb3y usuni\xeate.");
				break;
			}
			case HEADER_CG_PET_POTENTIAL:
				PacketPotential(ch, (const TPacketCGPetPotential*)data);
				break;
		}
	}

	// input_db.cpp (MT2009_PLUS_GROWTH_PET_V1 (db)): DG 185 (pets) and DG 186 (the skill proto).
	void DBPacket(DWORD dwHandle, BYTE header, const char* data)
	{
		if (header == HEADER_DG_GROWTH_PET_SKILL_TABLE)
		{
			LoadSkillTable(data);
			return;
		}
		if (header != HEADER_DG_GROWTH_PET_LOAD)
			return;
		const TPacketDGGrowthPetLoad* head = (const TPacketDGGrowthPetLoad*)data;
		LPDESC d = DESC_MANAGER::instance().FindByHandle(dwHandle);
		LPCHARACTER ch = d ? d->GetCharacter() : NULL;
		if (!ch || ch->GetPlayerID() != head->dwPID)
			return;
		OnLoaded(ch, head, (const TGrowthPet*)(data + sizeof(TPacketDGGrowthPetLoad)));
	}

	// GM /pet_set <level|clevel|evo|type|exp|iexp|cexp|life|age|skill <slot> <id> <lv>> <value> on the summoned pet.
	// MT2009_PLUS_PET_SKILL_TYPE_FIX_V1 (GM): /pet_set info [name] - the summoned pet's skills, what each should give
	// and the bonus points the character has now.
	void CommandInfo(CHARACTER* gm, CHARACTER* ch)
	{
		Pet* p = SummonedPet(ch);
		gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] %s: skill proto %u rows%s", ch->GetName(), (unsigned)s_skills.size(),
				s_skills.empty() ? " (NONE - db did not send the table)" : "");
		if (!p)
		{
			gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] no pet summoned (remembered id %u)", RememberedSummon(ch));
			return;
		}
		gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] pet %u seal %u evo %d lv %u cl %u type %u alive %d - skills %s", p->d.dwID,
				p->d.dwVnum, Stage(*p), p->d.dwLevel, p->d.dwChampionLevel, (unsigned)p->d.bType, IsAlive(*p) ? 1 : 0,
				Stage(*p) >= SKILL_OPEN_STAGE ? "open" : "closed (below Bohaterski)");
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS + GROWTH_PET_POTENTIAL_SLOTS; ++i)
		{
			const bool pot = i >= GROWTH_PET_SKILL_SLOTS;
			const int j = i - GROWTH_PET_SKILL_SLOTS;
			const BYTE sk = pot ? p->d.aPotential[j].bSkill : p->d.aSkill[i].bSkill;
			if (!sk || (pot && !PotentialActive(*p, j)))
				continue;
			const int lv = pot ? PotentialLevel(*p, j) : p->d.aSkill[i].bLevel;
			const TGrowthPetSkillTable* t = BaseSkillProto(sk);
			const TGrowthPetSkillTable* named = SkillProto(p->d.dwVnum, sk);
			const int value = SkillValue(*p, sk, lv, pot);
			if (t && t->bType == GROWTH_PET_SKILL_USE_PASSIVE)
			{
				const WORD point = PointOn(t);
				gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] %s%d %s (%u) lv %d passive %s: +%d (raw %d), point %u now %d",
						pot ? "pot" : "slot", pot ? j : i, named ? named->szName : "?", (unsigned)sk, lv, t->szPointOn,
						value / 10, value, (unsigned)point, point != POINT_NONE ? (int)ch->GetPoint(point) : 0);
			}
			else
				gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] %s%d %s (%u) lv %d %s: value %d, chance %d%%, cooldown %u s, ready in %d s",
						pot ? "pot" : "slot", pot ? j : i, named ? named->szName : "?", (unsigned)sk, lv,
						t ? (t->bType == GROWTH_PET_SKILL_USE_AUTO ? "auto" : "type?") : "no proto", value,
						pot ? (sk == SKILL_REMOVAL ? value / 10 : (t ? t->abActivate[MINMAX(1, lv, 20) - 1] : 0))
							: SkillActivatePct(*p, sk, lv, value),
						t ? (unsigned)t->dwCooldown : 0u,
						(int)MAX(0L, (long)(pot ? p->potentialCooltime[j] : p->d.aSkill[i].dwCooltime) - (long)Now()));
		}
		gm->ChatPacket(CHAT_TYPE_INFO, "[pet info] stats: max HP +%u.%03u%%, DEF +%u.%03u%%, max SP +%u.%03u%%",
				p->d.dwHP / 1000, p->d.dwHP % 1000, p->d.dwDef / 1000, p->d.dwDef % 1000, p->d.dwSP / 1000, p->d.dwSP % 1000);
	}

	void Command(CHARACTER* ch, const char* argument)
	{
		char a1[64], a2[64], a3[64], a4[64];
		const char* rest = one_argument(argument, a1, sizeof(a1));
		rest = one_argument(rest, a2, sizeof(a2));
		rest = one_argument(rest, a3, sizeof(a3));
		one_argument(rest, a4, sizeof(a4));
		if (!strcmp(a1, "info"))
		{
			LPCHARACTER target = *a2 ? CHARACTER_MANAGER::instance().FindPC(a2) : ch;
			if (!target)
				ch->ChatPacket(CHAT_TYPE_INFO, "[pet info] %s is not on this core", a2);
			else
				CommandInfo(ch, target);
			return;
		}
		Pet* p = SummonedPet(ch);
		if (!*a1 || !p)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "pet_set <level|clevel|evo|type|exp|iexp|cexp|life|age|skill slot id lv> <value> | info [name] (summoned pet)");
			return;
		}
		long long v = 0;
		str_to_number(v, a2);
		if (!strcmp(a1, "level"))
		{
			p->d.dwLevel = (DWORD)Clamp64<S64>(1, v, GROWTH_PET_MAX_LEVEL);
			p->d.ullExp = p->d.ullItemExp = 0;
			RecalcStats(*p);
		}
		else if (!strcmp(a1, "clevel"))
		{
			p->d.dwChampionLevel = (DWORD)Clamp64<S64>(0, v, GROWTH_PET_CHAMPION_MAX_LEVEL);
			RecalcStats(*p);
		}
		else if (!strcmp(a1, "evo"))
		{
			p->d.bEvolution = (BYTE)Clamp64<S64>(1, v, STAGE_MIGHTY);
			if (IsChampion(*p) && !p->d.dwChampionLevel)
			{
				p->d.dwChampionLevel = Stage(*p) == STAGE_MIGHTY ? 15 : 1;
				RollStart(*p, true);
			}
			RecalcStats(*p);
		}
		else if (!strcmp(a1, "type"))
		{
			p->d.bType = (BYTE)Clamp64<S64>(1, v, 8);
			RollAppliesKeepStart(*p);
			RecalcStats(*p);
		}
		else if (!strcmp(a1, "exp"))
			AddMobExp(ch, *p, (unsigned long long)Max64<S64>(0, v), IsChampion(*p));
		else if (!strcmp(a1, "iexp"))
			AddItemExp(ch, *p, (unsigned long long)Max64<S64>(0, v));
		else if (!strcmp(a1, "cexp"))
			AddMobExp(ch, *p, (unsigned long long)Max64<S64>(0, v), true);
		else if (!strcmp(a1, "life"))
			p->d.llEndTime = (long long)Now() + v;
		else if (!strcmp(a1, "age"))
			p->d.llBirthday = (long long)Now() - v * DAY;
		else if (!strcmp(a1, "skill"))
		{
			int slot = 0, lv = 1;
			str_to_number(slot, a2);
			long long id = 0;
			str_to_number(id, a3);
			str_to_number(lv, a4);
			if (slot >= 0 && slot < GROWTH_PET_SKILL_SLOTS)
			{
				p->d.aSkill[slot].bLocked = 0;
				p->d.aSkill[slot].bSkill = (BYTE)Clamp64<S64>(0, id, SKILL_COUNT);
				p->d.aSkill[slot].bLevel = (BYTE)MINMAX(1, lv, (int)GROWTH_PET_SKILL_LEVEL_MAX);
			}
		}
		SaveNow(*p);
		SyncSeal(ch, *p);
		SendSet(ch, *p);
		if (PetMob(*p))
			SpawnMob(ch, *p);
		ch->ComputePoints();
		ch->ChatPacket(CHAT_TYPE_INFO, "pet_set %s done (pet %u lv %u cl %u evo %u type %u)", a1, p->d.dwID, p->d.dwLevel,
				p->d.dwChampionLevel, (unsigned)p->d.bEvolution, (unsigned)p->d.bType);
	}
}

// ==== the engine's calls (extern "C++" free functions named in edits.json) ==========================================

int GrowthPetUseItem(LPCHARACTER ch, LPITEM item, TItemPos destCell) { return growth_pet::UseItem(ch, item, destCell); }
void GrowthPetOnItemLoad(LPCHARACTER ch) { growth_pet::OnItemLoad(ch); }
void GrowthPetOnSafeboxLoad(LPCHARACTER ch) { growth_pet::OnSafeboxLoad(ch); }
void GrowthPetOnItemAdd(LPCHARACTER ch, LPITEM item) { growth_pet::OnItemAdd(ch, item); }
void GrowthPetOnDestroy(LPCHARACTER ch) { growth_pet::OnDestroy(ch); }
void GrowthPetOnKillExp(LPCHARACTER victim, LPCHARACTER to, long long exp) { growth_pet::OnKillExp(victim, to, exp); }
// playerbot_champion.cpp declares it at block scope inside champion::GiveExp, i.e. as champion::GrowthPetOnChampionExp.
namespace champion { void GrowthPetOnChampionExp(LPCHARACTER victim, LPCHARACTER to, unsigned long long exp) { growth_pet::OnChampionExp(victim, to, exp); } }
void GrowthPetOnSungmaKill(LPCHARACTER victim, LPCHARACTER killer) { growth_pet::OnSungmaKill(victim, killer); }
void GrowthPetOnOwnerExpLoss(LPCHARACTER ch, long long loss, long long need) { growth_pet::OnOwnerExpLoss(ch, loss, need); }
void GrowthPetEncodeInsert(LPCHARACTER pet, LPDESC d) { growth_pet::EncodeInsert(pet, d); }
void GrowthPetOnExchangeItem(LPCHARACTER from, LPCHARACTER to, LPITEM item) { growth_pet::OnExchangeItem(from, to, item); }
bool GrowthPetIsInvincible(LPCHARACTER ch) { return growth_pet::IsInvincible(ch); }
int GrowthPetBlockPenetration(LPCHARACTER attacker) { return growth_pet::BlockPenetration(attacker); }
void GrowthPetPacket(LPCHARACTER ch, BYTE header, const char* data) { growth_pet::Packet(ch, header, data); }
void GrowthPetDBPacket(DWORD dwHandle, BYTE header, const char* data) { growth_pet::DBPacket(dwHandle, header, data); }

ACMD(do_pet_set)
{
	if (ch)
		growth_pet::Command(ch, argument);
}
