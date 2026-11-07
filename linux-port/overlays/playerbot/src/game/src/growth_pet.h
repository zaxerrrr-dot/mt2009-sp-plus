#ifndef __INC_MT2009_GROWTH_PET_H__
#define __INC_MT2009_GROWTH_PET_H__

// MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych (server-patches/pety/README.md): the game's part.
// growth_pet.cpp keeps every pet this core knows (the pets of the seals and cages its characters hold), summons one
// pet a character, levels it from its owner's kills, and serves the pet window's packets (CG 122-134 / GC 224-236).
// The engine calls in through server-patches/pety (edits.json) and the old New Pet System's hooks
// (server-patches/playerqol: NewPetUseItem / NewPetOnExp / NewPetApplyPoints / do_newpet, now growth pet shims in
// playerbot_newpet.h). The bots use the functions of namespace growth_pet below (playerbot_newpet_bots.h).

#include "../../common/tables.h"

class CHARACTER;
class CItem;
class DESC;

namespace growth_pet
{
	// What the bots and the pricing read of a pet (a copy).
	struct PetView
	{
		DWORD id;
		DWORD vnum;			// the seal's vnum
		BYTE state;
		std::string name;
		int level;
		int evolution;		// 1..6
		int championLevel;
		int type;
		bool alive;
		long long lifeLeft;	// seconds
		long long lifeMax;
		int ageDays;
		unsigned long long exp, needExp, itemExp, needItemExp;	// the current stage's bars (champion values at 5/6)
		BYTE skill[GROWTH_PET_SKILL_SLOTS];
		BYTE skillLevel[GROWTH_PET_SKILL_SLOTS];
		bool skillLocked[GROWTH_PET_SKILL_SLOTS];
		bool summoned;
		int potentialOpen;	// MT2009_PLUS_BOT_PET_GROW_V1: the champion's open potential slots (0-2)
		bool potentialActive[GROWTH_PET_POTENTIAL_SLOTS];
	};

	// ---- queries ----
	bool IsSealVnum(DWORD vnum);
	bool IsEggVnum(DWORD vnum);
	DWORD SealOfEgg(DWORD egg);
	const char* SpeciesName(DWORD sealOrEgg);
	bool GetPet(DWORD id, PetView& out);
	DWORD GetSummonedPetId(CHARACTER* ch);
	void ListPets(CHARACTER* ch, std::vector<PetView>& out);	// the pets of the seals in ch's bags
	bool CanEvolve(DWORD id, CHARACTER* ch, int& toStage);	// level/age/exp met (not the materials)
	bool GetEvolutionMaterials(int toStage, std::vector<std::pair<DWORD, int> >& out);
	int EvolutionLevel(int toStage);	// MT2009_PLUS_BOT_PET_GROW_V1: the level (champion level for 6) the step asks
	unsigned long long NeedMobExp(int level);
	unsigned long long NeedItemExp(int level);

	// ---- acts (the window's code paths; a bot calls them for its own pets) ----
	bool Hatch(CHARACTER* ch, CItem* egg, const char* name);	// true: the seal is in ch's bag
	bool ToggleSummon(CHARACTER* ch, CItem* seal);
	bool FeedLife(CHARACTER* ch, CItem* odzywka, CItem* seal);	// Odzywka on a seal (also the 50 % revive)
	bool FeedLifeWithEgg(CHARACTER* ch, CItem* egg, CItem* seal);	// MT2009_PLUS_BOT_PET_FEED_V1: an egg into the life bar (+3-5%)
	bool FeedItemExp(CHARACTER* ch, CItem* item, int count);		// the summoned pet; weapons, armour, Smakolyk(+)
	bool UseTastyTreat(CHARACTER* ch, CItem* item);				// Smaczny Smakolyk (55042)
	bool Evolve(CHARACTER* ch);									// the summoned pet; the materials from the bags
	bool LearnSkill(CHARACTER* ch, int slot, CItem* book);
	bool UpgradeSkill(CHARACTER* ch, int slot);
	bool FillPotential(CHARACTER* ch, int slot, CItem* egg);		// MT2009_PLUS_BOT_PET_GROW_V1: an egg into a champion's potential slot

	// ---- engine hooks (edits.json / playerqol shims) ----
	int UseItem(CHARACTER* ch, CItem* item, TItemPos destCell);	// -1 not ours, 0 refused, 1 used
	void OnItemLoad(CHARACTER* ch);
	void OnSafeboxLoad(CHARACTER* ch);
	void OnItemAdd(CHARACTER* ch, CItem* item);
	void OnDestroy(CHARACTER* ch);
	void OnKillExp(CHARACTER* victim, CHARACTER* to, long long exp);
	void OnChampionExp(CHARACTER* victim, CHARACTER* to, unsigned long long exp);
	void OnSungmaKill(CHARACTER* victim, CHARACTER* killer);
	void OnOwnerExpLoss(CHARACTER* ch, long long loss, long long levelNeed);
	void ApplyPoints(CHARACTER* ch);
	void EncodeInsert(CHARACTER* pet, DESC* d);
	void OnExchangeItem(CHARACTER* from, CHARACTER* to, CItem* item);
	bool IsInvincible(CHARACTER* ch);
	int BlockPenetration(CHARACTER* attacker);
	bool IsGrowthPetChar(CHARACTER* ch);
	void Packet(CHARACTER* ch, BYTE header, const char* data);
	void DBPacket(DWORD dwHandle, BYTE header, const char* data);
	void Command(CHARACTER* ch, const char* argument);	// GM /pet_set (and /pet_set info [name])
}

#endif
