// MT2009_PLUS_BONUS67_V1 - playerbot_bonus67.h, server-patches/bonusy67/README.md.
// New file outside the engine's own (the overlay's playerbot_* files build with every game core); the hooks are the
// edits of server-patches/bonusy67 (each declares what it calls).
#include "stdafx.h"
#include "playerbot_bonus67.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "sectree.h"
#include "questmanager.h"

#include <algorithm>
#include <map>
#include <vector>

static_assert(POINT_HIT_BUFF_ENCHANT_FIRE == 198 && POINT_GLOVE_BASE_ATTR_PCT == 251 && POINT_MAX_NUM == 252,
		"the 6th/7th bonus points 198-251 (item_attr ENUM of apply.sh MT2009_PLUS_BONUS67_V1, root/localeinfo_point.py)");
static_assert(POINT_MAX_NUM <= 256, "an item keeps its bonus type in one byte");
static_assert(SKILL_ILIPUNGU - SKILL_FINISH == POINT_GLOVE_COOLDOWN_ILIPUNGU - POINT_GLOVE_COOLDOWN_FINISH,
		"one glove cooldown line a champion skill, in the skills' order");
#ifdef MT2009_PLUS_ELEC_GLOVE_SE
// MT2009_PLUS_ELEC_GLOVE_V1: the lightning's hit effect (server-patches/elecglove) - the exe's SE_ELEC_ATTACK_HIT is 54
static_assert(SE_ELEC_ATTACK_HIT == 54, "SE_ELEC_ATTACK_HIT as the exe's (client-patches/exe/Server/common/length.h)");
#endif

bool Mt2009GloveType(DWORD dwVnum, BYTE& bWillType); // MT2009_PLUS_GLOVES_V1: playerbot_yohara_gear.cpp

namespace
{
	enum
	{
		ELEMENT_COUNT = 6,
		HIT_BUFF_COUNT = 12,				// HIT_BUFF_ENCHANT_* 198-203, HIT_BUFF_RESIST_* 204-209
		GLOVE_FALL_COOLDOWN_MS = 60000,		// the wiki: "czas regeneracji 60 sek."
		GLOVE_LIGHTNING_COOLDOWN_MS = 15000,	// the wiki: "czas regeneracji 15 sek."
		GLOVE_LIGHTNING_TARGETS = 8,
		SKILL_COOLDOWN_CUT_MS = 5000,		// the wiki: "skraca kolejny czas regeneracji ... o 5 sekund"
		HEADER_GC_SKILL_COOLTIME_END_B67 = 73,	// the exe's HEADER_GC_SKILL_COOLTIME_END (no GC header 73 on the server)
	};

	// The element order of the hit buffs (Owsap's APPLY_HIT_BUFF_*: fire, ice, lightning, wind, dark, earth) and the
	// points each one adds to while it lasts.
	const BYTE s_abHitBuffEnchant[ELEMENT_COUNT] = { POINT_ENCHANT_FIRE, POINT_ENCHANT_ICE, POINT_ENCHANT_ELECT,
			POINT_ENCHANT_WIND, POINT_ENCHANT_DARK, POINT_ENCHANT_EARTH };
	const BYTE s_abHitBuffResist[ELEMENT_COUNT] = { POINT_RESIST_FIRE, POINT_RESIST_ICE, POINT_RESIST_ELEC,
			POINT_RESIST_WIND, POINT_RESIST_DARK, POINT_RESIST_EARTH };

	// A bonus and its "+x% of the total" line.
	struct TPer
	{
		BYTE bPoint;
		BYTE bPer;
	};
	const TPer s_aPer[] = {
		{ POINT_ATTBONUS_MONSTER, POINT_ATTBONUS_PER_MONSTER }, { POINT_ATTBONUS_STONE, POINT_ATTBONUS_PER_STONE },
		{ POINT_ATTBONUS_MILGYO, POINT_ATTBONUS_PER_MILGYO }, { POINT_ATTBONUS_ORC, POINT_ATTBONUS_PER_ORC },
		{ POINT_ATTBONUS_DEVIL, POINT_ATTBONUS_PER_DEVIL }, { POINT_ATTBONUS_INSECT, POINT_ATTBONUS_PER_INSECT },
		{ POINT_ATTBONUS_ANIMAL, POINT_ATTBONUS_PER_ANIMAL },
		{ POINT_ENCHANT_ELECT, POINT_ENCHANT_PER_ELECT }, { POINT_ENCHANT_FIRE, POINT_ENCHANT_PER_FIRE },
		{ POINT_ENCHANT_ICE, POINT_ENCHANT_PER_ICE }, { POINT_ENCHANT_WIND, POINT_ENCHANT_PER_WIND },
		{ POINT_ENCHANT_EARTH, POINT_ENCHANT_PER_EARTH }, { POINT_ENCHANT_DARK, POINT_ENCHANT_PER_DARK },
		{ POINT_RESIST_HUMAN, POINT_RESIST_PER_HUMAN }, { POINT_RESIST_MAGIC, POINT_RESIST_PER_MAGIC },
		{ POINT_RESIST_ELEC, POINT_RESIST_PER_ELEC }, { POINT_RESIST_FIRE, POINT_RESIST_PER_FIRE },
		{ POINT_RESIST_ICE, POINT_RESIST_PER_ICE }, { POINT_RESIST_WIND, POINT_RESIST_PER_WIND },
		{ POINT_RESIST_EARTH, POINT_RESIST_PER_EARTH }, { POINT_RESIST_DARK, POINT_RESIST_PER_DARK },
	};

	// What a character's lines started, by VID (a VID is never given twice): the hit buffs and the gloves' times.
	struct TState
	{
		DWORD adwBuffUntil[HIT_BUFF_COUNT];
		DWORD adwBuffReady[HIT_BUFF_COUNT];
		DWORD dwFallUntil;
		DWORD dwFallReady;
		DWORD dwLightningReady;
		DWORD dwLast;
		TState() : dwFallUntil(0), dwFallReady(0), dwLightningReady(0), dwLast(0)
		{
			for (int i = 0; i < HIT_BUFF_COUNT; ++i)
				adwBuffUntil[i] = adwBuffReady[i] = 0;
		}
	};
	std::map<DWORD, TState> s_mapState;

	int EventFlag(const char* c_pszFlag, int iDefault, int iMax)
	{
		const int iFlag = quest::CQuestManager::instance().GetEventFlag(c_pszFlag);
		return iFlag > 0 ? MIN(iFlag, iMax) : iDefault;
	}

	bool Reached(DWORD dwNow, DWORD dwAt)
	{
		return (int) (dwNow - dwAt) >= 0;
	}

	const TState* FindState(const CHARACTER* ch)
	{
		std::map<DWORD, TState>::const_iterator it = s_mapState.find((DWORD) ch->GetVID());
		return it == s_mapState.end() ? NULL : &it->second;
	}

	TState& GetState(const CHARACTER* ch, DWORD dwNow)
	{
		if (s_mapState.size() > 4096)
		{
			// the characters gone long ago (their times are all over)
			for (std::map<DWORD, TState>::iterator it = s_mapState.begin(); it != s_mapState.end();)
			{
				if (dwNow - it->second.dwLast > 120000)
					s_mapState.erase(it++);
				else
					++it;
			}
		}
		TState& st = s_mapState[(DWORD) ch->GetVID()];
		st.dwLast = dwNow;
		return st;
	}

	// The hit buff a point has now (an element power / resistance) - 0 when none is on.
	int HitBuff(const CHARACTER* ch, BYTE bPoint)
	{
		const TState* st = FindState(ch);
		if (!st)
			return 0;
		const DWORD dwNow = get_dword_time();
		for (int i = 0; i < ELEMENT_COUNT; ++i)
		{
			if (s_abHitBuffEnchant[i] == bPoint && st->adwBuffUntil[i] && !Reached(dwNow, st->adwBuffUntil[i]))
				return EventFlag("b67_hitbuff_value", 10, 100);
			if (s_abHitBuffResist[i] == bPoint && st->adwBuffUntil[ELEMENT_COUNT + i] &&
					!Reached(dwNow, st->adwBuffUntil[ELEMENT_COUNT + i]))
				return EventFlag("b67_hitbuff_value", 10, 100);
		}
		return 0;
	}

	// A blow dealt (bResist false: HIT_BUFF_ENCHANT_*) or taken (HIT_BUFF_RESIST_*): each line the character has
	// starts its buff for its seconds, unless it started less than b67_hitbuff_cooldown seconds ago.
	void StartHitBuffs(LPCHARACTER ch, bool bResist)
	{
		const BYTE bFirst = bResist ? POINT_HIT_BUFF_RESIST_FIRE : POINT_HIT_BUFF_ENCHANT_FIRE;
		bool bAny = false;
		for (int i = 0; i < ELEMENT_COUNT && !bAny; ++i)
			bAny = ch->GetPoint(bFirst + i) > 0;
		if (!bAny)
			return;
		const DWORD dwNow = get_dword_time();
		TState& st = GetState(ch, dwNow);
		const int iCooldownMs = EventFlag("b67_hitbuff_cooldown", 15, 3600) * 1000;
		for (int i = 0; i < ELEMENT_COUNT; ++i)
		{
			const int iSec = MIN((int) ch->GetPoint(bFirst + i), 60);
			const int k = (bResist ? ELEMENT_COUNT : 0) + i;
			if (iSec <= 0 || (st.adwBuffReady[k] && !Reached(dwNow, st.adwBuffReady[k])))
				continue;
			st.adwBuffUntil[k] = dwNow + iSec * 1000;
			st.adwBuffReady[k] = dwNow + MAX(iCooldownMs, iSec * 1000);
		}
	}

	bool IsPlayer(const CHARACTER* ch)
	{
		return ch && !ch->IsNPC();
	}

	// "Boss or more" of the official lines: a monster of the boss rank and up; Metin stones have their own lines.
	bool IsBoss(const CHARACTER* ch)
	{
		return ch && ch->IsMonster() && !ch->IsStone() && ch->GetMobRank() >= MOB_RANK_BOSS;
	}

	struct FCollectMonsters
	{
		LPCHARACTER m_pkFrom;
		LPCHARACTER m_pkSkip;
		int m_iRange;
		std::vector<LPCHARACTER> m_vec;

		FCollectMonsters(LPCHARACTER pkFrom, LPCHARACTER pkSkip, int iRange) : m_pkFrom(pkFrom), m_pkSkip(pkSkip), m_iRange(iRange) {}

		void operator()(LPENTITY ent)
		{
			if (!ent->IsType(ENTITY_CHARACTER) || m_vec.size() >= GLOVE_LIGHTNING_TARGETS)
				return;
			LPCHARACTER tch = (LPCHARACTER) ent;
			if (tch == m_pkSkip || tch == m_pkFrom || !tch->IsMonster() || tch->IsDead() || tch->IsStone())
				return;
			if (DISTANCE_APPROX(tch->GetX() - m_pkFrom->GetX(), tch->GetY() - m_pkFrom->GetY()) > m_iRange)
				return;
			m_vec.push_back(tch);
		}
	};

	// The gloves' lightning: a normal hit of a character with the line strikes the monsters around it (but the one it
	// hit) for the same damage, once every 15 seconds. The wiki: no chance (the line has no value), the auto attack's
	// damage, 15 s; up to 8 monsters within b67_lightning_range (6 m, at most 30 m). Each one struck gets the chain
	// lightning's fly and (MT2009_PLUS_ELEC_GLOVE_V1) the global hit effect SE_ELEC_ATTACK_HIT
	// (d:/ymir work/effect/hit/blow_electric/6th7th_attributes_blow.mse, the exe's EFFECT_ELEC_ATTACK_HIT).
	void GloveLightning(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, int iDam)
	{
		static bool s_bInside = false;
		if (s_bInside || iDam <= 0 || pkAttacker->GetPoint(POINT_GLOVE_LIGHTNING) <= 0 || !pkAttacker->GetSectree())
			return;
		const DWORD dwNow = get_dword_time();
		TState& st = GetState(pkAttacker, dwNow);
		if (st.dwLightningReady && !Reached(dwNow, st.dwLightningReady))
			return;
		st.dwLightningReady = dwNow + GLOVE_LIGHTNING_COOLDOWN_MS;

		FCollectMonsters f(pkAttacker, pkVictim, EventFlag("b67_lightning_range", 600, 3000));
		pkAttacker->GetSectree()->ForEachAround(f);
		s_bInside = true;
		for (size_t i = 0; i < f.m_vec.size(); ++i)
		{
			LPCHARACTER tch = f.m_vec[i];
			if (tch->IsDead())
				continue;
			pkAttacker->CreateFly(FLY_CHAIN_LIGHTNING, tch);
#ifdef MT2009_PLUS_ELEC_GLOVE_SE
			tch->EffectPacket(SE_ELEC_ATTACK_HIT);
#endif
			tch->Damage(pkAttacker, iDam, DAMAGE_TYPE_SPECIAL);
		}
		s_bInside = false;
	}

	// The gloves' fall resistance: a blow taken in combat starts it with the line's chance, then not again for 60 s.
	void GloveFallResist(LPCHARACTER pkVictim)
	{
		const int iPct = MIN((int) pkVictim->GetPoint(POINT_GLOVE_FALL_RESIST), 100);
		if (iPct <= 0)
			return;
		const DWORD dwNow = get_dword_time();
		TState& st = GetState(pkVictim, dwNow);
		if (st.dwFallReady && !Reached(dwNow, st.dwFallReady))
			return;
		if (number(1, 100) > iPct)
			return;
		st.dwFallUntil = dwNow + EventFlag("b67_fall_seconds", 10, 60) * 1000;
		st.dwFallReady = dwNow + GLOVE_FALL_COOLDOWN_MS;
	}

	// An item's own rare line of this type (0 when it has none).
	int ItemRareValue(LPITEM item, BYTE bType)
	{
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
			if (item->GetAttributeType(i) == bType)
				return item->GetAttributeValue(i);
		return 0;
	}

	// The level of a new 6th/7th line: the panel's odds (m2_rare_lv1..5, as CItem::AddRareAttribute) or a table.
	int RollRareLevel(const int* aiPct)
	{
		static const int s_aiDefault[5] = { 35, 30, 20, 10, 5 };
		int aiOdds[5];
		int iTotal = 0;
		for (int i = 0; i < 5; ++i)
		{
			if (aiPct)
				aiOdds[i] = MAX(0, aiPct[i]);
			else
			{
				char szFlag[16];
				snprintf(szFlag, sizeof(szFlag), "m2_rare_lv%d", i + 1);
				aiOdds[i] = MAX(0, quest::CQuestManager::instance().GetEventFlag(szFlag));
			}
			iTotal += aiOdds[i];
		}
		if (iTotal <= 0)
		{
			for (int i = 0; i < 5; ++i)
				aiOdds[i] = s_aiDefault[i];
			iTotal = 100;
		}
		int iRoll = number(1, iTotal);
		int iLevel = 1;
		for (; iLevel < 5 && iRoll > aiOdds[iLevel - 1]; ++iLevel)
			iRoll -= aiOdds[iLevel - 1];
		return iLevel;
	}
}

int Bonus67Total(const CHARACTER* ch, unsigned char bPoint)
{
	if (!ch || bPoint >= POINT_MAX_NUM)
		return 0;
	int iValue = ch->GetPoint(bPoint);
	if (IsPlayer(ch))
	{
		iValue += HitBuff(ch, bPoint);
		for (size_t i = 0; i < sizeof(s_aPer) / sizeof(s_aPer[0]); ++i)
		{
			if (s_aPer[i].bPoint != bPoint)
				continue;
			const int iPer = ch->GetPoint(s_aPer[i].bPer);
			if (iPer > 0 && iValue > 0)
				iValue += iValue * iPer / 100;
			break;
		}
	}
	return iValue;
}

int Bonus67AttBonus(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, int iPointValue)
{
	if (!IsPlayer(pkAttacker) || !pkVictim || !pkVictim->IsNPC())
		return iPointValue;
	int iExtra = 0;
	// the lines whose bonus CalcAttBonus has just counted: the same conditions
	struct
	{
		BYTE bPoint;
		bool bOn;
	} aLines[] = {
		{ POINT_ATTBONUS_MONSTER, true },
		{ POINT_ATTBONUS_STONE, pkVictim->GetMobRank() >= MOB_RANK_BOSS && pkVictim->IsStone() },
		{ POINT_ATTBONUS_ANIMAL, pkVictim->IsRaceFlag(RACE_FLAG_ANIMAL) },
		{ POINT_ATTBONUS_DEVIL, pkVictim->IsRaceFlag(RACE_FLAG_DEVIL) },
		{ POINT_ATTBONUS_ORC, pkVictim->IsRaceFlag(RACE_FLAG_ORC) },
		{ POINT_ATTBONUS_MILGYO, pkVictim->IsRaceFlag(RACE_FLAG_MILGYO) },
		{ POINT_ATTBONUS_INSECT, pkVictim->IsRaceFlag(RACE_FLAG_INSECT) },
	};
	for (size_t i = 0; i < sizeof(aLines) / sizeof(aLines[0]); ++i)
	{
		if (!aLines[i].bOn)
			continue;
		const int iBase = pkAttacker->GetPoint(aLines[i].bPoint);
		if (iBase > 0)
			iExtra += Bonus67Total(pkAttacker, aLines[i].bPoint) - iBase;
	}
	// "Silny przeciwko potworom Zodiaku (+x% lacznej wartosci)": this engine has no separate bonus against the
	// Zodiac's monsters, so against one (RACE_FLAG_CZ) the line raises the whole race bonus counted above.
	const int iPerCz = pkAttacker->GetPoint(POINT_ATTBONUS_PER_CZ);
	if (iPerCz > 0 && iPointValue > 0 && pkVictim->IsRaceFlag(RACE_FLAG_CZ))
		iExtra += iPointValue * iPerCz / 100;
	return iPointValue + iExtra;
}

int Bonus67Damage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iType, int iDam)
{
	if (!pkVictim || !pkAttacker || iDam <= 0)
		return iDam;
	const bool bNormal = iType == DAMAGE_TYPE_NORMAL || iType == DAMAGE_TYPE_NORMAL_RANGE;
	const bool bSkill = iType == DAMAGE_TYPE_MELEE || iType == DAMAGE_TYPE_RANGE || iType == DAMAGE_TYPE_FIRE ||
			iType == DAMAGE_TYPE_ICE || iType == DAMAGE_TYPE_ELEC || iType == DAMAGE_TYPE_MAGIC;

	// the boss lines (each its own multiplier, as the engine's normal hit / skill bonuses)
	if (IsPlayer(pkAttacker) && IsBoss(pkVictim))
	{
		const int iPct = pkAttacker->GetPoint(bNormal ? POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE :
				bSkill ? POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE : POINT_NONE);
		if ((bNormal || bSkill) && iPct > 0)
			iDam = iDam * (100 + iPct) / 100;
	}
	if (IsPlayer(pkVictim) && IsBoss(pkAttacker))
	{
		const int iPct = pkVictim->GetPoint(bNormal ? POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE :
				bSkill ? POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE : POINT_NONE);
		if ((bNormal || bSkill) && iPct > 0)
			iDam = MAX(1, iDam * (100 - MIN(99, iPct)) / 100);
	}

	if (bNormal || bSkill)
	{
		if (IsPlayer(pkAttacker))
		{
			StartHitBuffs(pkAttacker, false);
			if (bNormal && pkVictim->IsNPC())
				GloveLightning(pkAttacker, pkVictim, iDam);
		}
		if (IsPlayer(pkVictim))
		{
			StartHitBuffs(pkVictim, true);
			GloveFallResist(pkVictim);
		}
	}
	return iDam;
}

bool Bonus67FallResist(const CHARACTER* ch)
{
	if (!IsPlayer(ch))
		return false;
	const TState* st = FindState(ch);
	return st && st->dwFallUntil && !Reached(get_dword_time(), st->dwFallUntil);
}

#pragma pack(push, 1)
struct TPacketGCSkillCoolTimeEndB67
{
	BYTE header;
	BYTE bSkill;
};
#pragma pack(pop)

EVENTINFO(bonus67_cooltime_info)
{
	DWORD dwVID;
	BYTE bSkill;
	bonus67_cooltime_info() : dwVID(0), bSkill(0) {}
};

EVENTFUNC(bonus67_cooltime_event)
{
	bonus67_cooltime_info* info = dynamic_cast<bonus67_cooltime_info*>(event->info);
	if (!info)
		return 0;
	LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(info->dwVID);
	if (ch && ch->GetDesc())
	{
		TPacketGCSkillCoolTimeEndB67 p;
		p.header = HEADER_GC_SKILL_COOLTIME_END_B67;
		p.bSkill = info->bSkill;
		ch->GetDesc()->Packet(&p, sizeof(p));
	}
	return 0;
}

unsigned int Bonus67SkillCooldown(LPCHARACTER ch, unsigned int dwVnum, unsigned int dwNextUsable)
{
	if (!IsPlayer(ch) || dwVnum < SKILL_FINISH || dwVnum > SKILL_ILIPUNGU || !dwNextUsable)
		return dwNextUsable;
	const int iPct = MIN((int) ch->GetPoint(POINT_GLOVE_COOLDOWN_FINISH + (dwVnum - SKILL_FINISH)), 100);
	if (iPct <= 0 || number(1, 100) > iPct)
		return dwNextUsable;
	const DWORD dwNow = get_dword_time();
	if (!Reached(dwNextUsable, dwNow + SKILL_COOLDOWN_CUT_MS + 1000))
		return dwNextUsable;	// less than 6 s left: nothing to cut
	const DWORD dwNew = dwNextUsable - SKILL_COOLDOWN_CUT_MS;
	if (ch->GetDesc())
	{
		// the client counts its own cooldown from the skill's table: it is ended when the server's is
		bonus67_cooltime_info* info = AllocEventInfo<bonus67_cooltime_info>();
		info->dwVID = (DWORD) ch->GetVID();
		info->bSkill = (BYTE) dwVnum;
		const long lPasses = MAX(1L, (long) PASSES_PER_SEC(1) * (long) (dwNew - dwNow + 200) / 1000L);
		event_create(bonus67_cooltime_event, info, lPasses);
		ch->ChatPacket(CHAT_TYPE_INFO, "Rekawice: kolejny czas odnowienia tej umiejetnosci krotszy o 5 sek.");
	}
	return dwNew;
}

int Bonus67AttrValue(LPITEM item, int iSlot, unsigned char bType, int iValue)
{
	if (!item || !iValue)
		return iValue;
	// MT2009_PLUS_GLOVE_BASE_V1: the glove's Will is no bonus slot any more - its "+x%" is Mt2009GloveBaseWill's
	int iPct = 0;
	if (iSlot >= 0 && iSlot < 5)
		iPct = ItemRareValue(item, (BYTE) (POINT_FIRST_ATTRIBUTE_BONUS + iSlot));
	if (iPct <= 0)
		return iValue;
	return iValue + iValue * iPct / 100;
}

// MT2009_PLUS_GLOVE_BASE_V1: the glove's 6th and 7th bonus are the 6/7 system's (the owner, 20 Oct) - its Will is its
// base attribute (playerbot_yohara_gear.cpp). An addition (71051, Seon-Hae) fills the first free of the two slots, a
// change (71052) rolls every line the glove has again (as the engine's ChangeRareAttribute), never one it had nor two
// alike. The pool's glove column (item_attr_rare.glove) and the level odds of the engine's own path.
namespace
{
	bool GloveRareRoll(LPITEM item, int iSlot, int iSet, int iMode, const int* aiPct, const std::vector<BYTE>& vecSkip)
	{
		std::vector<int> vecAvail;
		unsigned int uTotal = 0;
		for (TItemAttrMap::const_iterator it = g_map_itemRare.begin(); it != g_map_itemRare.end(); ++it)
		{
			const TItemAttrTable& r = it->second;
			if (!r.dwApplyIndex || r.dwApplyIndex >= POINT_MAX_NUM || !r.bMaxLevelBySet[iSet] || !r.dwProb)
				continue;
			if (std::find(vecSkip.begin(), vecSkip.end(), (BYTE) r.dwApplyIndex) != vecSkip.end())
				continue;
			vecAvail.push_back(it->first);
			uTotal += r.dwProb;
		}
		if (vecAvail.empty() || !uTotal)
			return false;
		unsigned int uRoll = number(1, uTotal);
		int iApply = vecAvail.back();
		for (size_t i = 0; i < vecAvail.size(); ++i)
		{
			const unsigned int uProb = g_map_itemRare[vecAvail[i]].dwProb;
			if (uRoll <= uProb)
			{
				iApply = vecAvail[i];
				break;
			}
			uRoll -= uProb;
		}
		const TItemAttrTable& r = g_map_itemRare[iApply];
		static const int s_aiAdd2[5] = { 40, 50, 10, 0, 0 };	// CItem::AddRareAttribute2's own table
		int iLevel = RollRareLevel(iMode == 0 || iMode == 2 ? NULL : (aiPct ? aiPct : s_aiAdd2));
		iLevel = MIN(iLevel, (int) r.bMaxLevelBySet[iSet]);
		const long lValue = r.lValues[MINMAX(1, iLevel, 5) - 1];
		if (!lValue)
			return false;
		item->SetForceAttribute(iSlot, (BYTE) iApply, (short) lValue);
		sys_log(0, "BONUS67: glove %u (id %u) bonus %d: line %d = %ld (level %d)", item->GetVnum(), item->GetID(),
				iSlot + 1, iApply, lValue, iLevel);
		return true;
	}
}

int Bonus67GloveRare(LPITEM item, int iMode, const int* aiPct)
{
	BYTE bWillType;
	if (!item || !Mt2009GloveType(item->GetVnum(), bWillType))
		return -1;
	const int iSet = item->GetAttributeSetIndex();
	if (iSet < 0)
		return 0;
	// never the glove's own flat Will (its base attribute) - the pool has no such line, kept as a guard
	std::vector<BYTE> vecSkip(1, bWillType);
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
		if (item->GetAttributeType(i))
			vecSkip.push_back(item->GetAttributeType(i));

	const bool bChange = iMode == 2 || iMode == 3;
	if (!bChange)
	{
		for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
			if (!item->GetAttributeType(i))
				return GloveRareRoll(item, i, iSet, iMode, aiPct, vecSkip) ? 1 : 0;
		return 0;	// both slots taken
	}

	// a change: the lines there now are rolled again in their slots (the old ones and the new ones never twice)
	bool bAny = false, bDone = false;
	for (int i = ITEM_ATTRIBUTE_RARE_START; i < ITEM_ATTRIBUTE_RARE_END; ++i)
	{
		if (!item->GetAttributeType(i))
			continue;
		bAny = true;
		const size_t uBefore = vecSkip.size();
		if (GloveRareRoll(item, i, iSet, iMode, aiPct, vecSkip))
		{
			bDone = true;
			if (vecSkip.size() == uBefore)
				vecSkip.push_back(item->GetAttributeType(i));
		}
	}
	return bAny && bDone ? 1 : 0;
}
