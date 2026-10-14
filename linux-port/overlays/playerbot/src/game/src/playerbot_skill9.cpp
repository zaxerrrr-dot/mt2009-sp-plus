// MT2009_PLUS_SKILL9_V1: the 9th skills of Yohara (playerbot_skill9.h, server-patches/skill9/README.md).
#include "stdafx.h"
#include "playerbot_skill9.h"
#include "playerbot_champion.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "char.h"
#include "char_manager.h"
#include "affect.h"
#include "skill.h"

#include <set>

namespace skill9
{
	bool IsNinth(unsigned int dwVnum)
	{
		return dwVnum >= SKILL_FINISH && dwVnum <= SKILL_CHEONUN;
	}

	unsigned int SkillFor(unsigned char bJob, unsigned char bGroup)
	{
		if (bGroup != 1 && bGroup != 2)
			return 0;
		switch (bJob)
		{
			case JOB_WARRIOR:	return SKILL_FINISH;
			case JOB_ASSASSIN:	return bGroup == 1 ? SKILL_ILGWANGPYO : SKILL_PUNGLOEPO;
			case JOB_SURA:		return bGroup == 1 ? SKILL_GEOMAGGWI : SKILL_MABEOBAGGWI;
			case JOB_SHAMAN:	return bGroup == 1 ? SKILL_METEO : SKILL_CHEONUN;
		}
		return 0;
	}

	unsigned int MotionBase(unsigned int dwVnum)
	{
		switch (dwVnum)
		{
			case SKILL_FINISH:
			case SKILL_ILGWANGPYO:
			case SKILL_GEOMAGGWI:
			case SKILL_METEO:
				return 9;
			case SKILL_PUNGLOEPO:
			case SKILL_MABEOBAGGWI:
			case SKILL_CHEONUN:
				return 24;
		}
		return 0;
	}

	unsigned int BookCost(unsigned int bSkillLevel)
	{
		return bSkillLevel < 20 ? BOOK_CHAMPION_EXP_NORMAL : BOOK_CHAMPION_EXP_MASTER;
	}

	int CheonunProtectSeconds(int iChance)
	{
		// chance = 18.4*k, seconds = 4*k: 0/9/15/23 % -> 0/2/3/5 s (the wiki's table), rounded.
		return iChance <= 0 ? 0 : (iChance * 10 + 23) / 46;
	}
}

using namespace skill9;

int Skill9Learnable(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsNinth(dwVnum))
		return -1;
	if (!ch || !ch->GetSkillGroup())
		return 0;
	if (SkillFor(ch->GetJob(), ch->GetSkillGroup()) != dwVnum)
		return 0;
	return ch->GetSkillLevel(dwVnum) < SKILL_MAX_LEVEL ? 1 : 0;
}

int Skill9BookCheck(CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsNinth(dwVnum) || !ch)
		return 1;
	if (ch->GetConquerorLevel() < 1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ta ksiega jest dla Czempionow: przeczytasz ja od 1. Poziomu Czempiona.");
		return 0;
	}
	const unsigned int cost = BookCost(ch->GetSkillLevel(dwVnum));
	if (ch->GetConquerorExp() < cost)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Kazda proba czytania tej ksiegi kosztuje %u PD Czempiona - masz za malo.", cost);
		return 0;
	}
	return 1;
}

void Skill9BookPay(CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsNinth(dwVnum) || !ch)
		return;
	// The level before the read (this runs before the roll and SkillLevelUp).
	const unsigned int cost = BookCost(ch->GetSkillLevel(dwVnum));
	const DWORD exp = ch->GetConquerorExp();
	ch->SetConquerorExp(exp > cost ? exp - cost : 0);
	champion::SendInfo(ch);
}

int Skill9CanUse(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsNinth(dwVnum))
		return -1;
	if (!ch || !ch->GetSkillGroup())
		return 0;
	return SkillFor(ch->GetJob(), ch->GetSkillGroup()) == dwVnum ? 1 : 0;
}

int Skill9UsableMotion(const CHARACTER* ch, unsigned int dwMotion)
{
	if (dwMotion >= 100)
		return -1;
	const unsigned int base = dwMotion % 25;
	if (base != 9 && base != 24)
		return -1;
	if (!ch)
		return 0;
	const unsigned int vnum = SkillFor(ch->GetJob(), ch->GetSkillGroup());
	if (!vnum || MotionBase(vnum) != base)
		return 0;
	return ch->GetSkillLevel(vnum) > 0 ? 1 : 0;
}

// Tarcza Eteru: while its affect lasts, a roll every 12 seconds (the first a second after it comes); a success
// protects its holder for CheonunProtectSeconds(chance) - every blow is blocked (Skill9Blocked). One event a
// holder, by VID (a character gone or without the affect ends it).
EVENTINFO(skill9_cheonun_info)
{
	DWORD vid;
	skill9_cheonun_info() : vid(0) {}
};

static std::set<DWORD> s_setCheonunVID;

EVENTFUNC(skill9_cheonun_event)
{
	skill9_cheonun_info* info = dynamic_cast<skill9_cheonun_info*>(event->info);
	if (!info)
		return 0;

	LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(info->vid);
	CAffect* pkAff = ch ? ch->FindAffect(SKILL_CHEONUN) : NULL;
	if (!pkAff)
	{
		s_setCheonunVID.erase(info->vid);
		return 0;
	}

	const int chance = (int)pkAff->lApplyValue;
	const int sec = CheonunProtectSeconds(chance);
	if (!ch->IsDead() && sec > 0 && number(1, 100) <= chance)
	{
		ch->AddAffect(AFFECT_CHEONUN_INVINCIBILITY, POINT_NONE, 0, AFF_NONE, sec, 0, true);
		char szEffect[MAX_EFFECT_FILE_NAME] = {};
		strlcpy(szEffect, "d:/ymir work/pc/shaman/effect/chunwoon_moojuk.mse", sizeof(szEffect));
		ch->SpecificEffectPacket(szEffect);
	}

	return PASSES_PER_SEC(CHEONUN_PERIOD_SEC);
}

void Skill9ComputeAffect(CHARACTER* ch, const CAffect* pkAff, bool bAdd)
{
	if (!ch || !pkAff || !bAdd || pkAff->dwType != SKILL_CHEONUN)
		return;
	const DWORD vid = (DWORD)ch->GetVID();
	if (!s_setCheonunVID.insert(vid).second)
		return;
	skill9_cheonun_info* info = AllocEventInfo<skill9_cheonun_info>();
	info->vid = vid;
	event_create(skill9_cheonun_event, info, PASSES_PER_SEC(1));
}

void Skill9RemoveAffects(CHARACTER* ch)
{
	if (!ch)
		return;
	ch->RemoveAffect(SKILL_CHEONUN);
	ch->RemoveAffect(AFFECT_CHEONUN_INVINCIBILITY);
}

int Skill9Blocked(CHARACTER* victim, CHARACTER* attacker)
{
	return victim && attacker && victim->FindAffect(AFFECT_CHEONUN_INVINCIBILITY) ? 1 : 0;
}

unsigned int Skill9MeleeReach(unsigned int dwVnum)
{
	// Trzesienie's four blows land 100..450 ahead of the Warrior with a radius of 100 (finish*.msa).
	return dwVnum == SKILL_FINISH ? 600 : 0;
}
