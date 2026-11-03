// MT2009_PLUS_FISH_PUZZLE_V1 / V2 / V3 - Event Rybacki - Puzzle (Wedkarskie Puzzle; the owner,
// 3 November 2026; server-patches/fishpuzzle, README.md). The official event of version 17.3 (pl-wiki "Event Rybacki -
// Puzzle", "Minigra: Wedkarskie Puzzle", "Pudlo wedkarskich puzzli", "Zl. Skrzynia na Ryby (D)").
//
// V2 (the owner's package "Mini Game Fish Event (17.3)" - "Jigsaw FULL + Fix Scale", 3 November 2026: "fully like on
// the global server, with this package; if the exe is needed we do it in the exe"): the package's game and its real
// packets, in a new exe (client-patches/exe, ENABLE_FISH_EVENT). V1's chat command protocol ("/fishpuzzle open|box|
// place|discard", "FP state|piece|done") is retired; "/fishpuzzle" now only says hello.
//
//   CG 219 HEADER_CG_FISH_EVENT_SEND  { BYTE header; BYTE sub; } + by sub, then the sequence byte:
//          0 BOX_USE    + BYTE window, WORD cell     a box from the inventory opened in the window (one attempt)
//          1 SHAPE_ADD  + BYTE cell                  the piece in hand laid with its top-left corner on the cell
//   GC 223 HEADER_GC_FISH_EVENT_INFO  { BYTE header; BYTE sub; DWORD arg1; DWORD arg2; }   10 B
//          0 BOX_USE    shape, attempts               the piece to hold (also again after a refused place)
//          1 SHAPE_ADD  cell, shape                   a laid piece (and every piece of the board after ENABLE)
//          2 GC_REWARD  reward vnum, 0                the board is full: the reward came, the board is empty again
//          3 GC_ENABLE  event shown 0/1, attempts     the event banner; ENABLE is followed by the board's pieces
// The numbers are free in our server packet.h and our exe Packet.h (both have 216-218, 220, 226, 238 but not 219 or
// 223) and are the package's own. An exe without them stops at an unknown header, so a client gets GC 223 only after
// its python said "/fishpuzzle hello" (root uifishpuzzle.py, only when app.ENABLE_FISH_EVENT): an old client gets
// nothing of it - a box used from its inventory says the event needs the new client, its old chat commands the same.
//
// The rules are the package's (char.cpp FishEvent*, fishing.cpp) with the drop of the pl-wiki (MT2009_PLUS_FISH_PUZZLE_V3,
// the owner, 3 November 2026: "exactly as on the pl-wiki"): during the event a catch (the fishing game won - a fish,
// a dye, anything) brings 5 Pudel wedkarskich puzzli 25106 (event flag fish_puzzle_boxes) with a 30% chance
// (fish_puzzle_chance, per cent), with Rybie Wnetrznosci (the premium fish mind or the unique group 10009: 71008,
// 72013-72015 - the package asks UNIQUE_ITEM_FISH_MIND) always; with them a catch also has a 2% chance of one Luks.
// pudlo wedk. puzzli 25107 on top (fish_puzzle_deluxe, per mille, 20) - the wiki's "100% for the box and a chance of
// the deluxe one" (the package gave every catch 5 boxes and 10% of the fish-mind catches the deluxe box instead of
// them). A box opened in the window is one
// attempt and a random piece of shapes 1-6 (25106) or the 3 x 2 piece 7 (25107); the piece goes onto the 6 x 4 board
// where it fits (inside, no overlap - the package's own table let an L wrap round the board's right edge, here the
// cells are checked) or is thrown away in the client (right click; the server keeps it until the next box, as the
// package). The board full: +30 000 experience and by the attempts Zl. Skrzynia na Ryby (D) 83003 (10 or fewer), (S)
// 83002 (11-24) or (M) 83001 (25 or more) - the package's 25113 / 25112 / 25111 are GACHA chests without contents;
// GF 26.1.11's item_list has the three chests as 83001-83003 (icon 25111.tga), so those stay (ShipDefense_ChestKeep:
// opened 3 / 2 / 1 times, special_item_group.fishpuzzle.txt).
// Fixed against the package: the piece in hand is spent by the place (the package kept it - the same piece could be
// laid again and again), the box cell is read as a WORD (the package read one char), a place out of the board or of
// a client that said no hello is ignored.
//
// The board, the piece in hand and the attempts live in player.fish_puzzle (fish_puzzle.sql) - the package's
// player.fish_slots / fish_use_count columns (TPlayerTable, db ClientManagerPlayer) are not taken: the same state
// without a db core rebuild or a player table change. The piece in hand is gone at the next hello (a new game window
// after a login, warp or channel change has no piece on the mouse) - the package lost it at the logout.
//
// The event (planner kind "fishpuzzle" 19, event flag fish_puzzle_event, playerbot_ingame_events.h; or a GM's
// "/e enable_fish_event 1", the package's flag) gates the boxes found while fishing, the banner and the game: V3 (the
// pl-wiki: "when the event is off its items cannot be found, the banner and the window are off too") - no reward
// window after it any more (V1 kept the banner 7 days, fish_puzzle_reward); a box used or a piece laid while it is
// off is refused with a line, the board and its attempts wait for the next run. A change of that state sends ENABLE
// and the board again to every client that said hello (Mt2009FishEventTick, once a second). Bots never get a box
// (their catches are skipped) and cannot play.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "db.h"
#include "log.h"
#include "packet.h"
#include "questmanager.h"
#include "unique_item.h"
#include "utils.h"

#include <cstdio>
#include <cstring>
#include <ctime>
#include <map>
#include <memory>
#include <string>
#include <vector>

// playerbot_ingame_events.h (MT2009_PLUS_EVENT_MANAGER_V1)
bool InGameEventIsActive(const char* key);

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
		PACKET_GAP_MS = 100,
		DEFAULT_BOXES = 5,
		DEFAULT_CHANCE_PCT = 30,		// MT2009_PLUS_FISH_PUZZLE_V3: pl-wiki "5 boxes with a 30% chance"
		DEFAULT_DELUXE_PERMILLE = 20,	// MT2009_PLUS_FISH_PUZZLE_V3: pl-wiki "+2%" with Rybie Wnetrznosci
	};

	// The seven pieces, as GF's pictures fish_1..fish_7.sub draw them (fishingevnet001.dds, 32 px a cell) and the
	// package's tables (char.cpp positionList, uiMiniGameFishEvent.py positionInfo: 0,6,12 / 0 / 0,6,7 / 0,1,7 /
	// 0,1,6,7 / 0,1,7,8 / 0,1,2,6,7,8): the cells (dx, dy) of each from its top-left corner.
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

	std::map<DWORD, DWORD> s_mapHello;			// pid -> the desc handle that said hello (a new connection must say it again)
	std::map<DWORD, DWORD> s_mapLastPacket;		// pid -> get_dword_time() of the last box / place
	int s_iShown = -1;							// the banner state the hello'd clients were last told

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

	// The boxes are found while the event runs (the planner's flag or the package's own).
	bool EventOn()
	{
		quest::CQuestManager& q = quest::CQuestManager::instance();
		return q.GetEventFlag("fish_puzzle_event") > 0 || q.GetEventFlag("enable_fish_event") > 0;
	}

	// The banner and the game show while it runs - MT2009_PLUS_FISH_PUZZLE_V3: only then (pl-wiki), no reward window.
	bool EventShown()
	{
		return EventOn() || InGameEventIsActive("fishpuzzle");
	}

	// MT2009_PLUS_FISH_PUZZLE_V3: a box or a piece while the event is off - the window is off (pl-wiki).
	bool RefuseOff(LPCHARACTER ch)
	{
		if (EventShown())
			return false;
		ch->ChatPacket(CHAT_TYPE_INFO, "Event Rybacki - Puzzle nie trwa teraz - pude\263ka otworzysz podczas nast\352pnego eventu.");
		return true;
	}

	bool Playable(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot() && ch->GetDesc()->IsPhase(PHASE_GAME);
	}

	bool HasHello(LPCHARACTER ch)
	{
		if (!Playable(ch))
			return false;
		std::map<DWORD, DWORD>::const_iterator it = s_mapHello.find(ch->GetPlayerID());
		return it != s_mapHello.end() && it->second == ch->GetDesc()->GetHandle();
	}

	void SendInfo(LPCHARACTER ch, BYTE sub, DWORD arg1, DWORD arg2)
	{
		if (!HasHello(ch))
			return;
		TPacketGCFishEventInfo p;
		p.bHeader = HEADER_GC_FISH_EVENT_INFO;
		p.bSubheader = sub;
		p.dwFirstArg = arg1;
		p.dwSecondArg = arg2;
		ch->GetDesc()->Packet(&p, sizeof(p));
	}

	// The package's FishEventGeneralInfo: the banner and the attempts, then every laid piece.
	void SendGeneral(LPCHARACTER ch, const TState& st)
	{
		SendInfo(ch, FISH_EVENT_SUBHEADER_GC_ENABLE, EventShown() ? 1 : 0, (DWORD)st.uses);
		for (size_t i = 0; i < st.pieces.size(); ++i)
			SendInfo(ch, FISH_EVENT_SUBHEADER_SHAPE_ADD, st.pieces[i].pos, st.pieces[i].shape);
	}

	DWORD RewardFor(int uses)
	{
		if (uses <= 10)
			return CHEST_D;
		if (uses <= 24)
			return CHEST_S;
		return CHEST_M;
	}

	bool TooFast(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastPacket[ch->GetPlayerID()];
		if (last && now - last < (DWORD)PACKET_GAP_MS)
			return true;
		last = now;
		return false;
	}

	void Hello(LPCHARACTER ch)
	{
		s_mapHello[ch->GetPlayerID()] = ch->GetDesc()->GetHandle();
		TState st;
		Load(ch->GetPlayerID(), st);
		if (st.pending)
		{
			// a new game window holds no piece: the one held before is gone, as the package's at the logout
			st.pending = 0;
			Save(ch->GetPlayerID(), st);
		}
		SendGeneral(ch, st);
	}

	// The package's FishEventUseBox.
	void UseBox(LPCHARACTER ch, BYTE window, WORD cell)
	{
		if (window != INVENTORY || !ch->CanHandleItem() || RefuseOff(ch))
			return;
		const TItemPos pos(window, cell);
		LPITEM item;
		if (!ch->IsValidItemPosition(pos) || !(item = ch->GetItem(pos)) || item->IsExchanging())
			return;
		const DWORD vnum = item->GetVnum();
		if (vnum != BOX_NORMAL && vnum != BOX_DELUXE)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie mo\277esz tutaj u\277y\346 tego przedmiotu.");
			return;
		}
		TState st;
		Load(ch->GetPlayerID(), st);
		st.pending = vnum == BOX_DELUXE ? (BYTE)SHAPE_DELUXE : (BYTE)number(1, 6);
		++st.uses;
		item->SetCount(item->GetCount() - 1);
		Save(ch->GetPlayerID(), st);
		LogManager::instance().ItemLog(ch, 0, vnum, "FISH_PUZZLE_BOX", std::to_string((int)st.pending).c_str());
		SendInfo(ch, FISH_EVENT_SUBHEADER_BOX_USE, st.pending, (DWORD)st.uses);
	}

	// The package's FishEventAddShape / FishEventPlaceShape / FishEventCheckEnd.
	void AddShape(LPCHARACTER ch, BYTE cell)
	{
		TState st;
		Load(ch->GetPlayerID(), st);
		if (!st.pending || cell >= CELLS || RefuseOff(ch))
			return;
		bool grid[CELLS];
		if (!Fits(st.pieces, st.pending, cell, grid))
		{
			// the piece back on the mouse (the package's answer), it stays the one in hand
			SendInfo(ch, FISH_EVENT_SUBHEADER_BOX_USE, st.pending, (DWORD)st.uses);
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten element nie pasuje w tym miejscu.");
			return;
		}
		TPiece p;
		p.shape = st.pending;
		p.pos = cell;
		st.pieces.push_back(p);
		st.pending = 0;
		bool full = true;
		for (int i = 0; i < CELLS; ++i)
			if (!grid[i])
				full = false;
		if (!full)
		{
			Save(ch->GetPlayerID(), st);
			SendInfo(ch, FISH_EVENT_SUBHEADER_SHAPE_ADD, p.pos, p.shape);
			return;
		}
		// the board is full: the reward, then an empty board (saved first - a crash after it pays nothing twice)
		const int uses = st.uses;
		const DWORD reward = RewardFor(uses);
		st.pieces.clear();
		st.uses = 0;
		++st.completed;
		Save(ch->GetPlayerID(), st);
		SendInfo(ch, FISH_EVENT_SUBHEADER_SHAPE_ADD, p.pos, p.shape);
		LPITEM item = ch->AutoGiveItem(reward, 1);
		ch->PointChange(POINT_EXP, REWARD_EXP, true);
		LogManager::instance().ItemLog(ch, item ? item->GetID() : 0, reward, "FISH_PUZZLE_REWARD", std::to_string(uses).c_str());
		sys_log(0, "FISH_PUZZLE: %s (%u) finished the board in %d attempt(s), reward %u", ch->GetName(), ch->GetPlayerID(), uses, reward);
		SendInfo(ch, FISH_EVENT_SUBHEADER_GC_REWARD, reward, 0);
	}
}

// CG 219 (input_main.cpp, server-patches/fishpuzzle): the extra length after the 2-byte head, -1 = wait for more.
int Mt2009FishEventPacket(LPCHARACTER ch, const char* data, size_t uiBytes)
{
	using namespace fishpuzzle;
	if (uiBytes < sizeof(TPacketCGFishEvent))
		return -1;
	const TPacketCGFishEvent* p = reinterpret_cast<const TPacketCGFishEvent*>(data);
	const char* c_pData = data + sizeof(TPacketCGFishEvent);
	uiBytes -= sizeof(TPacketCGFishEvent);

	switch (p->bSubheader)
	{
		case FISH_EVENT_SUBHEADER_BOX_USE:
		{
			const size_t extra = sizeof(BYTE) + sizeof(WORD);
			if (uiBytes < extra)
				return -1;
			const BYTE window = (BYTE)c_pData[0];
			WORD cell = 0;
			memcpy(&cell, c_pData + 1, sizeof(WORD));
			if (ch && HasHello(ch) && !TooFast(ch))
			{
				sys_log(0, "INPUT: %s FISH_EVENT: USE_BOX %u %u", ch->GetName(), (unsigned int)window, (unsigned int)cell);
				UseBox(ch, window, cell);
			}
			return (int)extra;
		}

		case FISH_EVENT_SUBHEADER_SHAPE_ADD:
		{
			if (uiBytes < sizeof(BYTE))
				return -1;
			const BYTE cell = (BYTE)c_pData[0];
			if (ch && HasHello(ch) && !TooFast(ch))
			{
				sys_log(0, "INPUT: %s FISH_EVENT: ADD_SHAPE %u", ch->GetName(), (unsigned int)cell);
				AddShape(ch, cell);
			}
			return (int)sizeof(BYTE);
		}

		default:
			sys_err("FISH_EVENT: unknown subheader %u from %s", (unsigned int)p->bSubheader, ch ? ch->GetName() : "?");
			break;
	}
	return 0;
}

// "/fishpuzzle hello" (cmd.cpp, server-patches/fishpuzzle) from root uifishpuzzle.py - only a client whose exe has
// ENABLE_FISH_EVENT says it. V1's other commands come from an old client: it is told to update.
void Mt2009FishPuzzleCommand(LPCHARACTER ch, const char* argument)
{
	using namespace fishpuzzle;
	if (!Playable(ch))
		return;
	char sub[32] = { 0 };
	one_argument(argument, sub, sizeof(sub));
	if (!strcmp(sub, "hello"))
	{
		Hello(ch);
		return;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, "W\352dkarskie Puzzle wymagaj\261 nowej wersji klienta - zaktualizuj gr\352.");
}

// UseItemEx (char_item.cpp): a puzzle box used from the inventory opens the window ("FP open", root
// uifishpuzzle.py); nothing is used up - a box is opened in the window. -1 = not a puzzle box, 0 = refused, 1 = done.
int Mt2009FishPuzzleUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace fishpuzzle;
	if (!ch || !item || (item->GetVnum() != BOX_NORMAL && item->GetVnum() != BOX_DELUXE))
		return -1;
	if (!Playable(ch))
		return 0;
	if (!HasHello(ch))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "W\352dkarskie Puzzle wymagaj\261 nowej wersji klienta - zaktualizuj gr\352.");
		return 0;
	}
	if (RefuseOff(ch))
		return 0;
	ch->ChatPacket(CHAT_TYPE_COMMAND, "FP open");
	return 1;
}

// fishing::ProcessFishingGameSuccess (fishing.cpp): during the event a catch brings boxes. MT2009_PLUS_FISH_PUZZLE_V3
// (pl-wiki "Event Rybacki - Puzzle", "Pudlo wedkarskich puzzli", "Luks. pudlo wedk. puzzli", "Rybie Wnetrznosci"):
// 5 boxes with a 30% chance, always with Rybie Wnetrznosci, and with them a 2% chance of one deluxe box on top.
void Mt2009FishPuzzleOnCatch(LPCHARACTER ch)
{
	using namespace fishpuzzle;
	if (!Playable(ch) || !EventOn())
		return;
	quest::CQuestManager& q = quest::CQuestManager::instance();
	const bool mind = ch->GetPremiumRemainSeconds(PREMIUM_FISH_MIND) > 0 || ch->IsEquipUniqueGroup(UNIQUE_GROUP_FISH_MIND);
	int boxes = q.GetEventFlag("fish_puzzle_boxes");
	if (boxes <= 0)
		boxes = DEFAULT_BOXES;
	if (boxes > 200)
		boxes = 200;
	int chance = q.GetEventFlag("fish_puzzle_chance");
	if (chance <= 0)
		chance = DEFAULT_CHANCE_PCT;
	int deluxe = q.GetEventFlag("fish_puzzle_deluxe");
	if (deluxe <= 0)
		deluxe = DEFAULT_DELUXE_PERMILLE;
	if (mind || number(1, 100) <= chance)
		ch->AutoGiveItem(BOX_NORMAL, boxes);
	if (mind && number(1, 1000) <= deluxe)
		ch->AutoGiveItem(BOX_DELUXE, 1);
}

// InGameEventTick (playerbot_ingame_events.h), once a second: the banner on or off for every hello'd client when the
// event starts, ends or its reward window closes (ENABLE and the board, as at the hello).
void Mt2009FishEventTick()
{
	using namespace fishpuzzle;
	const int shown = EventShown() ? 1 : 0;
	if (shown == s_iShown)
		return;
	const bool first = s_iShown < 0;
	s_iShown = shown;
	for (std::map<DWORD, DWORD>::iterator it = s_mapHello.begin(); it != s_mapHello.end(); )
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
		if (!ch || !HasHello(ch))
		{
			s_mapLastPacket.erase(it->first);
			s_mapHello.erase(it++);
			continue;
		}
		if (!first)
		{
			TState st;
			Load(ch->GetPlayerID(), st);
			SendGeneral(ch, st);
		}
		++it;
	}
}

// MT2009_PLUS_FISH_PUZZLE_V1 (link): the catch hook in fishing.cpp declares the function at block scope inside
// namespace fishing, so the call binds to fishing::Mt2009FishPuzzleOnCatch - this forwards it to the one above.
namespace fishing
{
	void Mt2009FishPuzzleOnCatch(LPCHARACTER ch)
	{
		::Mt2009FishPuzzleOnCatch(ch);
	}
}
