// MT2009_PLUS_SKILL_COLOR_V1: Kolor umiejetnosci - the player picks the colour of a skill's effects (five layers: the
// effect's particle systems 1-5, the 5th also for every later one) in a window of the skill tab; it is kept per
// character in player.skill_color (apply.sh) and every client around draws that character's skill in it. Port of the
// owner's package "SKILL_COLOR_SYSTEM by OSWAP (FULL)" (Owsap, V1.0.1.4), rebuilt for MT2009 PLUS 3.x
// (server-patches/skillcolor/README.md has the whole picture):
//   * a colour is one skill's, by vnum (the package had six slots of the shown path + five shaman buffs): both paths of
//     the class (the skill hack's other path too), the 9th skills 176-182, the horse skills 137-140 and the Buffi's
//     164-167 - riposty/dopalacze (221-243) are passive, they have no effect to colour;
//   * the package's own rule: a skill is coloured from its P (level 40); a horse skill once it is learned; "default"
//     (all five 0) always;
//   * own table, row per coloured skill (player_id, skill_vnum, col1..col5), read here at login (like the switchbot's
//     player.switchbot) and written when it changes - the db core and TPlayerTable are not touched;
//   * no colour in the character add/update packets (the package's 220 B in every update of every character to every
//     viewer): HEADER_GC_SKILL_COLOR (28 B), one per coloured skill, after the add packet and when it changes - bots
//     and players without colours cost nothing;
//   * a shaman's buff (94/95/96/110/111) shows the CASTER's colour on whoever got it (the package copied the caster's
//     colour into the target's "buff slots" and saved them in the target's row) - here a second, unsaved table of the
//     character ("got", SKILL_COLOR_TYPE_BUFF), set when ComputeSkill gives the buff; the Buffi's buffs carry the
//     owner's colour of the Buffi skill (164 -> 94, 165 -> 96, 166 -> 110, 167 -> 111), and the Buffi's own cast
//     motion the same.
// A colour is 0 (the effect's own) or 0xFFrrggbb; the exe keeps each particle's alpha and brightness and swaps its hue.
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "packet.h"
#include "char.h"
#include "desc.h"
#include "db.h"
#include "skill.h"

#include <cstdlib>
#include <map>
#include <unordered_map>

namespace skillcolor
{
	struct SColors
	{
		DWORD c[SKILL_COLOR_LAYERS];
	};

	struct SState
	{
		std::map<WORD, SColors> own;	// the character's own colours (player.skill_color)
		std::map<WORD, SColors> got;	// the colour of the shaman buff it carries (its caster's), not saved
		DWORD dwLastChange;
		SState() : dwLastChange(0) {}
	};

	// by VID: a PC's own colours come from its row at login; a Buffi's own (its cast motion) from its owner
	std::unordered_map<DWORD, SState> s_state;

	const DWORD CHANGE_GAP_MS = 400;	// one change a character every 0.4 s (the window sends one skill a click)
	const BYTE LEVEL_P = 40;			// the package's "grade P" (player.GetSkillGrade >= 3)

	// the classes' skills of both paths (playerbot_skillhack.cpp PATH_SKILLS - 0 = no skill)
	const unsigned int PATH_SKILLS[4][2][6] =
	{
		{ {  1,   2,   3,   4,   5,   0 }, {  16,  17,  18,  19,  20,   0 } },
		{ { 31,  32,  33,  34,  35,   0 }, {  46,  47,  48,  49,  50,   0 } },
		{ { 61,  62,  63,  64,  65,  66 }, {  76,  77,  78,  79,  80,  81 } },
		{ { 91,  92,  93,  94,  95,  96 }, { 106, 107, 108, 109, 110, 111 } },
	};
	// MT2009_PLUS_SKILL9_V1: the 9th skills of a class (Trzesienie is both of the Warrior's paths')
	const unsigned int NINTH_SKILLS[4][2] = { { 176, 0 }, { 177, 178 }, { 179, 180 }, { 181, 182 } };

	enum EKind { KIND_NONE, KIND_P, KIND_HORSE };

	EKind Kind(const CHARACTER* ch, unsigned int vnum)
	{
		const int job = ch->GetJob();
		if (job < 0 || job > 3)
			return KIND_NONE;
		for (int p = 0; p < 2; ++p)
			for (int i = 0; i < 6; ++i)
				if (PATH_SKILLS[job][p][i] && PATH_SKILLS[job][p][i] == vnum)
					return KIND_P;
		if (vnum && (NINTH_SKILLS[job][0] == vnum || NINTH_SKILLS[job][1] == vnum))
			return KIND_P;
		if (vnum >= 164 && vnum <= 167)	// MT2009_PLUS_BUFFI_V1: the Buffi's skills (every class)
			return KIND_P;
		if (vnum >= SKILL_HORSE_WILDATTACK && vnum <= SKILL_HORSE_WILDATTACK_RANGE)	// 137-140
			return KIND_HORSE;
		return KIND_NONE;
	}

	bool IsBuffSkill(unsigned int vnum)
	{
		return vnum == SKILL_BLESSING || vnum == SKILL_REFLECT || vnum == SKILL_DRAGON_HELP || vnum == SKILL_SWIFTNESS || vnum == SKILL_ATTACK_UP;	// 94 95 96 110 111
	}

	bool ValidColor(DWORD c)
	{
		return c == 0 || (c >> 24) == 0xFF;
	}

	bool IsDefault(const SColors& s)
	{
		for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
			if (s.c[i])
				return false;
		return true;
	}

	bool Same(const SColors& a, const SColors& b)
	{
		return memcmp(a.c, b.c, sizeof(a.c)) == 0;
	}

	const SColors& Zero()
	{
		static SColors z = { { 0, 0, 0, 0, 0 } };
		return z;
	}

	void Fill(TPacketGCSkillColor& p, DWORD vid, BYTE type, WORD vnum, const SColors& s)
	{
		p.bHeader = HEADER_GC_SKILL_COLOR;
		p.dwVID = vid;
		p.bType = type;
		p.wSkillVnum = vnum;
		memcpy(p.adwColor, s.c, sizeof(p.adwColor));
	}

	// one skill's colour to everyone who sees ch (ch too)
	void Broadcast(LPCHARACTER ch, BYTE type, WORD vnum, const SColors& s)
	{
		if (!ch || !ch->GetSectree())
			return;
		TPacketGCSkillColor p;
		Fill(p, ch->GetVID(), type, vnum, s);
		ch->PacketAround(&p, sizeof(p));
	}

	// table[vnum] = s (a default colour leaves the table); true when it changed
	bool Put(std::map<WORD, SColors>& table, WORD vnum, const SColors& s)
	{
		std::map<WORD, SColors>::iterator it = table.find(vnum);
		if (IsDefault(s))
		{
			if (it == table.end())
				return false;
			table.erase(it);
			return true;
		}
		if (it != table.end() && Same(it->second, s))
			return false;
		table[vnum] = s;
		return true;
	}

	const SColors& Own(LPCHARACTER ch, WORD vnum)
	{
		std::unordered_map<DWORD, SState>::const_iterator st = s_state.find((DWORD) ch->GetVID());
		if (st == s_state.end())
			return Zero();
		std::map<WORD, SColors>::const_iterator it = st->second.own.find(vnum);
		return it == st->second.own.end() ? Zero() : it->second;
	}

	void Save(DWORD pid, WORD vnum, const SColors& s)
	{
		if (IsDefault(s))
			DBManager::instance().Query("DELETE FROM player.skill_color WHERE player_id = %u AND skill_vnum = %u", pid, (unsigned int) vnum);
		else
			DBManager::instance().Query("REPLACE INTO player.skill_color (player_id, skill_vnum, col1, col2, col3, col4, col5) "
					"VALUES (%u, %u, %u, %u, %u, %u, %u)", pid, (unsigned int) vnum, s.c[0], s.c[1], s.c[2], s.c[3], s.c[4]);
	}
}

// input_main.cpp (MT2009_PLUS_SKILL_COLOR_V1 (packet)): HEADER_CG_SKILL_COLOR - the window's "Zastosuj" / "Domyslne".
// The packet has a fixed size (packet_info.cpp), so nothing extra is read.
void SkillColorPacket(LPCHARACTER ch, const char* data)
{
	using namespace skillcolor;
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	const TPacketCGSkillColor* p = (const TPacketCGSkillColor*) data;
	const unsigned int vnum = p->wSkillVnum;
	const EKind kind = Kind(ch, vnum);
	if (kind == KIND_NONE)
		return;
	SColors s;
	for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
	{
		if (!ValidColor(p->adwColor[i]))
			return;
		s.c[i] = p->adwColor[i];
	}
	SState& st = s_state[(DWORD) ch->GetVID()];
	const DWORD now = get_dword_time();
	if (st.dwLastChange && now - st.dwLastChange < CHANGE_GAP_MS)
		return;
	if (!IsDefault(s))
	{
		const int lv = ch->GetSkillLevel(vnum);
		if ((kind == KIND_P && lv < LEVEL_P) || (kind == KIND_HORSE && lv < 1))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, kind == KIND_P
				? "Kolor umiej\xea""tno\x9c""ci mo\xbf""na zmieni\xe6 od poziomu P tej umiej\xea""tno\x9c""ci."
				: "Kolor umiej\xea""tno\x9c""ci konnej mo\xbf""na zmieni\xe6, gdy j\xb9 znasz.");
			return;
		}
	}
	st.dwLastChange = now;
	if (!Put(st.own, (WORD) vnum, s))
		return;
	Save(ch->GetPlayerID(), (WORD) vnum, s);
	Broadcast(ch, SKILL_COLOR_TYPE_OWN, (WORD) vnum, s);
	// a shaman buff on himself shows his new colour at once
	if (IsBuffSkill(vnum) && st.got.count((WORD) vnum) && Put(st.got, (WORD) vnum, s))
		Broadcast(ch, SKILL_COLOR_TYPE_BUFF, (WORD) vnum, s);
}

// input_login.cpp (MT2009_PLUS_SKILL_COLOR_V1 (login)): the character's row (every core reads it again - a change made
// on another channel), to everyone around (the add packet went out before this).
void SkillColorOnLogin(LPCHARACTER ch)
{
	using namespace skillcolor;
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;	// bots never have a colour (no row, no query)
	SState& st = s_state[(DWORD) ch->GetVID()];
	st.own.clear();
	std::unique_ptr<SQLMsg> m(DBManager::instance().DirectQuery(
		"SELECT skill_vnum, col1, col2, col3, col4, col5 FROM player.skill_color WHERE player_id = %u", ch->GetPlayerID()));
	if (!m.get() || m->uiSQLErrno != 0 || !m->Get() || !m->Get()->pSQLResult)
		return;
	MYSQL_ROW row;
	while ((row = mysql_fetch_row(m->Get()->pSQLResult)))
	{
		unsigned int vnum = 0;
		str_to_number(vnum, row[0]);
		if (Kind(ch, vnum) == KIND_NONE)
			continue;
		SColors s;
		bool ok = true;
		for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
		{
			s.c[i] = row[1 + i] ? (DWORD) strtoul(row[1 + i], NULL, 10) : 0;	// INT UNSIGNED, up to 0xFFFFFFFF
			ok = ok && ValidColor(s.c[i]);
		}
		if (ok && Put(st.own, (WORD) vnum, s))
			Broadcast(ch, SKILL_COLOR_TYPE_OWN, (WORD) vnum, s);
	}
}

// char.cpp EncodeInsertPacket (MT2009_PLUS_SKILL_COLOR_V1 (insert)): ch's colours to one viewer, after its add packets.
void SkillColorEncodeInsert(LPCHARACTER ch, LPDESC d)
{
	using namespace skillcolor;
	if (!ch || !d)
		return;
	std::unordered_map<DWORD, SState>::const_iterator st = s_state.find((DWORD) ch->GetVID());
	if (st == s_state.end())
		return;
	TPacketGCSkillColor p;
	for (std::map<WORD, SColors>::const_iterator it = st->second.own.begin(); it != st->second.own.end(); ++it)
	{
		Fill(p, ch->GetVID(), SKILL_COLOR_TYPE_OWN, it->first, it->second);
		d->Packet(&p, sizeof(p));
	}
	for (std::map<WORD, SColors>::const_iterator it = st->second.got.begin(); it != st->second.got.end(); ++it)
	{
		Fill(p, ch->GetVID(), SKILL_COLOR_TYPE_BUFF, it->first, it->second);
		d->Packet(&p, sizeof(p));
	}
}

// char_skill.cpp ComputeSkill (MT2009_PLUS_SKILL_COLOR_V1 (buff)): a shaman buff given to pkVictim (himself, a party
// member, another player) wears the caster's colour - before its affect, so the client attaches it in that colour.
void SkillColorOnBuff(LPCHARACTER caster, LPCHARACTER victim, DWORD dwVnum)
{
	using namespace skillcolor;
	if (!caster || !victim || !IsBuffSkill(dwVnum))
		return;
	const SColors s = Own(caster, (WORD) dwVnum);
	std::unordered_map<DWORD, SState>::iterator st = s_state.find((DWORD) victim->GetVID());
	if (st == s_state.end())
	{
		if (IsDefault(s))
			return;	// nothing to change - and no state for every mob a shaman buffs
		st = s_state.insert(std::make_pair((DWORD) victim->GetVID(), SState())).first;
	}
	if (Put(st->second.got, (WORD) dwVnum, s))
		Broadcast(victim, SKILL_COLOR_TYPE_BUFF, (WORD) dwVnum, s);
}

// playerbot_buffi.cpp Cast (MT2009_PLUS_SKILL_COLOR_V1 (buffi)): the Buffi's buff dwShamanSkill (94/96/110/111) on its
// owner wears the owner's colour of the Buffi skill dwBuffiSkill (164-167); the Buffi's own cast motion too.
void SkillColorOnBuffiCast(LPCHARACTER owner, LPCHARACTER mob, DWORD dwBuffiSkill, DWORD dwShamanSkill)
{
	using namespace skillcolor;
	if (!owner || !IsBuffSkill(dwShamanSkill))
		return;
	const SColors s = Own(owner, (WORD) dwBuffiSkill);
	if (mob)
	{
		std::unordered_map<DWORD, SState>::iterator ms = s_state.find((DWORD) mob->GetVID());
		if (ms != s_state.end() || !IsDefault(s))
		{
			SState& m = s_state[(DWORD) mob->GetVID()];
			if (Put(m.own, (WORD) dwShamanSkill, s))
				Broadcast(mob, SKILL_COLOR_TYPE_OWN, (WORD) dwShamanSkill, s);
		}
	}
	std::unordered_map<DWORD, SState>::iterator st = s_state.find((DWORD) owner->GetVID());
	if (st == s_state.end())
	{
		if (IsDefault(s))
			return;
		st = s_state.insert(std::make_pair((DWORD) owner->GetVID(), SState())).first;
	}
	if (Put(st->second.got, (WORD) dwShamanSkill, s))
		Broadcast(owner, SKILL_COLOR_TYPE_BUFF, (WORD) dwShamanSkill, s);
}

// char.cpp Destroy (MT2009_PLUS_SKILL_COLOR_V1 (destroy)): the VID's state goes with it
void SkillColorOnDestroy(LPCHARACTER ch)
{
	if (ch)
		skillcolor::s_state.erase((DWORD) ch->GetVID());
}
