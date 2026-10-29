// MT2009_PLUS_HORSE40_V1 - the horse past level 21 (server-patches/konie/README.md).
//
// Up to 21 nothing changes (konie.quest's paid training 1-19, the battle and military horse missions
// horse_upgrade / horse_upgrade2). Past 21 the pl-wiki ("Kon", "Misje konne", "Otrzymujesz pasze dla
// konia", "Zlota Ksiega Konia") and the uploaded "system_rozwoju_konia" package (Best Studio's export of the
// official Mount Upgrade System - mount_up_grade.cpp, skill_proto.sql, the client window) are the rules:
//
//  * levels 22-40 with Pasza dla Konia (50048): feeding fills the horse's experience bar (200-250 a feed,
//    the package), a full bar is raised at the Stajenny for 50 feed and the wiki's Yang (500 000 at 21 ...
//    5 000 000 from 30); 50 % of the tries fail and keep the bar - the next try costs 50 Gaya too (100 from
//    level 30) and cannot fail (the package's retry). Character level 75, from horse level 30 Poziom
//    Czempiona 1 (the wiki). The experience, the failure and the horse skills are quest flags of
//    "konie_rozwoj" (no new column, no new packet: the client's window speaks chat commands);
//  * the horse's stats (horse_rider.cpp, the wiki's table; INT 1-21 too) and from 31 the wiki's Sung Ma - floors,
//    max(own with the equipment, table), on any mount (Mt2009KonieComputePoints);
//  * the horse skills of the wiki (the package's skills 285-311 and their skill_proto polynomials; the
//    player's skill array ends at 265, so they live in the flags s1/s1lv/s2/s2lv and their effects here):
//    one skill from horse level 21, a second from 31, levels 1-20 (1 000 Gaya and 20 000 000 Yang a level),
//    forgotten free at the Stajenny, on every mount. Passive ones (EXP, Precyzja, the strong-against ones)
//    count while riding; the timed ones start on a blow struck while riding (Zwinne Kopyta, Gwaltowna
//    Wichura, the four Sung Ma wills, Brak Odrzutu 1 %) or on foot (Bezszelestny Chod), Niesmiertelnosc
//    when a blow would leave less than 30 % HP; each has the wiki's cooldown;
//  * Potezny Kon Wojskowy (20149-20151) is the horse of 31+ whose rider earned the Zlota Ksiega Konia
//    (flag konie_rozwoj.zloty, quest konie_rozwoj); Czer. Zen-szen (premium) 50047 drops on the Sung Ma
//    maps and Szlachetna Trawa 50046 from Ahtrin Wielki Mistrz (6820).
// Bots (playerbot_horse30.h) use Mt2009KonieBot*.
#include "stdafx.h"
#include <map>
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "affect.h"
#include "desc.h"
#include "horse_rider.h"
#include "questmanager.h"
#include "questlua.h"
#include "cmd.h"

namespace champion { bool IsSungmaMap(long lMapIndex); }

namespace
{
	const int KONIE_FIRST = 21;               // the first level this system raises from
	const int KONIE_MAX = 40;                 // HORSE_MAX_LEVEL (horse_rider.h)
	const DWORD KONIE_FEED = 50048;           // Pasza dla Konia
	const int KONIE_FEED_LEVEL_UP = 50;       // feed a level-up try eats
	const int KONIE_FEED_EXP_MIN = 200;       // experience of one feed (the package)
	const int KONIE_FEED_EXP_MAX = 250;
	const int KONIE_SUCCESS_PCT = 50;         // a first try's chance (the package's 0/1 roll)
	const int KONIE_RETRY_GAYA_LOW = 50;      // a retry under horse level 30 (the wiki)
	const int KONIE_RETRY_GAYA_HIGH = 100;    // from 30
	const int KONIE_CHAR_LEVEL = 75;          // the wiki: "Poziom 75+"
	const int KONIE_CHAMPION_FROM = 30;       // from horse level 30 a try asks Poziom Czempiona 1
	const int KONIE_SKILL_MAX = 20;
	const int KONIE_SKILL_GAYA = 1000;
	const long long KONIE_SKILL_YANG = 20000000LL;
	const int KONIE_WINDOW_SECONDS = 900;     // the Stajenny's window stays usable this long

	// the experience a full bar needs and the Yang of the try, by the horse's level now (21..39) - the wiki
	const DWORD s_adwKonieExp[KONIE_MAX - KONIE_FIRST] = {
		12500, 12810, 13130, 13440, 14060, 14380, 14690, 15000, 18750, 37500,
		48800, 63490, 66930, 82620, 107510, 139890, 182030, 236860, 308200 };

	long long KoniePrice(int level)
	{
		return std::min<long long>(5000000LL, 500000LL * (level - KONIE_FIRST + 1));
	}

	// the wiki's Sung Ma of the horse 31..40 (STR, VIT, RES, INT) - minima while riding
	const int s_aiKonieSungma[10][4] = {
		{ 10, 15, 25, 25 }, { 11, 17, 26, 26 }, { 12, 19, 27, 27 }, { 13, 21, 28, 28 }, { 14, 23, 29, 29 },
		{ 15, 25, 30, 30 }, { 16, 27, 31, 31 }, { 17, 29, 32, 32 }, { 18, 31, 33, 33 }, { 35, 40, 45, 45 } };

	// the timed effects' affects (780-788: free in this engine - 760-776 are the relics', playerbot_relikty.cpp)
	enum
	{
		AFFECT_KONIE_NIMBLE = 780,          // 285 Zwinne Kopyta - movement speed
		AFFECT_KONIE_SPEED = 781,           // 287 Gwaltowna Wichura - attack speed
		AFFECT_KONIE_FEATHER = 782,         // 288 Bezszelestny Chod - Lekki Krok on foot
		AFFECT_KONIE_INVINCIBLE = 783,      // 289 Niesmiertelnosc
		AFFECT_KONIE_NO_KNOCKBACK = 784,    // 290 Brak Odrzutu
		AFFECT_KONIE_SUNGMA_STR = 785,      // 307-310 Wola Sung Ma
		AFFECT_KONIE_SUNGMA_HP = 786,
		AFFECT_KONIE_SUNGMA_MOVE = 787,
		AFFECT_KONIE_SUNGMA_IMMUNE = 788,
	};

	bool KonieIsSkill(DWORD v)
	{
		return v >= 285 && v <= 311 && v != 297 && v != 306;   // no zodiac race bonus, no Lycan in this world
	}

	// the constant (riding) skills' point
	BYTE KonieConstPoint(DWORD v)
	{
		switch (v)
		{
			case 286: return POINT_MALL_EXPBONUS;
			case 291: return POINT_ATTBONUS_HUMAN;
			case 292: return POINT_ATTBONUS_ANIMAL;
			case 293: return POINT_ATTBONUS_ORC;
			case 294: return POINT_ATTBONUS_MILGYO;
			case 295: return POINT_ATTBONUS_UNDEAD;
			case 296: return POINT_ATTBONUS_DEVIL;
			case 298: return POINT_ATTBONUS_DESERT;
			case 299: return POINT_ATTBONUS_INSECT;
			case 300: return POINT_ATTBONUS_MONSTER;
			case 302: return POINT_ATTBONUS_WARRIOR;
			case 303: return POINT_ATTBONUS_ASSASSIN;
			case 304: return POINT_ATTBONUS_SURA;
			case 305: return POINT_ATTBONUS_SHAMAN;
			case 311: return POINT_HIT_PCT;
		}
		return POINT_NONE;
	}

	// the package's polynomials (skill_proto.sql) - s the skill's level, h the horse's
	double KonieValue(DWORD v, double s, double h)
	{
		switch (v)
		{
			case 285: return (4.0 + h * s / 100.0) * (s / 3.0);
			case 286: return (h * s / 100.0) + 1.5 + (s / 8.0);
			case 287: return (5.0 + h * s / 600.0) * (s / 5.0);
			case 288: return 60.0 * std::min(1.0, s * h / 800.0);    // Lekki Krok's 60*k, k = s*h/800
			case 301: return s * s / (140.0 - h);                    // per cent (k = the skill level: the wiki's 3.36 % at 21)
			case 307: case 308: case 309: case 310: return 3.0 + (h * s) * (s / 500.0);
		}
		return 1.0 + s * h / 100.0;                                  // 291-305, 311
	}

	int KonieDuration(DWORD v, double s, double h)
	{
		double d = 0.0;
		switch (v)
		{
			case 285: case 287: case 307: case 308: case 309: case 310: d = 3.0 + (s * h * 0.4) / 20.0; break;
			case 288: d = 1.0 + (s * h * 0.3) / 20.0; break;
			case 289: d = (h * s * 0.3) / 60.0; break;
			case 290: d = 3.0 + (s * h * 0.5) / 20.0; break;
		}
		return std::max(1, (int)d);
	}

	int KonieCooldown(DWORD v)
	{
		switch (v)
		{
			case 288: return 300;
			case 289: return 600;
		}
		return 180;
	}

	quest::PC* KoniePC(const CHARACTER* ch)
	{
		if (!ch || !ch->IsPC())
			return NULL;
		return quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
	}

	int KonieFlag(const CHARACTER* ch, const char* name)
	{
		quest::PC* pc = KoniePC(ch);
		return pc ? pc->GetFlag(std::string("konie_rozwoj.") + name) : 0;
	}

	void KonieSetFlag(const CHARACTER* ch, const char* name, int value)
	{
		quest::PC* pc = KoniePC(ch);
		if (pc)
			pc->SetFlag(std::string("konie_rozwoj.") + name, value);
	}

	int KonieSlots(int horseLevel)
	{
		return horseLevel >= 31 ? 2 : (horseLevel >= KONIE_FIRST ? 1 : 0);
	}

	// the two skills of a rider (the flags read once a blow); a slot the horse's level does not open counts nothing
	struct SKonieSkills
	{
		DWORD v[2];
		int lv[2];
	};

	SKonieSkills KonieSkills(const CHARACTER* ch)
	{
		SKonieSkills k;
		const int slots = KonieSlots(ch->GetHorseLevel());
		k.v[0] = slots >= 1 ? KonieFlag(ch, "s1") : 0;
		k.lv[0] = slots >= 1 ? std::min(KONIE_SKILL_MAX, KonieFlag(ch, "s1lv")) : 0;
		k.v[1] = slots >= 2 ? KonieFlag(ch, "s2") : 0;
		k.lv[1] = slots >= 2 ? std::min(KONIE_SKILL_MAX, KonieFlag(ch, "s2lv")) : 0;
		return k;
	}

	// the level of a learned skill (0 = not learned)
	int KonieSkillLevel(const SKonieSkills& k, DWORD v)
	{
		for (int i = 0; i < 2; ++i)
			if (k.v[i] == v && k.lv[i] > 0)
				return k.lv[i];
		return 0;
	}

	// 0 the try may go, 1 character level, 2 Poziom Czempiona, 3 the horse is at its top, 4 no horse of 21
	int KonieRequirement(const CHARACTER* ch)
	{
		const int h = ch->GetHorseLevel();
		if (h < KONIE_FIRST)
			return 4;
		if (h >= KONIE_MAX)
			return 3;
		if (ch->GetLevel() < KONIE_CHAR_LEVEL)
			return 1;
		if (h >= KONIE_CHAMPION_FROM && ch->GetConquerorLevel() < 1)
			return 2;
		return 0;
	}

	DWORD KonieNeedExp(int level)
	{
		if (level < KONIE_FIRST || level >= KONIE_MAX)
			return 0;
		return s_adwKonieExp[level - KONIE_FIRST];
	}

	int KonieRetryGaya(int level)
	{
		return level < 30 ? KONIE_RETRY_GAYA_LOW : KONIE_RETRY_GAYA_HIGH;
	}

	bool KonieClient(const CHARACTER* ch)
	{
		return ch && ch->GetDesc() && ch->GetDesc()->IsPhase(PHASE_GAME) && !ch->GetDesc()->IsBot();
	}

	void KonieMsg(LPCHARACTER ch, int code, long long a = 0, long long b = 0)
	{
		if (KonieClient(ch))
			ch->ChatPacket(CHAT_TYPE_COMMAND, "konie_rozwoj_msg %d %lld %lld", code, a, b);
	}

	// cooldowns of the timed skills: pid -> skill -> the second it is ready again
	std::map<DWORD, std::map<DWORD, DWORD> > s_mapKonieReady;

	bool KonieReady(const CHARACTER* ch, DWORD v)
	{
		std::map<DWORD, std::map<DWORD, DWORD> >::const_iterator it = s_mapKonieReady.find(ch->GetPlayerID());
		if (it == s_mapKonieReady.end())
			return true;
		std::map<DWORD, DWORD>::const_iterator jt = it->second.find(v);
		return jt == it->second.end() || (DWORD)get_global_time() >= jt->second;
	}

	void KonieUsed(const CHARACTER* ch, DWORD v)
	{
		s_mapKonieReady[ch->GetPlayerID()][v] = get_global_time() + KonieCooldown(v);
	}

	// raises the horse a level; a horse under its rider is taken down and back (a player is asked to dismount
	// first - only a bot reaches this riding)
	void KonieSetLevel(LPCHARACTER ch, int level)
	{
		const bool wasRiding = ch->IsHorseRiding();
		if (wasRiding)
			ch->StopRiding();
		ch->SetHorseLevel(level);
		ch->ComputePoints();
		ch->SkillLevelPacket();
		if (wasRiding)
			ch->StartRiding();
	}

	// feeds until the bar is full or the bag empty; the feed eaten (0 = none)
	int KonieFeed(LPCHARACTER ch)
	{
		const int level = ch->GetHorseLevel();
		const DWORD need = KonieNeedExp(level);
		const DWORD have = (DWORD)std::max(0, KonieFlag(ch, "exp"));
		if (!need || have >= need)
			return 0;
		const int bag = (int)ch->CountSpecifyItem(KONIE_FEED);
		DWORD exp = have;
		int used = 0;
		while (used < bag && exp < need)
		{
			exp += number(KONIE_FEED_EXP_MIN, KONIE_FEED_EXP_MAX);
			++used;
		}
		if (!used)
			return 0;
		exp = std::min(exp, need);
		ch->RemoveSpecifyItem(KONIE_FEED, used);
		KonieSetFlag(ch, "exp", (int)exp);
		sys_log(0, "KONIE_ROZWOJ: feed pid=%u name=%s horse=%d used=%d exp=%u/%u", ch->GetPlayerID(), ch->GetName(),
				level, used, exp, need);
		return used;
	}

	// one try: -1 nothing done (the reason told), 0 a failed try, else the new level. A bot short of a retry's
	// Gaya retries without it (bBot - it has no Gaya shop to go to).
	int KonieTry(LPCHARACTER ch, int yangPercent, bool bTell, bool bBot = false)
	{
		const int level = ch->GetHorseLevel();
		const int req = KonieRequirement(ch);
		if (req)
		{
			if (bTell)
				KonieMsg(ch, 10 + req, req == 1 ? KONIE_CHAR_LEVEL : 1);
			return -1;
		}
		const DWORD need = KonieNeedExp(level);
		if ((DWORD)std::max(0, KonieFlag(ch, "exp")) < need)
		{
			if (bTell)
				KonieMsg(ch, 3);
			return -1;
		}
		if ((int)ch->CountSpecifyItem(KONIE_FEED) < KONIE_FEED_LEVEL_UP)
		{
			if (bTell)
				KonieMsg(ch, 2, KONIE_FEED_LEVEL_UP);
			return -1;
		}
		const long long yang = KoniePrice(level) * yangPercent / 100;
		if (ch->GetGold() < yang)
		{
			if (bTell)
				KonieMsg(ch, 4, yang);
			return -1;
		}
		const bool bRetry = KonieFlag(ch, "fail") > 0;
		int gaya = bRetry ? KonieRetryGaya(level) : 0;
		if (bBot && gaya > ch->GetGaya())
			gaya = 0;
		if (gaya > ch->GetGaya())
		{
			if (bTell)
				KonieMsg(ch, 5, gaya);
			return -1;
		}
		if (gaya && !ch->ChangeGaya(-gaya, "HORSE_LEVEL_RETRY"))
			return -1;
		ch->RemoveSpecifyItem(KONIE_FEED, KONIE_FEED_LEVEL_UP);
		if (yang > 0)
			ch->ChangeGold(-yang);
		if (!bRetry && number(1, 100) > KONIE_SUCCESS_PCT)
		{
			KonieSetFlag(ch, "fail", 1);
			sys_log(0, "KONIE_ROZWOJ: try failed pid=%u name=%s horse=%d yang=%lld", ch->GetPlayerID(), ch->GetName(),
					level, yang);
			if (bTell)
				KonieMsg(ch, 7, level + 1, KonieRetryGaya(level));
			return 0;
		}
		KonieSetFlag(ch, "fail", 0);
		KonieSetFlag(ch, "exp", 0);
		KonieSetLevel(ch, level + 1);
		sys_log(0, "KONIE_ROZWOJ: level up pid=%u name=%s horse=%d->%d yang=%lld gaya=%d", ch->GetPlayerID(),
				ch->GetName(), level, level + 1, yang, gaya);
		if (bTell)
			KonieMsg(ch, 6, level + 1);
		return level + 1;
	}

	void KonieSendInfo(LPCHARACTER ch, bool bOpen)
	{
		if (!KonieClient(ch))
			return;
		const int level = ch->GetHorseLevel();
		ch->ChatPacket(CHAT_TYPE_COMMAND, "konie_rozwoj_info %d %d %u %lld %d %d %d %d %d %d %d %d %d %d", bOpen ? 1 : 0,
				level, (unsigned int)std::max(0, KonieFlag(ch, "exp")), (unsigned int)KonieNeedExp(level), KoniePrice(level),
				KonieFlag(ch, "fail") > 0 ? 1 : 0, KonieRetryGaya(level), KonieRequirement(ch),
				KonieFlag(ch, "s1"), KonieFlag(ch, "s1lv"), KonieFlag(ch, "s2"), KonieFlag(ch, "s2lv"),
				KonieSlots(level), KonieFlag(ch, "zloty") > 0 ? 1 : 0);
	}

	bool KonieWindowOpen(LPCHARACTER ch)
	{
		if (KonieFlag(ch, "okno") >= get_global_time())
			return true;
		KonieMsg(ch, 1);
		return false;
	}

	// the anti-spam of the window's buttons
	std::map<DWORD, DWORD> s_mapKonieLastAction;

	bool KonieThrottle(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapKonieLastAction[ch->GetPlayerID()];
		if (last && now - last < 300)
			return false;
		last = now;
		return true;
	}

	int KonieSkillUp(LPCHARACTER ch, int slot)
	{
		if (slot != 1 && slot != 2)
			return -1;
		const char* fv = slot == 1 ? "s1" : "s2";
		const char* fl = slot == 1 ? "s1lv" : "s2lv";
		const DWORD v = KonieFlag(ch, fv);
		const int lv = KonieFlag(ch, fl);
		if (!KonieIsSkill(v) || lv <= 0)
			return -1;
		if (lv >= KONIE_SKILL_MAX)
		{
			KonieMsg(ch, 20);
			return -1;
		}
		if (ch->GetGaya() < KONIE_SKILL_GAYA)
		{
			KonieMsg(ch, 5, KONIE_SKILL_GAYA);
			return -1;
		}
		if (ch->GetGold() < KONIE_SKILL_YANG)
		{
			KonieMsg(ch, 4, KONIE_SKILL_YANG);
			return -1;
		}
		if (!ch->ChangeGaya(-KONIE_SKILL_GAYA, "HORSE_SKILL"))
			return -1;
		ch->ChangeGold(-KONIE_SKILL_YANG);
		KonieSetFlag(ch, fl, lv + 1);
		ch->ComputePoints();
		sys_log(0, "KONIE_ROZWOJ: skill up pid=%u name=%s skill=%u %d->%d", ch->GetPlayerID(), ch->GetName(), v, lv, lv + 1);
		KonieMsg(ch, 21, v, lv + 1);
		return lv + 1;
	}

	void KonieTimed(LPCHARACTER ch, const SKonieSkills& k, DWORD v, DWORD affect, BYTE point, DWORD flag, double h)
	{
		const int s = KonieSkillLevel(k, v);
		if (!s || !KonieReady(ch, v))
			return;
		const int value = point == POINT_NONE ? 0 : std::max(1, (int)KonieValue(v, s, h));
		ch->AddAffect(affect, point, value, flag, KonieDuration(v, s, h), 0, true);
		KonieUsed(ch, v);
	}
}

// ---------------------------------------------------------------- the engine's hooks

// CHARACTER::ComputePoints (char.cpp, after the equipment, before ComputeBattlePoints): on any mount the wiki's
// "Zmiana punktow statusu na roznych poziomach konia" - the LEAST the rider has of a stat, max(own, table), never
// added on top (the owner, 30 October 2026): STR / DEX / VIT / INT by the horse's level (c_aHorseStat, 1-40) and from
// 31 the Sung Ma wills; "own" is the base points with the worn items (the stock code took it before the items, so
// the items stacked on the floor - char.cpp's MT2009_PLUS_HORSE40_V1 (floors)). The affects come after this. Then
// the constant horse skills while riding. Every mount, dismount and level change recomputes the points.
void Mt2009KonieComputePoints(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetMountVnum())
		return;
	const int h = std::min<int>(ch->GetHorseLevel(), KONIE_MAX);
	if (h <= 0)
		return;
	const int floors[4][2] = { { POINT_ST, ch->GetHorseST() }, { POINT_DX, ch->GetHorseDX() },
			{ POINT_HT, ch->GetHorseHT() }, { POINT_IQ, ch->GetHorseIQ() } };
	for (int i = 0; i < 4; ++i)
		if (ch->GetPoint(floors[i][0]) < floors[i][1])
			ch->PointChange(floors[i][0], floors[i][1] - ch->GetPoint(floors[i][0]));
	if (h >= 31)
	{
		static const BYTE s_abPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
		const int* row = s_aiKonieSungma[h - 31];
		for (int i = 0; i < 4; ++i)
			if (ch->GetPoint(s_abPoint[i]) < row[i])
				ch->PointChange(s_abPoint[i], row[i] - ch->GetPoint(s_abPoint[i]));
	}
	if (h < KONIE_FIRST)
		return;
	const SKonieSkills k = KonieSkills(ch);
	for (int i = 0; i < 2; ++i)
	{
		const BYTE point = KonieConstPoint(k.v[i]);
		if (k.lv[i] <= 0 || point == POINT_NONE)
			continue;
		ch->PointChange(point, std::max(1, (int)KonieValue(k.v[i], k.lv[i], h)));
	}
}

// CHARACTER::Damage (char_battle.cpp): Niesmiertelnosc (the victim), Jazda (umiej. konne) and the timed skills
// started by a blow (the attacker). Answers the damage, or -1 when the blow is blocked.
int Mt2009KonieDamage(LPCHARACTER victim, LPCHARACTER attacker, int dam, DWORD dwUsedSkill)
{
	if (!victim)
		return dam;
	if (victim->IsPC() && victim->FindAffect(AFFECT_KONIE_INVINCIBLE))
		return -1;
	if (victim->IsPC() && dam > 0 && victim->GetHorseLevel() >= KONIE_FIRST && victim->IsRiding() &&
			(long long)(victim->GetHP() - dam) * 100 < (long long)victim->GetMaxHP() * 30)
	{
		const int s = KonieSkillLevel(KonieSkills(victim), 289);
		if (s && KonieReady(victim, 289))
		{
			victim->AddAffect(AFFECT_KONIE_INVINCIBLE, POINT_NONE, 0, AFF_NONE,
					KonieDuration(289, s, victim->GetHorseLevel()), 0, true);
			KonieUsed(victim, 289);
			return -1;
		}
	}
	if (!attacker || !attacker->IsPC() || attacker == victim || attacker->GetHorseLevel() < KONIE_FIRST)
		return dam;
	const SKonieSkills k = KonieSkills(attacker);
	if (!k.v[0] && !k.v[1])
		return dam;
	const double h = attacker->GetHorseLevel();
	if (attacker->IsRiding())
	{
		if (dwUsedSkill >= 137 && dwUsedSkill <= 140 && dam > 0)
		{
			const int s = KonieSkillLevel(k, 301);
			if (s)
				dam = (int)((double)dam * (100.0 + KonieValue(301, s, h)) / 100.0);
		}
		KonieTimed(attacker, k, 285, AFFECT_KONIE_NIMBLE, POINT_MOV_SPEED, AFF_NONE, h);
		KonieTimed(attacker, k, 287, AFFECT_KONIE_SPEED, POINT_ATT_SPEED, AFF_NONE, h);
		KonieTimed(attacker, k, 307, AFFECT_KONIE_SUNGMA_STR, POINT_SUNGMA_STR, AFF_NONE, h);
		KonieTimed(attacker, k, 308, AFFECT_KONIE_SUNGMA_HP, POINT_SUNGMA_HP, AFF_NONE, h);
		KonieTimed(attacker, k, 309, AFFECT_KONIE_SUNGMA_MOVE, POINT_SUNGMA_MOVE, AFF_NONE, h);
		KonieTimed(attacker, k, 310, AFFECT_KONIE_SUNGMA_IMMUNE, POINT_SUNGMA_IMMUNE, AFF_NONE, h);
		if (KonieSkillLevel(k, 290) && number(1, 100) == 1)
			KonieTimed(attacker, k, 290, AFFECT_KONIE_NO_KNOCKBACK, POINT_NONE, AFF_NONE, h);
	}
	else
		KonieTimed(attacker, k, 288, AFFECT_KONIE_FEATHER, POINT_MOV_SPEED, AFF_SKILL_FEATHER_WALK, h);
	return dam;
}

// CHARACTER::IsResistPush (char_battle.cpp): Brak Odrzutu while it lasts
bool Mt2009KonieResistPush(LPCHARACTER ch)
{
	return ch && ch->IsPC() && ch->FindAffect(AFFECT_KONIE_NO_KNOCKBACK);
}

// CHARACTER::OnStopRiding (char_horse.cpp): the riding skills' timed effects end with the ride
void Mt2009KonieStopRiding(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;
	static const DWORD s_adwRiding[] = { AFFECT_KONIE_NIMBLE, AFFECT_KONIE_SPEED, AFFECT_KONIE_NO_KNOCKBACK,
			AFFECT_KONIE_SUNGMA_STR, AFFECT_KONIE_SUNGMA_HP, AFFECT_KONIE_SUNGMA_MOVE, AFFECT_KONIE_SUNGMA_IMMUNE };
	for (size_t i = 0; i < sizeof(s_adwRiding) / sizeof(s_adwRiding[0]); ++i)
		if (ch->FindAffect(s_adwRiding[i]))
			ch->RemoveAffect(s_adwRiding[i]);
}

// CHARACTER::GetMyHorseVnum (char_horse.cpp): Potezny Kon Wojskowy for a horse of 31+ whose rider has the
// Zlota Ksiega Konia (0 = the old rule)
DWORD Mt2009KonieHorseVnum(const CHARACTER* ch, int delta)
{
	if (!ch || ch->GetHorseLevel() < 31 || KonieFlag(ch, "zloty") <= 0)
		return 0;
	return 20149 + std::max(0, std::min(2, delta));
}

// ITEM_MANAGER::CreateDropItem (item_manager.cpp): Czer. Zen-szen (premium) from the Sung Ma maps' monsters (the
// wiki: "Wszystkie potwory Yohara"), Szlachetna Trawa from Ahtrin Wielki Mistrz (Jaskinie Gnolli 3)
void Mt2009KonieDrop(LPCHARACTER pkChr, LPCHARACTER pkKiller, std::vector<LPITEM>& vec_item)
{
	if (!pkChr || !pkKiller || !pkKiller->IsPC() || pkChr->IsPC() || !pkChr->IsMonster())
		return;
	DWORD vnum = 0;
	if (pkChr->GetRaceNum() == 6820 && number(1, 100) <= 25)
		vnum = 50046;
	else if (champion::IsSungmaMap(pkChr->GetMapIndex()) && number(1, 1000) <= 5)
		vnum = 50047;
	if (!vnum)
		return;
	LPITEM item = ITEM_MANAGER::instance().CreateItem(vnum, 1, 0, true);
	if (item)
		vec_item.push_back(item);
}

// "/konie_rozwoj <info|karm|awans|umiej 1|2>" - the Stajenny's window (root/uikonierozwoj.py)
ACMD(do_konie_rozwoj)
{
	char arg1[256], arg2[256];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	if (!ch || !ch->IsPC())
		return;
	const std::string what = arg1;
	if (what == "info" || what.empty())
	{
		KonieSendInfo(ch, false);
		return;
	}
	if (!KonieThrottle(ch) || !KonieWindowOpen(ch))
		return;
	if (ch->IsHorseRiding() || ch->GetMountVnum())
	{
		KonieMsg(ch, 9);
		KonieSendInfo(ch, false);
		return;
	}
	if (what == "karm")
	{
		const int req = KonieRequirement(ch);
		if (req)
			KonieMsg(ch, 10 + req, req == 1 ? KONIE_CHAR_LEVEL : 1);
		else if (!ch->CountSpecifyItem(KONIE_FEED))
			KonieMsg(ch, 2, 1);
		else if ((DWORD)std::max(0, KonieFlag(ch, "exp")) >= KonieNeedExp(ch->GetHorseLevel()))
			KonieMsg(ch, 8);
		else
		{
			const int used = KonieFeed(ch);
			if (used)
				KonieMsg(ch, 22, used, KonieFlag(ch, "exp"));
		}
	}
	else if (what == "awans")
		KonieTry(ch, 100, true);
	else if (what == "umiej")
	{
		int slot = 0;
		str_to_number(slot, arg2);
		KonieSkillUp(ch, slot);
	}
	KonieSendInfo(ch, false);
}

// ---------------------------------------------------------------- the quest functions (horse.konie_*)

namespace quest
{
	// horse.konie_otworz() - the Stajenny opens the window (konie_rozwoj.quest)
	ALUA(horse_konie_otworz)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch && ch->IsPC())
		{
			KonieSetFlag(ch, "okno", get_global_time() + KONIE_WINDOW_SECONDS);
			KonieSendInfo(ch, true);
		}
		return 0;
	}

	// horse.konie_naucz(skill) - a book read: 0 learned, 1 no horse of 21, 2 no free slot, 3 learned already,
	// 4 no such skill here
	ALUA(horse_konie_naucz)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const DWORD v = lua_isnumber(L, 1) ? (DWORD)lua_tonumber(L, 1) : 0;
		int code = 4;
		if (ch && ch->IsPC() && KonieIsSkill(v))
		{
			const int h = ch->GetHorseLevel();
			const DWORD s1 = KonieFlag(ch, "s1"), s2 = KonieFlag(ch, "s2");
			if (h < KONIE_FIRST)
				code = 1;
			else if (s1 == v || s2 == v)
				code = 3;
			else if (!s1)
			{
				KonieSetFlag(ch, "s1", v);
				KonieSetFlag(ch, "s1lv", 1);
				code = 0;
			}
			else if (!s2 && KonieSlots(h) >= 2)
			{
				KonieSetFlag(ch, "s2", v);
				KonieSetFlag(ch, "s2lv", 1);
				code = 0;
			}
			else
				code = 2;
			if (code == 0)
			{
				ch->ComputePoints();
				sys_log(0, "KONIE_ROZWOJ: skill learned pid=%u name=%s skill=%u", ch->GetPlayerID(), ch->GetName(), v);
				if (KonieFlag(ch, "okno") >= get_global_time())
					KonieSendInfo(ch, false);
			}
		}
		lua_pushnumber(L, code);
		return 1;
	}

	// horse.konie_zapomnij(slot) - the Stajenny takes a skill back, free (the wiki)
	ALUA(horse_konie_zapomnij)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const int slot = lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : 0;
		bool done = false;
		if (ch && ch->IsPC() && (slot == 1 || slot == 2) && KonieFlag(ch, slot == 1 ? "s1" : "s2"))
		{
			const DWORD v = KonieFlag(ch, slot == 1 ? "s1" : "s2");
			if (slot == 1)
			{
				// the second skill moves up: slot 1 is the one a horse of 21 keeps
				KonieSetFlag(ch, "s1", KonieFlag(ch, "s2"));
				KonieSetFlag(ch, "s1lv", KonieFlag(ch, "s2lv"));
			}
			KonieSetFlag(ch, "s2", 0);
			KonieSetFlag(ch, "s2lv", 0);
			ch->ComputePoints();
			sys_log(0, "KONIE_ROZWOJ: skill forgotten pid=%u name=%s skill=%u", ch->GetPlayerID(), ch->GetName(), v);
			done = true;
		}
		lua_pushboolean(L, done ? 1 : 0);
		return 1;
	}

	// horse.konie_slot(slot) -> skill, level
	ALUA(horse_konie_slot)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const int slot = lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : 0;
		int v = 0, lv = 0;
		if (ch && ch->IsPC() && (slot == 1 || slot == 2))
		{
			v = KonieFlag(ch, slot == 1 ? "s1" : "s2");
			lv = KonieFlag(ch, slot == 1 ? "s1lv" : "s2lv");
		}
		lua_pushnumber(L, v);
		lua_pushnumber(L, lv);
		return 2;
	}

	// horse.konie_odswiez() - the points again (the Zlota Ksiega, a login)
	ALUA(horse_konie_odswiez)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch && ch->IsPC())
			ch->ComputePoints();
		return 0;
	}

	// horse.konie_karm() - Czer. Zen-szen (premium) feeds a horse of 31+ (horse.feed refuses it - questlua_horse.cpp)
	ALUA(horse_konie_karm)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		bool fed = false;
		if (ch && ch->IsPC() && ch->GetHorseLevel() >= 31 && ch->GetHorseHealth() > 0)
		{
			ch->FeedHorse();
			fed = true;
		}
		lua_pushboolean(L, fed ? 1 : 0);
		return 1;
	}

	// RegisterHorseFunctionTable (questlua_horse.cpp) adds these to the "horse" table
	void Mt2009KonieRegisterLua()
	{
		luaL_reg konie_functions[] =
		{
			{ "konie_otworz",	horse_konie_otworz	},
			{ "konie_naucz",	horse_konie_naucz	},
			{ "konie_zapomnij",	horse_konie_zapomnij	},
			{ "konie_slot",		horse_konie_slot	},
			{ "konie_odswiez",	horse_konie_odswiez	},
			{ "konie_karm",		horse_konie_karm	},
			{ NULL,			NULL			}
		};
		CQuestManager::instance().AddLuaFunctionTable("horse", konie_functions, true);
	}
}

// ---------------------------------------------------------------- the bots (playerbot_horse30.h)

// the bots never sell these (IsPlayerBotJunkItem, ScorePlayerBotShopStockRules, IsPlayerBotDealSellable)
bool Mt2009KonieIsKeptVnum(DWORD dwVnum)
{
	return (dwVnum >= 50046 && dwVnum <= 50049) || (dwVnum >= 55050 && dwVnum <= 55067) || dwVnum == 83050;
}

// the daily feed of quest konie_rozwoj (22-27 Pasza dla Konia once in 24 h) for a bot: a bot hunts anyway
void Mt2009KonieBotDailyFeed(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || ch->GetHorseLevel() < KONIE_FIRST || ch->GetHorseLevel() >= KONIE_MAX ||
			ch->GetLevel() < KONIE_CHAR_LEVEL)
		return;
	const int now = get_global_time();
	if (KonieFlag(ch, "pasza_bot") > now)
		return;
	const int n = number(22, 27);
	KonieSetFlag(ch, "pasza_bot", now + 24 * 60 * 60);
	ch->AutoGiveItem(KONIE_FEED, n, -1, false);
	sys_log(0, "PLAYERBOT_HORSE: daily feed pid=%u name=%s horse=%d feed=%d", ch->GetPlayerID(), ch->GetName(),
			ch->GetHorseLevel(), n);
}

// the feed the bar still needs (at the lowest roll) and the try's 50
int Mt2009KonieBotFeedWanted(LPCHARACTER ch)
{
	if (!ch || KonieRequirement(ch))
		return 0;
	const DWORD need = KonieNeedExp(ch->GetHorseLevel());
	const DWORD have = (DWORD)std::max(0, KonieFlag(ch, "exp"));
	const int bar = have >= need ? 0 : (int)((need - have + KONIE_FEED_EXP_MIN - 1) / KONIE_FEED_EXP_MIN);
	return bar + KONIE_FEED_LEVEL_UP;
}

// the Yang the next try costs a bot (its share of the price)
long long Mt2009KonieBotGold(LPCHARACTER ch, int yangPercent)
{
	if (!ch || KonieRequirement(ch))
		return 0;
	return KoniePrice(ch->GetHorseLevel()) * yangPercent / 100;
}

// a stable visit pays off: the feed for the bar and the try in the bag, the Yang (over `reserve`) and a retry's Gaya
bool Mt2009KonieBotCanTry(LPCHARACTER ch, int yangPercent, long long reserve)
{
	if (!ch || KonieRequirement(ch))
		return false;
	if ((int)ch->CountSpecifyItem(KONIE_FEED) < Mt2009KonieBotFeedWanted(ch))
		return false;
	return ch->GetGold() - reserve >= Mt2009KonieBotGold(ch, yangPercent);
}

// at the Stajenny: feed and one try - the new level, 0 a failed try, -1 nothing done
int Mt2009KonieBotTry(LPCHARACTER ch, int yangPercent)
{
	if (!ch || KonieRequirement(ch))
		return -1;
	KonieFeed(ch);
	return KonieTry(ch, yangPercent, false, true);
}
