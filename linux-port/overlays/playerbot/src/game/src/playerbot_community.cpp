// MT2009_PLUS_COMMUNITY_V1: the Community window - one window for friends (friends / blocked / requests),
// the guild and the settings, with a status message, an online / AFK / auto hunt / "appear offline" state
// and each friend's level and location. The idea and the window come from "Community System (Messenger
// Renewal)" (Autor: Best Studio, github.com/ybeststudio), which was written for another engine (its own
// messenger packets and CHARACTER members); here it is built on our messenger without changing a single
// existing packet. server-patches/community/README.md.
//
// New file outside the engine's own; the hooks are server-patches/community (edits.json), which also defines
// __MESSENGER_RENEWAL__ (CommonDefines.h) and the members of MessengerManager used here (messenger_manager.h).
//
// The client (root/uicommunity.py) talks with chat commands, so an older exe works as it is:
//   client -> "/community hello"            the window is there: from now on this character gets the lines below
//             "/community state <0|1|4>"    the state the player chose: 0 online, 1 AFK, 4 appear offline (saved)
//             "/community auto <0|1>"       Auto Lowy on / off (state 2 while the chosen state is "online")
//             "/community status [text]"    the status message (at most 50 bytes; empty = delete; saved)
//             "/community privacy <flags>"  8 = do not show my level, 16 = do not show my location (saved)
//             "/community guild"            the location of each online guild member
//             "/community party <name>"     a party invitation to a friend on the same map
//   server -> "community_my <state> <privacy> [status]"
//             "community_friend <name> <state> <level> <champion level> <channel> <map index> [status]"
//             "community_guild <pid>:<channel>:<map index> ..." (at most 20 per line)
//             "community_request <name> <level> <champion level> <channel> <map index>" (before "messenger_auth")
// The status message is the last field (it may have spaces). A friend who is offline - or "appears offline" -
// has state 4 and no level / location; the messenger itself also shows him offline (SendList / SendLogin /
// SendLogout), also to the old window and to an older client.
//
// The cores keep each other up to date with HEADER_GG_COMMUNITY (40): the state, privacy, level and status of
// a character, sent by its core when it logs in and when one of them changes; the channel and map of a
// character on another core are the P2P login's (CCI). player.status_message / player.community_flags
// (mariadb/playerbot/community.sql) keep the message and the chosen state + privacy between logins
// (community_flags: bits 0-2 the chosen state 0/1/4, 8 hide level, 16 hide location).
//
// Bots: they have a descriptor that drops every packet and never send "/community"; nothing is sent to a
// bot (CommunityIsClient), and a bot friend shows as any friend (online, its level and map).
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "locale_service.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "p2p.h"
#include "db.h"
#include "guild.h"
#include "banword.h"
#include "cmd.h"
#include "packet.h"
#include "messenger_manager.h"

#ifdef __MESSENGER_RENEWAL__

namespace
{
	enum
	{
		COMMUNITY_STATE_CONNECT = 0,
		COMMUNITY_STATE_LEFT_SEAT = 1,
		COMMUNITY_STATE_AUTO_HUNT = 2,
		COMMUNITY_STATE_SHOP_OPEN = 3,
		COMMUNITY_STATE_DISCONNECT = 4,

		COMMUNITY_FLAG_STATE_MASK = 0x07,
		COMMUNITY_FLAG_HIDE_LEVEL = 0x08,
		COMMUNITY_FLAG_HIDE_LOCATION = 0x10,
		COMMUNITY_FLAG_PRIVACY_MASK = COMMUNITY_FLAG_HIDE_LEVEL | COMMUNITY_FLAG_HIDE_LOCATION,

		COMMUNITY_GUILD_PER_LINE = 20,
	};

	enum ECommunityPulse
	{
		COMMUNITY_PULSE_STATE,
		COMMUNITY_PULSE_STATUS,
		COMMUNITY_PULSE_GUILD,
		COMMUNITY_PULSE_PARTY,
		COMMUNITY_PULSE_HELLO,
		COMMUNITY_PULSE_MAX,
	};

	// pid -> the last time (get_dword_time) of each kind of command
	std::map<DWORD, std::vector<DWORD> > s_mapCommunityPulse;

	bool CommunityThrottle(LPCHARACTER ch, ECommunityPulse ePulse, DWORD dwMs)
	{
		std::vector<DWORD>& v = s_mapCommunityPulse[ch->GetPlayerID()];
		if (v.size() < COMMUNITY_PULSE_MAX)
			v.resize(COMMUNITY_PULSE_MAX, 0);
		const DWORD dwNow = get_dword_time();
		if (v[ePulse] && dwNow - v[ePulse] < dwMs)
			return false;
		v[ePulse] = dwNow;
		return true;
	}

	// A real player's client: a character with a descriptor that is not a bot's.
	bool CommunityIsClient(LPCHARACTER ch)
	{
		return ch && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	BYTE CommunityChosenState(BYTE bFlags)
	{
		const BYTE b = bFlags & COMMUNITY_FLAG_STATE_MASK;
		return (b == COMMUNITY_STATE_LEFT_SEAT || b == COMMUNITY_STATE_DISCONNECT) ? b : COMMUNITY_STATE_CONNECT;
	}

	// One line of text: control bytes out, '|' (the client's colour / link codes) out, spaces squeezed,
	// at most COMMUNITY_STATUS_MAX_LEN bytes (a CP1250 letter is one byte).
	std::string CommunitySanitize(const char* c_szText)
	{
		std::string s;
		if (!c_szText)
			return s;
		for (const unsigned char* p = reinterpret_cast<const unsigned char*>(c_szText); *p; ++p)
		{
			unsigned char c = *p;
			if (c < 32 || c == 127 || c == '|')
				c = ' ';
			if (c == ' ' && (s.empty() || s[s.size() - 1] == ' '))
				continue;
			s += static_cast<char>(c);
			if (s.size() >= COMMUNITY_STATUS_MAX_LEN)
				break;
		}
		while (!s.empty() && s[s.size() - 1] == ' ')
			s.erase(s.size() - 1);
		return s;
	}

	const char* CommunitySkipSpaces(const char* p)
	{
		while (p && *p && isspace(static_cast<unsigned char>(*p)))
			++p;
		return p ? p : "";
	}
}

ACMD(do_community)
{
	MessengerManager::instance().CommunityCommand(ch, argument);
}

bool MessengerManager::CommunityIsHidden(MessengerManager::keyA name)
{
	if (m_set_loginAccount.find(name) == m_set_loginAccount.end())
		return false;
	std::map<keyT, SCommunityInfo>::const_iterator it = m_CommunityInfo.find(name);
	return it != m_CommunityInfo.end() && it->second.bState == COMMUNITY_STATE_DISCONNECT;
}

bool MessengerManager::__CommunityWants(MessengerManager::keyA account, LPCHARACTER* ppkChar)
{
	if (m_CommunityHello.find(account) == m_CommunityHello.end())
		return false;
	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	if (!CommunityIsClient(ch))
		return false;
	if (ppkChar)
		*ppkChar = ch;
	return true;
}

// Login(account), every core, before the friend list's query (the same SQL queue, so this answer is read
// first): the account's own message / flags and those of each of its friends.
void MessengerManager::__CommunityLogin(MessengerManager::keyA account)
{
	char szName[CHARACTER_NAME_MAX_LEN * 2 + 1];
	DBManager::instance().EscapeString(szName, sizeof(szName), account.c_str(), account.size());
	if (account.compare(szName))
		return;

	DBManager::instance().FuncQuery(msl::bind1st(std::mem_fn(&MessengerManager::__CommunityLoad), this),
		"SELECT a.name, IFNULL(a.status_message, ''), IFNULL(a.community_flags, 0), c.name, IFNULL(c.status_message, ''), "
		"IFNULL(c.community_flags, 0) FROM player%s AS a LEFT JOIN messenger_list%s AS m ON m.account = a.name "
		"LEFT JOIN player%s AS c ON c.name = m.companion WHERE a.name = '%s'",
		get_table_postfix(), get_table_postfix(), get_table_postfix(), szName);
}

void MessengerManager::__CommunityLoad(SQLMsg* msg)
{
	if (!msg || !msg->Get() || !msg->Get()->pSQLResult || msg->Get()->uiNumRows == 0)
		return;

	std::string strOwn;
	for (uint i = 0; i < msg->Get()->uiNumRows; ++i)
	{
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		if (!row || !row[0])
			continue;

		if (strOwn.empty())
		{
			strOwn = row[0];
			SCommunityInfo& own = m_CommunityInfo[strOwn];
			if (!own.bLive)
			{
				const BYTE bFlags = static_cast<BYTE>(row[2] ? atoi(row[2]) : 0);
				own.strStatus = CommunitySanitize(row[1]);
				own.bFlags = bFlags & COMMUNITY_FLAG_PRIVACY_MASK;
				own.bChosen = CommunityChosenState(bFlags);
				own.bState = own.bChosen;
			}
		}

		if (row[3] && *row[3])
		{
			const std::string strCompanion(row[3]);
			SCommunityInfo& info = m_CommunityInfo[strCompanion];
			// a friend online somewhere has the live values (his core's GG packet); the rest is the database's
			if (!info.bLive)
			{
				const BYTE bFlags = static_cast<BYTE>(row[5] ? atoi(row[5]) : 0);
				info.strStatus = CommunitySanitize(row[4]);
				info.bFlags = bFlags & COMMUNITY_FLAG_PRIVACY_MASK;
				info.bChosen = CommunityChosenState(bFlags);
				info.bState = info.bChosen;
			}
		}
	}

	if (strOwn.empty())
		return;

	// The owner's core: the character is here - its level, then the other cores and the friends hear it.
	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(strOwn.c_str());
	if (!ch || !ch->GetDesc() || m_set_loginAccount.find(strOwn) == m_set_loginAccount.end())
		return;

	SCommunityInfo& own = m_CommunityInfo[strOwn];
	own.bLive = true;
	__CommunityChanged(ch, own.bState, false);
}

void MessengerManager::__CommunityLogout(MessengerManager::keyA account)
{
	m_CommunityHello.erase(account);

	std::map<keyT, SCommunityInfo>::iterator it = m_CommunityInfo.find(account);
	if (it != m_CommunityInfo.end())
	{
		// offline: only the message and the chosen state stay (the next login reads them again)
		it->second.bLive = false;
		it->second.bAuto = false;
		it->second.bState = it->second.bChosen;
	}

	if (LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str()))
		s_mapCommunityPulse.erase(ch->GetPlayerID());
}

void MessengerManager::__CommunitySendMy(LPCHARACTER ch)
{
	LPCHARACTER pkMe = NULL;
	if (!ch || !__CommunityWants(ch->GetName(), &pkMe))
		return;

	const SCommunityInfo& own = m_CommunityInfo[ch->GetName()];
	ch->ChatPacket(CHAT_TYPE_COMMAND, "community_my %u %u %s", own.bState, own.bFlags, own.strStatus.c_str());
}

void MessengerManager::__CommunitySendFriend(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	LPCHARACTER ch = NULL;
	if (companion.empty() || !__CommunityWants(account, &ch))
		return;

	const bool bOnline = m_set_loginAccount.find(companion) != m_set_loginAccount.end() && !CommunityIsHidden(companion);

	std::map<keyT, SCommunityInfo>::const_iterator it = m_CommunityInfo.find(companion);
	const SCommunityInfo kEmpty;
	const SCommunityInfo& info = it != m_CommunityInfo.end() ? it->second : kEmpty;

	BYTE bState = COMMUNITY_STATE_DISCONNECT;
	unsigned int uLevel = 0, uConqueror = 0, uChannel = 0;
	long lMapIndex = 0;

	if (bOnline)
	{
		bState = info.bState;
		if (LPCHARACTER pkCompanion = CHARACTER_MANAGER::instance().FindPC(companion.c_str()))
		{
			uLevel = pkCompanion->GetLevel();
			uConqueror = pkCompanion->GetConquerorLevel();
			uChannel = g_bChannel;
			lMapIndex = pkCompanion->GetMapIndex();
		}
		else
		{
			uLevel = info.bLevel;
			uConqueror = info.bConqueror;
			if (CCI* pkCCI = P2P_MANAGER::instance().Find(companion.c_str()))
			{
				uChannel = pkCCI->bChannel;
				lMapIndex = pkCCI->lMapIndex;
			}
		}

		if (info.bFlags & COMMUNITY_FLAG_HIDE_LEVEL)
			uLevel = uConqueror = 0;
		if (info.bFlags & COMMUNITY_FLAG_HIDE_LOCATION)
		{
			uChannel = 0;
			lMapIndex = 0;
		}
	}

	ch->ChatPacket(CHAT_TYPE_COMMAND, "community_friend %s %u %u %u %u %ld %s", companion.c_str(), bState, uLevel,
		uConqueror, uChannel, lMapIndex, info.strStatus.c_str());
}

void MessengerManager::__CommunitySendFriends(MessengerManager::keyA account)
{
	if (!__CommunityWants(account, NULL))
		return;

	std::map<keyT, std::set<keyT> >::const_iterator it = m_Relation.find(account);
	if (it == m_Relation.end())
		return;

	const std::set<keyT> companions(it->second);
	for (std::set<keyT>::const_iterator c = companions.begin(); c != companions.end(); ++c)
		__CommunitySendFriend(account, *c);
}

// The friends on this core hear about name's change: a friend who has the window gets its line, and when
// "appear offline" was switched on or off every friend's messenger gets a logout / login.
void MessengerManager::__CommunityNotify(MessengerManager::keyA name, BYTE bOldState)
{
	std::map<keyT, std::set<keyT> >::const_iterator it = m_InverseRelation.find(name);
	if (it == m_InverseRelation.end())
		return;

	const bool bWasHidden = bOldState == COMMUNITY_STATE_DISCONNECT;
	const bool bIsHidden = CommunityIsHidden(name);
	const std::set<keyT> accounts(it->second);

	for (std::set<keyT>::const_iterator a = accounts.begin(); a != accounts.end(); ++a)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(a->c_str());
		if (!CommunityIsClient(ch))
			continue;

		if (bWasHidden != bIsHidden)
		{
			if (bIsHidden)
				SendLogout(*a, name);	// sends the window's line too
			else
				SendLogin(*a, name);	// sends the window's line too
		}
		else
			__CommunitySendFriend(*a, name);
	}
}

// ch's state / message / privacy changed (or ch logged in, bOldState = its state): save, tell the other
// cores and the friends here, and its own window.
void MessengerManager::__CommunityChanged(LPCHARACTER ch, BYTE bOldState, bool bSave)
{
	const std::string strName(ch->GetName());
	SCommunityInfo& own = m_CommunityInfo[strName];
	own.bLive = true;
	own.bLevel = static_cast<BYTE>(MINMAX(0, ch->GetLevel(), 255));
	own.bConqueror = ch->GetConquerorLevel();

	if (bSave && CommunityIsClient(ch))
	{
		char szStatus[COMMUNITY_STATUS_MAX_LEN * 2 + 1];
		DBManager::instance().EscapeString(szStatus, sizeof(szStatus), own.strStatus.c_str(), own.strStatus.size());
		DBManager::instance().Query("UPDATE player%s SET status_message = '%s', community_flags = %u WHERE id = %u",
			get_table_postfix(), szStatus, static_cast<unsigned int>(own.bChosen | own.bFlags), ch->GetPlayerID());
	}

	TPacketGGCommunity p;
	memset(&p, 0, sizeof(p));
	p.bHeader = HEADER_GG_COMMUNITY;
	strlcpy(p.szName, strName.c_str(), sizeof(p.szName));
	p.bState = own.bState;
	p.bFlags = own.bFlags;
	p.bLevel = own.bLevel;
	p.bConqueror = own.bConqueror;
	strlcpy(p.szStatus, own.strStatus.c_str(), sizeof(p.szStatus));
	P2P_MANAGER::instance().Send(&p, sizeof(p));

	__CommunityNotify(strName, bOldState);
	__CommunitySendMy(ch);
}

void MessengerManager::CommunityP2P(const char* c_pData)
{
	const TPacketGGCommunity* p = reinterpret_cast<const TPacketGGCommunity*>(c_pData);

	char szName[CHARACTER_NAME_MAX_LEN + 1];
	strlcpy(szName, p->szName, sizeof(szName));
	if (!*szName)
		return;

	char szStatus[COMMUNITY_STATUS_MAX_LEN + 1];
	strlcpy(szStatus, p->szStatus, sizeof(szStatus));

	const std::string strName(szName);
	SCommunityInfo& info = m_CommunityInfo[strName];
	const BYTE bOldState = info.bState;

	info.bLive = true;
	info.bState = p->bState <= COMMUNITY_STATE_DISCONNECT ? p->bState : COMMUNITY_STATE_CONNECT;
	info.bChosen = CommunityChosenState(info.bState == COMMUNITY_STATE_AUTO_HUNT || info.bState == COMMUNITY_STATE_SHOP_OPEN
		? COMMUNITY_STATE_CONNECT : info.bState);
	info.bFlags = p->bFlags & COMMUNITY_FLAG_PRIVACY_MASK;
	info.bLevel = p->bLevel;
	info.bConqueror = p->bConqueror;
	info.strStatus = CommunitySanitize(szStatus);

	__CommunityNotify(strName, bOldState);
}

// Called by RequestToAdd before "messenger_auth": the window shows the request with the inviter's level
// and location (his privacy kept).
void MessengerManager::CommunityRequestInfo(LPCHARACTER ch, LPCHARACTER target)
{
	if (!ch || !target || !__CommunityWants(target->GetName(), NULL))
		return;

	const SCommunityInfo& info = m_CommunityInfo[ch->GetName()];
	unsigned int uLevel = ch->GetLevel(), uConqueror = ch->GetConquerorLevel(), uChannel = g_bChannel;
	long lMapIndex = ch->GetMapIndex();
	if (info.bFlags & COMMUNITY_FLAG_HIDE_LEVEL)
		uLevel = uConqueror = 0;
	if (info.bFlags & COMMUNITY_FLAG_HIDE_LOCATION)
	{
		uChannel = 0;
		lMapIndex = 0;
	}
	target->ChatPacket(CHAT_TYPE_COMMAND, "community_request %s %u %u %u %ld", ch->GetName(), uLevel, uConqueror, uChannel,
		lMapIndex);
}

void MessengerManager::__CommunitySendGuild(LPCHARACTER ch)
{
	CGuild* pkGuild = ch->GetGuild();
	if (!pkGuild)
		return;

	std::vector<DWORD> vecPID;
	pkGuild->Mt2009ForEachMemberPID([&vecPID](DWORD dwPID) { vecPID.push_back(dwPID); });

	std::string strLine;
	int iCount = 0;
	for (size_t i = 0; i < vecPID.size(); ++i)
	{
		const DWORD dwPID = vecPID[i];
		unsigned int uChannel = 0;
		long lMapIndex = 0;
		std::string strName;

		if (LPCHARACTER pkMember = CHARACTER_MANAGER::instance().FindByPID(dwPID))
		{
			if (!pkMember->GetDesc())
				continue;
			strName = pkMember->GetName();
			uChannel = g_bChannel;
			lMapIndex = pkMember->GetMapIndex();
		}
		else if (CCI* pkCCI = P2P_MANAGER::instance().FindByPID(dwPID))
		{
			strName = pkCCI->szName;
			uChannel = pkCCI->bChannel;
			lMapIndex = pkCCI->lMapIndex;
		}
		else
			continue;

		std::map<keyT, SCommunityInfo>::const_iterator it = m_CommunityInfo.find(strName);
		if (it != m_CommunityInfo.end() && (it->second.bFlags & COMMUNITY_FLAG_HIDE_LOCATION || CommunityIsHidden(strName)))
			continue;

		char szItem[64];
		snprintf(szItem, sizeof(szItem), " %u:%u:%ld", dwPID, uChannel, lMapIndex);
		strLine += szItem;
		if (++iCount >= COMMUNITY_GUILD_PER_LINE)
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "community_guild%s", strLine.c_str());
			strLine.clear();
			iCount = 0;
		}
	}
	if (iCount > 0)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "community_guild%s", strLine.c_str());
}

void MessengerManager::__CommunityParty(LPCHARACTER ch, const char* c_szName)
{
	if (!c_szName || !*c_szName)
		return;

	if (ch->GetArena())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot use this in the duel arena."));
		return;
	}

	LPCHARACTER pkTarget = CHARACTER_MANAGER::instance().FindPC(c_szName);
	if (!pkTarget || pkTarget == ch || !pkTarget->GetDesc() || pkTarget->GetMapIndex() != ch->GetMapIndex()
		|| CommunityIsHidden(pkTarget->GetName()))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zaprosic do grupy mozna tylko gracza na tej samej mapie i tym samym kanale.");
		return;
	}

	ch->PartyInvite(pkTarget);
}

void MessengerManager::CommunityCommand(LPCHARACTER ch, const char* c_szArgument)
{
	if (!CommunityIsClient(ch))
		return;

	char szArg[64];
	const char* c_szRest = CommunitySkipSpaces(one_argument(c_szArgument, szArg, sizeof(szArg)));
	const std::string strName(ch->GetName());

	if (!strcmp(szArg, "hello"))
	{
		if (!CommunityThrottle(ch, COMMUNITY_PULSE_HELLO, 1000))
			return;
		m_CommunityHello.insert(strName);
		__CommunitySendMy(ch);
		__CommunitySendFriends(strName);
		return;
	}

	if (m_CommunityHello.find(strName) == m_CommunityHello.end())
		return;

	SCommunityInfo& own = m_CommunityInfo[strName];

	if (!strcmp(szArg, "state") || !strcmp(szArg, "auto"))
	{
		char szValue[16];
		one_argument(c_szRest, szValue, sizeof(szValue));
		const int iValue = atoi(szValue);
		const bool bState = szArg[0] == 's';

		if (bState && iValue != COMMUNITY_STATE_CONNECT && iValue != COMMUNITY_STATE_LEFT_SEAT && iValue != COMMUNITY_STATE_DISCONNECT)
			return;
		if (bState && !CommunityThrottle(ch, COMMUNITY_PULSE_STATE, 1000))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Poczekaj chwile przed kolejna zmiana stanu.");
			__CommunitySendMy(ch);
			return;
		}

		const BYTE bOld = own.bState;
		if (bState)
			own.bChosen = static_cast<BYTE>(iValue);
		else
			own.bAuto = iValue != 0;
		own.bState = own.bChosen != COMMUNITY_STATE_CONNECT ? own.bChosen
			: (own.bAuto ? static_cast<BYTE>(COMMUNITY_STATE_AUTO_HUNT) : static_cast<BYTE>(COMMUNITY_STATE_CONNECT));

		if (own.bState != bOld || bState)
			__CommunityChanged(ch, bOld, bState);
		return;
	}

	if (!strcmp(szArg, "status"))
	{
		if (!CommunityThrottle(ch, COMMUNITY_PULSE_STATUS, 1000))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Poczekaj chwile przed kolejna zmiana opisu.");
			return;
		}

		const std::string strStatus = CommunitySanitize(c_szRest);
		if (!strStatus.empty() && CBanwordManager::instance().CheckString(strStatus.c_str(), strStatus.size()))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Ten opis zawiera niedozwolone slowo.");
			return;
		}

		own.strStatus = strStatus;
		__CommunityChanged(ch, own.bState, true);
		return;
	}

	if (!strcmp(szArg, "privacy"))
	{
		char szValue[16];
		one_argument(c_szRest, szValue, sizeof(szValue));
		if (!CommunityThrottle(ch, COMMUNITY_PULSE_STATE, 500))
			return;
		own.bFlags = static_cast<BYTE>(atoi(szValue)) & COMMUNITY_FLAG_PRIVACY_MASK;
		__CommunityChanged(ch, own.bState, true);
		return;
	}

	if (!strcmp(szArg, "guild"))
	{
		if (CommunityThrottle(ch, COMMUNITY_PULSE_GUILD, 2000))
			__CommunitySendGuild(ch);
		return;
	}

	if (!strcmp(szArg, "party"))
	{
		char szTarget[CHARACTER_NAME_MAX_LEN + 1];
		one_argument(c_szRest, szTarget, sizeof(szTarget));
		if (!CommunityThrottle(ch, COMMUNITY_PULSE_PARTY, 2000))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Poczekaj chwile przed kolejnym zaproszeniem.");
			return;
		}
		__CommunityParty(ch, szTarget);
		return;
	}
}

#endif
