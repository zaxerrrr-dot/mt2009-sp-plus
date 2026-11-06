#!/usr/bin/env python3
"""gen_edits.py -- writes edits.json of server-patches/logtrim (README.md): MT2009_PLUS_BOT_LOG_TRIM_V1 (log.cpp:
the bots' GET_GOLD / SOCKET* / ATTR_FORCE rows, playerbot_logtrim.cpp) and MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1
(questmanager.cpp/.h, questevent.cpp: a quest's server_timer of a name and argument already registered reschedules
it instead of "already registered server timer" and a second, untracked timer chain). Anchors: the engine after every
other patch of the deploy list (logtrim goes last)."""
import json
import os

E = []


def edit(file, marker, old, new):
    E.append({"file": file, "marker": marker, "old": old, "new": new})


# ---------------------------------------------------------------- log.cpp
edit("log.cpp", "MT2009_PLUS_BOT_LOG_TRIM_V1 (decl)",
     '#include "utils.h"\n\nstatic char\t__escape_hint[1024];\n',
     '#include "utils.h"\n\n'
     '// MT2009_PLUS_BOT_LOG_TRIM_V1 (decl): the bots\' GET_GOLD as an hourly sum, no SOCKET*/ATTR_FORCE meta rows of\n'
     '// bots (playerbot_logtrim.cpp; event flag m2_bot_log_rows_on = 1 writes them as before)\n'
     'bool Mt2009BotLogTrimGold(LPCHARACTER ch, long long amount, const char* how);\n'
     'bool Mt2009BotLogTrimMeta(DWORD pid, const char* what);\n\n'
     'static char\t__escape_hint[1024];\n')

edit("log.cpp", "MT2009_PLUS_BOT_LOG_TRIM_V1 (socket)",
     'void LogManager::ItemSocketLog(DWORD who, DWORD itemID, DWORD itemVnum, BYTE socket, int value, const char* what)\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MID);\n',
     'void LogManager::ItemSocketLog(DWORD who, DWORD itemID, DWORD itemVnum, BYTE socket, int value, const char* what)\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MID);\n'
     '\t// MT2009_PLUS_BOT_LOG_TRIM_V1 (socket): a bot\'s SOCKET* row is only counted\n'
     '\tif (::Mt2009BotLogTrimMeta(who, what))\n\t\treturn;\n')

edit("log.cpp", "MT2009_PLUS_BOT_LOG_TRIM_V1 (attr)",
     'void LogManager::ItemAttrLog(DWORD who, DWORD itemID, DWORD itemVnum, WORD type, int value, const char* what) // MT2009_PLUS_WIDE_ATTR_V1\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MID);\n',
     'void LogManager::ItemAttrLog(DWORD who, DWORD itemID, DWORD itemVnum, WORD type, int value, const char* what) // MT2009_PLUS_WIDE_ATTR_V1\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MID);\n'
     '\t// MT2009_PLUS_BOT_LOG_TRIM_V1 (attr): a bot\'s ATTR_FORCE row is only counted\n'
     '\tif (::Mt2009BotLogTrimMeta(who, what))\n\t\treturn;\n')

edit("log.cpp", "MT2009_PLUS_BOT_LOG_TRIM_V1 (gold)",
     'void LogManager::CharLog(LPCHARACTER ch, long long dw, const char * c_pszText, const char * c_pszHint)\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MIN);\n',
     'void LogManager::CharLog(LPCHARACTER ch, long long dw, const char * c_pszText, const char * c_pszHint)\n'
     '{\n\tLOG_LEVEL_CHECK_N_RET(LOG_LEVEL_MIN);\n'
     '\t// MT2009_PLUS_BOT_LOG_TRIM_V1 (gold): a bot\'s GET_GOLD goes into the hourly sum row\n'
     '\tif (ch && ::Mt2009BotLogTrimGold(ch, dw, c_pszText))\n\t\treturn;\n')

# ---------------------------------------------------------------- quest server timers
edit("questmanager.h", "MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (decl)",
     '\t\t\tvoid\t\tClearServerTimerNotCancel(const string& name, DWORD arg);\n',
     '\t\t\t// MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (decl): self - the timer that fired; the entry goes only if it is still that one\n'
     '\t\t\tvoid\t\tClearServerTimerNotCancel(const string& name, DWORD arg, LPEVENT self = NULL);\n')

edit("questmanager.cpp", "MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (add)",
     '\t\tif (m_mapServerTimer.find(make_pair(name, arg)) != m_mapServerTimer.end())\n'
     '\t\t{\n'
     '\t\t\tsys_err("already registered server timer name:%s arg:%u", name.c_str(), arg);\n'
     '\t\t\treturn;\n'
     '\t\t}\n'
     '\t\tm_mapServerTimer.emplace(make_pair(name, arg), event);\n'
     '\t}\n'
     '\n'
     '\tvoid CQuestManager::ClearServerTimerNotCancel(const std::string& name, DWORD arg)\n'
     '\t{\n'
     '\t\tm_mapServerTimer.erase(make_pair(name, arg));\n'
     '\t}\n',
     '\t\t// MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (add): the same name and argument again (a quest\'s tick asking for its next\n'
     '\t\t// tick inside its own handler, or a stage/floor start while the previous tick still waits) reschedules it:\n'
     '\t\t// the waiting (or the running one-shot) event is cancelled and the new one is the registered one. The old\n'
     '\t\t// refusal left the new event running untracked - a second chain clear_server_timer / CancelServerTimers could\n'
     '\t\t// never stop, one more for every restart. Event flag m2_quest_timer_legacy = 1: the old refusal.\n'
     '\t\titertype(m_mapServerTimer) itOld = m_mapServerTimer.find(make_pair(name, arg));\n'
     '\t\tif (itOld != m_mapServerTimer.end())\n'
     '\t\t{\n'
     '\t\t\tif (GetEventFlag("m2_quest_timer_legacy") != 0)\n'
     '\t\t\t{\n'
     '\t\t\t\tsys_err("already registered server timer name:%s arg:%u", name.c_str(), arg);\n'
     '\t\t\t\treturn;\n'
     '\t\t\t}\n'
     '\t\t\tLPEVENT old = itOld->second;\n'
     '\t\t\tconst bool self = old && old->is_processing;\n'
     '\t\t\tif (old && old != event)\n'
     '\t\t\t\tevent_cancel(&old);\n'
     '\t\t\titOld->second = event;\n'
     '\t\t\tstatic DWORD s_dwSelf = 0, s_dwOther = 0, s_dwLogAt = 0;\n'
     '\t\t\tif (self)\n\t\t\t\t++s_dwSelf;\n\t\t\telse\n\t\t\t\t++s_dwOther;\n'
     '\t\t\tconst DWORD dwNow = get_dword_time();\n'
     '\t\t\tif (s_dwLogAt == 0 || dwNow - s_dwLogAt >= 600000)\n'
     '\t\t\t{\n'
     '\t\t\t\tsys_log(0, "QUEST_TIMER: rescheduled own_handler=%u while_waiting=%u last=%s:%u", s_dwSelf, s_dwOther, name.c_str(), arg);\n'
     '\t\t\t\ts_dwSelf = s_dwOther = 0;\n'
     '\t\t\t\ts_dwLogAt = dwNow;\n'
     '\t\t\t}\n'
     '\t\t\treturn;\n'
     '\t\t}\n'
     '\t\tm_mapServerTimer.emplace(make_pair(name, arg), event);\n'
     '\t}\n'
     '\n'
     '\tvoid CQuestManager::ClearServerTimerNotCancel(const std::string& name, DWORD arg, LPEVENT self)\n'
     '\t{\n'
     '\t\t// MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (clear): after a one-shot\'s handler - not the next tick it registered\n'
     '\t\titertype(m_mapServerTimer) it = m_mapServerTimer.find(make_pair(name, arg));\n'
     '\t\tif (it != m_mapServerTimer.end() && (!self || it->second == self))\n'
     '\t\t\tm_mapServerTimer.erase(it);\n'
     '\t}\n')

edit("questevent.cpp", "MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (fired)",
     '\t\tif (0 == info->time_cycle)\n'
     '\t\t{\n'
     '\t\t\tq.ClearServerTimerNotCancel(info->name, info->arg);\n',
     '\t\tif (0 == info->time_cycle)\n'
     '\t\t{\n'
     '\t\t\t// MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1 (fired): the entry only while it is this event, not its next tick\n'
     '\t\t\tq.ClearServerTimerNotCancel(info->name, info->arg, event);\n')

json.dump(E, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edits.json"), "w"), indent=1, ensure_ascii=True)
print("logtrim: %d edits" % len(E))
