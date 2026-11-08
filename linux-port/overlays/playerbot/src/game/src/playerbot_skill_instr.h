#ifndef __INC_METIN2_PLAYERBOT_SKILL_INSTR_H__
#define __INC_METIN2_PLAYERBOT_SKILL_INSTR_H__

// MT2009_PLUS_BOT_SKILL_INSTR_V1 - the bots and the skill INSTRUCTIONS (Instrukcje umiejetnosci; the owner, 8 November
// 2026). The early part: what an instruction is, the keep rule, the switches and the census counters - asked by the
// economy, the town and the counter (included before playerbot_economy.h). The ItemShop purchase, the chests and the
// census line are playerbot_skill_instr_late.h (after the V3 goals); the reading (Rada / Zwoj on the dearest skill) is
// ReadPlayerBotSkillBooksFocused in playerbot_manager.cpp, right before ManagePlayerBotSkillBooks.
//
// The items. An instruction is "Instr. <skill>" 50401-50511 (ITEM_SKILLBOOK, value0 = the skill's vnum: 50400 + the
// skill, e.g. 50404 Instr. Aura Miecza = skill 4) - one vnum a skill, never the Ksiega Umiejetnosci (KU) 50300 whose skill
// is socket 0. The engine reads both the same way (char_item.cpp ITEM_SKILLBOOK -> LearnSkillByBook: the same chances,
// the same wait between two reads of one skill, the same Zwoj Egzorcyzmu / Rada Pustelnika affects). Every path that
// takes a book's skill through GetPlayerBotSkillBookSkillVnum (value0 for every book but 50300) already sees an
// instruction as its skill's book: the stall's kind key (0x80000000 | skill), the asking price (GetPlayerBotBookAskingBase
// - the KU's sheet price for its skill, PLAYERBOT_BOOK_PRICES), the book pass. The warrior (1-5, 16-20), ninja (31-35,
// 46-50 + 51 Deszcz Strzal 50451), sura (61-66, 76-81) and shaman (91-96, 106-111) have them; the lycan has none.
//
// The keep rule (the owner's clarification, 8 November): an instruction of the bot's OWN skill is never surplus while
// that skill is under G1 (SKILL_GRAND_MASTER) - the bag keeps every one for reading, the counter / merchant / safebox
// take none; from G1 on it is surplus like a KU (keep 0 - GetPlayerBotBookKeepLimit), listed at its KU price. Another
// build's instruction is surplus at once (as another build's KU). The KU's own rule is unchanged (12 of a readable skill,
// 3 before it, 0 at G): the instructions of its skill that are kept whole are added to its keep, so the books of one
// skill counted together (CountPlayerBotSkillBooksAhead, CountPlayerBotStallKindUnits - KU and instructions alike) never
// make a KU look surplus because instructions stand in the bag.
//
// Switches (event flags, read once a second): m2_bot_skill_instr_off 1 - all of it (the bots as before);
// m2_bot_skill_instr_buy_off - no chest bought; m2_bot_skill_instr_focus_off - the old reading (a Rada on any class
// book, a Zwoj on the pass's best); m2_bot_skill_instr_keep_off - instructions surplus by the KU rule.
// The log: PLAYERBOT_SKILL_INSTR (throttled lines + the 10-minute census).

namespace
{
	const DWORD PLAYERBOT_SKILL_INSTR_FIRST = 50401;
	const DWORD PLAYERBOT_SKILL_INSTR_LAST = 50511;
	// "every one of them": the keep of an own skill's instruction under G1 (the bag holds no more than this anyway)
	const int PLAYERBOT_SKILL_INSTR_KEEP_ALL = 100000;
	const DWORD PLAYERBOT_SKILL_INSTR_CENSUS_MS = 10 * 60 * 1000;

	enum EPlayerBotSkillInstrPart
	{
		SKILLINSTR_ALL = 0,
		SKILLINSTR_BUY,
		SKILLINSTR_FOCUS,
		SKILLINSTR_KEEP,
		SKILLINSTR_COUNT
	};

	bool IsPlayerBotSkillInstrOn(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[SKILLINSTR_COUNT] = { false, false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_skill_instr_off") != 0;
			s_abOff[SKILLINSTR_ALL] = all;
			s_abOff[SKILLINSTR_BUY] = all || q.GetEventFlag("m2_bot_skill_instr_buy_off") != 0;
			s_abOff[SKILLINSTR_FOCUS] = all || q.GetEventFlag("m2_bot_skill_instr_focus_off") != 0;
			s_abOff[SKILLINSTR_KEEP] = all || q.GetEventFlag("m2_bot_skill_instr_keep_off") != 0;
		}
		return part >= 0 && part < SKILLINSTR_COUNT && !s_abOff[part];
	}

	bool IsPlayerBotSkillInstructionVnum(DWORD vnum)
	{
		if (vnum < PLAYERBOT_SKILL_INSTR_FIRST || vnum > PLAYERBOT_SKILL_INSTR_LAST)
			return false;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto && proto->bType == ITEM_SKILLBOOK && proto->alValues[0] > 0;
	}

	bool IsPlayerBotSkillInstruction(LPITEM item)
	{
		return item && item->GetType() == ITEM_SKILLBOOK && item->GetVnum() >= PLAYERBOT_SKILL_INSTR_FIRST &&
				item->GetVnum() <= PLAYERBOT_SKILL_INSTR_LAST && item->GetValue(0) > 0;
	}

	bool IsPlayerBotOwnSkill(LPCHARACTER ch, DWORD skillVnum);	// playerbot_economy.h

	// An instruction the bag keeps whole: the bot's own skill, under G1.
	bool IsPlayerBotSkillInstrKeptWhole(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !IsPlayerBotSkillInstruction(item) || !IsPlayerBotSkillInstrOn(SKILLINSTR_KEEP))
			return false;
		const DWORD skill = (DWORD)item->GetValue(0);
		return ch->GetSkillGroup() != 0 && IsPlayerBotOwnSkill(ch, skill) &&
				ch->GetSkillMasterType(skill) < SKILL_GRAND_MASTER;
	}

	// The instructions of one own skill under G1 in the bag (what a KU's keep of that skill is raised by).
	int CountPlayerBotKeptSkillInstr(LPCHARACTER ch, DWORD skill)
	{
		if (!ch || skill == 0 || !IsPlayerBotSkillInstrOn(SKILLINSTR_KEEP) || ch->GetSkillGroup() == 0 ||
				ch->GetSkillMasterType(skill) >= SKILL_GRAND_MASTER || !IsPlayerBotOwnSkill(ch, skill))
			return 0;
		int n = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotSkillInstruction(item) && (DWORD)item->GetValue(0) == skill)
				n += std::max<int>(1, item->GetCount());
		}
		return n;
	}

	// The census (PLAYERBOT_SKILL_INSTR: census, every PLAYERBOT_SKILL_INSTR_CENSUS_MS).
	struct TPlayerBotSkillInstrCensus
	{
		std::set<DWORD> shortBots;	// bots seen with a skill at M1-M9 and no book of it
		std::set<DWORD> shortNoChest;	// ... of them, no instruction chest in the ItemShop for their skills
		unsigned int uGoals, uChestsBought, uChestPieces, uV3Chests, uPoolBlock, uListed, uListedUnits;
		unsigned int uRadaSpill;	// a Rada affect a non-focus read took (left on from before)
		std::map<DWORD, std::pair<unsigned int, unsigned int> > readBySkill;	// instructions read / landed
		std::map<DWORD, std::pair<unsigned int, unsigned int> > kuBySkill;	// KU read / landed (for comparison)
		std::map<DWORD, unsigned int> radaBySkill, zwojBySkill;
		std::map<DWORD, unsigned int> chestsByVnum;
		TPlayerBotSkillInstrCensus() : uGoals(0), uChestsBought(0), uChestPieces(0), uV3Chests(0), uPoolBlock(0),
				uListed(0), uListedUnits(0), uRadaSpill(0) {}
	};
	TPlayerBotSkillInstrCensus s_kPlayerBotSkillInstrCensus;
	DWORD s_dwPlayerBotSkillInstrCensusAt = 0;

	// The counter took a line of instructions (playerbot_offline_shop.h, at the add).
	void NotePlayerBotSkillInstrListed(DWORD vnum, int count)
	{
		if (!IsPlayerBotSkillInstructionVnum(vnum))
			return;
		++s_kPlayerBotSkillInstrCensus.uListed;
		s_kPlayerBotSkillInstrCensus.uListedUnits += (unsigned int)std::max(1, count);
	}
}

#endif
