// MT2009_PLUS_RIPOSTY_V1: Riposty i Dopalacze (playerbot_riposty.h, server-patches/riposty/README.md). The engine's
// hooks are server-patches/riposty (edits.json) and call the free functions below (declared again at each hook, as the
// other patches do); the quest riposty (Podreczniki, Kamien Duchowy+, Zwoj Zmiany Treningu) uses the pc.* functions
// at the end (registered with the Champion's, playerbot_champion.cpp).
#include "stdafx.h"
#include "playerbot_riposty.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "skill.h"
#include "log.h"
#include "questmanager.h"
#include "questlua.h"
#include "char_manager.h"
#include "affect.h"
#include "item.h"
#include "item_manager.h"

#include <cstdio>
#include <map>
#include <string>

namespace riposty
{
	// GF's skill power of a level (SKILL_POWER_BY_LEVEL of its CONFIG; ours can be another per class): the wiki's
	// values are 24*k / 16*k on this table - 1: 1.2% / 0.8%, M1: 12% / 8%, G1: 19.68% / 13.12%, P: 30% / 20%.
	static const int s_aiPower[SKILL_MAX_LEVEL + 1] =
	{
		0,
		5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40,
		50, 52, 54, 56, 58, 60, 63, 66, 69, 72,
		82, 85, 88, 91, 94, 98, 102, 106, 110, 115,
		125,
	};

	// the attack skill each riposte / boost is about, in the vnums' order (221+i, 236+i)
	static const unsigned int s_adwSkill[8] =
	{
		SKILL_SWORD_SPIN,		// Wir Miecza (Wojownik Body)
		SKILL_AMBUSH,			// Zasadzka (Ninja Dagger)
		SKILL_FINGER_STRIKE,	// Uderzenie Palcem (Sura WP)
		SKILL_SHOOTING_DRAGON,	// Strzelajacy Smok (Szaman Smok)
		SKILL_SPIRIT_STRIKE,	// Duchowe Uderzenie (Wojownik Mental)
		SKILL_FIRE_ARROW,		// Ognista Strzala (Ninja Archer)
		SKILL_DARK_STRIKE,		// Mroczne Uderzenie (Sura BM)
		SKILL_SUMMON_LIGHTNING,	// Przywolanie Blyskawicy (Szaman Healer)
	};

	bool IsRiposte(unsigned int dwVnum)
	{
		return dwVnum >= RIPOSTE_FIRST && dwVnum <= RIPOSTE_LAST;
	}

	bool IsBoost(unsigned int dwVnum)
	{
		return dwVnum >= BOOST_FIRST && dwVnum <= BOOST_LAST;
	}

	bool IsPassive(unsigned int dwVnum)
	{
		return IsRiposte(dwVnum) || IsBoost(dwVnum);
	}

	unsigned int BoostFor(unsigned char bJob, unsigned char bGroup)
	{
		if (bGroup != 1 && bGroup != 2)
			return 0;
		switch (bJob)
		{
			case JOB_WARRIOR:	return bGroup == 1 ? 236 : 240;	// Wir Miecza / Duchowe Uderzenie
			case JOB_ASSASSIN:	return bGroup == 1 ? 237 : 241;	// Zasadzka / Ognista Strzala
			case JOB_SURA:		return bGroup == 1 ? 238 : 242;	// Uderzenie Palcem / Mroczne Uderzenie
			case JOB_SHAMAN:	return bGroup == 1 ? 239 : 243;	// Strzelajacy Smok / Przywolanie Blyskawicy
		}
		return 0;
	}

	static unsigned int Known(const CHARACTER* ch, unsigned int dwFirst, unsigned int dwLast)
	{
		if (!ch || !ch->IsPC())
			return 0;
		for (unsigned int v = dwFirst; v <= dwLast; ++v)
			if (ch->GetSkillLevel(v) > 0)
				return v;
		return 0;
	}

	unsigned int RiposteOf(const CHARACTER* ch)
	{
		return Known(ch, RIPOSTE_FIRST, RIPOSTE_LAST);
	}

	unsigned int BoostOf(const CHARACTER* ch)
	{
		return Known(ch, BOOST_FIRST, BOOST_LAST);
	}

	double Percent(unsigned int dwVnum, int iLevel)
	{
		if (iLevel <= 0)
			return 0.0;
		const double k = s_aiPower[MINMAX(0, iLevel, (int) SKILL_MAX_LEVEL)] / 100.0;
		return (IsBoost(dwVnum) ? 16.0 : 24.0) * k;
	}

	// The skill points a riposte / boost took (SkillLevelUp by a point): a skill reset keeps the skill, so these stay
	// spent; Zwoj Zmiany Treningu gives them back.
	static std::string PointFlag(unsigned int dwVnum)
	{
		char sz[48];
		snprintf(sz, sizeof(sz), "riposty.pts_%u", dwVnum);
		return sz;
	}

	int Learn(CHARACTER* ch, unsigned int dwVnum)
	{
		if (!ch || !ch->IsPC() || !IsPassive(dwVnum))
			return 5;
		if (!ch->GetSkillGroup())
			return 1;
		if (ch->GetLevel() < 5)
			return 2;
		if (IsRiposte(dwVnum))
		{
			if (RiposteOf(ch))
				return 3;
		}
		else
		{
			if (BoostFor(ch->GetJob(), ch->GetSkillGroup()) != dwVnum)
				return 5;
			if (BoostOf(ch))
				return 3;
			const unsigned int r = RiposteOf(ch);
			if (!r || ch->GetSkillLevel(r) < SKILL_MAX_LEVEL)
				return 4;
		}
		ch->SetSkillLevel(dwVnum, 1);
		ch->SetQuestFlag(PointFlag(dwVnum), 0);
		ch->Save();
		ch->ComputePoints();
		ch->SkillLevelPacket();
		LogManager::instance().CharLog(ch, dwVnum, "PASSIVE_LEARN", "");
		return 0;
	}

	int ResetAll(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC())
			return 0;
		int iCount = 0, iPoints = 0;
		for (unsigned int v = RIPOSTE_FIRST; v <= BOOST_LAST; ++v)
		{
			if (!IsPassive(v))
				continue;
			const int iSpent = MAX(0, ch->GetQuestFlag(PointFlag(v)));
			if (iSpent)
				ch->SetQuestFlag(PointFlag(v), 0);
			if (ch->GetSkillLevel(v) <= 0)
				continue;
			iPoints += iSpent;
			++iCount;
			char szFlag[64];
			snprintf(szFlag, sizeof(szFlag), "traning_master_skill.%u.read_count", v);
			ch->SetQuestFlag(szFlag, 0);
			ch->SetSkillLevel(v, 0);
			LogManager::instance().CharLog(ch, v, "PASSIVE_RESET", "");
		}
		if (iPoints)
			ch->PointChange(POINT_SKILL, iPoints);
		if (iCount)
		{
			ch->Save();
			ch->ComputePoints();
			ch->SkillLevelPacket();
		}
		return iCount;
	}
}

using namespace riposty;

// ---- the engine's hooks (server-patches/riposty) ------------------------------------------------------------------

// IsLearnableSkill: -1 not a riposte/boost; a known one (level 1+) of a character with a specialisation - and a boost
// only the class's own - can grow (points, books, Kamien Duchowy+); level 0 only with its Podrecznik (riposty::Learn).
int RipostyLearnable(const CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsPassive(dwVnum))
		return -1;
	if (!ch || !ch->IsPC() || !ch->GetSkillGroup())
		return 0;
	const int iLevel = ch->GetSkillLevel(dwVnum);
	if (iLevel <= 0 || iLevel >= SKILL_MAX_LEVEL)
		return 0;
	if (IsBoost(dwVnum) && BoostFor(ch->GetJob(), ch->GetSkillGroup()) != dwVnum)
		return 0;
	return 1;
}

// LearnSkillByBook, before everything: why a riposte's / boost's book cannot be read (in Polish); 1 go on.
int RipostyBookCheck(CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsPassive(dwVnum) || !ch)
		return 1;
	const int iLevel = ch->GetSkillLevel(dwVnum);
	if (IsRiposte(dwVnum))
	{
		const unsigned int known = RiposteOf(ch);
		if (!known)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw wybierz riposte - uzyj Podrecznika: Riposta.");
			return 0;
		}
		if (known != dwVnum)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Znasz juz inna riposte - mozna miec tylko jedna. Ta ksiega jej nie rozwija.");
			return 0;
		}
	}
	else
	{
		if (BoostFor(ch->GetJob(), ch->GetSkillGroup()) != dwVnum)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten dopalacz nie jest dla twojej klasy i drogi umiejetnosci.");
			return 0;
		}
		if (iLevel <= 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw naucz sie dopalacza - uzyj Podrecznika: Dopalacz.");
			return 0;
		}
	}
	if (iLevel >= 30)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Od stopnia G1 do P riposte i dopalacz rozwija Kamien Duchowy+.");
		return 0;
	}
	return 1;
}

// SkillLevelUp by a point: remember it (a skill reset keeps the skill and leaves the point spent).
void RipostyPointSpent(CHARACTER* ch, unsigned int dwVnum)
{
	if (!ch || !IsPassive(dwVnum))
		return;
	const std::string flag = PointFlag(dwVnum);
	ch->SetQuestFlag(flag, MAX(0, ch->GetQuestFlag(flag)) + 1);
}

// ClearSkill: the points of the riposte and boost a reset keeps (subtracted from the points it gives back).
int RipostyKeptPoints(CHARACTER* ch)
{
	if (!ch || !ch->IsPC())
		return 0;
	int iSum = 0;
	for (unsigned int v = RIPOSTE_FIRST; v <= BOOST_LAST; ++v)
		if (IsPassive(v) && ch->GetSkillLevel(v) > 0)
			iSum += MAX(0, ch->GetQuestFlag(PointFlag(v)));
	return iSum;
}

// The damage of an attack skill (CSkill splash damage, before Damage): the attacker's boost of it adds, the victim's
// riposte against it takes away (Owsap's order: the boost first).
int RipostyDamage(CHARACTER* pkAttacker, CHARACTER* pkVictim, unsigned int dwSkill, int iDam)
{
	if (iDam <= 0)
		return iDam;
	int i = 0;
	for (; i < 8; ++i)
		if (s_adwSkill[i] == dwSkill)
			break;
	if (i >= 8)
		return iDam;
	double dDam = iDam;
	if (pkAttacker && pkAttacker->IsPC())
	{
		const int iLevel = pkAttacker->GetSkillLevel(BOOST_FIRST + i);
		if (iLevel > 0)
			dDam += dDam * Percent(BOOST_FIRST + i, iLevel) / 100.0;
	}
	if (pkVictim && pkVictim->IsPC())
	{
		const int iLevel = pkVictim->GetSkillLevel(RIPOSTE_FIRST + i);
		if (iLevel > 0)
			dDam -= dDam * Percent(RIPOSTE_FIRST + i, iLevel) / 100.0;
	}
	if (test_server)
		sys_log(0, "RIPOSTY: skill %u damage %d -> %d", dwSkill, iDam, (int) dDam);
	return MAX(0, (int) dDam);
}

// SetSkillGroup: a boost belongs to a specialisation - a known boost of the other one moves to this one's (its level,
// its points), so a change of the path keeps it.
void RipostyGroupChanged(CHARACTER* ch)
{
	if (!ch || !ch->IsPC())
		return;
	const unsigned int want = BoostFor(ch->GetJob(), ch->GetSkillGroup());
	const unsigned int have = BoostOf(ch);
	if (!want || !have || want == have || ch->GetSkillLevel(want) > 0)
		return;
	const int iLevel = ch->GetSkillLevel(have);
	const int iSpent = MAX(0, ch->GetQuestFlag(PointFlag(have)));
	ch->SetSkillLevel(have, 0);
	ch->SetQuestFlag(PointFlag(have), 0);
	ch->SetSkillLevel(want, iLevel);
	ch->SetQuestFlag(PointFlag(want), iSpent);
	ch->SkillLevelPacket();
	sys_log(0, "RIPOSTY: %s boost %u -> %u (level %d)", ch->GetName(), have, want, iLevel);
}

// MT2009_PLUS_RIPOSTY_FORGET_V1: Ksiega Zapomnienia (70037) with a riposte / boost in its socket (the pl-wiki: "W grze
// istnieja takze Ksiegi Zapomnienia dla Ripost / Dopalaczy"; its page: one skill point back, "Umiejetnosci na M i wyzszej
// nie mozna cofnac"). SkillLevelDown, before the engine's own rules: -1 not a riposte / boost; 0 refused (why, in
// Polish); 1 a level down and a point back. Only the points spent on it come back (riposty.pts_<vnum>) - the levels its
// Podrecznik (1) and its books gave stay; Zwoj Zmiany Treningu still removes it whole.
int RipostyLevelDown(CHARACTER* ch, unsigned int dwVnum)
{
	if (!IsPassive(dwVnum))
		return -1;
	if (!ch || !ch->IsPC())
		return 0;
	const int iLevel = ch->GetSkillLevel(dwVnum);
	if (iLevel <= 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie znasz tej umiejetnosci.");
		return 0;
	}
	if (ch->GetSkillMasterType(dwVnum) != SKILL_NORMAL)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Riposty i dopalacza od stopnia M1 nie mozna cofnac.");
		return 0;
	}
	const std::string flag = PointFlag(dwVnum);
	const int iSpent = MAX(0, ch->GetQuestFlag(flag));
	if (iLevel <= 1 || iSpent <= 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Na te umiejetnosc nie wydano punktow umiejetnosci - poziomu z Podrecznika i z ksiag nie mozna cofnac. Cala riposte i dopalacz usuwa Zwoj Zmiany Treningu.");
		return 0;
	}
	ch->SetQuestFlag(flag, iSpent - 1);
	ch->PointChange(POINT_SKILL, 1);
	ch->SetSkillLevel(dwVnum, iLevel - 1);
	ch->Save();
	ch->ComputePoints();
	ch->SkillLevelPacket();
	LogManager::instance().CharLog(ch, dwVnum, "PASSIVE_FORGET", "");
	sys_log(0, "RIPOSTY: %s forgets a level of %u (%d -> %d)", ch->GetName(), dwVnum, iLevel, iLevel - 1);
	return 1;
}

// ITEM_MANAGER::CreateItem of a Ksiega Zapomnienia (its socket drawn by GetRandomSkillVnum, about 47 class skills):
// each riposte and boost is one more skill of that draw - 16 in 63 books are theirs. The same sources as every
// Ksiega Zapomnienia (Metins from 15, bosses, chests - the wiki).
unsigned int RipostyForgetBookSkill(unsigned int dwSkill)
{
	const int CLASS_SKILLS = 47, PASSIVES = 16;
	if (number(1, CLASS_SKILLS + PASSIVES) > PASSIVES)
		return dwSkill;
	const int i = number(0, PASSIVES - 1);
	return i < 8 ? RIPOSTE_FIRST + i : BOOST_FIRST + (i - 8);
}

// ---- bots (MT2009_PLUS_RIPOSTY_V2) -------------------------------------------------------------------------------
// Report #8 / the owner, 8 November 2026 ("nauka riposty ma byc jak na globalu"): until now no bot had a riposte or a
// boost - nothing of the bots' read a Podrecznik, a riposte's book or Kamien Duchowy+, and a Podrecznik in a bot's bag
// went to the merchant. A bot learns them the wiki's way, as a player does, with the same engine functions:
//   - Podrecznik: Riposta (50515) in the bag, level 5+, a path, no riposte: the riposte against the attack skill of
//     the path met most among the OTHER kingdoms' characters online (a draw weighted by their number - PvP is between
//     kingdoms; nobody online: by the pid), riposty::Learn, the book used up;
//   - Podrecznik: Dopalacz (50514) and a riposte at P: its own class's and path's boost (BoostFor);
//   - the riposte's / boost's own books (50516-50523 / 50560-50567, level 1 to G1): read through the engine
//     (ITEM_SKILLBOOK -> LearnSkillByBook: the chance, its wait, Zwoj Egzorcyzmu), the 20 000 experience lent as the
//     bots' class books do (playerbot_manager.cpp UsePlayerBotBook);
//   - Kamien Duchowy+ (50525, G1 -> P): what the quest riposty does - the rank 1000 + 500 a grade over G1 (twice below
//     zero), a third to a half of it on a failure, the stone spent, 12 h to the next (its flag riposty.next_time, the
//     quest's own) - only while the full price leaves the rank at zero or above (the bots' rule for Kamien Duchowy);
//   - the class skill points left once every skill of the bot's build is at its top by points
//     (ManagePlayerBotSkills' last pass): the riposte, then the boost, to M1 (the engine's roll at 17-19).
// Never Zwoj Zmiany Treningu (71000): a bot keeps its choice (playerbot_itemshop.h IsPlayerBotIshop3ExcludedVnum keeps
// it out of the bots' ItemShop purchases). A player's companion (sidekick) is left to its owner.
namespace riposty
{
	static const char* const s_aszSkillName[8] =
	{
		"Wir Miecza", "Zasadzka", "Uderzenie Palcem", "Strzelajacy Smok", "Duchowe Uderzenie", "Ognista Strzala",
		"Mroczne Uderzenie", "Przywolanie Blyskawicy",
	};

	const char* Name(unsigned int dwVnum)
	{
		static char s_aszName[16][48];
		if (!IsPassive(dwVnum))
			return NULL;
		const int i = IsRiposte(dwVnum) ? (int) (dwVnum - RIPOSTE_FIRST) : 8 + (int) (dwVnum - BOOST_FIRST);
		if (!s_aszName[i][0])
			snprintf(s_aszName[i], sizeof(s_aszName[i]), "%s: %s", i < 8 ? "Riposta" : "Dopalacz", s_aszSkillName[i % 8]);
		return s_aszName[i];
	}

	unsigned int BotChoice(const CHARACTER* ch)
	{
		if (!ch)
			return 0;
		int aiCount[8] = { 0 };
		int iTotal = 0;
		CHARACTER_MANAGER::NAME_MAP& pcs = CHARACTER_MANAGER::instance().GetPCMap();
		for (CHARACTER_MANAGER::NAME_MAP::const_iterator it = pcs.begin(); it != pcs.end(); ++it)
		{
			const CHARACTER* other = it->second;
			if (!other || other == ch || other->GetEmpire() == ch->GetEmpire())
				continue;
			const unsigned int b = BoostFor(other->GetJob(), other->GetSkillGroup());
			if (!b)
				continue;
			++aiCount[b - BOOST_FIRST];
			++iTotal;
		}
		if (!iTotal)
			return RIPOSTE_FIRST + ch->GetPlayerID() % 8;
		int iRoll = number(1, iTotal);
		for (int i = 0; i < 8; ++i)
		{
			iRoll -= aiCount[i];
			if (iRoll <= 0)
				return RIPOSTE_FIRST + i;
		}
		return RIPOSTE_LAST;
	}

	// One item of a vnum the bot can use (not locked, not in a trade).
	static LPITEM BotItem(CHARACTER* ch, unsigned int dwVnum)
	{
		LPITEM item = ch->FindSpecifyItem(dwVnum);
		if (!item || item->isLocked() || item->IsExchanging())
			return NULL;
		return item;
	}

	static void UseUp(LPITEM item, const char* why)
	{
		if (item->GetCount() > 1)
			item->SetCount(item->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(item, why);
	}

	static bool BotLearn(CHARACTER* ch, unsigned int dwBook, unsigned int dwVnum)
	{
		LPITEM book = BotItem(ch, dwBook);
		if (!book || !dwVnum)
			return false;
		const int r = Learn(ch, dwVnum);
		if (r != 0)
			return false;
		UseUp(book, IsRiposte(dwVnum) ? "RIPOSTA_LEARN" : "DOPALACZ_LEARN");
		sys_log(0, "PLAYERBOT_AI: riposty learn pid=%u name=%s skill=%u (%s)", ch->GetPlayerID(), ch->GetName(), dwVnum,
				Name(dwVnum));
		return true;
	}

	// A book of this riposte / boost (ITEM_SKILLBOOK, its skill in value0) read through the engine.
	static bool BotReadBook(CHARACTER* ch, unsigned int dwVnum)
	{
		const int iLevel = ch->GetSkillLevel(dwVnum);
		if (iLevel <= 0 || iLevel >= 30)
			return false;
		if (get_global_time() < ch->GetSkillNextReadTime(dwVnum) && !ch->FindAffect(AFFECT_SKILL_NO_BOOK_DELAY))
			return false;
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->GetType() != ITEM_SKILLBOOK || item->isLocked() ||
					item->IsExchanging() || (unsigned int) item->GetValue(0) != dwVnum)
				continue;
			const DWORD dwExp = ch->GetExp();
			const bool lend = dwExp < 20000;
			if (lend)
				ch->SetExp(20000);
			const bool used = ch->UseItem(TItemPos(INVENTORY, cell));
			if (lend)
				ch->SetExp(dwExp);
			sys_log(0, "PLAYERBOT_AI: riposty book pid=%u name=%s skill=%u level=%d->%d used=%d", ch->GetPlayerID(),
					ch->GetName(), dwVnum, iLevel, (int) ch->GetSkillLevel(dwVnum), used ? 1 : 0);
			return used;
		}
		return false;
	}

	// Kamien Duchowy+ as the quest riposty uses it.
	static bool BotSoulStone(CHARACTER* ch, unsigned int dwVnum)
	{
		const int iLevel = ch->GetSkillLevel(dwVnum);
		if (iLevel < 30 || iLevel >= SKILL_MAX_LEVEL)
			return false;
		LPITEM stone = BotItem(ch, ITEM_SOUL_STONE_PLUS);
		if (!stone)
			return false;
		const char* flag = "riposty.next_time";
		const int now = get_global_time();
		if (now < ch->GetQuestFlag(flag))
			return false;
		const int rank = ch->GetRealAlignment();
		const int cost = (1000 + 500 * (iLevel - 30)) * (rank < 0 ? 2 : 1);
		if (rank - cost < 0)
			return false;
		UseUp(stone, "RIPOSTY_SOUL_STONE");
		ch->SetQuestFlag(flag, now + 12 * 3600);
		const bool learned = ch->LearnGrandMasterSkill(dwVnum);
		ch->UpdateAlignment(-(learned ? cost : number(cost / 3, cost / 2)));
		sys_log(0, "PLAYERBOT_AI: riposty soul stone %s pid=%u name=%s skill=%u level=%d->%d rank=%d->%d",
				learned ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), dwVnum, iLevel,
				(int) ch->GetSkillLevel(dwVnum), rank, ch->GetRealAlignment());
		return true;
	}
}

// playerbot_manager.cpp, the bot's pass with the skill books (not a companion): one step a minute at most.
void RipostyManageBot(CHARACTER* ch)
{
	if (!ch || !ch->IsPC() || ch->IsDead() || !ch->IsItemLoaded() || !ch->GetSkillGroup() || ch->GetLevel() < 5 ||
			ch->GetExchange() || ch->GetMyShop() || ch->IsPolymorphed())
		return;
	static std::map<DWORD, DWORD> s_mapNext;
	DWORD& next = s_mapNext[ch->GetPlayerID()];
	const DWORD now = get_dword_time();
	if (now < next)
		return;
	next = now + 60 * 1000;

	const unsigned int r = RiposteOf(ch);
	if (!r)
	{
		if (BotItem(ch, ITEM_MANUAL_RIPOSTE))
			BotLearn(ch, ITEM_MANUAL_RIPOSTE, BotChoice(ch));
		return;
	}
	const unsigned int b = BoostOf(ch);
	if (!b && ch->GetSkillLevel(r) >= SKILL_MAX_LEVEL && BotLearn(ch, ITEM_MANUAL_BOOST, BoostFor(ch->GetJob(), ch->GetSkillGroup())))
		return;
	if (BotReadBook(ch, r) || (b && BotReadBook(ch, b)))
		return;
	if (BotSoulStone(ch, r) || (b && BotSoulStone(ch, b)))
		return;
}

// playerbot_skills.h ManagePlayerBotSkills, after the build's passes (its points are left over): the riposte, then the
// boost, to M1 by points; how many points went.
int RipostyBotSpendPoints(CHARACTER* ch)
{
	if (!ch || !ch->IsPC() || !ch->GetSkillGroup())
		return 0;
	int iSpent = 0;
	const unsigned int known[2] = { RiposteOf(ch), BoostOf(ch) };
	for (int k = 0; k < 2; ++k)
	{
		const unsigned int v = known[k];
		if (!v)
			continue;
		while (ch->GetPoint(POINT_SKILL) > 0 && ch->GetSkillMasterType(v) == SKILL_NORMAL &&
				ch->GetSkillLevel(v) > 0 && ch->GetSkillLevel(v) < 20)
		{
			const int before = ch->GetSkillLevel(v);
			ch->SkillLevelUp(v);
			if (ch->GetSkillLevel(v) == before)
				break;
			++iSpent;
		}
	}
	if (iSpent)
		sys_log(0, "PLAYERBOT_AI: riposty points pid=%u name=%s riposte=%u (%d) boost=%u (%d) spent=%d left=%d",
				ch->GetPlayerID(), ch->GetName(), known[0], known[0] ? (int) ch->GetSkillLevel(known[0]) : 0, known[1],
				known[1] ? (int) ch->GetSkillLevel(known[1]) : 0, iSpent, (int) ch->GetPoint(POINT_SKILL));
	return iSpent;
}

// ---- quest functions (quest riposty) ------------------------------------------------------------------------------

namespace quest
{
	static LPCHARACTER RipostyPC()
	{
		return CQuestManager::instance().GetCurrentCharacterPtr();
	}

	static int pc_get_riposte(lua_State* L)
	{
		lua_pushnumber(L, RiposteOf(RipostyPC()));
		return 1;
	}

	static int pc_get_boost(lua_State* L)
	{
		lua_pushnumber(L, BoostOf(RipostyPC()));
		return 1;
	}

	static int pc_get_class_boost(lua_State* L)
	{
		LPCHARACTER ch = RipostyPC();
		lua_pushnumber(L, ch ? BoostFor(ch->GetJob(), ch->GetSkillGroup()) : 0);
		return 1;
	}

	static int pc_learn_passive_skill(lua_State* L)
	{
		lua_pushnumber(L, lua_isnumber(L, 1) ? Learn(RipostyPC(), (unsigned int) lua_tonumber(L, 1)) : 5);
		return 1;
	}

	static int pc_reset_passive_skills(lua_State* L)
	{
		lua_pushnumber(L, ResetAll(RipostyPC()));
		return 1;
	}
}

// Called with the Champion's quest functions (quest::RegisterChampionFunctions, playerbot_champion.cpp).
void RegisterRipostyFunctions()
{
	using namespace quest;
	static const luaL_reg pc_add[] =
	{
		{ "get_riposte",			pc_get_riposte },
		{ "get_boost",				pc_get_boost },
		{ "get_class_boost",		pc_get_class_boost },
		{ "learn_passive_skill",	pc_learn_passive_skill },
		{ "reset_passive_skills",	pc_reset_passive_skills },
		{ NULL, NULL }
	};
	lua_State* L = CQuestManager::instance().GetLuaState();
	lua_getglobal(L, "pc");
	if (!lua_istable(L, -1))
	{
		lua_pop(L, 1);
		sys_err("RIPOSTY: the quest table pc does not exist");
		return;
	}
	for (const luaL_reg* reg = pc_add; reg->name; ++reg)
	{
		lua_pushstring(L, reg->name);
		lua_pushcfunction(L, reg->func);
		lua_rawset(L, -3);
	}
	lua_pop(L, 1);
}
