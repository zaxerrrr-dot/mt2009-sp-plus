#pragma once

// MT2009_PLUS_EVENT_MANAGER_V1 - the in-game event list (after Owsap's
// PythonInGameEventSystemManager, v6.2.6), made generic: an event is a string
// key ("catchking", "rumi", "easter", ...) with on/off, start, end, reward
// window end and a figure, exactly as the server's HEADER_GC_INGAME_EVENT
// brings it (server: playerbot_ingame_events.h). The exe keeps the list and
// hands it to python (module ingameEventSystem); what an event is called, its
// icon and its window are python's (root/uiingameevent.py), so a new event
// needs no new exe. See client-patches/exe/README.md.

#ifdef ENABLE_INGAME_EVENT_MANAGER
#include "Packet.h"

class CPythonInGameEventSystemManager : public CSingleton<CPythonInGameEventSystemManager>
{
	public:
		typedef struct SInGameEvent
		{
			std::string	strKey;
			bool		bEnable;
			DWORD		dwStartTime;
			DWORD		dwEndTime;
			DWORD		dwRewardEndTime;
			int			iValue;

			SInGameEvent() : bEnable(false), dwStartTime(0), dwEndTime(0), dwRewardEndTime(0), iValue(0) {}
		} TInGameEvent;

	public:
		CPythonInGameEventSystemManager();
		virtual ~CPythonInGameEventSystemManager();

		void	Destroy();
		void	Clear();

		// The python object told of every change: its RefreshInGameEvent(True)
		// (Owsap's name). False without one - the network stream then calls
		// the game window's BINARY_RefreshInGameEvent().
		void	SetInGameEventHandler(PyObject* poHandler);
		void	DestroyInGameEventHandler();
		bool	NotifyHandler();

		// The server's list: BeginList empties it first (a whole list), then
		// SetEvent for each event in the packet.
		void	BeginList();
		void	SetEvent(const char* c_szKey, bool bEnable, DWORD dwStart, DWORD dwEnd, DWORD dwRewardEnd, int iValue);
		bool	RemoveEvent(const char* c_szKey);

		size_t	GetEventCount() const { return m_vecEvents.size(); }
		const TInGameEvent* GetEventByIndex(size_t index) const;
		const TInGameEvent* GetEvent(const char* c_szKey) const;
		size_t	GetActiveEventCount() const;

	protected:
		std::vector<TInGameEvent>	m_vecEvents;	// in the server's order
		PyObject*					m_poHandler;
};
#endif
