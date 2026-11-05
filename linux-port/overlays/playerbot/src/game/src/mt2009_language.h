#ifndef __INC_METIN2_MT2009_LANGUAGE_H__
#define __INC_METIN2_MT2009_LANGUAGE_H__

// STUB – replaced by quest branch
//
// The player's language (the translation project, 5 November 2026): the code
// the client sends with "/lang <code>" after entering the game, kept in
// player.player.language. The quest branch owns the real file (the column,
// the command, pc.get_language(), LC_TEXT per language); this stub carries
// only the two signatures the bots' chat calls, so the bots' branch builds
// alone. A merge keeps the quest branch's version of both files.

class CHARACTER;
typedef CHARACTER* LPCHARACTER;

// The language code of a player ("pl", "en", "de", ...); "pl" by default and
// for anything unknown. Never NULL.
const char* GetPlayerLanguage(LPCHARACTER ch);
void SetPlayerLanguage(LPCHARACTER ch, const char* code);

#endif
