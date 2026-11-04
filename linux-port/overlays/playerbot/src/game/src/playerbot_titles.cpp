// MT2009_PLUS_TITLES_V1: Tytuly postaci - a character's titles (the owner's package "Official Title System Renewal",
// rebuilt for MT2009 PLUS 3.x; server-patches/tytuly/README.md has the whole picture). A player owns titles (for good or
// until a time), wears one of them, and every client around draws it with his name: a name plate (the title's name on a
// three-part plate, the animated banners above it) or an effect over his head.
//   * the catalogue is here (TITLES): index, look (plate / effect), Polish name and how it is got, permanent or the
//     default time, the client resource (d:/ymir work/ui/game/title/titles/title_<res>.sub) and the effect file - the
//     server sends it to the client (TABLE), so a title added here needs no client data but its pictures;
//   * player.player_title (apply.sh): a row an owned title (pid, title_index, end_time 0 = for good, equipped 0/1),
//     read at login, written at a change - no db core / TPlayerTable change, no quest flags (the package kept the
//     owned / worn titles twice: its table and quest flags);
//   * HEADER_CG_TITLE 185 / HEADER_GC_TITLE 189 (dynamic) - the package's numbers, free here and in the exe; the
//     client says hello (CG OPEN) when it enters the game, and only a client that did gets a title packet: an older exe
//     never sees GC 189 (no client version gate needed); bots never say it, nor have a title (no query for them);
//   * who wears what: GC VISUAL (vid, title) to every viewer that said hello - after its add packet (EncodeInsert) and
//     when it changes (the package abused SpecificEffectPacket with "path|index" to everyone around at each insert);
//   * the certificates 57000-57002 (the package's vnums): value0 the title, value1 the time in seconds (0 = the
//     title's default); a timed title already owned is lengthened (the package refused it);
//   * GM: /tytul (also the package's /title_system), quests: title.give / has / remove / equipped (questlua.cpp);
//   * expiry and the "one hour left" notice: a 60 s tick over the characters that own a timed title.
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "item.h"
#include "db.h"
#include "packet.h"
#include "questmanager.h"
#include "questlua.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace titles
{
	enum ETitleType
	{
		TYPE_TEXT = 1,			// the name only
		TYPE_EFFECT = 3,		// an effect over the head (no name)
		TYPE_NAMEPLATE = 4,		// the name on a plate (the resource's .sub: plate pictures, maybe animated banner)
	};

	enum EMessage
	{
		MSG_ALREADY_OWNED = 0,
		MSG_WRONG_REQUEST = 1,
		MSG_WRONG_ITEM = 2,
		MSG_EXPIRED = 3,
		MSG_GOT = 4,
		MSG_EQUIPPED = 5,
		MSG_UNEQUIPPED = 6,
		MSG_ONE_HOUR_LEFT = 7,
		MSG_TRY_LATER = 8,
		MSG_PROLONGED = 9,
		MSG_REMOVED = 10,
	};

	struct SProto
	{
		DWORD index;
		BYTE type;
		bool permanent;
		DWORD duration;			// the default time of a timed title (s)
		WORD resource;			// d:/ymir work/ui/game/title/titles/title_<resource>.sub
		short effectZ;			// the effect's height over the head
		DWORD color;			// the name's colour (ARGB)
		const char* name;
		const char* condition;
		const char* effect;		// the over-head effect (TYPE_EFFECT)
	};

	const DWORD DAY = 86400;
	const DWORD COLOR = 0xFFD6E3F3;	// the package's ice blue
	const char* const FX = "d:/ymir work/effect/etc/title/";

	// The package's titles and its Polish names (title_gf.txt / title_wz.txt); the official server's sources (its
	// premium membership, its other servers, Battle Royale) replaced by ours - the owner decides the rest (README).
	const SProto TITLES[] =
	{
		{ 1000, TYPE_NAMEPLATE, true, 0, 1005, 0, COLOR, "Szcz\xea\x9c""ciarz",
			"Niebieski Certyfikat Tytu\xb3u albo wygrana w losowaniu na evencie.", "" },
		{ 1002, TYPE_NAMEPLATE, false, 30 * DAY, 1003, 0, COLOR, "Heroiczny",
			"Czerwony Certyfikat Tytu\xb3u (30 dni, kolejny przed\xb3u\xbf""a).", "" },
		{ 1003, TYPE_NAMEPLATE, false, 30 * DAY, 1003, 0, COLOR, "Legendarny",
			"Nagroda za eventy (nadaje GM).", "" },
		{ 1004, TYPE_NAMEPLATE, false, 30 * DAY, 1003, 0, COLOR, "Mistyczny",
			"Nagroda za eventy (nadaje GM).", "" },
		{ 1005, TYPE_NAMEPLATE, true, 0, 1000, 0, COLOR, "Czciciel S\xb3o\xf1""ca",
			"Zielony Certyfikat Tytu\xb3u albo letni event.", "" },
		{ 1006, TYPE_NAMEPLATE, true, 0, 1002, 0, COLOR, "Gwiazda Polarna",
			"Do zdobycia podczas zimowego eventu.", "" },
		{ 1011, TYPE_NAMEPLATE, true, 0, 1001, 0, COLOR, "Wielki Mistrz Okey",
			"Zdob\xb9""d\x9f 500 lub wi\xea""cej punkt\xf3w w jednej rundzie Okey.", "" },
		{ 1012, TYPE_NAMEPLATE, true, 0, 1004, 0, COLOR, "\xa3owca Monet",
			"Nagroda za eventy (nadaje GM).", "" },
		{ 1, TYPE_EFFECT, false, 3 * 3600, 2000, 0, COLOR, "Ostatni Ocala\xb3y",
			"Przetrwaj do ko\xf1""ca eventu na arenie (3 godziny).", "crown01.mse" },
		{ 2, TYPE_EFFECT, false, 7 * DAY, 3003, 0, COLOR, "Niepokonany",
			"Zajmij 1. miejsce w tygodniowym rankingu zab\xf3jc\xf3w (7 dni).", "title_04_trophy.mse" },
		{ 3, TYPE_EFFECT, false, 7 * DAY, 3004, 0, COLOR, "Zwiastun Wojny",
			"Zajmij 2. miejsce w tygodniowym rankingu zab\xf3jc\xf3w (7 dni).", "title_05_medal.mse" },
		{ 4, TYPE_EFFECT, false, 7 * DAY, 3002, 0, COLOR, "Rze\x9fnik",
			"Zajmij 3. miejsce w tygodniowym rankingu zab\xf3jc\xf3w (7 dni).", "title_03_fist.mse" },
		{ 6, TYPE_EFFECT, false, 7 * DAY, 3005, 0, COLOR, "P\xb3omienny Pogromca",
			"Zajmij 1. miejsce w tygodniowym rankingu Schronienia Meley (7 dni).", "title_dragon_red.mse" },
		{ 7, TYPE_EFFECT, false, 7 * DAY, 3006, 0, COLOR, "Bezlitosny S\xea""dzia",
			"Zajmij 1. miejsce w tygodniowym rankingu Krypty Balathora (7 dni).", "title_dragon_gw.mse" },
	};
	const size_t TITLE_COUNT = sizeof(TITLES) / sizeof(TITLES[0]);

	// the certificates (the package's vnums); value0 = the title, value1 = its time (s, 0 = the title's default)
	const DWORD CERT_FIRST = 57000;
	const DWORD CERT_LAST = 57002;

	const DWORD ACTION_GAP_MS = 1000;	// one equip / unequip a second (the package's cooldown)
	const int TICK_SEC = 60;
	const DWORD MAX_END_AHEAD = 3650 * DAY;	// a prolonged title ends in at most ten years

	struct SState
	{
		bool hello;							// its client said hello (CG OPEN): it gets the title packets
		DWORD pid;
		std::map<DWORD, DWORD> owned;		// title -> end time (0 = for good)
		std::map<DWORD, bool> warned;		// "one hour left" said
		DWORD equipped;
		DWORD lastAction;
		SState() : hello(false), pid(0), equipped(0), lastAction(0) {}
	};

	// by VID - like skillcolor's state: a PC's titles from its rows at login, gone with the character
	std::unordered_map<DWORD, SState> s_state;
	LPEVENT s_pkTick = NULL;

	const SProto* Find(DWORD index)
	{
		for (size_t i = 0; i < TITLE_COUNT; ++i)
			if (TITLES[i].index == index)
				return &TITLES[i];
		return NULL;
	}

	bool IsPlayer(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	SState* StateOf(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		std::unordered_map<DWORD, SState>::iterator it = s_state.find((DWORD) ch->GetVID());
		return it == s_state.end() ? NULL : &it->second;
	}

	bool Owns(const SState& st, DWORD index, DWORD now)
	{
		std::map<DWORD, DWORD>::const_iterator it = st.owned.find(index);
		return it != st.owned.end() && (it->second == 0 || it->second > now);
	}

	// the entities that see ch (CEntity::m_map_view is protected - read through a derived class's member pointer)
	struct CViewAccess : public CEntity
	{
		static ENTITY_MAP CEntity::* Member() { return &CViewAccess::m_map_view; }
	};

	bool SaidHello(LPCHARACTER ch)
	{
		const SState* st = StateOf(ch);
		return st && st->hello && ch->GetDesc();
	}

	// one dynamic GC 189 packet: header + rows
	void Send(LPDESC d, BYTE sub, WORD count, const void* payload, size_t size)
	{
		if (!d)
			return;
		TPacketGCTitle p;
		p.bHeader = HEADER_GC_TITLE;
		p.wSize = (WORD) (sizeof(p) + size);
		p.bSubHeader = sub;
		p.wCount = count;
		std::vector<char> buf(sizeof(p) + size);
		memcpy(&buf[0], &p, sizeof(p));
		if (size)
			memcpy(&buf[sizeof(p)], payload, size);
		d->Packet(&buf[0], (int) buf.size());
	}

	void Notify(LPCHARACTER ch, BYTE msg, DWORD index)
	{
		if (!SaidHello(ch))
			return;
		TPacketGCTitleNotify n;
		n.bMessage = msg;
		n.dwTitle = index;
		Send(ch->GetDesc(), TITLE_GC_NOTIFY, 0, &n, sizeof(n));
	}

	void SendTable(LPCHARACTER ch)
	{
		std::vector<TPacketGCTitleRow> rows(TITLE_COUNT);
		for (size_t i = 0; i < TITLE_COUNT; ++i)
		{
			const SProto& t = TITLES[i];
			TPacketGCTitleRow& r = rows[i];
			memset(&r, 0, sizeof(r));
			r.dwTitle = t.index;
			r.bType = t.type;
			r.bPermanent = t.permanent ? 1 : 0;
			r.wResource = t.resource;
			r.dwDuration = t.permanent ? 0 : t.duration;
			r.dwColor = t.color;
			r.sEffectZ = t.effectZ;
			strlcpy(r.szName, t.name, sizeof(r.szName));
			strlcpy(r.szCondition, t.condition, sizeof(r.szCondition));
			if (t.effect && *t.effect)
				snprintf(r.szEffect, sizeof(r.szEffect), "%s%s", FX, t.effect);
		}
		Send(ch->GetDesc(), TITLE_GC_TABLE, (WORD) rows.size(), &rows[0], rows.size() * sizeof(TPacketGCTitleRow));
	}

	void SendOwned(LPCHARACTER ch)
	{
		const SState* st = StateOf(ch);
		if (!st || !st->hello)
			return;
		const DWORD now = (DWORD) get_global_time();
		std::vector<TPacketGCTitleOwned> rows;
		for (std::map<DWORD, DWORD>::const_iterator it = st->owned.begin(); it != st->owned.end(); ++it)
		{
			if (it->second && it->second <= now)
				continue;
			TPacketGCTitleOwned r;
			r.dwTitle = it->first;
			r.dwEndTime = it->second;
			rows.push_back(r);
		}
		Send(ch->GetDesc(), TITLE_GC_PLAYER, (WORD) rows.size(), rows.empty() ? NULL : &rows[0], rows.size() * sizeof(TPacketGCTitleOwned));
		const DWORD equipped = st->equipped;
		Send(ch->GetDesc(), TITLE_GC_EQUIPPED, 0, &equipped, sizeof(equipped));
	}

	// ch's worn title (0 = none) to one viewer that said hello
	void SendVisual(LPCHARACTER ch, LPCHARACTER viewer)
	{
		if (!ch || !SaidHello(viewer))
			return;
		const SState* st = StateOf(ch);
		TPacketGCTitleVisual v;
		v.dwVID = (DWORD) ch->GetVID();
		v.dwTitle = st ? st->equipped : 0;
		Send(viewer->GetDesc(), TITLE_GC_VISUAL, 0, &v, sizeof(v));
	}

	// ch's worn title to everyone who sees it (ch too)
	void BroadcastVisual(LPCHARACTER ch)
	{
		if (!ch || !ch->GetSectree())
			return;
		SendVisual(ch, ch);
		const CEntity::ENTITY_MAP& view = ch->*(CViewAccess::Member());
		for (CEntity::ENTITY_MAP::const_iterator it = view.begin(); it != view.end(); ++it)
		{
			LPENTITY ent = it->first;
			if (ent && ent->IsType(ENTITY_CHARACTER) && ent != ch)
				SendVisual(ch, (LPCHARACTER) ent);
		}
	}

	// after the hello: the titles of everyone viewer already sees (their add packets went before it)
	void SendViewVisuals(LPCHARACTER viewer)
	{
		const CEntity::ENTITY_MAP& view = viewer->*(CViewAccess::Member());
		for (CEntity::ENTITY_MAP::const_iterator it = view.begin(); it != view.end(); ++it)
		{
			LPENTITY ent = it->first;
			if (!ent || !ent->IsType(ENTITY_CHARACTER) || ent == viewer)
				continue;
			const SState* st = StateOf((LPCHARACTER) ent);
			if (st && st->equipped)
				SendVisual((LPCHARACTER) ent, viewer);
		}
		SendVisual(viewer, viewer);
	}

	void SaveRow(DWORD pid, DWORD index, DWORD end, bool equipped)
	{
		DBManager::instance().Query("REPLACE INTO player.player_title (pid, title_index, end_time, equipped) VALUES (%u, %u, %u, %u)",
			pid, index, end, equipped ? 1 : 0);
	}

	void SaveEquipped(DWORD pid, DWORD index)
	{
		DBManager::instance().Query("UPDATE player.player_title SET equipped = IF(title_index = %u, 1, 0) WHERE pid = %u", index, pid);
	}

	void DeleteRow(DWORD pid, DWORD index)
	{
		DBManager::instance().Query("DELETE FROM player.player_title WHERE pid = %u AND title_index = %u", pid, index);
	}

	EVENTINFO(titles_tick_info)
	{
		int dummy;
	};

	void Expire(LPCHARACTER ch, SState& st, DWORD now);

	EVENTFUNC(titles_tick)
	{
		const DWORD now = (DWORD) get_global_time();
		std::vector<DWORD> vids;
		for (std::unordered_map<DWORD, SState>::const_iterator it = s_state.begin(); it != s_state.end(); ++it)
			if (!it->second.owned.empty())
				vids.push_back(it->first);
		for (size_t i = 0; i < vids.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().Find(vids[i]);
			std::unordered_map<DWORD, SState>::iterator it = s_state.find(vids[i]);
			if (!ch || it == s_state.end())
				continue;
			Expire(ch, it->second, now);
		}
		return PASSES_PER_SEC(TICK_SEC);
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		titles_tick_info* info = AllocEventInfo<titles_tick_info>();
		s_pkTick = event_create(titles_tick, info, PASSES_PER_SEC(TICK_SEC));
	}

	// the titles whose time is up go (row, list, worn one), and the "one hour left" notice
	void Expire(LPCHARACTER ch, SState& st, DWORD now)
	{
		std::vector<DWORD> gone;
		for (std::map<DWORD, DWORD>::const_iterator it = st.owned.begin(); it != st.owned.end(); ++it)
		{
			if (!it->second)
				continue;
			if (it->second <= now)
				gone.push_back(it->first);
			else if (it->second - now <= 3600 && !st.warned[it->first])
			{
				st.warned[it->first] = true;
				Notify(ch, MSG_ONE_HOUR_LEFT, it->first);
			}
		}
		if (gone.empty())
			return;
		bool visual = false;
		for (size_t i = 0; i < gone.size(); ++i)
		{
			st.owned.erase(gone[i]);
			st.warned.erase(gone[i]);
			DeleteRow(st.pid, gone[i]);
			if (st.equipped == gone[i])
			{
				st.equipped = 0;
				visual = true;
			}
			Notify(ch, MSG_EXPIRED, gone[i]);
		}
		SendOwned(ch);
		if (visual)
			BroadcastVisual(ch);
	}

	// a title for ch (a certificate, a GM, a quest): iSeconds > 0 its time, 0 the title's default; a timed one already
	// owned gets the time on top. bWear: worn at once when ch wears none.
	bool Grant(LPCHARACTER ch, DWORD index, int iSeconds, bool bWear)
	{
		const SProto* t = Find(index);
		SState* st = StateOf(ch);
		if (!t || !st || !st->pid)
			return false;
		const DWORD now = (DWORD) get_global_time();
		const bool owned = Owns(*st, index, now);
		DWORD end = 0;
		if (!t->permanent)
		{
			const DWORD secs = iSeconds > 0 ? (DWORD) iSeconds : t->duration;
			const DWORD from = owned && st->owned[index] > now ? st->owned[index] : now;
			end = std::min(from + secs, now + MAX_END_AHEAD);
		}
		else if (owned)
		{
			Notify(ch, MSG_ALREADY_OWNED, index);
			return false;
		}
		st->owned[index] = end;
		st->warned.erase(index);
		const bool wear = bWear && !st->equipped;
		if (wear)
			st->equipped = index;
		SaveRow(st->pid, index, end, st->equipped == index);
		if (wear)
			SaveEquipped(st->pid, index);
		EnsureTick();
		Notify(ch, owned ? MSG_PROLONGED : MSG_GOT, index);
		SendOwned(ch);
		if (wear)
			BroadcastVisual(ch);
		return true;
	}

	bool Remove(LPCHARACTER ch, DWORD index)
	{
		SState* st = StateOf(ch);
		if (!st || !st->owned.count(index))
			return false;
		st->owned.erase(index);
		st->warned.erase(index);
		DeleteRow(st->pid, index);
		Notify(ch, MSG_REMOVED, index);
		if (st->equipped == index)
		{
			st->equipped = 0;
			BroadcastVisual(ch);
		}
		SendOwned(ch);
		return true;
	}

	bool Equip(LPCHARACTER ch, DWORD index)
	{
		SState* st = StateOf(ch);
		if (!st)
			return false;
		const DWORD ms = get_dword_time();
		if (st->lastAction && ms - st->lastAction < ACTION_GAP_MS)
		{
			Notify(ch, MSG_TRY_LATER, index);
			return false;
		}
		st->lastAction = ms;
		if (index && (!Find(index) || !Owns(*st, index, (DWORD) get_global_time())))
		{
			Notify(ch, MSG_WRONG_REQUEST, index);
			return false;
		}
		if (st->equipped == index)
			return true;
		const DWORD old = st->equipped;
		st->equipped = index;
		SaveEquipped(st->pid, index);
		Notify(ch, index ? MSG_EQUIPPED : MSG_UNEQUIPPED, index ? index : old);
		SendOwned(ch);
		BroadcastVisual(ch);
		return true;
	}

	std::string Trim(const std::string& s)
	{
		const size_t a = s.find_first_not_of(" \t\r\n");
		if (a == std::string::npos)
			return "";
		const size_t b = s.find_last_not_of(" \t\r\n");
		return s.substr(a, b - a + 1);
	}

	// a title by its number or (case-insensitive, ASCII) its name
	const SProto* Parse(const std::string& arg)
	{
		const std::string s = Trim(arg);
		if (s.empty())
			return NULL;
		bool digits = true;
		for (size_t i = 0; i < s.size(); ++i)
			digits = digits && isdigit((unsigned char) s[i]);
		if (digits)
			return Find((DWORD) strtoul(s.c_str(), NULL, 10));
		for (size_t i = 0; i < TITLE_COUNT; ++i)
			if (strcasecmp(TITLES[i].name, s.c_str()) == 0)
				return &TITLES[i];
		return NULL;
	}
}

// input_main.cpp (MT2009_PLUS_TITLES_V1 (packet)): HEADER_CG_TITLE - the hello (OPEN, also the window's refresh),
// wearing and taking off a title. The packet has a fixed size (packet_info.cpp).
void TitleSystemPacket(LPCHARACTER ch, const char* data)
{
	using namespace titles;
	if (!IsPlayer(ch))
		return;
	SState* st = StateOf(ch);
	if (!st)
		return;
	const TPacketCGTitle* p = (const TPacketCGTitle*) data;
	switch (p->bSubHeader)
	{
		case TITLE_CG_OPEN:
		{
			const bool first = !st->hello;
			st->hello = true;
			SendTable(ch);
			SendOwned(ch);
			if (first)
				SendViewVisuals(ch);
			break;
		}
		case TITLE_CG_EQUIP:
			if (st->hello)
				Equip(ch, p->dwTitle);
			break;
		case TITLE_CG_UNEQUIP:
			if (st->hello)
				Equip(ch, 0);
			break;
		default:
			break;
	}
}

// input_login.cpp (MT2009_PLUS_TITLES_V1 (login)): the character's rows (every core reads them again - a change made on
// another channel); an expired one goes; the worn one to everyone around who said hello.
void TitleSystemOnLogin(LPCHARACTER ch)
{
	using namespace titles;
	if (!IsPlayer(ch))
		return;	// bots: no title, no query
	SState& st = s_state[(DWORD) ch->GetVID()];
	st = SState();
	st.pid = ch->GetPlayerID();
	std::unique_ptr<SQLMsg> m(DBManager::instance().DirectQuery(
		"SELECT title_index, end_time, equipped FROM player.player_title WHERE pid = %u", st.pid));
	if (!m.get() || m->uiSQLErrno != 0 || !m->Get() || !m->Get()->pSQLResult)
		return;
	const DWORD now = (DWORD) get_global_time();
	DWORD equipped = 0;
	MYSQL_ROW row;
	while ((row = mysql_fetch_row(m->Get()->pSQLResult)))
	{
		DWORD index = 0, end = 0, worn = 0;
		str_to_number(index, row[0]);
		str_to_number(end, row[1]);
		str_to_number(worn, row[2]);
		const SProto* t = Find(index);
		if (!t || (end && end <= now))
		{
			DeleteRow(st.pid, index);	// a title taken out of the catalogue, or its time is up
			continue;
		}
		if (t->permanent)
			end = 0;
		st.owned[index] = end;
		if (worn)
			equipped = index;
	}
	st.equipped = equipped;
	if (!st.owned.empty())
		EnsureTick();
	if (st.equipped)
		BroadcastVisual(ch);
}

// char.cpp EncodeInsertPacket (MT2009_PLUS_TITLES_V1 (insert)): ch's worn title to one viewer, after its add packets
// (nothing for a character without one, nor to a viewer whose client did not say hello).
void TitleSystemEncodeInsert(LPCHARACTER ch, LPDESC d)
{
	using namespace titles;
	if (!ch || !d || !ch->IsPC())
		return;
	const SState* st = StateOf(ch);
	if (!st || !st->equipped)
		return;
	LPCHARACTER viewer = d->GetCharacter();
	if (viewer && viewer != ch)
		SendVisual(ch, viewer);
}

// char.cpp Destroy (MT2009_PLUS_TITLES_V1 (destroy)): the VID's state goes with it
void TitleSystemOnDestroy(LPCHARACTER ch)
{
	if (ch)
		titles::s_state.erase((DWORD) ch->GetVID());
}

// char_item.cpp UseItemEx (MT2009_PLUS_TITLES_V1 (use)): a certificate 57000-57002 - -1 not one, 0 refused, 1 used
int TitleSystemUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace titles;
	if (!ch || !item || item->GetVnum() < CERT_FIRST || item->GetVnum() > CERT_LAST)
		return -1;
	if (!IsPlayer(ch) || !StateOf(ch))
		return 0;
	const DWORD index = (DWORD) item->GetValue(0);
	if (!Find(index))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ten certyfikat nie nadaje \xbf""adnego tytu\xb3u.");
		return 0;
	}
	if (!SaidHello(ch))
		ch->ChatPacket(CHAT_TYPE_INFO, "Tytu\xb3y wymagaj\xb9 nowej wersji klienta - zaktualizuj gr\xea.");
	if (!Grant(ch, index, (int) item->GetValue(1), true))
	{
		if (!SaidHello(ch))
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz ju\xbf ten tytu\xb3.");
		return 0;
	}
	item->SetCount(item->GetCount() - 1);
	return 1;
}

// cmd.cpp (MT2009_PLUS_TITLES_V1 (command)): /tytul (and the package's /title_system), GM:
//   /tytul lista                         the catalogue
//   /tytul <numer|nazwa>                 the title for yourself
//   /tytul daj <gracz> <numer> [dni]     a title for a player of this core (dni: its time, else the title's default)
//   /tytul zabierz <gracz> <numer>       a title taken away
//   /tytul pokaz <gracz>                 what the player owns and wears
void TitleSystemCommand(LPCHARACTER ch, const char* argument)
{
	using namespace titles;
	if (!ch)
		return;
	std::vector<std::string> a;
	{
		std::string cur;
		for (const char* p = argument ? argument : ""; ; ++p)
		{
			if (!*p || isspace((unsigned char) *p))
			{
				if (!cur.empty())
					a.push_back(cur);
				cur.clear();
				if (!*p)
					break;
			}
			else
				cur.push_back(*p);
		}
	}
	if (a.empty())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "U\xbfycie: /tytul lista | /tytul <numer> | /tytul daj <gracz> <numer> [dni] | /tytul zabierz <gracz> <numer> | /tytul pokaz <gracz>");
		return;
	}
	if (a[0] == "lista")
	{
		for (size_t i = 0; i < TITLE_COUNT; ++i)
			ch->ChatPacket(CHAT_TYPE_INFO, "%u: %s (%s)", TITLES[i].index, TITLES[i].name,
				TITLES[i].permanent ? "na sta\xb3""e" : "czasowy");
		return;
	}
	if (a[0] == "daj" || a[0] == "zabierz" || a[0] == "pokaz")
	{
		if (a.size() < 2)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Podaj gracza.");
			return;
		}
		LPCHARACTER tch = CHARACTER_MANAGER::instance().FindPC(a[1].c_str());
		if (!tch || !IsPlayer(tch) || !StateOf(tch))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Gracza %s nie ma na tym kanale (albo to bot).", a[1].c_str());
			return;
		}
		if (a[0] == "pokaz")
		{
			const SState* st = StateOf(tch);
			const DWORD now = (DWORD) get_global_time();
			ch->ChatPacket(CHAT_TYPE_INFO, "%s: tytu\xb3\xf3w %u, za\xb3o\xbfony %u", tch->GetName(), (unsigned int) st->owned.size(), st->equipped);
			for (std::map<DWORD, DWORD>::const_iterator it = st->owned.begin(); it != st->owned.end(); ++it)
			{
				const SProto* t = Find(it->first);
				if (it->second)
					ch->ChatPacket(CHAT_TYPE_INFO, "  %u %s - jeszcze %u min", it->first, t ? t->name : "?",
						it->second > now ? (it->second - now) / 60 : 0);
				else
					ch->ChatPacket(CHAT_TYPE_INFO, "  %u %s - na sta\xb3""e", it->first, t ? t->name : "?");
			}
			return;
		}
		const SProto* t = a.size() >= 3 ? Parse(a[2]) : NULL;
		if (!t)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie ma takiego tytu\xb3u (/tytul lista).");
			return;
		}
		if (a[0] == "zabierz")
		{
			if (Remove(tch, t->index))
				ch->ChatPacket(CHAT_TYPE_INFO, "Zabrano tytu\xb3 %s graczowi %s.", t->name, tch->GetName());
			else
				ch->ChatPacket(CHAT_TYPE_INFO, "Gracz %s nie ma tytu\xb3u %s.", tch->GetName(), t->name);
			return;
		}
		const int days = a.size() >= 4 ? atoi(a[3].c_str()) : 0;
		if (Grant(tch, t->index, days > 0 ? days * (int) DAY : 0, true))
			ch->ChatPacket(CHAT_TYPE_INFO, "Nadano tytu\xb3 %s graczowi %s.", t->name, tch->GetName());
		else
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie nadano tytu\xb3u %s (gracz ma go ju\xbf na sta\xb3""e).", t->name);
		return;
	}
	std::string all = a[0];
	for (size_t i = 1; i < a.size(); ++i)
		all += " " + a[i];
	const SProto* t = Parse(all);
	if (!t)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie ma takiego tytu\xb3u (/tytul lista).");
		return;
	}
	if (!StateOf(ch) || !Grant(ch, t->index, 0, true))
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie nadano tytu\xb3u %s.", t->name);
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "Nadano tytu\xb3 %s.", t->name);
}

namespace quest
{
	// title.give(numer [, sekundy]) -> true when given / lengthened; title.has(numer); title.remove(numer);
	// title.equipped() -> the worn title's number (0 none). For the quest's current character.
	static int title_give(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const DWORD index = lua_isnumber(L, 1) ? (DWORD) lua_tonumber(L, 1) : 0;
		const int secs = lua_isnumber(L, 2) ? (int) lua_tonumber(L, 2) : 0;
		lua_pushboolean(L, ch && titles::IsPlayer(ch) && titles::Grant(ch, index, secs, true));
		return 1;
	}

	static int title_has(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const titles::SState* st = titles::StateOf(ch);
		const DWORD index = lua_isnumber(L, 1) ? (DWORD) lua_tonumber(L, 1) : 0;
		lua_pushboolean(L, st && titles::Owns(*st, index, (DWORD) get_global_time()));
		return 1;
	}

	static int title_remove(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const DWORD index = lua_isnumber(L, 1) ? (DWORD) lua_tonumber(L, 1) : 0;
		lua_pushboolean(L, ch && titles::Remove(ch, index));
		return 1;
	}

	static int title_equipped(lua_State* L)
	{
		const titles::SState* st = titles::StateOf(CQuestManager::instance().GetCurrentCharacterPtr());
		lua_pushnumber(L, st ? st->equipped : 0);
		return 1;
	}

	// questlua.cpp (MT2009_PLUS_TITLES_V1 (lua))
	void RegisterTitleFunctionTable()
	{
		luaL_reg title_functions[] =
		{
			{ "give",		title_give		},
			{ "has",		title_has		},
			{ "remove",		title_remove	},
			{ "equipped",	title_equipped	},
			{ NULL,			NULL			}
		};
		CQuestManager::instance().AddLuaFunctionTable("title", title_functions);
	}
}
