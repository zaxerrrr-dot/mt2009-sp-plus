#ifndef __INC_METIN2_PLAYERBOT_PROGRESSION_SHOP_H__
#define __INC_METIN2_PLAYERBOT_PROGRESSION_SHOP_H__

// MT2009_PLUS_BOT_PROGRESSION_SHOP_V1 - a bot held at a gate of the checklist (playerbot_progression.h) buys in the
// ItemShop V3 what meets the gate's unmet rows, the way a player with coins does it (the owner, 8 November 2026: "Jak nie
// maja progresu, to czemu nie kupia przedmiotow w ItemShopie, aby szybko sprogresowac? Przy duzej ilosci SM to nie
// problem zrobic wiecej HP czy ulepszyc EQ"). The 3 h timeout stays; nothing here adds a coin.
//
// The measure that asked for it (the test world after the 23:07 reset of 7 November, 2000 bots of 100 000 SM each; the
// three cores' playerbot_progression_status.tsv at 09:46 on 8 November): 1 116 bots held - 42 at 35, 633 at 45, 271 at
// 55 (and on ch1 game2 none). Unmet rows by count: at 45 "2 umiej. na 24+" 633 (every one, "ma 0"), "bron lv25+7" 632,
// "kon poz. 12" 631, "zbroja lv26+6" 473; at 55 skills 271, weapon 271, helmet 270, armour 210, shield 193; at 35 weapon
// 38, Metins 41, horse 26, armour 25. Behind them:
//   * the weapon: 603 of 603 held bots sampled wear a young heroes' weapon (21910-21950, no refine recipe) - the gate
//     read the prepared bag weapon instead of the worn one, so the owner's "+9 of its level" rule never applied. Fixed in
//     playerbot_progression.h (MeasurePlayerBotProgress, m2_bot_prog_mlodzi_hand_off): nothing to buy;
//   * the skills: the class chest (D) 39048-39062, 999 SM - 25 instructions of the path, 20 Zwoj Egzorcyzmu, 10 Rada
//     Pustelnika - was bought once by 2 045 bots at 06:34-08:44 and then waits PLAYERBOT_SKILL_INSTR_CHEST_GAP_H (12 h);
//     the instruction census said short_bots=1151 (a skill at M with no book left), chests_bought=0. Here: a held bot
//     with a row of skills short buys its path's chest again whenever a skill it needs for the row has no book left
//     (no gap, one unopened chest at a time, the bag's room for the opening);
//   * the armour / helmet / shield +N: the refine pass holds a worn piece without a safe scroll ("refine held, no burn
//     of worn or four-line gear without a scroll", ~1 700 a minute on ch1). The ItemShop's scroll is the Zwoj
//     Blogoslawienstwa 25041 (Smocze Znaki: 350 one, 720 three - the bots hold ~7 500 SZ from V3's 100% return; day cap
//     6). Here: while a piece of the gate's level lacks its plus, the bag is kept at its scrolls (up to the steps left,
//     the hold cap 6), the day cap off for it. Kamien Kowala 71025 / Magiczny Metal 71026 (the Blacksmith's better
//     scrolls) are already urgent goals for a gear-held bot (smith_scroll) - they need yang at Kowal 20016. The
//     materials (Kawalek Klejnotu 30021, Ezoteryczny Przewodnik 30008, Oczy Pajaka 30057 ... - 538 of 586 short armours
//     lacked theirs) and the fee are not sold in the ItemShop: counted, nothing bought;
//   * HP from items (no default gate asks it now): bonus_add / bonus_change are urgent for a bot held for it
//     (IsPlayerBotSmPoolUrgent);
//   * the horse: the ItemShop has no medal, no horse book; its feed (50048) is for a horse of 21+ (the catalogue's
//     horse_feed). Counted only. The Metins: nothing to buy - the progressive Metins (MT2009_PLUS_METIN_PROGRESS_V1).
//
// The coins: every SM purchase here is "progshop_*" - urgent in the daily pool (IsPlayerBotSmPoolUrgent) and, like the
// element gate's, the gate may spend up to PLAYERBOT_PSHOP_BUDGET of the balance whatever the day's seventh says
// (GetPlayerBotProgShopPoolRoom; event flag m2_bot_progshop_budget N, 100-200000). The scrolls are Smocze Znaki (no pool).
// Switches (event flags): m2_bot_progshop_off 1 - the pass off (the pool's room with it); m2_bot_progshop_budget N;
// m2_bot_progshop_skills_off / m2_bot_progshop_scrolls_off 1 - that requirement's purchases off.
// The log: PLAYERBOT_PROGSHOP: bought (throttled) and the census every PLAYERBOT_PSHOP_CENSUS_MS - the bots held per gate,
// the unmet rows per gate and kind, what was bought per requirement, SM / SZ spent, the gates passed (with a purchase at
// that gate or without) and given up, the minutes held at the pass / give-up, the gear and skills blockers, and the
// month rule's looks (MT2009_PLUS_BOT_LOOK_MONTHLY_V1, playerbot_itemshop.h).
//
// An implementation fragment: included once from playerbot_manager.cpp after playerbot_skill_instr_late.h (the class
// chests) and the V3 goals (the purchase); the tick beside the element gate's.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)

namespace
{
	const DWORD PLAYERBOT_PSHOP_STEP_MS = 30 * 1000;
	const DWORD PLAYERBOT_PSHOP_CENSUS_MS = 10 * 60 * 1000;
	const long long PLAYERBOT_PSHOP_BUDGET = 6000;
	const int PLAYERBOT_PSHOP_SCROLL_KEEP = 6;	// the catalogue's hold cap of 25041
	const int PLAYERBOT_PSHOP_CHEST_CELLS = 10;	// the class chest's opening (9) and the purchase

	struct TPlayerBotPShopRecord
	{
		BYTE bGate;
		DWORD dwNext, dwSeen;
		long long llSpent;	// SM this gate
		long long llMarks;	// SZ this gate
		int iChests, iScrolls;
		bool bBought;
		TPlayerBotPShopRecord() : bGate(0), dwNext(0), dwSeen(0), llSpent(0), llMarks(0), iChests(0), iScrolls(0),
			bBought(false) {}
	};
	std::map<DWORD, TPlayerBotPShopRecord> s_mapPlayerBotPShop;
	// MT2009_PLUS_BOT_MOUNT_GATE_V1: the horse row's mount (playerbot_mount_gate.h, included after this file)
	bool ManagePlayerBotProgShopMount(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotPShopRecord& rec, DWORD dwNow);

	struct TPlayerBotPShopStats
	{
		unsigned int chests, chestFails, scrolls, scrollBuys, scrollFails;
		long long sm, marks;
		unsigned int passed, passedBought, givenUp, givenUpBought;
		unsigned long long passedMin, passedBoughtMin, givenUpMin;
		// the blockers seen at the steps (bots, distinct in the period)
		std::set<DWORD> gearLevel, gearNoRecipe, gearNoFee, gearNoMats, gearScrollShort, skillsBelowM, skillsReading,
				skillsNoRoom, skillsChestHeld, skillsBudget, horse, metins, hp;
		TPlayerBotPShopStats() : chests(0), chestFails(0), scrolls(0), scrollBuys(0), scrollFails(0), sm(0), marks(0),
			passed(0), passedBought(0), givenUp(0), givenUpBought(0), passedMin(0), passedBoughtMin(0), givenUpMin(0) {}
	};
	TPlayerBotPShopStats s_kPlayerBotPShop;

	bool IsPlayerBotProgShopOn(const char* part = NULL)
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true, s_bSkills = true, s_bScrolls = true;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			s_bOn = q.GetEventFlag("m2_bot_progshop_off") == 0;
			s_bSkills = q.GetEventFlag("m2_bot_progshop_skills_off") == 0;
			s_bScrolls = q.GetEventFlag("m2_bot_progshop_scrolls_off") == 0;
		}
		if (!s_bOn)
			return false;
		if (part && strcmp(part, "skills") == 0)
			return s_bSkills;
		if (part && strcmp(part, "scrolls") == 0)
			return s_bScrolls;
		return true;
	}

	long long GetPlayerBotProgShopBudget()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_progshop_budget");
		return flag >= 100 && flag <= 200000 ? (long long)flag : PLAYERBOT_PSHOP_BUDGET;
	}

	// playerbot_itemshop.h (GetPlayerBotSmPoolRoom): the held gate's room in SM - the budget less what this gate spent;
	// -1 for any other reason or a bot not held.
	long long GetPlayerBotProgShopPoolRoom(LPCHARACTER ch, const char* reason)
	{
		if (!ch || !reason || strncmp(reason, "progshop", 8) != 0 || !IsPlayerBotProgShopOn())
			return -1;
		const TPlayerBotProgress* e = FindPlayerBotHeldProgress(ch->GetPlayerID());
		if (!e)
			return -1;
		std::map<DWORD, TPlayerBotPShopRecord>::const_iterator it = s_mapPlayerBotPShop.find(ch->GetPlayerID());
		const long long spent = it != s_mapPlayerBotPShop.end() && it->second.bGate == e->bGate ? it->second.llSpent : 0;
		return std::max(0LL, GetPlayerBotProgShopBudget() - spent);
	}

	// playerbot_progression.h: a gate passed or given up - the census's pass counts and minutes.
	void NotePlayerBotProgShopGateEnd(DWORD pid, BYTE gate, unsigned int heldMin, bool givenUp)
	{
		std::map<DWORD, TPlayerBotPShopRecord>::iterator it = s_mapPlayerBotPShop.find(pid);
		const bool bought = it != s_mapPlayerBotPShop.end() && it->second.bGate == gate && it->second.bBought;
		if (givenUp)
		{
			++s_kPlayerBotPShop.givenUp;
			s_kPlayerBotPShop.givenUpMin += heldMin;
			if (bought)
				++s_kPlayerBotPShop.givenUpBought;
		}
		else
		{
			++s_kPlayerBotPShop.passed;
			s_kPlayerBotPShop.passedMin += heldMin;
			if (bought)
			{
				++s_kPlayerBotPShop.passedBought;
				s_kPlayerBotPShop.passedBoughtMin += heldMin;
			}
		}
		if (bought)
			sys_log(0, "PLAYERBOT_PROGSHOP: gate %s pid=%u gate=%u held_min=%u sm=%lld sz=%lld chests=%d scrolls=%d",
					givenUp ? "given_up" : "passed", pid, (unsigned int)gate, heldMin, it->second.llSpent, it->second.llMarks,
					it->second.iChests, it->second.iScrolls);
		if (it != s_mapPlayerBotPShop.end())
			s_mapPlayerBotPShop.erase(it);
	}

	// One V3 batch for a requirement (the day cap off for it, the hold cap kept): the pieces got; SM / SZ paid noted.
	int BuyPlayerBotProgShopBatch(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotPShopRecord& rec, DWORD vnum, bool marks,
			int pieces, const char* reason, DWORD dwNow)
	{
		if (pieces <= 0)
			return 0;
		const int coins = state.iDragonCoins, sz = state.iDragonMarks;
		TPlayerBotIshop3Goal g = { vnum, marks, pieces, reason, 0 };
		int purchases = 0;
		s_bPlayerBotIshop3NoDayCap = true;
		const int got = BuyPlayerBotIshop3Pieces(ch, state, g, dwNow, &purchases);
		s_bPlayerBotIshop3NoDayCap = false;
		long long sm = 0, paidMarks = 0;
		if (marks)
			paidMarks = std::max(0LL, (long long)sz - (long long)state.iDragonMarks);
		else
			sm = std::max(0LL, (long long)coins - (long long)state.iDragonCoins);
		if (got > 0)
		{
			rec.llSpent += sm;
			rec.llMarks += paidMarks;
			rec.bBought = true;
			s_kPlayerBotPShop.sm += sm;
			s_kPlayerBotPShop.marks += paidMarks;
			PlayerBotLogThrottled("progshop_bought", dwNow,
					"PLAYERBOT_PROGSHOP: bought pid=%u name=%s lv=%d gate=%u vnum=%u pieces=%d reason=%s sm=%lld sz=%lld "
					"gate_sm=%lld coins=%d marks=%d", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (unsigned int)rec.bGate,
					vnum, got, reason, sm, paidMarks, rec.llSpent, state.iDragonCoins, state.iDragonMarks);
		}
		return got;
	}

	// The piece a gear row reads (the gate's own choice, MeasurePlayerBotProgress).
	LPITEM GetPlayerBotProgShopPiece(LPCHARACTER ch, int type)
	{
		static const BYTE s_abWear[] = { WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_FOOTS, WEAR_WRIST, WEAR_NECK,
			WEAR_EAR };
		const int i = type - playerbot_progression::REQ_WEAPON;
		if (i < 0 || i >= (int)(sizeof(s_abWear) / sizeof(s_abWear[0])))
			return NULL;
		if (i == 0)
			return IsPlayerBotMlodziWeapon(ch->GetWear(WEAR_WEAPON)) ? NULL : GetPlayerBotHandWeapon(ch);
		return ch->GetWear(s_abWear[i]);
	}

	// The gear rows: the steps of plus the pieces of the gate's level still lack (the scrolls they may take); the
	// blockers noted.
	int CollectPlayerBotProgShopGearSteps(LPCHARACTER ch, const std::vector<playerbot_progression::TReq>& reqs)
	{
		const DWORD pid = ch->GetPlayerID();
		int steps = 0;
		for (size_t r = 0; r < reqs.size(); ++r)
		{
			const playerbot_progression::TReq& q = reqs[r];
			if (q.type < playerbot_progression::REQ_WEAPON || q.type > playerbot_progression::REQ_EARRINGS)
				continue;
			LPITEM piece = GetPlayerBotProgShopPiece(ch, q.type);
			if (!piece || (long long)GetPlayerBotPersonaLevelLimit(piece) < q.a)
			{
				s_kPlayerBotPShop.gearLevel.insert(pid);	// a piece of the gate's level: the market / equipment pass's
				continue;
			}
			const int plus = (int)piece->GetRefineLevel();
			if (plus >= q.b)
				continue;
			const TRefineTable* recipe = piece->GetRefineSet() ? CRefineManager::instance().GetRefineRecipe(piece->GetRefineSet()) : NULL;
			if (!recipe)
			{
				s_kPlayerBotPShop.gearNoRecipe.insert(pid);
				continue;
			}
			if ((long long)ch->GetGold() < (long long)ch->ComputeRefineFee(recipe->cost))
				s_kPlayerBotPShop.gearNoFee.insert(pid);
			for (int m = 0; m < recipe->material_count; ++m)
				if (recipe->materials[m].vnum && recipe->materials[m].count &&
						(int)ch->CountSpecifyItem(recipe->materials[m].vnum) < (int)recipe->materials[m].count)
				{
					s_kPlayerBotPShop.gearNoMats.insert(pid);
					break;
				}
			steps += q.b - plus;
		}
		return steps;
	}

#ifdef PLAYERBOT_SKILL_INSTR_LATE
	// The skills row: the class chest of the bot's path when a skill it needs for the row (the nearest to the row's
	// level, at M) has no book left. True: a chest bought.
	bool ManagePlayerBotProgShopSkills(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotPShopRecord& rec,
			const playerbot_progression::TReq& q, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		if (!ch->GetSkillGroup())
			return false;
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), pid);
		std::vector<std::pair<int, DWORD> > below;	// (level, skill) under the row's level
		int have = 0;
		for (BYTE i = 0; i < build.bSkillCount; ++i)
		{
			const DWORD skill = build.dwSkills[i];
			if (!skill)
				continue;
			const int level = ch->GetSkillLevel(skill);
			if (level >= q.b)
				++have;
			else
				below.push_back(std::make_pair(level, skill));
		}
		const int short_ = (int)q.a - have;
		if (short_ <= 0)
			return false;
		std::sort(below.rbegin(), below.rend());
		bool needBooks = false, reading = false, underMaster = false;
		for (int i = 0; i < (int)below.size() && i < short_; ++i)
		{
			const DWORD skill = below[i].second;
			if (ch->GetSkillMasterType(skill) != SKILL_MASTER || below[i].first < 20)
			{
				underMaster = true;
				continue;
			}
			if (CountPlayerBotOwnedSkillBooks(ch, skill) > 0)
				reading = true;
			else
				needBooks = true;
		}
		if (underMaster)
			s_kPlayerBotPShop.skillsBelowM.insert(pid);
		if (!needBooks)
		{
			if (reading)
				s_kPlayerBotPShop.skillsReading.insert(pid);
			return false;
		}
		const TPlayerBotClassChest* chest = NULL;
		for (size_t i = 0; i < PLAYERBOT_CLASS_CHEST_COUNT && !chest; ++i)
			if (PLAYERBOT_CLASS_CHESTS[i].bJob == ch->GetJob() && PLAYERBOT_CLASS_CHESTS[i].bGroup == ch->GetSkillGroup())
				chest = &PLAYERBOT_CLASS_CHESTS[i];
		if (!chest)
			return false;
		if (ch->CountSpecifyItem(chest->dwChest) > 0 || ch->CountSpecifyItem(chest->dwBook) > 0)
		{
			s_kPlayerBotPShop.skillsChestHeld.insert(pid);	// the chest pass opens it first
			return false;
		}
		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_PSHOP_CHEST_CELLS)
		{
			s_kPlayerBotPShop.skillsNoRoom.insert(pid);
			return false;
		}
		const DWORD price = GetPlayerBotItemShopCheapest(ch, chest->dwChest, false);
		if (price == 0)
			return false;
		if ((long long)price > GetPlayerBotProgShopBudget() - rec.llSpent || state.iDragonCoins < (int)price)
		{
			s_kPlayerBotPShop.skillsBudget.insert(pid);
			return false;
		}
		const int got = BuyPlayerBotProgShopBatch(ch, state, rec, chest->dwChest, false, 1, "progshop_skills", dwNow);
		if (got > 0)
		{
			++rec.iChests;
			++s_kPlayerBotPShop.chests;
			return true;
		}
		++s_kPlayerBotPShop.chestFails;
		return false;
	}
#endif

	// The census line (PLAYERBOT_PROGSHOP: census) - see the header.
	void TickPlayerBotProgShopCensus(DWORD dwNow)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = dwNow + PLAYERBOT_PSHOP_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwAt) < 0)
			return;
		s_dwAt = dwNow + PLAYERBOT_PSHOP_CENSUS_MS;
		std::map<int, int> perGate;
		std::map<std::string, int> unmet;	// "<gate>:<kind>"
		std::map<int, unsigned long long> heldMin;
		int held = 0, withBuy = 0;
		for (std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.begin();
				it != s_mapPlayerBotProgress.end(); ++it)
		{
			const TPlayerBotProgress& e = it->second;
			if (!e.bHeld || !e.bEligible || dwNow - e.dwSeen > 60000U)
				continue;
			++held;
			++perGate[e.bGate];
			heldMin[e.bGate] += e.dwHeldMs / 60000U;
			for (size_t r = 0; r < e.vecShort.size(); ++r)
			{
				const int t = e.vecShort[r].type;
				char key[48];
				snprintf(key, sizeof(key), "%u:%s", (unsigned int)e.bGate,
						t < playerbot_progression::REQ_COUNT ? playerbot_progression::REQ_KEYS[t] : "?");
				++unmet[key];
			}
			std::map<DWORD, TPlayerBotPShopRecord>::const_iterator p = s_mapPlayerBotPShop.find(it->first);
			if (p != s_mapPlayerBotPShop.end() && p->second.bGate == e.bGate && p->second.bBought)
				++withBuy;
		}
		std::string gates, kinds;
		for (std::map<int, int>::const_iterator it = perGate.begin(); it != perGate.end(); ++it)
		{
			char one[64];
			snprintf(one, sizeof(one), "%s%d:%d/avg_min=%llu", gates.empty() ? "" : ",", it->first, it->second,
					it->second ? heldMin[it->first] / (unsigned long long)it->second : 0ULL);
			gates += one;
		}
		for (std::map<std::string, int>::const_iterator it = unmet.begin(); it != unmet.end(); ++it)
		{
			char one[64];
			snprintf(one, sizeof(one), "%s%s=%d", kinds.empty() ? "" : ",", it->first.c_str(), it->second);
			kinds += one;
		}
		TPlayerBotPShopStats& s = s_kPlayerBotPShop;
		sys_log(0, "PLAYERBOT_PROGSHOP: census on=%d held=%d with_purchase=%d gates=[%s] unmet=[%s] bought=[skills_chest:%u "
				"(failed %u),scroll_25041:%u pieces/%u buys (failed %u)] sm=%lld sz=%lld passed=%u (after_purchase=%u) "
				"given_up=%u (after_purchase=%u) avg_min passed=%llu passed_after_purchase=%llu given_up=%llu | blockers "
				"gear_level=%u gear_no_recipe=%u gear_no_fee=%u gear_no_mats=%u gear_scroll_short=%u skills_below_m=%u "
				"skills_reading=%u skills_chest_unopened=%u skills_no_room=%u skills_budget=%u horse_no_mount=%u "
				"metins_none_in_shop=%u hp_urgent=%u budget=%lld",
				IsPlayerBotProgShopOn() ? 1 : 0, held, withBuy, gates.c_str(), kinds.c_str(), s.chests, s.chestFails, s.scrolls,
				s.scrollBuys, s.scrollFails, s.sm, s.marks, s.passed, s.passedBought, s.givenUp, s.givenUpBought,
				s.passed ? s.passedMin / s.passed : 0ULL, s.passedBought ? s.passedBoughtMin / s.passedBought : 0ULL,
				s.givenUp ? s.givenUpMin / s.givenUp : 0ULL, (unsigned int)s.gearLevel.size(),
				(unsigned int)s.gearNoRecipe.size(), (unsigned int)s.gearNoFee.size(), (unsigned int)s.gearNoMats.size(),
				(unsigned int)s.gearScrollShort.size(), (unsigned int)s.skillsBelowM.size(), (unsigned int)s.skillsReading.size(),
				(unsigned int)s.skillsChestHeld.size(), (unsigned int)s.skillsNoRoom.size(), (unsigned int)s.skillsBudget.size(),
				(unsigned int)s.horse.size(), (unsigned int)s.metins.size(), (unsigned int)s.hp.size(),
				GetPlayerBotProgShopBudget());
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: the level-55 gate's paths (playerbot_progression.h) - the held bots let through
		// by each in the period (and their minutes held), the bots of the gate's window now by their look, the unmet
		// rows of the held ones with the alternative counted (55:fire - the fire short, 55:armour / helmet / shield at
		// the alternative's plus once the bot is on the fire path)
		{
			int fireMin = 0, firePlus = 0;
			const bool on = GetPlayerBotGate55Fire(&fireMin, &firePlus);
			int now[PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE + 1] = { 0 };
			int fireSum = 0, fireBots = 0, fire50 = 0;
			for (std::map<DWORD, TPlayerBotProgress>::const_iterator it = s_mapPlayerBotProgress.begin();
					it != s_mapPlayerBotProgress.end(); ++it)
			{
				const TPlayerBotProgress& e = it->second;
				if (!e.bEligible || dwNow - e.dwSeen > 60000U || e.bGate55Path == PLAYERBOT_GATE55_PATH_NONE ||
						e.bGate55Path > PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE)
					continue;
				++now[e.bGate55Path];
				if (e.bHeld && e.bGate == PLAYERBOT_GATE55_FIRE_LEVEL)
				{
					fireSum += e.iGate55Fire;
					++fireBots;
					if (e.iGate55Fire >= fireMin)
						++fire50;
				}
			}
			TPlayerBotGate55Stats& g = s_kPlayerBotGate55;
			sys_log(0, "PLAYERBOT_PROGSHOP: gate55 on=%d fire_min=%d plus=%d 55:passed_by_fire=%u 55:passed_by_plus6=%u "
					"avg_held_min fire=%llu plus6=%llu | now past_by_plus6=%d past_by_fire=%d held_fire_short=%d "
					"held_plus%d_short=%d held_both_short=%d held_other_rows=%d held_other_rows_fire_met=%d | held_fire_avg=%d "
					"held_at_fire_min=%d/%d",
					on ? 1 : 0, fireMin, firePlus, g.passedFire, g.passedPlus6,
					g.passedFire ? g.passedFireMin / g.passedFire : 0ULL, g.passedPlus6 ? g.passedPlus6Min / g.passedPlus6 : 0ULL,
					now[PLAYERBOT_GATE55_PATH_PLUS6], now[PLAYERBOT_GATE55_PATH_FIRE], now[PLAYERBOT_GATE55_PATH_HELD_FIRE], firePlus,
					now[PLAYERBOT_GATE55_PATH_HELD_GEAR], now[PLAYERBOT_GATE55_PATH_HELD_BOTH], now[PLAYERBOT_GATE55_PATH_HELD_OTHER],
					now[PLAYERBOT_GATE55_PATH_HELD_OTHER_FIRE], fireBots ? fireSum / fireBots : 0, fire50, fireBots);
			g = TPlayerBotGate55Stats();
		}
		// MT2009_PLUS_BOT_LOOK_MONTHLY_V1: the cosmetics' month (playerbot_itemshop.h)
		std::string looks;
		for (int k = 0; k <= PLAYERBOT_LOOK_MONTH_CHEST; ++k)
		{
			char one[64];
			snprintf(one, sizeof(one), "%s%s:%u/%u", k ? "," : "", PLAYERBOT_LOOK_MONTH_NAMES[k], s_kPlayerBotLookMonth.bought[k],
					(unsigned int)s_kPlayerBotLookMonth.blocked[k].size());
			looks += one;
			s_kPlayerBotLookMonth.bought[k] = 0;
			s_kPlayerBotLookMonth.blocked[k].clear();
		}
		sys_log(0, "PLAYERBOT_PROGSHOP: looks monthly=%d days=%d bought/blocked_bots=[%s]", IsPlayerBotLookMonthlyOn() ? 1 : 0,
				GetPlayerBotLookMonthSeconds() / 86400, looks.c_str());
		s = TPlayerBotPShopStats();
		for (std::map<DWORD, TPlayerBotPShopRecord>::iterator it = s_mapPlayerBotPShop.begin(); it != s_mapPlayerBotPShop.end();)
		{
			if (dwNow - it->second.dwSeen > 60U * 60U * 1000U)
				s_mapPlayerBotPShop.erase(it++);
			else
				++it;
		}
	}

	// The tick (the per-bot pass, beside the element gate's): every PLAYERBOT_PSHOP_STEP_MS while the bot is held.
	void ManagePlayerBotProgressionShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		TickPlayerBotProgShopCensus(dwNow);
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc() || !IsPlayerBotProgShopOn() ||
				GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return;
		const TPlayerBotProgress* e = FindPlayerBotHeldProgress(ch->GetPlayerID());
		if (!e || e->vecShort.empty())
			return;
		TPlayerBotPShopRecord& rec = s_mapPlayerBotPShop[ch->GetPlayerID()];
		rec.dwSeen = dwNow;
		if (rec.bGate != e->bGate)
		{
			rec = TPlayerBotPShopRecord();
			rec.bGate = e->bGate;
			rec.dwSeen = dwNow;
			rec.dwNext = dwNow + PlayerBotNavHash(ch->GetPlayerID() ^ 0x50534850U) % PLAYERBOT_PSHOP_STEP_MS;
		}
		if ((int)(dwNow - rec.dwNext) < 0)
			return;
		rec.dwNext = dwNow + PLAYERBOT_PSHOP_STEP_MS;
		if (ch->IsBusy() || ch->GetMyShop() || ch->GetExchange() || !ch->CanHandleItem())
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		const DWORD pid = ch->GetPlayerID();
		const std::vector<playerbot_progression::TReq> reqs = e->vecShort;	// the purchases below may re-weigh nothing, but copy
		for (size_t r = 0; r < reqs.size(); ++r)
		{
			switch (reqs[r].type)
			{
				// MT2009_PLUS_BOT_MOUNT_GATE_V1: no medal or horse book in the shop - a riding mount answers the row
				// (playerbot_mount_gate.h); counted when none could be bought
				case playerbot_progression::REQ_HORSE:
					if (!ManagePlayerBotProgShopMount(ch, state, rec, dwNow))
						s_kPlayerBotPShop.horse.insert(pid);
					break;
				case playerbot_progression::REQ_METINS: s_kPlayerBotPShop.metins.insert(pid); break;
				case playerbot_progression::REQ_HP: s_kPlayerBotPShop.hp.insert(pid); break;	// the bonus goals, urgent
#ifdef PLAYERBOT_SKILL_INSTR_LATE
				case playerbot_progression::REQ_SKILLS:
					if (IsPlayerBotProgShopOn("skills"))
						ManagePlayerBotProgShopSkills(ch, state, rec, reqs[r], dwNow);
					break;
#endif
				default: break;
			}
		}
		// the gear rows: the safe scrolls for the steps left, the bag kept at them (Smocze Znaki)
		const int steps = CollectPlayerBotProgShopGearSteps(ch, reqs);
		if (steps > 0 && IsPlayerBotProgShopOn("scrolls"))
		{
			const int held = CountPlayerBotSafeRefineScrolls(ch);
			const int want = std::min(steps, PLAYERBOT_PSHOP_SCROLL_KEEP);
			if (held < want)
			{
				s_kPlayerBotPShop.gearScrollShort.insert(pid);
				const int room = GetPlayerBotIshop3HoldRoom(ch, PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM);
				const int pieces = std::min(want - held, room == INT_MAX ? want - held : room);
				if (pieces > 0)
				{
					const int got = BuyPlayerBotProgShopBatch(ch, state, rec, PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM, true, pieces,
							"progshop_scroll", dwNow);
					if (got > 0)
					{
						rec.iScrolls += got;
						s_kPlayerBotPShop.scrolls += (unsigned int)got;
						++s_kPlayerBotPShop.scrollBuys;
					}
					else
						++s_kPlayerBotPShop.scrollFails;
				}
			}
		}
	}
}

#else

namespace
{
	long long GetPlayerBotProgShopPoolRoom(LPCHARACTER, const char*) { return -1; }
	void NotePlayerBotProgShopGateEnd(DWORD, BYTE, unsigned int, bool) {}
}

#endif

#endif
