// MT2009_PLUS_MLODZI_BOHATEROWIE_V1: Bronie dla Mlodych Bohaterow - the rule, the grant and the quests' "mlodzi"
// module (playerbot_mlodzi.h; quest mlodzi_bohaterowie; server-patches/mlodzi registers the module and refuses the
// bonus / refine / transmutation paths for these weapons).
//
//   mlodzi.enabled()            true unless M2_MLODZI_BOHATEROWIE=0 (event flag m2_mlodzi_off)
//   mlodzi.offer()              the tier the character may take now (1-8), 0 none
//   mlodzi.tier_level(tier)     1, 10, 20 ... 70
//   mlodzi.weapons()            n, vnum1, vnum2, vnum3 - the weapons of the current offer for the character's class
//   mlodzi.claim(tier, choice)  status (EClaim), vnum - the server checks everything again; the client sends only
//                               the tier and the 1-based choice, never a vnum
//   mlodzi.is_weapon(vnum)      true for 21900-21975 (kind 0-5)
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "questlua.h"
#include "playerbot_mlodzi.h"

namespace mlodzi
{
	static const char* const FLAG_CLAIMED = "mlodzi_bohaterowie.claimed";
	static const char* const FLAG_SEEN = "mlodzi_bohaterowie.seen";

	bool Enabled()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_mlodzi_off") == 0;
	}

	bool IsWeaponVnum(unsigned int vnum)
	{
		return vnum >= FIRST_VNUM && vnum <= LAST_VNUM && (vnum % 10) <= KIND_FAN;
	}

	bool IsWeapon(const CItem* item)
	{
		return item && IsWeaponVnum(const_cast<CItem*>(item)->GetVnum());
	}

	int TierForLevel(int level)
	{
		if (level < 1)
			return 0;
		const int tier = level / 10 + 1;
		return tier > TIER_COUNT ? TIER_COUNT : tier;
	}

	int TierLevel(int tier)
	{
		if (tier < 1 || tier > TIER_COUNT)
			return 0;
		return tier == 1 ? 1 : (tier - 1) * 10;
	}

	int TierOfVnum(unsigned int vnum)
	{
		return IsWeaponVnum(vnum) ? (int)(vnum - FIRST_VNUM) / 10 + 1 : 0;
	}

	int AverageDamage(int tier)
	{
		if (tier < 1)
			return 0;
		const int v = 10 + 3 * (tier - 1);
		return v > 30 ? 30 : v;
	}

	// the wiki's choices: Wojownik miecz / dwureczna, Ninja miecz / sztylet / luk, Sura miecz, Szaman dzwon / wachlarz
	static const int KINDS[4][MAX_CHOICES] = {
		{ KIND_SWORD, KIND_TWO_HANDED, -1 },		// JOB_WARRIOR
		{ KIND_SWORD, KIND_DAGGER, KIND_BOW },		// JOB_ASSASSIN
		{ KIND_SWORD, -1, -1 },				// JOB_SURA
		{ KIND_BELL, KIND_FAN, -1 },			// JOB_SHAMAN
	};

	int ChoiceCount(int job)
	{
		if (job < 0 || job > 3)
			return 0;
		int n = 0;
		for (int i = 0; i < MAX_CHOICES; ++i)
			if (KINDS[job][i] >= 0)
				++n;
		return n;
	}

	int ChoiceKind(int job, int choice)
	{
		if (choice < 1 || choice > ChoiceCount(job))
			return -1;
		return KINDS[job][choice - 1];
	}

	unsigned int WeaponVnum(int tier, int job, int choice)
	{
		const int kind = ChoiceKind(job, choice);
		if (tier < 1 || tier > TIER_COUNT || kind < 0)
			return 0;
		return FIRST_VNUM + 10 * (tier - 1) + kind;
	}

	int CurrentOffer(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC() || !Enabled() || !ChoiceCount(ch->GetJob()))
			return 0;
		const int tier = TierForLevel(ch->GetLevel());
		if (!tier)
			return 0;
		const int seen = ch->GetQuestFlag(FLAG_SEEN);
		if (tier > seen)
			ch->SetQuestFlag(FLAG_SEEN, tier);
		// a tier skipped is gone: only the tier of the character's level, never one below the highest reached
		if (tier < seen || tier <= ch->GetQuestFlag(FLAG_CLAIMED))
			return 0;
		return tier;
	}

	static bool ValidProto(const TItemTable* p, int tier)
	{
		if (!p || p->bType != ITEM_WEAPON || p->bSize < 1 || p->bSize > 3 || p->dwRefinedVnum != 0 ||
			p->bAlterToMagicItemPct != 0 || p->bGainSocketPct != 0)
			return false;
		const unsigned int need = ITEM_ANTIFLAG_DROP | ITEM_ANTIFLAG_SELL | ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_PKDROP |
			ITEM_ANTIFLAG_MYSHOP | ITEM_ANTIFLAG_SAFEBOX;
		if ((p->dwAntiFlags & need) != need || (p->dwAntiFlags & ITEM_ANTIFLAG_SAVE))
			return false;
		bool level = false, timer = false;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			if (p->aLimits[i].bType == LIMIT_LEVEL && p->aLimits[i].lValue == TierLevel(tier))
				level = true;
			if (p->aLimits[i].bType == LIMIT_REAL_TIME && p->aLimits[i].lValue == LIFE_SECONDS)
				timer = true;
		}
		return level && timer;	// never a weapon without its 15 days
	}

	int Claim(CHARACTER* ch, int tier, int choice, unsigned int* awardedVnum)
	{
		if (awardedVnum)
			*awardedVnum = 0;
		if (!ch || !ch->IsPC())
			return CLAIM_FAILED;
		if (!Enabled())
			return CLAIM_DISABLED;
		const unsigned int vnum = WeaponVnum(tier, ch->GetJob(), choice);
		if (!vnum)
			return CLAIM_BAD_CHOICE;
		if (CurrentOffer(ch) != tier)
			return CLAIM_NOT_OFFERED;
		if (!ch->CanHandleItem())
			return CLAIM_BUSY;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!ValidProto(proto, tier))
		{
			sys_err("MLODZI: item_proto %u is missing or not a young heroes' weapon (mlodzi_bohaterowie.sql)", vnum);
			return CLAIM_BAD_PROTO;
		}
		// never AutoGiveItem: a full inventory must not drop the weapon on the ground - nothing is used up then
		const int cell = ch->GetEmptyInventory(proto->bSize);
		if (cell < 0)
			return CLAIM_NO_SPACE;
		// LIMIT_REAL_TIME: CreateItem sets socket0 = now + 1296000 and starts the expiry event itself
		LPITEM item = ITEM_MANAGER::instance().CreateItem(vnum, 1, 0, false);
		if (!item)
			return CLAIM_FAILED;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			item->SetForceAttribute(i, 0, 0);
		// an attribute's type is a POINT_* number in this engine (as item_proto's applytype)
		item->SetForceAttribute(0, POINT_NORMAL_HIT_DAMAGE_BONUS, AverageDamage(tier));
		if (!item->AddToCharacter(ch, TItemPos(INVENTORY, cell)))
		{
			M2_DESTROY_ITEM(item);
			return CLAIM_FAILED;
		}
		ch->SetQuestFlag(FLAG_CLAIMED, tier);
		if (ch->GetQuestFlag(FLAG_SEEN) < tier)
			ch->SetQuestFlag(FLAG_SEEN, tier);
		item->Save();
		sys_log(0, "MLODZI_GRANT pid=%u name=%s tier=%d item=%u vnum=%u expiry=%ld", ch->GetPlayerID(), ch->GetName(),
			tier, item->GetID(), vnum, item->GetSocket(0));
		if (awardedVnum)
			*awardedVnum = vnum;
		return CLAIM_OK;
	}

	long SecondsLeft(const CItem* item)
	{
		if (!IsWeapon(item))
			return 0;
		const long left = const_cast<CItem*>(item)->GetSocket(0) - get_global_time();
		return left > 0 ? left : 0;
	}
}

bool MlodziIsWeaponVnum(unsigned int vnum)
{
	return mlodzi::IsWeaponVnum(vnum);
}

bool MlodziRefuseChange(CHARACTER* ch, CItem* item)
{
	if (!mlodzi::IsWeapon(item))
		return false;
	if (ch)
		ch->ChatPacket(CHAT_TYPE_INFO, "Broni dla Mlodych Bohaterow nie mozna ulepszac ani zmieniac.");
	return true;
}

namespace quest
{
	static int mlodzi_enabled(lua_State* L)
	{
		lua_pushboolean(L, mlodzi::Enabled());
		return 1;
	}

	static int mlodzi_offer(lua_State* L)
	{
		lua_pushnumber(L, mlodzi::CurrentOffer(CQuestManager::instance().GetCurrentCharacterPtr()));
		return 1;
	}

	static int mlodzi_tier_level(lua_State* L)
	{
		lua_pushnumber(L, mlodzi::TierLevel(lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : 0));
		return 1;
	}

	static int mlodzi_weapons(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const int tier = mlodzi::CurrentOffer(ch);
		const int n = tier && ch ? mlodzi::ChoiceCount(ch->GetJob()) : 0;
		lua_pushnumber(L, n);
		for (int i = 1; i <= mlodzi::MAX_CHOICES; ++i)
			lua_pushnumber(L, i <= n ? mlodzi::WeaponVnum(tier, ch->GetJob(), i) : 0);
		return 1 + mlodzi::MAX_CHOICES;
	}

	static int mlodzi_claim(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		int status = mlodzi::CLAIM_BAD_CHOICE;
		unsigned int vnum = 0;
		if (ch && lua_isnumber(L, 1) && lua_isnumber(L, 2))
		{
			const double t = lua_tonumber(L, 1), c = lua_tonumber(L, 2);
			// bounds before the conversion also refuse NaN, infinities and fractions
			if (t >= 1 && t <= mlodzi::TIER_COUNT && c >= 1 && c <= mlodzi::MAX_CHOICES && t == (int)t && c == (int)c)
				status = mlodzi::Claim(ch, (int)t, (int)c, &vnum);
		}
		lua_pushnumber(L, status);
		lua_pushnumber(L, vnum);
		return 2;
	}

	static int mlodzi_is_weapon(lua_State* L)
	{
		lua_pushboolean(L, lua_isnumber(L, 1) && mlodzi::IsWeaponVnum((unsigned int)lua_tonumber(L, 1)));
		return 1;
	}

	void RegisterMlodziFunctionTable()
	{
		luaL_reg mlodzi_functions[] =
		{
			{ "enabled",		mlodzi_enabled		},
			{ "offer",		mlodzi_offer		},
			{ "tier_level",		mlodzi_tier_level	},
			{ "weapons",		mlodzi_weapons		},
			{ "claim",		mlodzi_claim		},
			{ "is_weapon",		mlodzi_is_weapon	},
			{ NULL,			NULL			}
		};

		CQuestManager::instance().AddLuaFunctionTable("mlodzi", mlodzi_functions);
	}
}
