// MT2009_PLUS_FISH_PUZZLE_V1 - Event Rybacki - Puzzle (Wedkarskie Puzzle; the owner, 3 November 2026; server-patches/
// fishpuzzle, README.md). The official event of version 17.3 (pl-wiki "Event Rybacki - Puzzle", "Minigra: Wedkarskie
// Puzzle", "Pudlo wedkarskich puzzli", "Zl. Skrzynia na Ryby (D)"); the window and its pictures are GF 26.1.11's
// (uiscript/minigamefishgamepage.py, d:/ymir work/ui/minigame/fish_event, fishingevnet001.dds).
//
// NO NEW EXE. Neither our exe (client-build = exe-src8, exe-out9) nor the Ameria sources have the official
// HEADER_CG/GC fish event packets (Ameria has only a stray IsOpenJigsaw() call and the desc text; Owsap only the two
// uiscripts), so everything goes through the chat command channel every python-only system here uses:
//   client -> server  "/fishpuzzle open | box <1 normal | 2 deluxe> | place <cell 0-23> | discard"
//   server -> client  "FP state <event on> <attempts> <pending shape 0-7> <normal boxes> <deluxe boxes> <pieces|->"
//                     "FP open"   (a box used from the inventory: the window opens)
//                     "FP piece <shape> <attempts>"   (a box was opened - the piece to place)
//                     "FP done <attempts> <reward vnum>"   (the board is full: the reward came, the board is empty again)
//   pieces: two characters a placed piece - its shape '1'-'7' and its top-left cell 'a' + (0..23), row by row (6 x 4).
//
// The rules (the wiki): fishing during the event finds a Pudlo wedkarskich puzzli (25106) with 30% of the catches
// (event flag fish_puzzle_chance, per mille, 300), with Rybie Wnetrznosci (the premium fish mind or the unique group
// 10009: 71008, 72013-72015) every catch, and then 2% (fish_puzzle_deluxe, 20) of the catches a Luks. pudlo wedk.
// puzzli (25107) instead. A box opened in the window gives one random piece of six (25106) or the big 3x2 piece
// (25107); every box opened is an attempt. The piece goes onto the 6 x 4 board where it fits (no overlap, inside the
// board) or is thrown away (right click). The board full: +30 000 experience and by the attempts Zl. Skrzynia na Ryby
// (D) 83003 (10 or fewer), (S) 83002 (11-24) or (M) 83001 (25 or more) - opened 3 / 2 / 1 time(s)
// (ShipDefense_ChestKeep), the contents special_item_group.fishpuzzle.txt. The board, the piece in hand and the
// attempts live in player.fish_puzzle (fish_puzzle.sql), so a relog or a channel change keeps the game.
//
// The event (planner kind "fishpuzzle", event flag fish_puzzle_event, playerbot_ingame_events.h) only gates the
// boxes found while fishing: boxes left over can be opened and the board finished after it, as the wiki's window
// stays in the event list's reward window. Bots never get a box (their catches are skipped) and cannot play.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "db.h"
#include "log.h"
#include "questmanager.h"
#include "unique_item.h"
#include "utils.h"

#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace fishpuzzle
{
	enum
	{
		COLS = 6,
		ROWS = 4,
		CELLS = COLS * ROWS,
		SHAPE_DELUXE = 7,
		SHAPE_MAX = 7,
		BOX_NORMAL = 25106,
		BOX_DELUXE = 25107,
		CHEST_M = 83001,	// Zl. Skrzynia na Ryby (M): 25 attempts or more
		CHEST_S = 83002,	// Zl. Skrzynia na Ryby (S): 11-24
		CHEST_D = 83003,	// Zl. Skrzynia na Ryby (D): 10 or fewer
		REWARD_EXP = 30000,
		COMMAND_GAP_MS = 150,
	};

	// The seven pieces, as GF's pictures fish_1..fish_7.sub draw them (fishingevnet001.dds, 32 px a cell): the cells
	// (dx, dy) of each from its top-left corner, which need not be filled (the L pieces).
	struct TShape
	{
		BYTE n;
		signed char cell[6][2];
	};
	static const TShape s_aShape[SHAPE_MAX + 1] =
	{
		{ 0, { { 0, 0 } } },
		{ 3, { { 0, 0 }, { 0, 1 }, { 0, 2 } } },						// 1: three high
		{ 1, { { 0, 0 } } },											// 2: one
		{ 3, { { 0, 0 }, { 0, 1 }, { 1, 1 } } },						// 3: L (the corner bottom left)
		{ 3, { { 0, 0 }, { 1, 0 }, { 1, 1 } } },						// 4: L (the corner top right)
		{ 4, { { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } } },				// 5: square
		{ 4, { { 0, 0 }, { 1, 0 }, { 1, 1 }, { 2, 1 } } },				// 6: Z
		{ 6, { { 0, 0 }, { 1, 0 }, { 2, 0 }, { 0, 1 }, { 1, 1 }, { 2, 1 } } },	// 7: the deluxe 3 x 2
	};

	struct TPiece
	{
		BYTE shape;
		BYTE pos;
	};

	struct TState
	{
		std::vector<TPiece> pieces;
		BYTE pending;
		int uses;
		int completed;
	};

	std::map<DWORD, DWORD> s_mapLastCommand;	// pid -> get_dword_time() of the last command

	bool Fits(const std::vector<TPiece>& pieces, BYTE shape, int pos, bool* grid = NULL)
	{
		if (shape < 1 || shape > SHAPE_MAX || pos < 0 || pos >= CELLS)
			return false;
		bool used[CELLS];
		memset(used, 0, sizeof(used));
		for (size_t i = 0; i < pieces.size(); ++i)
		{
			const TShape& s = s_aShape[pieces[i].shape];
			for (int c = 0; c < s.n; ++c)
				used[(pieces[i].pos / COLS + s.cell[c][1]) * COLS + pieces[i].pos % COLS + s.cell[c][0]] = true;
		}
		const TShape& s = s_aShape[shape];
		for (int c = 0; c < s.n; ++c)
		{
			const int x = pos % COLS + s.cell[c][0];
			const int y = pos / COLS + s.cell[c][1];
			if (x >= COLS || y >= ROWS || used[y * COLS + x])
				return false;
		}
		if (grid)
		{
			memcpy(grid, used, sizeof(used));
			for (int c = 0; c < s.n; ++c)
				grid[(pos / COLS + s.cell[c][1]) * COLS + pos % COLS + s.cell[c][0]] = true;
		}
		return true;
	}

	std::string Encode(const std::vector<TPiece>& pieces)
	{
		std::string s;
		for (size_t i = 0; i < pieces.size(); ++i)
		{
			s += (char)('0' + pieces[i].shape);
			s += (char)('a' + pieces[i].pos);
		}
		return s;
	}

	// A stored board is rebuilt piece by piece through Fits, so nothing the table holds can break the board.
	void Decode(const char* text, std::vector<TPiece>& pieces)
	{
		pieces.clear();
		if (!text)
			return;
		const size_t len = strlen(text);
		for (size_t i = 0; i + 1 < len; i += 2)
		{
			const int shape = text[i] - '0';
			const int pos = text[i + 1] - 'a';
			if (shape < 1 || shape > SHAPE_MAX || !Fits(pieces, (BYTE)shape, pos))
				continue;
			TPiece p;
			p.shape = (BYTE)shape;
			p.pos = (BYTE)pos;
			pieces.push_back(p);
		}
	}

	void Load(DWORD pid, TState& st)
	{
		st.pieces.clear();
		st.pending = 0;
		st.uses = 0;
		st.completed = 0;
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"SELECT pieces, pending, uses, completed FROM fish_puzzle WHERE pid = %u", pid));
		if (!pMsg.get() || !pMsg->Get() || pMsg->Get()->uiNumRows == 0)
			return;
		MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
		if (!row)
			return;
		Decode(row[0], st.pieces);
		int pending = 0;
		str_to_number(pending, row[1]);
		st.pending = (pending >= 1 && pending <= SHAPE_MAX) ? (BYTE)pending : 0;
		str_to_number(st.uses, row[2]);
		str_to_number(st.completed, row[3]);
		if (st.uses < 0)
			st.uses = 0;
	}

	void Save(DWORD pid, const TState& st)
	{
		// only [1-7a-x] in the pieces (Encode), numbers elsewhere - nothing to escape
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"REPLACE INTO fish_puzzle (pid, pieces, pending, uses, completed) VALUES (%u, '%s', %u, %d, %d)",
				pid, Encode(st.pieces).c_str(), (unsigned int)st.pending, st.uses, st.completed));
	}

	bool EventOn()
	{
		return quest::CQuestManager::instance().GetEventFlag("fish_puzzle_event") > 0;
	}

	bool Playable(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot() && ch->GetDesc()->IsPhase(PHASE_GAME);
	}

	void SendState(LPCHARACTER ch, const TState& st)
	{
		const std::string pieces = Encode(st.pieces);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "FP state %d %d %u %u %u %s", EventOn() ? 1 : 0, st.uses, (unsigned int)st.pending,
				(unsigned int)ch->CountSpecifyItem(BOX_NORMAL), (unsigned int)ch->CountSpecifyItem(BOX_DELUXE),
				pieces.empty() ? "-" : pieces.c_str());
	}

	DWORD RewardFor(int uses)
	{
		if (uses <= 10)
			return CHEST_D;
		if (uses <= 24)
			return CHEST_S;
		return CHEST_M;
	}

	bool Busy(LPCHARACTER ch)
	{
		if (ch->GetExchange() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->GetMyShop())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij handel, sklep i magazyn, zanim otworzysz pud\263o puzzli.");
			return true;
		}
		return false;
	}

	void Box(LPCHARACTER ch, TState& st, int kind)
	{
		if (st.pending)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Najpierw u\277yj albo odrzu\346 element puzzli, kt\363ry trzymasz.");
			return;
		}
		const DWORD vnum = kind == 2 ? BOX_DELUXE : BOX_NORMAL;
		if (ch->CountSpecifyItem(vnum) < 1)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, kind == 2 ? "Nie masz luksusowego pud\263a w\352dkarskich puzzli."
					: "Nie masz pud\263a w\352dkarskich puzzli - z\263ap je w\352dk\261 podczas eventu.");
			return;
		}
		if (Busy(ch))
			return;
		ch->RemoveSpecifyItem(vnum, 1);
		st.pending = kind == 2 ? (BYTE)SHAPE_DELUXE : (BYTE)number(1, 6);
		++st.uses;
		Save(ch->GetPlayerID(), st);
		LogManager::instance().ItemLog(ch, 0, vnum, "FISH_PUZZLE_BOX", std::to_string((int)st.pending).c_str());
		ch->ChatPacket(CHAT_TYPE_COMMAND, "FP piece %u %d", (unsigned int)st.pending, st.uses);
	}

	void Place(LPCHARACTER ch, TState& st, int pos)
	{
		if (!st.pending)
			return;
		bool grid[CELLS];
		if (!Fits(st.pieces, st.pending, pos, grid))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten element nie zmie\266ci si\352 w tym miejscu.");
			return;
		}
		TPiece p;
		p.shape = st.pending;
		p.pos = (BYTE)pos;
		st.pieces.push_back(p);
		st.pending = 0;
		bool full = true;
		for (int i = 0; i < CELLS; ++i)
			if (!grid[i])
				full = false;
		if (!full)
		{
			Save(ch->GetPlayerID(), st);
			return;
		}
		// the board is full: the reward, then an empty board (saved first - a crash after it pays nothing twice)
		const int uses = st.uses;
		const DWORD reward = RewardFor(uses);
		st.pieces.clear();
		st.uses = 0;
		++st.completed;
		Save(ch->GetPlayerID(), st);
		ch->PointChange(POINT_EXP, REWARD_EXP, true);
		LPITEM item = ch->AutoGiveItem(reward, 1);
		LogManager::instance().ItemLog(ch, item ? item->GetID() : 0, reward, "FISH_PUZZLE_REWARD", std::to_string(uses).c_str());
		sys_log(0, "FISH_PUZZLE: %s (%u) finished the board in %d attempt(s), reward %u", ch->GetName(), ch->GetPlayerID(), uses, reward);
		ch->ChatPacket(CHAT_TYPE_INFO, "Puzzle u\263o\277one w %d pr\363bach! Otrzymujesz %d PD i nagrod\352.", uses, (int)REWARD_EXP);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "FP done %d %u", uses, reward);
	}
}

// "/fishpuzzle ..." (cmd.cpp, server-patches/fishpuzzle)
void Mt2009FishPuzzleCommand(LPCHARACTER ch, const char* argument)
{
	using namespace fishpuzzle;
	if (!Playable(ch))
		return;
	const DWORD now = get_dword_time();
	DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
	if (last && now - last < (DWORD)COMMAND_GAP_MS)
		return;
	last = now;

	char sub[32] = { 0 }, arg[32] = { 0 };
	two_arguments(argument, sub, sizeof(sub), arg, sizeof(arg));
	TState st;
	Load(ch->GetPlayerID(), st);
	if (!*sub || !strcmp(sub, "open"))
	{
		SendState(ch, st);
		return;
	}
	if (!strcmp(sub, "box"))
	{
		int kind = 1;
		str_to_number(kind, arg);
		Box(ch, st, kind == 2 ? 2 : 1);
	}
	else if (!strcmp(sub, "place"))
	{
		int pos = -1;
		if (!*arg || !str_to_number(pos, arg))
			return;
		Place(ch, st, pos);
	}
	else if (!strcmp(sub, "discard"))
	{
		if (!st.pending)
			return;
		st.pending = 0;
		Save(ch->GetPlayerID(), st);
	}
	else
		return;
	SendState(ch, st);
}

// UseItemEx (char_item.cpp): a puzzle box used from the inventory opens the window (nothing is used up);
// -1 = not a puzzle box, 0 = refused, 1 = done.
int Mt2009FishPuzzleUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace fishpuzzle;
	if (!ch || !item || (item->GetVnum() != BOX_NORMAL && item->GetVnum() != BOX_DELUXE))
		return -1;
	if (!Playable(ch))
		return 0;
	TState st;
	Load(ch->GetPlayerID(), st);
	SendState(ch, st);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "FP open");
	return 1;
}

// fishing::ProcessFishingGameSuccess (fishing.cpp): a catch during the event may bring a puzzle box.
void Mt2009FishPuzzleOnCatch(LPCHARACTER ch)
{
	using namespace fishpuzzle;
	if (!Playable(ch) || !EventOn())
		return;
	quest::CQuestManager& q = quest::CQuestManager::instance();
	const bool mind = ch->GetPremiumRemainSeconds(PREMIUM_FISH_MIND) > 0 || ch->IsEquipUniqueGroup(UNIQUE_GROUP_FISH_MIND);
	int chance = q.GetEventFlag("fish_puzzle_chance");
	if (chance <= 0)
		chance = 300;
	int deluxe = q.GetEventFlag("fish_puzzle_deluxe");
	if (deluxe <= 0)
		deluxe = 20;
	DWORD vnum = 0;
	if (mind && number(1, 1000) <= deluxe)
		vnum = BOX_DELUXE;
	else if (mind || number(1, 1000) <= chance)
		vnum = BOX_NORMAL;
	if (!vnum)
		return;
	ch->AutoGiveItem(vnum, 1);
}
