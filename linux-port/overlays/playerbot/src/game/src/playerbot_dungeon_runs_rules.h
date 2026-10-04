#ifndef __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_RULES_H__
#define __INC_METIN2_PLAYERBOT_DUNGEON_RUNS_RULES_H__

// MT2009_PLUS_BOT_DUNGEON_RUNS_V1 - the bots' own dungeon runs (the pure half).
//
// The owner, 4 October: "Do wersji na githuba niech wszystkie boty lataja na
// dungeony zgodnie ze swoimi lvl, niech zwoluja sobie party i chodza
// normalnie". The engine half (playerbot_dungeon_runs.h) picks the dungeon,
// the kingdom and the bots, moves them and runs the instance; this file is
// what can be said and decided without the engine, so it can be tested on
// its own:
//
//   - the level band of a run: the dungeon's level to fifteen above it (the
//     dungeon finder's, PLAYERBOT_LFG_LEVEL_SPAN), capped by the dungeon's own
//     upper level;
//   - the party: drawn by weight from the bots of the band, with no more of
//     one class than a third of the party (two at least), and a Shaman in it
//     whenever one answered - its buffs and heals are what keep the others
//     standing;
//   - the lines: the leader's call on the kingdom's shout ("szukam pt na
//     biblioteke 30-45 lvl", "zbieram ekipe na razadora, kto chetny?"), the
//     answers ("ja", "biore", "wbijam, 52 sura wp"), the start, the end - won
//     or lost - and the polite disband when nobody came, each from parts that
//     combine into many variants, in the bots' chat hand (playerbot_lfg's
//     markup: a backtick before a letter is its Polish form, rendered for the
//     bots that write them).
//
// This file itself stays ASCII.

#include <algorithm>
#include <vector>

#include "playerbot_dungeon_lfg_rules.h"

namespace playerbot_dgrun
{
	typedef unsigned int u32;
	using playerbot_conv::TRng;

	// The band: the dungeon's level to this much above it.
	const int LEVEL_SPAN = 15;
	// A party: the call wants at least PREFER_MIN and at most PARTY_MAX; a
	// gathering goes in with START_MIN of them, and a call is made only when
	// CALL_MIN bots of the band are free.
	const int START_MIN = 3;
	const int PREFER_MIN = 4;
	const int PARTY_MAX = 8;
	const int CALL_MIN = 4;

	inline int BandMax(int lvMin, int levelCap)
	{
		const int top = lvMin + LEVEL_SPAN;
		return levelCap > 0 && levelCap < top ? levelCap : top;
	}

	inline bool InBand(int level, int lvMin, int lvMax)
	{
		return level >= lvMin && level <= lvMax;
	}

	// How many a call asks for, from what the band offers and the dungeon's
	// own party limits.
	inline int PartyWant(TRng& rng, int available, int partyMin, int partyMax)
	{
		int hi = std::min(PARTY_MAX, partyMax > 0 ? partyMax : PARTY_MAX);
		int lo = std::max(PREFER_MIN, partyMin);
		if (hi < lo)
			hi = lo;
		int want = lo + (int)rng.Range((u32)(hi - lo + 1));
		if (want > available)
			want = available;
		return want;
	}

	// A bot of the band, as the draw sees it.
	struct TCand
	{
		u32 pid;
		int level;
		int job;	// 0 warrior, 1 ninja, 2 sura, 3 shaman
		int weight;
		TCand() : pid(0), level(0), job(0), weight(1) {}
		TCand(u32 p, int l, int j, int w) : pid(p), level(l), job(j), weight(w) {}
	};

	inline int MaxPerJob(size_t want)
	{
		return std::max(2, (int)((want + 2) / 3));
	}

	// The party: `want` of them drawn by weight, the first the leader. A class
	// that already has its share is passed over while another can still be
	// drawn, and the last drawn non-Shaman gives way to a Shaman when the
	// party has none and one is free.
	inline void PickParty(const std::vector<TCand>& all, size_t want, TRng& rng, std::vector<TCand>& out)
	{
		out.clear();
		std::vector<TCand> pool(all);
		if (want > pool.size())
			want = pool.size();
		const int cap = MaxPerJob(want);
		int perJob[4] = { 0, 0, 0, 0 };
		while (out.size() < want && !pool.empty())
		{
			// The ones whose class still has room; everybody when none has.
			std::vector<size_t> open;
			for (size_t i = 0; i < pool.size(); ++i)
				if (perJob[pool[i].job & 3] < cap)
					open.push_back(i);
			if (open.empty())
				for (size_t i = 0; i < pool.size(); ++i)
					open.push_back(i);
			long long total = 0;
			for (size_t i = 0; i < open.size(); ++i)
				total += std::max(1, pool[open[i]].weight);
			long long roll = (long long)rng.Range((u32)std::min<long long>(total, 0x7fffffffLL));
			size_t chosen = open[0];
			for (size_t i = 0; i < open.size(); ++i)
			{
				roll -= std::max(1, pool[open[i]].weight);
				if (roll < 0)
				{
					chosen = open[i];
					break;
				}
			}
			out.push_back(pool[chosen]);
			++perJob[pool[chosen].job & 3];
			pool.erase(pool.begin() + chosen);
		}
		if (perJob[3] == 0 && out.size() >= 2)
		{
			for (size_t i = 0; i < pool.size(); ++i)
				if (pool[i].job == 3)
				{
					out.back() = pool[i];
					break;
				}
		}
	}

	// A bot's own wish to go at all, by its pid: most bots like a dungeon now
	// and then, a few never.
	inline bool IsDungeonGoer(u32 pid, int sharePercent)
	{
		return playerbot_conv::HashStr("dgrun", pid ^ 0x44475255u) % 100u < (u32)sharePercent;
	}

	// ------------------------------------------------------------ the lines

	// What a line is about.
	struct TLine
	{
		std::string key;	// the dungeon (playerbot_lfg::Words)
		std::string botName;
		int level, job, group;
		int lvMin, lvMax;
		int need;		// how many more the call wants
		int minutes;		// how long the run took
		bool wantShaman;
		TLine() : level(0), job(0), group(0), lvMin(0), lvMax(0), need(0), minutes(0), wantShaman(false) {}
	};

	inline std::string Fill(TRng& rng, const TLine& l, std::string markup)
	{
		char buf[16];
		snprintf(buf, sizeof(buf), "%d", l.lvMin);
		playerbot_lfg::ReplaceAll(markup, "$MIN", buf);
		snprintf(buf, sizeof(buf), "%d", l.lvMax);
		playerbot_lfg::ReplaceAll(markup, "$MAX", buf);
		snprintf(buf, sizeof(buf), "%d", l.need > 0 ? l.need : 1);
		playerbot_lfg::ReplaceAll(markup, "$NEED", buf);
		snprintf(buf, sizeof(buf), "%d", l.minutes > 0 ? l.minutes : 1);
		playerbot_lfg::ReplaceAll(markup, "$TIME", buf);
		playerbot_lfg::TFacts f;
		f.level = l.level;
		f.job = l.job;
		f.group = l.group;
		f.botName = l.botName;
		f.key = l.key;
		return playerbot_lfg::Finish(rng, f, markup);
	}

	// The leader's call on the kingdom's shout.
	inline std::string CallLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"szukam pt na $NA $MIN-$MAX lvl, kto ch`etny?",
			"zbieram ekip`e na $NA, kto ch`etny? $MIN-$MAX",
			"pt na $NA, szukam jeszcze $NEED, lvl $MIN+",
			"kto na $NA? zbieram party $MIN-$MAX, pisa`c",
			"lf $NEED na $NA ($MIN-$MAX lvl)",
			"id`e na $NA, brakuje jeszcze ludzi, $MIN-$MAX",
			"robimy $NA? zbieram ekip`e, wej`scie za 2 min",
			"$NA - zbieram pt, kto ma $MIN-$MAX niech pisze",
			"szukam ludzi na $NA, jestem $CLS $LVL",
			"wbijamy na $NA, kto idzie? lvl $MIN-$MAX",
			"ekipa na $NA, zbi`orka pod wej`sciem do $GEN",
			"kto`s ch`etny na $NA? $MIN-$MAX, zaraz wchodzimy",
			"zbieram sk`lad na $NA, wolnych miejsc: $NEED",
			"pt na $NA $MIN-$MAX, wo`lam ch`etnych",
			"LF pt na $NA, lvl $MIN-$MAX, zbi`orka pod wej`sciem",
			"szukam jeszcze $NEED do pt na $NA, kto wbija?",
			"$NA kto? $MIN-$MAX lvl, zbieram",
			"ide na $NA z ekip`a, s`a jeszcze miejsca ($MIN-$MAX)",
		};
		static const char* const shaman[] = {
			"potrzebny szaman na $NA, reszta te`z mile widziana ($MIN-$MAX)",
			"zbieram pt na $NA, szukam szamana i dps, $MIN-$MAX",
			"$NA - brakuje szamana i $NEED dps, lvl $MIN+",
		};
		if (l.wantShaman && rng.Chance(25))
			return Fill(rng, l, playerbot_lfg::Any(rng, shaman));
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}

	// A bot of the band answering the call on the shout.
	inline std::string AnswerLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"ja", "ja!", "bior`e", "ja si`e pisz`e", "wbijam", "ja id`e, $LVL $CLS", "jestem, $CLS $LVL", "mog`e i`s`c",
			"zapisz mnie", "+1", "lec`e pod wej`scie", "ja, $LVL lvl", "dawaj, id`e", "ja ja", "pisz`e si`e",
			"ja na $NA", "jestem ch`etny, $CLS", "ja, $CLS", "id`e z wami", "bior`e si`e, $LVL", "ja, czekajcie",
			"o, ja wbijam", "ja mog`e, $LVL $CLS", "ja, ju`z lec`e",
		};
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}

	// The leader, the party gathered: in.
	inline std::string StartLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"mamy sk`lad, wchodzimy na $NA", "komplet, idziemy", "wbijamy, dzi`eki za zg`loszenia", "pt pe`lne, wchodzimy",
			"ok, sk`lad jest, wchodzimy do $GEN", "zamykam zapisy, idziemy na $NA", "dzi`eki, mamy ekip`e na $NA",
			"jest ekipa, lecimy", "wchodzimy, kto nie zd`a`zy`l ten nast`epnym razem",
		};
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}

	// The leader: nobody (or too few) came.
	inline std::string DisbandLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"nikt nie przyszed`l, rozwi`azuj`e pt", "nie zebra`lo si`e, mo`ze p`o`xniej", "za ma`lo ludzi na $NA, odpuszczam",
			"rozwi`azuj`e ekip`e, sorki", "nic z tego, nie ma ch`etnych na $NA", "dobra, nie ma sk`ladu, innym razem",
			"$NA odpada, za ma`lo os`ob", "sorki ludzie, nie uzbiera`lem pt", "nie ma kompletu, rozwi`azuje",
		};
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}

	// The leader after a run it won.
	inline std::string DoneLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"zrobili`smy $NA w $TIME min, dzi`eki ekipa", "gg, zaliczyli`smy $NA", "gg wp, $NA za nami ($TIME min)",
			"dzi`eki za $NA, dobra ekipa", "koniec, $NA przeszli`smy, dzi`eki wszystkim", "gg, $TIME minut na $NA",
			"przeszli`smy $NA, dzi`eki pt", "gg ez, $NA w $TIME min", "dobra robota, $NA przeszli`smy",
		};
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}

	// The leader after a run that failed.
	inline std::string FailLine(TRng& rng, const TLine& l)
	{
		static const char* const k[] = {
			"nie dali`smy rady na $NA, nast`epnym razem", "wywali`lo nas z $GEN, s`labo", "$NA nie przeszli`smy, trzeba podexpi`c",
			"eh, nie da`lo rady na $NA dzisiaj", "nie wysz`lo na $NA, sorki ekipa", "padli`smy na $NA, nast`epnym razem lepiej",
		};
		return Fill(rng, l, playerbot_lfg::Any(rng, k));
	}
}

#endif
