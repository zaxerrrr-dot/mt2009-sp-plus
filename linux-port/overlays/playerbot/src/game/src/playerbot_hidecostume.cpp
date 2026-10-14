// MT2009_PLUS_HIDE_COSTUME_V1: Ukryj kostium / fryzure / wizerunek broni / szarfe (Owsap v6.2.6
// __HIDE_COSTUME_SYSTEM__, Autor: Owsap) in place of our MT2009_PLUS_COSTUME_HIDE_V1/V2 (server-patches/playerqol).
// server-patches/ukryjkostium/README.md. New file outside the engine's own; the hooks are server-patches/ukryjkostium.
//
// Each part is hidden on its own, per character, saved in the quest flags Owsap uses (costume_option.hide_body,
// hide_hair, hide_acce, hide_weapon) - the old setting lived in the client's kostiumy.cfg, for every character of
// the computer. The costume stays worn and keeps its bonuses; only what the others (and the owner) see changes:
// the parts of the character's add / update packets (char.cpp, EncodeInsertPacket and UpdatePacket), not the
// character's own parts, so nothing else in the engine notices. Hidden costume -> the armour under it (its
// transmuted look, MT2009_PLUS_CHANGE_LOOK_V1) or the character's own body; hidden hairstyle -> the own hair;
// hidden weapon skin -> the weapon; hidden sash -> no sash.
//   client -> "/hide_costume_part <subtype> <0|1>" (Owsap's; COSTUME_BODY 0, HAIR 1, ACCE 3, WEAPON 4)
//   server -> "SetHiddenCostumePart <subtype> <0|1>" (after the login and after every change)
// Our "Ukryj cudze" (MT2009_PLUS_COSTUME_VIEW_OTHERS_V1, playerqol) stays as it was: it rewrites the parts for one
// viewer after these.
// Migration: the old client setting comes once, "/kostiumy_ukryj m <mask>" (1 costume, 2 hair, 4 weapon), the
// playerqol command; a character that never chose here takes it (costume_option.migrated).
#include "stdafx.h"
#include "constants.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "utils.h"
#include "cmd.h"
#include "packet.h"

#include <map>

#ifdef ENABLE_HIDE_COSTUME_SYSTEM

namespace hidecostume
{
	enum
	{
		HIDE_BODY = 1 << 0,
		HIDE_HAIR = 1 << 1,
		HIDE_WEAPON = 1 << 2,	// the same bits as the old kostiumy.cfg mask (1 costume, 2 hair, 4 weapon)
		HIDE_ACCE = 1 << 3,
	};

	struct TPart
	{
		BYTE bSubType;	// COSTUME_*
		BYTE bBit;
		const char* c_pszFlag;
	};

	const TPart s_aParts[] =
	{
		{ COSTUME_BODY,		HIDE_BODY,		"costume_option.hide_body" },
		{ COSTUME_HAIR,		HIDE_HAIR,		"costume_option.hide_hair" },
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		{ COSTUME_ACCE,		HIDE_ACCE,		"costume_option.hide_acce" },
#endif
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
		{ COSTUME_WEAPON,	HIDE_WEAPON,	"costume_option.hide_weapon" },
#endif
	};
	const char* const MIGRATED_FLAG = "costume_option.migrated";

	std::map<DWORD, BYTE> s_hidden;		// by player id, read at every login
	std::map<DWORD, DWORD> s_lastChange;	// by player id: the last change (Owsap: one in 3 s)

	BYTE Mask(LPCHARACTER ch)
	{
		std::map<DWORD, BYTE>::const_iterator it = s_hidden.find(ch->GetPlayerID());
		return it == s_hidden.end() ? 0 : it->second;
	}

	const TPart* Part(BYTE bSubType)
	{
		for (size_t i = 0; i < sizeof(s_aParts) / sizeof(s_aParts[0]); ++i)
			if (s_aParts[i].bSubType == bSubType)
				return &s_aParts[i];
		return NULL;
	}

	void Send(LPCHARACTER ch)
	{
		if (!ch->GetDesc())
			return;
		const BYTE bMask = Mask(ch);
		for (size_t i = 0; i < sizeof(s_aParts) / sizeof(s_aParts[0]); ++i)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "SetHiddenCostumePart %d %d", s_aParts[i].bSubType, (bMask & s_aParts[i].bBit) ? 1 : 0);
	}

	void Store(LPCHARACTER ch, BYTE bMask)
	{
		const BYTE bOld = Mask(ch);
		if (bMask)
			s_hidden[ch->GetPlayerID()] = bMask;
		else
			s_hidden.erase(ch->GetPlayerID());
		for (size_t i = 0; i < sizeof(s_aParts) / sizeof(s_aParts[0]); ++i)
			if ((bOld ^ bMask) & s_aParts[i].bBit)
				ch->SetQuestFlag(s_aParts[i].c_pszFlag, (bMask & s_aParts[i].bBit) ? 1 : 0);
		ch->SetQuestFlag(MIGRATED_FLAG, 1);
		if (bOld != bMask)
			ch->UpdatePacket();
	}
}

// input_login.cpp Entergame: the character's choice from its quest flags, to the client and - when anything is
// hidden - to everyone around (the character was shown before its flags were read here).
void Mt2009HideCostumeOnLogin(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc())
		return;
	BYTE bMask = 0;
	for (size_t i = 0; i < sizeof(hidecostume::s_aParts) / sizeof(hidecostume::s_aParts[0]); ++i)
		if (ch->GetQuestFlag(hidecostume::s_aParts[i].c_pszFlag))
			bMask |= hidecostume::s_aParts[i].bBit;
	if (bMask)
		hidecostume::s_hidden[ch->GetPlayerID()] = bMask;
	else
		hidecostume::s_hidden.erase(ch->GetPlayerID());
	hidecostume::Send(ch);
	if (bMask)
		ch->UpdatePacket();
}

// char.cpp: the parts of an add / update packet (CHR_EQUIPPART_*, filled with GetPart) with the hidden ones out.
void Mt2009HideCostumeParts(LPCHARACTER ch, DWORD* awPart)
{
	if (!ch || !awPart || !ch->IsPC() || ch->IsPolymorphed())
		return;
	const BYTE bMask = hidecostume::Mask(ch);
	if (!bMask)
		return;
	if ((bMask & hidecostume::HIDE_BODY) && ch->GetWear(WEAR_COSTUME_BODY))
	{
		LPITEM body = ch->GetWear(WEAR_BODY);
#ifdef ENABLE_CHANGELOOK_SYSTEM
		awPart[CHR_EQUIPPART_ARMOR] = body ? body->GetLookVnum() : ch->GetOriginalPart(PART_MAIN);
#else
		awPart[CHR_EQUIPPART_ARMOR] = body ? body->GetVnum() : ch->GetOriginalPart(PART_MAIN);
#endif
	}
	if ((bMask & hidecostume::HIDE_HAIR) && ch->GetWear(WEAR_COSTUME_HAIR))
		awPart[CHR_EQUIPPART_HAIR] = 0;	// the character's own hair, as with no hair costume on
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
	if ((bMask & hidecostume::HIDE_WEAPON) && ch->GetWear(WEAR_COSTUME_WEAPON))
	{
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
#ifdef ENABLE_CHANGELOOK_SYSTEM
		awPart[CHR_EQUIPPART_WEAPON] = weapon ? weapon->GetLookVnum() : 0;
#else
		awPart[CHR_EQUIPPART_WEAPON] = weapon ? weapon->GetVnum() : 0;
#endif
	}
#endif
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	if ((bMask & hidecostume::HIDE_ACCE) && ch->GetWear(WEAR_COSTUME_ACCE))
		awPart[CHR_EQUIPPART_ACCE] = 0;
#endif
}

// playerqol's "/kostiumy_ukryj m <mask>" (the old client setting): taken once, by a character that never chose.
void Mt2009HideCostumeLegacy(LPCHARACTER ch, BYTE bMask)
{
	if (!ch || !ch->IsPC() || ch->GetQuestFlag(hidecostume::MIGRATED_FLAG))
		return;
	hidecostume::Store(ch, bMask & (hidecostume::HIDE_BODY | hidecostume::HIDE_HAIR | hidecostume::HIDE_WEAPON));
	hidecostume::Send(ch);
}

// cmd.cpp: "/hide_costume_part <subtype> <0|1>" (Owsap's, with his rules: standing still, one change in 3 s)
ACMD(do_hide_costume_part)
{
	char arg1[32], arg2[32];
	two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	if (!*arg1 || !*arg2 || !ch || !ch->IsPC())
		return;
	int iSubType = -1, iHidden = 0;
	str_to_number(iSubType, arg1);
	str_to_number(iHidden, arg2);
	const hidecostume::TPart* pPart = iSubType >= 0 ? hidecostume::Part((BYTE) iSubType) : NULL;
	if (!pPart || ch->IsDead() || ch->IsWarping())
		return;

	const DWORD dwNow = get_dword_time();
	if (ch->IsStateMove() || dwNow - ch->GetLastAttackTime() < 1500 || dwNow - ch->GetLastMoveTime() < 1500)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zatrzymaj si\xea, \xbf" "eby ukry\xe6 albo pokaza\xe6 kostium.");
		hidecostume::Send(ch);
		return;
	}
	std::map<DWORD, DWORD>::iterator it = hidecostume::s_lastChange.find(ch->GetPlayerID());
	if (it != hidecostume::s_lastChange.end() && dwNow - it->second < 3000)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Poczekaj 3 sekundy przed kolejn\xb9 zmian\xb9.");
		hidecostume::Send(ch);
		return;
	}
	hidecostume::s_lastChange[ch->GetPlayerID()] = dwNow;

	BYTE bMask = hidecostume::Mask(ch);
	if (iHidden)
		bMask |= pPart->bBit;
	else
		bMask &= ~pPart->bBit;
	hidecostume::Store(ch, bMask);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "SetHiddenCostumePart %d %d", pPart->bSubType, iHidden ? 1 : 0);
}

#endif // ENABLE_HIDE_COSTUME_SYSTEM
