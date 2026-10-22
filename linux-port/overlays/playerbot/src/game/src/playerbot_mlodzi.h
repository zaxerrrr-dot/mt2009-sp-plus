// MT2009_PLUS_MLODZI_BOHATEROWIE_V1: Bronie dla Mlodych Bohaterow (Weapons for Young Heroes; the owner,
// 22 October 2026, the pl-wiki page of that name). At level 1, 10, 20 ... 70 a character may take ONE weapon of its
// class from the current tier (Wojownik: miecz / bron dwureczna, Ninja: miecz / sztylet / luk, Sura: miecz,
// Szaman: dzwon / wachlarz; no Lycan here). Only the tier of the character's level is offered: a tier skipped is gone
// (took 10, skipped 20, reached 30 -> only the 30 weapon). The weapons are the official vnums 21900-21975
// (21900 + 10 * (tier - 1) + kind, kind 0 sword, 1 dagger, 2 bow, 3 two-handed, 4 bell, 5 fan; the claws x6 are
// left out), item_proto rows of mariadb/playerbot/mlodzi_bohaterowie.sql (tools/mlodzi/gen_mlodzi.py): no trade /
// drop / sale / shop / storage (antiflags), no refine (refined_vnum 0), no sockets (socket_pct 0), no random bonus
// (magic_pct 0), LIMIT_REAL_TIME 1296000 (15 days from the grant, also while worn - the engine's
// real_time_expire_event removes it). The average damage (+10 .. +30 %, the wiki) is the item's attribute 0, set
// here at the grant. Bonus changes, 6/7 bonuses, the switchbot, transmutation, sash absorption etc. refuse these
// weapons (MlodziRefuseChange, server-patches/mlodzi).
//
// One rule for players (quest mlodzi_bohaterowie: the letter, the client's window, "/mlodzi_wybor") and bots
// (playerbot_*): CurrentOffer / Claim below. Per-character quest flags mlodzi_bohaterowie.claimed (the last tier
// taken, 0 none) and mlodzi_bohaterowie.seen (the highest tier the character has reached). Off with .env
// M2_MLODZI_BOHATEROWIE=0 (apply.sh writes the event flag m2_mlodzi_off): no letter, no grant; weapons already
// given keep their own 15 days.
#ifndef MT2009_PLAYERBOT_MLODZI_H
#define MT2009_PLAYERBOT_MLODZI_H

class CHARACTER;
class CItem;

namespace mlodzi
{
	enum
	{
		LIFE_SECONDS = 15 * 24 * 60 * 60,	// 1296000 - the item_proto's LIMIT_REAL_TIME
		TIER_COUNT = 8,				// levels 1, 10, 20, 30, 40, 50, 60, 70
		FIRST_VNUM = 21900,
		LAST_VNUM = 21975,
		MAX_CHOICES = 3,
		// the weapon kinds (vnum % 10)
		KIND_SWORD = 0, KIND_DAGGER = 1, KIND_BOW = 2, KIND_TWO_HANDED = 3, KIND_BELL = 4, KIND_FAN = 5,
	};

	// Claim() results
	enum EClaim
	{
		CLAIM_OK = 0,
		CLAIM_NOT_OFFERED = 1,	// no offer now, another tier, or this tier was taken
		CLAIM_BAD_CHOICE = 2,	// not a weapon of the character's class
		CLAIM_NO_SPACE = 3,	// no free inventory cells for the weapon (nothing is used up)
		CLAIM_BAD_PROTO = 4,	// the item_proto row is missing or not a young heroes' weapon
		CLAIM_FAILED = 5,	// the item could not be made / put into the inventory
		CLAIM_BUSY = 6,		// trade, shop, storage or refine window open
		CLAIM_DISABLED = 7,	// M2_MLODZI_BOHATEROWIE=0
	};

	bool Enabled();					// event flag m2_mlodzi_off is 0
	bool IsWeaponVnum(unsigned int vnum);		// 21900-21975 with kind 0-5
	bool IsWeapon(const CItem* item);
	int TierForLevel(int level);			// 1 (level 1-9), 2 (10-19) ... 8 (70+); 0 below 1
	int TierLevel(int tier);			// 1, 10, 20 ... 70
	int TierOfVnum(unsigned int vnum);		// 1-8, 0 for another item
	int AverageDamage(int tier);			// 10, 13, 16 ... 28, 30 (the wiki)
	int ChoiceCount(int job);			// 2 warrior, 3 ninja, 1 sura, 2 shaman, 0 other
	int ChoiceKind(int job, int choice);		// the weapon kind of a choice (1-based), -1 none
	unsigned int WeaponVnum(int tier, int job, int choice);	// 0 when not valid
	int CurrentOffer(CHARACTER* ch);		// the tier the character may take now, 0 none (also 0 when off)
	int Claim(CHARACTER* ch, int tier, int choice, unsigned int* awardedVnum);	// EClaim; logs MLODZI_GRANT
	long SecondsLeft(const CItem* item);		// until the weapon disappears (socket0 - now), 0 for another item
}

// Free functions for the engine edits of server-patches/mlodzi (declared there inline, no header needed):
//   true (and one chat line to ch, when given) when item is a young heroes' weapon - the caller refuses the change.
bool MlodziIsWeaponVnum(unsigned int vnum);
bool MlodziRefuseChange(CHARACTER* ch, CItem* item);

#endif
