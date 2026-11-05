// STUB – replaced by quest branch
//
// See mt2009_language.h. Every player reads Polish here; the bots' chat
// (playerbot_i18n.h) still answers a whisper written in another language in
// that language, by what the whisper says.
#include "stdafx.h"
#include "mt2009_language.h"

const char* GetPlayerLanguage(LPCHARACTER ch)
{
	(void)ch;
	return "pl";
}

void SetPlayerLanguage(LPCHARACTER ch, const char* code)
{
	(void)ch;
	(void)code;
}
