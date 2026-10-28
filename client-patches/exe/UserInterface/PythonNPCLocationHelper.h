#pragma once

// MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC (the improved world map; Autor: Best Studio, ported to our
// exe). Keeps what the server told about the character's helper (active, warp cooldown, last warp result, the map
// index the character is on) and gives python the module npcLocationHelper. The atlas part lives in PythonMiniMap.
// See client-patches/exe/README.md.

#ifdef ENABLE_NPC_LOCATION_HELPER
#include "Packet.h"

class CPythonNPCLocationHelper : public CSingleton<CPythonNPCLocationHelper>
{
	public:
		CPythonNPCLocationHelper();
		virtual ~CPythonNPCLocationHelper() {}

		void	Clear();
		void	SetStatus(const TPacketGCNPCLocationHelper& rkPacket);
		void	SetWarpResult(const TPacketGCNPCLocationHelper& rkPacket);

		bool	IsActive() const				{ return m_bActive; }
		DWORD	GetCooldownRemain() const;
		BYTE	GetLastResult() const			{ return m_bLastResult; }
		int		GetCurrentMapIndex() const		{ return m_iCurrentMapIndex; }

	private:
		bool	m_bActive;
		DWORD	m_dwCooldownRemain;
		DWORD	m_dwCooldownStamp;	// ELTimer ms when m_dwCooldownRemain came
		BYTE	m_bLastResult;
		int		m_iCurrentMapIndex;
};
#endif
