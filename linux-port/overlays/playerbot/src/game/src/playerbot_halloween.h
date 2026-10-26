// MT2009 PLUS Halloween event - MT2009_PLUS_HALLOWEEN_V1
// (the owner, 26 October: the Halloween event live for 31 October; Autor:
// Owsap - event_halloween_hair.quest, v6.2.6, the 2011-2014 "Halloween Hair").
//
// One switch, the in-game event manager's event "halloween"
// (playerbot_ingame_events.h): the panels' scheduler kind "halloween", or by
// hand the event flag halloween_hair (/eventflag halloween_hair 1 and 0), or -
// only when the operator asks for it - the calendar window below. While it is
// on, together:
//  - Jack Pumpkin (33008) stands in Yongan, Joan and Pyungmoo on Owsap's cells
//    (the manager's NPC spots) and trades a Jack O'Lantern Mask Card (30323)
//    for a Pumpkin Mask (quest/event_halloween_hair.quest); after a scheduled
//    run he stays the 7-day window halloween_hair_reward, with no drops;
//  - every monster and Metin stone a player kills may drop a Halloween
//    Pumpkin (30321), and every Metin stone a Magic Wand (30322) - the wand on
//    the pumpkin (the quest) makes a Halloween Chest (50215,
//    special_item_group.halloween.txt), where the Mask Card is.
//
// The drops follow this world's level rule for the rare drops (the Cor
// Draconis, the sash, the chest drop event): nothing from a mob more than 15
// levels below the killer ("z metinow do -15 poziomow postaci, czyli tak jak
// normalny drop"); a stronger one drops at the full chance. The chance is
// flat - no drop event, premium or glove raises it - and the drops are never
// doubled (they come after the double-loot events).
//
// The bots stay out: their kills drop neither, they never pick either up nor
// any other of the event's items (IsPlayerBotLeftOnGroundItem,
// playerbot_types.h), and they never talk to Jack Pumpkin.
//
// Live settings, event flags (0 / no row = the default; /eventflag or the panel):
//   m2_halloween_pumpkin   the pumpkin's chance a kill in hundredths of a percent
//                          (default 100 = 1 %, the stock halloween_drop's best)
//   m2_halloween_wand      the wand's chance a Metin in hundredths of a percent
//                          (default 1000 = 10 %, the owner's figure)
//   m2_halloween_auto      1 = the event also runs by itself every year from
//                          30 October 00:00 to 8 November 23:59 (server clock)
//
// An implementation fragment of playerbot_manager.cpp, after
// playerbot_ingame_events.h.

namespace mt2009_halloween
{
	const char* const EVENT_KEY = "halloween";
	const DWORD ITEM_PUMPKIN = 30321;	// Upiorna Dynia
	const DWORD ITEM_WAND = 30322;		// Czarodziejska Rozdzka
	// A kill counts when the killer is at most this many levels above the mob.
	const int LEVEL_GAP = 15;
	const int DEFAULT_PUMPKIN = 100;	// per 10 000 kills
	const int DEFAULT_WAND = 1000;		// per 10 000 Metin stones
	// The calendar window (m2_halloween_auto): from AUTO_START to AUTO_END,
	// both in October/November of the current year, the end exclusive.
	const int AUTO_START_MON = 9, AUTO_START_DAY = 30;	// 30 October
	const int AUTO_END_MON = 10, AUTO_END_DAY = 9;		// to 9 November 00:00

	int Chance(const char* flag, int fallback)
	{
		const int v = quest::CQuestManager::instance().GetEventFlag(flag);
		if (v <= 0)
			return fallback;
		return MIN(v, 10000);
	}

	bool Roll(int per10000)
	{
		return per10000 > 0 && number(1, 10000) <= per10000;
	}
}

bool HalloweenAutoWindow(long now, long& start, long& end)
{
	if (quest::CQuestManager::instance().GetEventFlag("m2_halloween_auto") <= 0)
		return false;
	time_t t = (time_t)now;
	struct tm local;
	localtime_r(&t, &local);
	struct tm a = tm();
	a.tm_year = local.tm_year;
	a.tm_mon = mt2009_halloween::AUTO_START_MON;
	a.tm_mday = mt2009_halloween::AUTO_START_DAY;
	a.tm_isdst = -1;
	struct tm b = a;
	b.tm_mon = mt2009_halloween::AUTO_END_MON;
	b.tm_mday = mt2009_halloween::AUTO_END_DAY;
	const long s = (long)mktime(&a);
	const long e = (long)mktime(&b);
	if (s <= 0 || e <= s || now < s || now >= e)
		return false;
	start = s;
	end = e;
	return true;
}

// Asked by Mt2009PlusChestDrops (playerbot_events.h), the engine's hook in
// CreateDropItem (item_manager.cpp), for every kill.
void Mt2009PlusHalloweenDrops(LPCHARACTER victim, LPCHARACTER killer, std::vector<LPITEM>& vec_item)
{
	using namespace mt2009_halloween;
	if (!victim || !killer || !killer->IsPC() || !killer->GetDesc() || killer->GetDesc()->IsBot())
		return;
	if (!(victim->IsMonster() || victim->IsStone()))
		return;
	if (!InGameEventIsActive(EVENT_KEY))
		return;
	if (killer->GetLevel() > victim->GetLevel() + LEVEL_GAP)
		return;
	if (victim->IsStone() && Roll(Chance("m2_halloween_wand", DEFAULT_WAND)))
	{
		if (LPITEM item = ITEM_MANAGER::instance().CreateItem(ITEM_WAND, 1, 0, true))
			vec_item.emplace_back(item);
	}
	if (Roll(Chance("m2_halloween_pumpkin", DEFAULT_PUMPKIN)))
	{
		if (LPITEM item = ITEM_MANAGER::instance().CreateItem(ITEM_PUMPKIN, 1, 0, true))
			vec_item.emplace_back(item);
	}
}
