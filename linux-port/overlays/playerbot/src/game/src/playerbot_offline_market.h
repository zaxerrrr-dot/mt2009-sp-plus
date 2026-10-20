#ifndef PLAYERBOT_OFFLINE_MARKET_H
#define PLAYERBOT_OFFLINE_MARKET_H
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
// Included after playerbot_market.h so the existing demand/gear rules are used.
// MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): the part of a stack a purchase takes
// (ikarus_shop_manager.cpp, MT2009_PLUS_SHOP_QOL_V2 (buy part) - the shop
// window's /ikashop_buy_part sets it the same way).
namespace ikashop { extern DWORD g_fleaBuyQuantity; }
namespace {
    // The line a walk over from a second village is for. Every bot of a
    // village read the same first village's lines and set off for the best
    // of them, and of the first 155 walks on the test world 31 found their
    // line sold on arrival - 29 of them to another bot that had walked over
    // for the same line (23 September). A walk claims its line for as long
    // as the walk and the ride to the stand may take, and every other look,
    // the browse of the stands in reach included, passes over it.
    struct TPlayerBotFarClaim { DWORD pid; DWORD until; };
    std::unordered_map<DWORD, TPlayerBotFarClaim> s_mapPlayerBotFarClaims;

    bool IsPlayerBotLineClaimedByOther(DWORD itemId, DWORD pid, DWORD now) {
        auto it = s_mapPlayerBotFarClaims.find(itemId);
        if (it == s_mapPlayerBotFarClaims.end()) return false;
        if (playerbot_offline::Due(now, it->second.until)) {
            s_mapPlayerBotFarClaims.erase(it);
            return false;
        }
        return it->second.pid != pid;
    }
    void ClaimPlayerBotLineUntil(DWORD itemId, DWORD pid, DWORD now, DWORD until) {
        if (!itemId) return;
        // A claim whose walk ended some other way than at the stand is left
        // to run out, and the ones that did are swept once the map is big.
        if (s_mapPlayerBotFarClaims.size() >= 4096)
            for (auto it = s_mapPlayerBotFarClaims.begin(); it != s_mapPlayerBotFarClaims.end(); )
                it = playerbot_offline::Due(now, it->second.until) ? s_mapPlayerBotFarClaims.erase(it) : std::next(it);
        s_mapPlayerBotFarClaims[itemId] = TPlayerBotFarClaim{ pid, until };
    }
    void ClaimPlayerBotFarLine(DWORD itemId, DWORD pid, DWORD now) {
        ClaimPlayerBotLineUntil(itemId, pid, now,
            now + PLAYERBOT_MARKET_JOAN_WALK_TIMEOUT + PLAYERBOT_MARKET_FAR_PICK_WALK_MS);
    }
    void ReleasePlayerBotFarLine(DWORD itemId, DWORD pid) {
        auto it = s_mapPlayerBotFarClaims.find(itemId);
        if (it != s_mapPlayerBotFarClaims.end() && it->second.pid == pid)
            s_mapPlayerBotFarClaims.erase(it);
    }

    // The buyer gives its pick up. A pick a walk over was made for says why,
    // once: the lines left after the claim are the ones whose reason is not
    // yet known, and "every way this function can decline looks identical
    // from outside" is how a walk over came to end nine times in ten with
    // nothing bought.
    void DropPlayerBotOfflinePick(LPCHARACTER ch, TPlayerBotAIState& state, const char* reason) {
        auto& o = state.offlineShop;
        if (o.buyOwner) {
            ReleasePlayerBotFarLine(o.buyItem, ch->GetPlayerID());
            if (o.farBuy)
                sys_log(0, "PLAYERBOT_MARKET: far pick lost pid=%u name=%s owner=%u item=%u reason=%s",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, reason);
        }
        o.farBuy = false;
        o.buyOwner = 0;
        o.buyQuantity = 0;
        o.haggleItem = 0;
        o.hagglePrice = 0;
    }

    // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1 (the owner, 16 October: "Niech boty jak
    // skupuja z rynku przedmioty niech preferuja przedmioty z bonusami (takie
    // jak im sa obecnie potrzebne). Jesli maja wybor przedmiot 0 bonusow i 2
    // bonusy i maja odpowiednia ilosc pieniedzy, wybieraja ten z 2 bonusami
    // aby w przyszlosci go dodac bonusy lub zacząć zmieniac bonusy aby wbic
    // lepszy eq"). The lines of a weapon or an armour piece the bot would
    // wear that are of use to it now: the bonus planner's own measure
    // (ScorePlayerBotBonusLine for the slot the piece goes in) of a line
    // Iwakura's PvE table does not rate under neutral for its class
    // (GetPlayerBotBonusTier: unrated, or PLAYERBOT_BUY_BONUS_USEFUL_TIER and
    // up) - a bad or a very bad line is no reason to pay more. Zero for
    // anything the bot does not wear (resale, materials, whims).
    const int PLAYERBOT_BUY_BONUS_USEFUL_TIER = 4;
    // The dearer, more useful line wins only while what it costs over the
    // cheaper one is at most this share of what the bot may spend now
    // (Affordable: the wallet less the gold it keeps for its other plans,
    // GetPlayerBotReservedGold) - the rest stays for those plans.
    const int PLAYERBOT_BUY_BONUS_PREF_BUDGET_PERCENT = 50;

    int CountPlayerBotUsefulBuyLines(LPCHARACTER ch, LPITEM item, int* cellOut = NULL) {
        if (cellOut) *cellOut = -1;
        if (!ch || !item || (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR) ||
                (item->GetType() == ITEM_WEAPON && item->GetSubType() == WEAPON_ARROW) ||
                !IsPlayerBotEquipmentCandidate(ch, item))
            return 0;
        const int cell = item->FindEquipCell(ch);
        if (cell < 0 || cell >= WEAR_MAX_NUM) return 0;
        if (cellOut) *cellOut = cell;
        int useful = 0;
        for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i) {
            const BYTE type = item->GetAttributeType(i);
            const long value = item->GetAttributeValue(i);
            if (type == APPLY_NONE || value <= 0) continue;
            const int tier = GetPlayerBotBonusTier(type, (int)ch->GetJob(), false);
            if (tier != 0 && tier < PLAYERBOT_BUY_BONUS_USEFUL_TIER) continue;
            if (ScorePlayerBotBonusLine(ch, (BYTE)cell, type, (short)std::min<long>(value, 32767)) > 0) ++useful;
        }
        return useful;
    }

    // Between two lines for the same need (the same slot, the same rank of
    // the search that found them): the one of more useful lines while its
    // extra cost fits PLAYERBOT_BUY_BONUS_PREF_BUDGET_PERCENT of `budget`,
    // else the cheaper - the old rule, which also decides an equal count.
    bool PlayerBotBuyPrefers(int useful, long long price, int bestUseful, long long bestPrice, long long budget) {
        const long long allowance = std::max<long long>(0, budget) * PLAYERBOT_BUY_BONUS_PREF_BUDGET_PERCENT / 100;
        if (useful > bestUseful) return price <= bestPrice || price - bestPrice <= allowance;
        if (useful < bestUseful) return price < bestPrice && bestPrice - price > allowance;
        return price < bestPrice;
    }

    // A search's best line so far, with what the preference did to it, for
    // the log line once the pick is made.
    struct TPlayerBotBuyBest {
        int priority = -1, cell = -1, useful = 0;
        long long price = 0;
        long long plainPrice = 0;   // the cheaper line of fewer useful lines it won over
        int plainUseful = 0;
        // Whether a line rated `priority` (-1: not bought) takes the place.
        bool Take(int newPriority, long long newPrice, int newCell, int newUseful, long long budget) {
            if (newPriority < 0 || newPriority < priority) return false;
            bool wins;
            bool sameNeed = newPriority == priority && newCell >= 0 && newCell == cell;
            if (newPriority > priority) wins = true;
            else if (sameNeed) wins = PlayerBotBuyPrefers(newUseful, newPrice, useful, price, budget);
            else wins = newPrice < price;
            if (!wins) {
                // A cheaper line of fewer useful lines the best stays over.
                if (sameNeed && useful > newUseful && newPrice < price &&
                        (plainPrice == 0 || newPrice < plainPrice)) {
                    plainPrice = newPrice;
                    plainUseful = newUseful;
                }
                return false;
            }
            if (sameNeed && newUseful > useful && newPrice > price) {
                plainPrice = price;
                plainUseful = useful;
            } else if (!sameNeed || newUseful <= plainUseful) {
                plainPrice = 0;
                plainUseful = 0;
            }
            priority = newPriority;
            price = newPrice;
            cell = newCell;
            useful = newUseful;
            return true;
        }
        void Log(LPCHARACTER ch, const char* where, DWORD owner, DWORD item) const {
            if (!ch || plainPrice <= 0 || useful <= plainUseful || price <= plainPrice) return;
            sys_log(0, "PLAYERBOT_MARKET: preferred bonused listing pid=%u name=%s search=%s owner=%u item=%u useful=%d price=%lld over plain useful=%d price=%lld gold=%lld",
                ch->GetPlayerID(), ch->GetName(), where, owner, item, useful, price, plainUseful, plainPrice,
                (long long)ch->GetGold());
        }
    };

    // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1 (the owner, 20 October): a
    // person's line wins over a bot's while it asks at most
    // SHOP_PLAYER_PREF_PCT (10%) more - the price a search ranks a line by is
    // a person's price / 1.10. Only the ranking: the purse pays the real price
    // and a person's price still has to be fair (CanPlayerBotPayForOffer).
    long long PlayerBotOfferRankPrice(DWORD ownerPid, long long price) {
        const int pct = GetPlayerBotShopMgmt(PLAYERBOT_SM_PLAYER_PREF_PCT);
        if (price <= 0) return price;
        if (!CPlayerBotManager::instance().IsRegisteredBotPID(ownerPid))
            return pct > 0 ? price * 100 / (100 + pct) : price;
        // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 1): and a bot's counter over its
        // fill target is ranked SHOP_MGMT_FULL_PREF_PCT cheaper, so the buyers
        // empty the full counters first (known by owner for a minute).
        const int fullPct = IsPlayerBotShopMgmtOn() ? GetPlayerBotShopMgmt(PLAYERBOT_SM_FULL_PREF_PCT) : 0;
        if (fullPct <= 0) return price;
        static std::unordered_map<DWORD, std::pair<DWORD, bool> > s_overTarget;
        const DWORD now = get_dword_time();
        auto known = s_overTarget.find(ownerPid);
        if (known == s_overTarget.end() || now - known->second.first >= 60000) {
            if (s_overTarget.size() > 8192) s_overTarget.clear();
            auto shop = ikashop::GetManager().GetShopByOwnerID(ownerPid);
            const bool over = shop && BotOfflineUsedCells(shop) > BotOfflineTargetCells();
            known = s_overTarget.insert_or_assign(ownerPid, std::make_pair(now ? now : 1, over)).first;
        }
        return known->second.second ? price * 100 / (100 + fullPct) : price;
    }

    // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5: "daj botom mozliwosc kupowania
    // pojedynczych przedmiotow ze stacka"): the price of `quantity` pieces of
    // a line of `lineCount`, as the engine reckons it (rounded up, and never
    // the whole line's price) - 0 when the line cannot be split so.
    long long PlayerBotPartPrice(long long lineYang, long long lineCount, long long quantity) {
        if (lineCount <= 1 || quantity <= 0 || quantity >= lineCount) return 0;
        const long long part = (lineYang * quantity + lineCount - 1) / lineCount;
        return part > 0 && lineYang - part >= 1 ? part : 0;
    }
    bool IsPlayerBotPartBuyOn() {
        return IsPlayerBotShopMgmtOn() && GetPlayerBotShopMgmt(PLAYERBOT_SM_PART_BUY) != 0;
    }
    // The most pieces of a stack line - fewer than all, `maxQuantity` at most
    // (0: no cap) - this bot would buy and could pay for, asked of the line's
    // preview cut to that count with the purchase's own tests
    // (WantsPlayerBotStallItem, CanPlayerBotPayForOffer at the part's price).
    // Both only say no to more once they say no, so the most is found by
    // halving. 0 when no part is bought; the preview keeps its count.
    int PlayerBotPartBuyCount(LPCHARACTER ch, LPITEM preview, long long lineYang, DWORD owner, int maxQuantity,
            long long& partYang) {
        partYang = 0;
        if (!ch || !preview || !IsPlayerBotPartBuyOn() || !preview->IsStackable()) return 0;
        const int count = (int)preview->GetCount();
        if (count <= 1) return 0;
        const int top = maxQuantity > 0 ? std::min(count - 1, maxQuantity) : count - 1;
        auto takes = [&](int quantity) {
            const long long part = PlayerBotPartPrice(lineYang, count, quantity);
            if (part <= 0) return false;
            preview->SetCount(quantity);
            return WantsPlayerBotStallItem(ch, preview) && CanPlayerBotPayForOffer(ch, preview, part, owner) &&
                    ch->GetEmptyInventory(preview->GetSize()) >= 0;
        };
        int best = 0;
        if (top >= 1 && takes(1)) {
            best = 1;
            int low = 2, high = top;
            while (low <= high) {
                const int mid = low + (high - low) / 2;
                if (takes(mid)) { best = mid; low = mid + 1; }
                else high = mid - 1;
            }
        }
        preview->SetCount(count);
        if (best > 0) partYang = PlayerBotPartPrice(lineYang, count, best);
        return partYang > 0 ? best : 0;
    }

    // One line of one stand as this bot would rate it: -1 for a line it would
    // not buy, else the priority a browse ranks by. The browse of the stands
    // in reach and the look at the first village's from a second village
    // (FindPlayerBotFarOfflinePick) ask this one function, so a walk over is
    // made for exactly what the buyer would take on arrival.
    template<class Shop, class Line>
    int RatePlayerBotOfflineLine(LPCHARACTER ch, const Shop& shop, const Line& line,
            long long budget, bool personFirst, long long& outPrice, int* cellOut = NULL, int* usefulOut = NULL,
            int* partOut = NULL, int* partTries = NULL) {
        if (cellOut) *cellOut = -1;
        if (usefulOut) *usefulOut = 0;
        if (partOut) *partOut = 0;
        if (!line) return -1;
        long long price = (long long)line->GetPrice().GetTotalYangAmount();
        // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): a stack dearer than the
        // budget may still sell the bot a part of it, below.
        const bool partCandidate = partOut && partTries && *partTries > 0 && IsPlayerBotPartBuyOn() &&
                line->GetInfo().count > 1;
        if (price <= 0 || (price > budget && !partCandidate)) return -1;
        auto preview = BotOfflinePreview(*line);
        if (!preview) return -1;
        // MT2009_PLUS_MARKET_LIFE_V1, point 9: a whim's line (a bargain, an
        // impulse) ranks under every line the bot needs.
        bool own = WantsPlayerBotStallItemOwn(ch, preview);
        bool want = price <= budget && (own || IsPlayerBotWhimCandidate(ch, preview)) &&
            CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
        // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): the whole stack is not for
        // this bot, the part it needs and can pay for is (a few such looks a
        // browse, partTries).
        if (!want && partCandidate) {
            --*partTries;
            long long partYang = 0;
            const int part = PlayerBotPartBuyCount(ch, preview, price, shop->GetOwnerPID(), 0, partYang);
            if (part > 0 && partYang <= budget) {
                preview->SetCount(part);
                price = partYang;
                own = WantsPlayerBotStallItemOwn(ch, preview);
                want = true;
                *partOut = part;
            }
        }
        int priority = (IsPlayerBotProgressionOffer(ch, preview) ? 200 : 0) + (own ? 1 : 0);
        // The class's level-30 weapon comes first, and of those the
        // highest average line, the price only breaking a tie: "12% za
        // 300k albo 26% za 450k - wybierze drozsza" (community patch 2).
        // A finished piece the market Perfectionist's anvil waits for.
        if (want && priority < 300 && IsPlayerBotReadyGearOffer(ch, preview))
            priority = 300;
        // A Stalki project (playerbot_stalki.h) under the level-30 weapon, the
        // higher plus first.
        if (want && IsPlayerBotStalkiProjectOffer(ch, preview))
            priority = 350 + std::min<int>(9, (int)preview->GetRefineLevel());
        if (want && IsPlayerBotClassLevel30Weapon(ch, preview))
            priority = 400 + (int)std::min<long>(99, std::max<long>(0,
                SumPlayerBotItemLines(preview, APPLY_NORMAL_HIT_DAMAGE_BONUS)));
        if (want && personFirst &&
                !CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID())) {
            const long long fair = GetPlayerBotShopAskingPrice(preview);
            if (fair > 0 && price <= fair * PLAYERBOT_MARKET_PERSON_PRICE_PERCENT / 100)
                priority += 100;
        }
        // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: a piece the bot wants for itself
        // says its slot and its useful lines, for the browse's tie-break.
        if (want && own && (cellOut || usefulOut)) {
            int cell = -1;
            const int useful = CountPlayerBotUsefulBuyLines(ch, preview, &cell);
            if (cellOut) *cellOut = cell;
            if (usefulOut) *usefulOut = useful;
        }
        M2_DELETE(preview);
        outPrice = price;
        if (!want && partOut) *partOut = 0;
        return want ? priority : -1;
    }

    // The people's stands among `shops`, every line up to
    // PLAYERBOT_MARKET_PERSON_LOOK_LINES, for a browse that looks at them
    // first: the window below reads sixty-four lines from a cursor, and a
    // first village holds some ten thousand.
    template<class Shops, class Visitor>
    void BrowsePlayerBotPersonLines(const Shops& shops, Visitor visit) {
        unsigned checked = 0;
        for (const auto& entry : shops) {
            const auto& shop = entry.second;
            if (CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID()))
                continue;
            for (const auto& [id, line] : shop->GetItems()) {
                if (++checked > PLAYERBOT_MARKET_PERSON_LOOK_LINES)
                    return;
                visit(shop, id, line);
            }
        }
    }

    // MT2009_PLUS_BOT_SHAMAN_INT_SET_V1: a piece for a Shaman's INT set
    // (playerbot_shaman_buff_set.h) out of its share - up to 40% of what the
    // bot can spend (MT2009_PLUS_BOT_SHAMAN_INT_SET_V2) - and a person's line no dearer than the bots'
    // cap on a person's price.
    bool IsPlayerBotBuffSetOffer(LPCHARACTER ch, LPITEM item, long long price, DWORD sellerPID) {
        if (!ch || !item || price <= 0 || !WantsPlayerBotBuffSetPiece(ch, item)) return false;
        const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - PLAYERBOT_SHOPPING_GOLD_FLOOR;
        if (price > spare * PLAYERBOT_BUFF_SET_BUDGET_PERCENT / 100) return false;
        if (IsPlayerBotPriceSlipOffer(item, price)) return false;
        return sellerPID == 0 || CPlayerBotManager::instance().IsRegisteredBotPID(sellerPID) ||
                IsPlayerBotPersonPriceFair(ch, item, price);
    }

    // The buyer's pick, taken to its stand and bought: the walk, the keeper's
    // edit mode waited out, the line asked again on arrival, and the request
    // to the db core, which delivers. True while it has the tick; false once
    // the pick is spent - asked for, or lost and said why. The browse below
    // and a gambler's walk along the counters (ManagePlayerBotGambleMarket)
    // both hand it their line.
    // MT2009_PLUS_PLAIN_GEAR_WINDOW_V1 (the owner, 8 October, the supporters'
    // market: "dlaczego wystawione sa tylko tarcze z bonusami?"). The bots do
    // list their plain gear - Czarna Okragla Tarcza+2 at 205 000-290 000 there -
    // but another bot bought each plain line as its armour upgrade within five
    // to twenty-five minutes of the add (listed_s 326-1458 in its syslog), and
    // the bonused copies at 1.3-5.5 million stood: a person searching the
    // market saw none without bonuses (0 plain lines of 13042, 89 bonused).
    // A plain weapon or armour piece of level PLAYERBOT_PLAIN_GEAR_WINDOW_MIN_LEVEL
    // and up a bot stand put up is for people for its first
    // PLAYERBOT_PLAIN_GEAR_WINDOW_MS: no bot buys it before. Known by the
    // keeper's own clock of its lines (offlineShop.listed), so only on the core
    // that added it; a line of unknown age is anybody's.
    const DWORD PLAYERBOT_PLAIN_GEAR_WINDOW_MS = 30 * 60 * 1000;
    const int PLAYERBOT_PLAIN_GEAR_WINDOW_MIN_LEVEL = 30;

    bool IsPlayerBotPlainGearLineForPeople(DWORD owner, DWORD itemId, const TItemTable* table,
            const TPlayerItemAttribute* attrs, DWORD now) {
        if (!table || !attrs || (table->bType != ITEM_WEAPON && table->bType != ITEM_ARMOR) ||
                (table->bType == ITEM_WEAPON && table->bSubType == WEAPON_ARROW) ||
                GetPlayerBotProtoLevelLimit(table) < PLAYERBOT_PLAIN_GEAR_WINDOW_MIN_LEVEL)
            return false;
        for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
            if (attrs[a].bType != 0)
                return false;
        TPlayerBotAIStateMap::const_iterator keeper = s_mapPlayerBotAIStates.find(owner);
        if (keeper == s_mapPlayerBotAIStates.end())
            return false;
        const auto listed = keeper->second.offlineShop.listed.find(itemId);
        if (listed == keeper->second.offlineShop.listed.end() || listed->second.when == 0)
            return false;
        return now - listed->second.when < PLAYERBOT_PLAIN_GEAR_WINDOW_MS;
    }

    bool RunPlayerBotOfflinePick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        auto& o = state.offlineShop;
        auto& manager = ikashop::GetManager();
        if (!o.buyOwner) return false;
        if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL) {
            // Something worth buying, on the shop channel: ask to be moved, at
            // most this often, and forget the pick - the purchase is made there,
            // by the browse after the move.
            DropPlayerBotOfflinePick(ch, state, "other_channel");
            if (Due(now, state.dwNextBuyChannelRequestTime)) {
                state.dwNextBuyChannelRequestTime = now + PLAYERBOT_SHOP_CHANNEL_BUY_REQUEST_GAP_MS;
                if (CPlayerBotManager::instance().RequestShopChannel(ch->GetPlayerID()))
                    PlayerBotLogThrottled("shop_channel_buy", now,
                            "PLAYERBOT_CHANNEL: pid=%u name=%s asks for the shop channel to buy (here %u)",
                            ch->GetPlayerID(), ch->GetName(), (unsigned int)g_bChannel);
            }
            return false;
        }
        auto shop = manager.GetShopByOwnerID(o.buyOwner);
        const char* lost = !shop ? "shop_gone" : shop->GetDuration() == 0 ? "shop_expired" :
            Due(now, o.buyUntil) ? "timeout" :
            (shop->GetSpawn().map != ch->GetMapIndex() || shop->GetSpawn().channel != g_bChannel) ? "elsewhere" : NULL;
        if (lost) {
            DropPlayerBotOfflinePick(ch, state, lost);
            ClearPlayerBotRoute(state, true);
            return false;
        }
        auto line = shop->GetItem(o.buyItem);
        if (!line) { DropPlayerBotOfflinePick(ch, state, "sold"); return false; }
        // MT2009_PLUS_PLAIN_GEAR_WINDOW_V1: a fresh plain piece is the people's.
        if (IsPlayerBotPlainGearLineForPeople(o.buyOwner, o.buyItem, line->GetTable(), line->GetInfo().aAttr, now)) {
            DropPlayerBotOfflinePick(ch, state, "plain_gear_for_people");
            return false;
        }
        SetPlayerBotAction(state, BOT_ACTION_TRAVEL, now);
        if (!MovePlayerBotTownLeg(ch, state, now, shop->GetSpawn().x, shop->GetSpawn().y, 600)) return true;
        // The keeper is serving its stand, which is a few seconds of edit
        // mode: the buyer waits them out at the counter instead of giving up
        // the line it came for - which it did, whatever the walk had cost.
        if (shop->IsEditMode()) return true;
        auto price = line->GetPrice().GetTotalYangAmount();
        auto finalPreview = BotOfflinePreview(*line);
        // MT2009_PLUS_BOT_SHAMAN_INT_SET_V1: or a piece for the Shaman's INT set.
        const bool setPiece = finalPreview && IsPlayerBotBuffSetOffer(ch, finalPreview, price, shop->GetOwnerPID());
        // MT2009_PLUS_BOT_HAGGLE_V2: a deal is a deal. The line the bot haggled
        // for, at the price agreed or less, is bought whatever the purse's
        // rules say of it now - the gold the bot holds and room in the bag are
        // all it asks. The rules re-asked here (a reserve grown since, the
        // person's cap drawn again) withdrew from deals the owner had kept.
        const bool haggled = finalPreview && o.haggleItem == o.buyItem && o.hagglePrice > 0 &&
                (long long)price <= o.hagglePrice &&
                (long long)ch->GetGold() - PLAYERBOT_SHOPPING_GOLD_FLOOR >= (long long)price;
        // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): the part of the stack the
        // pick was for (o.buyQuantity), asked again at the counter - or, the
        // whole line no longer for this bot, the part it would take now.
        const DWORD lineCount = (DWORD)line->GetInfo().count;
        DWORD part = 0;
        long long payPrice = (long long)price;
        bool wanted = false, payable = false;
        if (finalPreview && !haggled && !setPiece && o.buyQuantity > 0 && o.buyQuantity < lineCount) {
            long long partYang = 0;
            const int q = PlayerBotPartBuyCount(ch, finalPreview, (long long)price, shop->GetOwnerPID(),
                    (int)o.buyQuantity, partYang);
            if (q > 0) {
                part = (DWORD)q;
                payPrice = partYang;
                finalPreview->SetCount(part);
                wanted = payable = true;
            }
        } else {
            wanted = finalPreview && (haggled || setPiece || WantsPlayerBotStallItem(ch, finalPreview));
            payable = wanted && (haggled || setPiece || CanPlayerBotPayForOffer(ch, finalPreview, price, shop->GetOwnerPID()));
            if (!payable && finalPreview && !haggled && !setPiece && lineCount > 1) {
                long long partYang = 0;
                const int q = PlayerBotPartBuyCount(ch, finalPreview, (long long)price, shop->GetOwnerPID(), 0, partYang);
                if (q > 0) {
                    part = (DWORD)q;
                    payPrice = partYang;
                    finalPreview->SetCount(part);
                    wanted = payable = true;
                }
            }
        }
        const bool stillWanted = payable && ch->GetEmptyInventory(finalPreview->GetSize()) >= 0;
        // MT2009_PLUS_MARKET_LIFE_V1, point 9: a bargain's or an impulse's line.
        const int whim = stillWanted && !haggled && !setPiece && !WantsPlayerBotStallItemOwn(ch, finalPreview)
            ? GetPlayerBotWhimKind(ch, finalPreview, payPrice, shop->GetOwnerPID()) : 0;
        if (finalPreview) M2_DELETE(finalPreview);
        if (!stillWanted) {
            DropPlayerBotOfflinePick(ch, state, !wanted ? "no_longer_wanted" : !payable ? "cannot_pay" : "no_room");
            ClearPlayerBotRoute(state, true);
            return false;
        }
        if (!BotOfflineBudget(now)) return true;
        // Read before the request: the log line below must not touch the shop
        // line once the purchase is in the engine's hands.
        const DWORD boughtVnum = line->GetInfo().vnum;
        // MT2009_PLUS_BOT_SHOP_MGMT_V1: what this purchase takes and pays.
        const DWORD boughtCount = part ? part : lineCount;
        if (boughtVnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM)
            NotePlayerBotChestBought(ch->GetPlayerID(), now);
        NotePlayerBotMinigameChestBought(ch, boughtVnum, payPrice, boughtCount); // MT2009_PLUS_BOT_MINIGAMES_V1
        NotePlayerBotRecipeBought(ch, boughtVnum, payPrice);   // MT2009_PLUS_BOT_HERBALIST_BREW_V2
        if (IsPlayerBotSashVnum(boughtVnum))
            NotePlayerBotSashBought(ch, boughtVnum, payPrice);
        NotePlayerBotSaddlebagBought(ch, boughtVnum, payPrice, boughtCount);
        NotePlayerBotCorBought(ch, boughtVnum, payPrice, boughtCount); // MT2009_PLUS_MARKET_SINK_V1
        NotePlayerBotGuildMaterialBought(ch, boughtVnum, payPrice);
        NotePlayerBotCraftBought(ch, boughtVnum, payPrice); // MT2009_PLUS_BOT_WORKSHOP_V1
        if (Begin(ch->GetPlayerID(), Buy, o.buyItem, now)) {
            auto& request = requests.at(ch->GetPlayerID());
            request.vnum = line->GetInfo().vnum;
            request.count = boughtCount;
            request.unitPrice = uint32_t(payPrice / std::max<uint32_t>(1, request.count));
            if (auto preview = BotOfflinePreview(*line)) {
                request.refine = preview->GetRefineLevel();
                request.level30 = IsPlayerBotClassLevel30Weapon(ch, preview);
                request.gambleBase = IsPlayerBotGamblerBaseOffer(ch, preview);
                request.skill = preview->GetType() == ITEM_SKILLBOOK ? GetPlayerBotSkillBookSkillVnum(preview) : 0;
                // Out of the book purse as it is asked for: a refused purchase
                // costs a window's share, which the next window gives back.
                if (preview->GetType() == ITEM_SKILLBOOK)
                    NotePlayerBotBookBought(ch, payPrice);
                M2_DELETE(preview);
            }
            manager.RecvShopOpenClientPacket(ch, o.buyOwner);
            // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): a part of the stack, the
            // engine's part purchase (the seen price is the whole line's).
            ikashop::g_fleaBuyQuantity = part;
            manager.RecvShopBuyItemClientPacket(ch, o.buyOwner, o.buyItem, false, price);
            ikashop::g_fleaBuyQuantity = 0;
            const bool sent = EndCall(ch->GetPlayerID());
            manager.RecvCloseShopGuestClientPacket(ch);
            if (sent && whim)
                NotePlayerBotWhimBought(ch, whim, boughtVnum, payPrice);
            sys_log(0, "PLAYERBOT_OFFLINE: purchase_requested buyer=%u owner=%u item=%u vnum=%u price=%lld part=%u of=%u sent=%d",
                ch->GetPlayerID(), o.buyOwner, o.buyItem, (unsigned int)boughtVnum, payPrice,
                (unsigned int)part, (unsigned int)lineCount, sent);
        }
        ReleasePlayerBotFarLine(o.buyItem, ch->GetPlayerID());
        o.farBuy = false;
        o.buyOwner = 0;
        o.buyQuantity = 0;
        o.haggleItem = 0;
        o.hagglePrice = 0;
        ClearPlayerBotRoute(state, true);
        return false; // DB completion owns delivery; never synthesize money/items
    }

    // Defined below, with the gambler's walk along the counters it was
    // written for.
    bool FindPlayerBotGambleMaterialPick(LPCHARACTER ch, TPlayerBotAIState& state,
            const std::map<DWORD, int>& missing, long long cap, DWORD now);
    bool FindPlayerBotRareGamblerBasePick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now);
    bool FindPlayerBotStalkiPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now);
    bool FindPlayerBotBookPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now);
    bool FindPlayerBotOutdatedGearPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now);
    bool FindPlayerBotWeaponUpgradePick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now); // MT2009_PLUS_BOT_GEAR_UPGRADE_V1
    bool FindPlayerBotArmourUpgradePick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now); // MT2009_PLUS_BOT_GEAR_UPGRADE_V2
    bool FindPlayerBotBuffSetPick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now);
    bool FindPlayerBotSinkGoodsPick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now);
    // MT2009_PLUS_HORSE_ECONOMY_V2: the sink goods' scan of one map's stands.
    bool ScanPlayerBotSinkGoods(LPCHARACTER ch, long mapIndex, DWORD now, DWORD& owner, DWORD& item,
            DWORD& vnum, long long& unit, DWORD* partOut = NULL);
    // MT2009_PLUS_BOT_HAGGLE_V1: defined in playerbot_haggle.h, after the
    // whisper and the item link.
    bool TryStartPlayerBotHaggle(LPCHARACTER ch, TPlayerBotAIState& state,
            const std::vector<std::pair<int, NativeShop> >& shops, DWORD now);
    bool WatchPlayerBotHaggle(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now);

    bool ManagePlayerBotOfflineShopping(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        auto& o = state.offlineShop;
        auto& manager = ikashop::GetManager();
        // A gambler between the storekeeper and the anvil walks its own pick
        // (ManagePlayerBotGambleMarket, from the town visit, which runs after
        // this pass). The visit is what makes the bot busy below, and dropping
        // the pick there handed the gambler the same line again every tick:
        // eight "goes for materials" for one line in four seconds, and a
        // purchase only where the stand was in reach at once (m2zip,
        // 26 September: 4 lines bought of 167 picks).
        if (state.bTownVisitPhase == BOT_TOWN_PHASE_GAMBLE_MARKET)
            return false;
        const bool busy = BotOfflineBusy(ch, state);
        if (busy || requests.count(ch->GetPlayerID()) || o.visiting || state.bMarketTrip) {
            if (o.buyOwner)
                DropPlayerBotOfflinePick(ch, state, busy ? "busy" : o.visiting ? "service_visit" :
                    requests.count(ch->GetPlayerID()) ? "request_in_flight" : "market_trip");
            return false;
        }
        long pitchX = 0, pitchY = 0;
        if (!GetPlayerBotShopCentre(ch->GetMapIndex(), pitchX, pitchY)) return false;
        // MT2009_PLUS_BOT_HAGGLE_V1: a person's line the bot haggled for, at
        // the price agreed now, is this buyer's pick before anything else.
        if (!o.buyOwner && WatchPlayerBotHaggle(ch, state, now))
            return RunPlayerBotOfflinePick(ch, state, now);
        // The finished piece the anvil is waiting for, found line by line while
        // the bot stood at the blacksmith, is this buyer's pick before any
        // browse: it may stand anywhere on the map's ring, where a browse of
        // sixty-four lines a look does not reach inside the wait.
        if (!o.buyOwner && o.readyPickOwner) {
            if (!Due(now, o.readyPickUntil)) {
                o.buyOwner = o.readyPickOwner;
                o.buyItem = o.readyPickItem;
                o.buyQuantity = 0;
                o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
            }
            o.readyPickOwner = o.readyPickItem = o.readyPickUntil = 0;
        }
        if (!o.buyOwner) {
            if (!Due(now, o.nextBrowse)) return false;
            o.buyQuantity = 0;   // MT2009_PLUS_BOT_SHOP_MGMT_V1: each pick says its own part
            // MT2009_PLUS_DROPPER_INVEST_V1: a dropper's window is short, so
            // it looks again soon while the window lasts.
            const bool dropperWindow = IsPlayerBotDropper(state.bPersonality) &&
                    IsPlayerBotDropperShopping(ch->GetPlayerID(), now);
            // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 1): while the bots' counters
            // are glutted (IsPlayerBotShopGlut) a bot with gold over its
            // reserves looks again in SHOP_MGMT_BROWSE_PCT of the time.
            DWORD browseGap = (DWORD)number(120000, 240000);
            if (IsPlayerBotShopGlut() &&
                    Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR) > 0)
                browseGap = browseGap * (DWORD)GetPlayerBotShopMgmt(PLAYERBOT_SM_BROWSE_PCT) / 100U;
            o.nextBrowse = now + (dropperWindow ? PLAYERBOT_DROPPER_SHOP_BROWSE_MS : browseGap);
            // A guild master whose next building lacks materials looks for
            // them on every stand of the map, the gambler's way, paying out of
            // the guild's fund - which the budget below leaves out, being
            // reserved (playerbot_guild_land.h).
            {
                std::map<DWORD, int> missing;
                const long long guildCap = CollectPlayerBotGuildMaterialMissing(ch, missing);
                if (!missing.empty() && guildCap > 0 && FindPlayerBotGambleMaterialPick(ch, state, missing, guildCap, now)) {
                    sys_log(0, "PLAYERBOT_GUILD_LAND: master goes for materials pid=%u name=%s owner=%u item=%u lacking=%u",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            const long long budget = Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR);
            if (budget <= 0) return false;
            // MT2009_PLUS_DROPPER_INVEST_V1: a dropper's own next steps first -
            // the materials and scrolls of its weapon, armour and shield, up
            // to +9 - on every stand of the map, the gambler's way.
            if (dropperWindow) {
                std::map<DWORD, int> missing;
                CollectPlayerBotDropperInvestMissing(ch, missing);
                if (!missing.empty() && FindPlayerBotGambleMaterialPick(ch, state, missing, budget, now)) {
                    sys_log(0, "PLAYERBOT_MARKET: dropper invests in itself pid=%u name=%s owner=%u item=%u lacking=%u",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // What the piece under Iwakura's scroll rule lacks for its next
            // step - the weapon, or the armour once the weapon is at +8 - is
            // looked for on every stand of the map, the gambler's way, before
            // the browse of sixty-four lines: a first village holds some ten
            // thousand of them, and the rule's bots come in from the frontier
            // for a service visit of a minute or two.
            {
                std::map<DWORD, int> missing;
                CollectPlayerBotScrollRuleMissing(ch, missing);
                if (!missing.empty() && FindPlayerBotGambleMaterialPick(ch, state, missing, budget, now)) {
                    sys_log(0, "PLAYERBOT_MARKET: scroll-rule piece goes for materials pid=%u name=%s owner=%u item=%u lacking=%u",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // MT2009_PLUS_BOT_WORKSHOP_V1: a belt maker's materials and a talisman
            // worker's spare +0 and Ornament, on every stand of the map, the
            // gambler's way (playerbot_workshop.h).
            {
                std::map<DWORD, int> missing;
                const long long craftCap = CollectPlayerBotCraftMissing(ch, missing, budget);
                if (!missing.empty() && craftCap > 0 && FindPlayerBotGambleMaterialPick(ch, state, missing, craftCap, now)) {
                    sys_log(0, "PLAYERBOT_WORKSHOP: goes for craft materials pid=%u name=%s owner=%u item=%u lacking=%u",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // MT2009_PLUS_RANK_FRUIT_MARKET_V1: an eater's rank fruit, on every
            // stand of the map (playerbot_rank_fruit_market.h).
            {
                std::map<DWORD, int> missing;
                const long long fruitCap = std::min<long long>(budget, CollectPlayerBotRankFruitMissing(ch, missing));
                if (!missing.empty() && fruitCap > 0 && FindPlayerBotGambleMaterialPick(ch, state, missing, fruitCap, now)) {
                    sys_log(0, "PLAYERBOT_RANK: goes for rank fruit pid=%u name=%s owner=%u item=%u vnum=%u want=%d points=%d",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, missing.begin()->first,
                        missing.begin()->second, mt2009_rankp::KnownPoints(ch));
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // MT2009_PLUS_UPSTREAM_BOTLOGIC_SPIRIT_STONE_V1: the beans and the
            // Owoc Zycia for the rank its next Kamien Duchowy is short of, on
            // every stand of the map, out of a third of the budget.
            {
                std::map<DWORD, int> missing;
                if (CollectPlayerBotTrainingRankMissing(ch, missing, false) > 0 && budget / 3 > 0 &&
                        FindPlayerBotGambleMaterialPick(ch, state, missing, budget / 3, now)) {
                    sys_log(0, "PLAYERBOT_MARKET: goes for spirit stone rank pid=%u name=%s owner=%u item=%u kinds=%u rank=%d",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size(),
                        ch->GetRealAlignment());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // MT2009_PLUS_NEWPET_BOTS_V1: a keeper's egg, its pet's food, elixirs,
            // books and evolution materials, on every stand of the map
            // (playerbot_newpet_bots.h).
            {
                std::map<DWORD, int> missing;
                const long long petCap = CollectPlayerBotNewPetMissing(ch, missing);
                if (!missing.empty() && petCap > 0 && FindPlayerBotGambleMaterialPick(ch, state, missing, petCap, now)) {
                    sys_log(0, "PLAYERBOT_NEWPET: goes for pet goods pid=%u name=%s owner=%u item=%u lacking=%u first=%u gold=%lld",
                        ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size(),
                        missing.begin()->first, (long long)ch->GetGold());
                    return RunPlayerBotOfflinePick(ch, state, now);
                }
            }
            // And one of Community Patch 5's four gamblers buying its bases
            // looks on every stand of the map for one of its category.
            if (FindPlayerBotRareGamblerBasePick(ch, state, budget, now)) {
                sys_log(0, "PLAYERBOT_MARKET: gambler goes for a base pid=%u name=%s owner=%u item=%u category=%u bought=%u/%u",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem,
                    (unsigned int)state.persona.bGambleBuyCategory, (unsigned int)state.persona.bRareBought,
                    (unsigned int)state.persona.bRareBuyWant);
                return RunPlayerBotOfflinePick(ch, state, now);
            }
            // The books of its own skills at Master: every stand of the map,
            // not the browse's sixty-four lines a look. A bot on another
            // channel finds its line on the shop channel's stands and asks to
            // be moved there (RunPlayerBotOfflinePick).
            if (FindPlayerBotBookPick(ch, state, budget, now)) {
                sys_log(0, "PLAYERBOT_MARKET: goes for a skill book pid=%u name=%s owner=%u item=%u gold=%lld channel=%u",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (long long)ch->GetGold(),
                    (unsigned int)g_bChannel);
                return RunPlayerBotOfflinePick(ch, state, now);
            }
            // MT2009_PLUS_BOT_GEAR_UPGRADE_V1: a weapon that hits a tenth harder
            // than the best one it owns, at any plus, on every stand of the map.
            if (FindPlayerBotWeaponUpgradePick(ch, state, now))
                return RunPlayerBotOfflinePick(ch, state, now);
            // An outdated shield, helmet or body armour from level fifty: the
            // piece that replaces it, on every stand of the map.
            if (FindPlayerBotOutdatedGearPick(ch, state, budget, now)) {
                sys_log(0, "PLAYERBOT_MARKET: goes for a piece over outdated gear pid=%u name=%s owner=%u item=%u level=%d",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (int)ch->GetLevel());
                return RunPlayerBotOfflinePick(ch, state, now);
            }
            // MT2009_PLUS_BOT_GEAR_UPGRADE_V2: an armour a tenth better than
            // the best of its slot, at any plus, on every stand of the map -
            // after the weapon, whose price its purse leaves alone.
            if (FindPlayerBotArmourUpgradePick(ch, state, now))
                return RunPlayerBotOfflinePick(ch, state, now);
            // MT2009_PLUS_BOT_SHAMAN_INT_SET_V1: a Shaman looks on every stand
            // of the map for a piece that betters its INT set.
            if (FindPlayerBotBuffSetPick(ch, state, now)) {
                sys_log(0, "PLAYERBOT_BUFFSET: goes for a piece pid=%u name=%s owner=%u item=%u gold=%lld",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (long long)ch->GetGold());
                return RunPlayerBotOfflinePick(ch, state, now);
            }
            // And a bot in the market for a Stalki (playerbot_stalki.h) looks on
            // every stand of the map for one: the few lines of seven families
            // stand among some ten thousand, where the browse reads sixty-four.
            if (FindPlayerBotStalkiPick(ch, state, budget, now)) {
                sys_log(0, "PLAYERBOT_MARKET: stalki goes for a piece pid=%u name=%s owner=%u item=%u level=%d gold=%lld",
                    ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (int)ch->GetLevel(),
                    (long long)ch->GetGold());
                return RunPlayerBotOfflinePick(ch, state, now);
            }
            // MT2009_PLUS_HORSE_ECONOMY_V1 / MT2009_PLUS_SADDLEBAG_MARKET_V1 /
            // MT2009_PLUS_MARKET_SINK_V1: a horse medal, Materialy
            // Rzemieslnicze, a Cor Draconis or a sash, on every stand of the map.
            if (FindPlayerBotSinkGoodsPick(ch, state, now))
                return RunPlayerBotOfflinePick(ch, state, now);
            std::vector<std::pair<int, NativeShop> > shops;
            // Every stand is on the shop channel. With the assignment table a
            // bot elsewhere still reads the stands of its own map and asks to
            // be moved there when one holds something worth buying.
            const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                    ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
            for (const auto& [pid, shop] : manager.GetPlayerBotOfflineShops()) {
                if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
                const auto spawn = shop->GetSpawn();
                if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
                const int distance = DISTANCE_APPROX(spawn.x-ch->GetX(), spawn.y-ch->GetY());
                if (distance <= PLAYERBOT_MARKET_TRIP_RANGE) shops.emplace_back(distance, shop);
            }
            std::sort(shops.begin(), shops.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
            // Resume within the shop too: a full counter must not hide item 65.
            // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: of two lines for the same slot
            // at the same priority, the one of more useful lines while the
            // purse allows (TPlayerBotBuyBest), else the cheaper as before.
            TPlayerBotBuyBest best;
            const bool personFirst = number(1, 100) <= PLAYERBOT_MARKET_PERSON_FIRST_PERCENT;
            int partTries = 8;   // MT2009_PLUS_BOT_SHOP_MGMT_V1: part purchases looked at a browse
            auto rate = [&](auto shop, auto id, const auto& line) {
                if (IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now)) return;
                long long price = 0;
                int cell = -1, useful = 0, part = 0;
                const int priority = RatePlayerBotOfflineLine(ch, shop, line, budget, personFirst, price, &cell, &useful,
                        &part, &partTries);
                // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1: ranked by a person's price / 1.10.
                if (!best.Take(priority, PlayerBotOfferRankPrice(shop->GetOwnerPID(), price), cell, useful, budget)) return;
                o.buyOwner = shop->GetOwnerPID();
                o.buyItem = id;
                o.buyUntil = now + 45000;
                o.buyQuantity = (uint32_t)part;
            };
            if (personFirst)
                BrowsePlayerBotPersonLines(shops, rate);
            if (!o.buyOwner)
                BrowseLines(shops, o, 64, rate);
            if (o.buyOwner)
                best.Log(ch, "browse", o.buyOwner, o.buyItem);
            // A first village's stands with nothing on them this bot came for:
            // it asks on the trade channel, as a trip that found the market
            // empty always did. The classic trip was that trip's only caller,
            // and on this engine it no longer sets off (ManagePlayerBotShopping).
            // The shout is throttled world-wide and says nothing for a bag
            // that wants no material.
            if (!o.buyOwner && IsPlayerBotM1Map(ch->GetMapIndex()))
                AnnouncePlayerBotNeed(ch);
            // MT2009_PLUS_BOT_HAGGLE_V1: nothing to buy at once - a person's
            // finished piece too dear for the purse is haggled for by whisper.
            if (!o.buyOwner)
                TryStartPlayerBotHaggle(ch, state, shops, now);
        }
        if (!o.buyOwner) return false;
        return RunPlayerBotOfflinePick(ch, state, now);
    }
    // From a second village the buyer above cannot see its first village's
    // stands: they stand on another map. StartPlayerBotFarMarketWalk asks this
    // before the walk over - PLAYERBOT_MARKET_FAR_LOOK_LINES lines on a cursor
    // of their own, the next look going on where this one stopped - and the
    // line found is kept for the buyer, who takes it on arrival
    // (HandPlayerBotFarPickToBuyer). The walk used to be made for whatever
    // the bot might want, and nine times in ten it bought nothing.
    bool FindPlayerBotFarOfflinePick(LPCHARACTER ch, TPlayerBotAIState& state, long mapIndex) {
        using namespace playerbot_offline;
        auto& o = state.offlineShop;
        o.farPickOwner = o.farPickItem = 0;
        o.farPickSink = false;
        const long long budget = Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR);
        if (budget <= 0) return false;
        // MT2009_PLUS_HORSE_ECONOMY_V2: the first village's sink goods first.
        // Every one of the supporters' world's 1218 medal lines stood in a
        // first village, and the bots short of a medal were on the frontier
        // or in a second village, where the in-reach pick could not see them.
        {
            DWORD sinkOwner = 0, sinkItem = 0, sinkVnum = 0;
            long long sinkUnit = 0;
            if (ScanPlayerBotSinkGoods(ch, mapIndex, get_dword_time(), sinkOwner, sinkItem, sinkVnum, sinkUnit)) {
                o.farPickOwner = sinkOwner;
                o.farPickItem = sinkItem;
                o.farPickSink = true;
                sys_log(0, "PLAYERBOT_MARKET: far sink pick pid=%u name=%s map=%ld owner=%u item=%u vnum=%u unit=%lld lv=%d horse=%u",
                    ch->GetPlayerID(), ch->GetName(), mapIndex, sinkOwner, sinkItem, sinkVnum, sinkUnit,
                    (int)ch->GetLevel(), (unsigned int)ch->GetHorseLevel());
                return true;
            }
        }
        // In the order of their distance from the market's middle, which does
        // not move, so the cursor means the same thing at the next look.
        long centreX = 0, centreY = 0;
        GetPlayerBotShopCentre(mapIndex, centreX, centreY);
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        std::vector<std::pair<int, NativeShop> > shops;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != mapIndex || (int)spawn.channel != shopChannel) continue;
            shops.emplace_back(DISTANCE_APPROX(spawn.x - centreX, spawn.y - centreY), shop);
        }
        if (shops.empty()) return false;
        std::sort(shops.begin(), shops.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
        // A first look starts at a stand drawn by pid. From the middle, every
        // bot of a village read the same sixty-four lines and set off for the
        // same one - three walks in the first minute on the test world for
        // owner 1863's line, which one of them could buy.
        if (!o.farBrowseOwner) {
            o.farBrowseOwner = shops[ch->GetPlayerID() % shops.size()].second->GetOwnerPID();
            o.farBrowseItem = 0;
        }
        // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: the browse's own tie-break.
        TPlayerBotBuyBest best;
        const bool personFirst = number(1, 100) <= PLAYERBOT_MARKET_PERSON_FIRST_PERCENT;
        const DWORD now = get_dword_time();
        auto rate = [&](auto shop, auto id, const auto& line) {
            if (IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now)) return;
            long long price = 0;
            int cell = -1, useful = 0;
            const int priority = RatePlayerBotOfflineLine(ch, shop, line, budget, personFirst, price, &cell, &useful);
            if (!best.Take(priority, price, cell, useful, budget)) return;
            o.farPickOwner = shop->GetOwnerPID();
            o.farPickItem = id;
        };
        if (personFirst)
            BrowsePlayerBotPersonLines(shops, rate);
        if (!o.farPickOwner) {
            std::swap(o.browseOwner, o.farBrowseOwner);
            std::swap(o.browseItem, o.farBrowseItem);
            BrowseLines(shops, o, PLAYERBOT_MARKET_FAR_LOOK_LINES, rate);
            std::swap(o.browseOwner, o.farBrowseOwner);
            std::swap(o.browseItem, o.farBrowseItem);
        }
        if (o.farPickOwner)
            best.Log(ch, "far", o.farPickOwner, o.farPickItem);
        return o.farPickOwner != 0;
    }

    // Across: the line the walk was made for is the buyer's pick now, with
    // the time to ride from the gate to the stand, and the stands in reach
    // are read at once should it have sold meanwhile. Called on the tick of
    // arrival, and it claims that tick while the bot walks to the stand, or
    // the travel pass further down the tick would take it straight back.
    bool HandPlayerBotFarPickToBuyer(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        auto& o = state.offlineShop;
        if (o.farPickOwner) {
            o.buyOwner = o.farPickOwner;
            o.buyItem = o.farPickItem;
            o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
            o.farBuy = true;
        }
        o.farPickOwner = o.farPickItem = 0;
        o.nextBrowse = 0;
        return ManagePlayerBotOfflineShopping(ch, state, now);
    }

    // Declared in playerbot_economy.h: whether a stand of this bot's map holds
    // a finished piece for the slot that the buyer would take - the purchase's
    // own tests (WantsPlayerBotStallItem, the Perfectionist's purse) asked of
    // the line - and, when one does, the line handed to the buyer and claimed
    // for the wait. The anvil asks it once in PLAYERBOT_READY_GEAR_RECHECK_MS
    // a slot, so a read over every line of the map costs nothing to speak of;
    // only a line of the right kind, grade and class is built into an item.
    bool PlayerBotFindReadyGearToBuy(LPCHARACTER ch, TPlayerBotAIState& state, int wearCell) {
        using namespace playerbot_offline;
        if (!ch || !IsPlayerBotReadyGearSlot(wearCell)) return false;
        const long long budget = Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR);
        if (budget <= 0) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        const DWORD now = get_dword_time();
        TPlayerBotBuyBest best;
        DWORD bestOwner = 0, bestItem = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line) continue;
                const DWORD vnum = line->GetInfo().vnum;
                const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
                if (!IsPlayerBotReadyGearProto(ch, proto, vnum, wearCell) ||
                        !IsPlayerBotReadyGearOverWorn(ch, proto, vnum, wearCell) ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > budget) continue;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const bool buyable = preview->FindEquipCell(ch) == wearCell &&
                        IsPlayerBotReadyGearOffer(ch, preview) && WantsPlayerBotStallItem(ch, preview) &&
                        CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID());
                const int useful = buyable ? CountPlayerBotUsefulBuyLines(ch, preview) : 0;
                M2_DELETE(preview);
                if (!buyable) continue;
                // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: every finished piece for
                // the slot is weighed now, not the first one found - the one
                // of more useful lines while the purse allows, else the cheaper.
                if (best.Take(0, price, wearCell, useful, budget)) {
                    bestOwner = shop->GetOwnerPID();
                    bestItem = id;
                }
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.readyPickOwner = bestOwner;
        o.readyPickItem = bestItem;
        o.readyPickUntil = now + PLAYERBOT_READY_GEAR_WAIT_MS;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, now + PLAYERBOT_READY_GEAR_WAIT_MS);
        best.Log(ch, "ready_gear", bestOwner, bestItem);
        return true;
    }

    // MT2009_PLUS_BOSS_RAID_V2 (2.2.52, burn): the replacement for a weapon,
    // body armour or shield that has just burnt at the anvil, read on every
    // stand of the bot's map at once - the best by the equipment score of the
    // lines the bot can wear now, of the burnt piece's level or over, that
    // the buyer would take and could pay for - and handed to the buyer as the
    // anvil's finished piece is. False when the map has none: the merchant's
    // piece is then bought at once instead of after the market's wait (a bot
    // used to walk the merchants empty-handed for three minutes,
    // KrwawyKarp46 on 1 October).
    bool PlayerBotFindBurnReplacementToBuy(LPCHARACTER ch, TPlayerBotAIState& state, int wearCell, int minLevel) {
        using namespace playerbot_offline;
        if (!ch) return false;
        const long long budget = Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR);
        if (budget <= 0) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        const DWORD now = get_dword_time();
        DWORD bestOwner = 0, bestItem = 0;
        long long bestScore = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line) continue;
                const TItemTable* proto = ITEM_MANAGER::instance().GetTable(line->GetInfo().vnum);
                if (!proto || (proto->bType != ITEM_WEAPON && proto->bType != ITEM_ARMOR)) continue;
                const int level = GetPlayerBotProtoLevelLimit(proto);
                if (level < minLevel || level > (int)ch->GetLevel() ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > budget) continue;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                long long score = 0;
                const bool buyable = preview->FindEquipCell(ch) == wearCell &&
                        IsPlayerBotEquipmentCandidate(ch, preview) && WantsPlayerBotStallItem(ch, preview) &&
                        CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) &&
                        (score = GetPlayerBotEquipmentScore(preview, ch)) > bestScore;
                M2_DELETE(preview);
                if (!buyable) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestScore = score;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.readyPickOwner = bestOwner;
        o.readyPickItem = bestItem;
        o.readyPickUntil = now + PLAYERBOT_REBUILD_MARKET_MS;
        o.nextBrowse = 0;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, now + PLAYERBOT_REBUILD_MARKET_MS);
        return true;
    }

    // The cheapest line a unit of a material the gambler lacks
    // (CollectPlayerBotGambleMissingMaterials), on a stand of its map it can
    // walk to, that the buyer would take on arrival - the purchase's own tests
    // asked of the line - for no more than `cap`. Handed to the buyer and
    // claimed for the walk, as the Perfectionist's finished piece is.
    bool FindPlayerBotGambleMaterialPick(LPCHARACTER ch, TPlayerBotAIState& state,
            const std::map<DWORD, int>& missing, long long cap, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || missing.empty() || cap <= 0) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0, bestPart = 0;
        long long bestUnit = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            // Asked once a stand has a line worth walking to: Joan's wall
            // keeps some of its stands from the storekeeper's side.
            int reach = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line || missing.find(line->GetInfo().vnum) == missing.end() ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                long long price = (long long)line->GetPrice().GetTotalYangAmount();
                // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1: a person's unit ranked / 1.10.
                const long long unit = PlayerBotOfferRankPrice(shop->GetOwnerPID(),
                        price / std::max<long long>(1, (long long)line->GetInfo().count));
                // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): of a stack bigger than
                // what is missing, the missing part.
                DWORD part = 0;
                {
                    const int need = missing.find(line->GetInfo().vnum)->second;
                    const long long partYang = IsPlayerBotPartBuyOn() && need > 0
                            ? PlayerBotPartPrice(price, (long long)line->GetInfo().count, need) : 0;
                    if (partYang > 0) {
                        part = (DWORD)need;
                        price = partYang;
                    }
                }
                if (price <= 0 || price > cap || (bestOwner && unit >= bestUnit)) continue;
                if (reach < 0)
                    reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
                if (reach == 0) break;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                if (part) preview->SetCount(part);
                const bool buyable = WantsPlayerBotStallItem(ch, preview) &&
                        CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
                M2_DELETE(preview);
                if (!buyable) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestUnit = unit;
                bestPart = part;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyQuantity = bestPart;   // MT2009_PLUS_BOT_SHOP_MGMT_V1
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        return true;
    }

    // One of Community Patch 5's four gamblers buying its bases
    // (IsPlayerBotRareGamblerBuying): the cheapest line of its category on a
    // stand of its map it can walk to, the higher level first for the share
    // that wants weapons over thirty, that the buyer would take on arrival -
    // the purchase's own tests - for no more than `cap`. The browse reads
    // sixty-four lines a look, and a first village holds some ten thousand:
    // a gambler with three hours would have spent most of them looking.
    bool FindPlayerBotRareGamblerBasePick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || cap <= 0 || !IsPlayerBotRareGamblerBuying(state.persona, now)) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0;
        long long bestPrice = 0;
        int bestLevel = -1;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            int reach = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line || line->GetInfo().count != 1 || IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const TItemTable* proto = line->GetTable();
                if (!proto || (proto->bType != ITEM_WEAPON && proto->bType != ITEM_ARMOR)) continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const int level = (int)GetPlayerBotPersonaLevelLimit(preview);
                const bool better = !bestOwner || (state.persona.bGambleWeaponHigh && level != bestLevel
                        ? level > bestLevel : price < bestPrice);
                bool buyable = false;
                if (better && IsPlayerBotRareGamblerBaseOffer(ch, preview)) {
                    if (reach < 0)
                        reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
                    buyable = reach == 1 && WantsPlayerBotStallItem(ch, preview) &&
                            CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
                }
                M2_DELETE(preview);
                if (reach == 0) break;
                if (!buyable) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestPrice = price;
                bestLevel = level;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        return true;
    }

    // A bot in the market for a Stalki (IsPlayerBotStalkiShopper): the best
    // line of its own on a stand of its map it can walk to - the equipment
    // pass's score, the cheaper on a tie - that the buyer would take on
    // arrival, the purchase's own tests asked of the line, for no more than
    // `cap`. Only a line whose vnum is one of the families is built into an
    // item, so a look over the whole map costs a vnum test a line.
    bool FindPlayerBotStalkiPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || cap <= 0 ||
                (!IsPlayerBotStalkiShopper(ch, playerbot_stalki_rules::KIND_ARMOUR) &&
                 !IsPlayerBotStalkiShopper(ch, playerbot_stalki_rules::KIND_WEAPON)))
            return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0;
        long long bestPrice = 0, bestScore = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            int reach = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line || line->GetInfo().count != 1 || !playerbot_stalki_rules::IsStalki(line->GetInfo().vnum) ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const long long score = GetPlayerBotEquipmentScore(preview, ch);
                const bool better = !bestOwner || score > bestScore || (score == bestScore && price < bestPrice);
                bool buyable = false;
                if (better && IsPlayerBotStalkiProjectOffer(ch, preview)) {
                    if (reach < 0)
                        reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
                    buyable = reach == 1 && WantsPlayerBotStallItem(ch, preview) &&
                            CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
                }
                M2_DELETE(preview);
                if (reach == 0) break;
                if (!buyable) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestPrice = price;
                bestScore = score;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        return true;
    }

    // The books of its own skills at Master (PlayerBotWantsOwnBooks): the
    // cheapest book a unit on a stand of its map the buyer would take on
    // arrival, the purchase's own tests asked of the line, for no more than
    // `cap`. Only a line whose proto is a skill book is built into an item.
    bool FindPlayerBotBookPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || cap <= 0 || !PlayerBotWantsOwnBooks(ch)) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0;
        long long bestUnit = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            int reach = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line || !line->GetTable() || line->GetTable()->bType != ITEM_SKILLBOOK ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const auto& info = line->GetInfo();
                const DWORD skill = info.vnum == 50300 ? (DWORD)info.alSockets[0] : (DWORD)line->GetTable()->alValues[0];
                if (!IsPlayerBotOwnSkill(ch, skill) || ch->GetSkillMasterType(skill) != SKILL_MASTER) continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                const long long unit = price / std::max<long long>(1, (long long)info.count);
                if (bestOwner && unit >= bestUnit) continue;
                if (reach < 0)
                    reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
                if (reach == 0) break;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const bool buyable = IsPlayerBotProgressionOffer(ch, preview) && WantsPlayerBotStallItem(ch, preview) &&
                        CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
                M2_DELETE(preview);
                if (!buyable) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestUnit = unit;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        return true;
    }

    // The piece that replaces an outdated shield, helmet or body armour
    // (IsPlayerBotOutdatedGearOffer): a finished one at +6 or more first, then
    // the highest level, then the cheapest - on a stand of the map the bot
    // can walk to, for no more than `cap`.
    bool FindPlayerBotOutdatedGearPick(LPCHARACTER ch, TPlayerBotAIState& state, long long cap, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || cap <= 0) return false;
        // MT2009_PLUS_BOT_LAW_GEAR_V1: under level 50 only a piece under the
        // Law of Advancement's level window (IsPlayerBotLawStaleGear).
        const bool fifty = (int)ch->GetLevel() >= PLAYERBOT_OUTDATED_GEAR_MIN_LEVEL;
        bool outdated[3] = {
            IsPlayerBotOutdatedGear(ch, ch->GetWear(WEAR_BODY)) && (fifty || IsPlayerBotLawStaleGear(ch, ch->GetWear(WEAR_BODY))),
            IsPlayerBotOutdatedGear(ch, ch->GetWear(WEAR_HEAD)) && (fifty || IsPlayerBotLawStaleGear(ch, ch->GetWear(WEAR_HEAD))),
            fifty && IsPlayerBotOutdatedGear(ch, ch->GetWear(WEAR_SHIELD)) };
        if (!outdated[0] && !outdated[1] && !outdated[2]) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0;
        long long bestRank = -1, bestPrice = 0;
        TPlayerBotBuyBest best;   // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1, within one rank
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            int reach = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                const TItemTable* table = line ? line->GetTable() : NULL;
                if (!table || table->bType != ITEM_ARMOR || line->GetInfo().count != 1 ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now) ||
                        IsPlayerBotPlainGearLineForPeople(pid, id, table, line->GetInfo().aAttr, now))   // MT2009_PLUS_PLAIN_GEAR_WINDOW_V1
                    continue;
                const int slot = table->bSubType == ARMOR_BODY ? 0 : table->bSubType == ARMOR_HEAD ? 1 :
                        table->bSubType == ARMOR_SHIELD ? 2 : -1;
                if (slot < 0 || !outdated[slot]) continue;
                const int level = GetPlayerBotProtoLevelLimit(table);
                if (level > (int)ch->GetLevel() || level + PLAYERBOT_OUTDATED_GEAR_LEVELS <= (int)ch->GetLevel()) continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                const int plus = (int)(line->GetInfo().vnum % 10);
                const long long rank = (plus >= 6 ? 1000000LL : 0LL) + (long long)level * 100 + plus;
                // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: a dearer line of the same
                // rank is looked at too - its useful lines may win it.
                if (rank < bestRank) continue;
                if (reach < 0)
                    reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
                if (reach == 0) break;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const bool buyable = IsPlayerBotOutdatedGearOffer(ch, preview) && WantsPlayerBotStallItem(ch, preview) &&
                        CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
                const int useful = buyable ? CountPlayerBotUsefulBuyLines(ch, preview) : 0;
                M2_DELETE(preview);
                if (!buyable) continue;
                // The rank first (the old order), then the slot's useful lines
                // within the purse, then the price.
                if (!best.Take(rank > bestRank ? 1 : 0, price, slot, useful, cap) && rank == bestRank) continue;
                if (rank > bestRank) {
                    best = TPlayerBotBuyBest();
                    best.Take(0, price, slot, useful, cap);
                }
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestRank = rank;
                bestPrice = price;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        best.Log(ch, "outdated_gear", bestOwner, bestItem);
        return true;
    }

    // MT2009_PLUS_BOT_GEAR_UPGRADE_V1: the weapon on a stand of the bot's map
    // that hits hardest for it of those it would buy and could pay for
    // (IsPlayerBotWeaponUpgradeOffer, CanPlayerBotPayForOffer) - asked only
    // while its look at the first village found one (LookPlayerBotWeaponUpgrade),
    // so a bot with nothing to buy reads no stand. Every line is rated by its
    // proto's blow at its plus, the best PLAYERBOT_WEAPON_UPGRADE_PREVIEW_LINES
    // of them are built into an item and asked the purchase's own tests, and
    // the hardest exact blow is the pick, the cheaper line breaking a tie.
    bool FindPlayerBotWeaponUpgradePick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || !PlayerBotWantsWeaponUpgradeFromMarket(ch)) return false;
        const long long cap = GetPlayerBotWeaponUpgradeBudget(ch, PLAYERBOT_WEAPON_UPGRADE_BIG_GAIN_PERCENT);
        if (cap <= 0) return false;
        const TPlayerBotOwnedWeapon owned = ReadPlayerBotBestOwnedWeapon(ch);
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1: rank, a person's price / 1.10.
        struct TCandidate { long long blow; long long price; long long rank; DWORD owner; DWORD item; long x; long y; };
        std::vector<TCandidate> candidates;
        std::map<DWORD, long long> blowByVnum;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            for (const auto& [id, line] : shop->GetItems()) {
                const TItemTable* table = line ? line->GetTable() : NULL;
                if (!table || table->bType != ITEM_WEAPON || line->GetInfo().count != 1 ||
                        IsPlayerBotPlainGearLineForPeople(pid, id, table, line->GetInfo().aAttr, now)) continue;   // MT2009_PLUS_PLAIN_GEAR_WINDOW_V1
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                long long blow = 0;
                const auto known = blowByVnum.find(table->dwVnum);
                if (known != blowByVnum.end())
                    blow = known->second;
                else {
                    if (IsPlayerBotWeaponProtoFor(ch, table) &&
                            (owned.subType < 0 || (int)table->bSubType == owned.subType))
                        blow = GetPlayerBotWeaponHitDamageAt(NULL, table, ch);
                    blowByVnum[table->dwVnum] = blow;
                }
                if (blow <= 0 ||
                        (owned.item && blow * 100 < owned.blow * (100 + PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT)) ||
                        price > GetPlayerBotWeaponUpgradeBudget(ch, GetPlayerBotWeaponGainPercent(blow, owned.item ? owned.blow : 0)) ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                candidates.push_back(TCandidate{ blow, price, PlayerBotOfferRankPrice(shop->GetOwnerPID(), price),
                    shop->GetOwnerPID(), id, (long)spawn.x, (long)spawn.y });
            }
        }
        if (candidates.empty()) return false;
        std::sort(candidates.begin(), candidates.end(), [](const TCandidate& a, const TCandidate& b) {
            return a.blow != b.blow ? a.blow > b.blow : a.rank < b.rank;
        });
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0;
        long long bestBlow = 0, bestPrice = 0, bestGain = 0;
        int previewed = 0;
        TPlayerBotBuyBest best;   // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1, within one blow
        for (const TCandidate& c : candidates) {
            if (previewed >= PLAYERBOT_WEAPON_UPGRADE_PREVIEW_LINES) break;
            if (haveNav && !navigation.CanReach(ch->GetX(), ch->GetY(), c.x, c.y)) continue;
            auto shop = ikashop::GetManager().GetShopByOwnerID(c.owner);
            auto line = shop ? shop->GetItem(c.item) : nullptr;
            LPITEM preview = line ? BotOfflinePreview(*line) : NULL;
            if (!preview) continue;
            ++previewed;
            long long gain = 0;
            const bool buyable = IsPlayerBotWeaponUpgradeOffer(ch, preview, &gain) &&
                    WantsPlayerBotStallItem(ch, preview) &&
                    CanPlayerBotPayForOffer(ch, preview, c.price, c.owner) &&
                    ch->GetEmptyInventory(preview->GetSize()) >= 0;
            const long long blow = buyable ? GetPlayerBotWeaponHitDamage(preview, ch) : 0;
            const int useful = buyable ? CountPlayerBotUsefulBuyLines(ch, preview) : 0;
            M2_DELETE(preview);
            if (!buyable || blow <= 0 || blow < bestBlow) continue;
            // MT2009_PLUS_BOT_BUY_BONUS_PREF_V1: at an equal blow, the weapon
            // of more useful lines within the upgrade's purse, else the cheaper.
            if (blow == bestBlow && !best.Take(0, c.rank, WEAR_WEAPON, useful, cap)) continue;
            if (blow > bestBlow) {
                best = TPlayerBotBuyBest();
                best.Take(0, c.rank, WEAR_WEAPON, useful, cap);
            }
            bestOwner = c.owner;
            bestItem = c.item;
            bestBlow = blow;
            bestPrice = c.price;
            bestGain = gain;
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        ++s_dwPlayerBotWeaponUpgradePicks;
        best.Log(ch, "weapon_upgrade", bestOwner, bestItem);
        sys_log(0, "PLAYERBOT_GEAR_UPGRADE: goes for a weapon pid=%u name=%s level=%u owned=%u blow=%lld line=%u owner=%u blow=%lld gain=%lld%% price=%lld gold=%lld",
            ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), owned.item ? owned.item->GetVnum() : 0,
            owned.blow, bestItem, bestOwner, bestBlow, bestGain, bestPrice, (long long)ch->GetGold());
        return true;
    }

    // MT2009_PLUS_BOT_GEAR_UPGRADE_V2: the armour on a stand of the bot's map
    // that buys it the most score a yang of those it would buy and could pay
    // for (IsPlayerBotArmourUpgradeOffer, CanPlayerBotPayForOffer) - asked
    // only while its look at the first village found one
    // (LookPlayerBotArmourUpgrade), so a bot with nothing to buy reads no
    // stand. Every line is rated by a clean copy's score
    // (GetPlayerBotArmourProtoScore) against the best piece of its slot, the
    // best PLAYERBOT_ARMOUR_UPGRADE_PREVIEW_LINES of them are built into an
    // item and asked the purchase's own tests, and the most exact score a
    // yang is the pick, body armour first on a tie.
    bool FindPlayerBotArmourUpgradePick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || !PlayerBotWantsArmourUpgradeFromMarket(ch)) return false;
        const long long spare = GetPlayerBotArmourUpgradeSpare(ch);
        const long long cap = GetPlayerBotArmourUpgradeShare(spare, PLAYERBOT_ARMOUR_UPGRADE_BIG_GAIN_PERCENT);
        if (cap <= 0) return false;
        TPlayerBotOwnedArmour owned;
        ReadPlayerBotBestOwnedArmour(ch, owned);
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        struct TCandidate { long long value; int slot; long long price; DWORD owner; DWORD item; long x; long y; };
        std::vector<TCandidate> candidates;
        std::map<DWORD, long long> scoreByVnum;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            for (const auto& [id, line] : shop->GetItems()) {
                const TItemTable* table = line ? line->GetTable() : NULL;
                if (!table || table->bType != ITEM_ARMOR || line->GetInfo().count != 1 ||
                        IsPlayerBotPlainGearLineForPeople(pid, id, table, line->GetInfo().aAttr, now)) continue;   // MT2009_PLUS_PLAIN_GEAR_WINDOW_V1
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0 || price > cap) continue;
                long long score = 0;
                const auto known = scoreByVnum.find(table->dwVnum);
                if (known != scoreByVnum.end())
                    score = known->second;
                else {
                    if (IsPlayerBotArmourProtoFor(ch, table))
                        score = GetPlayerBotArmourProtoScore(ch, table);
                    scoreByVnum[table->dwVnum] = score;
                }
                if (score <= 0) continue;
                const int slot = GetPlayerBotArmourUpgradeSlot(table->bSubType);
                const long long ownedScore = owned.item[slot] ? owned.score[slot] : 0;
                if ((owned.item[slot] && score * 100 < ownedScore * (100 + PLAYERBOT_ARMOUR_UPGRADE_MIN_GAIN_PERCENT)) ||
                        price > GetPlayerBotArmourUpgradeShare(spare, GetPlayerBotArmourGainPercent(score, ownedScore)) ||
                        IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1: the value a yang of a person's price / 1.10.
                candidates.push_back(TCandidate{ GetPlayerBotArmourValuePerYang(score, ownedScore,
                    PlayerBotOfferRankPrice(shop->GetOwnerPID(), price)), slot, price,
                    shop->GetOwnerPID(), id, (long)spawn.x, (long)spawn.y });
            }
        }
        if (candidates.empty()) return false;
        std::sort(candidates.begin(), candidates.end(), [](const TCandidate& a, const TCandidate& b) {
            return a.value != b.value ? a.value > b.value : a.slot != b.slot ? a.slot < b.slot : a.price < b.price;
        });
        CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
        const bool haveNav = navigation.Init(ch->GetMapIndex());
        DWORD bestOwner = 0, bestItem = 0, bestVnum = 0;
        long long bestValue = -1, bestPrice = 0, bestGain = 0, bestScore = 0;
        int bestSlot = -1, previewed = 0;
        for (const TCandidate& c : candidates) {
            if (previewed >= PLAYERBOT_ARMOUR_UPGRADE_PREVIEW_LINES) break;
            if (haveNav && !navigation.CanReach(ch->GetX(), ch->GetY(), c.x, c.y)) continue;
            auto shop = ikashop::GetManager().GetShopByOwnerID(c.owner);
            auto line = shop ? shop->GetItem(c.item) : nullptr;
            LPITEM preview = line ? BotOfflinePreview(*line) : NULL;
            if (!preview) continue;
            ++previewed;
            long long gain = 0;
            const bool buyable = IsPlayerBotArmourUpgradeOffer(ch, preview, &gain) &&
                    WantsPlayerBotStallItem(ch, preview) &&
                    CanPlayerBotPayForOffer(ch, preview, c.price, c.owner) &&
                    ch->GetEmptyInventory(preview->GetSize()) >= 0;
            const long long score = buyable ? GetPlayerBotEquipmentScore(preview, ch) : 0;
            const DWORD vnum = preview->GetVnum();
            M2_DELETE(preview);
            if (!buyable) continue;
            const long long value = GetPlayerBotArmourValuePerYang(score,
                    owned.item[c.slot] ? owned.score[c.slot] : 0, PlayerBotOfferRankPrice(c.owner, c.price));
            if (value < bestValue || (value == bestValue && (c.slot > bestSlot ||
                    (c.slot == bestSlot && c.price >= bestPrice)))) continue;
            bestOwner = c.owner;
            bestItem = c.item;
            bestVnum = vnum;
            bestValue = value;
            bestPrice = c.price;
            bestGain = gain;
            bestScore = score;
            bestSlot = c.slot;
        }
        if (!bestOwner || bestSlot < 0) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        ++s_dwPlayerBotArmourUpgradePicks;
        LPITEM ownedItem = owned.item[bestSlot];
        sys_log(0, "PLAYERBOT_GEAR_UPGRADE: goes for armour pid=%u name=%s level=%u slot=%s owned=%u score=%lld vnum=%u line=%u owner=%u score=%lld gain=%lld%% price=%lld gold=%lld",
            ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), PLAYERBOT_ARMOUR_UPGRADE_SLOT_NAMES[bestSlot],
            ownedItem ? ownedItem->GetVnum() : 0, owned.score[bestSlot], bestVnum, bestItem, bestOwner, bestScore,
            bestGain, bestPrice, (long long)ch->GetGold());
        return true;
    }

    // MT2009_PLUS_BOT_SHAMAN_INT_SET_V1: the stand line that betters a
    // Shaman's INT set most for its price, on every stand of the bot's map -
    // looked for once in PLAYERBOT_BUFF_SET_MARKET_LOOK_MS a bot, and only a
    // line of the set's kinds is built into an item.
    const DWORD PLAYERBOT_BUFF_SET_MARKET_LOOK_MS = 15 * 60 * 1000;
    std::map<DWORD, DWORD> s_mapPlayerBotBuffSetNextLook;

    // MT2009_PLUS_HORSE_ECONOMY_V1 (with MT2009_PLUS_SADDLEBAG_MARKET_V1 and
    // MT2009_PLUS_MARKET_SINK_V1): the goods the world's counters were full of
    // while the bots that wanted them never bought them - on the supporters'
    // world 1216 horse medals, 14 205 Materialy Rzemieslnicze, 50 pages of
    // Cors and pages of sashes. The browse reads sixty-four lines a look of
    // some ten thousand on a first village's stands, so a bot short of a
    // medal for its horse, of materials for its saddlebag rows, of Cors or of
    // a sash met one by chance or never. Like the Stalki's and the books'
    // picks, this reads every stand of the map for those vnums alone - only
    // while the bot wants one of the four (asked without a counter) and
    // PLAYERBOT_SINK_LOOK_MS apart - and takes the cheapest piece among the
    // lines the purchase's own rules would buy (WantsPlayerBotStallItem,
    // CanPlayerBotPayForOffer).
    const DWORD PLAYERBOT_SINK_LOOK_MS = 2 * 60 * 1000;
    std::map<DWORD, DWORD> s_mapPlayerBotSinkNextLook;

    bool IsPlayerBotSinkGoodsVnum(DWORD vnum) {
        return vnum == PLAYERBOT_HORSE_MEDAL_VNUM || vnum == PLAYERBOT_CRAFT_MATERIAL_VNUM_PRICED ||
                IsPlayerBotCorVnum(vnum) || IsPlayerBotSashVnum(vnum);
    }

    // MT2009_PLUS_HORSE_ECONOMY_V2: the scan alone, for any map's stands (the
    // in-reach pick below and the far pick of a walk to the first village,
    // FindPlayerBotFarOfflinePick), on one throttle a bot.
    bool ScanPlayerBotSinkGoods(LPCHARACTER ch, long mapIndex, DWORD now, DWORD& bestOwner, DWORD& bestItem,
            DWORD& bestVnum, long long& bestUnit, DWORD* partOut) {
        using namespace playerbot_offline;
        if (partOut) *partOut = 0;
        bestOwner = bestItem = bestVnum = 0;
        bestUnit = 0;
        if (!ch || IsPlayerBotSidekickPID(ch->GetPlayerID()))
            return false;
        DWORD& next = s_mapPlayerBotSinkNextLook[ch->GetPlayerID()];
        if (next != 0 && !Due(now, next)) return false;
        next = now + PLAYERBOT_SINK_LOOK_MS;
        // MT2009_PLUS_HORSE30_V1: the next paid training's medals.
        const bool medal = PlayerBotHorseWantsMedal(ch) || PlayerBotSaddlebagWantsMedal(ch);
        const bool wants = medal || PlayerBotWantsSaddlebagGoods(ch) || PlayerBotWantsAlchemyFromMarket(ch) ||
                PlayerBotWantsSashFromMarket(ch);
        if (!wants) return false;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        // MT2009_PLUS_BOT_MARKET_SCAN_ORDER_V1: the scan walked the stands in
        // pid order and stopped after 400 previews, and only a line cheaper
        // than the best so far was previewed - so the bots' own stands, low
        // pids holding hundreds of medals, sashes and Cors, used the whole
        // allowance and a person's stand (pid 9005, the last of 1435 on map
        // 41) was never reached: no medal of his sold while the market sold
        // some 800 a day. Now a first pass reads only the vnum and the price
        // of every line of the map (no item built), the candidates are
        // ordered cheapest unit first - a person's line before a bot's at the
        // same unit, ties spread by bot so they do not all queue for one
        // line - and the previews go down that list: the first line the
        // purchase's rules accept is the cheapest buyable one, wherever its
        // stand sits in pid order.
        struct TSinkCandidate {
            long long unit, rank, price;
            int personRank;
            DWORD spread, owner, item, vnum;
            NativeShop shop;
        };
        std::vector<TSinkCandidate> candidates;
        auto& botManager = CPlayerBotManager::instance();
        const DWORD self = ch->GetPlayerID();
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == self || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != mapIndex || (int)spawn.channel != shopChannel) continue;
            int personRank = -1;
            for (const auto& [id, line] : shop->GetItems()) {
                if (!line) continue;
                const DWORD vnum = line->GetInfo().vnum;
                if (!IsPlayerBotSinkGoodsVnum(vnum) || (vnum == PLAYERBOT_HORSE_MEDAL_VNUM && !medal) ||
                        IsPlayerBotLineClaimedByOther(id, self, now))
                    continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0) continue;
                if (personRank < 0)
                    personRank = botManager.IsRegisteredBotPID(shop->GetOwnerPID()) ? 1 : 0;
                const long long unit = price / std::max<long long>(1, (long long)line->GetInfo().count);
                // MT2009_PLUS_BOT_MARKET_PLAYER_PREF_V1: sorted by a person's unit / 1.10.
                candidates.push_back({ unit, PlayerBotOfferRankPrice(shop->GetOwnerPID(), unit), price, personRank, (DWORD)((id ^ (self * 2654435761u)) * 2246822519u),
                    shop->GetOwnerPID(), id, vnum, shop });
            }
        }
        std::sort(candidates.begin(), candidates.end(), [](const TSinkCandidate& a, const TSinkCandidate& b) {
            if (a.rank != b.rank) return a.rank < b.rank;
            if (a.personRank != b.personRank) return a.personRank < b.personRank;
            return a.spread < b.spread;
        });
        unsigned int looked = 0;
        for (const auto& c : candidates) {
            if (++looked > 400) break;
            const auto& items = c.shop->GetItems();
            const auto it = items.find(c.item);
            if (it == items.end() || !it->second) continue;
            LPITEM preview = BotOfflinePreview(*it->second);
            if (!preview) continue;
            bool buyable = WantsPlayerBotStallItem(ch, preview) &&
                    CanPlayerBotPayForOffer(ch, preview, c.price, c.owner) &&
                    ch->GetEmptyInventory(preview->GetSize()) >= 0;
            // MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 5): or the part of the stack
            // the bot needs and can pay for - a medal or a few of a stack.
            DWORD part = 0;
            if (!buyable && partOut) {
                long long partYang = 0;
                part = (DWORD)PlayerBotPartBuyCount(ch, preview, c.price, c.owner, 0, partYang);
                buyable = part > 0;
            }
            M2_DELETE(preview);
            if (!buyable) continue;
            if (partOut) *partOut = part;
            bestOwner = c.owner;
            bestItem = c.item;
            bestVnum = c.vnum;
            bestUnit = c.unit;
            break;
        }
        return bestOwner != 0;
    }

    bool FindPlayerBotSinkGoodsPick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        DWORD bestOwner = 0, bestItem = 0, bestVnum = 0, bestPart = 0;
        long long bestUnit = 0;
        if (!ch || !ScanPlayerBotSinkGoods(ch, ch->GetMapIndex(), now, bestOwner, bestItem, bestVnum, bestUnit, &bestPart))
            return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyQuantity = bestPart;   // MT2009_PLUS_BOT_SHOP_MGMT_V1
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        sys_log(0, "PLAYERBOT_MARKET: sink pick pid=%u name=%s owner=%u item=%u vnum=%u unit=%lld lv=%d horse=%u gold=%lld",
            ch->GetPlayerID(), ch->GetName(), bestOwner, bestItem, bestVnum, bestUnit, (int)ch->GetLevel(),
            (unsigned int)ch->GetHorseLevel(), (long long)ch->GetGold());
        return true;
    }

    bool FindPlayerBotBuffSetPick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        if (!ch || ch->GetJob() != JOB_SHAMAN || ch->GetLevel() < 30 || IsPlayerBotSidekickPID(ch->GetPlayerID()))
            return false;
        DWORD& next = s_mapPlayerBotBuffSetNextLook[ch->GetPlayerID()];
        if (next != 0 && !Due(now, next)) return false;
        next = now + PLAYERBOT_BUFF_SET_MARKET_LOOK_MS;
        const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
                ? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
        DWORD bestOwner = 0, bestItem = 0;
        long bestIq = 0;
        long long bestPrice = 0;
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
            const auto spawn = shop->GetSpawn();
            if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel) continue;
            for (const auto& [id, line] : shop->GetItems()) {
                const TItemTable* table = line ? line->GetTable() : NULL;
                if (!table || line->GetInfo().count != 1 || IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
                    continue;
                const bool kind = table->bType == ITEM_WEAPON ||
                        (table->bType == ITEM_ARMOR && (table->bSubType == ARMOR_SHIELD ||
                         table->bSubType == ARMOR_EAR || table->bSubType == ARMOR_NECK));
                if (!kind || GetPlayerBotProtoLevelLimit(table) > (int)ch->GetLevel()) continue;
                const long long price = (long long)line->GetPrice().GetTotalYangAmount();
                if (price <= 0) continue;
                LPITEM preview = BotOfflinePreview(*line);
                if (!preview) continue;
                const long iq = SumPlayerBotItemLines(preview, APPLY_INT);
                const bool buyable = iq >= bestIq &&
                        IsPlayerBotBuffSetOffer(ch, preview, price, shop->GetOwnerPID()) &&
                        ch->GetEmptyInventory(preview->GetSize()) >= 0;
                M2_DELETE(preview);
                if (!buyable) continue;
                if (iq < bestIq || (iq == bestIq && bestOwner && price >= bestPrice)) continue;
                bestOwner = shop->GetOwnerPID();
                bestItem = id;
                bestIq = iq;
                bestPrice = price;
            }
        }
        if (!bestOwner) return false;
        auto& o = state.offlineShop;
        o.buyOwner = bestOwner;
        o.buyItem = bestItem;
        o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
        o.farBuy = false;
        ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
        return true;
    }

    // Declared in playerbot_town.h: a gambler's session between the
    // storekeeper and the anvil (BOT_TOWN_PHASE_GAMBLE_MARKET), by Iwakura's
    // answer of 26 September - "Zabiera baze z magazynu do ekwipunku ... i
    // kupuje ulepszacze na rynku i ulepsza, moze wiecej niz 1 Item, poki
    // budzet pozwala". It buys what its pieces lack for their plain steps to
    // +7, a line at a time, the cheapest first, each within
    // PLAYERBOT_GAMBLE_MARKET_BUDGET_PERCENT of what is left of the session's
    // budget, and waits for the db core to deliver each before it looks
    // again. True while it has the tick; false when the step is over - nothing
    // lacking, nothing on the counters it could take, PLAYERBOT_GAMBLE_MARKET_BUYS
    // lines bought, or PLAYERBOT_GAMBLE_MARKET_MS gone.
    bool ManagePlayerBotGambleMarket(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        if (!ch) return false;
        auto& p = state.persona;
        auto& o = state.offlineShop;
        if (!p.bGambleMarketPending || !IsPlayerBotGambling(state, now)) {
            if (o.buyOwner) DropPlayerBotOfflinePick(ch, state, "gamble_over");
            return false;
        }
        if (p.dwGambleMarketUntil == 0) p.dwGambleMarketUntil = now + PLAYERBOT_GAMBLE_MARKET_MS;
        const bool timeUp = Due(now, p.dwGambleMarketUntil);
        // A purchase the db core has not answered yet: its goods are not in
        // the bag, so what is lacking cannot be asked again until they are.
        if (requests.count(ch->GetPlayerID())) {
            if (timeUp) return false;
            SetPlayerBotAction(state, BOT_ACTION_SHOP, now);
            return true;
        }
        if (o.buyOwner) {
            if (timeUp) {
                DropPlayerBotOfflinePick(ch, state, "gamble_time");
                return false;
            }
            RunPlayerBotOfflinePick(ch, state, now);
            return true;
        }
        if (timeUp || p.bGambleMarketBuys >= PLAYERBOT_GAMBLE_MARKET_BUYS ||
                g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
            return false;
        std::map<DWORD, int> missing;
        CollectPlayerBotGambleMissingMaterials(ch, missing);
        if (missing.empty())
            return false;
        const long long left = playerbot_persona::BudgetLeft(p.llGambleGoldStart,
                GetPlayerBotGambleBudgetPercent(p, now), p.llGambleSpent);
        const long long cap = std::min<long long>(left * PLAYERBOT_GAMBLE_MARKET_BUDGET_PERCENT / 100,
                Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR));
        if (!FindPlayerBotGambleMaterialPick(ch, state, missing, cap, now)) {
            PlayerBotLogThrottled("gamble_market_empty", now,
                    "PLAYERBOT_PERSONA: gambler finds none of its materials on the counters pid=%u name=%s lacking=%u cap=%lld bought=%u",
                    ch->GetPlayerID(), ch->GetName(), (unsigned int)missing.size(), cap, (unsigned int)p.bGambleMarketBuys);
            return false;
        }
        ++p.bGambleMarketBuys;
        sys_log(0, "PLAYERBOT_PERSONA: gambler goes for materials pid=%u name=%s owner=%u item=%u lacking=%u line=%u cap=%lld",
                ch->GetPlayerID(), ch->GetName(), o.buyOwner, o.buyItem, (unsigned int)missing.size(),
                (unsigned int)p.bGambleMarketBuys, cap);
        RunPlayerBotOfflinePick(ch, state, now);
        return true;
    }

    // The slips standing on the running stands of this channel as the last
    // ledger pass found them (IsPlayerBotStandingPriceSlip), and when this
    // core first saw each: what CorrectPlayerBotStandingSlips works from.
    struct TPlayerBotStandingSlip { DWORD owner, item; };
    std::vector<TPlayerBotStandingSlip> s_vecPlayerBotStandingSlips;
    std::map<DWORD, DWORD> s_mapPlayerBotSlipSeenAt;

    void AddPlayerBotOfflineLedger(DWORD& stalls, DWORD& lines) {
        s_vecPlayerBotStandingSlips.clear();
        ClearPlayerBotWeaponLinePrices();   // MT2009_PLUS_BOT_GEAR_UPGRADE_V1
        ClearPlayerBotArmourLinePrices();   // MT2009_PLUS_BOT_GEAR_UPGRADE_V2
        // MT2009_PLUS_BOT_GEAR_UPGRADE_V1: a core that is not the shop channel
        // counts no stand below, and its bots buy on the shop channel's stands
        // (RunPlayerBotOfflinePick asks for the move): their weapons are priced
        // from there.
        if (CPlayerBotManager::instance().IsChannelTableMode() &&
                (int)g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
            for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
                if (!shop || shop->GetDuration() == 0 ||
                        (int)shop->GetSpawn().channel != playerbot_channel_rules::SHOP_CHANNEL) continue;
                for (const auto& [id, item] : shop->GetItems()) {
                    if (item && item->GetTable() && item->GetTable()->bType == ITEM_WEAPON)
                        NotePlayerBotWeaponLinePrice(shop->GetSpawn().map, item->GetTable(), item->GetInfo().count,
                            (long long)item->GetPrice().GetTotalYangAmount());
                    // MT2009_PLUS_BOT_GEAR_UPGRADE_V2: and the armour.
                    if (item && item->GetTable() && item->GetTable()->bType == ITEM_ARMOR)
                        NotePlayerBotArmourLinePrice(shop->GetSpawn().map, item->GetTable(), item->GetInfo().count,
                            (long long)item->GetPrice().GetTotalYangAmount());
                }
            }
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || shop->GetDuration() == 0 || shop->GetSpawn().channel != g_bChannel) continue;
            ++stalls;
            ++s_mapPlayerBotStallsByMap[shop->GetSpawn().map];
            if (IsPlayerBotM2Map(shop->GetSpawn().map)) ++s_iPlayerBotStallsInM2;
            const bool botShop = CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID());
            bool rareKinds[PLAYERBOT_RARE_GOODS_KINDS] = { false };
            for (const auto& [id, item] : shop->GetItems()) {
                if (!item) continue;
                // A slipped price is no bot's supply: no bot buys it (Community
                // Patch 5, point 6), so a trip made for it, or a listing held
                // back by it, would be made for nothing. Only a drawn line of one
                // unit is looked at closer, one in a thousand of them.
                bool slip = false;
                if (item->GetInfo().count == 1 && IsPlayerBotPriceSlipDrawn(id)) {
                    if (LPITEM preview = BotOfflinePreview(*item)) {
                        slip = IsPlayerBotStandingPriceSlip(preview, (long long)item->GetPrice().GetTotalYangAmount());
                        M2_DELETE(preview);
                    }
                    if (slip)
                        s_vecPlayerBotStandingSlips.push_back(TPlayerBotStandingSlip{ shop->GetOwnerPID(), id });
                }
                if (!slip) {
                    AddPlayerBotMarketSupply(item->GetVnum(), item->GetInfo().count, shop->GetSpawn().map);
                    // MT2009_PLUS_BOT_GEAR_UPGRADE_V1: the cheapest line of each
                    // weapon by map, for the bots' look from the frontier.
                    NotePlayerBotWeaponLinePrice(shop->GetSpawn().map, item->GetTable(), item->GetInfo().count,
                        (long long)item->GetPrice().GetTotalYangAmount());
                    // MT2009_PLUS_BOT_GEAR_UPGRADE_V2: and of each armour.
                    NotePlayerBotArmourLinePrice(shop->GetSpawn().map, item->GetTable(), item->GetInfo().count,
                        (long long)item->GetPrice().GetTotalYangAmount());
                }
                // MT2009_PLUS_MARKET_V3, point 4: a weapon's average damage, for
                // the census of the best copies (ReportPlayerBotTopCopies).
                if (s_bPlayerBotTopCopyCensus && item->GetTable() && item->GetTable()->bType == ITEM_WEAPON &&
                        item->GetTable()->bSubType != WEAPON_ARROW) {
                    long average = 0;
                    for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
                        if (item->GetInfo().aAttr[a].bType == APPLY_NORMAL_HIT_DAMAGE_BONUS)
                            average += item->GetInfo().aAttr[a].sValue;
                    NotePlayerBotAverageDamageCopy(item->GetVnum(), average);
                }
                if (botShop) {
                    NotePlayerBotCappedLineOnCounter(item->GetVnum(), item->GetInfo().count);
                    NotePlayerBotMissionBooksOnCounter(shop->GetSpawn().map, item->GetVnum(), item->GetInfo().count);
                }
                rareKinds[GetPlayerBotRareGoodsKind(item->GetVnum())] = true;
                ++lines;
            }
            // The bots' counters, and which of them carry a Cor Draconis or a
            // sash (IsPlayerBotRareGoodsShopQuotaFull).
            if (botShop) {
                ++s_iPlayerBotRareGoodsBotShops;
                for (int kind = PLAYERBOT_RARE_GOODS_NONE + 1; kind < PLAYERBOT_RARE_GOODS_KINDS; ++kind)
                    if (rareKinds[kind]) NotePlayerBotShopWithRareGoods(kind);
            }
        }
    }

    // A slip stands four hours at most (Community Patch 5, point 6). Its
    // keeper puts it right at its stand, called a little early
    // (BotOfflineDueSlipLine); this is the core putting it right where the
    // keeper cannot, PLAYERBOT_OFFLINE_SLIP_CORE_FIXES lines a ledger pass: a
    // bot's stand this core hosts whose keeper is not in the world here -
    // logged out, resting, moved to the other channel, where it would wait to
    // be moved back before it served anything - at once; one whose keeper
    // something held away from its stand past the four hours (a person's
    // party, a dungeon, the tower) at the four hours; and one whose age its
    // keeper here does not know, once the keeper has had
    // PLAYERBOT_OFFLINE_SLIP_KEEPER_LEAD_MS since this core first saw it. The
    // price goes through the db core's own edit, the packet a keeper's edit at
    // its board ends in, and nothing is done while the keeper is at its board
    // or has a request of its own under way. A person's stand is left alone.
    void CorrectPlayerBotStandingSlips(DWORD now) {
        using namespace playerbot_offline;
        {
            std::map<DWORD, DWORD> seen;
            for (const auto& slip : s_vecPlayerBotStandingSlips) {
                const auto was = s_mapPlayerBotSlipSeenAt.find(slip.item);
                seen[slip.item] = was != s_mapPlayerBotSlipSeenAt.end() ? was->second : now;
            }
            s_mapPlayerBotSlipSeenAt.swap(seen);
        }
        if (!db_clientdesc || !db_clientdesc->IsPhase(PHASE_DBCLIENT)) return;
        auto& manager = ikashop::GetManager();
        int corrected = 0;
        for (const auto& slip : s_vecPlayerBotStandingSlips) {
            if (corrected >= PLAYERBOT_OFFLINE_SLIP_CORE_FIXES) break;
            if (!CPlayerBotManager::instance().IsRegisteredBotPID(slip.owner) || requests.count(slip.owner)) continue;
            auto shop = manager.GetShopByOwnerID(slip.owner);
            if (!shop || shop->GetDuration() == 0 || shop->IsEditMode() ||
                    shop->GetSpawn().channel != g_bChannel || !IsPlayerBotMapHostedHere(shop->GetSpawn().map))
                continue;
            auto line = shop->GetItem(slip.item);
            if (!line) continue;
            auto keeper = s_mapPlayerBotAIStates.find(slip.owner);
            const char* why = "keeper_away";
            if (keeper != s_mapPlayerBotAIStates.end()) {
                const auto& listed = keeper->second.offlineShop.listed;
                const auto known = listed.find(slip.item);
                const uint32_t slippedAt = known != listed.end() ? known->second.slippedAt : 0;
                if (slippedAt ? !playerbot_stall_rules::SlipDue(slippedAt, now, 0)
                        : !Due(now, s_mapPlayerBotSlipSeenAt[slip.item] + PLAYERBOT_OFFLINE_SLIP_KEEPER_LEAD_MS))
                    continue;
                why = slippedAt ? "keeper_held" : "keeper_late";
            }
            LPITEM preview = BotOfflinePreview(*line);
            if (!preview) continue;
            const long long price = (long long)line->GetPrice().GetTotalYangAmount();
            const bool standing = IsPlayerBotStandingPriceSlip(preview, price);
            const long long normal = std::max<long long>(GetPlayerBotShopAskingPrice(preview),
                    GetPlayerBotRefineInvestment(preview));
            const DWORD vnum = preview->GetVnum();
            M2_DELETE(preview);
            if (!standing || normal <= 0 || normal >= price || normal >= PLAYERBOT_GOLD_MAX) continue; // MT2009_PLUS_YANG_LIMITS_V1
            if (!BotOfflineBudget(now)) break;
            ikashop::TPriceInfo meant{};
            meant.yang = normal;
            manager.SendShopEditItemDBPacket(slip.owner, slip.item, meant);
            if (keeper != s_mapPlayerBotAIStates.end()) {
                auto known = keeper->second.offlineShop.listed.find(slip.item);
                if (known != keeper->second.offlineShop.listed.end()) known->second.slippedAt = 0;
            }
            ++corrected;
            sys_log(0, "PLAYERBOT_OFFLINE: price slip put right by the core pid=%u name=%s item=%u vnum=%u from=%lld to=%lld why=%s",
                slip.owner, shop->GetOwnerName(), slip.item, vnum, price, normal, why);
            // The line's row (playerbot_explain.h): how long this core saw it
            // stand, and why the core and not its keeper.
            if (IsPlayerBotExplainOn()) {
                const auto seenAt = s_mapPlayerBotSlipSeenAt.find(slip.item);
                const long long minutes = seenAt != s_mapPlayerBotSlipSeenAt.end() ? (long long)((now - seenAt->second) / 60000U) : 0;
                const int by = strcmp(why, "keeper_held") == 0 ? per::SLIP_BY_CORE_HELD
                        : (strcmp(why, "keeper_late") == 0 ? per::SLIP_BY_CORE_LATE : per::SLIP_BY_CORE_AWAY);
                std::vector<per::TPair> steps(1, per::Pair(per::STEP_SLIP_PUT_RIGHT, normal, price, minutes, by));
                QueuePlayerBotListingEvent(slip.item, slip.owner, vnum, line->GetInfo().count, per::EVENT_SLIP_FIX_CORE,
                    normal, price, per::EncodePairs(steps, per::STEPS_COLUMN), 0, 0,
                    per::LFLAG_SLIP);
            }
        }
    }
}
#else
namespace {
    // The classic stalls of r40250 are the keepers' online counters, bought
    // from where the buyer stands (FindPlayerBotStallPick): a gambler there
    // goes from the storekeeper to the anvil as it always did.
    bool ManagePlayerBotGambleMarket(LPCHARACTER, TPlayerBotAIState&, DWORD) { return false; }
}
#endif
#endif
