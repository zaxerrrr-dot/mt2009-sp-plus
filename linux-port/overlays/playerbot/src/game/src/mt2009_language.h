#ifndef __INC_MT2009_LANGUAGE_H__
#define __INC_MT2009_LANGUAGE_H__

// MT2009_PLUS_LANGUAGE_V1: the server's language core (server-patches/language/README.md).
//
// Every player reads the language his client names: the client sends "/lang <code>" after entering the game and at
// every change; it is kept in player.player.language (VARCHAR(4), default 'pl') and read back when the character enters
// a core. Polish is the source of every text; anything said to a reader of another language is looked up in that
// language's dictionary (share/locale/<locale>/lang/<code>/*.tsv - Polish source<TAB>translation, UTF-8, converted to
// the language's code page when loaded) and, missing there, in the English one; a text without either stays Polish.
//
// Callers (the bots, any engine code): GetPlayerLanguage(target) names the reader's language ("pl" for a bot, a
// character with no client, nobody); Mt2009TranslateFor(target, polish) / LC_TEXT_FOR(target, key) give the text in it.
// CHARACTER::ChatPacket already translates INFO / NOTICE / BIG_NOTICE / TALKING / DICE lines by itself.

class CHARACTER;
typedef CHARACTER* LPCHARACTER;

// The reader's language code ("pl", "en", "de", ...); never NULL.
const char* GetPlayerLanguage(LPCHARACTER ch);
// Sets it (a known code, 2-4 letters; aliases such as "cs" -> "cz" are mapped) and stores it in player.player.language.
void SetPlayerLanguage(LPCHARACTER ch, const char* code);

// A Polish text in the language `lang` (exact text, then a format template "%d ..."; then English); the text itself
// when there is none. The pointer is valid until the next call.
const char* Mt2009Translate(const char* lang, const char* polish);
// The same for a reader (Polish reader: the text itself).
const char* Mt2009TranslateFor(LPCHARACTER ch, const char* polish);
// locale_string for a reader: LC_TEXT(key) (the Polish) in the reader's language.
const char* Mt2009LcTextFor(LPCHARACTER ch, const char* key);
#define LC_TEXT_FOR(ch, str) Mt2009LcTextFor((ch), (str))

// Item / monster name in a language, NULL when the language has none for the vnum.
const char* Mt2009ItemNameIn(const char* lang, unsigned int vnum);
const char* Mt2009MobNameIn(const char* lang, unsigned int vnum);

// Engine hooks (edits.json).
void Mt2009LanguageOnEnterGame(LPCHARACTER ch);
const char* Mt2009LanguageChatFormat(LPCHARACTER ch, unsigned char type, const char* format);
int Mt2009LanguageChatResult(LPCHARACTER ch, unsigned char type, bool formatTranslated, char* buf, size_t size, int len);
void Mt2009LanguageCommand(LPCHARACTER ch, const char* argument);

#endif
