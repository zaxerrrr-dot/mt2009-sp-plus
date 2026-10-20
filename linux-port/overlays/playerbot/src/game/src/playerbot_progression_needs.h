#ifndef PLAYERBOT_PROGRESSION_NEEDS_H
#define PLAYERBOT_PROGRESSION_NEEDS_H
namespace {
    int CountPlayerBotOwnedSkillBooks(LPCHARACTER ch, DWORD skill) {
        int count = 0;
        for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell) {
            LPITEM item = ch->GetInventoryItem(cell);
            if (item && item->GetCell() == cell && item->GetType() == ITEM_SKILLBOOK &&
                    GetPlayerBotSkillBookSkillVnum(item) == skill)
                count += item->GetCount();
        }
        return count;
    }
    bool PlayerBotHasGrandMasterToTrain(LPCHARACTER ch) {
        if (!ch || !ch->GetSkillGroup()) return false;
        const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
        for (BYTE i = 0; i < build.bSkillCount; ++i) {
            DWORD skill = build.dwSkills[i];
            if (skill && ch->GetSkillMasterType(skill) == SKILL_GRAND_MASTER &&
                    ch->GetSkillLevel(skill) >= 30 && ch->GetSkillLevel(skill) < 40) return true;
        }
        return false;
    }
    // MT2009_PLUS_UPSTREAM_BOTLOGIC_SPIRIT_STONE_V1: a Kamien Duchowy goes to
    // the skills in the build's own order (dwSkills, the order the points go
    // in) - the first skill at Grand Master (G1..G10) is the one read, and a
    // later one never jumps the queue because its read is cheaper. 0: none.
    DWORD GetPlayerBotGrandMasterOrderSkill(LPCHARACTER ch) {
        if (!ch || !ch->GetSkillGroup()) return 0;
        const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
        for (BYTE i = 0; i < build.bSkillCount; ++i) {
            const DWORD skill = build.dwSkills[i];
            if (!skill || ch->GetSkillMasterType(skill) != SKILL_GRAND_MASTER) continue;
            const int level = ch->GetSkillLevel(skill);
            if (level >= 30 && level < 40) return skill;
        }
        return 0;
    }
    // MT2009_PLUS_UPSTREAM_BOTLOGIC_SPIRIT_STONE_V1: the rank the skill next in
    // order is short of, beans counted - what sends a bot to the counters for
    // Fasolki Zen and Owoce Zycia (playerbot_market.h).
    bool PlayerBotNeedsTrainingRank(LPCHARACTER ch) {
        if (!PlayerBotHasGrandMasterToTrain(ch) || !ch->CountSpecifyItem(PLAYERBOT_GRAND_MASTER_STONE_VNUM)) return false;
        const DWORD skill = GetPlayerBotGrandMasterOrderSkill(ch);
        if (!skill) return false;
        // MT2009_PLUS_SIDEKICK_ZEN_BEAN_TRAINING_V1: the beans in the bag count.
        const int beanLift = GetPlayerBotZenBeanLift(ch);
        return ch->GetRealAlignment() + beanLift < GetPlayerBotGrandMasterRankCost(ch->GetSkillLevel(skill));
    }
    // MT2009_PLUS_UPSTREAM_BOTLOGIC_SPIRIT_STONE_V1: the Fasolki Zen and the
    // Owoce Zycia a bot short of rank for its next Kamien Duchowy buys off the
    // counters - beans up to its keep, fruit up to PLAYERBOT_LIFE_FRUIT_BUY_KEEP
    // (playerbot_market.h asks the same of each line). `onLedger` asks only for
    // what some counter holds (the walk's question, no counter read).
    int CollectPlayerBotTrainingRankMissing(LPCHARACTER ch, std::map<DWORD, int>& missing, bool onLedger) {
        if (!ch || ch->GetRealAlignment() < 0 || !PlayerBotNeedsTrainingRank(ch)) return 0;
        int kinds = 0;
        const int beans = GetPlayerBotZenBeanKeep(ch) - (int)ch->CountSpecifyItem(PLAYERBOT_ZEN_BEAN_VNUM);
        const int fruit = PLAYERBOT_LIFE_FRUIT_BUY_KEEP - (int)ch->CountSpecifyItem(PLAYERBOT_LIFE_FRUIT_VNUM);
        const DWORD vnums[2] = { PLAYERBOT_ZEN_BEAN_VNUM, PLAYERBOT_LIFE_FRUIT_VNUM };
        const int wants[2] = { beans, fruit };
        for (int i = 0; i < 2; ++i) {
            if (wants[i] <= 0) continue;
            if (onLedger) {
                const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnums[i]);
                if (!entry || entry->dwSupplyUnits == 0) continue;
            }
            missing[vnums[i]] = wants[i];
            ++kinds;
        }
        return kinds;
    }
    // The open collection chain, independent of whether a hunting slot is free.
    // Herbs and quest keys stay on their own quest path, never a new market.
    int GetPlayerBotBiologistPurchaseNeed(LPCHARACTER ch, DWORD vnum) {
        if (!ch || IsPlayerBotDropper(GetPlayerBotPersonalityByPID(ch->GetPlayerID()))) return 0;
        for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i) {
            const TPlayerBotBiologistMission& m = PLAYERBOT_BIOLOGIST_MISSIONS[i];
            if (m.itemVnum != vnum || m.requiredLevel < PLAYERBOT_BIOLOGIST_COLLECT_QUEST_LEVEL ||
                    ch->GetLevel() < m.requiredLevel || !IsPlayerBotBiologistMissionOpen(ch, i) ||
                    IsPlayerBotBiologistMissionComplete(ch, i) || IsPlayerBotBiologistKeyPhase(ch, i) ||
                    !IsPlayerBotHuntingMobHosted(m.mobVnum)) continue;
            return std::max(0, GetPlayerBotBiologistReserve(ch, vnum) - (int)ch->CountSpecifyItem(vnum));
        }
        return 0;
    }
    // Iwakura's Student (SUB-OSOBOWOSCI CHWILOWE): a book or a spirit stone a
    // bot drops it reads on the spot, but under the personality system it
    // buys one only once its big three - weapon, armour, shield - stand at +7
    // ("Grinder ... nigdy nie kupuje KU na rynku, gdyz priorytetowo odklada
    // Yang na ulepszenie sprzetu"). The keep limits below were already the
    // other half of his rule: a book for a skill at Master, a stone for one at
    // Grand Master, never one "na zapas".
    bool PlayerBotStudiesAtTheMarket(LPCHARACTER ch) {
        return !IsPlayerBotPersonaEnabled() || IsPlayerBotBigThreeAtPlus(ch, 7);
    }
    // Skills at M and beyond: the +7 rule above let 5 bots of 284 from level
    // fifty buy a book, so almost no bot ever had one for a skill at Master.
    // A bot holding more than PLAYERBOT_BOOK_SURPLUS_GOLD - on the price
    // sheet's scale (ScalePlayerBotIwakuraPrice) - buys the books of its own
    // skills out of what it holds over that sum, whatever its gear.
    const DWORD PLAYERBOT_BOOK_SURPLUS_GOLD = 10000000;
    DWORD ScalePlayerBotIwakuraPrice(DWORD base);
    long long GetPlayerBotBookSurplus(LPCHARACTER ch) {
        if (!ch) return 0;
        return std::max(0LL, (long long)ch->GetGold() -
            (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_BOOK_SURPLUS_GOLD));
    }
    bool PlayerBotStudiesFromSurplus(LPCHARACTER ch) {
        return GetPlayerBotBookSurplus(ch) > 0;
    }
    // Whoever buys the books of its own skills: the student above, the
    // trader (community patch 2, point 5) and the bot with the surplus.
    // MT2009_PLUS_PROGRESSION_V1: and the bot a gate of the checklist holds
    // for its skills (playerbot_progression.h).
    int GetPlayerBotProgressionNeeds(DWORD pid);
    bool PlayerBotStudiesBooks(LPCHARACTER ch) {
        return PlayerBotStudiesAtTheMarket(ch) || PlayerBotBuysBooksAsTrader(ch) || PlayerBotStudiesFromSurplus(ch) ||
            (ch && (GetPlayerBotProgressionNeeds(ch->GetPlayerID()) & playerbot_progression::NEED_SKILLS) != 0);
    }
    // Quantity needed, not a boolean reason to buy an arbitrarily large stack.
    int GetPlayerBotProgressionNeed(LPCHARACTER ch, LPITEM offer) {
        if (!ch || !offer || !ch->IsItemLoaded()) return 0;
        if (offer->GetType() == ITEM_SKILLBOOK) {
            DWORD skill = GetPlayerBotSkillBookSkillVnum(offer);
            // Only for a skill the engine will let the book train, which is a
            // skill at Master (LearnSkillByBook): of 1908 books bought on
            // m2zip on 26 September, 754 of those still in their buyer's bag
            // were for skills below seventeen, and 92 for one at Master.
            if (!ch->GetSkillGroup() || !IsPlayerBotOwnSkill(ch, skill) ||
                    ch->GetSkillMasterType(skill) != SKILL_MASTER ||
                    !PlayerBotStudiesBooks(ch)) return 0;
            return std::max(0, GetPlayerBotBookKeepLimit(ch, skill) - CountPlayerBotOwnedSkillBooks(ch, skill));
        }
        if (offer->GetVnum() == PLAYERBOT_GRAND_MASTER_STONE_VNUM)
            return PlayerBotHasGrandMasterToTrain(ch) && PlayerBotStudiesAtTheMarket(ch)
                ? std::max(0, PLAYERBOT_GRAND_MASTER_STONE_KEEP - (int)ch->CountSpecifyItem(offer->GetVnum())) : 0;
        return GetPlayerBotBiologistPurchaseNeed(ch, offer->GetVnum());
    }
    bool IsPlayerBotProgressionOffer(LPCHARACTER ch, LPITEM offer) {
        return offer && offer->GetCount() > 0 &&
            (int)offer->GetCount() <= GetPlayerBotProgressionNeed(ch, offer);
    }
    // A skill of the bot's build at Master still short of its books: what the
    // mad scientist goes to the market for (playerbot_rare_persona.h).
    bool PlayerBotNeedsMasterBooks(LPCHARACTER ch) {
        if (!ch || !ch->IsItemLoaded() || !ch->GetSkillGroup()) return false;
        const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
        for (BYTE i = 0; i < build.bSkillCount; ++i) {
            DWORD skill = build.dwSkills[i];
            if (skill && ch->GetSkillMasterType(skill) == SKILL_MASTER &&
                    CountPlayerBotOwnedSkillBooks(ch, skill) < GetPlayerBotBookKeepLimit(ch, skill)) return true;
        }
        return false;
    }
    // Such a skill, and a bot that buys its books: what the look over every
    // stand of the map is for (FindPlayerBotBookPick).
    bool PlayerBotWantsOwnBooks(LPCHARACTER ch) {
        return PlayerBotStudiesBooks(ch) && PlayerBotNeedsMasterBooks(ch);
    }
    // Iwakura's scroll rule (IsPlayerBotScrollRulePiece): what the next step
    // of its weapon - or of its armour, once the weapon is at +8 - lacks, when
    // the counters of the bot's first village hold every unit of it - the
    // ledger's count, asked again at the counter. The trip is how a bot that
    // lives on the frontier meets those counters at all.
    // MT2009_PLUS_M1_LOOP_FIX_V1 (market): units on a counter are a reason to
    // travel to it only for a bot that could pay for them - at the price the
    // counters last asked (or the sales' median), out of
    // PLAYERBOT_MARKET_TRIP_AFFORD_PERCENT of what it can spare. The Orc Tooth
    // stood at 1.2-1.5 million a unit against purses of 1.8-2.5 million, the
    // bots bought none, and its mere supply doubled the trips' places: 78
    // trips, 8 arrivals, the rest ten minutes held in M1 (loop report, 15
    // October). A price nobody has seen yet does not stop the trip; the
    // counter decides then, as before.
    const int PLAYERBOT_MARKET_TRIP_AFFORD_PERCENT = 80;
    bool CanPlayerBotAffordMarketUnits(LPCHARACTER ch, DWORD vnum, int units) {
        if (!ch || units <= 0) return true;
        const DWORD now = get_dword_time();
        DWORD unit = GetPlayerBotLastAsk(vnum, 0, now);
        if (unit == 0) unit = GetPlayerBotSaleUnitPrice(vnum, 0, now, NULL);
        if (unit == 0) return true;
        const long long spare = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
            (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
        return spare > 0 && (long long)unit * units <= spare * PLAYERBOT_MARKET_TRIP_AFFORD_PERCENT / 100;
    }
    bool PlayerBotScrollRuleSupplyExists(LPCHARACTER ch) {
        std::map<DWORD, int> missing;
        CollectPlayerBotScrollRuleMissing(ch, missing);
        if (missing.empty()) return false;
        const long firstVillage = playerbot_empire_rules::GetHomeMap(ch->GetEmpire(),
            playerbot_empire_rules::MAP_ROLE_M1);
        for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end(); ++it)
            if ((int)GetPlayerBotMarketLocalSupply(firstVillage, it->first) < it->second ||
                    !CanPlayerBotAffordMarketUnits(ch, it->first, it->second)) return false;   // MT2009_PLUS_M1_LOOP_FIX_V1
        return true;
    }
    bool PlayerBotNeedsProgressionShopping(LPCHARACTER ch) {
        if (!ch || !ch->IsItemLoaded()) return false;
        if (PlayerBotScrollRuleSupplyExists(ch)) return true;
        // A Stalki its first village's counters hold for it, the scroll rule's
        // way: the bots of sixty-four and more hunt on the frontier and meet
        // those counters on a trip or not at all (playerbot_stalki.h).
        if (PlayerBotStalkiSupplyExists(ch)) return true;
        // MT2009_PLUS_BOT_GEAR_UPGRADE_V1: a weapon its first village's stands
        // hold that hits a tenth harder than its own and that it can pay for
        // (playerbot_gear_upgrade.h) - the frontier bots meet those stands on
        // a trip or not at all, like the scroll rule's.
        if (PlayerBotWantsWeaponUpgradeFromMarket(ch)) return true;
        // MT2009_PLUS_BOT_GEAR_UPGRADE_V2: and an armour a tenth better than
        // the best of its slot.
        if (PlayerBotWantsArmourUpgradeFromMarket(ch)) return true;
        if (!ch->GetSkillGroup()) return false;
        const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
        const bool studies = PlayerBotStudiesAtTheMarket(ch);
        // Books are the trader's too (community patch 2, point 5).
        const bool studiesBooks = studies || PlayerBotStudiesBooks(ch);
        for (BYTE i = 0; studiesBooks && i < build.bSkillCount; ++i) {
            DWORD skill = build.dwSkills[i];
            if (skill && ch->GetSkillMasterType(skill) == SKILL_MASTER &&
                    CountPlayerBotOwnedSkillBooks(ch, skill) < GetPlayerBotBookKeepLimit(ch, skill)) return true;
        }
        if (studies && PlayerBotHasGrandMasterToTrain(ch) &&
                ch->CountSpecifyItem(PLAYERBOT_GRAND_MASTER_STONE_VNUM) < PLAYERBOT_GRAND_MASTER_STONE_KEEP) return true;
        for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i)
            if (GetPlayerBotBiologistPurchaseNeed(ch, PLAYERBOT_BIOLOGIST_MISSIONS[i].itemVnum) > 0) return true;
        return false;
    }

    bool PlayerBotProgressionSupplyExists(LPCHARACTER ch) {
        // The ledger is advisory; the actual offer is revalidated at purchase.
        const bool studies = PlayerBotStudiesAtTheMarket(ch);
        const TPlayerBotMarketLedgerEntry* books = GetPlayerBotMarketLedgerEntry(50300);
        if (PlayerBotStudiesBooks(ch) && books && books->dwSupplyUnits > 0 && ch->GetSkillGroup()) {
            const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
            for (BYTE i = 0; i < build.bSkillCount; ++i) {
                DWORD skill = build.dwSkills[i];
                if (skill && ch->GetSkillMasterType(skill) == SKILL_MASTER &&
                        CountPlayerBotOwnedSkillBooks(ch, skill) < GetPlayerBotBookKeepLimit(ch, skill)) return true;
            }
        }
        const TPlayerBotMarketLedgerEntry* stones = GetPlayerBotMarketLedgerEntry(PLAYERBOT_GRAND_MASTER_STONE_VNUM);
        if (studies && stones && stones->dwSupplyUnits > 0 && PlayerBotHasGrandMasterToTrain(ch) &&
                ch->CountSpecifyItem(PLAYERBOT_GRAND_MASTER_STONE_VNUM) < PLAYERBOT_GRAND_MASTER_STONE_KEEP) return true;
        for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i) {
            const DWORD vnum = PLAYERBOT_BIOLOGIST_MISSIONS[i].itemVnum;
            const TPlayerBotMarketLedgerEntry* supply = GetPlayerBotMarketLedgerEntry(vnum);
            if (supply && supply->dwSupplyUnits > 0 && GetPlayerBotBiologistPurchaseNeed(ch, vnum) > 0 &&
                    CanPlayerBotAffordMarketUnits(ch, vnum, 1)) return true;   // MT2009_PLUS_M1_LOOP_FIX_V1
        }
        return PlayerBotScrollRuleSupplyExists(ch) || PlayerBotStalkiSupplyExists(ch) ||
            PlayerBotWantsWeaponUpgradeFromMarket(ch) ||   // MT2009_PLUS_BOT_GEAR_UPGRADE_V1
            PlayerBotWantsArmourUpgradeFromMarket(ch);     // MT2009_PLUS_BOT_GEAR_UPGRADE_V2
    }
    // Who is out on a trip now, pid -> when it ends. A map rather than a count,
    // so a bot that despawns mid-trip frees its place when the trip would have
    // ended instead of holding it for ever.
    std::map<DWORD, DWORD> s_mapPlayerBotProgressionTrip;

    size_t CountPlayerBotProgressionTrips(DWORD now) {
        for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotProgressionTrip.begin();
                it != s_mapPlayerBotProgressionTrip.end(); ) {
            if ((int)(now - it->second) >= 0) s_mapPlayerBotProgressionTrip.erase(it++);
            else ++it;
        }
        return s_mapPlayerBotProgressionTrip.size();
    }

    bool ShouldPlayerBotVisitProgressionMarket(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        // A dropper's time is its dungeon's (ManagePlayerBotShopping refuses
        // it anyway, so the trip would be ten minutes on the square for
        // nothing), and a bot in a player's party goes where the player goes.
        if (!ch || IsPlayerBotOnAnyHorseTrial(ch) /* MT2009_PLUS_HORSE30_V1 */ ||
                IsPlayerBotDropper(state.bPersonality) ||
                (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()))) {
            if (state.dwProgressionTripUntil) {
                s_mapPlayerBotProgressionTrip.erase(ch ? ch->GetPlayerID() : 0);
                state.dwProgressionTripUntil = 0;
            }
            return false;
        }
        if (state.dwProgressionTripUntil && (int)(now - state.dwProgressionTripUntil) < 0) {
            if (PlayerBotNeedsProgressionShopping(ch)) return true;
            s_mapPlayerBotProgressionTrip.erase(ch->GetPlayerID());
            state.dwProgressionTripUntil = 0;
        }
        // Iwakura's Patch 3, point 7: the mad scientist goes to the market for
        // its books at once, past the share and the clocks - one trip, whose
        // end is the end of the state (playerbot_rare_persona.h).
        if (IsPlayerBotRareNow(state.persona, playerbot_persona::RARE_NAUKOWIEC, now)) {
            if (state.persona.bRareStage != 0 || !PlayerBotNeedsMasterBooks(ch)) return false;
            state.persona.bRareStage = 1;
            state.dwProgressionTripUntil = now + PLAYERBOT_PROGRESSION_TRIP_MS;
            s_mapPlayerBotProgressionTrip[ch->GetPlayerID()] = state.dwProgressionTripUntil;
            sys_log(0, "PLAYERBOT_MARKET: progression trip pid=%u name=%s map=%ld level=%d gold=%lld mad_scientist=1",
                ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (int)ch->GetLevel(), (long long)ch->GetGold());
            return true;
        }
        if (!state.dwProgressionTripNext) {
            state.dwProgressionTripNext = now + PLAYERBOT_PROGRESSION_TRIP_FIRST_MIN_MS +
                PlayerBotNavHash(ch->GetPlayerID()) %
                (PLAYERBOT_PROGRESSION_TRIP_FIRST_MAX_MS - PLAYERBOT_PROGRESSION_TRIP_FIRST_MIN_MS);
            return false;
        }
        if ((int)(now - state.dwProgressionTripNext) < 0) return false;
        state.dwProgressionTripNext = now + PLAYERBOT_PROGRESSION_TRIP_RETRY_MIN_MS +
            PlayerBotNavHash(ch->GetPlayerID() ^ now) %
            (PLAYERBOT_PROGRESSION_TRIP_RETRY_MAX_MS - PLAYERBOT_PROGRESSION_TRIP_RETRY_MIN_MS);
        if ((long long)ch->GetGold() <= GetPlayerBotReservedGold(ch) + PLAYERBOT_SHOPPING_GOLD_FLOOR ||
                !PlayerBotNeedsProgressionShopping(ch) || !PlayerBotProgressionSupplyExists(ch)) return false;
        // MT2009_PLUS_BOT_BIOLOGIST_EAGER_V1: a Biologist's specimen a counter
        // holds for it is a trip with twice the places - the market is the
        // quick way through a row ("kupuja potrzebne przedmioty na rynku albo
        // je dropia", the owner, 9 October).
        bool biologistSupply = false;
        for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT && !biologistSupply; ++i) {
            const DWORD vnum = PLAYERBOT_BIOLOGIST_MISSIONS[i].itemVnum;
            const TPlayerBotMarketLedgerEntry* supply = GetPlayerBotMarketLedgerEntry(vnum);
            biologistSupply = supply && supply->dwSupplyUnits > 0 && GetPlayerBotBiologistPurchaseNeed(ch, vnum) > 0 &&
                CanPlayerBotAffordMarketUnits(ch, vnum, 1);   // MT2009_PLUS_M1_LOOP_FIX_V1
        }
        const size_t cap = std::max<size_t>(1,
            (size_t)GetPlayerBotsAlive() * PLAYERBOT_PROGRESSION_TRIP_PER_MILLE / 1000) * (biologistSupply ? 2 : 1);
        if (CountPlayerBotProgressionTrips(now) >= cap) return false;
        state.dwProgressionTripUntil = now + PLAYERBOT_PROGRESSION_TRIP_MS;
        s_mapPlayerBotProgressionTrip[ch->GetPlayerID()] = state.dwProgressionTripUntil;
        sys_log(0, "PLAYERBOT_MARKET: progression trip pid=%u name=%s map=%ld level=%d gold=%lld trips=%u cap=%u scroll_rule=%d stalki=%d",
            ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (int)ch->GetLevel(),
            (long long)ch->GetGold(), (unsigned)s_mapPlayerBotProgressionTrip.size(), (unsigned)cap,
            PlayerBotScrollRuleSupplyExists(ch) ? 1 : 0, PlayerBotStalkiSupplyExists(ch) ? 1 : 0);
        return true;
    }
}
#endif
