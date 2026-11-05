// MT2009_PLUS_FARM_SESSION_V1 - Sesja farmienia (server-patches/sesja/README.md). Port of Digi Rasta's package
// p-sesja-farmienia (marker DR_FARM_SESSION_V1, kept below): the server's part of the "Sesja farmienia" window
// (uifarmsession.py, the Y key). One session per human player: a counter of the time spent in the game (paused on
// logout, on a change of channel or core), of the experience, the yang, the items and the kills of monsters, Metin
// stones and bosses. The state is kept in dr_farm_session.cpp (a map by player id) and in the tables
// player.dr_farm_* (AccountDB, made by the core at its start); CHARACTER and ITEM are untouched.
//
// The whole content is under #ifdef DR_FARM_SESSION_V1 (CommonDefines.h, the patch's define), so a build without the
// patch compiles the overlay away. Not self-contained: stdafx.h (and so <vector>, typedef.h) comes first.

#pragma once
#include "../../common/CommonDefines.h"

#ifdef DR_FARM_SESSION_V1

// The number of sessions that are running on this core (paused and ended ones
// do not count). Every hook on a hot path starts with "if (!g_iDrFarmActive)".
extern int g_iDrFarmActive;

// "/sesja start <sec>|pauza|wznow|koniec|stan|pelne|historia|stat" (cmd_general.cpp, do_sesja).
void DrFarmCommand(LPCHARACTER ch, const char* argument);
// The character has entered the game (input_login.cpp, humans only): the open
// session of the player is read from the table.
void DrFarmOnEnterGame(LPCHARACTER ch);
// The character leaves this core (CHARACTER::Disconnect: logout, change of
// channel or core): the time stops, the session is written with DirectQuery.
void DrFarmOnDisconnect(LPCHARACTER ch);
// At the core's start (main.cpp): the tables are made.
void DrFarmInit();
// A real player: not a bot - neither a bot's descriptor (DESC::IsBot) nor a registered bot's player id
// (CPlayerBotManager::IsRegisteredBotPID, as the weekly ranking tells them).
bool DrFarmIsHuman(LPCHARACTER ch);

// The source of a kill, an item, yang: 0 monsters, 1 Metin stones (IsStone),
// 2 bosses (MOB_RANK_BOSS and up, or IsMiniBoss) - the order of the stat_*
// counters in CHARACTER::Reward.
BYTE DrFarmSourceOf(LPCHARACTER victim);

// The last kill DrFarmOnKill saw (g_iDrFarmActive set): the drop and yang
// hooks later in the same CHARACTER::Reward read it by the victim's VID.
enum { DR_FARM_KILL_PIDS = 8 };
struct TDrFarmKillCtx
{
	DWORD victimVid;
	BYTE src;			// DrFarmSourceOf
	DWORD mobVnum;
	long mapIdx;		// an instance's index is its map's (idx / 10000)
	BYTE count;			// pids used
	DWORD pids[DR_FARM_KILL_PIDS];	// humans with a running session, the killer first
};

// A monster's death (CHARACTER::Reward, after KillLog): a kill for every human
// with a running session among the killer (a companion's kill is its owner's),
// the killer's party near the corpse and those who hurt it near the corpse.
void DrFarmOnKill(LPCHARACTER victim, LPCHARACTER killer, const std::vector<LPCHARACTER>& hurt);
// The experience GiveExp gave (ENABLE_NEWEXP_CALCULATION, after PointChange).
void DrFarmOnExp(LPCHARACTER to, int iExp);
// NULL when the last kill is another victim's or counted nobody.
const TDrFarmKillCtx* DrFarmLastKill(DWORD dwVictimVID);

// The drop and the yang of a kill count when they reach a bag: an item on the
// ground carries a tag (by its VID: the yang has no ID) with the kill's source,
// map and the pids that may count it; the pick-up counts it for the receiver
// when the receiver is one of them and its session runs. A tag lives 330 s.
// What a kill hands over at once (GiveGold, AutoGiveItem) counts inside a
// DrFarmKillScope. Every function is a no-op while g_iDrFarmActive is 0.

// After CreateDropItem (CHARACTER::Reward): the items of the kill's drop.
void DrFarmTagDrops(LPCHARACTER victim, LPCHARACTER killer, const std::vector<LPITEM>& items);
// A boss's yang laid on the ground (CHARACTER::RewardGold): counted at its pick-up only.
void DrFarmTagGroundYang(LPITEM item, LPCHARACTER victim, LPCHARACTER killer);
// CItem::SetOwnership: the owner may count a tagged item too; an untagged item
// owned inside a DrFarmKillScope (a card, a rank fruit, a rune of the kill) gets
// the scope's tag.
void DrFarmTagOwner(DWORD dwItemVID, DWORD dwPID);

// CHARACTER::PickupItem: read before the item moves (AutoStackItem may destroy it).
struct TDrFarmPick
{
	DWORD vid, vnum, count;
	bool tagged;
};
TDrFarmPick DrFarmPickBegin(LPITEM item);
// The item is in the receiver's bag: counted when the receiver may count it;
// the tag goes either way.
void DrFarmPickDone(const TDrFarmPick& pick, LPCHARACTER receiver);

// The kill (or the picked-up yang's tag) whose yang and items DrFarmOnYang and
// DrFarmOnAutoGive count while it lives. Nested scopes stack; inert while
// g_iDrFarmActive is 0.
struct DrFarmKillScope
{
	DrFarmKillScope(LPCHARACTER victim, LPCHARACTER killer);
	explicit DrFarmKillScope(const TDrFarmPick& pick);
	~DrFarmKillScope();
	DrFarmKillScope(const DrFarmKillScope&) = delete;
	DrFarmKillScope& operator=(const DrFarmKillScope&) = delete;
private:
	bool m_bPushed;
};

// Yang that reached ch's purse (GiveGold: its own share, the party's shares).
void DrFarmOnYang(LPCHARACTER ch, long long llAmount);
// An item AutoGiveItem put into ch's bag.
void DrFarmOnAutoGive(LPCHARACTER ch, DWORD dwVnum, DWORD dwCount);
// The category of an item (item_proto's type): 0 materials, 1 usable, 2 weapons,
// 3 armour, 4 jewellery, 5 other.
BYTE DrFarmCategoryOf(DWORD vnum);

#endif // DR_FARM_SESSION_V1
