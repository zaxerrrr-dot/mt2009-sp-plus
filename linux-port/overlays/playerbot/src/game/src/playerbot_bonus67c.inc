// MT2009_PLUS_BONUS67_SKILL_V1 - the 6th/7th bonuses of the wiki round 3 (the owner, 4 November 2026: "add ALL the missing
// 6/7 bonuses exactly as on the wiki, without the Lycan"; server-patches/bonusy67c/README.md). Included once by
// playerbot_bonus67.cpp (after its cooldown event, before Bonus67SkillCooldown) and only with the patch
// (MT2009_PLUS_BONUS67_SKILL from common/length.h) - it uses that file's IsPlayer / EventFlag / Reached and the
// bonus67_cooltime event. The points 256-318 and what each one does: tools/bonusy67/bonusy67c_data.py; the table
// below is generated from it (playerbot_bonus67c_table.h).
//
// The wiki gives each line's range only (x% / x seconds) - what the engine does with it is ours, as close to the
// official words as this engine allows:
//   * "Absorbuje x% PZ przy uzyciu <umiejetnosc>": x% of the HP the skill's blow took from its victim comes back to
//     the attacker (each victim of a splash skill; the HP potion's fly from the victim, as the engine's STEAL_HP).
//   * "Czas regeneracji <umiejetnosc>: -x sek. z 10% / 20% szans": using the skill, with that chance its cooldown is
//     x seconds shorter (never below 1 s left); the client's cooldown ends with the server's
//     (HEADER_GC_SKILL_COOLTIME_END, as the gloves' lines). Both lines on one character: each rolls, the longer cut.
//   * "Czas trwania <umiejetnosc> +x sek.": the skill's affect x seconds longer (after the items' per cent).
//   * "Na x sek. otrzymujesz bonus do ataku / obrony / zwieksza szybkosc zaklecia przy uzyciu <umiejetnosc>": using
//     the skill gives the caster Wartosc Ataku + b67_skill_att (50) / Obrona + b67_skill_def (50) / Szybkosc
//     zaklecia + b67_skill_cast (20%) for x seconds (one affect each: 830 / 831 / 832, a new use starts it again).
//     The wiki gives no amount: the defaults are the 6th/7th Wartosc Ataku line's maximum (50) and the same for the
//     defence; event flags change them.
//   * "<Umiejetnosc> ma x% szans na ogluszenie przeciwnika": each victim the skill's blow hurt is stunned with x%
//     chance (2 s a player, 4 s a monster - as STUN_PCT's normal hit), unless immune (IMMUNE_STUN, champion immunity).
//   * "<Umiejetnosc> ma x% szans na oddanie przeciwnikowi": the same chance to knock the victim back b67_knock_length
//     (300) away from the attacker (CHARACTER::Knockback - a boss, a Metin, a monster that never moves and
//     "Odpornosc na Upadek" resist it; never into a wall).
//   * "Obrazenia od <umiejetnosc> +x%" (the body armour): the skill's damage x% higher, before the victim's defence
//     lines (Damage).
// Wola Zycia (6), Krag Mieczy (21) and Wolno Dzialajaca Trucizna (36) are not skills of this world (no skill_proto row,
// no place in the skill window): their lines work by number, but their pool rows roll nowhere (bonusy67c_wiki.sql).
namespace
{
	enum
	{
		B67C_RANK, B67C_PER, B67C_ABSORB, B67C_CD10, B67C_CD20, B67C_DUR, B67C_ATT, B67C_DEF, B67C_CAST, B67C_STUN,
		B67C_KNOCK, B67C_SKDMG,
	};
	enum
	{
		AFFECT_B67C_SKILL_ATT = 830,	// "bonus do ataku przy uzyciu ..." (free numbers: no other affect uses 820-849)
		AFFECT_B67C_SKILL_DEF = 831,	// "bonus do obrony przy uzyciu ..."
		AFFECT_B67C_SKILL_CAST = 832,	// "zwieksza szybkosc zaklecia przy uzyciu ..."
	};

	struct TB67cLine
	{
		WORD wPoint;
		BYTE bKind;
		BYTE bSkill;
	};
#include "playerbot_bonus67c_table.h"

	const TB67cLine* B67cFindPoint(int iPoint)
	{
		for (size_t i = 0; i < sizeof(s_aB67cLine) / sizeof(s_aB67cLine[0]); ++i)
			if (s_aB67cLine[i].wPoint == iPoint)
				return &s_aB67cLine[i];
		return NULL;
	}

	// The value of the character's line of this kind for this skill (0: none).
	int B67cLine(const CHARACTER* ch, int iKind, unsigned int dwVnum)
	{
		if (!dwVnum || dwVnum > 255)
			return 0;
		for (size_t i = 0; i < sizeof(s_aB67cLine) / sizeof(s_aB67cLine[0]); ++i)
			if (s_aB67cLine[i].bKind == iKind && s_aB67cLine[i].bSkill == dwVnum)
				return MAX(0, (int) ch->GetPoint(s_aB67cLine[i].wPoint));
		return 0;
	}

	// The class of a skill of the four classes (1-21 warrior, 31-51 ninja, 61-81 sura, 91-111 shaman) and its way
	// (1: the first 15 numbers of the class, 2: the next 15); -1 for any other.
	int B67cSkillJob(unsigned int dwVnum)
	{
		if (dwVnum < 1 || dwVnum > 111)
			return -1;
		const int iJob = (int) (dwVnum - 1) / 30;
		return (int) (dwVnum - 1) % 30 < 21 ? iJob : -1;
	}

	int B67cSkillGroup(unsigned int dwVnum)
	{
		return (int) (dwVnum - 1) % 30 < 15 ? 1 : 2;
	}

	bool B67cIsArcherSkill(unsigned int dwVnum)
	{
		return dwVnum >= 46 && dwVnum <= 51;
	}

	// The cooldown cut: the client's cooldown ends when the server's does (the gloves' event).
	void B67cCooltimeEndAt(LPCHARACTER ch, unsigned int dwVnum, DWORD dwAt)
	{
		if (!ch->GetDesc())
			return;
		bonus67_cooltime_info* info = AllocEventInfo<bonus67_cooltime_info>();
		info->dwVID = (DWORD) ch->GetVID();
		info->bSkill = (BYTE) dwVnum;
		const DWORD dwNow = get_dword_time();
		const long lPasses = MAX(1L, (long) PASSES_PER_SEC(1) * (long) (dwAt - dwNow + 200) / 1000L);
		event_create(bonus67_cooltime_event, info, lPasses);
	}
}

// "Czas regeneracji <umiejetnosc>: -x sek. z 10% / 20% szans" - the new next usable time.
static unsigned int Bonus67cCooldownCut(LPCHARACTER ch, unsigned int dwVnum, unsigned int dwNextUsable)
{
	const int iSec20 = B67cLine(ch, B67C_CD20, dwVnum);
	const int iSec10 = B67cLine(ch, B67C_CD10, dwVnum);
	int iCut = 0;
	if (iSec20 > 0 && number(1, 100) <= 20)
		iCut = iSec20;
	if (iSec10 > 0 && number(1, 100) <= 10)
		iCut = MAX(iCut, iSec10);
	iCut = MIN(iCut, 60);
	if (iCut <= 0)
		return dwNextUsable;
	const DWORD dwNow = get_dword_time();
	if (!Reached(dwNextUsable, dwNow + 1500))
		return dwNextUsable;	// less than 1.5 s left: nothing to cut
	const DWORD dwCutMs = MIN((DWORD) iCut * 1000, dwNextUsable - dwNow - 1000);
	const DWORD dwNew = dwNextUsable - dwCutMs;
	B67cCooltimeEndAt(ch, dwVnum, dwNew);
	if (ch->GetDesc())
		ch->ChatPacket(CHAT_TYPE_INFO, "Bonus: czas regeneracji tej umiejetnosci krotszy o %d sek.", (int) ((dwCutMs + 500) / 1000));
	return dwNew;
}

// "Na x sek. otrzymujesz bonus do ataku / obrony / zwieksza szybkosc zaklecia przy uzyciu <umiejetnosc>".
static void Bonus67cSkillUsed(LPCHARACTER ch, unsigned int dwVnum)
{
	static const struct
	{
		int iKind;
		DWORD dwAffect;
		WORD wPoint;
		const char* c_pszFlag;
		int iDefault;
		int iMax;
	} s_aBuff[] = {
		{ B67C_ATT, AFFECT_B67C_SKILL_ATT, POINT_ATT_GRADE_BONUS, "b67_skill_att", 50, 1000 },
		{ B67C_DEF, AFFECT_B67C_SKILL_DEF, POINT_DEF_GRADE_BONUS, "b67_skill_def", 50, 1000 },
		{ B67C_CAST, AFFECT_B67C_SKILL_CAST, POINT_CASTING_SPEED, "b67_skill_cast", 20, 100 },
	};
	for (size_t i = 0; i < sizeof(s_aBuff) / sizeof(s_aBuff[0]); ++i)
	{
		const int iSec = MIN(B67cLine(ch, s_aBuff[i].iKind, dwVnum), 60);
		if (iSec <= 0)
			continue;
		ch->AddAffect(s_aBuff[i].dwAffect, s_aBuff[i].wPoint, EventFlag(s_aBuff[i].c_pszFlag, s_aBuff[i].iDefault, s_aBuff[i].iMax),
				AFF_NONE, iSec, 0, true);
	}
}

int Bonus67SkillHitDamage(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, unsigned int dwVnum, int iDam)
{
	if (!IsPlayer(pkAttacker) || !pkVictim || iDam <= 0)
		return iDam;
	const int iPct = MIN(B67cLine(pkAttacker, B67C_SKDMG, dwVnum), 100);
	if (iPct > 0)
		iDam += (int) ((long long) iDam * iPct / 100);
	return iDam;
}

void Bonus67SkillHitAfter(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, unsigned int dwVnum, int iDealt, bool bDead)
{
	if (!IsPlayer(pkAttacker) || !pkVictim || pkVictim == pkAttacker || iDealt <= 0 || pkAttacker->IsDead())
		return;

	const int iAbsorb = MIN(B67cLine(pkAttacker, B67C_ABSORB, dwVnum), 100);
	if (iAbsorb > 0)
	{
		const int iHP = (int) ((long long) iDealt * iAbsorb / 100);
		if (iHP > 0 && pkAttacker->GetHP() < pkAttacker->GetMaxHP())
		{
			if (!bDead)
				pkVictim->CreateFly(FLY_HP_SMALL, pkAttacker);
			pkAttacker->PointChange(POINT_HP, iHP);
		}
	}
	if (bDead || pkVictim->IsDead() || pkVictim->IsStone() || pkVictim->IsDoor())
		return;

	const int iStun = MIN(B67cLine(pkAttacker, B67C_STUN, dwVnum), 100);
	if (iStun > 0 && number(1, 100) <= iStun && !pkVictim->IsAffectFlag(AFF_STUN) &&
			!pkVictim->IsImmune(IMMUNE_STUN, pkAttacker))
	{
		bool ChampionImmuneBlocks(LPCHARACTER, LPCHARACTER);
		if (!ChampionImmuneBlocks(pkAttacker, pkVictim))
			pkVictim->AddAffect(AFFECT_STUN, POINT_NONE, 0, AFF_STUN, pkVictim->IsPC() ? 2 : 4, 0, true);
	}

	const int iKnock = MIN(B67cLine(pkAttacker, B67C_KNOCK, dwVnum), 100);
	if (iKnock > 0 && number(1, 100) <= iKnock && pkVictim->GetSectree())
	{
		const float fx = (float) (pkVictim->GetX() - pkAttacker->GetX());
		const float fy = (float) (pkVictim->GetY() - pkAttacker->GetY());
		const float fLen = sqrtf(fx * fx + fy * fy);
		if (fLen >= 1.0f)
		{
			VECTOR dir;
			dir.x = fx / fLen;
			dir.y = fy / fLen;
			dir.z = 0.0f;
			const int iPush = EventFlag("b67_knock_length", 300, 1000);
			const long lDestX = pkVictim->GetX() + (long) (dir.x * iPush);
			const long lDestY = pkVictim->GetY() + (long) (dir.y * iPush);
			if (!pkVictim->GetSectree()->IsAttr(lDestX, lDestY, ATTR_BLOCK | ATTR_OBJECT))
				pkVictim->Knockback(pkAttacker, iPush, dir);
		}
	}
}

int Bonus67SkillDurationSec(LPCHARACTER ch, unsigned int dwVnum)
{
	if (!IsPlayer(ch))
		return 0;
	return MIN(B67cLine(ch, B67C_DUR, dwVnum), 60);
}

bool Bonus67RareFits(CItem* item, int iApply)
{
	const TB67cLine* pLine = B67cFindPoint(iApply);
	if (!item || !pLine || !pLine->bSkill)
		return true;
	static const DWORD s_adwAnti[4] = { ITEM_ANTIFLAG_WARRIOR, ITEM_ANTIFLAG_ASSASSIN, ITEM_ANTIFLAG_SURA, ITEM_ANTIFLAG_SHAMAN };
	const int iJob = B67cSkillJob(pLine->bSkill);
	if (iJob < 0 || iJob > 3)
		return false;
	if (IS_SET(item->GetAntiFlag(), s_adwAnti[iJob]))
		return false;	// its class cannot wear it
	// a bow takes only the archer's lines, any other weapon never theirs (the dagger ninja's are not a bow's)
	if (item->GetType() == ITEM_WEAPON && iJob == JOB_ASSASSIN &&
			B67cIsArcherSkill(pLine->bSkill) != (item->GetSubType() == WEAPON_BOW))
		return false;
	return true;
}

int Bonus67PerHuman(LPCHARACTER pkAttacker, int iValue)
{
	if (!IsPlayer(pkAttacker) || iValue <= 0)
		return iValue;
	const int iPer = pkAttacker->GetPoint(POINT_ATTBONUS_PER_HUMAN);
	return iPer > 0 ? iValue + iValue * iPer / 100 : iValue;
}

// The bots' bonus scoring: a line of a skill of another class or way is a line still (1); their own skill's lines
// are worth what they change in a grinder's fight - the armour's damage of a skill it casts all the time most, the
// HP back and the stun of a hitting skill next, a cooldown cut by its chance, the buffs by their seconds.
int Bonus67SkillLineScore(LPCHARACTER ch, unsigned int dwPoint, int iValue)
{
	const TB67cLine* pLine = B67cFindPoint((int) dwPoint);
	if (!pLine)
		return -1;
	if (iValue <= 0)
		return iValue;
	if (pLine->bKind == B67C_RANK)
	{
		// only a character of a low rank gains (a bot's rank is kept as a player's)
		const int iAlign = ch ? ch->GetAlignment() / 10 : 0;
		const int iRankPct = iAlign >= 0 ? 0 : iAlign > -4000 ? 1 : iAlign > -8000 ? 2 : iAlign > -12000 ? 3 : 5;
		return iRankPct > 0 ? iValue * iRankPct * 12 : 1;
	}
	if (pLine->bKind == B67C_PER)
		return iValue * (pLine->wPoint == POINT_ATTBONUS_PER_HUMAN ? 2 : 3);
	if (!ch || B67cSkillJob(pLine->bSkill) != (int) ch->GetJob() || B67cSkillGroup(pLine->bSkill) != (int) ch->GetSkillGroup())
		return 1;
	switch (pLine->bKind)
	{
		case B67C_SKDMG:	return iValue * 10;
		case B67C_ABSORB:	return iValue * 6;
		case B67C_STUN:		return iValue * 5;
		case B67C_CD20:		return iValue * 5;
		case B67C_CD10:		return iValue * 3;
		case B67C_ATT:		return iValue * 4;
		case B67C_DEF:		return iValue * 3;
		case B67C_CAST:		return iValue * 2;
		case B67C_DUR:		return iValue * 2;
		case B67C_KNOCK:	return iValue * 2;
	}
	return 1;
}
