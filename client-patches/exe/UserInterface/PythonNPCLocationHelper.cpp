#include "StdAfx.h"

// MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC (Autor: Best Studio; the package's PythonNPCLocationHelper,
// ported). See PythonNPCLocationHelper.h and client-patches/exe/README.md.

#ifdef ENABLE_NPC_LOCATION_HELPER
#include "PythonNPCLocationHelper.h"
#include "PythonNetworkStream.h"
#include "../EterPack/EterPackManager.h"

namespace
{
	// The one instance (CSingleton keeps the pointer); made before python starts, lives as long as the exe.
	CPythonNPCLocationHelper gs_kNPCLocationHelper;
}

CPythonNPCLocationHelper::CPythonNPCLocationHelper()
{
	Clear();
}

void CPythonNPCLocationHelper::Clear()
{
	m_bActive = false;
	m_dwCooldownRemain = 0;
	m_dwCooldownStamp = 0;
	m_bLastResult = 0;
	m_iCurrentMapIndex = 0;
}

void CPythonNPCLocationHelper::SetStatus(const TPacketGCNPCLocationHelper& rkPacket)
{
	m_bActive = rkPacket.active != 0;
	m_dwCooldownRemain = rkPacket.cooldownRemain;
	m_dwCooldownStamp = ELTimer_GetMSec();
	if (NPC_LOCATION_HELPER_GC_STATUS == rkPacket.subheader && rkPacket.mapIndex > 0)
		m_iCurrentMapIndex = rkPacket.mapIndex;
}

void CPythonNPCLocationHelper::SetWarpResult(const TPacketGCNPCLocationHelper& rkPacket)
{
	SetStatus(rkPacket);
	m_bLastResult = rkPacket.result;
}

DWORD CPythonNPCLocationHelper::GetCooldownRemain() const
{
	// counts down between the server's packets (seconds)
	const DWORD dwPassed = (ELTimer_GetMSec() - m_dwCooldownStamp) / 1000;
	return dwPassed >= m_dwCooldownRemain ? 0 : m_dwCooldownRemain - dwPassed;
}

//////////////////////////////////////////////////////////////////////////////////////////////
// network (declared in PythonNetworkStream.h)

bool CPythonNetworkStream::SendNPCLocationHelperPacket(BYTE bSubHeader, int iMapIndex, DWORD dwVnum, int iX, int iY)
{
	TPacketCGNPCLocationHelper packet;
	packet.header = HEADER_CG_NPC_LOCATION_HELPER;
	packet.subheader = bSubHeader;
	packet.mapIndex = iMapIndex;
	packet.vnum = dwVnum;
	packet.x = iX;
	packet.y = iY;

	if (!Send(sizeof(packet), &packet))
		return false;

	return SendSequence();
}

bool CPythonNetworkStream::RecvNPCLocationHelperPacket()
{
	TPacketGCNPCLocationHelper packet;
	if (!Recv(sizeof(packet), &packet))
		return false;

	CPythonNPCLocationHelper& rkHelper = CPythonNPCLocationHelper::Instance();
	PyObject* poGame = m_apoPhaseWnd[PHASE_WINDOW_GAME];

	switch (packet.subheader)
	{
		case NPC_LOCATION_HELPER_GC_STATUS:
			rkHelper.SetStatus(packet);
			if (poGame)
				PyCallClassMemberFunc(poGame, "RefreshNPCLocationHelperStatus", Py_BuildValue("()"));
			break;

		case NPC_LOCATION_HELPER_GC_WARP_RESULT:
			rkHelper.SetWarpResult(packet);
			if (poGame)
				PyCallClassMemberFunc(poGame, "OnNPCLocationHelperWarpResult", Py_BuildValue("(i)", (int)packet.result));
			break;

		case NPC_LOCATION_HELPER_GC_GUILD_LAND:
			if (poGame)
				PyCallClassMemberFunc(poGame, "RefreshNPCLocationHelperGuildLand", Py_BuildValue("(ii)", packet.mapIndex, (int)packet.result));
			break;
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////////////////////////
// module npcLocationHelper

PyObject* npcLocationHelperRequestStatus(PyObject* poSelf, PyObject* poArgs)
{
	CPythonNetworkStream::Instance().SendNPCLocationHelperPacket(NPC_LOCATION_HELPER_CG_REQUEST_STATUS, 0, 0, 0, 0);
	return Py_BuildNone();
}

// WarpToNPC(mapIndex, vnum, x, y) - x/y local metres, as in the point files / 100
PyObject* npcLocationHelperWarpToNPC(PyObject* poSelf, PyObject* poArgs)
{
	int iMapIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iMapIndex))
		return Py_BuildException();
	int iVnum;
	if (!PyTuple_GetInteger(poArgs, 1, &iVnum))
		return Py_BuildException();
	int iX;
	if (!PyTuple_GetInteger(poArgs, 2, &iX))
		return Py_BuildException();
	int iY;
	if (!PyTuple_GetInteger(poArgs, 3, &iY))
		return Py_BuildException();

	CPythonNetworkStream::Instance().SendNPCLocationHelperPacket(NPC_LOCATION_HELPER_CG_WARP_TO_NPC, iMapIndex, (DWORD)iVnum, iX, iY);
	return Py_BuildNone();
}

PyObject* npcLocationHelperUseTicket(PyObject* poSelf, PyObject* poArgs)
{
	CPythonNetworkStream::Instance().SendNPCLocationHelperPacket(NPC_LOCATION_HELPER_CG_USE_TICKET, 0, 0, 0, 0);
	return Py_BuildNone();
}

PyObject* npcLocationHelperRequestGuildLand(PyObject* poSelf, PyObject* poArgs)
{
	int iMapIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iMapIndex))
		return Py_BuildException();

	CPythonNetworkStream::Instance().SendNPCLocationHelperPacket(NPC_LOCATION_HELPER_CG_REQUEST_GUILD_LAND, iMapIndex, 0, 0, 0);
	return Py_BuildNone();
}

PyObject* npcLocationHelperIsActive(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonNPCLocationHelper::Instance().IsActive() ? 1 : 0);
}

PyObject* npcLocationHelperGetCooldownRemain(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int)CPythonNPCLocationHelper::Instance().GetCooldownRemain());
}

PyObject* npcLocationHelperGetLastResult(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int)CPythonNPCLocationHelper::Instance().GetLastResult());
}

// The map index the server last reported for the character (STATUS packet); 0 = not known yet.
PyObject* npcLocationHelperGetCurrentMapIndex(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonNPCLocationHelper::Instance().GetCurrentMapIndex());
}

// ReadTextFile(path) -> list of lines (no CR/LF); from the packs, else from the disk; [] when missing
PyObject* npcLocationHelperReadTextFile(PyObject* poSelf, PyObject* poArgs)
{
	char* szFileName;
	if (!PyTuple_GetString(poArgs, 0, &szFileName))
		return Py_BuildException();

	PyObject* poList = PyList_New(0);

	CMappedFile file;
	LPCVOID pvData = NULL;
	if (!CEterPackManager::Instance().Get(file, szFileName, &pvData) || !pvData)
		return poList;

	const char* pData = static_cast<const char*>(pvData);
	const DWORD dwSize = file.Size();
	std::string line;

	for (DWORD i = 0; i < dwSize; ++i)
	{
		const char ch = pData[i];
		if (ch == '\n')
		{
			PyObject* poLine = Py_BuildValue("s", line.c_str());
			PyList_Append(poList, poLine);
			Py_DECREF(poLine);
			line.clear();
		}
		else if (ch != '\r')
		{
			line.push_back(ch);
		}
	}

	if (!line.empty())
	{
		PyObject* poLine = Py_BuildValue("s", line.c_str());
		PyList_Append(poList, poLine);
		Py_DECREF(poLine);
	}

	return poList;
}

void initNPCLocationHelper()
{
	static PyMethodDef s_methods[] =
	{
		{ "RequestStatus",			npcLocationHelperRequestStatus,			METH_VARARGS },
		{ "WarpToNPC",				npcLocationHelperWarpToNPC,				METH_VARARGS },
		{ "UseTicket",				npcLocationHelperUseTicket,				METH_VARARGS },
		{ "RequestGuildLand",		npcLocationHelperRequestGuildLand,		METH_VARARGS },
		{ "IsActive",				npcLocationHelperIsActive,				METH_VARARGS },
		{ "GetCooldownRemain",		npcLocationHelperGetCooldownRemain,		METH_VARARGS },
		{ "GetLastResult",			npcLocationHelperGetLastResult,			METH_VARARGS },
		{ "GetCurrentMapIndex",		npcLocationHelperGetCurrentMapIndex,	METH_VARARGS },
		{ "ReadTextFile",			npcLocationHelperReadTextFile,			METH_VARARGS },
		{ NULL, NULL, 0 },
	};

	PyObject* poModule = Py_InitModule("npcLocationHelper", s_methods);
	PyModule_AddIntConstant(poModule, "CG_REQUEST_STATUS", NPC_LOCATION_HELPER_CG_REQUEST_STATUS);
	PyModule_AddIntConstant(poModule, "CG_WARP_TO_NPC", NPC_LOCATION_HELPER_CG_WARP_TO_NPC);
	PyModule_AddIntConstant(poModule, "CG_USE_TICKET", NPC_LOCATION_HELPER_CG_USE_TICKET);
	PyModule_AddIntConstant(poModule, "CG_REQUEST_GUILD_LAND", NPC_LOCATION_HELPER_CG_REQUEST_GUILD_LAND);
	PyModule_AddIntConstant(poModule, "GC_STATUS", NPC_LOCATION_HELPER_GC_STATUS);
	PyModule_AddIntConstant(poModule, "GC_WARP_RESULT", NPC_LOCATION_HELPER_GC_WARP_RESULT);
	PyModule_AddIntConstant(poModule, "GC_GUILD_LAND", NPC_LOCATION_HELPER_GC_GUILD_LAND);
	PyModule_AddIntConstant(poModule, "RESULT_OK", 0);
	PyModule_AddIntConstant(poModule, "RESULT_NOT_ACTIVE", 1);
	PyModule_AddIntConstant(poModule, "RESULT_CANNOT_USE", 2);
	PyModule_AddIntConstant(poModule, "RESULT_COOLDOWN", 3);
	PyModule_AddIntConstant(poModule, "RESULT_INVALID_TARGET", 4);
	PyModule_AddIntConstant(poModule, "RESULT_LEVEL_LIMIT", 5);
	PyModule_AddIntConstant(poModule, "RESULT_EMPIRE_LIMIT", 6);
	PyModule_AddIntConstant(poModule, "RESULT_NEED_ITEM", 7);
	PyModule_AddIntConstant(poModule, "RESULT_NEED_YANG", 8);
	PyModule_AddIntConstant(poModule, "ATLAS_SCALE_MIN", 1);
	PyModule_AddIntConstant(poModule, "ATLAS_SCALE_MAX", 3);
}
#endif
