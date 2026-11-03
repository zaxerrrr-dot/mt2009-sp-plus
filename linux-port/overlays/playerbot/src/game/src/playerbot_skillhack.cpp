// MT2009_PLUS_SKILL_HACK_V1: the skills of the other specialisation (playerbot_skillhack.h,
// server-patches/skillhack/README.md).
#include "stdafx.h"
#include "playerbot_skillhack.h"
#include "playerbot_skill9.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "char.h"
#include "desc.h"
#include "desc_manager.h"
#include "questmanager.h"
#include "skill.h"

namespace skill2
{
	// The event flag every core reads (apply.sh writes it from M2_SKILL_HACK; web_admin.quest SKILL2 / "/e").
	const char* const FLAG = "m2_skill_hack";

	// The client's slots of the other path (client root skillhack.py): its places 1-6 in 61-66, its 9th skill in 67.
	const unsigned int CLIENT_SLOT_FIRST = 61;
	const unsigned int CLIENT_SLOT_LAST = 67;

	// The two paths' skills of the four classes, as CanUseSkill's SkillList (char_skill.cpp) - without the Ninja's 36
	// (no skill) and 51 (Deszcz Strzal, not used); the Warrior has five a path.
	const unsigned int PATH_SKILLS[4][2][6] =
	{
		{ {  1,   2,   3,   4,   5,   0 }, {  16,  17,  18,  19,  20,   0 } },
		{ { 31,  32,  33,  34,  35,   0 }, {  46,  47,  48,  49,  50,   0 } },
		{ { 61,  62,  63,  64,  65,  66 }, {  76,  77,  78,  79,  80,  81 } },
		{ { 91,  92,  93,  94,  95,  96 }, { 106, 107, 108, 109, 110, 111 } },
	};

	bool Enabled()
	{
		return quest::CQuestManager::instance().GetEventFlag(FLAG) != 0;
	}

	bool Applies(const CHARACTER* ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
			return false;
		const BYTE bGroup = ch->GetSkillGroup();
		return (bGroup == 1 || bGroup == 2) && ch->GetJob() <= JOB_SHAMAN;
	}

	bool IsForeign(const CHARACTER* ch, unsigned int dwVnum)
	{
		if (!ch || !dwVnum)
			return false;
		const BYTE bJob = ch->GetJob();
		const BYTE bGroup = ch->GetSkillGroup();
		if (bJob > JOB_SHAMAN || (bGroup != 1 && bGroup != 2))
			return false;
		const BYTE bOther = 3 - bGroup;
		if (skill9::IsNinth(dwVnum))
		{
			// The Warrior's Trzesienie (176) is both paths' - never foreign.
			const unsigned int dwOther = skill9::SkillFor(bJob, bOther);
			return dwOther == dwVnum && skill9::SkillFor(bJob, bGroup) != dwVnum;
		}
		for (int i = 0; i < 6; ++i)
			if (PATH_SKILLS[bJob][bOther - 1][i] == dwVnum)
				return true;
		return false;
	}

	// The other path's skills off: the quick slots that hold one of its client slots go (the owner's P8).
	static void ClearQuickslots(CHARACTER* ch)
	{
		for (BYTE pos = 0; pos < QUICKSLOT_MAX_NUM; ++pos)
		{
			TQuickslot* slot = NULL;
			if (!ch->GetQuickslot(pos, &slot) || !slot)
				continue;
			if (slot->type == QUICKSLOT_TYPE_SKILL && slot->pos >= CLIENT_SLOT_FIRST && slot->pos <= CLIENT_SLOT_LAST)
				ch->DelQuickslot(pos);
		}
	}

	void SendState(CHARACTER* ch, bool bResendLevels)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
			return;
		const bool bOn = Enabled() && Applies(ch);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "SKILL2 %d", bOn ? 1 : 0);
		if (bOn)
		{
			// The client registered the other path's slots on the command just now; the levels it got at the
			// login had nowhere to go yet - once more (one packet).
			if (bResendLevels)
				ch->SkillLevelPacket();
		}
		else
			ClearQuickslots(ch);
	}
}

using namespace skill2;

int Skill2Learnable(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsForeign(ch, dwVnum))
		return -1;
	// Off, or a bot / companion: the other path is not learnable - no points, books, Soul Stones or Ksiega
	// Zapomnienia (the engine's class-only rule let a book of the other path through before).
	if (!Applies(ch) || !Enabled())
		return 0;
	// The other 9th skill: playerbot_skill9.cpp's Skill9Learnable wants the own path - its own rule otherwise
	// (books by a Champion, Skill9BookCheck, still apply).
	if (skill9::IsNinth(dwVnum))
		return ch->GetSkillLevel(dwVnum) < SKILL_MAX_LEVEL ? 1 : 0;
	return -1;	// the engine's rule (the class, a chosen path, the top level)
}

int Skill2CanUse(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsForeign(ch, dwVnum))
		return -1;
	// As the own path's: true whatever the level (do_skillup asks this before the first point too).
	return Applies(ch) && Enabled() ? 1 : 0;
}

int Skill2NinthMotion(const CHARACTER* ch, unsigned int dwMotion)
{
	if (dwMotion >= 100)
		return -1;
	const unsigned int base = dwMotion % 25;
	if (base != 9 && base != 24)
		return -1;
	if (!Applies(ch) || !Enabled())
		return -1;
	const unsigned int dwOther = skill9::SkillFor(ch->GetJob(), 3 - ch->GetSkillGroup());
	if (!dwOther || !IsForeign(ch, dwOther) || skill9::MotionBase(dwOther) != base)
		return -1;
	// Learnt: the motion is the other 9th skill's - otherwise the own rule (Skill9UsableMotion) decides.
	return ch->GetSkillLevel(dwOther) > 0 ? 1 : -1;
}

bool Skill2MotionGroup(const CHARACTER* ch, unsigned int dwJobGroup)
{
	// IsUsableSkillMotion's job group is (job + 1) * 10 + path; the loop still wants the skill learnt (level > 0).
	if (!Applies(ch) || !Enabled())
		return false;
	return dwJobGroup == (unsigned int) ((ch->GetJob() + 1) * 10 + (3 - ch->GetSkillGroup()));
}

void Skill2OnLogin(CHARACTER* ch)
{
	SendState(ch, true);
}

void Skill2FlagChanged(int iValue, int iPrev)
{
	if ((iValue != 0) == (iPrev != 0))
		return;
	sys_log(0, "SKILL2: %s (event flag %s = %d)", iValue ? "on" : "off", FLAG, iValue);
	const DESC_MANAGER::DESC_SET& c_set = DESC_MANAGER::instance().GetClientSet();
	for (DESC_MANAGER::DESC_SET::const_iterator it = c_set.begin(); it != c_set.end(); ++it)
	{
		LPDESC d = *it;
		if (!d || d->IsBot() || !d->GetCharacter())
			continue;
		SendState(d->GetCharacter(), iValue != 0);
	}
}
