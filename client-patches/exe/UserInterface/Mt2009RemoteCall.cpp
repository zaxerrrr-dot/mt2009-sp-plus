/*
* MT2009_PLUS_REMOTE_CALL_V1 - Enasir, the summonable storekeeper / merchant (the "Official Remote Call" package by
* Khaled / LungSam, rebuilt for MT2009 PLUS 3.x - server-patches/remotecall/README.md; the server's half is
* remote_call.cpp in the overlay). The server decides everything (the buffs Dozorca / Handlarz Enasir, where he may
* be summoned, the cooldown); the exe only keeps what the server last said and hands it to python.
*
* CG 190 HEADER_CG_REMOTE_CALL (2 B + the sequence byte): HELLO (the state, sent by itself at every game phase),
*   SUMMON, UNSUMMON.
* GC 190 HEADER_GC_REMOTE_CALL (14 B, static):
*   STATE     v0 the storeroom buff's seconds left, v1 the shop buff's seconds left (0 none), v2 bit0 allowed here
*   SUMMONED  v0 the seconds Enasir stays, v1 his VID (his SPAWN motion is played once)
*   GONE      v0 the cooldown's seconds
*   MESSAGE   v0 a code (root uiremotecall.py has the texts)
*   SAFEBOX   the next storeroom window is Enasir's (remoteCall.IsSafeboxRemote)
*   after each: the game window's BINARY_RemoteCall_Event(sub, v0).
* The times are kept as wall-clock ends (time()), so the getters return the seconds left. A new game phase (login,
* warp, channel) forgets everything before the hello - Enasir never survives a map change.
*
* Python module remoteCall:
*   SendPacket(sub)            CG 190 (CG_HELLO / CG_SUMMON / CG_UNSUMMON)
*   GetBuffLeft(kind)          BUFF_SAFEBOX (0) / BUFF_SHOP (1): seconds left, 0 none
*   GetSummonLeft()            seconds Enasir still stays, 0 not summoned
*   GetCoolLeft()              seconds until he can be summoned again
*   GetNpcVID()                his VID (0 none)
*   IsAllowedHere()            1 when the server allows the summoning on this map
*   IsSafeboxRemote(), SetSafeboxRemote(i)
*   Clear()
*   constants CG_*, GC_*, BUFF_SAFEBOX, BUFF_SHOP, MOB_VNUM, SUMMON_SEC, COOLTIME_SEC, MAX_BUFF_SEC
*   app.MT2009_REMOTE_CALL_EXE = 1
*/
#include "StdAfx.h"

#ifdef ENABLE_MT2009_REMOTE_CALL
#include "InstanceBase.h"
#include "PythonCharacterManager.h"
#include "PythonNetworkStream.h"
#include "../GameLib/RaceMotionData.h"

#include <ctime>

namespace
{
	enum
	{
		BUFF_SAFEBOX = 0,
		BUFF_SHOP = 1,
		BUFF_MAX = 2,
		MOB_VNUM = 20874,
		SUMMON_SEC = 180,
		COOLTIME_SEC = 10,
		MAX_BUFF_SEC = 86400000,	// 1000 days
		FLAG_ALLOWED_HERE = 1,
	};

	DWORD	s_adwBuffEnd[BUFF_MAX] = { 0, 0 };
	DWORD	s_dwSummonEnd = 0;
	DWORD	s_dwCoolEnd = 0;
	DWORD	s_dwNpcVID = 0;
	bool	s_bAllowedHere = false;
	bool	s_bSafeboxRemote = false;

	DWORD Now()
	{
		return (DWORD) time(NULL);
	}

	DWORD EndOf(DWORD dwSeconds)
	{
		if (!dwSeconds)
			return 0;
		if (dwSeconds > MAX_BUFF_SEC)
			dwSeconds = MAX_BUFF_SEC;
		return Now() + dwSeconds;
	}

	int LeftOf(DWORD dwEnd)
	{
		const DWORD dwNow = Now();
		return dwEnd > dwNow ? (int) (dwEnd - dwNow) : 0;
	}

	void ClearState()
	{
		s_adwBuffEnd[BUFF_SAFEBOX] = 0;
		s_adwBuffEnd[BUFF_SHOP] = 0;
		s_dwSummonEnd = 0;
		s_dwCoolEnd = 0;
		s_dwNpcVID = 0;
		s_bAllowedHere = false;
		s_bSafeboxRemote = false;
	}

	// ------------------------------------------------------------------------------------------------ python

	PyObject * rcSendPacket(PyObject * poSelf, PyObject * poArgs)
	{
		int iSub;
		if (!PyTuple_GetInteger(poArgs, 0, &iSub))
			return Py_BuildException();
		if (iSub < REMOTE_CALL_CG_HELLO || iSub > REMOTE_CALL_CG_UNSUMMON)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", CPythonNetworkStream::Instance().SendRemoteCallPacket((BYTE) iSub) ? 1 : 0);
	}

	PyObject * rcGetBuffLeft(PyObject * poSelf, PyObject * poArgs)
	{
		int iKind;
		if (!PyTuple_GetInteger(poArgs, 0, &iKind))
			return Py_BuildException();
		if (iKind < 0 || iKind >= BUFF_MAX)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", LeftOf(s_adwBuffEnd[iKind]));
	}

	PyObject * rcGetSummonLeft(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", s_dwNpcVID ? LeftOf(s_dwSummonEnd) : 0);
	}

	PyObject * rcGetCoolLeft(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", LeftOf(s_dwCoolEnd));
	}

	PyObject * rcGetNpcVID(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", (int) s_dwNpcVID);
	}

	PyObject * rcIsAllowedHere(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", s_bAllowedHere ? 1 : 0);
	}

	PyObject * rcIsSafeboxRemote(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", s_bSafeboxRemote ? 1 : 0);
	}

	PyObject * rcSetSafeboxRemote(PyObject * poSelf, PyObject * poArgs)
	{
		int iOn;
		if (!PyTuple_GetInteger(poArgs, 0, &iOn))
			return Py_BuildException();
		s_bSafeboxRemote = iOn != 0;
		return Py_BuildNone();
	}

	PyObject * rcClear(PyObject * poSelf, PyObject * poArgs)
	{
		ClearState();
		return Py_BuildNone();
	}
}

// ---------------------------------------------------------------------------------------------- CPythonNetworkStream

bool CPythonNetworkStream::SendRemoteCallPacket(BYTE bSubHeader)
{
	TPacketCGRemoteCall kPacket;
	kPacket.bHeader = HEADER_CG_REMOTE_CALL;
	kPacket.bSubHeader = bSubHeader;
	if (!Send(sizeof(kPacket), &kPacket))
	{
		Tracef("SendRemoteCallPacket Error\n");
		return false;
	}
	return SendSequence();
}

bool CPythonNetworkStream::RecvRemoteCallPacket()
{
	TPacketGCRemoteCall kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;

	switch (kPacket.bSubHeader)
	{
		case REMOTE_CALL_GC_STATE:
			s_adwBuffEnd[BUFF_SAFEBOX] = EndOf(kPacket.dwValue0);
			s_adwBuffEnd[BUFF_SHOP] = EndOf(kPacket.dwValue1);
			s_bAllowedHere = (kPacket.dwValue2 & FLAG_ALLOWED_HERE) != 0;
			break;

		case REMOTE_CALL_GC_SUMMONED:
		{
			s_dwSummonEnd = EndOf(kPacket.dwValue0);
			s_dwNpcVID = kPacket.dwValue1;
			s_dwCoolEnd = 0;
			// the server shows him before this packet: his add packet came first
			CInstanceBase * pkNpc = s_dwNpcVID ? CPythonCharacterManager::Instance().GetInstancePtr(s_dwNpcVID) : NULL;
			if (pkNpc)
				pkNpc->PushOnceMotion(CRaceMotionData::NAME_SPAWN);
			break;
		}

		case REMOTE_CALL_GC_GONE:
			s_dwSummonEnd = 0;
			s_dwNpcVID = 0;
			s_dwCoolEnd = EndOf(kPacket.dwValue0);
			break;

		case REMOTE_CALL_GC_MESSAGE:
			break;

		case REMOTE_CALL_GC_SAFEBOX:
			s_bSafeboxRemote = true;
			break;

		default:
			return true;
	}

	if (m_apoPhaseWnd[PHASE_WINDOW_GAME])
		PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "BINARY_RemoteCall_Event",
			Py_BuildValue("(ii)", (int) kPacket.bSubHeader, (int) kPacket.dwValue0));
	return true;
}

// ------------------------------------------------------------------------------------------------------------ hooks

// PythonNetworkStreamPhaseGame.cpp SetGamePhase: a new game (login, warp, channel) - nothing of the old one stays; the hello
void Mt2009RemoteCall_OnGamePhase()
{
	ClearState();
	CPythonNetworkStream::Instance().SendRemoteCallPacket(REMOTE_CALL_CG_HELLO);
}

// UserInterface.cpp, after the modules: module remoteCall, app.MT2009_REMOTE_CALL_EXE
void Mt2009RemoteCall_RegisterPython()
{
	static PyMethodDef s_methods[] =
	{
		{ "SendPacket",			rcSendPacket,			METH_VARARGS },
		{ "GetBuffLeft",		rcGetBuffLeft,			METH_VARARGS },
		{ "GetSummonLeft",		rcGetSummonLeft,		METH_VARARGS },
		{ "GetCoolLeft",		rcGetCoolLeft,			METH_VARARGS },
		{ "GetNpcVID",			rcGetNpcVID,			METH_VARARGS },
		{ "IsAllowedHere",		rcIsAllowedHere,		METH_VARARGS },
		{ "IsSafeboxRemote",	rcIsSafeboxRemote,		METH_VARARGS },
		{ "SetSafeboxRemote",	rcSetSafeboxRemote,		METH_VARARGS },
		{ "Clear",				rcClear,				METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	PyObject * poModule = Py_InitModule("remoteCall", s_methods);
	PyModule_AddIntConstant(poModule, "CG_HELLO", REMOTE_CALL_CG_HELLO);
	PyModule_AddIntConstant(poModule, "CG_SUMMON", REMOTE_CALL_CG_SUMMON);
	PyModule_AddIntConstant(poModule, "CG_UNSUMMON", REMOTE_CALL_CG_UNSUMMON);
	PyModule_AddIntConstant(poModule, "GC_STATE", REMOTE_CALL_GC_STATE);
	PyModule_AddIntConstant(poModule, "GC_SUMMONED", REMOTE_CALL_GC_SUMMONED);
	PyModule_AddIntConstant(poModule, "GC_GONE", REMOTE_CALL_GC_GONE);
	PyModule_AddIntConstant(poModule, "GC_MESSAGE", REMOTE_CALL_GC_MESSAGE);
	PyModule_AddIntConstant(poModule, "GC_SAFEBOX", REMOTE_CALL_GC_SAFEBOX);
	PyModule_AddIntConstant(poModule, "BUFF_SAFEBOX", BUFF_SAFEBOX);
	PyModule_AddIntConstant(poModule, "BUFF_SHOP", BUFF_SHOP);
	PyModule_AddIntConstant(poModule, "MOB_VNUM", MOB_VNUM);
	PyModule_AddIntConstant(poModule, "SUMMON_SEC", SUMMON_SEC);
	PyModule_AddIntConstant(poModule, "COOLTIME_SEC", COOLTIME_SEC);
	PyModule_AddIntConstant(poModule, "MAX_BUFF_SEC", MAX_BUFF_SEC);
	PyObject * poApp = PyImport_AddModule("app");	// borrowed
	if (poApp)
		PyModule_AddIntConstant(poApp, "MT2009_REMOTE_CALL_EXE", 1);
}
#else
void Mt2009RemoteCall_RegisterPython() {}
void Mt2009RemoteCall_OnGamePhase() {}
#endif
