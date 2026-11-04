/**
* MT2009_PLUS_CHANGE_LOOK_V1 - Transmutacja (Owsap v6.2.6 __CHANGE_LOOK_SYSTEM__, Autor: blackdragonx61 / Mali) and
* MT2009_PLUS_HIDE_COSTUME_V1 - Owsap's costume hiding, in the Yohara 3.0 exe (server-patches/transmutacja,
* server-patches/ukryjkostium).
*
* The look of an item (another item's vnum, 0: none) comes with the item: dwTransmutation at the end of the
* server's item set (GC 21), item update (GC 25), safebox / mall set (GC 85 / 128) and exchange (GC exchange)
* packets and of ikashop::TPlayerItem (Packet.h); TItemData::dwTransmutationVnum keeps it (GameType.h). What the
* other characters look like needs nothing here - the server sends the looks as the parts.
* Owsap's change-look window packets are not used: the window (root/uichangelook.py) speaks chat commands with
* the server, so only these Python functions are new:
*   player.GetChangeLookVnum(slot) / (window, slot)      the look of an item of the bag / equipment
*   safebox.GetItemChangeLookVnum(slot), safebox.GetMallItemChangeLookVnum(slot)
*   exchange.GetChangeLookVnumFromSelf(pos), exchange.GetChangeLookVnumFromTarget(pos)
*   app.ENABLE_CHANGE_LOOK_SYSTEM = 1, app.ENABLE_HIDE_COSTUME_SYSTEM = 1, app.MT2009_CHANGE_LOOK_EXE = 1
*/
#include "StdAfx.h"
#include "PythonPlayer.h"
#include "PythonSafeBox.h"
#include "PythonExchange.h"
#include "Packet.h"

#ifdef ENABLE_CHANGELOOK_SYSTEM

// the server's sizes (game -m32, pack(1); measured on the engine with server-patches/transmutacja, 14 October 2026):
// the look is one DWORD at the end of each; MT2009_PLUS_WIDE_ATTR_V1 (server-patches/wideattr, measured 4 November 2026): each
// of the seven bonus lines is 4 B (WORD type), 7 B more than before
static_assert(sizeof(TPacketGCItemSet2) == 65, "GC item set (21) is 65 B on the server (TPacketGCItemSet)");
static_assert(sizeof(TPacketGCItemUpdate) == 52, "GC item update (25) is 52 B on the server");
static_assert(sizeof(TPacketGCExchange) == 65, "GC exchange is 65 B on the server (packet_exchange)");
#ifdef ENABLE_IKASHOP_RENEWAL
static_assert(sizeof(ikashop::TPlayerItem) == 63, "the server's TPlayerItem (common/tables.h) is 63 B");
#endif

namespace
{
	DWORD s_adwExchangeLook[2][CPythonExchange::EXCHANGE_ITEM_MAX_NUM] = {};	// [0] the target's, [1] mine

	PyObject* playerGetChangeLookVnum(PyObject* poSelf, PyObject* poArgs)
	{
		TItemPos Cell;
		switch (PyTuple_Size(poArgs))
		{
			case 1:
			{
				int iSlotIndex;
				if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
					return Py_BuildException();
				Cell = TItemPos(INVENTORY, iSlotIndex);
				break;
			}
			case 2:
				if (!PyTuple_GetByte(poArgs, 0, &Cell.window_type))
					return Py_BuildException();
				if (!PyTuple_GetInteger(poArgs, 1, &Cell.cell))
					return Py_BuildException();
				break;
			default:
				return Py_BuildException();
		}
		const TItemData* pItem = CPythonPlayer::Instance().GetItemData(Cell);
		return Py_BuildValue("i", (pItem && pItem->vnum) ? pItem->dwTransmutationVnum : 0);
	}

	PyObject* safeboxGetItemChangeLookVnum(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlotIndex;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
			return Py_BuildException();
		TItemData* pItem = NULL;
		if (iSlotIndex < 0 || !CPythonSafeBox::Instance().GetItemDataPtr(iSlotIndex, &pItem) || !pItem || !pItem->vnum)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", pItem->dwTransmutationVnum);
	}

	PyObject* safeboxGetMallItemChangeLookVnum(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlotIndex;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
			return Py_BuildException();
		TItemData* pItem = NULL;
		if (iSlotIndex < 0 || !CPythonSafeBox::Instance().GetMallItemDataPtr(iSlotIndex, &pItem) || !pItem || !pItem->vnum)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", pItem->dwTransmutationVnum);
	}

	PyObject* ExchangeLook(PyObject* poArgs, int iSide)
	{
		int iPos;
		if (!PyTuple_GetInteger(poArgs, 0, &iPos))
			return Py_BuildException();
		if (iPos < 0 || iPos >= CPythonExchange::EXCHANGE_ITEM_MAX_NUM)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", s_adwExchangeLook[iSide][iPos]);
	}

	PyObject* exchangeGetChangeLookVnumFromSelf(PyObject* poSelf, PyObject* poArgs) { return ExchangeLook(poArgs, 1); }
	PyObject* exchangeGetChangeLookVnumFromTarget(PyObject* poSelf, PyObject* poArgs) { return ExchangeLook(poArgs, 0); }

	void AddFunctions(const char* c_szModule, PyMethodDef* pMethods)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (!poModule)
			return;
		for (PyMethodDef* p = pMethods; p->ml_name; ++p)
			PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
	}

	void AddInt(const char* c_szModule, const char* c_szName, long lValue)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (poModule)
			PyModule_AddIntConstant(poModule, c_szName, lValue);
	}
}

// PythonNetworkStreamPhaseGame.cpp, the exchange's item add (is_me: mine)
void Mt2009ChangeLook_SetExchangeItem(bool bSelf, int iPos, DWORD dwLook)
{
	if (iPos >= 0 && iPos < CPythonExchange::EXCHANGE_ITEM_MAX_NUM)
		s_adwExchangeLook[bSelf ? 1 : 0][iPos] = dwLook;
}

// PythonNetworkStreamPhaseGameItem.cpp, the item update: the look of an item already in the bag
void Mt2009ChangeLook_SetItemLook(const TItemPos& c_rCell, DWORD dwLook)
{
	TItemData* pItem = const_cast<TItemData*>(CPythonPlayer::Instance().GetItemData(c_rCell));
	if (pItem)
		pItem->dwTransmutationVnum = dwLook;
}

void Mt2009ChangeLook_RegisterPython()
{
	static PyMethodDef s_playerMethods[] =
	{
		{ "GetChangeLookVnum",		playerGetChangeLookVnum,		METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	static PyMethodDef s_safeboxMethods[] =
	{
		{ "GetItemChangeLookVnum",		safeboxGetItemChangeLookVnum,		METH_VARARGS },
		{ "GetMallItemChangeLookVnum",	safeboxGetMallItemChangeLookVnum,	METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	static PyMethodDef s_exchangeMethods[] =
	{
		{ "GetChangeLookVnumFromSelf",		exchangeGetChangeLookVnumFromSelf,		METH_VARARGS },
		{ "GetChangeLookVnumFromTarget",	exchangeGetChangeLookVnumFromTarget,	METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	AddFunctions("player", s_playerMethods);
	AddFunctions("safebox", s_safeboxMethods);
	AddFunctions("exchange", s_exchangeMethods);
	AddInt("app", "ENABLE_CHANGE_LOOK_SYSTEM", 1);
	AddInt("app", "MT2009_CHANGE_LOOK_EXE", 1);
#ifdef ENABLE_HIDE_COSTUME_SYSTEM
	AddInt("app", "ENABLE_HIDE_COSTUME_SYSTEM", 1);
#endif
}

#endif // ENABLE_CHANGELOOK_SYSTEM
