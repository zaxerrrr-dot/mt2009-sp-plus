#ifndef __INC_METIN2_PLAYERBOT_NEWPET_BOTS_H__
#define __INC_METIN2_PLAYERBOT_NEWPET_BOTS_H__

// MT2009_PLUS_NEWPET_BOTS_V2 - the bots and the growth pet (MT2009_PLUS_GROWTH_PET_V1, growth_pet.cpp; the old
// MT2009_PLUS_NEWPET_BOTS_V1 of the retired New Pet System rebuilt on it, the owner, 4 November 2026: "bots may keep
// pets"). A bot never has the pet window: it calls the window's code paths of namespace growth_pet for its own seals -
// Hatch, ToggleSummon, FeedLife, FeedItemExp, UseTastyTreat, Evolve, LearnSkill, UpgradeSkill - so every rule of the
// system (levels never above the owner's, the wiki's evolution materials and ages, the prices) holds for bots too.
//
// Who: PLAYERBOT_NEWPET_SHARE_PERCENT of the bots (by player id) from PLAYERBOT_NEWPET_MIN_LEVEL, and a player's
// companion (playerbot_sidekick.h). What a keeper does at a look (every PLAYERBOT_NEWPET_LOOK_MIN_MS to _MAX_MS):
//   - no pet: hatches its best egg (PLAYERBOT_NEWPET_EGG_RANK; the weak Malpiszon / Pajak only when no other can be
//     had); with no egg it buys a good one off a counter;
//   - a dead pet: Odzywka (the 50 % revive); a living one under PLAYERBOT_NEWPET_FEED_BELOW_PCT of its life: Odzywka;
//   - the pet out whenever it lives and its level allows; it takes the kill experience by itself (growth_pet.cpp);
//   - the item experience (the blue bar): Smakolyk, Smakolyk+, else the bag's junk weapons and armour (what the bot
//     would sell to the merchant); Smaczny Smakolyk eaten at once;
//   - evolution when the level / age / experience allow and the stage's materials are in the bag (bought off the
//     counters when the step is reachable);
//   - skills from Bohaterski: the chosen books (GetPlayerBotNewPetSkills) into the open slots, one level a look for
//     2 000 000 Yang while the purse keeps PLAYERBOT_NEWPET_SKILL_RESERVE over its reserve.
// What it does not use goes on its counter (GetPlayerBotNewPetKeep, one unit a line). Included once, from
// playerbot_manager.cpp, after playerbot_newpet.h and before playerbot_energy_shards.h and playerbot_economy.h.
//
// MT2009_PLUS_BOT_PET_GROW_V1 (the owner, 6 November 2026: "boty maja dostawac, wykluwac, karmic i rozwijac pety"):
// on the test world 34 of 396 keepers a core had a pet. The cause was the pets' ids, not the bots: the old system's
// pets got ids from 0xF0000000, a seal's socket is a 32-bit long in this engine, and the seal kept 0 at its first save
// (MT2009_PLUS_GROWTH_PET_ID_FIX_V1, pety.sql pety:id_fix_v1 gives the 605 seals their pets back). The bots without an
// egg had no road to one but a good egg on a counter (nearly none stand there). What this adds, each with a switch:
//   egg      (m2_bot_pet_egg_off) a keeper with no pet and no egg takes a weak egg off a counter when no good one can be
//            had, and after PLAYERBOT_NEWPET_BOX_WAIT_MS without one (or at once when no counter holds any egg) buys a
//            Skrzynka na Zwierzaka (55400) in the ItemShop V3 pets tab with its weekly Smocze Monety (the catalogue's
//            NEWPET need) - the chest pass opens it, the look hatches what came out;
//   evolve   (m2_bot_pet_evolve_off) the next stage's materials are kept from the bag's drops and bought off the
//            counters from PLAYERBOT_NEWPET_NEAR_LEVELS levels (PLAYERBOT_NEWPET_NEAR_CHAMPION_LEVELS champion levels)
//            before the step, not only once it is ready; off: no evolution at all;
//   books    (m2_bot_pet_books_off) a Bohaterski+ pet with an open slot reads its wanted books first and, after
//            PLAYERBOT_NEWPET_BOOK_WAIT_MS with the slot still open, any book it holds; with no book to read it buys a
//            Skrzynia Ksiag Zwierza (55009, the pets tab) - its book is read or goes on the counter;
//   potential (m2_bot_pet_potential_off) a champion's open, empty potential slot gets an egg (a weak one first, one off
//            a counter when the bag has none to spare) - the window's own add (growth_pet::FillPotential).
// m2_bot_pet_grow_off: all four. The census: one BOT_PETGROW line with the PLAYERBOT_NEWPET one (every
// PLAYERBOT_NEWPET_CENSUS_MS): keepers, have_pet, eggs, hatched, the stages, the books learned, the potential.

namespace
{
	DWORD GetPlayerBotShopAskingPrice(LPITEM item);
	bool PlayerBotHasGrandMasterToTrain(LPCHARACTER ch);
	bool IsPlayerBotJunkItem(LPCHARACTER ch, LPITEM item);

	const int PLAYERBOT_NEWPET_SHARE_PERCENT = 50;
	const int PLAYERBOT_NEWPET_MIN_LEVEL = 30;
	const DWORD PLAYERBOT_NEWPET_EGG_PRICE = 2000000;
	DWORD ScalePlayerBotIwakuraPrice(DWORD base);
	DWORD GetPlayerBotNewPetEggPrice()
	{
		return ScalePlayerBotIwakuraPrice(PLAYERBOT_NEWPET_EGG_PRICE);
	}
	const DWORD PLAYERBOT_NEWPET_LOOK_MIN_MS = 90 * 1000;
	const DWORD PLAYERBOT_NEWPET_LOOK_MAX_MS = 180 * 1000;
	const DWORD PLAYERBOT_NEWPET_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_NEWPET_FEED_BELOW_PCT = 30;
	const int PLAYERBOT_NEWPET_FOOD_KEEP = 4;		// Odzywka
	const int PLAYERBOT_NEWPET_TREAT_KEEP = 3;		// Smakolyk / Smakolyk+ each
	const long long PLAYERBOT_NEWPET_SKILL_RESERVE = 10000000LL;
	const int PLAYERBOT_NEWPET_EGG_PURSE_PERCENT = 60;
	const int PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT = 25;
	const int PLAYERBOT_NEWPET_FAIR_PERCENT = 130;
	const int PLAYERBOT_NEWPET_ACTS_PER_LOOK = 6;
	const DWORD PLAYERBOT_NEWPET_EGG_WORLD_LINES = 100;
	const DWORD PLAYERBOT_NEWPET_WEAK_WAIT_MS = 2 * 60 * 60 * 1000;
	const long long PLAYERBOT_NEWPET_HATCH_PRICE = 100000;

	// MT2009_PLUS_BOT_PET_GROW_V1: the switches (event flags, once a second) and the numbers.
	enum EPlayerBotPetGrow
	{
		PETGROW_EGG = 0,
		PETGROW_EVOLVE,
		PETGROW_BOOKS,
		PETGROW_POTENTIAL,
		PETGROW_COUNT
	};

	bool IsPlayerBotPetGrowOn(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[PETGROW_COUNT] = { false, false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_pet_grow_off") != 0;
			s_abOff[PETGROW_EGG] = all || q.GetEventFlag("m2_bot_pet_egg_off") != 0;
			s_abOff[PETGROW_EVOLVE] = all || q.GetEventFlag("m2_bot_pet_evolve_off") != 0;
			s_abOff[PETGROW_BOOKS] = all || q.GetEventFlag("m2_bot_pet_books_off") != 0;
			s_abOff[PETGROW_POTENTIAL] = all || q.GetEventFlag("m2_bot_pet_potential_off") != 0;
		}
		return part >= 0 && part < PETGROW_COUNT && !s_abOff[part];
	}

	const DWORD PLAYERBOT_NEWPET_BOX_VNUM = 55400;		// Skrzynka na Zwierzaka (the ItemShop's pets tab)
	const DWORD PLAYERBOT_NEWPET_BOOK_BOX_VNUM = 55009;	// Skrzynia Ksiag Zwierza (the ItemShop's pets tab)
	const DWORD PLAYERBOT_NEWPET_BOX_WAIT_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_NEWPET_BOOK_WAIT_MS = 6 * 60 * 60 * 1000;
	const int PLAYERBOT_NEWPET_NEAR_LEVELS = 10;
	const int PLAYERBOT_NEWPET_NEAR_CHAMPION_LEVELS = 5;
	const int PLAYERBOT_NEWPET_BOOK_KEEP_STAGE = 3;	// Dzielny: the books are kept for the Bohaterski step

	const DWORD PLAYERBOT_PET_FOOD = 55001;
	const DWORD PLAYERBOT_PET_TREAT = 55028;
	const DWORD PLAYERBOT_PET_TREAT_PLUS = 55031;
	const DWORD PLAYERBOT_PET_TASTY_TREAT = 55042;

	// The species, best first (the wiki's rare ones first); the weak two last.
	const DWORD PLAYERBOT_NEWPET_EGG_RANK[] = { 55414, 55413, 55412, 55411, 55410, 55406, 55409, 55403, 55404, 55405,
			55408, 55407, 55402, 55401 };

	bool IsPlayerBotNewPetEggVnum(DWORD vnum) { return growth_pet::IsEggVnum(vnum); }

	int GetPlayerBotNewPetEggRank(DWORD vnum)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			if (PLAYERBOT_NEWPET_EGG_RANK[i] == vnum)
				return (int)i;
		return IsPlayerBotNewPetEggVnum(vnum) ? 98 : 99;
	}

	bool IsPlayerBotNewPetWeakEgg(DWORD vnum) { return vnum == 55401 || vnum == 55402; }
	bool IsPlayerBotNewPetGoodEgg(DWORD vnum) { return IsPlayerBotNewPetEggVnum(vnum) && !IsPlayerBotNewPetWeakEgg(vnum); }

	bool IsPlayerBotNewPetBookVnum(DWORD vnum)
	{
		return (vnum >= 55010 && vnum <= 55027) || (vnum >= 55034 && vnum <= 55038);
	}

	int PlayerBotNewPetBookSkill(DWORD vnum)
	{
		if (vnum >= 55010 && vnum <= 55027)
			return (int)(vnum - 55009);
		if (vnum >= 55034 && vnum <= 55038)
			return (int)(vnum - 55034 + 19);
		return 0;
	}

	// The pet goods a counter may hold.
	bool IsPlayerBotNewPetGoodsVnum(DWORD vnum)
	{
		return IsPlayerBotNewPetEggVnum(vnum) || IsPlayerBotNewPetBookVnum(vnum) || vnum == PLAYERBOT_PET_FOOD ||
				vnum == 55002 || vnum == 55008 || vnum == 55009 || vnum == PLAYERBOT_PET_TREAT || vnum == 55029 ||
				vnum == 55030 || vnum == PLAYERBOT_PET_TREAT_PLUS || vnum == 55032 || vnum == 55033 ||
				vnum == PLAYERBOT_PET_TASTY_TREAT || vnum == 55100 || vnum == 55400;
	}

	bool IsPlayerBotNewPetBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() &&
				CPlayerBotManager::instance().IsManaged(ch->GetPlayerID());
	}

	bool IsPlayerBotNewPetCompanion(LPCHARACTER ch)
	{
		return ch && IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	bool IsPlayerBotNewPetKeeper(LPCHARACTER ch)
	{
		if (!IsPlayerBotNewPetBot(ch))
			return false;
		if (IsPlayerBotNewPetCompanion(ch))
			return true;
		if (ch->GetLevel() < PLAYERBOT_NEWPET_MIN_LEVEL)
			return false;
		return (int)(((ch->GetPlayerID() ^ 0x50455453U) * 2654435761U >> 16) % 100U) < PLAYERBOT_NEWPET_SHARE_PERCENT;
	}

	// This core's memory of a keeper's last look (the market's questions must not query).
	struct TPlayerBotNewPetView
	{
		DWORD nextLook;
		bool known;
		bool hasPet;
		growth_pet::PetView pet;
		int nextStage;			// the stage its next evolution goes to (0 = none)
		bool evolveReady;		// level / age / experience met
		DWORD lastSeen;
		DWORD weakWaitSince;
		// MT2009_PLUS_BOT_PET_GROW_V1: the bag at the last look, and the waits
		int eggsGood, eggsWeak, emptySeals;
		DWORD noEggSince;		// no pet and no egg since (0: not so)
		DWORD bookWaitSince;	// an open skill slot and no wanted book since (0: not so)
		TPlayerBotNewPetView() : nextLook(0), known(false), hasPet(false), nextStage(0), evolveReady(false), lastSeen(0),
				weakWaitSince(0), eggsGood(0), eggsWeak(0), emptySeals(0), noEggSince(0), bookWaitSince(0) {}
	};

	std::map<DWORD, TPlayerBotNewPetView> s_mapPlayerBotNewPet;

	struct TPlayerBotNewPetStats
	{
		DWORD hatched, fed, revived, treats, junk, evolved, skills, upgrades, summoned;
		DWORD eggFeeds;	// MT2009_PLUS_BOT_PET_FEED_V1
		DWORD booksAny, potential;	// MT2009_PLUS_BOT_PET_GROW_V1: a held book of another skill read; an egg into potential
		TPlayerBotNewPetStats() : hatched(0), fed(0), revived(0), treats(0), junk(0), evolved(0), skills(0), upgrades(0),
				summoned(0), eggFeeds(0), booksAny(0), potential(0) {}
	};
	TPlayerBotNewPetStats s_kPlayerBotNewPetStats;
	DWORD s_dwPlayerBotNewPetCensusAt = 0;

	const TPlayerBotNewPetView* GetPlayerBotNewPetView(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		std::map<DWORD, TPlayerBotNewPetView>::const_iterator it = s_mapPlayerBotNewPet.find(ch->GetPlayerID());
		return it == s_mapPlayerBotNewPet.end() || !it->second.known ? NULL : &it->second;
	}

	// The skills a bot raises: the monsters' (it hunts), its class's damage, then experience and yang.
	int GetPlayerBotNewPetSkills(LPCHARACTER ch, int out[4])
	{
		out[0] = 20;	// Lowca Potworow
		const int job = (int)ch->GetJob();
		out[1] = (job == JOB_SURA || job == JOB_SHAMAN) ? 7 : 6;	// Antymagia / Berserk
		out[2] = 21;	// Spostrzegawczosc
		out[3] = 15;	// Drop Yang
		return 4;
	}

	bool IsPlayerBotNewPetWantedSkill(LPCHARACTER ch, int skill)
	{
		int wanted[4];
		const int n = GetPlayerBotNewPetSkills(ch, wanted);
		for (int i = 0; i < n; ++i)
			if (wanted[i] == skill)
				return true;
		return false;
	}

	int CountPlayerBotNewPetFreeSlots(const growth_pet::PetView& p)
	{
		int n = 0;
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			if (!p.skillLocked[i] && !p.skill[i])
				++n;
		return n;
	}

	bool PlayerBotPetKnows(const growth_pet::PetView& p, int skill)
	{
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
			if (p.skill[i] == skill)
				return true;
		return false;
	}

	int CountPlayerBotNewPetGoodEggs(LPCHARACTER ch)
	{
		int n = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			if (IsPlayerBotNewPetGoodEgg(PLAYERBOT_NEWPET_EGG_RANK[i]))
				n += (int)ch->CountSpecifyItem(PLAYERBOT_NEWPET_EGG_RANK[i]);
		return n;
	}

	DWORD CountPlayerBotNewPetGoodEggSupply()
	{
		DWORD units = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			if (IsPlayerBotNewPetGoodEgg(PLAYERBOT_NEWPET_EGG_RANK[i]))
				if (const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(PLAYERBOT_NEWPET_EGG_RANK[i]))
					units += e->dwSupplyUnits;
		return units;
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: the eggs of every kind in the bag, and on the counters.
	int CountPlayerBotNewPetEggs(LPCHARACTER ch)
	{
		int n = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			n += (int)ch->CountSpecifyItem(PLAYERBOT_NEWPET_EGG_RANK[i]);
		return n;
	}

	DWORD CountPlayerBotNewPetEggSupply()
	{
		DWORD units = 0;
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			if (const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(PLAYERBOT_NEWPET_EGG_RANK[i]))
				units += e->dwSupplyUnits;
		return units;
	}

	// The champion's open potential slots with no egg working in them.
	int CountPlayerBotNewPetPotentialFree(const TPlayerBotNewPetView& v)
	{
		if (!v.hasPet || !IsPlayerBotPetGrowOn(PETGROW_POTENTIAL))
			return 0;
		int n = 0;
		for (int i = 0; i < v.pet.potentialOpen && i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
			n += v.pet.potentialActive[i] ? 0 : 1;
		return n;
	}

	// The next evolution is within PLAYERBOT_NEWPET_NEAR_LEVELS (champion: _NEAR_CHAMPION_LEVELS) of the pet: its
	// materials are kept and bought from here on.
	bool PlayerBotNewPetStageNear(const TPlayerBotNewPetView& v)
	{
		if (!v.hasPet || !v.nextStage || !IsPlayerBotPetGrowOn(PETGROW_EVOLVE))
			return false;
		const int gate = growth_pet::EvolutionLevel(v.nextStage);
		if (gate <= 0)
			return false;
		if (v.nextStage >= 6)
			return v.pet.championLevel + PLAYERBOT_NEWPET_NEAR_CHAMPION_LEVELS >= gate;
		return v.pet.level + PLAYERBOT_NEWPET_NEAR_LEVELS >= gate;
	}

	bool PlayerBotNewPetStepOpen(const TPlayerBotNewPetView& v)
	{
		return v.evolveReady || PlayerBotNewPetStageNear(v);
	}

	// A book of a skill the pet does not know and an open slot could take (the wanted ones and, after the wait, any).
	bool IsPlayerBotNewPetReadableBook(const TPlayerBotNewPetView& v, DWORD vnum)
	{
		const int skill = PlayerBotNewPetBookSkill(vnum);
		return skill > 0 && v.hasPet && !PlayerBotPetKnows(v.pet, skill) && CountPlayerBotNewPetFreeSlots(v.pet) > 0;
	}

	bool PlayerBotHoldsNewPetReadableBook(LPCHARACTER ch, const TPlayerBotNewPetView& v)
	{
		for (DWORD b = 55010; b <= 55038; ++b)
			if (IsPlayerBotNewPetBookVnum(b) && IsPlayerBotNewPetReadableBook(v, b) && ch->CountSpecifyItem(b) > 0)
				return true;
		return false;
	}

	long long GetPlayerBotNewPetSpare(LPCHARACTER ch)
	{
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return std::max<long long>(0, spare);
	}

	bool PlayerBotNewPetGrowing(const TPlayerBotNewPetView& v)
	{
		return v.hasPet && v.pet.alive && v.pet.itemExp < v.pet.needItemExp;
	}

	// The next evolution's material need (0 when the step is not up or the vnum is not one of it).
	int GetPlayerBotNewPetMaterialNeed(LPCHARACTER ch, const TPlayerBotNewPetView& v, DWORD vnum)
	{
		// MT2009_PLUS_BOT_PET_GROW_V1: from PLAYERBOT_NEWPET_NEAR_LEVELS before the step (was: once it is ready)
		if (!v.hasPet || !PlayerBotNewPetStepOpen(v) || !v.nextStage)
			return 0;
		std::vector<std::pair<DWORD, int> > mats;
		growth_pet::GetEvolutionMaterials(v.nextStage, mats);
		for (size_t i = 0; i < mats.size(); ++i)
			if (mats[i].first == vnum)
			{
				int need = mats[i].second;
				if (vnum == PLAYERBOT_GRAND_MASTER_STONE_VNUM && PlayerBotHasGrandMasterToTrain(ch))
					need += PLAYERBOT_GRAND_MASTER_STONE_KEEP;
				return need;
			}
		return 0;
	}

	bool IsPlayerBotNewPetEvolutionReachable(LPCHARACTER ch, const TPlayerBotNewPetView& v)
	{
		std::vector<std::pair<DWORD, int> > mats;
		if (!PlayerBotNewPetStepOpen(v) || !growth_pet::GetEvolutionMaterials(v.nextStage, mats))
			return false;
		for (size_t i = 0; i < mats.size(); ++i)
		{
			const int missing = mats[i].second - (int)ch->CountSpecifyItem(mats[i].first);
			if (missing <= 0)
				continue;
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(mats[i].first);
			if (!entry || (int)entry->dwSupplyUnits < missing)
				return false;
		}
		return true;
	}

	bool PlayerBotSeeksGoodNewPetEgg(const TPlayerBotNewPetView& v)
	{
		return !v.hasPet || IsPlayerBotNewPetWeakEgg(v.pet.vnum - 300);
	}

	// How many units of the vnum a keeper would buy now (never a companion's).
	int GetPlayerBotNewPetWant(LPCHARACTER ch, DWORD vnum)
	{
		if (!IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !ch->IsItemLoaded())
			return 0;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		if (!v)
			return 0;
		// MT2009_PLUS_BOT_PET_GROW_V1: the pets tab's box (no pet, no egg, the wait over or no egg on any counter) and
		// book chest (an open slot, no book to read, the wait over)
		if (vnum == PLAYERBOT_NEWPET_BOX_VNUM)
			return IsPlayerBotPetGrowOn(PETGROW_EGG) && !v->hasPet && v->noEggSince != 0 && CountPlayerBotNewPetEggs(ch) == 0 &&
					ch->CountSpecifyItem(vnum) == 0 && ((DWORD)(get_dword_time() - v->noEggSince) >= PLAYERBOT_NEWPET_BOX_WAIT_MS ||
					CountPlayerBotNewPetEggSupply() == 0) ? 1 : 0;
		if (vnum == PLAYERBOT_NEWPET_BOOK_BOX_VNUM)
			return IsPlayerBotPetGrowOn(PETGROW_BOOKS) && v->hasPet && v->pet.evolution >= 4 && v->bookWaitSince != 0 &&
					(DWORD)(get_dword_time() - v->bookWaitSince) >= PLAYERBOT_NEWPET_BOOK_WAIT_MS &&
					CountPlayerBotNewPetFreeSlots(v->pet) > 0 && !PlayerBotHoldsNewPetReadableBook(ch, *v) &&
					ch->CountSpecifyItem(vnum) == 0 ? 1 : 0;
		if (IsPlayerBotNewPetEggVnum(vnum))
		{
			if (IsPlayerBotNewPetGoodEgg(vnum))
				return PlayerBotSeeksGoodNewPetEgg(*v) && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0;
			// MT2009_PLUS_BOT_PET_GROW_V1: a weak egg - for a keeper with no pet and no egg when no good one can be had, and
			// for a champion's empty potential slot the bag has no egg for
			if (IsPlayerBotPetGrowOn(PETGROW_EGG) && !v->hasPet && CountPlayerBotNewPetEggs(ch) == 0 &&
					!(CountPlayerBotNewPetGoodEggSupply() > 0 && GetPlayerBotNewPetSpare(ch) * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100 >=
					(long long)GetPlayerBotNewPetEggPrice()))
				return ch->CountSpecifyItem(vnum) == 0 ? 1 : 0;
			const int potential = CountPlayerBotNewPetPotentialFree(*v);
			if (potential > 0)
				return std::max(0, potential - (int)(ch->CountSpecifyItem(55401) + ch->CountSpecifyItem(55402)));
			return 0;
		}
		if (!v->hasPet)
			return 0;
		if (vnum == PLAYERBOT_PET_FOOD)
			return std::max(0, PLAYERBOT_NEWPET_FOOD_KEEP - (int)ch->CountSpecifyItem(vnum)) +
					GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		if (vnum == PLAYERBOT_PET_TREAT || vnum == PLAYERBOT_PET_TREAT_PLUS)
			return PlayerBotNewPetGrowing(*v) ? std::max(0, PLAYERBOT_NEWPET_TREAT_KEEP - (int)ch->CountSpecifyItem(vnum)) : 0;
		if (IsPlayerBotNewPetBookVnum(vnum))
		{
			const int skill = PlayerBotNewPetBookSkill(vnum);
			// MT2009_PLUS_BOT_PET_GROW_V1: from Dzielny (the books wait for the Bohaterski step in the bag)
			const int fromStage = IsPlayerBotPetGrowOn(PETGROW_BOOKS) ? PLAYERBOT_NEWPET_BOOK_KEEP_STAGE : 4;
			return v->pet.evolution >= fromStage && IsPlayerBotNewPetWantedSkill(ch, skill) && !PlayerBotPetKnows(v->pet, skill) &&
					CountPlayerBotNewPetFreeSlots(v->pet) > 0 && ch->CountSpecifyItem(vnum) == 0 ? 1 : 0;
		}
		const int need = GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		if (need <= 0 || !IsPlayerBotNewPetEvolutionReachable(ch, *v))
			return 0;
		return std::max(0, need - (int)ch->CountSpecifyItem(vnum));
	}

	bool IsPlayerBotNewPetEvolutionMaterial(LPCHARACTER ch, DWORD vnum)
	{
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		return v && GetPlayerBotNewPetMaterialNeed(ch, *v, vnum) > 0;
	}

	bool WantsPlayerBotNewPetOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer)
			return false;
		const int want = GetPlayerBotNewPetWant(ch, offer->GetVnum());
		return want > 0 && (int)offer->GetCount() <= want;
	}

	bool CanPlayerBotPayForNewPetOffer(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0 || !WantsPlayerBotNewPetOffer(ch, item))
			return false;
		const long long count = std::max<long long>(1, (long long)item->GetCount());
		const long long spare = GetPlayerBotNewPetSpare(ch);
		if (IsPlayerBotNewPetEggVnum(item->GetVnum()))
			return price / count <= (long long)GetPlayerBotNewPetEggPrice() &&
					price <= spare * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(item);
		if (fair <= 0 || price * 100 > fair * PLAYERBOT_NEWPET_FAIR_PERCENT)
			return false;
		return price <= spare * PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT / 100 ||
				(IsPlayerBotNewPetEvolutionMaterial(ch, item->GetVnum()) && price <= spare / 2);
	}

	long long CollectPlayerBotNewPetMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		if (!ch || !IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !GetPlayerBotNewPetView(ch))
			return 0;
		const long long spare = GetPlayerBotNewPetSpare(ch);
		if (spare <= 0)
			return 0;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		std::vector<DWORD> candidates;
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			candidates.push_back(PLAYERBOT_NEWPET_EGG_RANK[i]);
		long long cap = spare * PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT / 100;
		if (v->hasPet)
		{
			candidates.push_back(PLAYERBOT_PET_FOOD);
			candidates.push_back(PLAYERBOT_PET_TREAT);
			candidates.push_back(PLAYERBOT_PET_TREAT_PLUS);
			for (DWORD b = 55010; b <= 55038; ++b)
				if (IsPlayerBotNewPetBookVnum(b))
					candidates.push_back(b);
			std::vector<std::pair<DWORD, int> > mats;
			if (PlayerBotNewPetStepOpen(*v) && growth_pet::GetEvolutionMaterials(v->nextStage, mats))
			{
				for (size_t i = 0; i < mats.size(); ++i)
					candidates.push_back(mats[i].first);
				cap = std::max(cap, spare / 2);
			}
		}
		else
			cap = std::max(cap, std::min<long long>(spare * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100,
					(long long)GetPlayerBotNewPetEggPrice()));
		for (size_t i = 0; i < candidates.size(); ++i)
		{
			const int want = GetPlayerBotNewPetWant(ch, candidates[i]);
			if (want > 0)
				missing[candidates[i]] = want;
		}
		return missing.empty() ? 0 : cap;
	}

	std::map<DWORD, std::pair<DWORD, bool> > s_mapPlayerBotNewPetMarketAnswer;

	bool PlayerBotWantsNewPetFromMarket(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !GetPlayerBotNewPetView(ch))
			return false;
		const DWORD now = get_dword_time();
		std::pair<DWORD, bool>& answer = s_mapPlayerBotNewPetMarketAnswer[ch->GetPlayerID()];
		if (answer.first != 0 && (int)(now - answer.first) < 60000)
			return answer.second;
		std::map<DWORD, int> missing;
		bool any = false;
		if (CollectPlayerBotNewPetMissing(ch, missing) > 0)
			for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end() && !any; ++it)
			{
				const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(it->first);
				any = entry && entry->dwSupplyUnits > 0;
			}
		answer = std::make_pair(now, any);
		return any;
	}

	// The units of a pet good the bot keeps off its counter.
	int GetPlayerBotNewPetKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || !IsPlayerBotNewPetKeeper(ch))
			return 0;
		if (IsPlayerBotNewPetCompanion(ch))
			return 1000000;	// its player's business
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		if (!v)
			return 1000000;
		if (IsPlayerBotNewPetWeakEgg(vnum))
			return (!v->hasPet && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0) +
					CountPlayerBotNewPetPotentialFree(*v);	// MT2009_PLUS_BOT_PET_GROW_V1: the potential's eggs
		if (IsPlayerBotNewPetEggVnum(vnum))
			return PlayerBotSeeksGoodNewPetEgg(*v) ? 1 : 0;
		if (!v->hasPet)
			return 0;
		if (vnum == PLAYERBOT_PET_FOOD)
			return PLAYERBOT_NEWPET_FOOD_KEEP + GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		if (vnum == PLAYERBOT_PET_TREAT || vnum == PLAYERBOT_PET_TREAT_PLUS || vnum == PLAYERBOT_PET_TASTY_TREAT)
			return 1000000;	// eaten at the next looks
		if (vnum == PLAYERBOT_NEWPET_BOOK_BOX_VNUM)	// MT2009_PLUS_BOT_PET_GROW_V1: bought to be opened, never a counter's
			return IsPlayerBotPetGrowOn(PETGROW_BOOKS) && v->pet.evolution >= 4 ? 1 : 0;
		if (IsPlayerBotNewPetBookVnum(vnum))
		{
			// MT2009_PLUS_BOT_PET_GROW_V1: any book an open slot of a Dzielny+ pet could still take
			if (IsPlayerBotPetGrowOn(PETGROW_BOOKS) && v->pet.evolution >= PLAYERBOT_NEWPET_BOOK_KEEP_STAGE &&
					IsPlayerBotNewPetReadableBook(*v, vnum))
				return 1;
			return IsPlayerBotNewPetWantedSkill(ch, PlayerBotNewPetBookSkill(vnum)) && !PlayerBotPetKnows(v->pet, PlayerBotNewPetBookSkill(vnum)) ? 1 : 0;
		}
		const int need = GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		return need > 0 ? need : 0;
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: what a counter's stack of an evolution material keeps back for the keeper's next
	// step (playerbot_economy.h, GetPlayerBotStallBaseKeep) - the pet goods have their own keep above.
	int GetPlayerBotNewPetStageKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || IsPlayerBotNewPetGoodsVnum(vnum) || !IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch))
			return 0;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		return v ? GetPlayerBotNewPetMaterialNeed(ch, *v, vnum) : 0;
	}

	int GetPlayerBotNewPetGoodsForSale(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotNewPetGoodsVnum(item->GetVnum()))
			return 0;
		if (IsPlayerBotNewPetWeakEgg(item->GetVnum()))
			return 0;
		if (IsPlayerBotNewPetEggVnum(item->GetVnum()) && CountPlayerBotNewPetGoodEggSupply() >= PLAYERBOT_NEWPET_EGG_WORLD_LINES)
			return 0;
		if (item->GetVnum() == 55002 && item->GetSocket(2))
			return 0;	// a cage with a pet: a person's trade
		return (int)ch->CountSpecifyItem(item->GetVnum()) - GetPlayerBotNewPetKeep(ch, item->GetVnum());
	}

	// A weak egg's stack the bot does not keep goes to the merchant - a companion's never.
	bool IsPlayerBotNewPetJunkEgg(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotNewPetWeakEgg(item->GetVnum()) || !IsPlayerBotNewPetBot(ch) ||
				IsPlayerBotNewPetCompanion(ch))
			return false;
		const int spare = (int)ch->CountSpecifyItem(item->GetVnum()) - GetPlayerBotNewPetKeep(ch, item->GetVnum());
		return spare >= (int)item->GetCount();
	}

	// ---- the look -----------------------------------------------------------------------------------------------

	LPITEM FindPlayerBotNewPetItem(LPCHARACTER ch, DWORD vnum)
	{
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (item && item->GetVnum() == vnum && item->GetCount() > 0 && !item->isLocked() && !item->IsExchanging())
				return item;
		}
		return NULL;
	}

	LPITEM FindPlayerBotNewPetSeal(LPCHARACTER ch, DWORD petId)
	{
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (item && growth_pet::IsSealVnum(item->GetVnum()) && (DWORD)item->GetSocket(2) == petId)
				return item;
		}
		return NULL;
	}

	std::string MakePlayerBotPetName(LPCHARACTER ch, DWORD egg, int attempt)
	{
		static const char* const COMMON[] = { "Puszek", "Kropka", "Tofik", "Fafik", "Lunka", "Azor", "Mruczek", "Bobo", "Kajtek", "Pimpek" };
		struct SNames { DWORD egg; const char* names[6]; };
		static const SNames BY_EGG[] = {
			{ 55401, { "Bananek", "Psotka", "Kiki", "Hopek", "Figiel", "Czika" } },
			{ 55402, { "Siecik", "Tkacz", "Nitka", "Pajonk", "Kosmatek", "Szpilka" } },
			{ 55403, { "Plomyk", "Zarek", "Iskra", "Razik", "Wulkan", "Ognik" } },
			{ 55404, { "Szronek", "Sopel", "Mrozik", "Sniezek", "Nemik", "Lodzik" } },
			{ 55405, { "Smoczus", "Drako", "Lusek", "Pazurek", "Smokus", "Dracik" } },
			{ 55406, { "Rubin", "Czerwik", "Ognisty", "Zarzewie", "Smoczyca", "Rubik" } },
			{ 55407, { "Kostek", "Mrok", "Azik", "Cien", "Kosiarz", "Mroczek" } },
			{ 55408, { "Grubcio", "Katek", "Toporek", "Bulek", "Tlusty", "Kacik" } },
			{ 55409, { "Baszek", "Rogacz", "Kopytko", "Baashi", "Rogalik", "Bashi" } },
			{ 55410, { "Nessi", "Plusk", "Fala", "Bulbul", "Wodnik", "Glebia" } },
			{ 55411, { "Pierzak", "Cwirek", "Exi", "Skrzydlo", "Pisklak", "Puch" } },
			{ 55412, { "Bielik", "Alek", "Sniezka", "Gniewek", "Bialas", "Szron" } },
			{ 55413, { "Dowodek", "Kapral", "Straznik", "Szef", "Wodzik", "Major" } },
			{ 55414, { "Aamonek", "Zachlan", "Skarbek", "Monek", "Zlotko", "Chciwek" } },
		};
		const DWORD seed = (ch->GetPlayerID() * 2654435761U) ^ (egg * 40503U) ^ ((DWORD)attempt * 977U);
		const char* base = COMMON[(seed >> 8) % (sizeof(COMMON) / sizeof(COMMON[0]))];
		if ((seed >> 4) % 10 < 7)
			for (size_t i = 0; i < sizeof(BY_EGG) / sizeof(BY_EGG[0]); ++i)
				if (BY_EGG[i].egg == egg)
					base = BY_EGG[i].names[(seed >> 12) % 6];
		std::string name(base);
		if ((seed >> 20) % 100 < 15 || attempt > 0)
		{
			char digits[8];
			snprintf(digits, sizeof(digits), "%u", (unsigned int)((seed >> 3) % 99 + 1));
			name += digits;
		}
		if (name.size() > (size_t)GROWTH_PET_NAME_MAX)
			name.resize(GROWTH_PET_NAME_MAX);
		return name;
	}

	bool HatchPlayerBotPet(LPCHARACTER ch, bool goodOnly)
	{
		if ((long long)ch->GetGold() < PLAYERBOT_NEWPET_HATCH_PRICE + (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR)
			return false;
		LPITEM egg = NULL;
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (!item || !IsPlayerBotNewPetEggVnum(item->GetVnum()) || item->isLocked())
				continue;
			if ((long long)item->GetSocket(0) > 0 && (long long)item->GetSocket(0) < (long long)get_global_time())
				continue;
			if ((!goodOnly || IsPlayerBotNewPetGoodEgg(item->GetVnum())) &&
					(!egg || GetPlayerBotNewPetEggRank(item->GetVnum()) < GetPlayerBotNewPetEggRank(egg->GetVnum())))
				egg = item;
		}
		if (!egg)
			return false;
		const DWORD vnum = egg->GetVnum();
		for (int attempt = 0; attempt < 3; ++attempt)
		{
			const std::string name = MakePlayerBotPetName(ch, vnum, attempt);
			if (growth_pet::Hatch(ch, egg, name.c_str()))
			{
				++s_kPlayerBotNewPetStats.hatched;
				sys_log(0, "PLAYERBOT_NEWPET: hatched pid=%u name=%s egg=%u pet_name=%s", ch->GetPlayerID(), ch->GetName(),
						vnum, name.c_str());
				return true;
			}
		}
		return false;
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: the bag's eggs and its seals without a pet (socket 2 = 0 - the id fix's census),
	// once a look.
	void NotePlayerBotNewPetBag(LPCHARACTER ch, TPlayerBotNewPetView& v)
	{
		v.eggsGood = CountPlayerBotNewPetGoodEggs(ch);
		v.eggsWeak = (int)(ch->CountSpecifyItem(55401) + ch->CountSpecifyItem(55402));
		v.emptySeals = 0;
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (item && growth_pet::IsSealVnum(item->GetVnum()) && item->GetSocket(2) == 0)
				++v.emptySeals;
		}
	}

	void NotePlayerBotNewPetView(LPCHARACTER ch, TPlayerBotNewPetView& v)
	{
		std::vector<growth_pet::PetView> pets;
		growth_pet::ListPets(ch, pets);
		v.known = true;
		v.hasPet = false;
		v.nextStage = 0;
		v.evolveReady = false;
		// the summoned pet, else the best living one (the highest level)
		// MT2009_PLUS_BOT_PET_GROW_V1: a living pet of a good species before a summoned weak one (Malpiszon / Pajak - the
		// egg the keeper hatched while no good one could be had), the higher stage and level first
		const DWORD summoned = growth_pet::GetSummonedPetId(ch);
		const bool preferGood = IsPlayerBotPetGrowOn(PETGROW_EGG);
		int best = -1, current = -1;
		for (size_t i = 0; i < pets.size(); ++i)
		{
			if (pets[i].id == summoned)
				current = (int)i;
			const long long score = (pets[i].alive ? 1000000LL : 0) +
					(preferGood && !IsPlayerBotNewPetWeakEgg(pets[i].vnum - 300) ? 100000LL : 0) +
					pets[i].evolution * 1000LL + pets[i].level;
			const long long bestScore = best < 0 ? -1 : (pets[best].alive ? 1000000LL : 0) +
					(preferGood && !IsPlayerBotNewPetWeakEgg(pets[best].vnum - 300) ? 100000LL : 0) +
					pets[best].evolution * 1000LL + pets[best].level;
			if (score > bestScore)
				best = (int)i;
		}
		if (current >= 0 && (!preferGood || !IsPlayerBotNewPetWeakEgg(pets[current].vnum - 300) || !pets[best].alive ||
				IsPlayerBotNewPetWeakEgg(pets[best].vnum - 300)))
			best = current;
		if (best < 0)
			return;
		v.hasPet = true;
		v.pet = pets[best];
		int to = 0;
		v.evolveReady = growth_pet::CanEvolve(v.pet.id, ch, to);
		v.nextStage = to <= 6 ? to : 0;
	}

	// MT2009_PLUS_BOT_PET_FEED_V1: the life share under which a keeper feeds its pet.
	int GetPlayerBotNewPetFeedPct()
	{
		return IsPlayerBotSmallFixOn(SMALLFIX_PETS) ? GetPlayerBotSmallFixCfg().petFeedPct : PLAYERBOT_NEWPET_FEED_BELOW_PCT;
	}

	bool PlayerBotNewPetHungry(const TPlayerBotNewPetView& v)
	{
		return v.hasPet && v.pet.alive && v.pet.lifeMax > 0 && v.pet.lifeLeft * 100 < v.pet.lifeMax * GetPlayerBotNewPetFeedPct();
	}

	// A weak egg (Malpiszon / Pajak) the keeper does not keep (GetPlayerBotNewPetKeep) - the junk the merchant would get
	// for a pittance; a good egg is a counter's goods (two million), never food. Never a companion's (its player's).
	LPITEM FindPlayerBotNewPetSpareEgg(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotNewPetCompanion(ch))
			return NULL;
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (!item || !IsPlayerBotNewPetWeakEgg(item->GetVnum()) || item->isLocked() || item->IsExchanging())
				continue;
			if ((int)ch->CountSpecifyItem(item->GetVnum()) > GetPlayerBotNewPetKeep(ch, item->GetVnum()))
				return item;
		}
		return NULL;
	}

	// MT2009_PLUS_BOT_PET_GROW_V1: an egg for a potential slot - a weak one first, else a good one the keeper does not
	// keep for itself; never one past its time (the potential lasts as long as the egg would have).
	LPITEM FindPlayerBotNewPetPotentialEgg(LPCHARACTER ch)
	{
		LPITEM best = NULL;
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (!item || !IsPlayerBotNewPetEggVnum(item->GetVnum()) || item->isLocked() || item->IsExchanging())
				continue;
			if ((long long)item->GetSocket(0) <= (long long)get_global_time())
				continue;
			if (IsPlayerBotNewPetWeakEgg(item->GetVnum()))
				return item;
			if (!best && (int)ch->CountSpecifyItem(item->GetVnum()) > GetPlayerBotNewPetKeep(ch, item->GetVnum()))
				best = item;
		}
		return best;
	}

	// One act, or false.
	bool ActPlayerBotNewPet(LPCHARACTER ch, TPlayerBotNewPetView& v)
	{
		if (!v.hasPet)
			return false;
		LPITEM seal = FindPlayerBotNewPetSeal(ch, v.pet.id);
		if (!seal)
			return false;
		// life: dead -> Odzywka (the 50 % revive); low -> Odzywka
		// MT2009_PLUS_BOT_PET_FEED_V1: "low" is PLAYERBOT_NEWPET_FEED_PCT (50) while the fix is on, and with no Odzywka in
		// the bag a spare egg goes into the life bar (the feed window's way, +3-5% an egg).
		const bool hungry = PlayerBotNewPetHungry(v);
		if (!v.pet.alive || hungry)
			if (LPITEM food = FindPlayerBotNewPetItem(ch, PLAYERBOT_PET_FOOD))
				if (growth_pet::FeedLife(ch, food, seal))
				{
					++(v.pet.alive ? s_kPlayerBotNewPetStats.fed : s_kPlayerBotNewPetStats.revived);
					return true;
				}
		if (!v.pet.alive)
			return false;
		if (hungry && IsPlayerBotSmallFixOn(SMALLFIX_PETS))
			if (LPITEM egg = FindPlayerBotNewPetSpareEgg(ch))
			{
				const DWORD eggVnum = egg->GetVnum();
				if (growth_pet::FeedLifeWithEgg(ch, egg, seal))
				{
					++s_kPlayerBotNewPetStats.eggFeeds;
					PlayerBotLogThrottledEvery("newpet_egg_feed", get_dword_time(), 600000,
							"BOT_PETFEED: egg fed pid=%u name=%s pet=%u egg=%u life=%lld/%lld",
							ch->GetPlayerID(), ch->GetName(), v.pet.id, eggVnum, v.pet.lifeLeft, v.pet.lifeMax);
					return true;
				}
			}
		// out
		if (!v.pet.summoned && v.pet.level <= ch->GetLevel())
		{
			if (growth_pet::ToggleSummon(ch, seal))
			{
				++s_kPlayerBotNewPetStats.summoned;
				return true;
			}
			return false;
		}
		if (!v.pet.summoned)
			return false;
		if (LPITEM tasty = FindPlayerBotNewPetItem(ch, PLAYERBOT_PET_TASTY_TREAT))
			if (growth_pet::UseTastyTreat(ch, tasty))
			{
				++s_kPlayerBotNewPetStats.treats;
				return true;
			}
		// item experience
		if (v.pet.itemExp < v.pet.needItemExp)
		{
			static const DWORD treats[2] = { PLAYERBOT_PET_TREAT_PLUS, PLAYERBOT_PET_TREAT };
			for (int t = 0; t < 2; ++t)
				if (LPITEM treat = FindPlayerBotNewPetItem(ch, treats[t]))
					if (growth_pet::FeedItemExp(ch, treat, 1))
					{
						++s_kPlayerBotNewPetStats.treats;
						return true;
					}
			const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
			for (int i = 0; i < cells; ++i)
			{
				LPITEM item = ch->GetInventoryItem((WORD)i);
				if (!item || item->isLocked() || item->IsEquipped() ||
						(item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR) || !IsPlayerBotJunkItem(ch, item))
					continue;
				if (growth_pet::FeedItemExp(ch, item, (int)item->GetCount()))
				{
					++s_kPlayerBotNewPetStats.junk;
					return true;
				}
			}
		}
		// evolution (MT2009_PLUS_BOT_PET_GROW_V1: m2_bot_pet_evolve_off stops it)
		if (v.evolveReady && v.nextStage && IsPlayerBotPetGrowOn(PETGROW_EVOLVE))
		{
			std::vector<std::pair<DWORD, int> > mats;
			bool ready = growth_pet::GetEvolutionMaterials(v.nextStage, mats);
			for (size_t i = 0; i < mats.size() && ready; ++i)
				ready = (int)ch->CountSpecifyItem(mats[i].first) >= GetPlayerBotNewPetMaterialNeed(ch, v, mats[i].first);
			if (ready && growth_pet::Evolve(ch))
			{
				++s_kPlayerBotNewPetStats.evolved;
				sys_log(0, "PLAYERBOT_NEWPET: evolved pid=%u name=%s pet=%u stage=%d", ch->GetPlayerID(), ch->GetName(),
						v.pet.id, v.nextStage);
				return true;
			}
		}
		// skills (from Bohaterski)
		if (v.pet.evolution >= 4)
		{
			int wanted[4];
			const int n = GetPlayerBotNewPetSkills(ch, wanted);
			for (int w = 0; w < n; ++w)
			{
				if (PlayerBotPetKnows(v.pet, wanted[w]))
					continue;
				int slot = -1;
				for (int i = 0; i < GROWTH_PET_SKILL_SLOTS && slot < 0; ++i)
					if (!v.pet.skillLocked[i] && !v.pet.skill[i])
						slot = i;
				if (slot < 0)
					break;
				const DWORD book = wanted[w] <= 18 ? 55009 + wanted[w] : 55034 + wanted[w] - 19;
				if (LPITEM item = FindPlayerBotNewPetItem(ch, book))
					if (growth_pet::LearnSkill(ch, slot, item))
					{
						++s_kPlayerBotNewPetStats.skills;
						sys_log(0, "BOT_PETGROW: book read pid=%u name=%s pet=%u book=%u skill=%d slot=%d wanted=1",
								ch->GetPlayerID(), ch->GetName(), v.pet.id, book, wanted[w], slot);
						return true;
					}
			}
			// MT2009_PLUS_BOT_PET_GROW_V1: an open slot no wanted book came for in PLAYERBOT_NEWPET_BOOK_WAIT_MS takes any
			// book the bag holds (one the market, a drop or the book chest gave)
			const DWORD dwNow = get_dword_time();
			int open = -1;
			for (int i = 0; i < GROWTH_PET_SKILL_SLOTS && open < 0; ++i)
				if (!v.pet.skillLocked[i] && !v.pet.skill[i])
					open = i;
			if (open < 0 || !IsPlayerBotPetGrowOn(PETGROW_BOOKS))
				v.bookWaitSince = 0;
			else
			{
				if (v.bookWaitSince == 0)
					v.bookWaitSince = dwNow ? dwNow : 1;
				if ((DWORD)(dwNow - v.bookWaitSince) >= PLAYERBOT_NEWPET_BOOK_WAIT_MS)
					for (DWORD b = 55010; b <= 55038; ++b)
					{
						if (!IsPlayerBotNewPetBookVnum(b) || !IsPlayerBotNewPetReadableBook(v, b))
							continue;
						LPITEM item = FindPlayerBotNewPetItem(ch, b);
						if (item && growth_pet::LearnSkill(ch, open, item))
						{
							++s_kPlayerBotNewPetStats.skills;
							++s_kPlayerBotNewPetStats.booksAny;
							sys_log(0, "BOT_PETGROW: book read pid=%u name=%s pet=%u book=%u skill=%d slot=%d wanted=0",
									ch->GetPlayerID(), ch->GetName(), v.pet.id, b, PlayerBotNewPetBookSkill(b), open);
							v.bookWaitSince = 0;
							return true;
						}
					}
			}
			if ((long long)ch->GetGold() - GetPlayerBotReservedGold(ch) >= 2000000LL + PLAYERBOT_NEWPET_SKILL_RESERVE)
				for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
					if (v.pet.skill[i] && v.pet.skillLevel[i] < GROWTH_PET_SKILL_LEVEL_MAX && growth_pet::UpgradeSkill(ch, i))
					{
						++s_kPlayerBotNewPetStats.upgrades;
						return true;
					}
		}
		// MT2009_PLUS_BOT_PET_GROW_V1: a champion's open, empty potential slot takes an egg
		if (CountPlayerBotNewPetPotentialFree(v) > 0)
			for (int slot = 0; slot < v.pet.potentialOpen && slot < GROWTH_PET_POTENTIAL_SLOTS; ++slot)
			{
				if (v.pet.potentialActive[slot])
					continue;
				LPITEM egg = FindPlayerBotNewPetPotentialEgg(ch);
				if (!egg)
					break;
				const DWORD eggVnum = egg->GetVnum();
				if (growth_pet::FillPotential(ch, slot, egg))
				{
					++s_kPlayerBotNewPetStats.potential;
					sys_log(0, "BOT_PETGROW: potential pid=%u name=%s pet=%u slot=%d egg=%u champion_level=%d", ch->GetPlayerID(),
							ch->GetName(), v.pet.id, slot, eggVnum, v.pet.championLevel);
					return true;
				}
			}
		return false;
	}

	void LogPlayerBotNewPetCensus()
	{
		DWORD keepers = 0, withPet = 0, out = 0, dead = 0, levelSum = 0, levelMax = 0, champ = 0;
		DWORD hungry = 0, lifeSum = 0;	// MT2009_PLUS_BOT_PET_FEED_V1
		DWORD stage[7] = { 0 };
		// MT2009_PLUS_BOT_PET_GROW_V1
		DWORD noPetEgg = 0, noPetNoEgg = 0, eggsGood = 0, eggsWeak = 0, emptySeals = 0, withSkill = 0, skillsKnown = 0;
		DWORD potentialActive = 0, stepReady = 0, stepNear = 0, bookWait = 0;
		const DWORD dwNow = get_dword_time();
		for (std::map<DWORD, TPlayerBotNewPetView>::iterator it = s_mapPlayerBotNewPet.begin(); it != s_mapPlayerBotNewPet.end(); )
		{
			if ((int)(dwNow - it->second.lastSeen) > 60 * 60 * 1000)
			{
				s_mapPlayerBotNewPetMarketAnswer.erase(it->first);
				s_mapPlayerBotNewPet.erase(it++);
				continue;
			}
			const TPlayerBotNewPetView& v = it->second;
			++it;
			++keepers;
			eggsGood += (DWORD)v.eggsGood;
			eggsWeak += (DWORD)v.eggsWeak;
			emptySeals += v.emptySeals > 0 ? 1 : 0;
			if (!v.hasPet)
			{
				++(v.eggsGood + v.eggsWeak > 0 ? noPetEgg : noPetNoEgg);
				continue;
			}
			{
				int known = 0;
				for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
					known += v.pet.skill[i] ? 1 : 0;
				withSkill += known > 0 ? 1 : 0;
				skillsKnown += (DWORD)known;
				for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
					potentialActive += v.pet.potentialActive[i] ? 1 : 0;
				stepReady += v.evolveReady ? 1 : 0;
				stepNear += !v.evolveReady && PlayerBotNewPetStageNear(v) ? 1 : 0;
				bookWait += v.bookWaitSince != 0 ? 1 : 0;
			}
			++withPet;
			out += v.pet.summoned ? 1 : 0;
			dead += v.pet.alive ? 0 : 1;
			levelSum += (DWORD)v.pet.level;
			levelMax = std::max<DWORD>(levelMax, (DWORD)v.pet.level);
			champ += v.pet.championLevel > 0 ? 1 : 0;
			++stage[MINMAX(1, v.pet.evolution, 6)];
			hungry += PlayerBotNewPetHungry(v) ? 1 : 0;
			lifeSum += v.pet.alive && v.pet.lifeMax > 0 ? (DWORD)(v.pet.lifeLeft * 100 / v.pet.lifeMax) : 0;
		}
		const TPlayerBotNewPetStats& s = s_kPlayerBotNewPetStats;
		sys_log(0, "PLAYERBOT_NEWPET: census keepers=%u with_pet=%u out=%u dead=%u lv_avg=%u lv_max=%u champions=%u "
				"stages=%u/%u/%u/%u/%u/%u | hatched=%u fed=%u revived=%u treats=%u junk=%u evolved=%u skills=%u upgrades=%u summoned=%u",
				keepers, withPet, out, dead, withPet ? levelSum / withPet : 0, levelMax, champ, stage[1], stage[2], stage[3],
				stage[4], stage[5], stage[6], s.hatched, s.fed, s.revived, s.treats, s.junk, s.evolved, s.skills, s.upgrades,
				s.summoned);
		// MT2009_PLUS_BOT_PET_FEED_V1: the hungry ones (under the feed share, alive) and the eggs fed this window.
		sys_log(0, "BOT_PETFEED: census on=%d feed_pct=%d with_pet=%u hungry=%u dead=%u life_avg_pct=%u fed=%u egg_feeds=%u revived=%u",
				IsPlayerBotSmallFixOn(SMALLFIX_PETS) ? 1 : 0, GetPlayerBotNewPetFeedPct(), withPet, hungry, dead,
				withPet ? lifeSum / withPet : 0, s.fed, s.eggFeeds, s.revived);
		// MT2009_PLUS_BOT_PET_GROW_V1: one line, a stable prefix - the keepers' pets, eggs, stages, books and potential.
		sys_log(0, "BOT_PETGROW: census egg=%d evolve=%d books=%d potential=%d keepers=%u have_pet=%u no_pet_egg=%u "
				"no_pet_no_egg=%u eggs_good=%u eggs_weak=%u empty_seals=%u stages=%u/%u/%u/%u/%u/%u champions=%u step_ready=%u "
				"step_near=%u pets_with_skill=%u skills_known=%u book_wait=%u potential_active=%u | hatched=%u evolved=%u "
				"books=%u books_any=%u upgrades=%u potential=%u",
				IsPlayerBotPetGrowOn(PETGROW_EGG) ? 1 : 0, IsPlayerBotPetGrowOn(PETGROW_EVOLVE) ? 1 : 0,
				IsPlayerBotPetGrowOn(PETGROW_BOOKS) ? 1 : 0, IsPlayerBotPetGrowOn(PETGROW_POTENTIAL) ? 1 : 0, keepers, withPet,
				noPetEgg, noPetNoEgg, eggsGood, eggsWeak, emptySeals, stage[1], stage[2], stage[3], stage[4], stage[5], stage[6],
				champ, stepReady, stepNear, withSkill, skillsKnown, bookWait, potentialActive, s.hatched, s.evolved, s.skills,
				s.booksAny, s.upgrades, s.potential);
		s_kPlayerBotNewPetStats = TPlayerBotNewPetStats();
	}

	// The tick's call (playerbot_manager.cpp).
	void ManagePlayerBotNewPet(LPCHARACTER ch, DWORD dwNow)
	{
		if (s_dwPlayerBotNewPetCensusAt == 0 || (int)(dwNow - s_dwPlayerBotNewPetCensusAt) >= 0)
		{
			if (s_dwPlayerBotNewPetCensusAt != 0)
				LogPlayerBotNewPetCensus();
			s_dwPlayerBotNewPetCensusAt = dwNow + PLAYERBOT_NEWPET_CENSUS_MS;
		}
		if (!ch || ch->IsDead() || !ch->IsItemLoaded() || !IsPlayerBotNewPetKeeper(ch))
			return;
		TPlayerBotNewPetView& view = s_mapPlayerBotNewPet[ch->GetPlayerID()];
		view.lastSeen = dwNow;
		if (view.nextLook != 0 && (int)(dwNow - view.nextLook) < 0)
			return;
		view.nextLook = dwNow + (view.nextLook == 0 ? (DWORD)number(5000, 60000)
				: (DWORD)number(PLAYERBOT_NEWPET_LOOK_MIN_MS, PLAYERBOT_NEWPET_LOOK_MAX_MS));
		if (ch->GetExchange() || ch->GetMyShop() || ch->IsObserverMode() || !ch->GetSectree())
			return;
		NotePlayerBotNewPetView(ch, view);
		NotePlayerBotNewPetBag(ch, view);	// MT2009_PLUS_BOT_PET_GROW_V1
		if (view.hasPet || view.eggsGood + view.eggsWeak > 0)
			view.noEggSince = 0;
		else if (view.noEggSince == 0)
			view.noEggSince = dwNow ? dwNow : 1;
		// a pet: hatch the best egg (a weak one only when no good one can be had or after the wait)
		if (!view.hasPet)
		{
			if (CountPlayerBotNewPetGoodEggs(ch) > 0)
				HatchPlayerBotPet(ch, true);
			else if (ch->CountSpecifyItem(55401) + ch->CountSpecifyItem(55402) > 0)
			{
				const bool canBuy = !IsPlayerBotNewPetCompanion(ch) && CountPlayerBotNewPetGoodEggSupply() > 0 &&
						GetPlayerBotNewPetSpare(ch) * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100 >= (long long)GetPlayerBotNewPetEggPrice();
				if (canBuy && view.weakWaitSince == 0)
					view.weakWaitSince = dwNow;
				if (!canBuy || (DWORD)(dwNow - view.weakWaitSince) >= PLAYERBOT_NEWPET_WEAK_WAIT_MS)
				{
					view.weakWaitSince = 0;
					HatchPlayerBotPet(ch, false);
				}
			}
			NotePlayerBotNewPetView(ch, view);
		}
		// MT2009_PLUS_BOT_PET_GROW_V1: the good egg a keeper of a weak pet bought (PlayerBotSeeksGoodNewPetEgg) is hatched
		// - the new pet is the one raised from now on (NotePlayerBotNewPetView)
		else if (IsPlayerBotPetGrowOn(PETGROW_EGG) && IsPlayerBotNewPetWeakEgg(view.pet.vnum - 300) && view.eggsGood > 0 &&
				HatchPlayerBotPet(ch, true))
			NotePlayerBotNewPetView(ch, view);
		for (int acts = 0; acts < PLAYERBOT_NEWPET_ACTS_PER_LOOK && view.hasPet; ++acts)
		{
			if (!ActPlayerBotNewPet(ch, view))
				break;
			NotePlayerBotNewPetView(ch, view);
		}
	}
}

#endif
