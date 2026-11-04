#pragma once

// MT2009_PLUS_SWITCHBOT_V1: Ameria Project's switchbot (srcs/client/UserInterface/PythonSwitchbot.h) - what the server
// told about the five slots (TSwitchbotTable, Packet.h) plus the alternatives the player is setting up, and the bonuses
// with their maxima of every attribute set (from item_attr, sent at "/switchbot hello"). The python module "switchbot"
// (PythonSwitchbot.cpp) is root/uiswitchbot.py's.
#ifdef ENABLE_SWITCHBOT

#include "Packet.h"

#include <map>
#include <vector>

class CPythonSwitchbot : public CSingleton <CPythonSwitchbot>
{
public:
	CPythonSwitchbot();
	virtual ~CPythonSwitchbot();

	void Initialize();
	void Update(const TSwitchbotTable& table);

	void SetAttribute(BYTE slot, BYTE alternative, BYTE attrIdx, WORD attrType, int attrValue); // MT2009_PLUS_WIDE_ATTR_V1
	TPlayerItemAttribute GetAttribute(BYTE slot, BYTE alternative, BYTE attrIdx);
	void GetAlternatives(BYTE slot, std::vector<TSwitchbotAttributeAlternativeTable>& attributes);
	int GetAttibuteSet(BYTE slot);
	bool IsActive(BYTE slot);
	bool IsFinished(BYTE slot);

	void ClearSlot(BYTE slot);
	void ClearAttributeMap();

	void AddAttributeToMap(const TSwitchbotAttributeInfo& table);
	void GetAttributesBySet(int iAttributeSet, std::vector<TPlayerItemAttribute>& vec_attributes);
	long GetAttributeMaxValue(int iAttributeSet, WORD attrType); // MT2009_PLUS_WIDE_ATTR_V1

protected:
	TSwitchbotTable m_SwitchbotTable;
	std::map<BYTE, std::map<WORD, long>> m_map_AttributesBySet; // MT2009_PLUS_WIDE_ATTR_V1: attribute set -> bonus type (a WORD) -> max
};
#endif
