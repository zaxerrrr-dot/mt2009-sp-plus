/**
* MT2009_PLUS_WIKI_V1 - the in-game wiki's data (python module "wikipedia"; the owner's Valiant2 wiki package,
* PythonWiki.cpp, rebuilt). Valiant2's PythonWiki.cpp read item_proto itself and kept every list in the exe
* (bossChests, dungeonChests, cubeNpcVnums*, m_CostumeData, dungeonMobMap, a "+9" name test for the refine level...).
* Here every list comes from the files OUR server data generates (client-patches/client-2.0.30/tools/wikiv2/
* gen_wiki_data.py -> locale/common/wiki/{items,mobs,chests,crafting}.txt in the locale pack): the refine chains and
* steps (item_proto refined_vnum / refine_set, refine_proto), the drop rows with the chance the server works out, the
* chests' contents, the cube recipes and where their NPCs stand, the monsters' stats and places. So a release that
* changes the server data only re-runs the generator. Fixed on the way (the package's README list): the job flags
* (sura bit 2, shaman bit 3 - Valiant2 swapped them), sCube::resetAllData (memset of a pointer's size over a vector),
* the +9-name refine test, ENABLE_INGAME_WIKI / SelectByNamePart, the "encrypted" drop files (plain numbers now).
*
* Files: CP1250, one record a line, TAB between fields, '#' a comment (the formats: gen_wiki_data.py's header). Read
* once, on the first wikipedia.Load() (the window's first opening).
*
*   Load() -> 1/0            IsLoaded()
*   GetEquipList(cat, jobmask) -> [(v0, level, jobmask)]        GetChain(v) -> (v0, v1, ...)
*   GetRefineStep(v) -> (to, cost, prob, ((mat, count, last), ...)) | None   (last > mat: any one of mat..last)      GetRefineFrom(v) -> from | 0
*   GetCostumeList(cat) -> [(vnum, preview)]                    GetCostumeInfo(v) -> (cat, preview) | None
*   GetMobCategories() -> [(id, group, label)]                  GetMobCategory(id) -> [mob]
*   GetMobStats(mob) -> (level, rank, type, hp, exp, dmgMin, dmgMax, def, goldMin, goldMax, raceFlag, immuneFlag,
*                        aiFlag, (11 resists), (6 elements)) | None
*   GetMobDrops(mob) / GetItemMobs(item) -> [(item | mob, countMin, countMax, chance)]   chance: 100000000 = 100%
*   GetMobPlaces(mob) -> [(map, kind)]                          GetMapName(map) -> str
*   GetChestCategories() -> [(id, label)]   GetChestCategory(id) -> [(chest, fromMob)]
*   GetChestContent(chest) / GetItemChests(item) -> [(item | chest, countMin, countMax, chance)]
*   GetCraftNpcs() -> [(npc, label)]        GetNpcLocations(npc) -> [(map, x, y)]
*   GetNpcCubes(npc) / GetItemCubeSources(item) / GetItemCubeUses(item) -> [recipe]
*   GetCube(recipe) -> ((npc, ...), kind, result, count, gold, percent, ((mat, count, last), ...)) | None
*   GetItemRefineUses(item) -> [(from, count)]  GetItemShops(item) -> [(npc, price, count)]  GetItemNotes(item) -> [str]
*   SearchItems(text, max) / SearchMobs(text, max) -> [vnum]    (case and Polish letters ignored, a number = a vnum)
*   ItemExists(vnum) / MobExists(vnum) -> 1/0                   (the client's item_proto / mob_proto has it)
*   app.ENABLE_WIKI = 1
**/

#include "StdAfx.h"

#ifdef ENABLE_MT2009_WIKI
#include "../EterPack/EterPackManager.h"
#include "../GameLib/ItemManager.h"
#include "../GameLib/ItemData.h"
#include "PythonNonPlayer.h"

#include <algorithm>
#include <cstdlib>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace
{
	const char* WIKI_DIR = "locale/common/wiki/";
	const int EQUIP_CATEGORIES = 16;
	const int COSTUME_CATEGORIES = 16;

	typedef std::vector<std::string> TTokens;
	struct SMat
	{
		DWORD dwVnum;
		int iCount;
		DWORD dwLast;	// a range "a-b:c": c of any one of a..b (Mnich Milbon's exchanges); else = dwVnum
	};
	typedef std::vector<SMat> TMaterials;

	struct SRow
	{
		DWORD dwVnum;
		int iMin;
		int iMax;
		DWORD dwChance;
	};

	struct SEquip
	{
		DWORD dwVnum;
		int iLevel;
		int iJobMask;
	};

	struct SStep
	{
		DWORD dwTo;
		long long llCost;
		int iProb;
		TMaterials kMats;
	};

	struct SCube
	{
		std::vector<DWORD> kNpcs;
		int iKind;
		DWORD dwResult;
		int iCount;
		long long llGold;
		int iPercent;
		TMaterials kMats;
	};

	struct SShop
	{
		DWORD dwNpc;
		long long llPrice;
		int iCount;
	};

	struct SLoc
	{
		DWORD dwMap;
		int iX;
		int iY;
	};

	struct SWikiData
	{
		bool bLoaded;
		bool bTried;
		std::vector<SEquip> akEquip[EQUIP_CATEGORIES];
		std::vector<std::vector<DWORD> > kChains;
		std::map<DWORD, size_t> kChainOf;
		std::map<DWORD, SStep> kSteps;
		std::map<DWORD, DWORD> kStepFrom;
		std::map<DWORD, std::vector<std::pair<DWORD, int> > > kRefineUses;
		std::vector<std::pair<DWORD, DWORD> > akCostumes[COSTUME_CATEGORIES];
		std::map<DWORD, std::pair<int, DWORD> > kCostumeOf;
		std::map<DWORD, std::vector<SShop> > kShops;
		std::map<DWORD, std::vector<std::string> > kNotes;
		std::map<DWORD, std::string> kMapNames;
		std::vector<std::pair<int, std::pair<int, std::string> > > kMobCats;
		std::map<int, std::vector<DWORD> > kMobCatList;
		std::map<DWORD, std::vector<long long> > kMobStats;
		std::map<DWORD, std::vector<SRow> > kMobDrops;
		std::map<DWORD, std::vector<SRow> > kItemMobs;
		std::map<DWORD, std::vector<std::pair<DWORD, int> > > kMobPlaces;
		std::vector<std::pair<int, std::string> > kChestCats;
		std::map<int, std::vector<std::pair<DWORD, DWORD> > > kChestCatList;
		std::map<DWORD, std::vector<SRow> > kChestContent;
		std::map<DWORD, std::vector<SRow> > kItemChests;
		std::vector<std::pair<DWORD, std::string> > kCraftNpcs;
		std::map<DWORD, std::vector<SLoc> > kNpcLocs;
		std::vector<SCube> kCubes;
		std::map<DWORD, std::vector<int> > kNpcCubes;
		std::map<DWORD, std::vector<int> > kItemCubeSources;
		std::map<DWORD, std::vector<int> > kItemCubeUses;

		SWikiData() : bLoaded(false), bTried(false) {}
	};

	SWikiData s_kWiki;

	// ------------------------------------------------------------------------------------------------- reading

	long long ToLL(const std::string& s)		{ return _atoi64(s.c_str()); }
	int ToInt(const std::string& s)				{ return atoi(s.c_str()); }
	DWORD ToDword(const std::string& s)			{ return DWORD(strtoul(s.c_str(), NULL, 10)); }

	void Split(const std::string& s, char c, TTokens& out)
	{
		out.clear();
		size_t start = 0;
		while (true)
		{
			const size_t pos = s.find(c, start);
			if (pos == std::string::npos)
			{
				out.push_back(s.substr(start));
				return;
			}
			out.push_back(s.substr(start, pos - start));
			start = pos + 1;
		}
	}

	// "v:c,v:c" ("-" = none); "a-b:c" = c of any one of a..b
	void ParseMaterials(const std::string& s, TMaterials& out)
	{
		out.clear();
		if (s.empty() || s == "-")
			return;
		TTokens kParts, kPair;
		Split(s, ',', kParts);
		for (size_t i = 0; i < kParts.size(); ++i)
		{
			Split(kParts[i], ':', kPair);
			if (kPair.size() < 2)
				continue;
			SMat m;
			m.dwVnum = ToDword(kPair[0]);
			const size_t dash = kPair[0].find('-');
			m.dwLast = dash != std::string::npos ? ToDword(kPair[0].substr(dash + 1)) : m.dwVnum;
			if (m.dwLast < m.dwVnum)
				m.dwLast = m.dwVnum;
			m.iCount = ToInt(kPair[1]);
			if (m.dwVnum)
				out.push_back(m);
		}
	}

	template <typename F>
	bool ReadFile(const char* c_szName, F fnLine)
	{
		std::string strPath = std::string(WIKI_DIR) + c_szName;
		CMappedFile kFile;
		LPCVOID pData = NULL;
		if (!CEterPackManager::Instance().Get(kFile, strPath.c_str(), &pData) || !pData)
		{
			TraceError("wikipedia: %s not found", strPath.c_str());
			return false;
		}
		const char* p = static_cast<const char*>(pData);
		const size_t size = kFile.Size();
		TTokens kTok;
		size_t start = 0;
		while (start < size)
		{
			size_t end = start;
			while (end < size && p[end] != '\n')
				++end;
			std::string strLine(p + start, end - start);
			start = end + 1;
			if (!strLine.empty() && strLine[strLine.size() - 1] == '\r')
				strLine.erase(strLine.size() - 1);
			if (strLine.empty() || strLine[0] == '#')
				continue;
			Split(strLine, '\t', kTok);
			if (kTok.size() < 2)
				continue;
			fnLine(kTok);
		}
		return true;
	}

	void AddRow(std::vector<SRow>& rv, DWORD dwVnum, int iMin, int iMax, DWORD dwChance)
	{
		SRow r;
		r.dwVnum = dwVnum;
		r.iMin = iMin;
		r.iMax = iMax;
		r.dwChance = dwChance;
		rv.push_back(r);
	}

	bool ByChance(const SRow& a, const SRow& b)
	{
		if (a.dwChance != b.dwChance)
			return a.dwChance > b.dwChance;
		return a.dwVnum < b.dwVnum;
	}

	bool ByLevel(const SEquip& a, const SEquip& b)
	{
		if (a.iLevel != b.iLevel)
			return a.iLevel < b.iLevel;
		return a.dwVnum < b.dwVnum;
	}

	void LoadItems()
	{
		SWikiData& w = s_kWiki;
		ReadFile("items.txt", [&w](const TTokens& t)
		{
			const std::string& tag = t[0];
			if (tag == "EQ" && t.size() >= 5)
			{
				const int iCat = ToInt(t[1]);
				if (iCat < 0 || iCat >= EQUIP_CATEGORIES)
					return;
				SEquip e;
				e.iJobMask = ToInt(t[2]);
				e.iLevel = ToInt(t[3]);
				e.dwVnum = ToDword(t[4]);
				w.akEquip[iCat].push_back(e);
			}
			else if (tag == "CH")
			{
				std::vector<DWORD> kChain;
				for (size_t i = 1; i < t.size(); ++i)
					if (DWORD v = ToDword(t[i]))
						kChain.push_back(v);
				if (kChain.empty())
					return;
				const size_t idx = w.kChains.size();
				for (size_t i = 0; i < kChain.size(); ++i)
					if (w.kChainOf.find(kChain[i]) == w.kChainOf.end())
						w.kChainOf[kChain[i]] = idx;
				w.kChains.push_back(kChain);
			}
			else if (tag == "RS" && t.size() >= 6)
			{
				SStep s;
				const DWORD dwFrom = ToDword(t[1]);
				s.dwTo = ToDword(t[2]);
				s.llCost = ToLL(t[3]);
				s.iProb = ToInt(t[4]);
				ParseMaterials(t[5], s.kMats);
				w.kSteps[dwFrom] = s;
				if (s.dwTo)
					w.kStepFrom[s.dwTo] = dwFrom;
				for (size_t i = 0; i < s.kMats.size(); ++i)
					w.kRefineUses[s.kMats[i].dwVnum].push_back(std::make_pair(dwFrom, s.kMats[i].iCount));
			}
			else if (tag == "CO" && t.size() >= 3)
			{
				const int iCat = ToInt(t[1]);
				if (iCat < 0 || iCat >= COSTUME_CATEGORIES)
					return;
				const DWORD dwVnum = ToDword(t[2]);
				const DWORD dwPreview = t.size() >= 4 ? ToDword(t[3]) : 0;
				w.akCostumes[iCat].push_back(std::make_pair(dwVnum, dwPreview));
				w.kCostumeOf[dwVnum] = std::make_pair(iCat, dwPreview);
			}
			else if (tag == "SHOP" && t.size() >= 5)
			{
				SShop s;
				s.dwNpc = ToDword(t[1]);
				s.llPrice = ToLL(t[3]);
				s.iCount = ToInt(t[4]);
				w.kShops[ToDword(t[2])].push_back(s);
			}
			else if (tag == "SRC" && t.size() >= 3)
				w.kNotes[ToDword(t[1])].push_back(t[2]);
		});
		for (int i = 0; i < EQUIP_CATEGORIES; ++i)
			std::stable_sort(w.akEquip[i].begin(), w.akEquip[i].end(), ByLevel);
	}

	void LoadMobs()
	{
		SWikiData& w = s_kWiki;
		ReadFile("mobs.txt", [&w](const TTokens& t)
		{
			const std::string& tag = t[0];
			if (tag == "MAP" && t.size() >= 3)
				w.kMapNames[ToDword(t[1])] = t[2];
			else if (tag == "MCAT" && t.size() >= 4)
				w.kMobCats.push_back(std::make_pair(ToInt(t[1]), std::make_pair(ToInt(t[2]), t[3])));
			else if (tag == "MC" && t.size() >= 3)
				w.kMobCatList[ToInt(t[1])].push_back(ToDword(t[2]));
			else if (tag == "MS" && t.size() >= 15)
			{
				std::vector<long long>& v = w.kMobStats[ToDword(t[1])];
				v.clear();
				for (size_t i = 2; i <= 14; ++i)
					v.push_back(ToLL(t[i]));
				TTokens kList;
				for (size_t k = 15; k <= 16; ++k)
				{
					const size_t want = k == 15 ? 11 : 6;
					if (t.size() > k)
						Split(t[k], ',', kList);
					else
						kList.clear();
					for (size_t i = 0; i < want; ++i)
						v.push_back(i < kList.size() ? ToLL(kList[i]) : 0);
				}
			}
			else if (tag == "MD" && t.size() >= 6)
			{
				const DWORD dwMob = ToDword(t[1]), dwItem = ToDword(t[2]);
				const int iMin = ToInt(t[3]), iMax = ToInt(t[4]);
				const DWORD dwChance = ToDword(t[5]);
				AddRow(w.kMobDrops[dwMob], dwItem, iMin, iMax, dwChance);
				AddRow(w.kItemMobs[dwItem], dwMob, iMin, iMax, dwChance);
			}
			else if (tag == "MP" && t.size() >= 4)
				w.kMobPlaces[ToDword(t[1])].push_back(std::make_pair(ToDword(t[2]), ToInt(t[3])));
		});
		for (std::map<DWORD, std::vector<SRow> >::iterator it = w.kItemMobs.begin(); it != w.kItemMobs.end(); ++it)
			std::stable_sort(it->second.begin(), it->second.end(), ByChance);
		for (std::map<DWORD, std::vector<SRow> >::iterator it = w.kMobDrops.begin(); it != w.kMobDrops.end(); ++it)
			std::stable_sort(it->second.begin(), it->second.end(), ByChance);
	}

	void LoadChests()
	{
		SWikiData& w = s_kWiki;
		ReadFile("chests.txt", [&w](const TTokens& t)
		{
			const std::string& tag = t[0];
			if (tag == "CCAT" && t.size() >= 3)
				w.kChestCats.push_back(std::make_pair(ToInt(t[1]), t[2]));
			else if (tag == "CL" && t.size() >= 4)
				w.kChestCatList[ToInt(t[1])].push_back(std::make_pair(ToDword(t[2]), ToDword(t[3])));
			else if (tag == "CC" && t.size() >= 6)
			{
				const DWORD dwChest = ToDword(t[1]), dwItem = ToDword(t[2]);
				const int iMin = ToInt(t[3]), iMax = ToInt(t[4]);
				const DWORD dwChance = ToDword(t[5]);
				AddRow(w.kChestContent[dwChest], dwItem, iMin, iMax, dwChance);
				AddRow(w.kItemChests[dwItem], dwChest, iMin, iMax, dwChance);
			}
		});
		for (std::map<DWORD, std::vector<SRow> >::iterator it = w.kItemChests.begin(); it != w.kItemChests.end(); ++it)
			std::stable_sort(it->second.begin(), it->second.end(), ByChance);
	}

	void LoadCrafting()
	{
		SWikiData& w = s_kWiki;
		ReadFile("crafting.txt", [&w](const TTokens& t)
		{
			const std::string& tag = t[0];
			if (tag == "NPC" && t.size() >= 2)
				w.kCraftNpcs.push_back(std::make_pair(ToDword(t[1]), t.size() >= 3 && t[2] != "-" ? t[2] : std::string()));
			else if (tag == "LOC" && t.size() >= 5)
			{
				SLoc l;
				l.dwMap = ToDword(t[2]);
				l.iX = ToInt(t[3]);
				l.iY = ToInt(t[4]);
				w.kNpcLocs[ToDword(t[1])].push_back(l);
			}
			else if (tag == "CUBE" && t.size() >= 8)
			{
				SCube c;
				TTokens kNpcs;
				Split(t[1], ',', kNpcs);
				for (size_t i = 0; i < kNpcs.size(); ++i)
					if (DWORD n = ToDword(kNpcs[i]))
						c.kNpcs.push_back(n);
				c.iKind = ToInt(t[2]);
				c.dwResult = ToDword(t[3]);
				c.iCount = ToInt(t[4]);
				c.llGold = ToLL(t[5]);
				c.iPercent = ToInt(t[6]);
				ParseMaterials(t[7], c.kMats);
				const int idx = int(w.kCubes.size());
				w.kCubes.push_back(c);
				for (size_t i = 0; i < c.kNpcs.size(); ++i)
					w.kNpcCubes[c.kNpcs[i]].push_back(idx);
				w.kItemCubeSources[c.dwResult].push_back(idx);
				std::set<DWORD> kSeen;
				for (size_t i = 0; i < c.kMats.size(); ++i)
					for (DWORD v = c.kMats[i].dwVnum; v <= c.kMats[i].dwLast && v - c.kMats[i].dwVnum < 200; ++v)
						if (kSeen.insert(v).second)
							w.kItemCubeUses[v].push_back(idx);
			}
		});
	}

	bool Load()
	{
		if (s_kWiki.bTried)
			return s_kWiki.bLoaded;
		s_kWiki.bTried = true;
		const DWORD dwStart = ELTimer_GetMSec();
		LoadItems();
		LoadMobs();
		LoadChests();
		LoadCrafting();
		s_kWiki.bLoaded = !s_kWiki.kChains.empty() || !s_kWiki.kMobDrops.empty();
		TraceError("wikipedia: loaded in %u ms - %u chains, %u steps, %u mobs with drops, %u chests, %u recipes",
			ELTimer_GetMSec() - dwStart, (unsigned) s_kWiki.kChains.size(), (unsigned) s_kWiki.kSteps.size(),
			(unsigned) s_kWiki.kMobDrops.size(), (unsigned) s_kWiki.kChestContent.size(), (unsigned) s_kWiki.kCubes.size());
		return s_kWiki.bLoaded;
	}

	// ------------------------------------------------------------------------------------------------- search

	// lower case, Polish letters (CP1250) to plain ones
	std::string Fold(const char* c_szText)
	{
		static const struct { unsigned char code; char plain; } s_aCp1250[] =
		{
			{ 0xB9, 'a' }, { 0xA5, 'a' }, { 0xE6, 'c' }, { 0xC6, 'c' }, { 0xEA, 'e' }, { 0xCA, 'e' },
			{ 0xB3, 'l' }, { 0xA3, 'l' }, { 0xF1, 'n' }, { 0xD1, 'n' }, { 0xF3, 'o' }, { 0xD3, 'o' },
			{ 0x9C, 's' }, { 0x8C, 's' }, { 0x9F, 'z' }, { 0x8F, 'z' }, { 0xBF, 'z' }, { 0xAF, 'z' },
		};
		std::string out;
		for (const unsigned char* p = (const unsigned char*) (c_szText ? c_szText : ""); *p; ++p)
		{
			if (*p < 0x80)
			{
				out += (char) tolower(*p);
				continue;
			}
			char plain = 0;
			for (size_t i = 0; i < _countof(s_aCp1250); ++i)
				if (s_aCp1250[i].code == *p)
				{
					plain = s_aCp1250[i].plain;
					break;
				}
			out += plain ? plain : (char) *p;
		}
		return out;
	}

	// a name without its "+N" ending
	std::string BaseName(const std::string& name)
	{
		const size_t pos = name.rfind('+');
		if (pos != std::string::npos && pos > 0 && pos + 1 < name.size() && isdigit((unsigned char) name[pos + 1]))
		{
			size_t end = pos;
			while (end > 0 && name[end - 1] == ' ')
				--end;
			return name.substr(0, end);
		}
		return name;
	}

	// 0 the whole name, 1 its start, 2 a word's start, 3 anywhere; -1 not in it
	int Score(const std::string& name, const std::string& query)
	{
		const size_t pos = name.find(query);
		if (pos == std::string::npos)
			return -1;
		if (name == query)
			return 0;
		if (pos == 0)
			return 1;
		const char c = name[pos - 1];
		if (c == ' ' || c == '(' || c == '-')
			return 2;
		return 3;
	}

	struct SMatch
	{
		int iScore;
		size_t length;
		DWORD dwVnum;
		bool operator<(const SMatch& o) const
		{
			if (iScore != o.iScore)
				return iScore < o.iScore;
			if (length != o.length)
				return length < o.length;
			return dwVnum < o.dwVnum;
		}
	};

	bool HasItemInfo(DWORD dwVnum)
	{
		const SWikiData& w = s_kWiki;
		return w.kChainOf.count(dwVnum) || w.kItemMobs.count(dwVnum) || w.kItemChests.count(dwVnum) ||
			w.kItemCubeSources.count(dwVnum) || w.kItemCubeUses.count(dwVnum) || w.kChestContent.count(dwVnum) ||
			w.kShops.count(dwVnum) || w.kNotes.count(dwVnum) || w.kRefineUses.count(dwVnum) || w.kCostumeOf.count(dwVnum);
	}

	// the first item of a refine chain stands for the whole chain
	DWORD ChainHead(DWORD dwVnum)
	{
		std::map<DWORD, size_t>::const_iterator it = s_kWiki.kChainOf.find(dwVnum);
		if (it == s_kWiki.kChainOf.end())
			return dwVnum;
		return s_kWiki.kChains[it->second].front();
	}

	// ------------------------------------------------------------------------------------------------- python

	PyObject* RowList(const std::vector<SRow>* pv)
	{
		PyObject* poList = PyList_New(0);
		if (pv)
			for (size_t i = 0; i < pv->size(); ++i)
			{
				const SRow& r = (*pv)[i];
				PyObject* po = Py_BuildValue("(iiii)", int(r.dwVnum), r.iMin, r.iMax, int(r.dwChance));
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* IntList(const std::vector<int>* pv)
	{
		PyObject* poList = PyList_New(0);
		if (pv)
			for (size_t i = 0; i < pv->size(); ++i)
			{
				PyObject* po = PyInt_FromLong((*pv)[i]);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* MaterialTuple(const TMaterials& kMats)
	{
		PyObject* poTuple = PyTuple_New(kMats.size());
		for (size_t i = 0; i < kMats.size(); ++i)
			PyTuple_SetItem(poTuple, i, Py_BuildValue("(iii)", int(kMats[i].dwVnum), kMats[i].iCount, int(kMats[i].dwLast)));
		return poTuple;
	}

	template <typename M>
	const typename M::mapped_type* Find(const M& m, DWORD k)
	{
		typename M::const_iterator it = m.find(k);
		return it == m.end() ? NULL : &it->second;
	}

	DWORD ArgVnum(PyObject* poArgs, int iPos = 0)
	{
		int iValue = 0;
		if (!PyTuple_GetInteger(poArgs, iPos, &iValue))
			return 0;
		return DWORD(iValue);
	}

	PyObject* wikiLoad(PyObject* poSelf, PyObject* poArgs)		{ return Py_BuildValue("i", Load() ? 1 : 0); }
	PyObject* wikiIsLoaded(PyObject* poSelf, PyObject* poArgs)	{ return Py_BuildValue("i", s_kWiki.bLoaded ? 1 : 0); }

	PyObject* wikiGetEquipList(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		int iCat = 0, iJobMask = 0;
		PyTuple_GetInteger(poArgs, 0, &iCat);
		PyTuple_GetInteger(poArgs, 1, &iJobMask);
		PyObject* poList = PyList_New(0);
		if (iCat >= 0 && iCat < EQUIP_CATEGORIES)
			for (size_t i = 0; i < s_kWiki.akEquip[iCat].size(); ++i)
			{
				const SEquip& e = s_kWiki.akEquip[iCat][i];
				if (iJobMask && !(e.iJobMask & iJobMask))
					continue;
				PyObject* po = Py_BuildValue("(iii)", int(e.dwVnum), e.iLevel, e.iJobMask);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetChain(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const DWORD dwVnum = ArgVnum(poArgs);
		std::map<DWORD, size_t>::const_iterator it = s_kWiki.kChainOf.find(dwVnum);
		if (it == s_kWiki.kChainOf.end())
			return Py_BuildValue("(i)", int(dwVnum));
		const std::vector<DWORD>& c = s_kWiki.kChains[it->second];
		PyObject* poTuple = PyTuple_New(c.size());
		for (size_t i = 0; i < c.size(); ++i)
			PyTuple_SetItem(poTuple, i, PyInt_FromLong(long(c[i])));
		return poTuple;
	}

	PyObject* wikiGetRefineStep(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const SStep* p = Find(s_kWiki.kSteps, ArgVnum(poArgs));
		if (!p)
			return Py_BuildNone();
		return Py_BuildValue("(iLiN)", int(p->dwTo), p->llCost, p->iProb, MaterialTuple(p->kMats));
	}

	PyObject* wikiGetRefineFrom(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const DWORD* p = Find(s_kWiki.kStepFrom, ArgVnum(poArgs));
		return Py_BuildValue("i", p ? int(*p) : 0);
	}

	PyObject* wikiGetCostumeList(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		int iCat = 0;
		PyTuple_GetInteger(poArgs, 0, &iCat);
		PyObject* poList = PyList_New(0);
		if (iCat >= 0 && iCat < COSTUME_CATEGORIES)
			for (size_t i = 0; i < s_kWiki.akCostumes[iCat].size(); ++i)
			{
				PyObject* po = Py_BuildValue("(ii)", int(s_kWiki.akCostumes[iCat][i].first), int(s_kWiki.akCostumes[iCat][i].second));
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetCostumeInfo(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const std::pair<int, DWORD>* p = Find(s_kWiki.kCostumeOf, ArgVnum(poArgs));
		if (!p)
			return Py_BuildNone();
		return Py_BuildValue("(ii)", p->first, int(p->second));
	}

	PyObject* wikiGetMobCategories(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		for (size_t i = 0; i < s_kWiki.kMobCats.size(); ++i)
		{
			PyObject* po = Py_BuildValue("(iis)", s_kWiki.kMobCats[i].first, s_kWiki.kMobCats[i].second.first,
				s_kWiki.kMobCats[i].second.second.c_str());
			PyList_Append(poList, po);
			Py_DECREF(po);
		}
		return poList;
	}

	PyObject* wikiGetMobCategory(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		int iCat = 0;
		PyTuple_GetInteger(poArgs, 0, &iCat);
		PyObject* poList = PyList_New(0);
		std::map<int, std::vector<DWORD> >::const_iterator it = s_kWiki.kMobCatList.find(iCat);
		if (it != s_kWiki.kMobCatList.end())
			for (size_t i = 0; i < it->second.size(); ++i)
			{
				PyObject* po = PyInt_FromLong(long(it->second[i]));
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetMobStats(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const std::vector<long long>* p = Find(s_kWiki.kMobStats, ArgVnum(poArgs));
		if (!p || p->size() < 13 + 17)
			return Py_BuildNone();
		const std::vector<long long>& v = *p;
		PyObject* poRes = PyTuple_New(11);
		PyObject* poEl = PyTuple_New(6);
		for (int i = 0; i < 11; ++i)
			PyTuple_SetItem(poRes, i, PyLong_FromLongLong(v[13 + i]));
		for (int i = 0; i < 6; ++i)
			PyTuple_SetItem(poEl, i, PyLong_FromLongLong(v[24 + i]));
		PyObject* poTuple = PyTuple_New(15);
		for (int i = 0; i < 13; ++i)
			PyTuple_SetItem(poTuple, i, PyLong_FromLongLong(v[i]));
		PyTuple_SetItem(poTuple, 13, poRes);
		PyTuple_SetItem(poTuple, 14, poEl);
		return poTuple;
	}

	PyObject* wikiGetMobDrops(PyObject* poSelf, PyObject* poArgs)	{ Load(); return RowList(Find(s_kWiki.kMobDrops, ArgVnum(poArgs))); }
	PyObject* wikiGetItemMobs(PyObject* poSelf, PyObject* poArgs)	{ Load(); return RowList(Find(s_kWiki.kItemMobs, ArgVnum(poArgs))); }
	PyObject* wikiGetChestContent(PyObject* poSelf, PyObject* poArgs)	{ Load(); return RowList(Find(s_kWiki.kChestContent, ArgVnum(poArgs))); }
	PyObject* wikiGetItemChests(PyObject* poSelf, PyObject* poArgs)	{ Load(); return RowList(Find(s_kWiki.kItemChests, ArgVnum(poArgs))); }

	PyObject* wikiGetMobPlaces(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		const std::vector<std::pair<DWORD, int> >* p = Find(s_kWiki.kMobPlaces, ArgVnum(poArgs));
		if (p)
			for (size_t i = 0; i < p->size(); ++i)
			{
				PyObject* po = Py_BuildValue("(ii)", int((*p)[i].first), (*p)[i].second);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetMapName(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		const std::string* p = Find(s_kWiki.kMapNames, ArgVnum(poArgs));
		return Py_BuildValue("s", p ? p->c_str() : "");
	}

	PyObject* wikiGetChestCategories(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		for (size_t i = 0; i < s_kWiki.kChestCats.size(); ++i)
		{
			PyObject* po = Py_BuildValue("(is)", s_kWiki.kChestCats[i].first, s_kWiki.kChestCats[i].second.c_str());
			PyList_Append(poList, po);
			Py_DECREF(po);
		}
		return poList;
	}

	PyObject* wikiGetChestCategory(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		int iCat = 0;
		PyTuple_GetInteger(poArgs, 0, &iCat);
		PyObject* poList = PyList_New(0);
		std::map<int, std::vector<std::pair<DWORD, DWORD> > >::const_iterator it = s_kWiki.kChestCatList.find(iCat);
		if (it != s_kWiki.kChestCatList.end())
			for (size_t i = 0; i < it->second.size(); ++i)
			{
				PyObject* po = Py_BuildValue("(ii)", int(it->second[i].first), int(it->second[i].second));
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetCraftNpcs(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		for (size_t i = 0; i < s_kWiki.kCraftNpcs.size(); ++i)
		{
			PyObject* po = Py_BuildValue("(is)", int(s_kWiki.kCraftNpcs[i].first), s_kWiki.kCraftNpcs[i].second.c_str());
			PyList_Append(poList, po);
			Py_DECREF(po);
		}
		return poList;
	}

	PyObject* wikiGetNpcLocations(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		const std::vector<SLoc>* p = Find(s_kWiki.kNpcLocs, ArgVnum(poArgs));
		if (p)
			for (size_t i = 0; i < p->size(); ++i)
			{
				PyObject* po = Py_BuildValue("(iii)", int((*p)[i].dwMap), (*p)[i].iX, (*p)[i].iY);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetNpcCubes(PyObject* poSelf, PyObject* poArgs)		{ Load(); return IntList(Find(s_kWiki.kNpcCubes, ArgVnum(poArgs))); }
	PyObject* wikiGetItemCubeSources(PyObject* poSelf, PyObject* poArgs)	{ Load(); return IntList(Find(s_kWiki.kItemCubeSources, ArgVnum(poArgs))); }
	PyObject* wikiGetItemCubeUses(PyObject* poSelf, PyObject* poArgs)	{ Load(); return IntList(Find(s_kWiki.kItemCubeUses, ArgVnum(poArgs))); }

	PyObject* wikiGetCube(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		int iIndex = -1;
		PyTuple_GetInteger(poArgs, 0, &iIndex);
		if (iIndex < 0 || iIndex >= int(s_kWiki.kCubes.size()))
			return Py_BuildNone();
		const SCube& c = s_kWiki.kCubes[iIndex];
		PyObject* poNpcs = PyTuple_New(c.kNpcs.size());
		for (size_t i = 0; i < c.kNpcs.size(); ++i)
			PyTuple_SetItem(poNpcs, i, PyInt_FromLong(long(c.kNpcs[i])));
		return Py_BuildValue("(NiiiLiN)", poNpcs, c.iKind, int(c.dwResult), c.iCount, c.llGold, c.iPercent, MaterialTuple(c.kMats));
	}

	PyObject* wikiGetItemRefineUses(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		const std::vector<std::pair<DWORD, int> >* p = Find(s_kWiki.kRefineUses, ArgVnum(poArgs));
		if (p)
			for (size_t i = 0; i < p->size(); ++i)
			{
				PyObject* po = Py_BuildValue("(ii)", int((*p)[i].first), (*p)[i].second);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetItemShops(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		const std::vector<SShop>* p = Find(s_kWiki.kShops, ArgVnum(poArgs));
		if (p)
			for (size_t i = 0; i < p->size(); ++i)
			{
				PyObject* po = Py_BuildValue("(iLi)", int((*p)[i].dwNpc), (*p)[i].llPrice, (*p)[i].iCount);
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	PyObject* wikiGetItemNotes(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		PyObject* poList = PyList_New(0);
		const std::vector<std::string>* p = Find(s_kWiki.kNotes, ArgVnum(poArgs));
		if (p)
			for (size_t i = 0; i < p->size(); ++i)
			{
				PyObject* po = PyString_FromString((*p)[i].c_str());
				PyList_Append(poList, po);
				Py_DECREF(po);
			}
		return poList;
	}

	// the client's item_proto has the item (item.SelectItem of an unknown vnum leaves the next call an error)
	PyObject* wikiItemExists(PyObject* poSelf, PyObject* poArgs)
	{
		CItemData* pItemData = NULL;
		const DWORD dwVnum = ArgVnum(poArgs);
		return Py_BuildValue("i", dwVnum && CItemManager::Instance().GetItemDataPointer(dwVnum, &pItemData) && pItemData ? 1 : 0);
	}

	// the client's mob_proto has the race
	PyObject* wikiMobExists(PyObject* poSelf, PyObject* poArgs)
	{
		return Py_BuildValue("i", CPythonNonPlayer::Instance().GetTable(ArgVnum(poArgs)) ? 1 : 0);
	}

	PyObject* wikiHasItemInfo(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		return Py_BuildValue("i", HasItemInfo(ArgVnum(poArgs)) ? 1 : 0);
	}

	PyObject* SearchResult(std::vector<SMatch>& kMatches, int iMax)
	{
		std::sort(kMatches.begin(), kMatches.end());
		PyObject* poList = PyList_New(0);
		for (size_t i = 0; i < kMatches.size() && int(i) < iMax; ++i)
		{
			PyObject* po = PyInt_FromLong(long(kMatches[i].dwVnum));
			PyList_Append(poList, po);
			Py_DECREF(po);
		}
		return poList;
	}

	PyObject* wikiSearchItems(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		char* szText = NULL;
		int iMax = 50;
		if (!PyTuple_GetString(poArgs, 0, &szText))
			return PyList_New(0);
		PyTuple_GetInteger(poArgs, 1, &iMax);
		const std::string query = Fold(szText);
		std::vector<SMatch> kMatches;
		if (query.size() < 2 && !(query.size() == 1 && isdigit((unsigned char) query[0])))
			return PyList_New(0);
		const DWORD dwNumber = isdigit((unsigned char) query[0]) ? ToDword(query) : 0;

		std::map<DWORD, std::string> kNames;
		CItemManager::Instance().GetItemsNameMap(kNames);
		std::set<DWORD> kSeen;
		std::map<std::string, DWORD> kByName;	// one result a name (the wiki's item first)
		for (std::map<DWORD, std::string>::const_iterator it = kNames.begin(); it != kNames.end(); ++it)
		{
			const DWORD dwVnum = it->first;
			int iScore = -1;
			std::string strName = Fold(BaseName(it->second).c_str());
			if (dwNumber && dwVnum == dwNumber)
				iScore = 0;
			else if (!strName.empty())
				iScore = Score(strName, query);
			if (iScore < 0)
				continue;
			const DWORD dwHead = ChainHead(dwVnum);
			if (!kSeen.insert(dwHead).second)
				continue;
			// the same name for many vnums (old copies): the one the wiki knows something of
			std::map<std::string, DWORD>::iterator itName = kByName.find(strName);
			if (itName != kByName.end() && !(dwNumber && dwVnum == dwNumber))
			{
				if (HasItemInfo(itName->second) || !HasItemInfo(dwHead))
					continue;
				for (size_t i = 0; i < kMatches.size(); ++i)
					if (kMatches[i].dwVnum == itName->second)
					{
						kMatches[i].dwVnum = dwHead;
						break;
					}
				itName->second = dwHead;
				continue;
			}
			kByName[strName] = dwHead;
			SMatch m;
			m.iScore = iScore * 2 + (HasItemInfo(dwHead) ? 0 : 1);
			m.length = strName.size();
			m.dwVnum = dwHead;
			kMatches.push_back(m);
		}
		return SearchResult(kMatches, iMax);
	}

	PyObject* wikiSearchMobs(PyObject* poSelf, PyObject* poArgs)
	{
		Load();
		char* szText = NULL;
		int iMax = 50;
		if (!PyTuple_GetString(poArgs, 0, &szText))
			return PyList_New(0);
		PyTuple_GetInteger(poArgs, 1, &iMax);
		const std::string query = Fold(szText);
		if (query.empty())
			return PyList_New(0);
		const DWORD dwNumber = isdigit((unsigned char) query[0]) ? ToDword(query) : 0;
		std::vector<SMatch> kMatches;
		std::set<std::string> kNames;
		for (std::map<DWORD, std::vector<long long> >::const_iterator it = s_kWiki.kMobStats.begin(); it != s_kWiki.kMobStats.end(); ++it)
		{
			const DWORD dwVnum = it->first;
			const std::string strName = Fold(CPythonNonPlayer::Instance().GetMonsterName(dwVnum));
			int iScore = -1;
			if (dwNumber && dwVnum == dwNumber)
				iScore = 0;
			else if (!strName.empty() && query.size() >= 2)
				iScore = Score(strName, query);
			if (iScore < 0)
				continue;
			// a name many races share (a dungeon's copy): the one with drops first, then the lowest vnum
			SMatch m;
			m.iScore = iScore * 2 + (s_kWiki.kMobDrops.count(dwVnum) ? 0 : 1);
			m.length = strName.size();
			m.dwVnum = dwVnum;
			kMatches.push_back(m);
		}
		return SearchResult(kMatches, iMax);
	}
}

void Mt2009Wiki_RegisterPython()
{
	static PyMethodDef s_methods[] =
	{
		{ "Load",					wikiLoad,					METH_VARARGS, NULL },
		{ "IsLoaded",				wikiIsLoaded,				METH_VARARGS, NULL },
		{ "GetEquipList",			wikiGetEquipList,			METH_VARARGS, NULL },
		{ "GetChain",				wikiGetChain,				METH_VARARGS, NULL },
		{ "GetRefineStep",			wikiGetRefineStep,			METH_VARARGS, NULL },
		{ "GetRefineFrom",			wikiGetRefineFrom,			METH_VARARGS, NULL },
		{ "GetCostumeList",			wikiGetCostumeList,			METH_VARARGS, NULL },
		{ "GetCostumeInfo",			wikiGetCostumeInfo,			METH_VARARGS, NULL },
		{ "GetMobCategories",		wikiGetMobCategories,		METH_VARARGS, NULL },
		{ "GetMobCategory",			wikiGetMobCategory,			METH_VARARGS, NULL },
		{ "GetMobStats",			wikiGetMobStats,			METH_VARARGS, NULL },
		{ "GetMobDrops",			wikiGetMobDrops,			METH_VARARGS, NULL },
		{ "GetMobPlaces",			wikiGetMobPlaces,			METH_VARARGS, NULL },
		{ "GetMapName",				wikiGetMapName,				METH_VARARGS, NULL },
		{ "GetItemMobs",			wikiGetItemMobs,			METH_VARARGS, NULL },
		{ "GetChestCategories",		wikiGetChestCategories,		METH_VARARGS, NULL },
		{ "GetChestCategory",		wikiGetChestCategory,		METH_VARARGS, NULL },
		{ "GetChestContent",		wikiGetChestContent,		METH_VARARGS, NULL },
		{ "GetItemChests",			wikiGetItemChests,			METH_VARARGS, NULL },
		{ "GetCraftNpcs",			wikiGetCraftNpcs,			METH_VARARGS, NULL },
		{ "GetNpcLocations",		wikiGetNpcLocations,		METH_VARARGS, NULL },
		{ "GetNpcCubes",			wikiGetNpcCubes,			METH_VARARGS, NULL },
		{ "GetCube",				wikiGetCube,				METH_VARARGS, NULL },
		{ "GetItemCubeSources",		wikiGetItemCubeSources,		METH_VARARGS, NULL },
		{ "GetItemCubeUses",		wikiGetItemCubeUses,		METH_VARARGS, NULL },
		{ "GetItemRefineUses",		wikiGetItemRefineUses,		METH_VARARGS, NULL },
		{ "GetItemShops",			wikiGetItemShops,			METH_VARARGS, NULL },
		{ "GetItemNotes",			wikiGetItemNotes,			METH_VARARGS, NULL },
		{ "HasItemInfo",			wikiHasItemInfo,			METH_VARARGS, NULL },
		{ "ItemExists",				wikiItemExists,				METH_VARARGS, NULL },
		{ "MobExists",				wikiMobExists,				METH_VARARGS, NULL },
		{ "SearchItems",			wikiSearchItems,			METH_VARARGS, NULL },
		{ "SearchMobs",				wikiSearchMobs,				METH_VARARGS, NULL },
		{ NULL, NULL, 0, NULL },
	};
	Py_InitModule("wikipedia", s_methods);

	if (PyObject* poApp = PyImport_AddModule("app"))	// borrowed; initapp made it
	{
		PyModule_AddIntConstant(poApp, "ENABLE_WIKI", 1);
#if defined(RENDER_TARGET)
		PyModule_AddIntConstant(poApp, "ENABLE_RENDER_TARGET_WIKI", 1);
#else
		PyModule_AddIntConstant(poApp, "ENABLE_RENDER_TARGET_WIKI", 0);
#endif
	}
}
#else
void Mt2009Wiki_RegisterPython() {}
#endif
