#ifndef __INC_MT2009_LANGUAGE_H__
#define __INC_MT2009_LANGUAGE_H__

// MT2009_PLUS_LANGUAGE_V1: the server's language core (server-patches/language/README.md).
//
// Every player reads the language his client names: the client sends "/lang <code>" after entering the game and at
// every change (only a language its user chose); it is kept in player.player.language (VARCHAR(4), NULL = never
// chosen: the server's default, M2_DEFAULT_LANGUAGE) and read back when the character enters a core. Polish is the
// source of every text; anything said to a reader of another language is looked up in that language's dictionary
// (share/locale/<locale>/lang/<code>/*.tsv - Polish source<TAB>translation, UTF-8, converted to the language's code
// page when loaded) and, missing there, in the English one; a text without either stays Polish.
//
// Callers (the bots, any engine code): GetPlayerLanguage(target) names the reader's language (his own choice, else the
// server's default - a bot's too; "pl" for nobody); Mt2009TranslateFor(target, polish) / LC_TEXT_FOR(target, key) give
// the text in it.
// CHARACTER::ChatPacket already translates INFO / NOTICE / BIG_NOTICE / TALKING / DICE lines by itself.

#include <cstddef>
#include <string>

class CHARACTER;
typedef CHARACTER* LPCHARACTER;

// MT2009_PLUS_LANGUAGE_DEFAULT_V1: the server's default language (M2_DEFAULT_LANGUAGE in .env, "pl" when not set) -
// the language of every player who never chose one (player.player.language NULL) and of the bots' public channels.
const char* Mt2009DefaultLanguage();
// The reader's language code ("pl", "en", "de", ...): the player's own choice, else the server's default ("pl" for
// nobody, a monster); never NULL.
const char* GetPlayerLanguage(LPCHARACTER ch);
// Whether the player chose a language himself ("/lang <code>"), rather than reading the server's default.
bool Mt2009PlayerChoseLanguage(LPCHARACTER ch);
// Sets it (a known code, 2-4 letters; aliases such as "cs" -> "cz" are mapped) and stores it in player.player.language;
// "default" (or NULL / "") forgets the choice - the player reads the server's default again (NULL in the table).
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

// MT2009_PLUS_LANGUAGE_QUESTINFO_V1: the code page of a language's client (1250 Polish / Czech / Hungarian / Romanian,
// 1252 English / German / ..., 1253 Greek, 1254 Turkish, 1256 Arabic).
int Mt2009LanguageCodePage(const char* lang);
// The Polish words of text[0, size) (up to its NUL) without their diacritics when the reader's client does not use
// cp1250 - words already in his language are left alone; whether anything changed.
bool Mt2009TransliterateFor(LPCHARACTER ch, char* text, size_t size);
// A quest window field (title 30+1, clock / counter name 16+1 bytes) for a reader: the Polish kept in the quest's
// state put into his language (a short form of *quest_info*.tsv first), else without its diacritics; cut at a
// word's end to fit; out is NUL-filled.
void Mt2009QuestInfoText(LPCHARACTER ch, const std::string& polish, char* out, size_t size);
// The titles / clock and counter names of every quest in the quest window again, in the reader's current language
// (after "/lang").
void Mt2009ResendQuestInfo(LPCHARACTER ch);
// DESC::Packet: a text packet (chat but the client's commands, whisper, quest script, quest confirm) for the reader
// with its Polish words without diacritics when his client's code page is not cp1250 - a copy, or data itself.
const void* Mt2009LanguagePacketOut(LPCHARACTER ch, const void* data, int size);

// Engine hooks (edits.json).
void Mt2009LanguageOnEnterGame(LPCHARACTER ch);
const char* Mt2009LanguageChatFormat(LPCHARACTER ch, unsigned char type, const char* format);
int Mt2009LanguageChatResult(LPCHARACTER ch, unsigned char type, bool formatTranslated, char* buf, size_t size, int len);
void Mt2009LanguageCommand(LPCHARACTER ch, const char* argument);

#endif
