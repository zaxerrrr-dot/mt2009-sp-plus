#ifndef __INC_METIN2_PLAYERBOT_CH2_STAND_H__
#define __INC_METIN2_PLAYERBOT_CH2_STAND_H__

// MT2009_PLUS_BOT_CH2_STAND_V1 - a bot of the second channel with goods worth a stand moves to the first channel and
// opens it there (the owner, 7 and 8 November 2026: "niech boty z ch2 zmieniaja channel na ch1 i tam wystawiaja
// sklepy"; "Czemu nadal boty nie przechodza z ch2 na ch1 aby wystawiac sklepy? Sprawdz to i napraw").
//
// The chain as the test world showed it (8 November, 10:37-11:22, the logs of both channels and the test DB at 11:26):
//   * want: the second channel's stand pass asks for a reason only in its first village right after a town visit
//     (justFinishedInTown / at the pitch) - a bot out hunting never asks; and the reasons were blind to the extra
//     inventory (HasPlayerBotHoardedGoods and the books read the bag's cells; since MT2009_PLUS_BOT_EKW_ROUTE_V1 the
//     materials lie in UPGRADE_INVENTORY and the other builds' books in BOOK_INVENTORY) and to the materials' board
//     (IsPlayerBotMatsBoardCounterDue asked PlayerBotHasCounter, false on every channel but the first). The second
//     channel's 804 bots held 2875 units of the nine short materials (2664 in UPGRADE_INVENTORY), 483 of them six
//     books or more, 0 of them a stand; ERRAND census noted=stand:97 / stand:40 a 10 minutes, nearly all of them the
//     medal droppers' stock and the stands' owners, a handful "phase=open".
//   * cannot pay: the fee test held the horse's training savings back (GetPlayerBotReservedGold): 1616 refusals
//     "cannot_pay" in 45 minutes on channel 1 and 100 on channel 2, purses of 220-350k against a "need" of 376-451k
//     for a stand that costs 8000 - a ch2 bot refused there never asked to move; a medal dropper on ch1 refused so
//     went to its first village and back to the second every 2-4 minutes ("medal_stall_to_m1" / "level_to_m2").
//   * released / moved: a released stand (why=stand) waits in town PLAYERBOT_SHOP_CHANNEL_WAIT_TIMEOUT_MS (75 s); the
//     coordinator moves at most once a gate (120 s) after a request's 30 s of standing - 56 of 56 asks at 10:43 timed
//     out ("waited for the shop channel and goes back to its life") and were moved at 10:44:32 out in the field.
//   * opened: the move is a logout and a login; the reason, the walk and the in-town gate were the old core's state.
//     On channel 1 the bot started where it had walked to, with no memory of its stand: of the 230 bots that arrived
//     on channel 1 in those 45 minutes 13 opened a stand (22 of the 222 moved in since 10:30 own one now) and 23 were
//     sent back to channel 2 within the window.
//   * pinned: every stand owner is on channel 1 (674 of 674 rows; the cost of a live stand keeps it there), so the
//     pin was not the break.
//
// What this does:
//   * the ask (channel 2+, ManagePlayerBotCh2StandAsk, from the stand pass): every PLAYERBOT_CH2_STAND_CHECK_MS (5 min,
//     spread by pid) a free bot (no party, fight, dungeon, war, event, trip, company) with no stand asks the stand's
//     reason - the same GetPlayerBotShopReason the first channel's bots use, now reading the extra inventories and the
//     board on every channel - and a goods reason (the materials' hoard or the board's surplus, a spare, a counter's
//     worth of books, a full bag) that can pay the fee asks for the shop channel at once wherever it is (the stand
//     errand, released at once - MT2009_PLUS_BOT_STAND_ERRAND_NOW_V1), within PLAYERBOT_CH2_STAND_PER_10MIN (24) asks a
//     core a 10 minutes - the rest wait their turn (budget_wait), so a deploy is no relog storm;
//   * the intent rides the move: quest flag playerbot.ch2_stand_at (the time of the ask) - set by this ask and by the
//     town pass's own channel ask (EnsurePlayerBotPrivateShopChannel), saved with the character at the move;
//   * the arrival (channel 1, IsPlayerBotCh2StandDriveDue): a bot with a live intent (PLAYERBOT_CH2_STAND_TTL_S, 90 min)
//     and no stand is driven to its stand as a medal dropper with its stock is - to its first village from wherever
//     it spawned, past the in-town gate, the extra inventory's goods into the bag (PlayerBotEkwFetchGoods), held at its
//     pitch through the two minutes after a spawn - and the channel coordinator does not move it while it goes (the
//     presence pin, PLAYERBOT_CH2_STAND_DRIVE_PIN_MS); the stand opened, or no reason / nothing to sell / the permanent
//     bundle / no first village / the TTL, ends the intent;
//   * the fee (GetPlayerBotStandFeeReserve): a stand's fee and bundle are paid over the base reserve (the earned
//     horse's fee, the teleporter fares, a guild fund) - not over the horse's training savings, which the stand's
//     sales are for;
//   * the reasons read the extra inventories (IsPlayerBotStandStorageReasonsOn): the hoard over the bag and every
//     storage (CollectPlayerBotOwnedItems), and PLAYERBOT_SHOP_BOOK_PRESSURE_MIN surplus books over bag + BOOK_INVENTORY
//     (the bag's rule as it was stays beside it); the board's counter reason on every channel for a bot that could
//     keep a counter on the first (IsPlayerBotCh2StandCandidate);
//   * the materials' board's direct bot-to-bot sale is off unless event flag m2_bot_mats_board_sale_on 1
//     (MT2009_PLUS_BOT_MATS_BOARD_SALE_OPT_IN_V1, playerbot_mats_board.h) - the surplus goes through the stands.
//
// Switches (event flags, read once a second): m2_bot_ch2_stand_off 1 - no ask and no drive (the intent flag is then
// ignored); m2_bot_stand_storage_reasons_off 1 - the reasons read the bag only, as before; m2_bot_stand_fee_full_reserve
// 1 - the fee over the whole reserve again (the horse's savings too). Env (read once): PLAYERBOT_CH2_STAND_PER_10MIN
// (24, 0..1000 asks a core a 10 minutes).
// The log: PLAYERBOT_CH2STAND - ask / drive / opened / ended lines (throttled), census every 10 minutes on every core:
//   ask side (the off-shop channels): checked, busy, has_stand, no_reason, the goods reasons by kind
//     (want_board/hoard/spare/books/bag), no_fee, budget_wait, held, requested (this ask), town_intents (the town
//     pass's), left (moved off this core with an intent), back_unopened (came back with the intent still open),
//     owners_here (bots here whose stand runs on channel 1), owners_arrived;
//   arrival side (the shop channel): arrived (with an intent), to_m1, opened (+ avg minutes from the arrival),
//     no_reason, nothing_to_sell, cannot_pay, bundle, no_village, expired, pending, and fee_eased (fee tests passed that
//     the old reserve refused - every channel), board_sale (the board's direct sale on/off).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_mats_board.h, in the anonymous
// namespace; its hooks are declared where they are asked (playerbot_town.h, playerbot_mats_board.h,
// playerbot_dungeon_runs.h, playerbot_manager.cpp).

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)

namespace
{
	const char* const PLAYERBOT_CH2_STAND_FLAG = "playerbot.ch2_stand_at";
	const int PLAYERBOT_CH2_STAND_TTL_S = 90 * 60;
	const DWORD PLAYERBOT_CH2_STAND_CHECK_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_CHECK_SPREAD_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_BUSY_RETRY_MS = 90 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_BUDGET_RETRY_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_REQUEST_REFRESH_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_REQUEST_HOLD_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_DRIVE_PIN_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_WARMUP_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_WINDOW_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_CH2_STAND_ENTRY_GONE_MS = 2 * 60 * 60 * 1000;

	int ReadPlayerBotYoharaEnvInt(const char* name, int def, int lo, int hi);	// playerbot_yohara_bots.h

	// The switches: 0 the ask and the drive, 1 the reasons' extra inventories, 2 the fee's base reserve.
	bool IsPlayerBotCh2StandSwitchOn(int which)
	{
		static const char* const s_flags[3] = { "m2_bot_ch2_stand_off", "m2_bot_stand_storage_reasons_off",
				"m2_bot_stand_fee_full_reserve" };
		static DWORD s_dwAt = 0;
		static bool s_bOn[3] = { true, true, true };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			for (int i = 0; i < 3; ++i)
				s_bOn[i] = quest::CQuestManager::instance().GetEventFlag(s_flags[i]) == 0;
		}
		return which >= 0 && which < 3 && s_bOn[which];
	}

	bool IsPlayerBotStandStorageReasonsOn()
	{
		return IsPlayerBotCh2StandSwitchOn(1);
	}

	int GetPlayerBotCh2StandPer10Min()
	{
		static int s_i = -1;
		if (s_i < 0)
		{
			s_i = ReadPlayerBotYoharaEnvInt("PLAYERBOT_CH2_STAND_PER_10MIN", 24, 0, 1000);
			sys_log(0, "PLAYERBOT_CH2STAND: config per_10min=%d ttl_min=%d check_min=%u", s_i,
					PLAYERBOT_CH2_STAND_TTL_S / 60, (unsigned int)(PLAYERBOT_CH2_STAND_CHECK_MS / 60000));
		}
		return s_i;
	}

	enum EPlayerBotCh2StandOutcome
	{
		CH2STAND_OPENED = 0,
		CH2STAND_NO_REASON,
		CH2STAND_NOTHING_TO_SELL,
		CH2STAND_CANNOT_PAY,	// not an end: it asks again until the TTL
		CH2STAND_BUNDLE,
		CH2STAND_NO_VILLAGE,
		CH2STAND_EXPIRED,
		CH2STAND_OUTCOMES
	};

	struct TPlayerBotCh2StandBot
	{
		bool loaded;
		int intentAt;	// get_global_time() of the ask, 0: none
		DWORD firstSeen, lastSeen, nextCheck, requestedAt, nextRequest, arrivedAt;
		TPlayerBotCh2StandBot() : loaded(false), intentAt(0), firstSeen(0), lastSeen(0), nextCheck(0), requestedAt(0),
				nextRequest(0), arrivedAt(0) {}
	};
	std::map<DWORD, TPlayerBotCh2StandBot> s_mapPlayerBotCh2Stand;

	struct TPlayerBotCh2StandStats
	{
		// the ask side
		unsigned checked, busy, hasStand, noReason, wantBoard, wantHoard, wantSpare, wantBooks, wantBag, noFee, budgetWait,
				held, requested, townIntents, reasks, left, backUnopened, ownersArrived;
		// the arrival side
		unsigned arrived, toM1, opened, openMinutes, feeEased;
		unsigned outcome[CH2STAND_OUTCOMES];
		TPlayerBotCh2StandStats()
		{
			memset(this, 0, sizeof(*this));
		}
	};
	TPlayerBotCh2StandStats s_kPlayerBotCh2StandStats;
	DWORD s_dwPlayerBotCh2StandCoreStart = 0;
	DWORD s_dwPlayerBotCh2StandWindowAt = 0;
	int s_iPlayerBotCh2StandWindowAsks = 0;

	bool IsPlayerBotCh2StandTableMode()
	{
		return CPlayerBotManager::instance().IsChannelTableMode();
	}

	bool IsPlayerBotCh2StandIntentLive(const TPlayerBotCh2StandBot& b)
	{
		return b.intentAt != 0 && get_global_time() - b.intentAt < PLAYERBOT_CH2_STAND_TTL_S;
	}

	void ClearPlayerBotCh2StandIntent(LPCHARACTER ch, TPlayerBotCh2StandBot& b)
	{
		b.intentAt = 0;
		b.arrivedAt = 0;
		if (ch)
			ch->SetQuestFlag(PLAYERBOT_CH2_STAND_FLAG, 0);
	}

	// The bot's entry; the first look on this core reads the intent the move carried.
	TPlayerBotCh2StandBot& GetPlayerBotCh2StandEntry(LPCHARACTER ch, DWORD now)
	{
		if (!now)
			now = 1;
		if (s_dwPlayerBotCh2StandCoreStart == 0)
			s_dwPlayerBotCh2StandCoreStart = now;
		TPlayerBotCh2StandBot& b = s_mapPlayerBotCh2Stand[ch->GetPlayerID()];
		b.lastSeen = now;
		if (b.loaded)
			return b;
		b.loaded = true;
		b.firstSeen = now;
		b.intentAt = ch->GetQuestFlag(PLAYERBOT_CH2_STAND_FLAG);
		if (b.intentAt == 0)
			return b;
		if (!IsPlayerBotCh2StandIntentLive(b))
		{
			ClearPlayerBotCh2StandIntent(ch, b);
			return b;
		}
		if (g_bChannel == playerbot_channel_rules::SHOP_CHANNEL)
		{
			b.arrivedAt = now;
			++s_kPlayerBotCh2StandStats.arrived;
			PlayerBotLogThrottled("ch2stand_arrived", now,
					"PLAYERBOT_CH2STAND: arrived pid=%u name=%s map=%ld level=%u gold=%lld asked_min_ago=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (unsigned int)ch->GetLevel(),
					(long long)ch->GetGold(), (int)((get_global_time() - b.intentAt) / 60));
		}
		else if (now - s_dwPlayerBotCh2StandCoreStart >= PLAYERBOT_CH2_STAND_WARMUP_MS)
		{
			// back on the second channel with the intent still open: it left the first without opening
			++s_kPlayerBotCh2StandStats.backUnopened;
			PlayerBotLogThrottled("ch2stand_back", now,
					"PLAYERBOT_CH2STAND: back unopened pid=%u name=%s channel=%u asked_min_ago=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)g_bChannel,
					(int)((get_global_time() - b.intentAt) / 60));
			ClearPlayerBotCh2StandIntent(ch, b);
		}
		return b;
	}

	// ---------------------------------------------------------------- the fee

	int GetPlayerBotBaseReservedGold(LPCHARACTER ch);	// playerbot_battle_horse.h
	int GetPlayerBotReservedGold(LPCHARACTER ch);

	// What a stand's fee and bundle are paid over: the base reserve (the horse's savings are the stand's to earn).
	int GetPlayerBotStandFeeReserve(LPCHARACTER ch)
	{
		return IsPlayerBotCh2StandSwitchOn(2) ? GetPlayerBotBaseReservedGold(ch) : GetPlayerBotReservedGold(ch);
	}

	// The open pass's fee test passed where the old reserve would have refused.
	void NotePlayerBotStandFeeEased(LPCHARACTER ch, long long cost)
	{
		if (!ch || !IsPlayerBotCh2StandSwitchOn(2))
			return;
		if ((long long)ch->GetGold() - cost < (long long)GetPlayerBotReservedGold(ch))
			++s_kPlayerBotCh2StandStats.feeEased;
	}

	long long GetPlayerBotStandOpenCost(LPCHARACTER ch)
	{
		return (ch->CountSpecifyItem(50200) > 0 ? 0LL : (long long)PLAYERBOT_SHOP_BUNDLE_PRICE) +
				(long long)aOfflineShopTime[1].price;
	}

	// ---------------------------------------------------------------- the reasons

	// IsPlayerBotMatsBoardCounterDue's question off the shop channel: a bot that could keep a counter on the first.
	bool IsPlayerBotCh2StandCandidate(LPCHARACTER ch)
	{
		return ch && IsPlayerBotCh2StandSwitchOn(0) && g_bChannel != playerbot_channel_rules::SHOP_CHANNEL &&
				IsPlayerBotCh2StandTableMode() && ch->CanOpenShop() && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	// Surplus skill books over the bag and the extra inventory (BOOK_INVENTORY).
	int CountPlayerBotOwnedSurplusSkillBooks(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotStandStorageReasonsOn())
			return 0;
		std::vector<LPITEM> owned;
		CollectPlayerBotOwnedItems(ch, owned);
		int surplus = 0;
		for (size_t i = 0; i < owned.size(); ++i)
		{
			LPITEM item = owned[i];
			if (item && !item->IsEquipped() && !item->isLocked() && IsPlayerBotSurplusSkillBook(ch, item))
				surplus += std::max<int>(1, (int)item->GetCount());
		}
		return surplus;
	}

	// ---------------------------------------------------------------- the ask (off the shop channel)

	void NotePlayerBotCh2StandIntent(LPCHARACTER ch, const char* why)
	{
		if (!ch || g_bChannel == playerbot_channel_rules::SHOP_CHANNEL || !IsPlayerBotCh2StandSwitchOn(0) ||
				!IsPlayerBotCh2StandTableMode())
			return;
		const DWORD now = get_dword_time();
		TPlayerBotCh2StandBot& b = GetPlayerBotCh2StandEntry(ch, now);
		const bool fresh = !IsPlayerBotCh2StandIntentLive(b);
		b.intentAt = get_global_time();
		ch->SetQuestFlag(PLAYERBOT_CH2_STAND_FLAG, b.intentAt);
		if (fresh && why && strcmp(why, "goods") != 0)
			++s_kPlayerBotCh2StandStats.townIntents;
	}

	bool IsPlayerBotCh2StandBusy(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD now)
	{
		const DWORD pid = ch->GetPlayerID();
		return ch->IsDead() || ch->GetParty() || ch->GetVictim() || ch->GetExchange() || ch->GetMyShop() ||
				ch->IsOpenSafebox() || ch->IsCubeOpen() || ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ||
				(state.dwLastCombatActionTime != 0 && now - state.dwLastCombatActionTime < 20000) ||
				state.dwGuildWarEnemyGID != 0 || state.bWorldEventKind != 0 || IsPlayerBotOnDungeonRun(pid) ||
				IsPlayerBotInDungeonBusiness(ch, state) || IsPlayerBotOnTowerBusiness(ch, state) ||
				IsPlayerBotKVHeld(pid) || IsPlayerBotOnKingdomVisit(pid) || IsPlayerBotHeldForCompany(ch) ||
				IsPlayerBotArezzoHeldHere(ch) || IsPlayerBotInMeetup(pid) || IsPlayerBotSummoned(pid);
	}

	// From the stand pass (ManagePlayerBotPrivateShop) of a bot with no stand, off the shop channel.
	void ManagePlayerBotCh2StandAsk(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!ch || !ch->IsItemLoaded() || g_bChannel == playerbot_channel_rules::SHOP_CHANNEL ||
				!IsPlayerBotCh2StandSwitchOn(0) || !IsPlayerBotCh2StandTableMode() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return;
		if (!now)
			now = 1;
		TPlayerBotCh2StandBot& b = GetPlayerBotCh2StandEntry(ch, now);
		// asked: the request stands until the move (the coordinator's gate and the 30 s of standing)
		if (b.requestedAt != 0 && now - b.requestedAt < PLAYERBOT_CH2_STAND_REQUEST_HOLD_MS)
		{
			if ((int)(now - b.nextRequest) >= 0)
			{
				b.nextRequest = now + PLAYERBOT_CH2_STAND_REQUEST_REFRESH_MS;
				if (CPlayerBotManager::instance().RequestShopChannel(ch->GetPlayerID()))
					++s_kPlayerBotCh2StandStats.reasks;
			}
			return;
		}
		if (b.nextCheck == 0)
			b.nextCheck = now + PlayerBotNavHash(ch->GetPlayerID() ^ 0x43483253U) % PLAYERBOT_CH2_STAND_CHECK_SPREAD_MS;
		if ((int)(now - b.nextCheck) < 0)
			return;
		b.nextCheck = now + PLAYERBOT_CH2_STAND_CHECK_MS + PlayerBotNavHash(ch->GetPlayerID() ^ (now / 60000U)) % 60000U;
		++s_kPlayerBotCh2StandStats.checked;
		if (HasPlayerBotOfflineShop(ch))
		{
			++s_kPlayerBotCh2StandStats.hasStand;	// its stand's service asks for the move itself
			return;
		}
		if (IsPlayerBotCh2StandBusy(ch, state, now))
		{
			++s_kPlayerBotCh2StandStats.busy;
			b.nextCheck = now + PLAYERBOT_CH2_STAND_BUSY_RETRY_MS;
			return;
		}
		const BYTE reason = GetPlayerBotShopReason(ch, state);
		const char* kind = NULL;
		switch (reason)
		{
			case PLAYERBOT_SHOP_REASON_HOARD:
				if (IsPlayerBotMatsBoardCounterDue(ch))
				{
					kind = "board";
					++s_kPlayerBotCh2StandStats.wantBoard;
				}
				else
				{
					kind = "hoard";
					++s_kPlayerBotCh2StandStats.wantHoard;
				}
				break;
			case PLAYERBOT_SHOP_REASON_SPARE:
				kind = "spare";
				++s_kPlayerBotCh2StandStats.wantSpare;
				break;
			case PLAYERBOT_SHOP_REASON_BOOKS:
				kind = "books";
				++s_kPlayerBotCh2StandStats.wantBooks;
				break;
			case PLAYERBOT_SHOP_REASON_BAG_FULL:
			case PLAYERBOT_SHOP_REASON_DROPPER_PRESSURE:
				kind = "bag";
				++s_kPlayerBotCh2StandStats.wantBag;
				break;
			default:
				// no goods reason: the medal stock has its own road, the rolls the town pass's (as before)
				++s_kPlayerBotCh2StandStats.noReason;
				return;
		}
		if (ch->CountSpecifyItem(71049) > 0)
		{
			++s_kPlayerBotCh2StandStats.noFee;
			return;
		}
		const long long cost = GetPlayerBotStandOpenCost(ch);
		if ((long long)ch->GetGold() - cost < (long long)GetPlayerBotStandFeeReserve(ch))
		{
			++s_kPlayerBotCh2StandStats.noFee;
			return;
		}
		// the core's budget of asks a 10 minutes
		if (s_dwPlayerBotCh2StandWindowAt == 0 || now - s_dwPlayerBotCh2StandWindowAt >= PLAYERBOT_CH2_STAND_WINDOW_MS)
		{
			s_dwPlayerBotCh2StandWindowAt = now;
			s_iPlayerBotCh2StandWindowAsks = 0;
		}
		if (s_iPlayerBotCh2StandWindowAsks >= GetPlayerBotCh2StandPer10Min())
		{
			++s_kPlayerBotCh2StandStats.budgetWait;
			b.nextCheck = now + PLAYERBOT_CH2_STAND_BUDGET_RETRY_MS +
					PlayerBotNavHash(ch->GetPlayerID() ^ 0x42554447U) % PLAYERBOT_CH2_STAND_BUDGET_RETRY_MS;
			return;
		}
		NotePlayerBotCh2StandIntent(ch, "goods");
		if (!RequestPlayerBotShopErrand(ch, PLAYERBOT_ERRAND_STAND, now))
		{
			++s_kPlayerBotCh2StandStats.held;	// the errand batch holds it (m2_bot_stand_errand_batch 1)
			return;
		}
		++s_iPlayerBotCh2StandWindowAsks;
		++s_kPlayerBotCh2StandStats.requested;
		b.requestedAt = now;
		b.nextRequest = now + PLAYERBOT_CH2_STAND_REQUEST_REFRESH_MS;
		PlayerBotLogThrottled("ch2stand_ask", now,
				"PLAYERBOT_CH2STAND: asks pid=%u name=%s channel=%u why=%s map=%ld level=%u gold=%lld asks_window=%d/%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)g_bChannel, kind, ch->GetMapIndex(),
				(unsigned int)ch->GetLevel(), (long long)ch->GetGold(), s_iPlayerBotCh2StandWindowAsks,
				GetPlayerBotCh2StandPer10Min());
	}

	// The leave loop (CPlayerBotManager::OnChannelAssignments): the bot logs out here for another channel.
	void NotePlayerBotCh2StandLeaving(DWORD pid)
	{
		std::map<DWORD, TPlayerBotCh2StandBot>::iterator it = s_mapPlayerBotCh2Stand.find(pid);
		if (it == s_mapPlayerBotCh2Stand.end())
			return;
		if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL && IsPlayerBotCh2StandIntentLive(it->second))
			++s_kPlayerBotCh2StandStats.left;
		s_mapPlayerBotCh2Stand.erase(it);	// read again from its flag when it comes back
	}

	// ---------------------------------------------------------------- the arrival (the shop channel)

	bool IsPlayerBotCh2StandDriveDue(LPCHARACTER ch, DWORD now)
	{
		if (!ch || g_bChannel != playerbot_channel_rules::SHOP_CHANNEL || !IsPlayerBotCh2StandSwitchOn(0) ||
				!IsPlayerBotCh2StandTableMode())
			return false;
		TPlayerBotCh2StandBot& b = GetPlayerBotCh2StandEntry(ch, now);
		if (b.intentAt == 0)
			return false;
		if (!IsPlayerBotCh2StandIntentLive(b))
		{
			++s_kPlayerBotCh2StandStats.outcome[CH2STAND_EXPIRED];
			PlayerBotLogThrottled("ch2stand_end", now, "PLAYERBOT_CH2STAND: ended pid=%u name=%s why=expired map=%ld",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex());
			ClearPlayerBotCh2StandIntent(ch, b);
			return false;
		}
		if (b.arrivedAt == 0)
			b.arrivedAt = now;
		return true;
	}

	void NotePlayerBotCh2StandOutcome(LPCHARACTER ch, int outcome)
	{
		if (!ch || outcome < 0 || outcome >= CH2STAND_OUTCOMES)
			return;
		std::map<DWORD, TPlayerBotCh2StandBot>::iterator it = s_mapPlayerBotCh2Stand.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotCh2Stand.end() || it->second.intentAt == 0)
			return;
		++s_kPlayerBotCh2StandStats.outcome[outcome];
		if (outcome == CH2STAND_CANNOT_PAY)
			return;
		static const char* const s_names[CH2STAND_OUTCOMES] = { "opened", "no_reason", "nothing_to_sell", "cannot_pay",
				"bundle", "no_village", "expired" };
		PlayerBotLogThrottled("ch2stand_end", get_dword_time(),
				"PLAYERBOT_CH2STAND: ended pid=%u name=%s why=%s map=%ld gold=%lld min_since_arrival=%u",
				ch->GetPlayerID(), ch->GetName(), s_names[outcome], ch->GetMapIndex(), (long long)ch->GetGold(),
				it->second.arrivedAt ? (unsigned int)((get_dword_time() - it->second.arrivedAt) / 60000U) : 0U);
		ClearPlayerBotCh2StandIntent(ch, it->second);
	}

	void NotePlayerBotCh2StandToM1(LPCHARACTER ch, long homeMap)
	{
		++s_kPlayerBotCh2StandStats.toM1;
		PlayerBotLogThrottled("ch2stand_drive", get_dword_time(),
				"PLAYERBOT_CH2STAND: to its first village pid=%u name=%s from=%ld to=%ld level=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), homeMap, (unsigned int)ch->GetLevel());
	}

	// The stand pass's first look: a bot that came for its stand and has it now.
	void NotePlayerBotCh2StandShopSeen(LPCHARACTER ch)
	{
		if (!ch || g_bChannel != playerbot_channel_rules::SHOP_CHANNEL)
			return;
		std::map<DWORD, TPlayerBotCh2StandBot>::iterator it = s_mapPlayerBotCh2Stand.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotCh2Stand.end())
		{
			if (!IsPlayerBotCh2StandSwitchOn(0))
				return;
			GetPlayerBotCh2StandEntry(ch, get_dword_time());	// the arrival's first look reads its flag
			it = s_mapPlayerBotCh2Stand.find(ch->GetPlayerID());
		}
		if (it == s_mapPlayerBotCh2Stand.end() || it->second.intentAt == 0)
			return;
		++s_kPlayerBotCh2StandStats.opened;
		if (it->second.arrivedAt)
			s_kPlayerBotCh2StandStats.openMinutes += (get_dword_time() - it->second.arrivedAt) / 60000U;
		NotePlayerBotCh2StandOutcome(ch, CH2STAND_OPENED);
	}

	// The presence pin (PublishChannelPresence): a bot on its way to the stand it came for stays.
	bool IsPlayerBotCh2StandDrivePinned(DWORD pid, DWORD now)
	{
		if (g_bChannel != playerbot_channel_rules::SHOP_CHANNEL || !IsPlayerBotCh2StandSwitchOn(0))
			return false;
		std::map<DWORD, TPlayerBotCh2StandBot>::const_iterator it = s_mapPlayerBotCh2Stand.find(pid);
		return it != s_mapPlayerBotCh2Stand.end() && it->second.intentAt != 0 && it->second.arrivedAt != 0 &&
				now - it->second.arrivedAt < PLAYERBOT_CH2_STAND_DRIVE_PIN_MS;
	}

	// ---------------------------------------------------------------- the census

	bool IsPlayerBotMatsBoardOff(int part);	// playerbot_mats_board.h

	void ManagePlayerBotCh2Stand(DWORD now)
	{
		static DWORD s_dwNextCensus = 0;
		if (!now)
			now = 1;
		if (s_dwPlayerBotCh2StandCoreStart == 0)
			s_dwPlayerBotCh2StandCoreStart = now;
		if (s_dwNextCensus == 0)
		{
			s_dwNextCensus = now + PLAYERBOT_CH2_STAND_CENSUS_MS;
			GetPlayerBotCh2StandPer10Min();	// the config line at the core's start
			return;
		}
		if ((int)(now - s_dwNextCensus) < 0)
			return;
		s_dwNextCensus = now + PLAYERBOT_CH2_STAND_CENSUS_MS;
		unsigned pending = 0, ownersHere = 0;
		const bool shopChannel = g_bChannel == playerbot_channel_rules::SHOP_CHANNEL;
		for (std::map<DWORD, TPlayerBotCh2StandBot>::iterator it = s_mapPlayerBotCh2Stand.begin();
				it != s_mapPlayerBotCh2Stand.end();)
		{
			if (now - it->second.lastSeen >= PLAYERBOT_CH2_STAND_ENTRY_GONE_MS)
			{
				s_mapPlayerBotCh2Stand.erase(it++);
				continue;
			}
			if (IsPlayerBotCh2StandIntentLive(it->second))
				++pending;
			++it;
		}
		if (!shopChannel)
		{
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				auto shop = ikashop::GetManager().GetShopByOwnerID(it->first);
				if (shop && shop->GetDuration() != 0)
					++ownersHere;
			}
		}
		TPlayerBotCh2StandStats& s = s_kPlayerBotCh2StandStats;
		sys_log(0, "PLAYERBOT_CH2STAND: census channel=%u on=%d per_10min=%d storage_reasons=%d fee_base_reserve=%d "
				"board_sale=%d | ask checked=%u busy=%u has_stand=%u no_reason=%u want_board=%u want_hoard=%u "
				"want_spare=%u want_books=%u want_bag=%u no_fee=%u budget_wait=%u held=%u requested=%u town_intents=%u "
				"reasks=%u left=%u back_unopened=%u owners_here=%u | arrival arrived=%u to_m1=%u opened=%u "
				"open_avg_min=%u no_reason=%u nothing_to_sell=%u cannot_pay=%u bundle=%u no_village=%u expired=%u "
				"pending=%u fee_eased=%u",
				(unsigned int)g_bChannel, IsPlayerBotCh2StandSwitchOn(0) ? 1 : 0, GetPlayerBotCh2StandPer10Min(),
				IsPlayerBotStandStorageReasonsOn() ? 1 : 0, IsPlayerBotCh2StandSwitchOn(2) ? 1 : 0,
				IsPlayerBotMatsBoardOff(MATS_BOARD_SALE) ? 0 : 1,
				s.checked, s.busy, s.hasStand, s.noReason, s.wantBoard, s.wantHoard, s.wantSpare, s.wantBooks, s.wantBag,
				s.noFee, s.budgetWait, s.held, s.requested, s.townIntents, s.reasks, s.left, s.backUnopened, ownersHere,
				s.arrived, s.toM1, s.opened, s.opened ? s.openMinutes / s.opened : 0U,
				s.outcome[CH2STAND_NO_REASON], s.outcome[CH2STAND_NOTHING_TO_SELL], s.outcome[CH2STAND_CANNOT_PAY],
				s.outcome[CH2STAND_BUNDLE], s.outcome[CH2STAND_NO_VILLAGE], s.outcome[CH2STAND_EXPIRED], pending,
				s.feeEased);
		s_kPlayerBotCh2StandStats = TPlayerBotCh2StandStats();
	}
}

#else

namespace
{
	bool IsPlayerBotStandStorageReasonsOn() { return false; }
	int GetPlayerBotStandFeeReserve(LPCHARACTER ch) { return GetPlayerBotReservedGold(ch); }
	void NotePlayerBotStandFeeEased(LPCHARACTER, long long) {}
	bool IsPlayerBotCh2StandCandidate(LPCHARACTER) { return false; }
	int CountPlayerBotOwnedSurplusSkillBooks(LPCHARACTER) { return 0; }
	void NotePlayerBotCh2StandLeaving(DWORD) {}
	bool IsPlayerBotCh2StandDrivePinned(DWORD, DWORD) { return false; }
	void ManagePlayerBotCh2Stand(DWORD) {}
}

#endif

#endif
