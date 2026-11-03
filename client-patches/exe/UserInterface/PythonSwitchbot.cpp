#include "StdAfx.h"

// MT2009_PLUS_SWITCHBOT_V1: Ameria Project's switchbot (srcs/client/UserInterface/PythonSwitchbot.cpp and its
// PythonNetworkStreamPhaseGame.cpp RecvSwitchbotPacket / SendSwitchbotStartPacket / SendSwitchbotStopPacket), ported to
// this exe: the packets' fields have fixed sizes (Packet.h - the server's packet.h the same, server-patches/switchbot),
// a GC packet of an unexpected size is read past (the stream stays in step), the items of the window SWITCHBOT are kept
// in CPythonPlayer (aSwitchbotItem). Python module "switchbot" for root/uiswitchbot.py.

#ifdef ENABLE_SWITCHBOT

#include "PythonSwitchbot.h"
#include "PythonNetworkStream.h"
#include "PythonPlayer.h"
#include "AbstractPlayer.h"
#include "../GameLib/ItemManager.h"

static_assert(SWITCHBOT == 16, "the window SWITCHBOT is the server's 16 (after the extra inventory's 11-15)");

// MT2009_PLUS_SWITCHBOT_GLOVE_TALISMAN_V1 / MT2009_PLUS_SWITCHBOT_COSTUME_V1: the attribute sets the server numbers its
// SUBHEADER_GC_SWITCHBOT_SEND_ATTRIBUTE_INFORMATION rows with (its common/length.h EAttributeSet with ENABLE_ITEM_ATTR_COSTUME,
// ENABLE_WEAPON_COSTUME_SYSTEM, ENABLE_PENDANT_SYSTEM and ENABLE_GLOVE_SYSTEM: the eight old sets 0-7, the costume's
// 8-10, the talisman's 11, the glove's 12 - 13 sets, item_attr's columns). This exe's own EAttributeSet has no costume
// sets (ENABLE_ITEM_ATTR_COSTUME is off here), so its ATTRIBUTE_SET_PENDANT is not the server's - the server's numbers.
enum
{
	SERVER_ATTRIBUTE_SET_COSTUME_BODY = 8,
	SERVER_ATTRIBUTE_SET_COSTUME_HAIR = 9,
	SERVER_ATTRIBUTE_SET_COSTUME_WEAPON = 10,
	SERVER_ATTRIBUTE_SET_PENDANT = 11,
	SERVER_ATTRIBUTE_SET_GLOVE = 12,
};
static_assert(ATTRIBUTE_SET_EAR == 7, "the eight old attribute sets are numbered as on the server");

CPythonSwitchbot::CPythonSwitchbot()
{
	Initialize();
}

CPythonSwitchbot::~CPythonSwitchbot()
{
	Initialize();
}

void CPythonSwitchbot::Initialize()
{
	memset(&m_SwitchbotTable, 0, sizeof(m_SwitchbotTable));
	m_map_AttributesBySet.clear();
}

void CPythonSwitchbot::Update(const TSwitchbotTable& table)
{
	memcpy(m_SwitchbotTable.active, table.active, sizeof(table.active));
	memcpy(m_SwitchbotTable.finished, table.finished, sizeof(table.finished));
	memcpy(m_SwitchbotTable.alternatives, table.alternatives, sizeof(table.alternatives));
	memcpy(m_SwitchbotTable.items, table.items, sizeof(table.items));
	m_SwitchbotTable.player_id = table.player_id;
}

void CPythonSwitchbot::SetAttribute(BYTE slot, BYTE alternative, BYTE attrIdx, BYTE attrType, int attrValue)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return;
	}

	if (alternative >= SWITCHBOT_ALTERNATIVE_COUNT)
	{
		return;
	}

	if (attrIdx >= SWITCHBOT_ATTR_COUNT)
	{
		return;
	}

	m_SwitchbotTable.alternatives[slot][alternative].attributes[attrIdx].bType = attrType;
	m_SwitchbotTable.alternatives[slot][alternative].attributes[attrIdx].sValue = attrValue;
}

TPlayerItemAttribute CPythonSwitchbot::GetAttribute(BYTE slot, BYTE alternative, BYTE attrIdx)
{
	TPlayerItemAttribute attr = {};

	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return attr;
	}

	if (alternative >= SWITCHBOT_ALTERNATIVE_COUNT)
	{
		return attr;
	}

	if (attrIdx >= SWITCHBOT_ATTR_COUNT)
	{
		return attr;
	}

	attr.bType = m_SwitchbotTable.alternatives[slot][alternative].attributes[attrIdx].bType;
	attr.sValue = m_SwitchbotTable.alternatives[slot][alternative].attributes[attrIdx].sValue;

	return attr;
}

void CPythonSwitchbot::GetAlternatives(BYTE slot, std::vector<TSwitchbotAttributeAlternativeTable>& vec_alternatives)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return;
	}

	for (int i = 0; i < SWITCHBOT_ALTERNATIVE_COUNT; ++i)
	{
		vec_alternatives.push_back(m_SwitchbotTable.alternatives[slot][i]);
	}
}

int CPythonSwitchbot::GetAttibuteSet(BYTE slot)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return -1;
	}

	TItemPos pos(SWITCHBOT, slot);

	CItemData* pItemDataPtr = NULL;
	BYTE item_type = 0, item_subtype = 0;

	if (CItemManager::Instance().GetItemDataPointer(CPythonPlayer::Instance().GetItemIndex(pos), &pItemDataPtr))
	{
		item_type = pItemDataPtr->GetType();
		item_subtype = pItemDataPtr->GetSubType();
	}

	if (item_type == 0 && item_subtype == 0)
	{
		return -1;
	}

	if (item_type == ITEM_WEAPON)
	{
		if (item_subtype == WEAPON_ARROW)
		{
			return -1;
		}

		return ATTRIBUTE_SET_WEAPON;
	}

	if (item_type == ITEM_ARMOR)
	{
		switch (item_subtype)
		{
		case ARMOR_BODY:
			return ATTRIBUTE_SET_BODY;

		case ARMOR_WRIST:
			return ATTRIBUTE_SET_WRIST;

		case ARMOR_FOOTS:
			return ATTRIBUTE_SET_FOOTS;

		case ARMOR_NECK:
			return ATTRIBUTE_SET_NECK;

		case ARMOR_HEAD:
			return ATTRIBUTE_SET_HEAD;

		case ARMOR_SHIELD:
			return ATTRIBUTE_SET_SHIELD;

		case ARMOR_EAR:
			return ATTRIBUTE_SET_EAR;

		// MT2009_PLUS_SWITCHBOT_GLOVE_TALISMAN_V1: a talisman and a glove (the server's switchbot takes them now)
		case ARMOR_PENDANT:
			return SERVER_ATTRIBUTE_SET_PENDANT;

		case ARMOR_GLOVE:
			return SERVER_ATTRIBUTE_SET_GLOVE;
		}
	}

	// MT2009_PLUS_SWITCHBOT_COSTUME_V1: a costume, a hairstyle, a weapon skin - their own sets (item_attr.costume_*).
	// Ameria's code gave a costume the armour's set of its subtype (a hairstyle the helmet's, a weapon skin the feet's).
	if (item_type == ITEM_COSTUME)
	{
		switch (item_subtype)
		{
		case COSTUME_BODY:
			return SERVER_ATTRIBUTE_SET_COSTUME_BODY;

		case COSTUME_HAIR:
			return SERVER_ATTRIBUTE_SET_COSTUME_HAIR;

#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
		case COSTUME_WEAPON:
			return SERVER_ATTRIBUTE_SET_COSTUME_WEAPON;
#endif
		}
	}

	return -1;
}

bool CPythonSwitchbot::IsActive(BYTE slot)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return false;
	}

	return m_SwitchbotTable.active[slot];
}

bool CPythonSwitchbot::IsFinished(BYTE slot)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return false;
	}

	return m_SwitchbotTable.finished[slot];
}

void CPythonSwitchbot::ClearSlot(BYTE slot)
{
	if (slot >= SWITCHBOT_SLOT_COUNT)
	{
		return;
	}

	m_SwitchbotTable.active[slot] = false;
	m_SwitchbotTable.items[slot] = 0;
	memset(&m_SwitchbotTable.alternatives[slot], 0, sizeof(m_SwitchbotTable.alternatives[slot]));
}

void CPythonSwitchbot::ClearAttributeMap()
{
	m_map_AttributesBySet.clear();
}

void CPythonSwitchbot::AddAttributeToMap(const TSwitchbotAttributeInfo& table)
{
	m_map_AttributesBySet[table.attribute_set][(BYTE)table.apply_num] = table.max_value;
}

void CPythonSwitchbot::GetAttributesBySet(int iAttributeSet, std::vector<TPlayerItemAttribute>& vec_attributes)
{
	if (iAttributeSet == -1)
	{
		return;
	}

	const auto it = m_map_AttributesBySet.find(iAttributeSet);
	if (it == m_map_AttributesBySet.end())
	{
		return;
	}

	for (const auto& it2 : it->second)
	{
		TPlayerItemAttribute attr;
		attr.bType = it2.first;
		attr.sValue = (short)it2.second;

		vec_attributes.push_back(attr);
	}
}

long CPythonSwitchbot::GetAttributeMaxValue(int iAttributeSet, BYTE attrType)
{
	if (iAttributeSet == -1)
	{
		return 0;
	}

	const auto it = m_map_AttributesBySet.find(iAttributeSet);
	if (it == m_map_AttributesBySet.end())
	{
		return 0;
	}

	const auto it2 = it->second.find(attrType);
	if (it2 == it->second.end())
	{
		return 0;
	}

	return it2->second;
}

// ---------------------------------------------------------------- packets (Ameria's, in PythonNetworkStreamPhaseGame.cpp)

bool CPythonNetworkStream::RecvSwitchbotPacket()
{
	TPacketGCSwitchbot pack;
	if (!Recv(sizeof(pack), &pack))
	{
		return false;
	}

	if (pack.size < sizeof(TPacketGCSwitchbot))
	{
		return false;
	}

	size_t packet_size = size_t(pack.size) - sizeof(TPacketGCSwitchbot);
	// a body of an unexpected size is read past, so the stream stays in step
	auto SkipSwitchbotBody = [this](size_t body) -> bool
	{
		if (!body)
			return true;

		std::vector<char> skip(body);
		return Recv((int)body, &skip[0]);
	};
	if (pack.subheader == SUBHEADER_GC_SWITCHBOT_UPDATE)
	{
		if (packet_size != sizeof(TSwitchbotTable))
		{
			TraceError("RecvSwitchbotPacket: UPDATE of %u bytes", (unsigned int)packet_size);
			return SkipSwitchbotBody(packet_size);
		}

		TSwitchbotTable table;
		if (!Recv(sizeof(table), &table))
		{
			return false;
		}

		CPythonSwitchbot::Instance().Update(table);
		PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "RefreshSwitchbotWindow", Py_BuildValue("()"));
	}
	else if (pack.subheader == SUBHEADER_GC_SWITCHBOT_UPDATE_ITEM)
	{
		if (packet_size != sizeof(TSwitchbotUpdateItem))
		{
			TraceError("RecvSwitchbotPacket: UPDATE_ITEM of %u bytes", (unsigned int)packet_size);
			return SkipSwitchbotBody(packet_size);
		}

		TSwitchbotUpdateItem update;
		if (!Recv(sizeof(update), &update))
		{
			return false;
		}

		if (update.slot >= SWITCHBOT_SLOT_COUNT)
		{
			return true;
		}

		TItemPos pos(SWITCHBOT, update.slot);
		TItemPos posInven(INVENTORY, update.CellInven);

		IAbstractPlayer& rkPlayer = IAbstractPlayer::GetSingleton();
		rkPlayer.SetItemCount(pos, update.count);

		for (int i = 0; i < ITEM_SOCKET_SLOT_MAX_NUM; ++i)
		{
			rkPlayer.SetItemMetinSocket(pos, i, update.alSockets[i]);
		}

		for (int j = 0; j < ITEM_ATTRIBUTE_SLOT_MAX_NUM; ++j)
		{
			rkPlayer.SetItemAttribute(pos, j, update.aAttr[j].bType, update.aAttr[j].sValue);
			if (posInven.IsValidItemPosition())
				rkPlayer.SetItemAttribute(posInven, j, update.aAttr[j].bType, update.aAttr[j].sValue);
		}

		PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "RefreshSwitchbotItem", Py_BuildValue("(i)", update.slot));
		return true;
	}
	else if (pack.subheader == SUBHEADER_GC_SWITCHBOT_SEND_ATTRIBUTE_INFORMATION)
	{
		CPythonSwitchbot::Instance().ClearAttributeMap();

		const size_t table_size = sizeof(TSwitchbotAttributeInfo);
		while (packet_size >= table_size)
		{
			TSwitchbotAttributeInfo table;
			if (!Recv(table_size, &table))
			{
				return false;
			}

			CPythonSwitchbot::Instance().AddAttributeToMap(table);
			packet_size -= table_size;
		}

		return SkipSwitchbotBody(packet_size);
	}
	else
	{
		return SkipSwitchbotBody(packet_size);
	}

	return true;
}

bool CPythonNetworkStream::SendSwitchbotStartPacket(BYTE slot, const std::vector<TSwitchbotAttributeAlternativeTable>& alternatives)
{
	if (alternatives.size() != SWITCHBOT_ALTERNATIVE_COUNT)
	{
		return false;
	}

	TPacketCGSwitchbot pack;
	pack.header = HEADER_CG_SWITCHBOT;
	pack.subheader = SUBHEADER_CG_SWITCHBOT_START;
	pack.size = sizeof(TPacketCGSwitchbot) + sizeof(TSwitchbotAttributeAlternativeTable) * SWITCHBOT_ALTERNATIVE_COUNT;
	pack.slot = slot;

	if (!Send(sizeof(pack), &pack))
	{
		return false;
	}

	for (size_t i = 0; i < alternatives.size(); ++i)
	{
		if (!Send(sizeof(TSwitchbotAttributeAlternativeTable), &alternatives[i]))
		{
			return false;
		}
	}

	return SendSequence();
}

bool CPythonNetworkStream::SendSwitchbotStopPacket(BYTE slot)
{
	TPacketCGSwitchbot pack;
	pack.header = HEADER_CG_SWITCHBOT;
	pack.subheader = SUBHEADER_CG_SWITCHBOT_STOP;
	pack.size = sizeof(TPacketCGSwitchbot);
	pack.slot = slot;

	if (!Send(sizeof(pack), &pack))
	{
		return false;
	}

	return SendSequence();
}

// ---------------------------------------------------------------- python module "switchbot"

PyObject* switchbotIsActive(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	return Py_BuildValue("i", CPythonSwitchbot::Instance().IsActive(bSlot));
}

PyObject* switchbotIsFinished(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	return Py_BuildValue("i", CPythonSwitchbot::Instance().IsFinished(bSlot));
}

PyObject* switchbotGetAttribute(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	BYTE bAlternative;
	if (!PyTuple_GetByte(poArgs, 1, &bAlternative))
	{
		return Py_BuildException();
	}

	BYTE bAttrIndex;
	if (!PyTuple_GetByte(poArgs, 2, &bAttrIndex))
	{
		return Py_BuildException();
	}

	TPlayerItemAttribute attr = CPythonSwitchbot::Instance().GetAttribute(bSlot, bAlternative, bAttrIndex);
	return Py_BuildValue("ii", attr.bType, attr.sValue);
}

PyObject* switchbotSetAttribute(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	BYTE bAlternative;
	if (!PyTuple_GetByte(poArgs, 1, &bAlternative))
	{
		return Py_BuildException();
	}

	BYTE bAttrIndex;
	if (!PyTuple_GetByte(poArgs, 2, &bAttrIndex))
	{
		return Py_BuildException();
	}

	BYTE bType;
	if (!PyTuple_GetByte(poArgs, 3, &bType))
	{
		return Py_BuildException();
	}

	int iValue;
	if (!PyTuple_GetInteger(poArgs, 4, &iValue))
	{
		return Py_BuildException();
	}

	CPythonSwitchbot::Instance().SetAttribute(bSlot, bAlternative, bAttrIndex, bType, iValue);
	return Py_BuildNone();
}

PyObject* switchbotClearSlot(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	CPythonSwitchbot::Instance().ClearSlot(bSlot);
	return Py_BuildNone();
}

PyObject* switchbotGetAttributesForSet(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	PyObject* list = PyList_New(0);

	int iAttributeSet = CPythonSwitchbot::Instance().GetAttibuteSet(bSlot);
	if (iAttributeSet == -1)
	{
		return list;
	}

	std::vector<TPlayerItemAttribute> vec_attributes;
	CPythonSwitchbot::Instance().GetAttributesBySet(iAttributeSet, vec_attributes);

	std::sort(vec_attributes.begin(), vec_attributes.end(),
		[](const TPlayerItemAttribute& a, const TPlayerItemAttribute& b) { return a.bType < b.bType; });

	for (size_t i = 0; i < vec_attributes.size(); ++i)
	{
		PyObject* item = Py_BuildValue("(ii)", vec_attributes[i].bType, vec_attributes[i].sValue);
		PyList_Append(list, item);
		Py_DECREF(item);
	}

	return list;
}

PyObject* switchbotGetAttributeMaxValue(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	BYTE bAttrType;
	if (!PyTuple_GetByte(poArgs, 1, &bAttrType))
	{
		return Py_BuildException();
	}

	int iAttributeSet = CPythonSwitchbot::Instance().GetAttibuteSet(bSlot);
	if (iAttributeSet == -1)
	{
		return Py_BuildValue("i", 0);
	}

	long maxValue = CPythonSwitchbot::Instance().GetAttributeMaxValue(iAttributeSet, bAttrType);
	return Py_BuildValue("i", maxValue);
}

PyObject* switchbotStart(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	if (bSlot >= SWITCHBOT_SLOT_COUNT)
	{
		return Py_BuildNone();
	}

	std::vector<TSwitchbotAttributeAlternativeTable> vec_alternatives;
	CPythonSwitchbot::Instance().GetAlternatives(bSlot, vec_alternatives);

	CPythonNetworkStream::Instance().SendSwitchbotStartPacket(bSlot, vec_alternatives);
	return Py_BuildNone();
}

PyObject* switchbotStop(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bSlot;
	if (!PyTuple_GetByte(poArgs, 0, &bSlot))
	{
		return Py_BuildException();
	}

	if (bSlot >= SWITCHBOT_SLOT_COUNT)
	{
		return Py_BuildNone();
	}

	CPythonNetworkStream::Instance().SendSwitchbotStopPacket(bSlot);
	return Py_BuildNone();
}

void initSwitchbot()
{
	static PyMethodDef s_methods[] =
	{
		{ "IsActive",				switchbotIsActive,				METH_VARARGS },
		{ "IsFinished",				switchbotIsFinished,			METH_VARARGS },
		{ "GetAttribute",			switchbotGetAttribute,			METH_VARARGS },
		{ "SetAttribute",			switchbotSetAttribute,			METH_VARARGS },
		{ "GetAttributesForSet",	switchbotGetAttributesForSet,	METH_VARARGS },
		{ "GetAttributeMaxValue",	switchbotGetAttributeMaxValue,	METH_VARARGS },
		{ "ClearSlot",				switchbotClearSlot,				METH_VARARGS },
		{ "Start",					switchbotStart,					METH_VARARGS },
		{ "Stop",					switchbotStop,					METH_VARARGS },

		{ NULL, NULL, NULL },
	};

	PyObject * poModule = Py_InitModule("switchbot", s_methods);
	PyModule_AddIntConstant(poModule, "SLOT_COUNT", SWITCHBOT_SLOT_COUNT);
	PyModule_AddIntConstant(poModule, "ALTERNATIVE_COUNT", SWITCHBOT_ALTERNATIVE_COUNT);
	PyModule_AddIntConstant(poModule, "ATTR_COUNT", SWITCHBOT_ATTR_COUNT);
}

#endif
