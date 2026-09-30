#include "StdAfx.h"

// MT2009_PLUS_EVENT_MANAGER_V1 - see PythonInGameEventSystemManager.h and
// client-patches/exe/README.md.

#ifdef ENABLE_INGAME_EVENT_MANAGER
#include "PythonInGameEventSystemManager.h"

CPythonInGameEventSystemManager::CPythonInGameEventSystemManager()
	: m_poHandler(NULL)
{
}

CPythonInGameEventSystemManager::~CPythonInGameEventSystemManager()
{
	Destroy();
}

void CPythonInGameEventSystemManager::Destroy()
{
	m_vecEvents.clear();
	DestroyInGameEventHandler();
}

void CPythonInGameEventSystemManager::Clear()
{
	m_vecEvents.clear();
}

void CPythonInGameEventSystemManager::SetInGameEventHandler(PyObject* poHandler)
{
	if (poHandler == m_poHandler)
		return;
	// Held, unlike Owsap's raw pointer: a window python has dropped without
	// DestroyInGameEventHandler must not be called after it is gone.
	Py_XINCREF(poHandler);
	PyObject* poOld = m_poHandler;
	m_poHandler = poHandler;
	Py_XDECREF(poOld);
}

void CPythonInGameEventSystemManager::DestroyInGameEventHandler()
{
	PyObject* poOld = m_poHandler;
	m_poHandler = NULL;
	Py_XDECREF(poOld);
}

bool CPythonInGameEventSystemManager::NotifyHandler()
{
	if (!m_poHandler)
		return false;
	PyCallClassMemberFunc(m_poHandler, "RefreshInGameEvent", Py_BuildValue("(i)", 1));
	return true;
}

void CPythonInGameEventSystemManager::BeginList()
{
	m_vecEvents.clear();
}

void CPythonInGameEventSystemManager::SetEvent(const char* c_szKey, bool bEnable, DWORD dwStart, DWORD dwEnd, DWORD dwRewardEnd, int iValue)
{
	if (!c_szKey || !*c_szKey)
		return;
	TInGameEvent* pkEvent = NULL;
	for (size_t i = 0; i < m_vecEvents.size(); ++i)
	{
		if (m_vecEvents[i].strKey == c_szKey)
		{
			pkEvent = &m_vecEvents[i];
			break;
		}
	}
	if (!pkEvent)
	{
		m_vecEvents.push_back(TInGameEvent());
		pkEvent = &m_vecEvents.back();
		pkEvent->strKey = c_szKey;
	}
	pkEvent->bEnable = bEnable;
	pkEvent->dwStartTime = dwStart;
	pkEvent->dwEndTime = dwEnd;
	pkEvent->dwRewardEndTime = dwRewardEnd;
	pkEvent->iValue = iValue;
}

bool CPythonInGameEventSystemManager::RemoveEvent(const char* c_szKey)
{
	if (!c_szKey)
		return false;
	for (std::vector<TInGameEvent>::iterator it = m_vecEvents.begin(); it != m_vecEvents.end(); ++it)
	{
		if (it->strKey == c_szKey)
		{
			m_vecEvents.erase(it);
			return true;
		}
	}
	return false;
}

const CPythonInGameEventSystemManager::TInGameEvent* CPythonInGameEventSystemManager::GetEventByIndex(size_t index) const
{
	return index < m_vecEvents.size() ? &m_vecEvents[index] : NULL;
}

const CPythonInGameEventSystemManager::TInGameEvent* CPythonInGameEventSystemManager::GetEvent(const char* c_szKey) const
{
	if (!c_szKey)
		return NULL;
	for (size_t i = 0; i < m_vecEvents.size(); ++i)
		if (m_vecEvents[i].strKey == c_szKey)
			return &m_vecEvents[i];
	return NULL;
}

size_t CPythonInGameEventSystemManager::GetActiveEventCount() const
{
	size_t count = 0;
	for (size_t i = 0; i < m_vecEvents.size(); ++i)
		if (m_vecEvents[i].bEnable)
			++count;
	return count;
}

// ---------------------------------------------------------------- python

static const CPythonInGameEventSystemManager::TInGameEvent* __GetEventArg(PyObject* poArgs)
{
	char* szKey;
	if (!PyTuple_GetString(poArgs, 0, &szKey))
		return NULL;
	return CPythonInGameEventSystemManager::Instance().GetEvent(szKey);
}

PyObject* ingameEventSystemSetInGameEventHandler(PyObject* poSelf, PyObject* poArgs)
{
	PyObject* poHandler;
	if (!PyTuple_GetObject(poArgs, 0, &poHandler))
		return Py_BuildException();
	if (poHandler == Py_None)
		CPythonInGameEventSystemManager::Instance().DestroyInGameEventHandler();
	else
		CPythonInGameEventSystemManager::Instance().SetInGameEventHandler(poHandler);
	return Py_BuildNone();
}

PyObject* ingameEventSystemDestroyInGameEventHandler(PyObject* poSelf, PyObject* poArgs)
{
	CPythonInGameEventSystemManager::Instance().DestroyInGameEventHandler();
	return Py_BuildNone();
}

PyObject* ingameEventSystemClear(PyObject* poSelf, PyObject* poArgs)
{
	CPythonInGameEventSystemManager::Instance().Clear();
	return Py_BuildNone();
}

PyObject* ingameEventSystemGetEventCount(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int)CPythonInGameEventSystemManager::Instance().GetEventCount());
}

PyObject* ingameEventSystemGetActiveEventCount(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int)CPythonInGameEventSystemManager::Instance().GetActiveEventCount());
}

PyObject* ingameEventSystemGetEventKey(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent =
		iIndex >= 0 ? CPythonInGameEventSystemManager::Instance().GetEventByIndex((size_t)iIndex) : NULL;
	return Py_BuildValue("s", pkEvent ? pkEvent->strKey.c_str() : "");
}

PyObject* ingameEventSystemGetActiveEvents(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager& rkMgr = CPythonInGameEventSystemManager::Instance();
	PyObject* poList = PyList_New(0);
	for (size_t i = 0; i < rkMgr.GetEventCount(); ++i)
	{
		const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = rkMgr.GetEventByIndex(i);
		if (!pkEvent || !pkEvent->bEnable)
			continue;
		PyObject* poKey = PyString_FromString(pkEvent->strKey.c_str());
		PyList_Append(poList, poKey);
		Py_DECREF(poKey);
	}
	PyObject* poTuple = PyList_AsTuple(poList);
	Py_DECREF(poList);
	return poTuple;
}

PyObject* ingameEventSystemIsActive(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	return Py_BuildValue("i", pkEvent && pkEvent->bEnable ? 1 : 0);
}

PyObject* ingameEventSystemIsEvent(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", __GetEventArg(poArgs) ? 1 : 0);
}

PyObject* ingameEventSystemGetEventStart(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	return Py_BuildValue("i", pkEvent ? (int)pkEvent->dwStartTime : 0);
}

PyObject* ingameEventSystemGetEventEnd(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	return Py_BuildValue("i", pkEvent ? (int)pkEvent->dwEndTime : 0);
}

PyObject* ingameEventSystemGetEventRewardEnd(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	return Py_BuildValue("i", pkEvent ? (int)pkEvent->dwRewardEndTime : 0);
}

PyObject* ingameEventSystemGetEventValue(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	return Py_BuildValue("i", pkEvent ? pkEvent->iValue : 0);
}

// (enable, start, end, reward end, value); all 0 for an event not in the list.
PyObject* ingameEventSystemGetEventInfo(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonInGameEventSystemManager::TInGameEvent* pkEvent = __GetEventArg(poArgs);
	if (!pkEvent)
		return Py_BuildValue("(iiiii)", 0, 0, 0, 0, 0);
	return Py_BuildValue("(iiiii)", pkEvent->bEnable ? 1 : 0, (int)pkEvent->dwStartTime, (int)pkEvent->dwEndTime,
		(int)pkEvent->dwRewardEndTime, pkEvent->iValue);
}

// SetEvent(key, enable, start, end, rewardEnd, value): python may feed the
// list itself (the chat-line fallback, Owsap's "<flag> <value>" commands).
PyObject* ingameEventSystemSetEvent(PyObject* poSelf, PyObject* poArgs)
{
	char* szKey;
	if (!PyTuple_GetString(poArgs, 0, &szKey))
		return Py_BuildException();
	int iEnable = 0, iStart = 0, iEnd = 0, iRewardEnd = 0, iValue = 0;
	if (!PyTuple_GetInteger(poArgs, 1, &iEnable))
		return Py_BuildException();
	PyTuple_GetInteger(poArgs, 2, &iStart);
	PyTuple_GetInteger(poArgs, 3, &iEnd);
	PyTuple_GetInteger(poArgs, 4, &iRewardEnd);
	PyTuple_GetInteger(poArgs, 5, &iValue);
	if (strlen(szKey) > INGAME_EVENT_KEY_MAX_LEN)
		return Py_BuildException("ingameEventSystem.SetEvent: key longer than %d", INGAME_EVENT_KEY_MAX_LEN);
	CPythonInGameEventSystemManager::Instance().SetEvent(szKey, iEnable != 0, (DWORD)iStart, (DWORD)iEnd, (DWORD)iRewardEnd, iValue);
	return Py_BuildNone();
}

PyObject* ingameEventSystemRemoveEvent(PyObject* poSelf, PyObject* poArgs)
{
	char* szKey;
	if (!PyTuple_GetString(poArgs, 0, &szKey))
		return Py_BuildException();
	return Py_BuildValue("i", CPythonInGameEventSystemManager::Instance().RemoveEvent(szKey) ? 1 : 0);
}

void initInGameEventSystem()
{
	static PyMethodDef s_methods[] =
	{
		{ "SetInGameEventHandler",		ingameEventSystemSetInGameEventHandler,		METH_VARARGS },
		// Owsap's spelling of the same.
		{ "SetIngameEventHandler",		ingameEventSystemSetInGameEventHandler,		METH_VARARGS },
		{ "DestroyInGameEventHandler",	ingameEventSystemDestroyInGameEventHandler,	METH_VARARGS },
		{ "Clear",						ingameEventSystemClear,						METH_VARARGS },
		{ "GetEventCount",				ingameEventSystemGetEventCount,				METH_VARARGS },
		{ "GetActiveEventCount",		ingameEventSystemGetActiveEventCount,		METH_VARARGS },
		{ "GetEventKey",				ingameEventSystemGetEventKey,				METH_VARARGS },
		{ "GetActiveEvents",			ingameEventSystemGetActiveEvents,			METH_VARARGS },
		{ "IsActive",					ingameEventSystemIsActive,					METH_VARARGS },
		{ "IsEventActive",				ingameEventSystemIsActive,					METH_VARARGS },
		{ "IsEvent",					ingameEventSystemIsEvent,					METH_VARARGS },
		{ "GetEventStart",				ingameEventSystemGetEventStart,				METH_VARARGS },
		{ "GetEventEnd",				ingameEventSystemGetEventEnd,				METH_VARARGS },
		{ "GetEventEndTime",			ingameEventSystemGetEventEnd,				METH_VARARGS },
		{ "GetEventRewardEnd",			ingameEventSystemGetEventRewardEnd,			METH_VARARGS },
		{ "GetEventValue",				ingameEventSystemGetEventValue,				METH_VARARGS },
		{ "GetEventInfo",				ingameEventSystemGetEventInfo,				METH_VARARGS },
		{ "SetEvent",					ingameEventSystemSetEvent,					METH_VARARGS },
		{ "RemoveEvent",				ingameEventSystemRemoveEvent,				METH_VARARGS },
		{ NULL, NULL, 0 },
	};

	PyObject* poModule = Py_InitModule("ingameEventSystem", s_methods);
	PyModule_AddIntConstant(poModule, "KEY_MAX_LEN", INGAME_EVENT_KEY_MAX_LEN);
	// The protocol's version: python says hello with the packet only when the
	// exe has this module.
	PyModule_AddIntConstant(poModule, "VERSION", 1);
}
#endif
