#ifndef __INC_METIN2_PLAYERBOT_ZODIAC_BOTS_H__
#define __INC_METIN2_PLAYERBOT_ZODIAC_BOTS_H__

// MT2009_PLUS_ZODIAC_BOTS_V1 - a person's party bots in the Swiatynia Zodiaku
// (MT2009_PLUS_ZODIAC_V1, server-patches/zodiak; Autor: Digi Rasta).
//
// The temple is not a CDungeon: its floors are private copies of 358
// (3580000-3589999) owned by a CZodiac (playerbot_zodiac_temple.h), whose
// member count ends the temple when the last character is out. So a bot:
//
//   - is a member of the temple whose floor it stands on, and of no other -
//     CPlayerBotManager::WarpBot calls SyncPlayerBotZodiac after every map
//     change it makes (the temple's own JumpParty and JoinParty warp the
//     party's bots that way, and the party dungeon pass puts a bot after its
//     person by it); a person gets that from input_login.cpp's hook;
//   - goes in after its person like into any party dungeon
//     (playerbot_party_dungeon.h: 358 is one of IsPlayerBotPartyDungeonMap's
//     maps, the instance is let through when the temple exists), fights
//     beside the person and leaves with the person;
//   - leaves the statues (20452-20463) and the cannon (20464) to the person:
//     a statue takes 1 point a blow and the cannon fires on its own when hit -
//     a bot hits them only when the person does;
//   - stands up where it fell with the temple's Prisms (33025, 33032) it
//     carries, the person's price (do_revive on itself: 1, 2, 4, 8, 10 by the
//     deaths); a bot without enough of them stands up for free - restart_here
//     would only send it the temple's revive window, which a bot never answers,
//     and leave it lying for good. The temple's death flags are cleared once
//     the bot is out. MT2009_PLUS_SIDEKICK_ZODIAC_V1: except a person's own
//     Towarzysz while the person stands on its floor - it keeps the temple's
//     rule and waits for Prisms (HoldPlayerBotSidekickInZodiac,
//     playerbot_sidekick.h); every map change of a bot (TransitionPlayerBotMap,
//     PlacePlayerBotSidekickAt) syncs its temple now, not WarpBot's alone.
//   - the person's Anima Spheres pay the entry: the quest zodiac_temples does
//     not count a bot of the party (pc.is_playerbot()).
//
// The bots' own temple runs are not here (see server-patches/zodiak/README.md,
// "Boty").

#ifdef ENABLE_12ZI
#include "playerbot_zodiac_temple.h"
#endif

namespace
{
	const long PLAYERBOT_ZODIAC_MAP = 358;
	const long PLAYERBOT_ZODIAC_INSTANCE_MIN = 3580000;
	const long PLAYERBOT_ZODIAC_INSTANCE_MAX = 3589999;
	const DWORD PLAYERBOT_ZODIAC_PRISM = 33025;
	const DWORD PLAYERBOT_ZODIAC_PRISM_AWAKENING = 33032;
	unsigned int s_uPlayerBotZodiacFreeRevives = 0;
	// MT2009_PLUS_ZODIAC_RUNS_V1: the bots' own runs count their deaths (playerbot_zodiac_runs.h, later).
	void NotePlayerBotZodiacRunRevive(DWORD pid, bool prisms);
	unsigned int s_uPlayerBotZodiacPrismRevives = 0;

	bool IsPlayerBotZodiacInstance(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_ZODIAC_INSTANCE_MIN && mapIndex <= PLAYERBOT_ZODIAC_INSTANCE_MAX;
	}

	// The temple's statues and its cannon: the person's to hit.
	bool IsPlayerBotZodiacLeftToPerson(DWORD race)
	{
		return race >= 20452 && race <= 20464;
	}

	// A temple floor that exists now (the instance is the CZodiac's).
	bool IsPlayerBotZodiacLive(long mapIndex)
	{
#ifdef ENABLE_12ZI
		return IsPlayerBotZodiacInstance(mapIndex) && CZodiacManager::instance().FindByMapIndex(mapIndex) != NULL;
#else
		(void)mapIndex;
		return false;
#endif
	}

	// MT2009_PLUS_ZODIAC_PETRIFY_END_V1: the temple's petrification - a boss's
	// skill turns a character in its reach into its statue (20452-20463) or
	// the dog (101) by SetPolymorph(race, false) (playerbot_zodiac_battle.cpp,
	// FPolyMonster in playerbot_zodiac_temple.cpp). There is no affect and no
	// timer behind it: a person is freed by another person's click on the
	// floor (char.cpp OnClick, MT2009_PLUS_ZODIAC_V1 (17)) or by the warp out,
	// which loads the person anew. A bot is never loaded anew and nobody
	// clicks it, so a bot hit once stayed the statue for good: the supporters'
	// server, 15 October, V3rt1's Towarzysz (pid 1498) petrified by the Wei
	// boss on 3580000 at 10:14:26 walked after its owner as the Wei statue on
	// every map, for everybody to see ("polymorph ended with the owner's ...
	// still=1": RemoveAffect(AFFECT_POLYMORPH) has nothing to remove). Now a
	// bot's petrification ends off the temple's floors at once, and on a
	// floor after PLAYERBOT_ZODIAC_PETRIFY_MS.
	const DWORD PLAYERBOT_ZODIAC_PETRIFY_MS = 10000;
	std::map<DWORD, DWORD> s_mapPlayerBotZodiacPetrified;

	// The temple's shape: a statue or the dog, with no polymorph affect of a
	// marble or a quest under it.
	bool IsPlayerBotZodiacPetrified(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPolymorphed())
			return false;
		const DWORD race = ch->GetPolymorphVnum();
		if (!((race >= 20452 && race <= 20463) || race == 101))
			return false;
		return ch->FindAffect(AFFECT_POLYMORPH) == NULL;
	}

	void EndPlayerBotZodiacPetrify(LPCHARACTER ch, long mapIndex, const char* why)
	{
		const DWORD race = ch->GetPolymorphVnum();
		s_mapPlayerBotZodiacPetrified.erase(ch->GetPlayerID());
		ch->SetPolymorph(0);
		sys_log(0, "PLAYERBOT_ZODIAC: petrification ended pid=%u name=%s race=%u map=%ld why=%s still=%d",
				ch->GetPlayerID(), ch->GetName(), race, mapIndex, why, ch->IsPolymorphed() ? 1 : 0);
	}

	// Every tick of a bot in the game.
	void ManagePlayerBotZodiacPetrify(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		if (!IsPlayerBotZodiacPetrified(ch))
		{
			if (!s_mapPlayerBotZodiacPetrified.empty())
				s_mapPlayerBotZodiacPetrified.erase(ch->GetPlayerID());
			return;
		}
		if (!IsPlayerBotZodiacInstance(ch->GetMapIndex()))
		{
			EndPlayerBotZodiacPetrify(ch, ch->GetMapIndex(), "outside");
			return;
		}
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotZodiacPetrified.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotZodiacPetrified.end())
		{
			s_mapPlayerBotZodiacPetrified[ch->GetPlayerID()] = dwNow;
			return;
		}
		if (!ch->IsDead() && dwNow - it->second >= PLAYERBOT_ZODIAC_PETRIFY_MS)
			EndPlayerBotZodiacPetrify(ch, ch->GetMapIndex(), "time");
	}

	// After a map change the bot's temple is the one of the floor it stands
	// on; out of the temple its death count and flags go.
	void SyncPlayerBotZodiac(LPCHARACTER bot, long mapIndex)
	{
#ifdef ENABLE_12ZI
		if (!bot)
			return;
		// MT2009_PLUS_ZODIAC_PETRIFY_END_V1: off the temple's floors as itself.
		if (!IsPlayerBotZodiacInstance(mapIndex) && IsPlayerBotZodiacPetrified(bot))
			EndPlayerBotZodiacPetrify(bot, mapIndex, "warp");
		LPZODIAC want = IsPlayerBotZodiacInstance(mapIndex) ? CZodiacManager::instance().FindByMapIndex(mapIndex) : NULL;
		LPZODIAC had = bot->GetZodiac();
		if (had != want)
		{
			if (had)
				bot->SetZodiac(NULL);
			if (want)
				bot->SetZodiac(want);
			sys_log(0, "PLAYERBOT_ZODIAC: member pid=%u name=%s map=%ld temple=%s",
					bot->GetPlayerID(), bot->GetName(), mapIndex, want ? "in" : "out");
		}
		if (!want)
		{
			bot->SetDeadCount(0);
			if (bot->GetQuestFlag("12zi_temple.IsDead") != 0)
				bot->SetQuestFlag("12zi_temple.IsDead", 0);
			if (bot->GetQuestFlag("12zi_temple.PrismNeed") != 0)
				bot->SetQuestFlag("12zi_temple.PrismNeed", 0);
		}
#else
		(void)bot;
		(void)mapIndex;
#endif
	}

	// MT2009_PLUS_SIDEKICK_ZODIAC_V1: the temple's death count and flags of a
	// bot that stands outside every temple floor - one taken off a floor some
	// other way than a warp of this core's (the floor closed under it and the
	// bot loaded anew on 358, an old one from before this was kept) still had
	// "12zi_temple.IsDead" and "PrismNeed", and on its next floor the temple
	// asked it for the Prisms of the deaths before. Membership is not touched
	// here: SyncPlayerBotZodiac is the only one that sets it.
	void ClearPlayerBotZodiacFlagsOutside(LPCHARACTER bot)
	{
#ifdef ENABLE_12ZI
		if (!bot || IsPlayerBotZodiacInstance(bot->GetMapIndex()))
			return;
		if (bot->GetDeadCount() != 0)
			bot->SetDeadCount(0);
		if (bot->GetQuestFlag("12zi_temple.IsDead") != 0)
			bot->SetQuestFlag("12zi_temple.IsDead", 0);
		if (bot->GetQuestFlag("12zi_temple.PrismNeed") != 0)
			bot->SetQuestFlag("12zi_temple.PrismNeed", 0);
#else
		(void)bot;
#endif
	}

	// The Prisms the temple asks of a revive after the bot's deaths there:
	// 1, 2, 4, 8, then 10 (cmd_general.cpp's restart hook, do_revive).
	int GetPlayerBotZodiacPrismNeed(LPCHARACTER ch)
	{
#ifdef ENABLE_12ZI
		const int n = std::max<int>(ch->GetQuestFlag("12zi_temple.PrismNeed"), (int)ch->GetDeadCount());
		if (n <= 2)
			return std::max(1, n);
		if (n == 3)
			return 4;
		if (n == 4)
			return 8;
		return 10;
#else
		(void)ch;
		return 0;
#endif
	}

	// HandleDeath (playerbot_survival.h): true when the bot lies on a temple
	// floor - it stood up here (prisms or not), restart_here is not for it.
	bool RevivePlayerBotInZodiac(LPCHARACTER ch)
	{
#ifdef ENABLE_12ZI
		if (!ch || !ch->IsDead() || !IsPlayerBotZodiacInstance(ch->GetMapIndex()))
			return false;
		const int need = GetPlayerBotZodiacPrismNeed(ch);
		const int have = (int)(ch->CountSpecifyItem(PLAYERBOT_ZODIAC_PRISM) + ch->CountSpecifyItem(PLAYERBOT_ZODIAC_PRISM_AWAKENING));
		if (have >= need)
		{
			char cmd[64];
			snprintf(cmd, sizeof(cmd), "revive %u", (unsigned int)ch->GetVID());
			interpret_command(ch, cmd, strlen(cmd));
			if (!ch->IsDead())
			{
				NotePlayerBotZodiacRunRevive(ch->GetPlayerID(), true);
				++s_uPlayerBotZodiacPrismRevives;
				sys_log(0, "PLAYERBOT_ZODIAC: revived pid=%u name=%s map=%ld prisms=%d left=%d deaths=%u total=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), need, have - need,
						(unsigned int)ch->GetDeadCount(), s_uPlayerBotZodiacPrismRevives);
				return true;
			}
		}
		// No prisms (or the revive refused): the bot's own stand-up, as
		// restart_here does it anywhere else.
		ch->ChatPacket(CHAT_TYPE_COMMAND, "CloseRestartWindow");
		ch->SetPosition(POS_STANDING);
		ch->StartRecoveryEvent();
		ch->RestartAtSamePos();
		ch->PointChange(POINT_HP, 50 - ch->GetHP());
		ch->ReviveInvisible(5);
		ch->SetQuestFlag("12zi_temple.IsDead", 0);
		++s_uPlayerBotZodiacFreeRevives;
		NotePlayerBotZodiacRunRevive(ch->GetPlayerID(), false);
		sys_log(0, "PLAYERBOT_ZODIAC: stood up pid=%u name=%s map=%ld prisms_needed=%d had=%d deaths=%u total=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), need, have, (unsigned int)ch->GetDeadCount(),
				s_uPlayerBotZodiacFreeRevives);
		return true;
#else
		(void)ch;
		return false;
#endif
	}
}

#endif
