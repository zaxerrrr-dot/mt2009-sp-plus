#ifndef __INC_METIN2_PLAYERBOT_YOHARA_RESIST_HP_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_RESIST_HP_H__

// MT2009_PLUS_BOT_YOHARA_RESIST_HP_V1 - a Yohara bot builds the resistance of its Sung Ma map first (the owner, 7 November
// 2026: Dongan - "nie [limit, tylko druzyny], niech sie boty naucza budowac odpornosc na zywioly - to ona da rade im na
// Dongan i wszystkich mapach Yohary. Odpornosc na zywioly i HP to najwazniejsze bonusy na Yoharze"; Wawoz - "zrob
// wymagany zywiol"). Within the owner's element rules of 28 October (playerbot_element_resist.h): ice, earth and dark
// never on the armour, helmet or bracelet - a talisman line only; the hunt element changes only up the maps; down to
// another element only with the second set.
//
// What was measured (the test, 7 November 14:00-15:20, game3: the last map of every bot's PLAYERBOT_SUNGMA retreat /
// fallen line, 449 bots, with their worn items read from the database - lines and the protos' applies, the dragon
// stones' first deck, Kamien Ochrony Zywiolow's +10; the elixirs left out):
//   map (CL med)        element  resist avg / med    the talisman's line   other element of the map
//   373 Dongan (6)      fire     63 / 57             fire 13.8             dark 30%: ~25 (no line anywhere)
//   376 Seoganland (9)  earth    44 / 47             earth 22.4            -
//   377 Namgan (11)     wind     90 / 92             wind 22.6             -
//   385 Yilad (15)      earth    47 / 47             earth 25.0            -
//   388 Wawoz (18)      lightning 105 / 111         lightning 23.4        ICE 50%: 29 / 22 (talisman ice 5.3)
//   389 Rozpadlina (22) lightning 110 / 122         lightning 24.8        ICE 50%: 28 / 22 (talisman ice 4.2)
//   393 Schronienie(25) ice      42 / 47             ice 20.5              -
//   394 Zejscie (29)    lightning 93 / 96           lightning 22.2        (every monster ice + lightning: the better counts)
// The engine (playerbot_elements.cpp) counts min(resistance, 80) of the monster's own element. Wawoz and Rozpadlina are
// half ice, half lightning by separate monsters: the bots stood at 105-110 lightning - 25-30 over the cap, wasted - and
// 22 ice, so half the map's monsters hit them nearly in full. Their talisman (the one gear line ice can have) held the
// 25 of lightning: the 28 October rule "one element, everything for it" put the talisman's must on the hunt element,
// whatever the rest of the gear already gave. The change stones were not the limit (Wawoz / Rozpadlina bots held 40-600
// Zaczarowania, 100 on average); the Smocze Monety day pool was (ItemShop V3 bonus_change: 4205 pool blocks against 11
// purchases since 14:00) - for the bots that did run out. Kamien Ochrony Zywiolow: worn by all 474. Max HP: median
// 22-25 k; Max HP lines on the armour ~80%, bracelet ~80%, necklace and boots ~100% (1600-1750 each); the body costume's
// Max HP on 2-30% (the costume's first line is the hunt element's). The elixirs: uptime 0-4% (PLAYERBOT_ELEMENT census
// no_stock - one costs 10 Materialy Rzemieslnicze, 20% for 10 minutes); the attack talisman of the map's element (the
// report's "12%") is the element POWER (94xxx protos), no resistance - the Talizman Woli the bots wear for their Will
// holds the resistance line, so the pendant is not changed here.
//
// 1. The talisman's element (GetPlayerBotTalismanResistElement, the pendant's must of playerbot_yohara_bonus.h - its
//    element phase rerolls the talisman first, with a fresh element budget when the element changes):
//    * a builder for a gated map (below, refused within PLAYERBOT_YRESIST_BUILD_MS - an earth bot on Yilad too) and a
//      bot on a gated map: the gate's element (Wawoz: ice);
//    * a bot whose hunt element no gear holds (ice, earth, dark): the hunt element, as before;
//    * else the element where the talisman's top line (25) takes off the most damage on the map: for each element of
//      the map, share x (min(80, R + 25) - min(80, R)), R the bot's steady resistance to it without the talisman's own
//      line; the old choice stays unless another wins by PLAYERBOT_YRESIST_TAL_HYSTERESIS (share x points). Dongan at
//      fire 50 without the talisman: fire (70 x 25 against dark's 30 x 25); Wawoz at lightning 82 without it: ice.
//      Zejscie (both flags on every monster): the hunt element.
//    The "steady" resistance: Bonus67Total less an elixir's affect, the dragon stones' best deck counted while the deck
//    is off (it is on only around a fight).
// 2. The Sung Ma element gate (PassPlayerBotSungmaElementGate, from PickPlayerBotSungmaMap after the HP floor): the map's
//    element that only the talisman holds (share 25% or more; Wawoz: ice) at PLAYERBOT_SUNGMA_GATE_ROWS' value to
//    step on (40), and its stay value to stay (35). The gear's element (Wawoz: lightning) is the move's preparation's
//    (playerbot_element_resist.h, 5) - it is made after the pick, never before (a bot on Yilad hunts earth). A refused
//    bot hunts on lower (from Yilad: Yilad, the safest map - 0.32 deaths a bot-hour) and is a builder: its talisman
//    rolls the gate element there (1); a bot on the map under the stay value has no way down (the element rule) and
//    builds it where it stands. The table's value: ice 25 (the talisman) + 10 (the stone) + the stones' ~12 reach it,
//    and 40 against 22 halves what the ice half of the map takes.
//    The ItemShop V3's change stones for it are urgent already (IsPlayerBotYoharaMoveWaitingOnBonus: the talisman's
//    element target short).
// 3. The census (PLAYERBOT_YRESIST census, every PLAYERBOT_YRESIST_CENSUS_MS): per Sung Ma map - the bots, each element
//    of the map (25%+): the steady resistance capped at 80, average / median; the gate and the bots meeting it; the
//    median Max HP; the talismans whose line is one of the map's elements (any / at its top) and those moved off the
//    hunt element; Kamien Ochrony Zywiolow worn; and since the start: the talisman's switches, the gate's looks, the
//    builders, the bonus pass's stones by what they went to (the element phase / a Max HP must piece / other).
//
// Switches (event flags, read every 5 s): m2_bot_yresist_tal_off (1: the talisman's must is the hunt element again),
// m2_bot_sungma_gate_off (1: no Sung Ma element gate), m2_bot_sungma_gate_<map> (over 0: that map's step-on value, the
// stay value 5 under it - a map not in the table takes a gate this way too, on its talisman-only element).
// The log: PLAYERBOT_YRESIST - "talisman" (a bot's talisman element changed, throttled), "gate" (a bot's gate decision
// changed, throttled), "census".
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_element_pet.h, in the anonymous
// namespace; the declarations the earlier fragments use are in playerbot_types.h.

namespace
{
	const int PLAYERBOT_YRESIST_CAP = 80;
	const int PLAYERBOT_YRESIST_SHARE_MIN = 25;
	const int PLAYERBOT_YRESIST_TAL_LINE = 25;
	const int PLAYERBOT_YRESIST_TAL_HYSTERESIS = 250;
	const int PLAYERBOT_YRESIST_GATE_STAY_SLACK = 5;
	const DWORD PLAYERBOT_YRESIST_FLAGS_MS = 5000;
	const DWORD PLAYERBOT_YRESIST_TAL_CACHE_MS = 30 * 1000;
	const DWORD PLAYERBOT_YRESIST_BUILD_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_YRESIST_TICK_MS = 30 * 1000;
	const DWORD PLAYERBOT_YRESIST_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_YRESIST_SEEN_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_YRESIST_STONE_VNUM = 39120;	// Kamien Ochrony Zywiolow (playerbot_element_stones.h)

	// The Sung Ma maps with an element gate: the step-on value and the stay value of the map's talisman-only element.
	struct TPlayerBotSungmaGateRow { long lMap; int iGate; int iStay; };
	const TPlayerBotSungmaGateRow PLAYERBOT_SUNGMA_GATE_ROWS[] = {
		{ PLAYERBOT_MAP_SUNGMA_WAWOZ, 40, 35 },	// ice (the owner, 7 November: "zrob wymagany zywiol")
	};
	const int PLAYERBOT_SUNGMA_GATE_ROW_COUNT = (int)(sizeof(PLAYERBOT_SUNGMA_GATE_ROWS) / sizeof(PLAYERBOT_SUNGMA_GATE_ROWS[0]));

	struct TPlayerBotYResistFlags
	{
		DWORD dwAt;
		bool bTalOff, bGateOff;
		std::map<long, int> mapGate;	// m2_bot_sungma_gate_<map> over 0
		TPlayerBotYResistFlags() : dwAt(0), bTalOff(false), bGateOff(false) {}
	};
	TPlayerBotYResistFlags s_kPlayerBotYResistFlags;

	const TPlayerBotYResistFlags& GetPlayerBotYResistFlags()
	{
		TPlayerBotYResistFlags& f = s_kPlayerBotYResistFlags;
		const DWORD now = get_dword_time();
		if (f.dwAt != 0 && now - f.dwAt < PLAYERBOT_YRESIST_FLAGS_MS)
			return f;
		f.dwAt = now ? now : 1;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		f.bTalOff = q.GetEventFlag("m2_bot_yresist_tal_off") != 0;
		f.bGateOff = q.GetEventFlag("m2_bot_sungma_gate_off") != 0;
		f.mapGate.clear();
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT; ++i)
		{
			char name[48];
			snprintf(name, sizeof(name), "m2_bot_sungma_gate_%ld", PLAYERBOT_YOHARA_ELEMENT_MAPS[i].lMap);
			const int v = q.GetEventFlag(name);
			if (v > 0)
				f.mapGate[PLAYERBOT_YOHARA_ELEMENT_MAPS[i].lMap] = std::min(v, PLAYERBOT_YRESIST_CAP);
		}
		return f;
	}

	struct TPlayerBotYResistBot
	{
		// the talisman's element (1)
		int iTal;
		DWORD dwTalAt;
		const char* szTalWhy;
		// a builder for a gated map (2)
		long lBuildMap;
		int iBuildElement;
		DWORD dwBuildAt;
		// the gate's last logged decision
		long lGateMap;
		int iGateDecision;
		// the census's look (3)
		DWORD dwNextTick, dwSeen;
		long lSeenMap;
		int aiResist[PLAYERBOT_YOHARA_ELEMENTS];	// steady, capped
		long lMaxHp;
		int iHunt, iTalLook;
		long lTalLine, lTalTop;
		bool bStone;
		TPlayerBotYResistBot() : iTal(-1), dwTalAt(0), szTalWhy("-"), lBuildMap(0), iBuildElement(-1), dwBuildAt(0), lGateMap(0),
			iGateDecision(-1), dwNextTick(0), dwSeen(0), lSeenMap(0), lMaxHp(0), iHunt(-1), iTalLook(-1), lTalLine(0), lTalTop(0),
			bStone(false)
		{
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				aiResist[e] = 0;
		}
	};
	std::map<DWORD, TPlayerBotYResistBot> s_mapPlayerBotYResist;

	struct TPlayerBotYResistStats
	{
		unsigned int talSwitches, talBuild, talGate, talBest, talBack;
		unsigned int gatePass, gateRefused, gateStayShort, gateBuilt;
		unsigned int changes[3], adds[3];	// the element phase, a Max HP must piece, other
		DWORD dwCensusAt;
		TPlayerBotYResistStats() : talSwitches(0), talBuild(0), talGate(0), talBest(0), talBack(0), gatePass(0), gateRefused(0),
			gateStayShort(0), gateBuilt(0), dwCensusAt(0)
		{
			for (int i = 0; i < 3; ++i)
				changes[i] = adds[i] = 0;
		}
	};
	TPlayerBotYResistStats s_kPlayerBotYResistStats;

	long GetPlayerBotYResistBase(long map)
	{
		return map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? map / 10000 : map;
	}

	const char* GetPlayerBotYResistElementName(int e)
	{
		return e >= 0 && e < PLAYERBOT_YOHARA_ELEMENTS ? PLAYERBOT_YOHARA_ELEMENT_NAMES[e] : "-";
	}

	// The bot's steady resistance to the element (uncapped): every source GetPoint and the 6th/7th "+x%" lines count
	// (Bonus67Total), less an elixir's affect (it runs out in ten minutes), with the dragon stones' best deck while the
	// deck is off (on only around a fight, playerbot_alchemy.h).
	int GetPlayerBotYResistSteady(LPCHARACTER ch, int e)
	{
		const BYTE point = GetPlayerBotElementResistPoint(e);
		if (!ch || !point)
			return 0;
		long total = Bonus67Total(ch, point);
		CAffect* elixir = ch->FindAffect(AFFECT_BLEND, point);
		if (elixir)
			total -= elixir->lApplyValue;
		if (ch->DragonSoul_GetActiveDeck() < 0)
			total += GetPlayerBotDsDeckResist(ch, point, false);
		return (int)std::max(0L, total);
	}

	// The map's element only a talisman holds (ice, earth, dark), of a share of PLAYERBOT_YRESIST_SHARE_MIN or more - the
	// largest; -1 none.
	int GetPlayerBotSungmaGateElement(long map)
	{
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(GetPlayerBotYResistBase(map), share))
			return -1;
		int best = -1;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (share[e] >= PLAYERBOT_YRESIST_SHARE_MIN && !IsPlayerBotElementOnGear(e) && (best < 0 || share[e] > share[best]))
				best = e;
		return best;
	}

	// The gate's value on the map (stay: the stay's), 0 for none.
	int GetPlayerBotSungmaGateValue(long map, bool stay)
	{
		const TPlayerBotYResistFlags& f = GetPlayerBotYResistFlags();
		if (f.bGateOff)
			return 0;
		const long base = GetPlayerBotYResistBase(map);
		std::map<long, int>::const_iterator o = f.mapGate.find(base);
		if (o != f.mapGate.end())
			return stay ? std::max(0, o->second - PLAYERBOT_YRESIST_GATE_STAY_SLACK) : o->second;
		for (int i = 0; i < PLAYERBOT_SUNGMA_GATE_ROW_COUNT; ++i)
			if (PLAYERBOT_SUNGMA_GATE_ROWS[i].lMap == base)
				return stay ? PLAYERBOT_SUNGMA_GATE_ROWS[i].iStay : PLAYERBOT_SUNGMA_GATE_ROWS[i].iGate;
		return 0;
	}

	enum { PLAYERBOT_YRESIST_GATE_PASS = 0, PLAYERBOT_YRESIST_GATE_REFUSE, PLAYERBOT_YRESIST_GATE_STAY_SHORT };

	// (2) From PickPlayerBotSungmaMap: may the bot step on (stay on) the map?
	bool PassPlayerBotSungmaElementGate(LPCHARACTER ch, long map, bool stay)
	{
		if (!ch)
			return true;
		const long base = GetPlayerBotYResistBase(map);
		const int gate = GetPlayerBotSungmaGateValue(base, stay);
		const int e = gate > 0 ? GetPlayerBotSungmaGateElement(base) : -1;
		if (e < 0)
			return true;
		const int resist = std::min(GetPlayerBotYResistSteady(ch, e), PLAYERBOT_YRESIST_CAP);
		const bool pass = resist >= gate;
		const DWORD now = get_dword_time();
		TPlayerBotYResistBot& b = s_mapPlayerBotYResist[ch->GetPlayerID()];
		const int decision = pass ? PLAYERBOT_YRESIST_GATE_PASS : (stay ? PLAYERBOT_YRESIST_GATE_STAY_SHORT : PLAYERBOT_YRESIST_GATE_REFUSE);
		TPlayerBotYResistStats& st = s_kPlayerBotYResistStats;
		if (pass)
		{
			++st.gatePass;
			if (b.lBuildMap == base)
			{
				++st.gateBuilt;
				b.lBuildMap = 0;
				b.iBuildElement = -1;
			}
		}
		else
		{
			++(stay ? st.gateStayShort : st.gateRefused);
			b.lBuildMap = base;
			b.iBuildElement = e;
			b.dwBuildAt = now ? now : 1;
			b.dwTalAt = 0;	// the talisman's element asked again now
		}
		if (b.lGateMap != base || b.iGateDecision != decision)
		{
			static const char* const s_aszDecisions[3] = { "pass", "refuse", "stay_short" };
			LPITEM tal = ch->GetWear(WEAR_PENDANT);
			PlayerBotLogThrottled(pass ? "yresist_gate_pass" : "yresist_gate_short", now,
					"PLAYERBOT_YRESIST: gate pid=%u name=%s champion=%d map=%ld here=%ld element=%s resist=%d gate=%d stay=%d "
					"decision=%s talisman=%s:%ld",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetConquerorLevel(), base, ch->GetMapIndex(),
					GetPlayerBotYResistElementName(e), resist, gate, stay ? 1 : 0, s_aszDecisions[decision],
					GetPlayerBotYResistElementName(b.iTal), tal ? GetPlayerBotYoharaPieceLine(tal, GetPlayerBotElementResistPoint(b.iTal)) : -1L);
			b.lGateMap = base;
			b.iGateDecision = decision;
		}
		return pass;
	}

	// (1) The talisman's element now: why - "hunt", "build", "gate", "best", "kept", "off".
	int ChoosePlayerBotTalismanResistElement(LPCHARACTER ch, TPlayerBotYResistBot& b, int hunt, int prev, const char*& why)
	{
		why = "hunt";
		const DWORD now = get_dword_time();
		// a builder for a gated map first - whatever its hunt element where it waits (an earth bot on Yilad for Wawoz)
		if (b.lBuildMap != 0 && b.iBuildElement >= 0 && now - b.dwBuildAt < PLAYERBOT_YRESIST_BUILD_MS)
		{
			why = "build";
			return b.iBuildElement;
		}
		const long map = GetPlayerBotYResistBase(GetPlayerBotYoharaElementMap(ch));
		if (map == 0)
		{
			why = "kept";
			return prev;	// a moment off its maps: as it was
		}
		if (GetPlayerBotSungmaGateValue(map, true) > 0)
		{
			const int g = GetPlayerBotSungmaGateElement(map);
			if (g >= 0)
			{
				why = "gate";
				return g;
			}
		}
		if (!IsPlayerBotElementOnGear(hunt))
			return hunt;	// ice, earth, dark: the talisman is its only gear line
		if (map == PLAYERBOT_MAP_SUNGMA_ZEJSCIE)
			return hunt;	// both flags on every monster: the better of the two counts
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(map, share))
			return hunt;
		LPITEM tal = ch->GetWear(WEAR_PENDANT);
		int best = -1;
		long bestGain = -1, prevGain = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			if (share[e] <= 0)
				continue;
			const BYTE point = GetPlayerBotElementResistPoint(e);
			const long line = tal ? GetPlayerBotYoharaPieceLine(tal, point) : 0;
			const long top = tal ? std::max(1L, GetPlayerBotYoharaTopLineValue(tal, point)) : (long)PLAYERBOT_YRESIST_TAL_LINE;
			const long rest = std::max(0L, (long)GetPlayerBotYResistSteady(ch, e) - line);
			const long gain = (long)share[e] * (std::min((long)PLAYERBOT_YRESIST_CAP, rest + top) - std::min((long)PLAYERBOT_YRESIST_CAP, rest));
			if (e == prev)
				prevGain = gain;
			if (gain > bestGain || (gain == bestGain && e == hunt))
			{
				best = e;
				bestGain = gain;
			}
		}
		if (best < 0)
			return hunt;
		// the old choice stays within the hysteresis - while it is an element of this map at all
		if (best != prev && prev >= 0 && share[prev] > 0 && bestGain < prevGain + PLAYERBOT_YRESIST_TAL_HYSTERESIS)
		{
			why = "kept";
			return prev;
		}
		why = best == hunt ? "hunt" : "best";
		return best;
	}

	int GetPlayerBotTalismanResistElement(LPCHARACTER ch)
	{
		const int hunt = GetPlayerBotHuntElementIndex(ch);
		if (!ch || hunt < 0)
			return hunt;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		if (s_dwPlayerBotElementOverridePid != 0 && ch->GetPlayerID() == s_dwPlayerBotElementOverridePid)
			return hunt;	// the second set's talisman: its own element
#endif
		if (GetPlayerBotYResistFlags().bTalOff)
			return hunt;
		TPlayerBotYResistBot& b = s_mapPlayerBotYResist[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (b.iTal >= 0 && b.dwTalAt != 0 && now - b.dwTalAt < PLAYERBOT_YRESIST_TAL_CACHE_MS)
			return b.iTal;
		b.dwTalAt = now ? now : 1;
		const int prev = b.iTal >= 0 ? b.iTal : hunt;
		const char* why = "hunt";
		const int e = ChoosePlayerBotTalismanResistElement(ch, b, hunt, prev, why);
		if (e != prev)
		{
			TPlayerBotYResistStats& st = s_kPlayerBotYResistStats;
			++st.talSwitches;
			if (strcmp(why, "build") == 0)
				++st.talBuild;
			else if (strcmp(why, "gate") == 0)
				++st.talGate;
			else if (e == hunt)
				++st.talBack;
			else
				++st.talBest;
			LPITEM tal = ch->GetWear(WEAR_PENDANT);
			PlayerBotLogThrottled("yresist_talisman", now,
					"PLAYERBOT_YRESIST: talisman pid=%u name=%s champion=%d map=%ld element_map=%ld hunt=%s from=%s to=%s why=%s "
					"resist_from=%d resist_to=%d line_from=%ld line_to=%ld",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetConquerorLevel(), ch->GetMapIndex(),
					GetPlayerBotYoharaElementMap(ch), GetPlayerBotYResistElementName(hunt), GetPlayerBotYResistElementName(prev),
					GetPlayerBotYResistElementName(e), why, GetPlayerBotYResistSteady(ch, prev), GetPlayerBotYResistSteady(ch, e),
					tal ? GetPlayerBotYoharaPieceLine(tal, GetPlayerBotElementResistPoint(prev)) : -1L,
					tal ? GetPlayerBotYoharaPieceLine(tal, GetPlayerBotElementResistPoint(e)) : -1L);
		}
		b.iTal = e;
		b.szTalWhy = why;
		return e;
	}

	// The bonus pass's stones (playerbot_yohara_bonus.h): 0 the element phase, 1 a piece whose must is Max HP, 2 other.
	void NotePlayerBotYoharaBonusSpend(LPCHARACTER ch, BYTE wearCell, bool elementPhase, int changes, int adds)
	{
		if (!ch)
			return;
		const int kind = elementPhase ? 0 : (wearCell == WEAR_BODY || wearCell == WEAR_WRIST || wearCell == WEAR_NECK ||
				wearCell == WEAR_FOOTS) ? 1 : 2;
		s_kPlayerBotYResistStats.changes[kind] += (unsigned int)std::max(0, changes);
		s_kPlayerBotYResistStats.adds[kind] += (unsigned int)std::max(0, adds);
	}

	int GetPlayerBotYResistMedian(std::vector<long>& v)
	{
		if (v.empty())
			return 0;
		std::nth_element(v.begin(), v.begin() + v.size() / 2, v.end());
		return (int)v[v.size() / 2];
	}

	// (3) Every PLAYERBOT_YRESIST_CENSUS_MS: the Sung Ma maps' bots seen in the last PLAYERBOT_YRESIST_SEEN_MS.
	void TickPlayerBotYResistCensus(DWORD dwNow)
	{
		TPlayerBotYResistStats& st = s_kPlayerBotYResistStats;
		if (st.dwCensusAt == 0)
		{
			st.dwCensusAt = dwNow + PLAYERBOT_YRESIST_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - st.dwCensusAt) < 0)
			return;
		st.dwCensusAt = dwNow + PLAYERBOT_YRESIST_CENSUS_MS;
		int builders = 0;
		std::string line;
		for (int slot = 0; slot < PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT; ++slot)
		{
			const long map = PLAYERBOT_YOHARA_ELEMENT_MAPS[slot].lMap;
			int share[PLAYERBOT_YOHARA_ELEMENTS];
			GetPlayerBotYoharaMapShares(map, share);
			const int gateE = GetPlayerBotSungmaGateElement(map);
			const int gate = gateE >= 0 ? GetPlayerBotSungmaGateValue(map, false) : 0;
			std::vector<long> resist[PLAYERBOT_YOHARA_ELEMENTS], hp;
			long long sum[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
			int bots = 0, meetGate = 0, talMap = 0, talTop = 0, talMoved = 0, stone = 0;
			for (std::map<DWORD, TPlayerBotYResistBot>::const_iterator it = s_mapPlayerBotYResist.begin();
					it != s_mapPlayerBotYResist.end(); ++it)
			{
				const TPlayerBotYResistBot& b = it->second;
				if (b.dwSeen == 0 || dwNow - b.dwSeen > PLAYERBOT_YRESIST_SEEN_MS || b.lSeenMap != map)
					continue;
				++bots;
				for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
					if (share[e] >= PLAYERBOT_YRESIST_SHARE_MIN)
					{
						resist[e].push_back(b.aiResist[e]);
						sum[e] += b.aiResist[e];
					}
				hp.push_back(b.lMaxHp);
				meetGate += gate > 0 && b.aiResist[gateE] >= gate ? 1 : 0;
				if (b.iTalLook >= 0 && share[b.iTalLook] >= PLAYERBOT_YRESIST_SHARE_MIN && b.lTalLine > 0)
				{
					++talMap;
					talTop += b.lTalTop > 0 && b.lTalLine >= b.lTalTop ? 1 : 0;
				}
				talMoved += b.iTalLook >= 0 && b.iHunt >= 0 && b.iTalLook != b.iHunt ? 1 : 0;
				stone += b.bStone ? 1 : 0;
			}
			if (bots == 0)
				continue;
			std::string el;
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			{
				if (resist[e].empty())
					continue;
				char one[64];
				snprintf(one, sizeof(one), "%s%s:%lld/%d", el.empty() ? "" : ",", PLAYERBOT_YOHARA_ELEMENT_NAMES[e],
						sum[e] / (long long)resist[e].size(), GetPlayerBotYResistMedian(resist[e]));
				el += one;
			}
			char buf[384];
			snprintf(buf, sizeof(buf), " %ld=[bots=%d resist_avg/med=%s gate=%s:%d meet=%d/%d hp_med=%d tal_map=%d tal_top=%d "
					"tal_moved=%d stone=%d]", map, bots, el.c_str(), GetPlayerBotYResistElementName(gate > 0 ? gateE : -1), gate,
					gate > 0 ? meetGate : 0, bots, GetPlayerBotYResistMedian(hp), talMap, talTop, talMoved, stone);
			line += buf;
		}
		for (std::map<DWORD, TPlayerBotYResistBot>::iterator it = s_mapPlayerBotYResist.begin(); it != s_mapPlayerBotYResist.end();)
		{
			const TPlayerBotYResistBot& b = it->second;
			const bool building = b.lBuildMap != 0 && dwNow - b.dwBuildAt < PLAYERBOT_YRESIST_BUILD_MS;
			builders += building ? 1 : 0;
			// forgotten: unseen for an hour and no talisman look for an hour
			if (dwNow - b.dwSeen > 60 * 60 * 1000 && dwNow - b.dwTalAt > 60 * 60 * 1000 && !building)
				s_mapPlayerBotYResist.erase(it++);
			else
				++it;
		}
		const TPlayerBotYResistFlags& f = GetPlayerBotYResistFlags();
		sys_log(0, "PLAYERBOT_YRESIST: census tal=%s gate=%s talisman_switches=%u [build=%u gate=%u best=%u back=%u] "
				"gate_looks=[pass=%u refused=%u stay_short=%u built=%u] builders=%d stones=[element=%u/%u hp_piece=%u/%u other=%u/%u] "
				"(changes/adds since start)%s",
				f.bTalOff ? "off" : "on", f.bGateOff ? "off" : "on", st.talSwitches, st.talBuild, st.talGate, st.talBest, st.talBack,
				st.gatePass, st.gateRefused, st.gateStayShort, st.gateBuilt, builders, st.changes[0], st.adds[0], st.changes[1],
				st.adds[1], st.changes[2], st.adds[2], line.c_str());
	}

	// From the top of every tick: a Yohara bot standing on a Sung Ma map is looked at every PLAYERBOT_YRESIST_TICK_MS.
	void ManagePlayerBotYoharaResistTick(LPCHARACTER ch, DWORD dwNow)
	{
		TickPlayerBotYResistCensus(dwNow);
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead())
			return;
		const long here = GetPlayerBotYResistBase(ch->GetMapIndex());
		if (GetPlayerBotYoharaElementSlot(here) < 0 || !IsPlayerBotYoharaBonusMember(ch))
			return;
		TPlayerBotYResistBot& b = s_mapPlayerBotYResist[ch->GetPlayerID()];
		if (b.dwNextTick != 0 && (int)(dwNow - b.dwNextTick) < 0)
			return;
		b.dwNextTick = dwNow + PLAYERBOT_YRESIST_TICK_MS;
		b.dwSeen = dwNow ? dwNow : 1;
		b.lSeenMap = here;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			b.aiResist[e] = std::min(GetPlayerBotYResistSteady(ch, e), PLAYERBOT_YRESIST_CAP);
		b.lMaxHp = ch->GetMaxHP();
		b.iHunt = GetPlayerBotHuntElementIndex(ch);
		b.iTalLook = GetPlayerBotTalismanResistElement(ch);
		LPITEM tal = ch->GetWear(WEAR_PENDANT);
		const BYTE point = GetPlayerBotElementResistPoint(b.iTalLook);
		b.lTalLine = tal && point ? GetPlayerBotYoharaPieceLine(tal, point) : 0;
		b.lTalTop = tal && point ? GetPlayerBotYoharaTopLineValue(tal, point) : 0;
		b.bStone = false;
		for (int cell = 0; cell < WEAR_MAX_NUM && !b.bStone; ++cell)
		{
			LPITEM item = ch->GetWear(cell);
			b.bStone = item && item->GetVnum() == PLAYERBOT_YRESIST_STONE_VNUM;
		}
	}
}

#endif
