#ifndef PLAYERBOT_YOHARA_BONUS_RULES_H
#define PLAYERBOT_YOHARA_BONUS_RULES_H
// MT2009_PLUS_BOT_YOHARA_BONUS_V1 - the pure half of a Yohara bot bonusing its own gear with the stones it holds
// (Wzmocnienie Przedmiotu 71085 adds a line, Zaczarowanie Przedmiotu 71084 rerolls them all, the Marmur
// Blogoslawienstwa the fifth): which piece the next stone goes on, which stone, and when a piece is done. No engine
// types: playerbot_yohara_bonus.h reads the pieces, the bag and the lines, asks here, and spends the stone named.
//
// The owner, 27 October 2026: "Nie bonuj EQ, daj im po 400 wzmocnien przedmiotow i po 800 zaczarowan przedmiotow,
// tak aby samodzielnie wybonowaly sobie potrzebny im EQ na Yohare."
//
//   1. Fill first: an empty line is free power, and a change keeps the count - so every piece takes adds (in the
//      priority order) until it has four lines (the engine's add stops at four: USE_ADD_ATTRIBUTE), then a marble
//      gives the fifth where the bag holds one (USE_ADD_ATTRIBUTE2, on a piece of exactly four).
//   2. Then the changes, one piece at a time in the priority order (weapon, armour, helmet, the jewellery, the
//      earrings, the shield, the glove), each to its target (TIER_STRONG) and never again once it is there - a change
//      rerolls every line and can lose what a piece has.
//   3. A budget per piece, so one piece cannot burn the stock: the pool (the change stones held plus those already
//      spent on the pieces worn now, less a reserve kept for the next pieces the bot will wear) shared by the slots'
//      weights. Over half of its share a piece settles for the fair tier; at its share it stops.
//   4. The leftover: once no piece wants a change within its share, what is left over the reserve goes first to a
//      piece below the fair tier, then - only while the bag holds a safety margin over the reserve, since a reroll
//      can drop a fair piece back below fair - to the fair piece that has had the fewest stones for its weight, up
//      to three of its shares in all (LEFTOVER_SHARES).
//
// MT2009_PLUS_BOT_ELEMENT_RESIST_V2 (the owner, 28 October 2026: the bots' element resistance far too low - "musza
// znacznie lepiej bonowac EQ pod odpornosci"): 2a. the element phase, before the shares - the pieces that carry the
// hunt element's resistance (the engine's half ranks them: talisman, armour, bracelet, helmet) are changed, one at a
// time in that rank, until the line stands at its top level (and the piece's Max HP must at its level), each up to an
// element budget of its own (elemCap, changes on the piece in all). A piece whose element target is met counts as
// strong (the engine's half) and is never changed again; one whose budget ran out goes on by the shares as before.
namespace playerbot_yohara_bonus_rules {

enum ETier { TIER_NONE = 0, TIER_FAIR = 1, TIER_STRONG = 2 };
// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: ROLE_MUST2 - a second must kind of its own (the resistance to the bot's hunt
// element next to the armour's and the bracelet's Max HP): a tier asks each must kind that can roll on the piece.
enum ERole { ROLE_OTHER = 0, ROLE_MUST = 1, ROLE_WANTED = 2, ROLE_MUST2 = 3 };
// The must kinds that can roll on a piece (Meets' mustMask).
enum { MUST_ROLLS_1 = 1, MUST_ROLLS_2 = 2 };
enum EStep { STEP_NONE, STEP_ADD, STEP_MARBLE, STEP_CHANGE };
enum EWant { WANT_NONE, WANT_FAIR, WANT_STRONG };

// A tier: this many lines of the slot's list, the slot's must line (if one can roll on the slot) at mustLevel or
// higher and the others at otherLevel or higher. A level is the item_attr table's (1-5), normalised so that a slot's
// own top level counts as 5 (playerbot_yohara_bonus.h).
struct TTier
{
	int lines;
	int mustLevel;
	int otherLevel;
};

struct TLine
{
	int role;
	int level;
};

// Whether a piece's lines meet a tier. available: how many kinds of the slot's list (must and wanted) can roll on
// the piece at all - a tier never asks more lines than that; mustMask: which must kinds (MUST_ROLLS_1 for ROLE_MUST,
// MUST_ROLLS_2 for ROLE_MUST2) can roll on it - each of those must be there at mustLevel or higher.
inline bool Meets(const TLine* lines, int count, const TTier& tier, int mustMask, int available)
{
	int need = tier.lines < available ? tier.lines : available;
	int found = 0;
	int others = 0;
	for (int i = 0; i < count; ++i)
	{
		const int bit = lines[i].role == ROLE_MUST ? MUST_ROLLS_1 : (lines[i].role == ROLE_MUST2 ? MUST_ROLLS_2 : 0);
		if (bit && !(found & bit) && lines[i].level >= tier.mustLevel)
			found |= bit;
		else if (lines[i].role != ROLE_OTHER && lines[i].level >= tier.otherLevel)
			++others;
	}
	if ((found & mustMask) != mustMask)
		return false;
	const int musts = ((found & MUST_ROLLS_1) ? 1 : 0) + ((found & MUST_ROLLS_2) ? 1 : 0);
	return musts + others >= need;
}

inline int TierOf(const TLine* lines, int count, const TTier& strong, const TTier& fair, int mustMask, int available)
{
	if (count <= 0)
		return TIER_NONE;
	if (Meets(lines, count, strong, mustMask, available))
		return TIER_STRONG;
	if (Meets(lines, count, fair, mustMask, available))
		return TIER_FAIR;
	return TIER_NONE;
}

// A piece's share of the pool.
inline int PieceCap(int weight, int sumWeights, int pool)
{
	if (weight <= 0 || sumWeights <= 0 || pool <= 0)
		return 0;
	return (int)((long long)pool * weight / sumWeights);
}

// Within its share: the strong tier while under half of it, the fair tier up to all of it.
inline EWant MainWant(int tier, int spent, int cap)
{
	if (tier >= TIER_STRONG || cap <= 0)
		return WANT_NONE;
	if (spent * 2 < cap)
		return WANT_STRONG;
	if (spent < cap && tier < TIER_FAIR)
		return WANT_FAIR;
	return WANT_NONE;
}

// Past its share (the leftover, see the head of the file).
inline EWant LeftoverWant(int tier, int changeUnits, int reserve, int safety)
{
	if (tier >= TIER_STRONG)
		return WANT_NONE;
	if (tier < TIER_FAIR)
		return changeUnits > reserve ? WANT_FAIR : WANT_NONE;
	return changeUnits > reserve + safety ? WANT_STRONG : WANT_NONE;
}

// How many of its shares a fair piece may take in all, the leftover included.
const int LEFTOVER_SHARES = 3;

struct TPiece
{
	int lines;
	int maxStoneLines;	// the add stone's ceiling (4)
	bool lineRolls;	// a new line can still land on it (the engine draws among lines it does not carry yet)
	int tier;
	int spent;	// changes spent on it (this world's memory of the pass)
	int weight;
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase - its rank (-1 not in it), whether its element target is
	// short, and its budget (changes on the piece in all)
	int elemRank;
	bool elemShort;
	int elemCap;
	// MT2009_PLUS_BOT_MARBLE_FIRST_V1 (playerbot_marble_first.h): a bot with SM changes this piece not now (short of its
	// five lines - the marble first), and a piece of the 6/7 scope takes the adds and the marble before the rest
	bool changeBlocked = false;
	bool fifthPriority = false;
};

struct TBag
{
	int addUnits;
	int changeUnits;
	bool marble;
};

struct TChoice
{
	int piece;
	EStep step;
	EWant want;
	bool leftover;
	int cap;
	bool element;	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase's change
};

// The pool the shares are cut from: the change stones held, plus those spent on the pieces listed, less the reserve.
inline int Pool(const TPiece* pieces, int count, int changeUnits, int reserve)
{
	long long pool = changeUnits - reserve;
	for (int i = 0; i < count; ++i)
		pool += pieces[i].spent;
	return pool > 0 ? (int)pool : 0;
}

// The next stone. The pieces come in the priority order.
inline TChoice Pick(const TPiece* pieces, int count, const TBag& bag, int reserve, int safety)
{
	TChoice c = { -1, STEP_NONE, WANT_NONE, false, 0, false };
	// 1. the adds, then the marble's fifth line (MT2009_PLUS_BOT_MARBLE_FIRST_V1: the 6/7 scope's pieces first)
	for (int round = 0; round < 2; ++round)
	{
		if (bag.addUnits > 0)
			for (int i = 0; i < count; ++i)
				if ((round == 1 || pieces[i].fifthPriority) && pieces[i].lines < pieces[i].maxStoneLines &&
						pieces[i].lineRolls)
				{
					c.piece = i;
					c.step = STEP_ADD;
					return c;
				}
		if (bag.marble)
			for (int i = 0; i < count; ++i)
				if ((round == 1 || pieces[i].fifthPriority) && pieces[i].lines == pieces[i].maxStoneLines &&
						pieces[i].lineRolls)
				{
					c.piece = i;
					c.step = STEP_MARBLE;
					return c;
				}
	}
	// the reserve is the next pieces' (a new weapon, a new armour), never spent on these
	if (bag.changeUnits <= reserve)
		return c;
	// 2a. MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase - the best ranked piece short of its element target,
	// within its element budget
	int elem = -1;
	for (int i = 0; i < count; ++i)
		if (pieces[i].lines > 0 && !pieces[i].changeBlocked && pieces[i].elemRank >= 0 && pieces[i].elemShort &&
				pieces[i].spent < pieces[i].elemCap &&
				(elem < 0 || pieces[i].elemRank < pieces[elem].elemRank))
			elem = i;
	if (elem >= 0)
	{
		c.piece = elem;
		c.step = STEP_CHANGE;
		c.want = WANT_STRONG;
		c.cap = pieces[elem].elemCap;
		c.element = true;
		return c;
	}
	int sumWeights = 0;
	for (int i = 0; i < count; ++i)
		if (pieces[i].lines > 0)
			sumWeights += pieces[i].weight;
	const int pool = Pool(pieces, count, bag.changeUnits, reserve);
	// 2. the changes within each piece's share
	for (int i = 0; i < count; ++i)
	{
		if (pieces[i].lines <= 0 || pieces[i].changeBlocked)
			continue;
		const int cap = PieceCap(pieces[i].weight, sumWeights, pool);
		const EWant want = MainWant(pieces[i].tier, pieces[i].spent, cap);
		if (want != WANT_NONE)
		{
			c.piece = i;
			c.step = STEP_CHANGE;
			c.want = want;
			c.cap = cap;
			return c;
		}
	}
	// 3. the leftover: a piece below fair first, then the fair piece with the fewest stones for its weight
	int best = -1;
	long long bestRatio = 0;
	for (int i = 0; i < count; ++i)
	{
		if (pieces[i].lines <= 0 || pieces[i].changeBlocked)
			continue;
		const EWant want = LeftoverWant(pieces[i].tier, bag.changeUnits, reserve, safety);
		if (want == WANT_FAIR)
		{
			best = i;
			break;
		}
		// a fair piece takes the leftover up to LEFTOVER_SHARES of its share, no more: the rest waits for the next
		// pieces the bot will wear
		if (want == WANT_STRONG &&
				pieces[i].spent < LEFTOVER_SHARES * PieceCap(pieces[i].weight, sumWeights, pool))
		{
			const long long ratio = (long long)pieces[i].spent * 1000 / (pieces[i].weight > 0 ? pieces[i].weight : 1);
			if (best < 0 || ratio < bestRatio)
			{
				best = i;
				bestRatio = ratio;
			}
		}
	}
	if (best >= 0)
	{
		c.piece = best;
		c.step = STEP_CHANGE;
		c.want = LeftoverWant(pieces[best].tier, bag.changeUnits, reserve, safety);
		c.leftover = true;
		c.cap = PieceCap(pieces[best].weight, sumWeights, pool);
	}
	return c;
}

} // namespace playerbot_yohara_bonus_rules

#endif
