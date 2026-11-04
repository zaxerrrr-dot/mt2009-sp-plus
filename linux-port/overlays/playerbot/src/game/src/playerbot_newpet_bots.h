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
		TPlayerBotNewPetView() : nextLook(0), known(false), hasPet(false), nextStage(0), evolveReady(false), lastSeen(0),
				weakWaitSince(0) {}
	};

	std::map<DWORD, TPlayerBotNewPetView> s_mapPlayerBotNewPet;

	struct TPlayerBotNewPetStats
	{
		DWORD hatched, fed, revived, treats, junk, evolved, skills, upgrades, summoned;
		TPlayerBotNewPetStats() : hatched(0), fed(0), revived(0), treats(0), junk(0), evolved(0), skills(0), upgrades(0),
				summoned(0) {}
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
		if (!v.hasPet || !v.evolveReady || !v.nextStage)
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
		if (!v.evolveReady || !growth_pet::GetEvolutionMaterials(v.nextStage, mats))
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
		if (IsPlayerBotNewPetEggVnum(vnum))
			return IsPlayerBotNewPetGoodEgg(vnum) && PlayerBotSeeksGoodNewPetEgg(*v) && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0;
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
			return v->pet.evolution >= 4 && IsPlayerBotNewPetWantedSkill(ch, skill) && !PlayerBotPetKnows(v->pet, skill) &&
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
			if (v->evolveReady && growth_pet::GetEvolutionMaterials(v->nextStage, mats))
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
			return !v->hasPet && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0;
		if (IsPlayerBotNewPetEggVnum(vnum))
			return PlayerBotSeeksGoodNewPetEgg(*v) ? 1 : 0;
		if (!v->hasPet)
			return 0;
		if (vnum == PLAYERBOT_PET_FOOD)
			return PLAYERBOT_NEWPET_FOOD_KEEP + GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		if (vnum == PLAYERBOT_PET_TREAT || vnum == PLAYERBOT_PET_TREAT_PLUS || vnum == PLAYERBOT_PET_TASTY_TREAT)
			return 1000000;	// eaten at the next looks
		if (IsPlayerBotNewPetBookVnum(vnum))
			return IsPlayerBotNewPetWantedSkill(ch, PlayerBotNewPetBookSkill(vnum)) && !PlayerBotPetKnows(v->pet, PlayerBotNewPetBookSkill(vnum)) ? 1 : 0;
		const int need = GetPlayerBotNewPetMaterialNeed(ch, *v, vnum);
		return need > 0 ? need : 0;
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

	void NotePlayerBotNewPetView(LPCHARACTER ch, TPlayerBotNewPetView& v)
	{
		std::vector<growth_pet::PetView> pets;
		growth_pet::ListPets(ch, pets);
		v.known = true;
		v.hasPet = false;
		v.nextStage = 0;
		v.evolveReady = false;
		// the summoned pet, else the best living one (the highest level)
		const DWORD summoned = growth_pet::GetSummonedPetId(ch);
		int best = -1;
		for (size_t i = 0; i < pets.size(); ++i)
		{
			if (pets[i].id == summoned)
			{
				best = (int)i;
				break;
			}
			if (best < 0 || (pets[i].alive && (!pets[best].alive || pets[i].level > pets[best].level)))
				best = (int)i;
		}
		if (best < 0)
			return;
		v.hasPet = true;
		v.pet = pets[best];
		int to = 0;
		v.evolveReady = growth_pet::CanEvolve(v.pet.id, ch, to);
		v.nextStage = to <= 6 ? to : 0;
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
		if (!v.pet.alive || (v.pet.lifeMax > 0 && v.pet.lifeLeft * 100 < v.pet.lifeMax * PLAYERBOT_NEWPET_FEED_BELOW_PCT))
			if (LPITEM food = FindPlayerBotNewPetItem(ch, PLAYERBOT_PET_FOOD))
				if (growth_pet::FeedLife(ch, food, seal))
				{
					++(v.pet.alive ? s_kPlayerBotNewPetStats.fed : s_kPlayerBotNewPetStats.revived);
					return true;
				}
		if (!v.pet.alive)
			return false;
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
		// evolution
		if (v.evolveReady && v.nextStage)
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
						return true;
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
		return false;
	}

	void LogPlayerBotNewPetCensus()
	{
		DWORD keepers = 0, withPet = 0, out = 0, dead = 0, levelSum = 0, levelMax = 0, champ = 0;
		DWORD stage[7] = { 0 };
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
			if (!v.hasPet)
				continue;
			++withPet;
			out += v.pet.summoned ? 1 : 0;
			dead += v.pet.alive ? 0 : 1;
			levelSum += (DWORD)v.pet.level;
			levelMax = std::max<DWORD>(levelMax, (DWORD)v.pet.level);
			champ += v.pet.championLevel > 0 ? 1 : 0;
			++stage[MINMAX(1, v.pet.evolution, 6)];
		}
		const TPlayerBotNewPetStats& s = s_kPlayerBotNewPetStats;
		sys_log(0, "PLAYERBOT_NEWPET: census keepers=%u with_pet=%u out=%u dead=%u lv_avg=%u lv_max=%u champions=%u "
				"stages=%u/%u/%u/%u/%u/%u | hatched=%u fed=%u revived=%u treats=%u junk=%u evolved=%u skills=%u upgrades=%u summoned=%u",
				keepers, withPet, out, dead, withPet ? levelSum / withPet : 0, levelMax, champ, stage[1], stage[2], stage[3],
				stage[4], stage[5], stage[6], s.hatched, s.fed, s.revived, s.treats, s.junk, s.evolved, s.skills, s.upgrades,
				s.summoned);
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
		for (int acts = 0; acts < PLAYERBOT_NEWPET_ACTS_PER_LOOK && view.hasPet; ++acts)
		{
			if (!ActPlayerBotNewPet(ch, view))
				break;
			NotePlayerBotNewPetView(ch, view);
		}
	}
}

#endif
