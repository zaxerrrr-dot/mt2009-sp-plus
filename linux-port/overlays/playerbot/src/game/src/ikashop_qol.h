// MT2009_PLUS_SHOP_QOL_V2 (Autor: Vekirion) - a new engine file kept in the overlay, like
// auction_house.cpp; server-patches/shopqol includes it from ikarus_shop_manager.cpp.
//
// MT2009_PLUS_SHOP_QOL_V2 - the offline shops' second round (2026-10-13):
//   * the bigger shop: a person's shop gets the bots' second page while the
//     event flag m2_shop_big_on is 1 (the classic panel's switch, web_admin.quest)
//   * the age of a line (since it was put up or last sold from) for the owner's
//     "stale" frame, and the automatic price drop: X% every Y hours nobody bought,
//     never under a minimum - player.ikashop_item_meta, one row a line
//   * /ikashop_autoprice, /ikashop_extend, /ikashop_buy_part (cmd.cpp)
// Included once, by ikarus_shop_manager.cpp (inside no namespace).
#pragma once

#include <unordered_map>

namespace ikashop_qol
{
	constexpr const char* BIG_SHOP_FLAG = "m2_shop_big_on";
	constexpr int AUTO_PRICE_PCT_MAX = 50;
	constexpr int AUTO_PRICE_HOURS_MAX = 720;

	inline bool BigShopsOn()
	{
		return quest::CQuestManager::instance().GetEventFlag(BIG_SHOP_FLAG) != 0;
	}

	inline int PageCells()
	{
		return SHOP_PLAYER_WIDTH * SHOP_PLAYER_HEIGHT;
	}

	// The pages the owner's window lays out: two while the switch is on, and
	// two while a line still stands on the second page after it went off (the
	// line stays sellable, only new ones go to the first page).
	inline int OwnerPages(ikashop::CShop* shop)
	{
		if (BigShopsOn())
			return 2;
		if (shop)
			for (const auto& [id, line] : shop->GetItems())
				if (line && (int) line->GetInfo().pos >= PageCells())
					return 2;
		return 1;
	}

	// ------------------------------------------------------------------ meta
	inline long long Now()
	{
		return (long long) get_global_time();
	}

	// MT2009_PLUS_SHOP_QOL_AUTH_GUARD_V1: the auth core runs UpdateShopsDuration too
	// (g_bChannel is 1 there) but holds no shops and talks to the account
	// database - no table, no clocks, no cleanup there.
	inline bool SkipCore()
	{
		return g_bAuthServer != 0;
	}

	inline void EnsureTable()
	{
		static bool done = false;
		if (done || SkipCore())
			return;
		done = true;
		DBManager::instance().Query(
			"CREATE TABLE IF NOT EXISTS ikashop_item_meta ("
			" item_id INT UNSIGNED NOT NULL PRIMARY KEY,"
			" owner INT UNSIGNED NOT NULL DEFAULT 0,"
			" since INT UNSIGNED NOT NULL DEFAULT 0,"
			" ap_anchor INT UNSIGNED NOT NULL DEFAULT 0,"
			" ap_pct TINYINT UNSIGNED NOT NULL DEFAULT 0,"
			" ap_hours SMALLINT UNSIGNED NOT NULL DEFAULT 0,"
			" ap_min BIGINT NOT NULL DEFAULT 0,"
			" KEY owner_idx (owner)"
			") ENGINE=InnoDB");
	}

	// A line put up: its clock starts, with no price drop.
	inline void OnListed(DWORD owner, DWORD item)
	{
		EnsureTable();
		const long long now = Now();
		DBManager::instance().Query(
			"REPLACE INTO ikashop_item_meta (item_id, owner, since, ap_anchor, ap_pct, ap_hours, ap_min) "
			"VALUES (%u, %u, %lld, %lld, 0, 0, 0)", item, owner, now, now);
	}

	// A part of the stack sold: both clocks start again.
	inline void OnPartSold(DWORD item)
	{
		EnsureTable();
		const long long now = Now();
		DBManager::instance().Query(
			"UPDATE ikashop_item_meta SET since=%lld, ap_anchor=%lld WHERE item_id=%u", now, now, item);
	}

	// The owner changed the price by hand: the drop counts from now.
	inline void OnPriceEdited(DWORD item)
	{
		EnsureTable();
		DBManager::instance().Query(
			"UPDATE ikashop_item_meta SET ap_anchor=%lld WHERE item_id=%u", Now(), item);
	}

	// The line left the shop (sold whole, taken off).
	inline void OnRemoved(DWORD item)
	{
		EnsureTable();
		DBManager::instance().Query("DELETE FROM ikashop_item_meta WHERE item_id=%u", item);
	}

	inline void SendMetaLine(LPCHARACTER ch, DWORD item, long long since, int pct, int hours, long long minYang)
	{
		if (ch && ch->GetDesc())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "IkaShopMeta %u %lld %d %d %lld", item, since, pct, hours, minYang);
	}

	// The owner's window opened: the pages, then every line's clock and drop.
	// A line with no row yet (put up before this existed) starts its clock now.
	inline void SendOwnerMeta(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc())
			return;
		auto shop = ch->GetIkarusShop();
		ch->ChatPacket(CHAT_TYPE_COMMAND, "IkaShopPages %d", OwnerPages(shop ? shop.get() : nullptr));
		if (!shop)
			return;

		EnsureTable();
		struct TMeta { long long since; int pct; int hours; long long minYang; };
		std::unordered_map<DWORD, TMeta> rows;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
			"SELECT item_id, since, ap_pct, ap_hours, ap_min FROM ikashop_item_meta WHERE owner=%u", ch->GetPlayerID()));
		if (msg && msg->Get() && msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				DWORD id = 0;
				TMeta meta{};
				str_to_number(id, row[0]);
				str_to_number(meta.since, row[1]);
				str_to_number(meta.pct, row[2]);
				str_to_number(meta.hours, row[3]);
				str_to_number(meta.minYang, row[4]);
				rows[id] = meta;
			}
		}

		const long long now = Now();
		for (const auto& [id, line] : shop->GetItems())
		{
			auto it = rows.find(id);
			if (it == rows.end())
			{
				DBManager::instance().Query(
					"INSERT IGNORE INTO ikashop_item_meta (item_id, owner, since, ap_anchor) VALUES (%u, %u, %lld, %lld)",
					id, ch->GetPlayerID(), now, now);
				SendMetaLine(ch, id, now, 0, 0, 0);
			}
			else
				SendMetaLine(ch, id, it->second.since, it->second.pct, it->second.hours, it->second.minYang);
		}
	}

	// /ikashop_autoprice <item> <pct> <hours> <minYang>; pct 0 switches it off.
	inline void SetAutoPrice(LPCHARACTER ch, DWORD item, int pct, int hours, long long minYang)
	{
		if (!ch || !ch->GetIkarusShop())
			return;
		auto shop = ch->GetIkarusShop();
		auto line = shop->GetItem(item);
		if (!line)
			return;
		if (pct < 0 || pct > AUTO_PRICE_PCT_MAX || (pct > 0 && (hours < 1 || hours > AUTO_PRICE_HOURS_MAX)) || minYang < 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Auto-obnizka: od 1 do %d%% co 1-%d godzin.", AUTO_PRICE_PCT_MAX, AUTO_PRICE_HOURS_MAX);
			return;
		}
		if (pct == 0)
		{
			hours = 0;
			minYang = 0;
		}
		EnsureTable();
		const long long now = Now();
		DBManager::instance().Query(
			"INSERT INTO ikashop_item_meta (item_id, owner, since, ap_anchor, ap_pct, ap_hours, ap_min) "
			"VALUES (%u, %u, %lld, %lld, %d, %d, %lld) "
			"ON DUPLICATE KEY UPDATE owner=VALUES(owner), ap_anchor=VALUES(ap_anchor), ap_pct=VALUES(ap_pct), "
			"ap_hours=VALUES(ap_hours), ap_min=VALUES(ap_min)",
			item, ch->GetPlayerID(), now, now, pct, hours, minYang);

		long long since = now;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
			"SELECT since FROM ikashop_item_meta WHERE item_id=%u", item));
		if (msg && msg->Get() && msg->Get()->uiNumRows > 0)
			if (MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult))
				str_to_number(since, row[0]);
		SendMetaLine(ch, item, since, pct, hours, minYang);
	}

	// The price a drop of pct leaves: down by pct (at least 1 Yang), never
	// under minYang (nor under 1).
	inline long long DroppedPrice(long long price, int pct, long long minYang)
	{
		const long long floorYang = std::max<long long>(1, minYang);
		if (price <= floorYang)
			return price;
		long long step = price * pct / 100;
		if (step < 1)
			step = 1;
		return std::max(floorYang, price - step);
	}

	// Every minute on every core (UpdateShopsDuration). A shop's drops are the
	// core's that stands it (its entity is here), so they happen once.
	inline void Process(ikashop::CShopManager& manager, const std::map<DWORD, std::shared_ptr<ikashop::CShop>>& shops)
	{
		if (SkipCore()) // MT2009_PLUS_SHOP_QOL_AUTH_GUARD_V1
			return;
		bool anyLocal = false;
		for (const auto& [owner, shop] : shops)
			if (shop && shop->GetEntity() && shop->GetDuration() > 0)
			{
				anyLocal = true;
				break;
			}
		if (!anyLocal)
			return;

		EnsureTable();
		const long long now = Now();
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
			"SELECT item_id, owner, ap_anchor, ap_pct, ap_hours, ap_min FROM ikashop_item_meta "
			"WHERE ap_pct > 0 AND ap_hours > 0 AND ap_anchor + ap_hours * 3600 <= %lld LIMIT 500", now));
		if (!msg || !msg->Get() || msg->Get()->uiNumRows == 0)
			return;

		MYSQL_ROW row;
		while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			DWORD item = 0, owner = 0;
			long long anchor = 0, minYang = 0;
			int pct = 0, hours = 0;
			str_to_number(item, row[0]);
			str_to_number(owner, row[1]);
			str_to_number(anchor, row[2]);
			str_to_number(pct, row[3]);
			str_to_number(hours, row[4]);
			str_to_number(minYang, row[5]);

			auto it = shops.find(owner);
			if (it == shops.end() || !it->second)
				continue;
			auto& shop = it->second;
			if (!shop->GetEntity() || shop->GetDuration() == 0 || shop->IsEditMode())
				continue;
			auto line = shop->GetItem(item);
			if (!line)
				continue;

			ikashop::TPriceInfo price = line->GetPrice();
			const long long dropped = DroppedPrice(price.yang, pct, minYang);
			// Whole steps missed while the shop stood closed are not caught up:
			// one drop, and the next counts from now.
			DBManager::instance().Query("UPDATE ikashop_item_meta SET ap_anchor=%lld WHERE item_id=%u", now, item);
			if (dropped >= price.yang)
				continue;
			price.yang = dropped;
			manager.SendShopEditItemDBPacket(owner, item, price);
			if (LPCHARACTER ownerCh = CHARACTER_MANAGER::instance().FindByPID(owner))
			{
				ownerCh->ChatPacket(CHAT_TYPE_COMMAND, "IkaShopAutoPrice %u %lld", item, dropped);
			}
		}
	}

	// Once an hour: rows of lines that left the shops some other way (expired,
	// the shop closed and emptied) and are older than a day.
	inline void Cleanup()
	{
		static long long next = 0;
		const long long now = Now();
		if (now < next)
			return;
		next = now + 3600;
		if (g_bChannel != 1 || SkipCore()) // MT2009_PLUS_SHOP_QOL_AUTH_GUARD_V1
			return;
		EnsureTable();
		DBManager::instance().Query(
			"DELETE m FROM ikashop_item_meta m LEFT JOIN item i ON i.id = m.item_id AND i.`window` = 'IKASHOP_OFFLINESHOP' "
			"WHERE i.id IS NULL AND m.since < %lld", now - 86400);
	}
}
