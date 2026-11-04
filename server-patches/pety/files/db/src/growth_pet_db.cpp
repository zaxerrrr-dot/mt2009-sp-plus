// MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: the db core's part (server-patches/pety/README.md).
// Installed into db/src by server-patches/pety/apply_pety.py (overwritten when it differs); the db Makefile builds
// every *.cpp. The engine calls in through the edits of server-patches/pety/edits.json (ClientManager.cpp).
//
// The pets live in player.growth_pet, one row a pet, keyed by the pet's id - socket 2 of the seal or of the cage it
// travels in. Unlike Anka2 (rows owned by a pid, or by an account id while in the safebox, with a cache set per
// owner) nothing here knows where a pet is: a game core asks for the pets of the seals and cages it holds (GD 149
// with their ids; at login, when a storeroom opens, when a seal or cage comes in, when a cage is opened) and saves a
// pet whenever it changes (GD 147). One cache entry a pet, in this process only, so every core reads what the last
// one wrote (a character that changes cores saves on the old one before it loads on the new one). A saved pet is
// written to the table after GROWTH_PET_FLUSH_SECONDS (and at shutdown); a deleted one at once. This also fixes
// Anka2's account-id / pid collision of its owner-keyed cache sets and lets a cage go through any trade route.
//
// The skill proto (player.growth_pet_skill_proto, the wiki's tables) is read at boot and sent to every core right
// after its boot packet (DG 186), like the Ikarus shop table.
#include "stdafx.h"
#include "ClientManager.h"
#include "DBManager.h"
#include "Peer.h"
#include "Main.h"

#include <map>
#include <set>
#include <string>
#include <vector>

namespace
{
	const time_t GROWTH_PET_FLUSH_SECONDS = 10;
	const time_t GROWTH_PET_FORGET_SECONDS = 30 * 60;
	const int GROWTH_PET_FLUSH_PER_PULSE = 200;

	struct SPetCache
	{
		TGrowthPet data;
		bool dirty;
		bool deleted;
		time_t changed;
		time_t used;
	};

	std::map<DWORD, SPetCache> s_mapPets;
	std::vector<TGrowthPetSkillTable> s_vecSkillTable;

	unsigned long long ToULL(const char* s)
	{
		return s ? strtoull(s, NULL, 10) : 0ULL;
	}

	DWORD ToDW(const char* s)
	{
		return s ? (DWORD)strtoul(s, NULL, 10) : 0;
	}

	const char* const SELECT_COLUMNS =
			"id, owner_id, vnum, state, name, size, level, level_step, evolution, type, type_known, hp, sp, def, hp_apply, "
			"sp_apply, def_apply, age_apply, skill0_lock, skill0, skill0_level, skill1_lock, skill1, skill1_level, skill2_lock, "
			"skill2, skill2_level, exp, item_exp, birthday, end_time, max_time, champion_level, champion_exp, "
			"champion_item_exp, champ_res, champ_block, champ_prec, champ_res_apply, champ_block_apply, champ_prec_apply, "
			"pot0_egg, pot0_skill, pot0_end, pot1_egg, pot1_skill, pot1_end";

	void ReadRow(MYSQL_ROW row, unsigned long* lengths, TGrowthPet& p)
	{
		memset(&p, 0, sizeof(p));
		int c = 0;
		p.dwID = ToDW(row[c++]);
		p.dwOwner = ToDW(row[c++]);
		p.dwVnum = ToDW(row[c++]);
		p.bState = (BYTE)ToDW(row[c++]);
		if (row[c])
		{
			const size_t len = MIN((size_t)lengths[c], (size_t)GROWTH_PET_NAME_MAX);
			memcpy(p.szName, row[c], len);
			p.szName[len] = '\0';
		}
		++c;
		p.bSize = (BYTE)ToDW(row[c++]);
		p.dwLevel = ToDW(row[c++]);
		p.bLevelStep = (BYTE)ToDW(row[c++]);
		p.bEvolution = (BYTE)ToDW(row[c++]);
		p.bType = (BYTE)ToDW(row[c++]);
		p.bTypeKnown = (BYTE)ToDW(row[c++]);
		p.dwHP = ToDW(row[c++]);
		p.dwSP = ToDW(row[c++]);
		p.dwDef = ToDW(row[c++]);
		p.dwHPApply = ToDW(row[c++]);
		p.dwSPApply = ToDW(row[c++]);
		p.dwDefApply = ToDW(row[c++]);
		p.dwAgeApply = ToDW(row[c++]);
		for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
		{
			p.aSkill[i].bLocked = (BYTE)ToDW(row[c++]);
			p.aSkill[i].bSkill = (BYTE)ToDW(row[c++]);
			p.aSkill[i].bLevel = (BYTE)ToDW(row[c++]);
			p.aSkill[i].dwCooltime = 0;
		}
		p.ullExp = ToULL(row[c++]);
		p.ullItemExp = ToULL(row[c++]);
		p.llBirthday = (long long)ToULL(row[c++]);
		p.llEndTime = (long long)ToULL(row[c++]);
		p.llMaxTime = (long long)ToULL(row[c++]);
		p.dwChampionLevel = ToDW(row[c++]);
		p.ullChampionExp = ToULL(row[c++]);
		p.ullChampionItemExp = ToULL(row[c++]);
		p.dwChampionRes = ToDW(row[c++]);
		p.dwChampionBlockPen = ToDW(row[c++]);
		p.dwChampionPrecision = ToDW(row[c++]);
		p.dwChampionResApply = ToDW(row[c++]);
		p.dwChampionBlockPenApply = ToDW(row[c++]);
		p.dwChampionPrecisionApply = ToDW(row[c++]);
		for (int i = 0; i < GROWTH_PET_POTENTIAL_SLOTS; ++i)
		{
			p.aPotential[i].dwEggVnum = ToDW(row[c++]);
			p.aPotential[i].bSkill = (BYTE)ToDW(row[c++]);
			p.aPotential[i].dwEndTime = ToDW(row[c++]);
		}
	}

	std::string SaveQuery(const TGrowthPet& p)
	{
		char szName[GROWTH_PET_NAME_MAX * 2 + 1];
		CDBManager::instance().EscapeString(szName, p.szName, strnlen(p.szName, GROWTH_PET_NAME_MAX));
		char q[4096];
		snprintf(q, sizeof(q),
				"REPLACE INTO growth_pet%s (id, owner_id, vnum, state, name, size, level, level_step, evolution, type, type_known, "
				"hp, sp, def, hp_apply, sp_apply, def_apply, age_apply, skill0_lock, skill0, skill0_level, skill1_lock, skill1, "
				"skill1_level, skill2_lock, skill2, skill2_level, exp, item_exp, birthday, end_time, max_time, champion_level, "
				"champion_exp, champion_item_exp, champ_res, champ_block, champ_prec, champ_res_apply, champ_block_apply, "
				"champ_prec_apply, pot0_egg, pot0_skill, pot0_end, pot1_egg, pot1_skill, pot1_end) VALUES (%u, %u, %u, %u, '%s', "
				"%u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %llu, %llu, %lld, %lld, "
				"%lld, %u, %llu, %llu, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u, %u)",
				GetTablePostfix(), p.dwID, p.dwOwner, p.dwVnum, (unsigned)p.bState, szName, (unsigned)p.bSize, p.dwLevel,
				(unsigned)p.bLevelStep, (unsigned)p.bEvolution, (unsigned)p.bType, (unsigned)p.bTypeKnown, p.dwHP, p.dwSP,
				p.dwDef, p.dwHPApply, p.dwSPApply, p.dwDefApply, p.dwAgeApply,
				(unsigned)p.aSkill[0].bLocked, (unsigned)p.aSkill[0].bSkill, (unsigned)p.aSkill[0].bLevel,
				(unsigned)p.aSkill[1].bLocked, (unsigned)p.aSkill[1].bSkill, (unsigned)p.aSkill[1].bLevel,
				(unsigned)p.aSkill[2].bLocked, (unsigned)p.aSkill[2].bSkill, (unsigned)p.aSkill[2].bLevel,
				p.ullExp, p.ullItemExp, p.llBirthday, p.llEndTime, p.llMaxTime, p.dwChampionLevel, p.ullChampionExp,
				p.ullChampionItemExp, p.dwChampionRes, p.dwChampionBlockPen, p.dwChampionPrecision, p.dwChampionResApply,
				p.dwChampionBlockPenApply, p.dwChampionPrecisionApply,
				p.aPotential[0].dwEggVnum, (unsigned)p.aPotential[0].bSkill, p.aPotential[0].dwEndTime,
				p.aPotential[1].dwEggVnum, (unsigned)p.aPotential[1].bSkill, p.aPotential[1].dwEndTime);
		return q;
	}

	void FlushOne(SPetCache& c, bool bDirect)
	{
		if (c.deleted)
		{
			char q[128];
			snprintf(q, sizeof(q), "DELETE FROM growth_pet%s WHERE id=%u", GetTablePostfix(), c.data.dwID);
			if (bDirect)
				CDBManager::instance().DirectQuery(q);
			else
				CDBManager::instance().AsyncQuery(q);
		}
		else
		{
			const std::string q = SaveQuery(c.data);
			if (bDirect)
				CDBManager::instance().DirectQuery(q.c_str());
			else
				CDBManager::instance().AsyncQuery(q.c_str());
		}
		c.dirty = false;
	}

	void SplitCsv(const char* s, std::vector<long long>& out)
	{
		out.clear();
		if (!s)
			return;
		const char* p = s;
		while (*p)
		{
			char* end = NULL;
			const long long v = strtoll(p, &end, 10);
			if (end == p)
				break;
			out.push_back(v);
			p = end;
			while (*p == ',' || *p == ' ')
				++p;
		}
	}
}

// ---- boot: the skill proto -----------------------------------------------------------------------------------------

bool GrowthPetDBLoadSkillTable()
{
	char q[1024];
	snprintf(q, sizeof(q),
			"SELECT pet_vnum, skill_vnum, name, type+0, cooldown, point_on, unit, value_t1, value_t2, value_t3, value_t4, "
			"value_t5, value_t6, value_t7, value_t8, level_curve, grow_levels, activate, duration FROM growth_pet_skill_proto%s",
			GetTablePostfix());
	std::unique_ptr<SQLMsg> msg(CDBManager::instance().DirectQuery(q));
	s_vecSkillTable.clear();
	if (!msg.get() || !msg->Get() || !msg->Get()->pSQLResult)
	{
		// No table yet (apply.sh did not run): the pets work without skills; the game says so in its log.
		sys_err("GROWTH_PET: growth_pet_skill_proto%s not readable - no pet skills", GetTablePostfix());
		return true;
	}
	MYSQL_ROW row;
	std::vector<long long> v;
	while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
	{
		TGrowthPetSkillTable t;
		memset(&t, 0, sizeof(t));
		int c = 0;
		t.dwPetVnum = ToDW(row[c++]);
		t.bSkill = (BYTE)ToDW(row[c++]);
		strlcpy(t.szName, row[c] ? row[c] : "", sizeof(t.szName));
		++c;
		t.bType = (BYTE)ToDW(row[c++]);
		t.dwCooldown = ToDW(row[c++]);
		strlcpy(t.szPointOn, row[c] ? row[c] : "", sizeof(t.szPointOn));
		++c;
		strlcpy(t.szUnit, row[c] ? row[c] : "", sizeof(t.szUnit));
		++c;
		for (int i = 0; i < 8; ++i)
			t.adwValue[i] = ToDW(row[c++]);
		SplitCsv(row[c++], v);
		for (size_t i = 0; i < v.size() && i < 20; ++i)
			t.adwCurve[i] = (DWORD)MAX(0LL, v[i]);
		SplitCsv(row[c++], v);
		for (size_t i = 0; i < v.size() && i < 7; ++i)
			t.abGrowLevel[i] = (BYTE)MINMAX(0LL, v[i], 255LL);
		SplitCsv(row[c++], v);
		for (size_t i = 0; i < v.size() && i < 20; ++i)
			t.abActivate[i] = (BYTE)MINMAX(0LL, v[i], 100LL);
		SplitCsv(row[c++], v);
		for (size_t i = 0; i < v.size() && i < 20; ++i)
			t.abDuration[i] = (BYTE)MINMAX(0LL, v[i], 255LL);
		if (!t.bSkill)
			continue;
		s_vecSkillTable.push_back(t);
	}
	sys_log(0, "GROWTH_PET: %u skill proto rows", (unsigned)s_vecSkillTable.size());
	return true;
}

// Right after the boot packet (and the Ikarus shop table) to a core that just booted.
void GrowthPetDBSendSkillTable(CPeer* peer)
{
	if (!peer)
		return;
	if (s_vecSkillTable.empty())
		GrowthPetDBLoadSkillTable();
	const WORD wCount = (WORD)MIN((size_t)0xFFFF, s_vecSkillTable.size());
	peer->EncodeHeader(HEADER_DG_GROWTH_PET_SKILL_TABLE, 0, sizeof(WORD) + sizeof(WORD) + sizeof(TGrowthPetSkillTable) * wCount);
	peer->EncodeWORD(sizeof(TGrowthPetSkillTable));
	peer->EncodeWORD(wCount);
	if (wCount)
		peer->Encode(&s_vecSkillTable[0], sizeof(TGrowthPetSkillTable) * wCount);
}

// ---- the pets -----------------------------------------------------------------------------------------------------

static void SendLoad(CPeer* peer, DWORD dwHandle, const TPacketGDGrowthPetLoad& req, const std::vector<TGrowthPet>& pets)
{
	TPacketDGGrowthPetLoad head;
	head.dwPID = req.dwPID;
	head.bReason = req.bReason;
	head.dwParam = req.dwParam;
	head.wCount = (WORD)MIN((size_t)GROWTH_PET_LOAD_MAX, pets.size());
	peer->EncodeHeader(HEADER_DG_GROWTH_PET_LOAD, dwHandle, sizeof(head) + sizeof(TGrowthPet) * head.wCount);
	peer->Encode(&head, sizeof(head));
	if (head.wCount)
		peer->Encode(&pets[0], sizeof(TGrowthPet) * head.wCount);
}

static void QueryLoad(CPeer* peer, DWORD dwHandle, const TPacketGDGrowthPetLoad* p)
{
	std::vector<TGrowthPet> pets;
	const time_t now = time(0);
	char q[2048];

	if (p->bReason == GROWTH_PET_LOAD_PENDING)
	{
		// the old-system pets waiting for their seals: only from the table (a pending row is never cached)
		snprintf(q, sizeof(q), "SELECT %s FROM growth_pet%s WHERE owner_id=%u AND state=%u LIMIT %u", SELECT_COLUMNS,
				GetTablePostfix(), p->dwPID, (unsigned)GROWTH_PET_STATE_PENDING, (unsigned)GROWTH_PET_LOAD_MAX);
		std::unique_ptr<SQLMsg> msg(CDBManager::instance().DirectQuery(q));
		if (msg.get() && msg->Get() && msg->Get()->pSQLResult)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				TGrowthPet pet;
				ReadRow(row, mysql_fetch_lengths(msg->Get()->pSQLResult), pet);
				// a pet in the cache (it got its seal meanwhile) is not pending any more
				std::map<DWORD, SPetCache>::const_iterator it = s_mapPets.find(pet.dwID);
				if (it != s_mapPets.end())
					continue;
				pets.push_back(pet);
			}
		}
		SendLoad(peer, dwHandle, *p, pets);
		return;
	}

	std::string missing;
	const BYTE bCount = MIN(p->bCount, (BYTE)GROWTH_PET_LOAD_MAX);
	std::set<DWORD> seen;
	for (BYTE i = 0; i < bCount; ++i)
	{
		const DWORD id = p->adwID[i];
		if (!id || !seen.insert(id).second)
			continue;
		std::map<DWORD, SPetCache>::iterator it = s_mapPets.find(id);
		if (it != s_mapPets.end())
		{
			it->second.used = now;
			if (!it->second.deleted)
				pets.push_back(it->second.data);
			continue;
		}
		char part[16];
		snprintf(part, sizeof(part), "%s%u", missing.empty() ? "" : ",", id);
		missing += part;
	}
	if (!missing.empty())
	{
		snprintf(q, sizeof(q), "SELECT %s FROM growth_pet%s WHERE id IN (%s)", SELECT_COLUMNS, GetTablePostfix(),
				missing.c_str());
		std::unique_ptr<SQLMsg> msg(CDBManager::instance().DirectQuery(q));
		if (msg.get() && msg->Get() && msg->Get()->pSQLResult)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				TGrowthPet pet;
				ReadRow(row, mysql_fetch_lengths(msg->Get()->pSQLResult), pet);
				SPetCache& c = s_mapPets[pet.dwID];
				c.data = pet;
				c.dirty = false;
				c.deleted = false;
				c.changed = now;
				c.used = now;
				pets.push_back(pet);
			}
		}
	}
	SendLoad(peer, dwHandle, *p, pets);
}

// ClientManager::ProcessPackets: GD 147 / 148 / 149. True when the header was ours.
bool GrowthPetDBPacket(CPeer* peer, DWORD dwHandle, BYTE bHeader, const char* data, DWORD dwLength)
{
	const time_t now = time(0);
	switch (bHeader)
	{
		case HEADER_GD_GROWTH_PET_SAVE:
		{
			if (dwLength < sizeof(TGrowthPet))
			{
				sys_err("GROWTH_PET: save packet %u < %u", dwLength, (unsigned)sizeof(TGrowthPet));
				return true;
			}
			const TGrowthPet* p = (const TGrowthPet*)data;
			if (!p->dwID)
				return true;
			SPetCache& c = s_mapPets[p->dwID];
			c.data = *p;
			c.data.szName[GROWTH_PET_NAME_MAX] = '\0';
			c.dirty = true;
			c.deleted = false;
			c.changed = now;
			c.used = now;
			// a pet leaving its pending state, or packed into a cage, is written at once: the next core asking for it
			// may be another process's reader of the table (the panel), and a cage may travel far
			if (p->bState == GROWTH_PET_STATE_BAG)
				FlushOne(c, false);
			return true;
		}
		case HEADER_GD_GROWTH_PET_DELETE:
		{
			if (dwLength < sizeof(TPacketGDGrowthPetDelete))
				return true;
			const TPacketGDGrowthPetDelete* p = (const TPacketGDGrowthPetDelete*)data;
			if (!p->dwID)
				return true;
			SPetCache& c = s_mapPets[p->dwID];
			c.data.dwID = p->dwID;
			c.deleted = true;
			c.dirty = true;
			c.changed = now;
			c.used = now;
			FlushOne(c, false);
			return true;
		}
		case HEADER_GD_GROWTH_PET_LOAD:
		{
			if (dwLength < sizeof(TPacketGDGrowthPetLoad))
				return true;
			QueryLoad(peer, dwHandle, (const TPacketGDGrowthPetLoad*)data);
			return true;
		}
	}
	return false;
}

// The main loop, beside UpdateItemCache: the saves older than GROWTH_PET_FLUSH_SECONDS, and the entries nobody used
// for GROWTH_PET_FORGET_SECONDS forgotten.
void GrowthPetDBUpdate()
{
	const time_t now = time(0);
	int flushed = 0;
	for (std::map<DWORD, SPetCache>::iterator it = s_mapPets.begin(); it != s_mapPets.end(); )
	{
		SPetCache& c = it->second;
		if (c.dirty && now - c.changed >= GROWTH_PET_FLUSH_SECONDS && flushed < GROWTH_PET_FLUSH_PER_PULSE)
		{
			FlushOne(c, false);
			++flushed;
		}
		if (!c.dirty && now - c.used >= GROWTH_PET_FORGET_SECONDS)
		{
			s_mapPets.erase(it++);
			continue;
		}
		++it;
	}
}

// MainLoop's end (shutdown): every unsaved pet written now.
void GrowthPetDBFlushAll()
{
	int n = 0;
	for (std::map<DWORD, SPetCache>::iterator it = s_mapPets.begin(); it != s_mapPets.end(); ++it)
		if (it->second.dirty)
		{
			FlushOne(it->second, true);
			++n;
		}
	s_mapPets.clear();
	sys_log(0, "GROWTH_PET: %d pet(s) written at shutdown", n);
}
