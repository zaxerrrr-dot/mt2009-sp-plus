#include "StdAfx.h"
#include "../eterPack/EterPackManager.h"
#include "../eterLib/ResourceManager.h"

#include "ItemManager.h"
#include <algorithm>	// MT2009_PLUS_AREZZO_COSTUME_SETS_V1 (LoadShiningTable)

static DWORD s_adwItemProtoKey[4] =
{
	173217,
	72619434,
	408587239,
	27973291
};

namespace
{
	bool IsCorDraconis(DWORD dwVnum)
	{
		static const DWORD s_adwCorVnums[] =
		{
			50252, 50255, 50256, 50257, 50258, 50259, 50260,
			51501, 51502, 51503, 51504, 51505, 51506, 51507, 51508, 51509, 51510,
			51541, 51548, 51549, 51562, 51569, 51576, 51583, 51590, 51597,
			51604, 51611, 51618, 51625, 51632, 76040,
		};
		for (size_t i = 0; i < _countof(s_adwCorVnums); ++i)
			if (s_adwCorVnums[i] == dwVnum)
				return true;
		return false;
	}

	bool IsTradeableCorOrSash(DWORD dwVnum)
	{
		if (IsCorDraconis(dwVnum))
			return true;
		if (dwVnum >= 85101 && dwVnum <= 85104)
			return true;
		if (dwVnum >= 86061 && dwVnum <= 86064)
			return true;
		if (dwVnum < 85001 || dwVnum > 85024)
			return false;
		const DWORD dwGrade = dwVnum % 10;
		return dwGrade != 9 && dwGrade != 0;
	}
}

BOOL CItemManager::SelectItemData(DWORD dwIndex)
{
	TItemMap::iterator f = m_ItemMap.find(dwIndex);

	if (m_ItemMap.end() == f)
	{
		int n = m_vec_ItemRange.size();
		for (int i = 0; i < n; i++)
		{
			CItemData * p = m_vec_ItemRange[i];
			const CItemData::TItemTable * pTable = p->GetTable();
			if ((pTable->dwVnum < dwIndex) &&
				dwIndex < (pTable->dwVnum + pTable->dwVnumRange))
			{
				m_pSelectedItemData = p;
				return TRUE;
			}
		}
		Tracef(" CItemManager::SelectItemData - FIND ERROR [%d]\n", dwIndex);
		return FALSE;
	}

	m_pSelectedItemData = f->second;

	return TRUE;
}

CItemData * CItemManager::GetSelectedItemDataPointer()
{
	return m_pSelectedItemData;
}

BOOL CItemManager::GetItemDataPointer(DWORD dwItemID, CItemData ** ppItemData)
{
	if (0 == dwItemID)
		return FALSE;

	TItemMap::iterator f = m_ItemMap.find(dwItemID);

	if (m_ItemMap.end() == f)
	{
		int n = m_vec_ItemRange.size();
		for (int i = 0; i < n; i++)
		{
			CItemData * p = m_vec_ItemRange[i];
			const CItemData::TItemTable * pTable = p->GetTable();
			if ((pTable->dwVnum < dwItemID) &&
				dwItemID < (pTable->dwVnum + pTable->dwVnumRange))
			{
				*ppItemData = p;
				return TRUE;
			}
		}
		Tracef(" CItemManager::GetItemDataPointer - FIND ERROR [%d]\n", dwItemID);
		return FALSE;
	}

	*ppItemData = f->second;

	return TRUE;
}

CItemData * CItemManager::MakeItemData(DWORD dwIndex)
{
	TItemMap::iterator f = m_ItemMap.find(dwIndex);

	if (m_ItemMap.end() == f)
	{
		CItemData * pItemData = CItemData::New();

		m_ItemMap.insert(TItemMap::value_type(dwIndex, pItemData));

		return pItemData;
	}

	return f->second;
}

////////////////////////////////////////////////////////////////////////////////////////
// Load Item Table

bool CItemManager::LoadItemList(const char * c_szFileName)
{
	CMappedFile File;
	LPCVOID pData;

	if (!CEterPackManager::Instance().Get(File, c_szFileName, &pData))
		return false;

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(File.Size(), pData);

	CTokenVector TokenVector;
    for (DWORD i = 0; i < textFileLoader.GetLineCount(); ++i)
	{
		if (!textFileLoader.SplitLine(i, &TokenVector, "\t"))
			continue;

		if (!(TokenVector.size() == 3 || TokenVector.size() == 4))
		{
			TraceError(" CItemManager::LoadItemList(%s) - StrangeLine in %d\n", c_szFileName, i);
			continue;
		}

		const std::string & c_rstrID = TokenVector[0];
		//const std::string & c_rstrType = TokenVector[1];
		const std::string & c_rstrIcon = TokenVector[2];

		DWORD dwItemVNum=atoi(c_rstrID.c_str());

		CItemData * pItemData = MakeItemData(dwItemVNum);

		extern BOOL USE_VIETNAM_CONVERT_WEAPON_VNUM;
		if (USE_VIETNAM_CONVERT_WEAPON_VNUM)
		{
			extern DWORD Vietnam_ConvertWeaponVnum(DWORD vnum);
			DWORD dwMildItemVnum = Vietnam_ConvertWeaponVnum(dwItemVNum);
			if (dwMildItemVnum == dwItemVNum)
			{
				if (4 == TokenVector.size())
				{
					const std::string & c_rstrModelFileName = TokenVector[3];
					pItemData->SetDefaultItemData(c_rstrIcon.c_str(), c_rstrModelFileName.c_str());
				}
				else
				{
					pItemData->SetDefaultItemData(c_rstrIcon.c_str());
				}
			}
			else
			{
				DWORD dwMildBaseVnum = dwMildItemVnum / 10 * 10;
				char szMildIconPath[MAX_PATH];
				sprintf(szMildIconPath, "icon/item/%.5d.tga", dwMildBaseVnum);
				if (4 == TokenVector.size())
				{
					char szMildModelPath[MAX_PATH];
					sprintf(szMildModelPath, "d:/ymir work/item/weapon/%.5d.gr2", dwMildBaseVnum);
					pItemData->SetDefaultItemData(szMildIconPath, szMildModelPath);
				}
				else
				{
					pItemData->SetDefaultItemData(szMildIconPath);
				}
			}
		}
		else
		{
			if (4 == TokenVector.size())
			{
				const std::string & c_rstrModelFileName = TokenVector[3];
				pItemData->SetDefaultItemData(c_rstrIcon.c_str(), c_rstrModelFileName.c_str());
			}
			else
			{
				pItemData->SetDefaultItemData(c_rstrIcon.c_str());
			}
		}
	}

	return true;
}

const std::string& __SnapString(const std::string& c_rstSrc, std::string& rstTemp)
{
	UINT uSrcLen=c_rstSrc.length();
	if (uSrcLen<2)
		return c_rstSrc;

	if (c_rstSrc[0]!='"')
		return c_rstSrc;

	UINT uLeftCut=1;

	UINT uRightCut=uSrcLen;
	if (c_rstSrc[uSrcLen-1]=='"')
		uRightCut=uSrcLen-1;

	rstTemp=c_rstSrc.substr(uLeftCut, uRightCut-uLeftCut);
	return rstTemp;
}
#ifdef ENABLE_IKASHOP_RENEWAL
void CItemManager::GetItemsNameMap(std::map<DWORD, std::string>& inMap)
{
	inMap.clear();

	for(auto& it : m_ItemMap)
		inMap.insert(std::make_pair(it.first, it.second->GetName())); 
}
#endif

bool CItemManager::LoadItemNames(const char* c_szFileName)
{
	const VOID* pvData;
	CMappedFile kFile;
	if (!CEterPackManager::Instance().Get(kFile, c_szFileName, &pvData))
	{
		Tracenf("CItemManager::LoadItemNames(c_szFileName=%s) - Load Error", c_szFileName);
		return false;
	}

	CMemoryTextFileLoader kTextFileLoader;
	kTextFileLoader.Bind(kFile.Size(), pvData);

	std::string stTemp;

	CTokenVector kTokenVector;
	for (DWORD i = 0; i < kTextFileLoader.GetLineCount(); ++i)
	{
		if (!kTextFileLoader.SplitLineByTab(i, &kTokenVector))
			continue;

		while (kTokenVector.size() < ITEMNAME_COL_NUM)
			kTokenVector.push_back("");

		DWORD dwVnum = atoi(kTokenVector[ITEMNAME_COL_VNUM].c_str());
		const std::string& c_rstrName = kTokenVector[ITEMNAME_COL_NAME];
		TItemMap::iterator f = m_ItemMap.find(dwVnum);
		if (m_ItemMap.end() == f)
			continue;

		CItemData* pkItemDataFind = f->second;
		pkItemDataFind->SetLocaleName(c_rstrName);
	}
	return true;
}

bool CItemManager::LoadItemDesc(const char* c_szFileName)
{
	const VOID* pvData;
	CMappedFile kFile;
	if (!CEterPackManager::Instance().Get(kFile, c_szFileName, &pvData))
	{
		Tracenf("CItemManager::LoadItemDesc(c_szFileName=%s) - Load Error", c_szFileName);
		return false;
	}

	CMemoryTextFileLoader kTextFileLoader;
	kTextFileLoader.Bind(kFile.Size(), pvData);

	std::string stTemp;

	CTokenVector kTokenVector;
	for (DWORD i = 0; i < kTextFileLoader.GetLineCount(); ++i)
	{
		if (!kTextFileLoader.SplitLineByTab(i, &kTokenVector))
			continue;

		while (kTokenVector.size()<ITEMDESC_COL_NUM)
			kTokenVector.push_back("");

		//assert(kTokenVector.size()==ITEMDESC_COL_NUM);

		DWORD dwVnum=atoi(kTokenVector[ITEMDESC_COL_VNUM].c_str());
		const std::string& c_rstDesc=kTokenVector[ITEMDESC_COL_DESC];
		const std::string& c_rstSumm=kTokenVector[ITEMDESC_COL_SUMM];
		TItemMap::iterator f = m_ItemMap.find(dwVnum);
		if (m_ItemMap.end() == f)
			continue;

		CItemData* pkItemDataFind = f->second;

		pkItemDataFind->SetDescription(__SnapString(c_rstDesc, stTemp));
		pkItemDataFind->SetSummary(__SnapString(c_rstSumm, stTemp));
	}
	return true;
}

DWORD GetHashCode( const char* pString )
{
	   unsigned long i,len;
	   unsigned long ch;
	   unsigned long result;

	   len     = strlen( pString );
	   result = 5381;
	   for( i=0; i<len; i++ )
	   {
	   	   ch = (unsigned long)pString[i];
	   	   result = ((result<< 5) + result) + ch; // hash * 33 + ch
	   }

	   return result;
}

bool CItemManager::LoadItemTable(const char* c_szFileName)
{
	CMappedFile file;
	LPCVOID pvData;

	if (!CEterPackManager::Instance().Get(file, c_szFileName, &pvData))
		return false;

	DWORD dwFourCC, dwElements, dwDataSize;
	DWORD dwVersion=0;
	DWORD dwStride=0;

	file.Read(&dwFourCC, sizeof(DWORD));

	if (dwFourCC == MAKEFOURCC('M', 'I', 'P', 'X'))
	{
		file.Read(&dwVersion, sizeof(DWORD));
		file.Read(&dwStride, sizeof(DWORD));

		if (dwVersion != 1)
		{
			TraceError("CPythonItem::LoadItemTable: invalid item_proto[%s] VERSION[%d]", c_szFileName, dwVersion);
			return false;
		}

#ifdef ENABLE_PROTOSTRUCT_AUTODETECT
		if (!CItemData::TItemTableAll::IsValidStruct(dwStride))
#else
		if (dwStride != sizeof(CItemData::TItemTable))
#endif
		{
			TraceError("CPythonItem::LoadItemTable: invalid item_proto[%s] STRIDE[%d] != sizeof(SItemTable)",
				c_szFileName, dwStride, sizeof(CItemData::TItemTable));
			return false;
		}
	}
	else if (dwFourCC != MAKEFOURCC('M', 'I', 'P', 'T'))
	{
		TraceError("CPythonItem::LoadItemTable: invalid item proto type %s", c_szFileName);
		return false;
	}

	file.Read(&dwElements, sizeof(DWORD));
	file.Read(&dwDataSize, sizeof(DWORD));

	BYTE * pbData = new BYTE[dwDataSize];
	file.Read(pbData, dwDataSize);

	/////

	CLZObject zObj;

	if (!CLZO::Instance().Decompress(zObj, pbData, s_adwItemProtoKey))
	{
		delete [] pbData;
		return false;
	}

	/////

	char szName[64+1];
	std::map<DWORD,DWORD> itemNameMap;

	for (DWORD i = 0; i < dwElements; ++i)
	{
#ifdef ENABLE_PROTOSTRUCT_AUTODETECT
		CItemData::TItemTable t = {0};
		CItemData::TItemTableAll::Process(zObj.GetBuffer(), dwStride, i, t);
#else
		CItemData::TItemTable & t = *((CItemData::TItemTable *) zObj.GetBuffer() + i);
#endif
		CItemData::TItemTable * table = &t;

		CItemData * pItemData;
		DWORD dwVnum = table->dwVnum;
		if (IsTradeableCorOrSash(dwVnum))
			table->dwAntiFlags &= ~(ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP);
		if (IsCorDraconis(dwVnum))
		{
			// Cor Draconis is a consumable container.  Both the stack flag and
			// the absence of ANTI_STACK are required by the inventory move code.
			table->dwFlags |= ITEM_FLAG_STACKABLE;
			table->dwAntiFlags &= ~ITEM_ANTIFLAG_STACK;
			table->dwMaxStack = 200;
		}

		TItemMap::iterator f = m_ItemMap.find(dwVnum);
		if (m_ItemMap.end() == f)
		{
			_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", dwVnum);

			if (CResourceManager::Instance().IsFileExist(szName) == false)
			{
				std::map<DWORD, DWORD>::iterator itVnum = itemNameMap.find(GetHashCode(table->szName));

				if (itVnum != itemNameMap.end())
					_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", itVnum->second);
				else
					_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", dwVnum-dwVnum % 10);

				if (CResourceManager::Instance().IsFileExist(szName) == false)
				{
					#ifdef _DEBUG
					TraceError("%16s(#%-5d) cannot find icon file. setting to default.", table->szName, dwVnum);
					#endif
					const DWORD EmptyBowl = 27995;
					_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", EmptyBowl);
				}
			}

			pItemData = CItemData::New();

			pItemData->SetDefaultItemData(szName);
			m_ItemMap.insert(TItemMap::value_type(dwVnum, pItemData));
		}
		else
		{
			pItemData = f->second;
		}
		if (itemNameMap.find(GetHashCode(table->szName)) == itemNameMap.end())
			itemNameMap.insert(std::map<DWORD,DWORD>::value_type(GetHashCode(table->szName),table->dwVnum));
		pItemData->SetItemTableData(table);
		if (0 != table->dwVnumRange)
		{
			m_vec_ItemRange.push_back(pItemData);
		}
	}

#ifdef ENABLE_DRAGON_SOUL_SYSTEM
	// The bundled item_proto uses the older 184-byte layout.  Register the
	// final server-side Dragon Soul ranges here so Myth grade and the seventh
	// (Amethyst) type are available without replacing that incompatible proto.
	m_vec_ItemRange.erase(
		std::remove_if(m_vec_ItemRange.begin(), m_vec_ItemRange.end(),
			[](CItemData* pItemData)
			{
				return pItemData && pItemData->GetTable()->bType == ITEM_DS;
			}),
		m_vec_ItemRange.end());

	const char* aszDragonSoulType[DS_SLOT_MAX] =
	{
		"Diament", "Rubin", "Jadeit", "Szafir", "Granat", "Onyks", "Ametyst"
	};
	const char* aszDragonSoulGrade[DRAGON_SOUL_GRADE_MAX] =
	{
		"Surowy", "Szlifowany", "Rzadki", "Antyczny", "Legendarny", "Mityczny"
	};

	for (DWORD type = 0; type < DS_SLOT_MAX; ++type)
	{
		for (DWORD grade = 0; grade < DRAGON_SOUL_GRADE_MAX; ++grade)
		{
			for (DWORD step = 0; step < DRAGON_SOUL_STEP_MAX; ++step)
			{
				const DWORD dwVnum = 110000 + type * 10000 + grade * 1000 + step * 100;
				CItemData::TItemTable table = { 0 };
				table.dwVnum = dwVnum;
				table.dwVnumRange = 100;
				_snprintf(table.szName, sizeof(table.szName), "%s Smoczy Kamien %s", aszDragonSoulGrade[grade], aszDragonSoulType[type]);
				strncpy_s(table.szLocaleName, table.szName, _TRUNCATE);
				table.bType = ITEM_DS;
				table.bSubType = static_cast<BYTE>(type);
				table.bSize = 1;
				table.dwAntiFlags = ITEM_ANTIFLAG_DROP | ITEM_ANTIFLAG_SELL | ITEM_ANTIFLAG_GIVE |
					ITEM_ANTIFLAG_PKDROP | ITEM_ANTIFLAG_STACK | ITEM_ANTIFLAG_MYSHOP | ITEM_ANTIFLAG_SAFEBOX;
				table.aLimits[0].bType = LIMIT_TIMER_BASED_ON_WEAR;
				table.aLimits[0].lValue = 86400;

				char szDragonSoulIcon[MAX_PATH];
				_snprintf(szDragonSoulIcon, sizeof(szDragonSoulIcon), "icon/item/%u.tga", dwVnum);
				CItemData* pItemData = MakeItemData(dwVnum);
				pItemData->SetDefaultItemData(szDragonSoulIcon);
				pItemData->SetItemTableData(&table);
				m_vec_ItemRange.push_back(pItemData);
			}
		}
	}

	struct SDragonSoulUtilityItem
	{
		DWORD dwVnum;
		const char* szName;
		BYTE bType;
		BYTE bSubType;
		DWORD dwMaxStack;
	};
	const SDragonSoulUtilityItem aDragonSoulUtilityItems[] =
	{
		{ 30270,  "Odłamek Smoczego Kamienia", ITEM_QUEST,    0,                          200 },
		{ 50255,  "Cor Draconis",               ITEM_GIFTBOX,  1,                          200 },
		{ 50260,  "Cor Draconis+",              ITEM_GIFTBOX,  1,                          200 },
		{ 76029,  "Smocza Fasola",              ITEM_MATERIAL, MATERIAL_DS_REFINE_NORMAL, 200 },
		{ 100100, "Szczypce Czasu",             ITEM_EXTRACT,  EXTRACT_DRAGON_SOUL,       200 },
		{ 100101, "Szczypce Czasu+",            ITEM_EXTRACT,  EXTRACT_DRAGON_SOUL,       200 },
		{ 100200, "Szczypce Smoka",             ITEM_EXTRACT,  EXTRACT_DRAGON_HEART,      200 },
		{ 100300, "Smocza Fasola",              ITEM_MATERIAL, MATERIAL_DS_REFINE_NORMAL, 200 },
		{ 100400, "Błogosławiona Smocza Fasola",ITEM_MATERIAL, MATERIAL_DS_REFINE_BLESSED,200 },
		{ 100500, "Zielona Smocza Fasola",      ITEM_MATERIAL, MATERIAL_DS_REFINE_HOLLY,  200 },
		{ 100700, "Płomień Smoka",              ITEM_MATERIAL, MATERIAL_DS_CHANGE_ATTR,   200 },
		{ 100701, "Płomień Smoka+",             ITEM_MATERIAL, MATERIAL_DS_CHANGE_ATTR,   200 },
	};

	for (DWORD i = 0; i < _countof(aDragonSoulUtilityItems); ++i)
	{
		const SDragonSoulUtilityItem& source = aDragonSoulUtilityItems[i];
		CItemData::TItemTable table = { 0 };
		table.dwVnum = source.dwVnum;
		strncpy_s(table.szName, source.szName, _TRUNCATE);
		strncpy_s(table.szLocaleName, source.szName, _TRUNCATE);
		table.bType = source.bType;
		table.bSubType = source.bSubType;
		table.bSize = 1;
		table.dwMaxStack = source.dwMaxStack;
		table.dwFlags |= ITEM_FLAG_STACKABLE;
		table.dwAntiFlags &= ~ITEM_ANTIFLAG_STACK;

		char szDragonSoulIcon[MAX_PATH];
		_snprintf(szDragonSoulIcon, sizeof(szDragonSoulIcon), "icon/item/%u.tga", source.dwVnum);
		CItemData* pItemData = MakeItemData(source.dwVnum);
		pItemData->SetDefaultItemData(szDragonSoulIcon);
		pItemData->SetItemTableData(&table);
	}
#endif



	// MT2009 Plus search glasses. Server owns duration and use behaviour.
	struct SShopSearchGlass { DWORD vnum; const char* name; long duration; YANG price; };
	const SShopSearchGlass glasses[] = {
		{ 60004, "Lupa", 3600, 50000 },
		{ 60005, "Lupa Handlarza", 604800, 1000000 },
	};
	for (size_t i = 0; i < _countof(glasses); ++i)
	{
		CItemData::TItemTable table = { 0 };
		table.dwVnum = glasses[i].vnum;
		strncpy_s(table.szName, glasses[i].name, _TRUNCATE);
		strncpy_s(table.szLocaleName, glasses[i].name, _TRUNCATE);
		table.bType = ITEM_USE;
		table.bSubType = USE_SPECIAL;
		table.bSize = 1;
		table.dwIBuyItemPrice = glasses[i].price;
		table.dwISellItemPrice = glasses[i].price / 5;
		table.dwAntiFlags = ITEM_ANTIFLAG_DROP | ITEM_ANTIFLAG_SELL | ITEM_ANTIFLAG_GIVE |
			ITEM_ANTIFLAG_PKDROP | ITEM_ANTIFLAG_STACK | ITEM_ANTIFLAG_MYSHOP;
		table.aLimits[0].bType = LIMIT_REAL_TIME;
		table.aLimits[0].lValue = glasses[i].duration;
		char icon[MAX_PATH];
		_snprintf(icon, sizeof(icon), "icon/item/%u.tga", glasses[i].vnum);
		CItemData* data = MakeItemData(glasses[i].vnum);
		data->SetDefaultItemData(icon);
		data->SetItemTableData(&table);
	}

#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	// The shipped item_proto predates the sash system. Register the classic
	// shoulder sashes here, while item_list.txt supplies their icons/models.
	struct SAcceItem
	{
		DWORD dwVnum;
		const char* szName;
		DWORD dwNextVnum;
		long lAbsorptionRate;
	};
	const SAcceItem aAcceItems[] =
	{
		{ 85001, "Szarfa Wladcy (prosta)",       85002,  1 },
		{ 85002, "Szarfa Wladcy (dostojna)",     85003,  5 },
		{ 85003, "Szarfa Wladcy (zacna)",        85004, 10 },
		{ 85004, "Szarfa Wladcy (unikatowa)",        0, 20 },
		{ 85005, "Szarfa Mistrza (prosta)",      85006,  1 },
		{ 85006, "Szarfa Mistrza (dostojna)",    85007,  5 },
		{ 85007, "Szarfa Mistrza (zacna)",       85008, 10 },
		{ 85008, "Szarfa Mistrza (unikatowa)",       0, 20 },
		{ 85011, "Szarfa Wladcy Absolutnego (prosta)",   85012,  1 },
		{ 85012, "Szarfa Wladcy Absolutnego (dostojna)", 85013,  5 },
		{ 85013, "Szarfa Wladcy Absolutnego (zacna)",    85014, 10 },
		{ 85014, "Szarfa Wladcy Absolutnego (unikatowa)",    0, 20 },
		{ 85015, "Krolewska Szarfa (prosta)",     85016,  1 },
		{ 85016, "Krolewska Szarfa (dostojna)",   85017,  5 },
		{ 85017, "Krolewska Szarfa (zacna)",      85018, 10 },
		{ 85018, "Krolewska Szarfa (unikatowa)",      0, 20 },
		{ 85021, "Rocznicowa Szarfa (prosta)",    85022,  1 },
		{ 85022, "Rocznicowa Szarfa (dostojna)",  85023,  5 },
		{ 85023, "Rocznicowa Szarfa (zacna)",     85024, 10 },
		{ 85024, "Rocznicowa Szarfa (unikatowa)",     0, 20 },
		{ 85101, "Skrzydla Wladcy Smierci (proste)",       85102,  1 },
		{ 85102, "Skrzydla Wladcy Smierci (dostojne)",     85103,  5 },
		{ 85103, "Skrzydla Wladcy Smierci (zacne)",        85104, 10 },
		{ 85104, "Skrzydla Wladcy Smierci (unikatowe)",        0, 20 },
	};

	for (DWORD i = 0; i < _countof(aAcceItems); ++i)
	{
		const SAcceItem& source = aAcceItems[i];
		CItemData::TItemTable table = { 0 };
		table.dwVnum = source.dwVnum;
		strncpy_s(table.szName, source.szName, _TRUNCATE);
		strncpy_s(table.szLocaleName, source.szName, _TRUNCATE);
		table.bType = ITEM_COSTUME;
		table.bSubType = COSTUME_ACCE;
		table.bSize = 1;
		// Every sash is tradeable.  DROP and PKDROP remain blocked, while GIVE
		// and MYSHOP are deliberately absent just as on the server item_proto.
		table.dwAntiFlags = ITEM_ANTIFLAG_DROP | ITEM_ANTIFLAG_PKDROP;
		table.dwRefinedVnum = source.dwNextVnum;
		table.wRefineSet = source.dwNextVnum ? 409 : 0;
		table.aApplies[0].bType = 97; // APPLY_ACCEDRAIN_RATE
		table.aApplies[0].lValue = source.lAbsorptionRate;
		table.bSpecular = 100;

		CItemData* pItemData = MakeItemData(source.dwVnum);
		pItemData->SetItemTableData(&table);
	}
#endif

	// Magma Manni mount seals.  The matching server entries use the same
	// item VNUM as the race VNUM stored in value1.
	const DWORD adwMagmaManniVnum[] = { 53201, 53202, 53203 };
	const long alMagmaManniHP[] = { 50, 100, 150 };
	const char* aszMagmaManniName[] =
	{
		"Magma Manni I",
		"Magma Manni II",
		"Magma Manni III",
	};

	for (DWORD i = 0; i < _countof(adwMagmaManniVnum); ++i)
	{
		const DWORD dwVnum = adwMagmaManniVnum[i];
		TItemMap::iterator existingItem = m_ItemMap.find(dwVnum);

		CItemData::TItemTable table = { 0 };
		table.dwVnum = dwVnum;
		strncpy_s(table.szName, aszMagmaManniName[i], _TRUNCATE);
		strncpy_s(table.szLocaleName, aszMagmaManniName[i], _TRUNCATE);
		table.bType = 28;       // ITEM_COSTUME
		table.bSubType = 2;     // COSTUME_MOUNT
		table.bWeight = 0;
		table.bSize = 1;
		table.dwMaxStack = 200;
		table.dwAntiFlags = 106881;
		table.aLimits[0].bType = 7;       // LIMIT_REAL_TIME_START_FIRST_USE
		table.aLimits[0].lValue = 86400;  // 24 hours
		table.aApplies[0].bType = 6;      // APPLY_MAX_HP
		table.aApplies[0].lValue = alMagmaManniHP[i];
		table.alValues[0] = 1;
		table.alValues[1] = dwVnum;
		for (DWORD socket = 0; socket < ITEM_SOCKET_MAX_NUM; ++socket)
			table.alSockets[socket] = -1;

		_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", dwVnum);
		CItemData* pItemData = NULL;
		if (existingItem == m_ItemMap.end())
		{
			pItemData = CItemData::New();
			m_ItemMap.insert(TItemMap::value_type(dwVnum, pItemData));
		}
		else
		{
			pItemData = existingItem->second;
		}

		pItemData->SetDefaultItemData(szName);
		pItemData->SetItemTableData(&table);
		pItemData->SetDescription("Pieczec przywolujaca wierzchowca Magma Manni.");
		pItemData->SetSummary("Czas trwania: 24 godziny od pierwszego uzycia.");
	}

	// Official Easter 2026 Lightbearer costume set.  These entries are
	// registered here because this client uses an older binary item_proto
	// format for which no matching packer is available in the distribution.
	struct SLightbearerItem
	{
		DWORD dwVnum;
		const char* szName;
		BYTE bSubType;
		BYTE bSize;
		DWORD dwAntiFlags;
	};

	const DWORD c_dwCommonAntiFlags =
		ITEM_ANTIFLAG_DROP | ITEM_ANTIFLAG_PKDROP | ITEM_ANTIFLAG_STACK;
	const DWORD c_dwWolfmanAntiFlag = (1 << 18);
	const SLightbearerItem aLightbearerItems[] =
	{
		{ 41974, "Sw. Nosiciel Swiatla+", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_FEMALE },
		{ 41975, "Maj. Nosiciel Swiatla+", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_FEMALE },
		{ 41976, "Sw. Nosicielka Swiatla+", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_MALE | c_dwWolfmanAntiFlag },
		{ 41977, "Maj. Nosicielka Swiatla+", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_MALE | c_dwWolfmanAntiFlag },
		{ 45718, "Swietlisty Diadem+ (m)", 1, 1, c_dwCommonAntiFlags | ITEM_ANTIFLAG_FEMALE },
		{ 45719, "Majestat. Diadem+ (m)", 1, 1, c_dwCommonAntiFlags | ITEM_ANTIFLAG_FEMALE },
		{ 45720, "Swietlisty Diadem+ (k)", 1, 1, c_dwCommonAntiFlags | ITEM_ANTIFLAG_MALE | c_dwWolfmanAntiFlag },
		{ 45721, "Majestat. Diadem+ (k)", 1, 1, c_dwCommonAntiFlags | ITEM_ANTIFLAG_MALE | c_dwWolfmanAntiFlag },
	};

	for (DWORD i = 0; i < _countof(aLightbearerItems); ++i)
	{
		const SLightbearerItem& source = aLightbearerItems[i];
		CItemData::TItemTable table = { 0 };
		table.dwVnum = source.dwVnum;
		strncpy_s(table.szName, source.szName, _TRUNCATE);
		strncpy_s(table.szLocaleName, source.szName, _TRUNCATE);
		table.bType = 28; // ITEM_COSTUME
		table.bSubType = source.bSubType; // COSTUME_BODY / COSTUME_HAIR
		table.bSize = source.bSize;
		table.dwAntiFlags = source.dwAntiFlags;
		table.aLimits[0].bType = LIMIT_REAL_TIME;
		table.aLimits[0].lValue = 2592000; // 30 days
		table.alValues[3] = source.dwVnum;
		table.bSpecular = 100;

		_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", source.dwVnum);
		TItemMap::iterator existingItem = m_ItemMap.find(source.dwVnum);
		CItemData* pItemData = NULL;
		if (existingItem == m_ItemMap.end())
		{
			pItemData = CItemData::New();
			m_ItemMap.insert(TItemMap::value_type(source.dwVnum, pItemData));
		}
		else
		{
			pItemData = existingItem->second;
		}

		pItemData->SetDefaultItemData(szName);
		pItemData->SetItemTableData(&table);
		pItemData->SetDescription(source.bSubType == 0
			? "Kostium z zestawu Nosiciela Swiatla."
			: "Diadem z zestawu Nosiciela Swiatla.");
		pItemData->SetSummary("Czas trwania: 30 dni.");
	}

	// Death Ruler costumes.  The legacy binary item_proto shipped with this
	// client cannot represent these newer rows, so keep the client table in
	// sync with the server at runtime.
	const SLightbearerItem aDeathRulerCostumes[] =
	{
		{ 41980, "Kostium Wladcy Smierci (m)", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_FEMALE },
		{ 41981, "Kostium Wladcy Smierci (k)", 0, 2, c_dwCommonAntiFlags | ITEM_ANTIFLAG_MALE | c_dwWolfmanAntiFlag },
		{ 45722, "Fryzura Wladcy Smierci",      1, 1, c_dwCommonAntiFlags },
	};

	for (DWORD i = 0; i < _countof(aDeathRulerCostumes); ++i)
	{
		const SLightbearerItem& source = aDeathRulerCostumes[i];
		CItemData::TItemTable table = { 0 };
		table.dwVnum = source.dwVnum;
		strncpy_s(table.szName, source.szName, _TRUNCATE);
		strncpy_s(table.szLocaleName, source.szName, _TRUNCATE);
		table.bType = ITEM_COSTUME;
		table.bSubType = source.bSubType;
		table.bSize = source.bSize;
		table.dwAntiFlags = source.dwAntiFlags;
		table.alValues[3] = source.dwVnum;
		table.bSpecular = 100;

		_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", source.dwVnum);
		CItemData* pItemData = MakeItemData(source.dwVnum);
		pItemData->SetDefaultItemData(szName);
		pItemData->SetItemTableData(&table);
		pItemData->SetDescription(source.bSubType == 0
			? "Kostium z zestawu Wladcy Smierci."
			: "Fryzura z zestawu Wladcy Smierci.");
	}

#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
	struct SDeathRulerWeapon
	{
		DWORD dwVnum;
		const char* szName;
		const char* szModel;
		BYTE bWeaponType;
		BYTE bSize;
		DWORD dwClassAntiFlags;
	};
	const SDeathRulerWeapon aDeathRulerWeapons[] =
	{
		{ 49001, "Nakladka Miecza Wladcy Smierci",      "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_sword.gr2",      WEAPON_SWORD,      2, ITEM_ANTIFLAG_SURA | ITEM_ANTIFLAG_SHAMAN },
		{ 49002, "Nakladka Dwureki Wladcy Smierci",     "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_twohand.gr2",    WEAPON_TWO_HANDED, 3, ITEM_ANTIFLAG_ASSASSIN | ITEM_ANTIFLAG_SURA | ITEM_ANTIFLAG_SHAMAN },
		{ 49003, "Nakladka Sztyletow Wladcy Smierci",   "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_dagger.gr2",     WEAPON_DAGGER,     1, ITEM_ANTIFLAG_WARRIOR | ITEM_ANTIFLAG_SURA | ITEM_ANTIFLAG_SHAMAN },
		{ 49004, "Nakladka Luku Wladcy Smierci",        "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_bow.gr2",        WEAPON_BOW,        2, ITEM_ANTIFLAG_WARRIOR | ITEM_ANTIFLAG_SURA | ITEM_ANTIFLAG_SHAMAN },
		{ 49005, "Nakladka Miecza Sury Wladcy Smierci", "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_sword_sura.gr2", WEAPON_SWORD,      2, ITEM_ANTIFLAG_WARRIOR | ITEM_ANTIFLAG_ASSASSIN | ITEM_ANTIFLAG_SHAMAN },
		{ 49006, "Nakladka Dzwonu Wladcy Smierci",      "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_bell.gr2",       WEAPON_BELL,       1, ITEM_ANTIFLAG_WARRIOR | ITEM_ANTIFLAG_ASSASSIN | ITEM_ANTIFLAG_SURA },
		{ 49007, "Nakladka Wachlarza Wladcy Smierci",   "d:/ymir work/item/weapon/plechito/death_ruler_set/dr_fan.gr2",        WEAPON_FAN,        1, ITEM_ANTIFLAG_WARRIOR | ITEM_ANTIFLAG_ASSASSIN | ITEM_ANTIFLAG_SURA },
	};

	for (DWORD i = 0; i < _countof(aDeathRulerWeapons); ++i)
	{
		const SDeathRulerWeapon& source = aDeathRulerWeapons[i];
		CItemData::TItemTable table = { 0 };
		table.dwVnum = source.dwVnum;
		strncpy_s(table.szName, source.szName, _TRUNCATE);
		strncpy_s(table.szLocaleName, source.szName, _TRUNCATE);
		table.bType = ITEM_COSTUME;
		table.bSubType = COSTUME_WEAPON;
		table.bSize = source.bSize;
		table.dwAntiFlags = c_dwCommonAntiFlags | source.dwClassAntiFlags;
		table.alValues[3] = source.bWeaponType;
		table.bSpecular = 100;

		_snprintf(szName, sizeof(szName), "icon/item/%05d.tga", source.dwVnum);
		CItemData* pItemData = MakeItemData(source.dwVnum);
		pItemData->SetDefaultItemData(szName, source.szModel);
		pItemData->SetItemTableData(&table);
		pItemData->SetDescription("Nakladka na bron z zestawu Wladcy Smierci.");
	}
#endif

	// Gameforge 26.1 cosmetic catalogues. The base client still ships a legacy
	// encrypted item_proto, so newer records are loaded from compact numeric
	// tables after the base and local custom records have been registered.
	// item_list.txt is loaded first and already owns official icon/model paths.
	struct SGFSupplementalTable
	{
		const char* fileName;
		BYTE itemType;
		const char* logName;
	};
	const SGFSupplementalTable gfTables[] =
	{
		{ "gamedata/gf_official_costumes.txt", ITEM_COSTUME, "costume" },
		{ "gamedata/gf_official_pets.txt", ITEM_PET, "simple pet" },
		{ "gamedata/costume_attr_items.txt", ITEM_USE, "costume attribute item" },
		{ "gamedata/costume_transfer_item.txt", ITEM_QUEST, "costume transfer catalyst" },
	};

	for (DWORD tableIndex = 0; tableIndex < _countof(gfTables); ++tableIndex)
	{
		CMappedFile gfFile;
		LPCVOID gfData;
		const SGFSupplementalTable& source = gfTables[tableIndex];
		if (CEterPackManager::Instance().Get(gfFile, source.fileName, &gfData))
		{
			CMemoryTextFileLoader gfLoader;
			gfLoader.Bind(gfFile.Size(), gfData);
			CTokenVector tokens;
			DWORD loadedCount = 0;

			for (DWORD line = 0; line < gfLoader.GetLineCount(); ++line)
			{
				if (!gfLoader.SplitLine(line, &tokens, "\t") || tokens.empty())
					continue;
				if (!tokens[0].empty() && tokens[0][0] == '#')
					continue;
				if (tokens.size() != 24)
				{
					TraceError("GF %s table: invalid column count %u on line %u", source.logName, tokens.size(), line + 1);
					continue;
				}

				CItemData::TItemTable table = { 0 };
				table.dwVnum = strtoul(tokens[0].c_str(), NULL, 10);
				strncpy_s(table.szName, tokens[1].c_str(), _TRUNCATE);
				strncpy_s(table.szLocaleName, tokens[1].c_str(), _TRUNCATE);
				table.bType = source.itemType;
				table.bSubType = static_cast<BYTE>(atoi(tokens[2].c_str()));
				table.bSize = static_cast<BYTE>(atoi(tokens[3].c_str()));
				table.dwMaxStack = 1;
				table.dwAntiFlags = strtoul(tokens[4].c_str(), NULL, 10);
				table.dwFlags = strtoul(tokens[5].c_str(), NULL, 10);

				for (DWORD i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
				{
					table.aLimits[i].bType = static_cast<BYTE>(atoi(tokens[6 + i * 2].c_str()));
					table.aLimits[i].lValue = atol(tokens[7 + i * 2].c_str());
				}
				for (DWORD i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
				{
					table.aApplies[i].bType = static_cast<BYTE>(atoi(tokens[10 + i * 2].c_str()));
					table.aApplies[i].lValue = atol(tokens[11 + i * 2].c_str());
				}
				for (DWORD i = 0; i < ITEM_VALUES_MAX_NUM; ++i)
					table.alValues[i] = atol(tokens[16 + i].c_str());
				table.bSpecular = static_cast<BYTE>(atoi(tokens[22].c_str()));

				CItemData* itemData = MakeItemData(table.dwVnum);
				itemData->SetItemTableData(&table);
				++loadedCount;
			}

			Tracef("GF %s table: loaded %u records\n", source.logName, loadedCount);
		}
		else
		{
			TraceError("GF %s table: cannot open %s", source.logName, source.fileName);
		}
	}

	delete [] pbData;
	return true;
}

#ifdef ENABLE_ITEM_SHINING_TABLE
// MT2009_PLUS_AREZZO_COSTUME_SETS_V1: the glow effects of the Arezzo costumes (weapon skins and costumes) by vnum.
// A line: vnum, then one or more effect files, tab separated, quotes and backslashes allowed;
// '#' starts a comment. A missing file is no error (the client then shows no glow).
bool CItemManager::LoadShiningTable(const char* c_szFileName)
{
	m_ShiningTable.clear();

	CMappedFile File;
	LPCVOID pData;
	if (!CEterPackManager::Instance().Get(File, c_szFileName, &pData))
		return false;

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(File.Size(), pData);

	CTokenVector TokenVector;
	for (DWORD i = 0; i < textFileLoader.GetLineCount(); ++i)
	{
		if (!textFileLoader.SplitLine(i, &TokenVector, "\t") || TokenVector.size() < 2)
			continue;
		if (TokenVector[0].empty() || TokenVector[0][0] == '#')
			continue;

		const DWORD dwVnum = strtoul(TokenVector[0].c_str(), NULL, 10);
		if (!dwVnum)
			continue;

		std::vector<std::string>& rvecFiles = m_ShiningTable[dwVnum];
		for (size_t j = 1; j < TokenVector.size(); ++j)
		{
			std::string strFile = TokenVector[j];
			strFile.erase(std::remove(strFile.begin(), strFile.end(), '"'), strFile.end());
			std::replace(strFile.begin(), strFile.end(), '\\', '/');
			while (!strFile.empty() && (strFile.back() == ' ' || strFile.back() == '\r'))
				strFile.pop_back();
			if (!strFile.empty())
				rvecFiles.push_back(strFile);
		}
		if (rvecFiles.empty())
			m_ShiningTable.erase(dwVnum);
	}

	Tracef("CItemManager::LoadShiningTable(%s): %u items\n", c_szFileName, (unsigned)m_ShiningTable.size());
	return true;
}

const std::vector<std::string>* CItemManager::GetShiningFiles(DWORD dwVnum) const
{
	std::map<DWORD, std::vector<std::string> >::const_iterator it = m_ShiningTable.find(dwVnum);
	return it == m_ShiningTable.end() ? NULL : &it->second;
}
#endif

void CItemManager::Destroy()
{
	TItemMap::iterator i;
	for (i=m_ItemMap.begin(); i!=m_ItemMap.end(); ++i)
		CItemData::Delete(i->second);

	m_ItemMap.clear();
}

#ifdef ENABLE_ACCE_COSTUME_SYSTEM
bool CItemManager::LoadItemScale(const char* szItemScale)
{
	CMappedFile File;
	LPCVOID pData;
	if (!CEterPackManager::Instance().Get(File, szItemScale, &pData))
		return false;

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(File.Size(), pData);

	CTokenVector TokenVector;
	for (DWORD i = 0; i < textFileLoader.GetLineCount(); ++i)
	{
		if (!textFileLoader.SplitLine(i, &TokenVector, "\t"))
			continue;

		if (!(TokenVector.size() == 6 || TokenVector.size() == 7))
		{
			TraceError(" CItemManager::LoadItemScale(%s) - Error on line %d\n", szItemScale, i);
			continue;
		}

		const std::string& c_rstrID = TokenVector[ITEMSCALE_COL_VNUM];
		const std::string& c_rstrJob = TokenVector[ITEMSCALE_COL_JOB];
		const std::string& c_rstrSex = TokenVector[ITEMSCALE_COL_SEX];
		const std::string& c_rstrScaleX = TokenVector[ITEMSCALE_COL_SCALE_X];
		const std::string& c_rstrScaleY = TokenVector[ITEMSCALE_COL_SCALE_Y];
		const std::string& c_rstrScaleZ = TokenVector[ITEMSCALE_COL_SCALE_Z];

		DWORD dwItemVnum = atoi(c_rstrID.c_str());
		BYTE bJob = 0;
		if (!strcmp(c_rstrJob.c_str(), "JOB_WARRIOR")) bJob = NRaceData::JOB_WARRIOR;
		if (!strcmp(c_rstrJob.c_str(), "JOB_ASSASSIN")) bJob = NRaceData::JOB_ASSASSIN;
		if (!strcmp(c_rstrJob.c_str(), "JOB_SURA")) bJob = NRaceData::JOB_SURA;
		if (!strcmp(c_rstrJob.c_str(), "JOB_SHAMAN")) bJob = NRaceData::JOB_SHAMAN;
#ifdef ENABLE_WOLFMAN_CHARACTER
		if (!strcmp(c_rstrJob.c_str(), "JOB_WOLFMAN")) bJob = NRaceData::JOB_WOLFMAN;
#endif
		BYTE bSex = c_rstrSex[0] == 'M';

		float fScaleX = atof(c_rstrScaleX.c_str()) * 0.01f;
		float fScaleY = atof(c_rstrScaleY.c_str()) * 0.01f;
		float fScaleZ = atof(c_rstrScaleZ.c_str()) * 0.01f;
		float fParticleScale = 1.0f;
		if (TokenVector.size() == 7)
		{
			const std::string& c_rstrParticleScale = TokenVector[ITEMSCALE_COL_PARTICLE_SCALE];
			fParticleScale = atof(c_rstrParticleScale.c_str());
		}

		CItemData* pItemData = MakeItemData(dwItemVnum);
		BYTE bGradeMax = 5;
#ifdef ENABLE_AURA_COSTUME_SYSTEM
		if (pItemData->GetType() == CItemData::ITEM_TYPE_COSTUME && pItemData->GetSubType() == CItemData::COSTUME_AURA)
			bGradeMax = 6;
#endif

		for (BYTE i = 0; i < bGradeMax; ++i)
		{
			pItemData = MakeItemData(dwItemVnum + i);
			if (pItemData)
				pItemData->SetItemTableScaleData(bJob, bSex, fScaleX, fScaleY, fScaleZ, fParticleScale);
		}
	}

	return true;
}
#endif

CItemManager::CItemManager() : m_pSelectedItemData(NULL)
{
}
CItemManager::~CItemManager()
{
	Destroy();
}
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
