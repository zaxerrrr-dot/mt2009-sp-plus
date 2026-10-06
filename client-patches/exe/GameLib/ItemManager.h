#pragma once

#include "ItemData.h"

class CItemManager : public CSingleton<CItemManager>
{
	public:
		enum EItemDescCol
		{
			ITEMDESC_COL_VNUM,
			ITEMDESC_COL_NAME,
			ITEMDESC_COL_DESC,
			ITEMDESC_COL_SUMM,
			ITEMDESC_COL_NUM,
		};

		enum EItemNames
		{
			ITEMNAME_COL_VNUM,
			ITEMNAME_COL_NAME,
			ITEMNAME_COL_NUM
		};

#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		enum EItemScaleCol
		{
			ITEMSCALE_COL_VNUM,
			ITEMSCALE_COL_JOB,
			ITEMSCALE_COL_SEX,
			ITEMSCALE_COL_SCALE_X,
			ITEMSCALE_COL_SCALE_Y,
			ITEMSCALE_COL_SCALE_Z,
			ITEMSCALE_COL_PARTICLE_SCALE,
		};
#endif

	public:
		typedef std::map<DWORD, CItemData*> TItemMap;
		typedef std::map<DWORD, std::string> TItemNameMap;

	public:
		CItemManager();
		virtual ~CItemManager();

		void			Destroy();

		BOOL			SelectItemData(DWORD dwIndex);
		CItemData *		GetSelectedItemDataPointer();

		BOOL			GetItemDataPointer(DWORD dwItemID, CItemData ** ppItemData);

		/////
		bool			LoadItemNames(const char* c_szFileName);
		bool			LoadItemDesc(const char* c_szFileName);
		bool			LoadItemList(const char* c_szFileName);
		bool			LoadItemTable(const char* c_szFileName);
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		bool			LoadItemScale(const char* szItemScale);
#endif
#ifdef ENABLE_ITEM_SHINING_TABLE
		// MT2009_PLUS_AREZZO_COSTUME_SETS_V1: glow effects (.mse) of an item by its vnum, gamedata/shiningtable.txt
		// ("vnum<TAB>"effect"[<TAB>"effect"...]", the Arezzo costumes' format).
		bool			LoadShiningTable(const char* c_szFileName);
		const std::vector<std::string>* GetShiningFiles(DWORD dwVnum) const;
#endif

		CItemData *		MakeItemData(DWORD dwIndex);
#ifdef ENABLE_IKASHOP_RENEWAL
		void			GetItemsNameMap(std::map<DWORD, std::string>& inMap);
#endif

	protected:
#ifdef ENABLE_ITEM_SHINING_TABLE
		std::map<DWORD, std::vector<std::string> > m_ShiningTable;
#endif
		TItemMap m_ItemMap;
		std::vector<CItemData*>  m_vec_ItemRange;
		CItemData * m_pSelectedItemData;
};
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
