#ifndef __INC_METIN2_PLAYERBOT_I18N_H__
#define __INC_METIN2_PLAYERBOT_I18N_H__

// MT2009_PLUS_BOT_I18N_V1 - the bots speak a player's language (5 November).
//
// The bots are written in Polish, and stay so: every generator, every rule
// and every unit test works on the Polish line. What a person reads is turned
// into that person's language at the last moment, by catalogs:
//
//   <locale>/playerbot_i18n/chat_<lang>.tsv     "Polish template<TAB>translation"
//   <locale>/playerbot_i18n/input_<lang>.tsv    "their words<TAB>Polish words" (understanding)
//   <locale>/playerbot_i18n/names/item_names_<lang>.txt, mob_names_<lang>.txt   "vnum<TAB>name"
//   <locale>/playerbot_i18n/config.tsv          the switches (and /opt/m2spool/playerbot_i18n.tsv over it)
//
// A language is there when its chat file is: dropping chat_xx.tsv in adds
// "xx". The files are UTF-8; each is turned into its readers' code page at
// load ("#@codepage<TAB>1252" in the file, else the Windows page of the
// language).
//
// HOW A LINE IS TRANSLATED. A template is the Polish source text with its
// slots: $NAME (the conversation's placeholders) and {1}..{n} (printf's %s,
// %d in order). The finished Polish line is matched against the templates -
// case and Polish marks folded, a full stop at the end optional - and the
// slots it captured go into the translation, each itself translated when it
// is a known phrase ("w Dolinie Orkow" -> "in Orc Valley"), an item or a
// monster (by its vnum, from the names files) - or left as it is (a name, a
// number). A line no template covers whole is cut at its sentences (". ",
// "! ", "? ", ", ") and each piece is matched; a line some piece of which
// stays unknown falls back to Polish (FALLBACK 0) or is not said (1), and is
// written to /opt/m2spool/playerbot_i18n_miss_<lang>.tsv for the catalog.
//
// WHO READS WHAT
//   - a whisper, a companion's line, a notice: the reader's language
//     (GetPlayerLanguage, mt2009_language.h) - or the language the reader
//     has just written in, when DETECT is on and the whisper says so clearly;
//   - the shout, the '@' trade chat, the line over a bot's head, the guild's
//     chat: many readers, one line. The world speaks the server's default
//     language (M2_DEFAULT_LANGUAGE, Polish when not set -
//     MT2009_PLUS_LANGUAGE_DEFAULT_V1); with
//     PUBLIC_FOREIGN_PCT > 0 that share of the bots speaks one of the other
//     languages of the players online (PUBLIC_NEED_PLAYERS 1: only while such
//     players are online), weighted by how many play in each. An answer on
//     the shout to a person's question is in that person's language.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, early in playerbot_manager.cpp.

#include "mt2009_language.h"
#include "playerbot_i18n_codepages.h"
#include "locale_service.h"
#include <dirent.h>
#include <sys/stat.h>
#include <cctype>

namespace
{
	// The mark of a line already in its reader's language (the conversation's
	// own, playerbot_conv_style.h): the last step drops it and leaves the rest.
	const char PLAYERBOT_I18N_DONE = '\x01';

	const char* const PLAYERBOT_I18N_SPOOL_CONFIG = "/opt/m2spool/playerbot_i18n.tsv";
	const char* const PLAYERBOT_I18N_MISS_PREFIX = "/opt/m2spool/playerbot_i18n_miss_";
	const DWORD PLAYERBOT_I18N_RELOAD_MS = 60 * 1000;
	const DWORD PLAYERBOT_I18N_DETECT_TTL_MS = 30 * 60 * 1000;
	const size_t PLAYERBOT_I18N_MAX_MISSES = 4000;

	struct TPlayerBotI18nConfig
	{
		bool enabled;
		bool detect;
		int fallback;        // 0 Polish, 1 nothing
		int publicPct;       // share of the bots speaking another language on the public channels
		bool publicNeedPlayers;
		bool logMisses;
		TPlayerBotI18nConfig() : enabled(true), detect(true), fallback(0), publicPct(10), publicNeedPlayers(true),
			logMisses(true) {}
	};

	struct TPlayerBotI18nPiece
	{
		bool slot;
		std::string text;    // literal: folded; slot: its name ("$MAPIN", "{2}")
	};

	struct TPlayerBotI18nOutPiece
	{
		int slot;            // index into the template's slots, -1 literal
		std::string text;    // literal bytes in the reader's code page
	};

	struct TPlayerBotI18nEntry
	{
		std::vector<TPlayerBotI18nPiece> pieces;
		std::vector<std::string> slots;    // the slot names in order
		std::vector<TPlayerBotI18nOutPiece> out;
		size_t literalBytes;               // how much of the template is fixed text
	};

	struct TPlayerBotI18nLang
	{
		std::string code;
		const playerbot_i18n_cp::TCodePage* page;
		std::vector<TPlayerBotI18nEntry> entries;
		std::map<std::string, std::vector<size_t> > byHead;   // the first two folded bytes of the first literal
		std::vector<size_t> slotHead;                          // templates that open with a slot
		std::vector<std::pair<std::vector<std::string>, std::string> > input; // their words -> Polish
		std::set<std::string> detectWords;
		std::map<DWORD, std::string> itemNames;
		std::map<DWORD, std::string> mobNames;
		std::set<std::string> missed;
		TPlayerBotI18nLang() : page(NULL) {}
	};

	TPlayerBotI18nConfig s_PlayerBotI18nConfig;
	std::map<std::string, TPlayerBotI18nLang> s_mapPlayerBotI18n;
	bool s_bPlayerBotI18nLoaded = false;
	DWORD s_dwPlayerBotI18nCheck = 0;
	std::string s_strPlayerBotI18nStamp;
	// The Polish names of the items and monsters the names files know, folded,
	// to their vnum - the reverse of the protos (built at the first need).
	std::map<std::string, DWORD> s_mapPlayerBotI18nItemByName;
	std::map<std::string, DWORD> s_mapPlayerBotI18nMobByName;
	bool s_bPlayerBotI18nNamesIndexed = false;

	// ------------------------------------------------------------ code pages

	const playerbot_i18n_cp::TCodePage* FindPlayerBotI18nPage(int id)
	{
		for (int i = 0; i < playerbot_i18n_cp::kPageCount; ++i)
			if (playerbot_i18n_cp::kPages[i].id == id)
				return &playerbot_i18n_cp::kPages[i];
		return NULL;
	}

	const playerbot_i18n_cp::TCodePage* PlayerBotI18nPolishPage()
	{
		static const playerbot_i18n_cp::TCodePage* page = FindPlayerBotI18nPage(1250);
		return page;
	}

	// The Windows page a client of the language reads, when its file does not say.
	int PlayerBotI18nDefaultPage(const std::string& code)
	{
		if (code == "pl" || code == "cz" || code == "cs" || code == "hu" || code == "ro" || code == "sk")
			return 1250;
		if (code == "tr")
			return 1254;
		if (code == "gr" || code == "el")
			return 1253;
		if (code == "ru" || code == "uk" || code == "ua" || code == "bg")
			return 1251;
		if (code == "ae" || code == "ar")
			return 1256;
		return 1252;
	}

	inline unsigned char FoldPlayerBotI18nByte(unsigned char c, const playerbot_i18n_cp::TCodePage* page)
	{
		if (c < 0x80)
			return (c >= 'A' && c <= 'Z') ? (unsigned char)(c - 'A' + 'a') : c;
		return page ? page->fold[c - 0x80] : (unsigned char)' ';
	}

	std::string FoldPlayerBotI18n(const std::string& in, const playerbot_i18n_cp::TCodePage* page)
	{
		std::string out(in);
		for (size_t i = 0; i < out.size(); ++i)
		{
			const unsigned char c = (unsigned char)out[i];
			// A non-letter keeps itself: the punctuation matters to a template.
			const unsigned char f = FoldPlayerBotI18nByte(c, page);
			out[i] = (char)(c >= 0x80 && f == ' ' ? c : f);
		}
		return out;
	}

	// UTF-8 to the bytes of a code page; what the page has not got becomes '?'.
	std::string PlayerBotI18nFromUtf8(const std::string& in, const playerbot_i18n_cp::TCodePage* page)
	{
		std::string out;
		out.reserve(in.size());
		for (size_t i = 0; i < in.size(); )
		{
			const unsigned char c = (unsigned char)in[i];
			unsigned int cp = c;
			size_t len = 1;
			if (c >= 0xF0 && i + 3 < in.size())
			{
				cp = ((c & 7u) << 18) | ((in[i + 1] & 0x3Fu) << 12) | ((in[i + 2] & 0x3Fu) << 6) | (in[i + 3] & 0x3Fu);
				len = 4;
			}
			else if (c >= 0xE0 && i + 2 < in.size())
			{
				cp = ((c & 0xFu) << 12) | ((in[i + 1] & 0x3Fu) << 6) | (in[i + 2] & 0x3Fu);
				len = 3;
			}
			else if (c >= 0xC0 && i + 1 < in.size())
			{
				cp = ((c & 0x1Fu) << 6) | (in[i + 1] & 0x3Fu);
				len = 2;
			}
			i += len;
			if (cp < 0x80)
			{
				out += (char)cp;
				continue;
			}
			// Romanian s and t with a comma below are written with the cedilla
			// in the Windows page (the letters the client's font has).
			if (cp == 0x0219) cp = 0x015F;
			else if (cp == 0x0218) cp = 0x015E;
			else if (cp == 0x021B) cp = 0x0163;
			else if (cp == 0x021A) cp = 0x0162;
			char b = '?';
			if (page)
				for (int k = 0; k < 128; ++k)
					if (page->uni[k] == cp)
					{
						b = (char)(0x80 + k);
						break;
					}
			// A typographic mark the page lacks has a plain one.
			if (b == '?')
			{
				if (cp == 0x2019 || cp == 0x2018) b = '\'';
				else if (cp == 0x201C || cp == 0x201D || cp == 0x201E) b = '"';
				else if (cp == 0x2013 || cp == 0x2014) b = '-';
				else if (cp == 0x2026) b = '.';
				else if (cp == 0x00A0) b = ' ';
			}
			out += b;
		}
		return out;
	}

	std::string PlayerBotI18nToUtf8(const std::string& in, const playerbot_i18n_cp::TCodePage* page)
	{
		std::string out;
		for (size_t i = 0; i < in.size(); ++i)
		{
			const unsigned char c = (unsigned char)in[i];
			unsigned int cp = c;
			if (c >= 0x80)
				cp = page && page->uni[c - 0x80] ? page->uni[c - 0x80] : (unsigned int)'?';
			if (cp < 0x80)
				out += (char)cp;
			else if (cp < 0x800)
			{
				out += (char)(0xC0 | (cp >> 6));
				out += (char)(0x80 | (cp & 0x3F));
			}
			else
			{
				out += (char)(0xE0 | (cp >> 12));
				out += (char)(0x80 | ((cp >> 6) & 0x3F));
				out += (char)(0x80 | (cp & 0x3F));
			}
		}
		return out;
	}

	// ------------------------------------------------------------ templates

	inline bool IsPlayerBotI18nSlotChar(char c)
	{
		return (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_';
	}

	// "$NAME" or "{n}" at `i`: its length, 0 when there is none.
	size_t PlayerBotI18nSlotAt(const std::string& s, size_t i)
	{
		if (s[i] == '$' && i + 1 < s.size() && s[i + 1] >= 'A' && s[i + 1] <= 'Z')
		{
			size_t j = i + 1;
			while (j < s.size() && IsPlayerBotI18nSlotChar(s[j]))
				++j;
			return j - i;
		}
		if (s[i] == '{' && i + 2 < s.size() && s[i + 1] >= '1' && s[i + 1] <= '9')
		{
			size_t j = i + 1;
			while (j < s.size() && s[j] >= '0' && s[j] <= '9')
				++j;
			if (j < s.size() && s[j] == '}')
				return j + 1 - i;
		}
		return 0;
	}

	// A template's trailing full stop is optional: it is cut off the template
	// and off the line before they are compared.
	void TrimPlayerBotI18nEnd(std::string& s)
	{
		while (!s.empty() && s[s.size() - 1] == ' ')
			s.erase(s.size() - 1);
		if (s.size() >= 2 && s[s.size() - 1] == '.' && s[s.size() - 2] != '.')
			s.erase(s.size() - 1);
	}

	bool ParsePlayerBotI18nEntry(const std::string& plCp1250, const std::string& outBytes, TPlayerBotI18nEntry& e)
	{
		std::string pl = plCp1250;
		TrimPlayerBotI18nEnd(pl);
		std::string lit;
		e.literalBytes = 0;
		for (size_t i = 0; i < pl.size(); )
		{
			const size_t n = PlayerBotI18nSlotAt(pl, i);
			if (n == 0)
			{
				lit += pl[i++];
				continue;
			}
			if (!lit.empty())
			{
				TPlayerBotI18nPiece p;
				p.slot = false;
				p.text = FoldPlayerBotI18n(lit, PlayerBotI18nPolishPage());
				e.literalBytes += lit.size();
				e.pieces.push_back(p);
				lit.clear();
			}
			TPlayerBotI18nPiece p;
			p.slot = true;
			p.text = pl.substr(i, n);
			e.pieces.push_back(p);
			e.slots.push_back(p.text);
			i += n;
		}
		if (!lit.empty())
		{
			TPlayerBotI18nPiece p;
			p.slot = false;
			p.text = FoldPlayerBotI18n(lit, PlayerBotI18nPolishPage());
			e.literalBytes += lit.size();
			e.pieces.push_back(p);
		}
		// A template of slots and marks alone ("{1}, {2}") would match anything.
		int letters = 0;
		for (size_t i = 0; i < e.pieces.size(); ++i)
			if (!e.pieces[i].slot)
				for (size_t k = 0; k < e.pieces[i].text.size(); ++k)
					if (isalpha((unsigned char)e.pieces[i].text[k]))
						++letters;
		if (letters < 2)
			return false;
		std::string olit;
		for (size_t i = 0; i < outBytes.size(); )
		{
			const size_t n = PlayerBotI18nSlotAt(outBytes, i);
			if (n == 0)
			{
				olit += outBytes[i++];
				continue;
			}
			const std::string name = outBytes.substr(i, n);
			int slot = -1;
			for (size_t k = 0; k < e.slots.size(); ++k)
				if (e.slots[k] == name)
				{
					slot = (int)k;
					break;
				}
			if (slot < 0)
			{
				// "$X" the Polish has not got: a literal after all (a price "$5"?), or a typo.
				olit += name;
				i += n;
				continue;
			}
			if (!olit.empty())
			{
				TPlayerBotI18nOutPiece o;
				o.slot = -1;
				o.text = olit;
				e.out.push_back(o);
				olit.clear();
			}
			TPlayerBotI18nOutPiece o;
			o.slot = slot;
			e.out.push_back(o);
			i += n;
		}
		if (!olit.empty())
		{
			TPlayerBotI18nOutPiece o;
			o.slot = -1;
			o.text = olit;
			e.out.push_back(o);
		}
		return true;
	}

	// ------------------------------------------------------------ loading

	void ReadPlayerBotI18nConfigFile(const std::string& path)
	{
		FILE* fp = fopen(path.c_str(), "r");
		if (!fp)
			return;
		char line[512];
		while (fgets(line, sizeof(line), fp))
		{
			char key[64];
			long value = 0;
			if (line[0] == '#' || sscanf(line, "%63s %ld", key, &value) != 2)
				continue;
			const std::string k(key);
			if (k == "ENABLED") s_PlayerBotI18nConfig.enabled = value != 0;
			else if (k == "DETECT") s_PlayerBotI18nConfig.detect = value != 0;
			else if (k == "FALLBACK") s_PlayerBotI18nConfig.fallback = value != 0 ? 1 : 0;
			else if (k == "PUBLIC_FOREIGN_PCT") s_PlayerBotI18nConfig.publicPct = (int)MINMAX(0L, value, 100L);
			else if (k == "PUBLIC_NEED_PLAYERS") s_PlayerBotI18nConfig.publicNeedPlayers = value != 0;
			else if (k == "LOG_MISSES") s_PlayerBotI18nConfig.logMisses = value != 0;
		}
		fclose(fp);
	}

	// Splits a UTF-8 line at its first tab; false for a comment or no tab.
	bool SplitPlayerBotI18nLine(std::string line, std::string& left, std::string& right)
	{
		while (!line.empty() && (line[line.size() - 1] == '\n' || line[line.size() - 1] == '\r'))
			line.erase(line.size() - 1);
		if (line.empty() || line[0] == '#')
			return false;
		const size_t tab = line.find('\t');
		if (tab == std::string::npos || tab == 0)
			return false;
		left = line.substr(0, tab);
		right = line.substr(tab + 1);
		const size_t tab2 = right.find('\t');
		if (tab2 != std::string::npos)
			right.erase(tab2);
		return !right.empty() && right != "-";
	}

	bool ReadPlayerBotI18nLines(const std::string& path, std::vector<std::string>& lines, int* codepage)
	{
		FILE* fp = fopen(path.c_str(), "r");
		if (!fp)
			return false;
		char buf[4096];
		while (fgets(buf, sizeof(buf), fp))
		{
			std::string line(buf);
			if (codepage && line.compare(0, 11, "#@codepage\t") == 0)
				*codepage = atoi(line.c_str() + 11);
			lines.push_back(line);
		}
		fclose(fp);
		return true;
	}

	void SplitPlayerBotI18nWords(const std::string& folded, std::vector<std::string>& words)
	{
		words.clear();
		std::string w;
		for (size_t i = 0; i <= folded.size(); ++i)
		{
			const unsigned char c = i < folded.size() ? (unsigned char)folded[i] : ' ';
			const bool word = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c >= 0x80 || c == '\'';
			if (word)
				w += (char)c;
			else if (!w.empty())
			{
				words.push_back(w);
				w.clear();
			}
		}
	}

	void LoadPlayerBotI18nNames(const std::string& path, const playerbot_i18n_cp::TCodePage* page,
			std::map<DWORD, std::string>& out)
	{
		std::vector<std::string> lines;
		if (!ReadPlayerBotI18nLines(path, lines, NULL))
			return;
		for (size_t i = 0; i < lines.size(); ++i)
		{
			std::string left, right;
			if (!SplitPlayerBotI18nLine(lines[i], left, right))
				continue;
			const DWORD vnum = (DWORD)strtoul(left.c_str(), NULL, 10);
			if (vnum)
				out[vnum] = PlayerBotI18nFromUtf8(right, page);
		}
	}

	void LoadPlayerBotI18nLanguage(const std::string& dir, const std::string& code)
	{
		TPlayerBotI18nLang lang;
		lang.code = code;
		int codepage = PlayerBotI18nDefaultPage(code);
		std::vector<std::string> lines;
		if (!ReadPlayerBotI18nLines(dir + "/chat_" + code + ".tsv", lines, &codepage))
			return;
		lang.page = FindPlayerBotI18nPage(codepage);
		if (!lang.page)
		{
			sys_err("PLAYERBOT_I18N: %s: code page %d unknown, using 1252", code.c_str(), codepage);
			lang.page = FindPlayerBotI18nPage(1252);
		}
		std::set<std::string> seen;
		for (size_t i = 0; i < lines.size(); ++i)
		{
			std::string pl, tr;
			if (!SplitPlayerBotI18nLine(lines[i], pl, tr))
				continue;
			const std::string plBytes = PlayerBotI18nFromUtf8(pl, PlayerBotI18nPolishPage());
			if (!seen.insert(plBytes).second)
				continue;
			TPlayerBotI18nEntry e;
			if (!ParsePlayerBotI18nEntry(plBytes, PlayerBotI18nFromUtf8(tr, lang.page), e))
				continue;
			const size_t index = lang.entries.size();
			lang.entries.push_back(e);
			const TPlayerBotI18nPiece& first = e.pieces[0];
			if (first.slot)
				lang.slotHead.push_back(index);
			else
				lang.byHead[first.text.substr(0, std::min<size_t>(2, first.text.size()))].push_back(index);
		}
		// Understanding: "their words<TAB>Polish words"; "#@detect<TAB>w1 w2 ..."
		// names the words that say a line is in this language.
		std::vector<std::string> in;
		if (ReadPlayerBotI18nLines(dir + "/input_" + code + ".tsv", in, NULL))
		{
			for (size_t i = 0; i < in.size(); ++i)
			{
				if (in[i].compare(0, 9, "#@detect\t") == 0)
				{
					std::vector<std::string> words;
					SplitPlayerBotI18nWords(FoldPlayerBotI18n(PlayerBotI18nFromUtf8(in[i].substr(9), lang.page), lang.page),
							words);
					lang.detectWords.insert(words.begin(), words.end());
					continue;
				}
				std::string theirs, pl;
				if (!SplitPlayerBotI18nLine(in[i], theirs, pl))
					continue;
				std::vector<std::string> words;
				SplitPlayerBotI18nWords(FoldPlayerBotI18n(PlayerBotI18nFromUtf8(theirs, lang.page), lang.page), words);
				if (words.empty())
					continue;
				lang.input.push_back(std::make_pair(words, PlayerBotI18nFromUtf8(pl, PlayerBotI18nPolishPage())));
			}
			// Longest phrases first: "where are you" before "where".
			struct ByLength
			{
				bool operator()(const std::pair<std::vector<std::string>, std::string>& a,
						const std::pair<std::vector<std::string>, std::string>& b) const
				{
					return a.first.size() > b.first.size();
				}
			};
			std::stable_sort(lang.input.begin(), lang.input.end(), ByLength());
		}
		LoadPlayerBotI18nNames(dir + "/names/item_names_" + code + ".txt", lang.page, lang.itemNames);
		LoadPlayerBotI18nNames(dir + "/names/mob_names_" + code + ".txt", lang.page, lang.mobNames);
		sys_log(0, "PLAYERBOT_I18N: %s loaded templates=%u input=%u detect=%u items=%u mobs=%u codepage=%d",
				code.c_str(), (unsigned int)lang.entries.size(), (unsigned int)lang.input.size(),
				(unsigned int)lang.detectWords.size(), (unsigned int)lang.itemNames.size(),
				(unsigned int)lang.mobNames.size(), lang.page->id);
		s_mapPlayerBotI18n[code].entries.swap(lang.entries);
		TPlayerBotI18nLang& slot = s_mapPlayerBotI18n[code];
		slot.code = code;
		slot.page = lang.page;
		slot.byHead.swap(lang.byHead);
		slot.slotHead.swap(lang.slotHead);
		slot.input.swap(lang.input);
		slot.detectWords.swap(lang.detectWords);
		slot.itemNames.swap(lang.itemNames);
		slot.mobNames.swap(lang.mobNames);
	}

	// What the files are now: their names, sizes and times, to reload on a change.
	std::string PlayerBotI18nStamp(const std::string& dir, std::vector<std::string>* codes)
	{
		std::string stamp;
		struct stat st;
		if (stat(PLAYERBOT_I18N_SPOOL_CONFIG, &st) == 0)
			stamp += "spool:" + std::to_string((long long)st.st_mtime) + ";";
		DIR* d = opendir(dir.c_str());
		if (!d)
			return stamp;
		std::vector<std::string> names;
		while (struct dirent* e = readdir(d))
			names.push_back(e->d_name);
		closedir(d);
		std::sort(names.begin(), names.end());
		for (size_t i = 0; i < names.size(); ++i)
		{
			const std::string& n = names[i];
			if (n.size() < 4 || n.compare(n.size() - 4, 4, ".tsv") != 0)
				continue;
			if (stat((dir + "/" + n).c_str(), &st) == 0)
				stamp += n + ":" + std::to_string((long long)st.st_mtime) + ":" + std::to_string((long long)st.st_size) + ";";
			if (codes && n.compare(0, 5, "chat_") == 0)
			{
				const std::string code = n.substr(5, n.size() - 9);
				if (!code.empty() && code != "pl" && code.size() <= 4)
					codes->push_back(code);
			}
		}
		return stamp;
	}

	void RefreshPlayerBotI18n()
	{
		const DWORD now = get_dword_time();
		if (s_bPlayerBotI18nLoaded && now - s_dwPlayerBotI18nCheck < PLAYERBOT_I18N_RELOAD_MS)
			return;
		s_dwPlayerBotI18nCheck = now;
		const std::string dir = LocaleService_GetBasePath() + "/playerbot_i18n";
		std::vector<std::string> codes;
		const std::string stamp = PlayerBotI18nStamp(dir, &codes);
		if (s_bPlayerBotI18nLoaded && stamp == s_strPlayerBotI18nStamp)
			return;
		s_bPlayerBotI18nLoaded = true;
		s_strPlayerBotI18nStamp = stamp;
		s_PlayerBotI18nConfig = TPlayerBotI18nConfig();
		ReadPlayerBotI18nConfigFile(dir + "/config.tsv");
		ReadPlayerBotI18nConfigFile(PLAYERBOT_I18N_SPOOL_CONFIG);
		// A language whose file is gone goes with it.
		std::map<std::string, TPlayerBotI18nLang> old;
		old.swap(s_mapPlayerBotI18n);
		for (size_t i = 0; i < codes.size(); ++i)
		{
			LoadPlayerBotI18nLanguage(dir, codes[i]);
			std::map<std::string, TPlayerBotI18nLang>::iterator it = s_mapPlayerBotI18n.find(codes[i]);
			std::map<std::string, TPlayerBotI18nLang>::iterator was = old.find(codes[i]);
			if (it != s_mapPlayerBotI18n.end() && was != old.end())
				it->second.missed.swap(was->second.missed);
		}
		s_bPlayerBotI18nNamesIndexed = false;
		sys_log(0, "PLAYERBOT_I18N: %u languages, enabled=%d detect=%d fallback=%d public=%d%% need_players=%d",
				(unsigned int)s_mapPlayerBotI18n.size(), s_PlayerBotI18nConfig.enabled ? 1 : 0,
				s_PlayerBotI18nConfig.detect ? 1 : 0, s_PlayerBotI18nConfig.fallback,
				s_PlayerBotI18nConfig.publicPct, s_PlayerBotI18nConfig.publicNeedPlayers ? 1 : 0);
	}

	TPlayerBotI18nLang* FindPlayerBotI18nLang(const std::string& code)
	{
		RefreshPlayerBotI18n();
		if (!s_PlayerBotI18nConfig.enabled || code.empty() || code == "pl")
			return NULL;
		std::map<std::string, TPlayerBotI18nLang>::iterator it = s_mapPlayerBotI18n.find(code);
		return it == s_mapPlayerBotI18n.end() ? NULL : &it->second;
	}

	// The Polish names of the items and monsters some names file knows.
	void IndexPlayerBotI18nNames()
	{
		if (s_bPlayerBotI18nNamesIndexed)
			return;
		s_bPlayerBotI18nNamesIndexed = true;
		s_mapPlayerBotI18nItemByName.clear();
		s_mapPlayerBotI18nMobByName.clear();
		std::set<DWORD> items, mobs;
		for (std::map<std::string, TPlayerBotI18nLang>::const_iterator it = s_mapPlayerBotI18n.begin();
				it != s_mapPlayerBotI18n.end(); ++it)
		{
			for (std::map<DWORD, std::string>::const_iterator n = it->second.itemNames.begin(); n != it->second.itemNames.end(); ++n)
				items.insert(n->first);
			for (std::map<DWORD, std::string>::const_iterator n = it->second.mobNames.begin(); n != it->second.mobNames.end(); ++n)
				mobs.insert(n->first);
		}
		for (std::set<DWORD>::const_iterator v = items.begin(); v != items.end(); ++v)
			if (const TItemTable* proto = ITEM_MANAGER::instance().GetTable(*v))
				s_mapPlayerBotI18nItemByName.insert(std::make_pair(
						FoldPlayerBotI18n(proto->szLocaleName, PlayerBotI18nPolishPage()), *v));
		for (std::set<DWORD>::const_iterator v = mobs.begin(); v != mobs.end(); ++v)
			if (const CMob* mob = CMobManager::instance().Get(*v))
				s_mapPlayerBotI18nMobByName.insert(std::make_pair(
						FoldPlayerBotI18n(mob->m_table.szLocaleName, PlayerBotI18nPolishPage()), *v));
	}

	// ------------------------------------------------------------ matching

	struct TPlayerBotI18nMatch
	{
		std::vector<std::pair<size_t, size_t> > caps;   // offset, length in the line
	};

	bool IsPlayerBotI18nSentenceEnd(const std::string& s, size_t i);

	// Whether raw[from, from + len) holds a cut of the line (". ", ", ", ":D ").
	bool PlayerBotI18nHasCut(const std::string& raw, size_t from, size_t len)
	{
		for (size_t i = from; i + 1 < from + len; ++i)
			if (IsPlayerBotI18nSentenceEnd(raw, i))
				return true;
		return false;
	}

	// Pieces from `pi` against folded[ti, end). Slots take one byte at least.
	bool MatchPlayerBotI18nPieces(const TPlayerBotI18nEntry& e, size_t pi, const std::string& folded, size_t ti,
			size_t end, TPlayerBotI18nMatch& m, int& budget)
	{
		if (--budget < 0)
			return false;
		if (pi == e.pieces.size())
			return ti == end;
		const TPlayerBotI18nPiece& p = e.pieces[pi];
		if (!p.slot)
		{
			if (end - ti < p.text.size() || folded.compare(ti, p.text.size(), p.text) != 0)
				return false;
			return MatchPlayerBotI18nPieces(e, pi + 1, folded, ti + p.text.size(), end, m, budget);
		}
		if (ti >= end)
			return false;
		if (pi + 1 == e.pieces.size())
		{
			m.caps.push_back(std::make_pair(ti, end - ti));
			return true;
		}
		const TPlayerBotI18nPiece& next = e.pieces[pi + 1];
		if (next.slot)
		{
			// Two slots side by side: the first takes one byte, then more.
			for (size_t len = 1; ti + len < end; ++len)
			{
				m.caps.push_back(std::make_pair(ti, len));
				if (MatchPlayerBotI18nPieces(e, pi + 1, folded, ti + len, end, m, budget))
					return true;
				m.caps.pop_back();
				if (budget < 0)
					return false;
			}
			return false;
		}
		for (size_t at = folded.find(next.text, ti + 1); at != std::string::npos && at < end;
				at = folded.find(next.text, at + 1))
		{
			if (at + next.text.size() > end)
				break;
			m.caps.push_back(std::make_pair(ti, at - ti));
			if (MatchPlayerBotI18nPieces(e, pi + 1, folded, at, end, m, budget))
				return true;
			m.caps.pop_back();
			if (budget < 0)
				return false;
		}
		return false;
	}

	std::string TranslatePlayerBotI18nValue(TPlayerBotI18nLang& lang, const std::string& value, int depth, bool* ok = NULL);

	// The translation of one template's match, or false when a slot holds a
	// cut of the line it cannot translate: "Stoje ze straganem $MAPIN" must
	// not take "w Joan. Wpadnij :D" for its place and leave half of it Polish.
	bool BuildPlayerBotI18nOutput(TPlayerBotI18nLang& lang, const TPlayerBotI18nEntry& e, const TPlayerBotI18nMatch& m,
			const std::string& raw, int depth, std::string& out)
	{
		std::vector<std::string> values(m.caps.size());
		for (size_t k = 0; k < m.caps.size(); ++k)
		{
			const std::pair<size_t, size_t>& c = m.caps[k];
			bool ok = true;
			values[k] = TranslatePlayerBotI18nValue(lang, raw.substr(c.first, c.second), depth + 1, &ok);
			if (!ok && PlayerBotI18nHasCut(raw, c.first, c.second))
				return false;
		}
		out.clear();
		for (size_t i = 0; i < e.out.size(); ++i)
		{
			const TPlayerBotI18nOutPiece& o = e.out[i];
			if (o.slot < 0)
				out += o.text;
			else if (o.slot < (int)values.size())
				out += values[o.slot];
		}
		return true;
	}

	// Every template that could cover folded[start, end) whole, the most fixed
	// text first. The translation in `out`.
	bool TranslatePlayerBotI18nWhole(TPlayerBotI18nLang& lang, const std::string& raw, const std::string& folded,
			size_t start, size_t end, std::string& out, int depth)
	{
		if (end <= start || depth > 4)
			return false;
		const TPlayerBotI18nEntry* best = NULL;
		std::string bestOut;
		const std::string head = folded.substr(start, std::min<size_t>(2, end - start));
		for (int pass = 0; pass < 3; ++pass)
		{
			const std::vector<size_t>* list = NULL;
			std::map<std::string, std::vector<size_t> >::const_iterator it;
			if (pass == 0)
			{
				it = lang.byHead.find(head);
				list = it == lang.byHead.end() ? NULL : &it->second;
			}
			else if (pass == 1)
			{
				// A one-byte literal ("?", "A ...") heads its own list.
				it = lang.byHead.find(head.substr(0, 1));
				list = head.size() > 1 && it != lang.byHead.end() ? &it->second : NULL;
			}
			else
				list = &lang.slotHead;
			if (!list)
				continue;
			for (size_t k = 0; k < list->size(); ++k)
			{
				const TPlayerBotI18nEntry& e = lang.entries[(*list)[k]];
				if (best && e.literalBytes <= best->literalBytes)
					continue;
				if (e.literalBytes > end - start)
					continue;
				TPlayerBotI18nMatch m;
				int budget = 2000;
				std::string o;
				if (MatchPlayerBotI18nPieces(e, 0, folded, start, end, m, budget) &&
						BuildPlayerBotI18nOutput(lang, e, m, raw, depth, o))
				{
					best = &e;
					bestOut.swap(o);
				}
			}
		}
		if (!best)
			return false;
		out.swap(bestOut);
		return true;
	}

	// An item or a monster by its Polish name, "+7" and " x5" kept.
	bool TranslatePlayerBotI18nName(TPlayerBotI18nLang& lang, const std::string& value, std::string& out)
	{
		if (lang.itemNames.empty() && lang.mobNames.empty())
			return false;
		IndexPlayerBotI18nNames();
		std::string name = value, suffix, prefix;
		const size_t x = name.rfind(" x");
		if (x != std::string::npos && x + 2 < name.size() && isdigit((unsigned char)name[x + 2]))
		{
			suffix = name.substr(x);
			name.erase(x);
		}
		const std::string folded = FoldPlayerBotI18n(name, PlayerBotI18nPolishPage());
		std::map<std::string, DWORD>::const_iterator it = s_mapPlayerBotI18nItemByName.find(folded);
		if (it != s_mapPlayerBotI18nItemByName.end())
		{
			std::map<DWORD, std::string>::const_iterator n = lang.itemNames.find(it->second);
			if (n != lang.itemNames.end())
			{
				out = n->second + suffix;
				return true;
			}
		}
		// "Miecz+7" whose +7 the table names on its own row only.
		const size_t plus = folded.rfind('+');
		if (plus != std::string::npos && plus > 0)
		{
			it = s_mapPlayerBotI18nItemByName.find(folded.substr(0, plus));
			if (it == s_mapPlayerBotI18nItemByName.end())
				it = s_mapPlayerBotI18nItemByName.find(folded.substr(0, plus) + "+0");
			if (it != s_mapPlayerBotI18nItemByName.end())
			{
				std::map<DWORD, std::string>::const_iterator n = lang.itemNames.find(it->second);
				if (n != lang.itemNames.end())
				{
					std::string base = n->second;
					const size_t p0 = base.rfind("+0");
					if (p0 != std::string::npos && p0 + 2 == base.size())
						base.erase(p0);
					out = base + name.substr(plus) + suffix;
					return true;
				}
			}
		}
		it = s_mapPlayerBotI18nMobByName.find(folded);
		if (it != s_mapPlayerBotI18nMobByName.end())
		{
			std::map<DWORD, std::string>::const_iterator n = lang.mobNames.find(it->second);
			if (n != lang.mobNames.end())
			{
				out = n->second + suffix;
				return true;
			}
		}
		return false;
	}

	// An item link's name ("|Hitem:c47c:...|h[Name]|h") in the reader's language.
	std::string TranslatePlayerBotI18nLinks(TPlayerBotI18nLang& lang, const std::string& text)
	{
		if (lang.itemNames.empty() || text.find("|Hitem:") == std::string::npos)
			return text;
		std::string out;
		size_t pos = 0;
		for (;;)
		{
			const size_t h = text.find("|Hitem:", pos);
			if (h == std::string::npos)
				break;
			const size_t open = text.find("|h[", h);
			const size_t close = open == std::string::npos ? std::string::npos : text.find("]|h", open);
			if (close == std::string::npos)
				break;
			const DWORD vnum = (DWORD)strtoul(text.c_str() + h + 7, NULL, 16);
			std::map<DWORD, std::string>::const_iterator n = lang.itemNames.find(vnum);
			out += text.substr(pos, open + 3 - pos);
			out += n != lang.itemNames.end() ? n->second : text.substr(open + 3, close - open - 3);
			pos = close;
		}
		out += text.substr(pos);
		return out;
	}

	std::string TranslatePlayerBotI18nValue(TPlayerBotI18nLang& lang, const std::string& value, int depth, bool* ok)
	{
		if (ok)
			*ok = true;
		if (value.empty() || depth > 3)
			return value;
		// The spaces round it stay where they were.
		size_t a = 0, b = value.size();
		while (a < b && value[a] == ' ')
			++a;
		while (b > a && value[b - 1] == ' ')
			--b;
		if (a == b)
			return value;
		const std::string core = value.substr(a, b - a);
		bool digits = true;
		for (size_t i = 0; i < core.size() && digits; ++i)
			digits = isdigit((unsigned char)core[i]) || core[i] == '.' || core[i] == ',' || core[i] == 'k' ||
					core[i] == '%' || core[i] == '+' || core[i] == '-';
		if (digits)
			return value;
		std::string out;
		if (core.find("|H") != std::string::npos)
			out = TranslatePlayerBotI18nLinks(lang, core);
		else
		{
			std::string folded = FoldPlayerBotI18n(core, PlayerBotI18nPolishPage());
			std::string trimmed = folded;
			TrimPlayerBotI18nEnd(trimmed);
			if (!TranslatePlayerBotI18nWhole(lang, core, folded, 0, trimmed.size(), out, depth) &&
					!TranslatePlayerBotI18nName(lang, core, out))
			{
				out = core;
				bool all = false;
				// A list: "Kosc x3, Miecz+5" item by item.
				if (core.find(", ") != std::string::npos)
				{
					all = true;
					std::string joined;
					size_t from = 0;
					while (from <= core.size())
					{
						size_t comma = core.find(", ", from);
						if (comma == std::string::npos)
							comma = core.size();
						// Item by item: a part must be an item's or a monster's name, not a sentence.
						std::string part;
						const bool partOk = TranslatePlayerBotI18nName(lang, core.substr(from, comma - from), part);
						if (!joined.empty())
							joined += ", ";
						joined += part;
						all = all && partOk;
						from = comma + 2;
					}
					if (all)
						out = joined;
				}
				if (!all && ok)
					*ok = false;
			}
			else if (trimmed.size() < core.size() && (out.empty() || out[out.size() - 1] != '.'))
				out += core.substr(trimmed.size());
		}
		return value.substr(0, a) + out + value.substr(b);
	}

	void NotePlayerBotI18nMiss(TPlayerBotI18nLang& lang, const std::string& text)
	{
		if (!s_PlayerBotI18nConfig.logMisses || lang.missed.size() >= PLAYERBOT_I18N_MAX_MISSES)
			return;
		if (!lang.missed.insert(text).second)
			return;
		const std::string path = std::string(PLAYERBOT_I18N_MISS_PREFIX) + lang.code + ".tsv";
		if (FILE* fp = fopen(path.c_str(), "a"))
		{
			std::string line = PlayerBotI18nToUtf8(text, PlayerBotI18nPolishPage());
			for (size_t i = 0; i < line.size(); ++i)
				if (line[i] == '\t' || line[i] == '\n' || line[i] == '\r')
					line[i] = ' ';
			fprintf(fp, "%s\n", line.c_str());
			fclose(fp);
		}
	}

	// Where a line may be cut into pieces: after a mark (". ", ", ", "? ") or a
	// smiley (":D ", "xD ") followed by a space.
	bool IsPlayerBotI18nSentenceEnd(const std::string& s, size_t i)
	{
		if (i + 1 >= s.size() || s[i + 1] != ' ')
			return false;
		const char c = s[i];
		if (c == '.' || c == '!' || c == '?' || c == ',' || c == ';' || c == ':')
			return true;
		if (i == 0)
			return false;
		const char p = s[i - 1];
		return ((p == ':' || p == ';') && (c == 'D' || c == 'P' || c == 'p' || c == ')' || c == '(' || c == 'd')) ||
				((p == 'x' || p == 'X') && (c == 'D' || c == 'd'));
	}

	// Polish line -> the reader's language. False when some part of it is not
	// in the catalog (`out` is then empty).
	bool TranslatePlayerBotI18nLine(TPlayerBotI18nLang& lang, const std::string& text, std::string& out)
	{
		out.clear();
		if (text.empty())
			return true;
		const std::string folded = FoldPlayerBotI18n(text, PlayerBotI18nPolishPage());
		// The cuts: after ". ", "! ", "? ", ", " ...; the line's end.
		std::vector<size_t> cuts;   // start offsets of the pieces, and the end
		cuts.push_back(0);
		for (size_t i = 0; i + 1 < text.size(); ++i)
			if (IsPlayerBotI18nSentenceEnd(text, i))
				cuts.push_back(i + 2);
		cuts.push_back(text.size());
		const size_t n = cuts.size();
		if (n > 24)
			return false;
		// best[j]: the fewest pieces covering text[0, cuts[j]), and how.
		std::vector<int> best(n, INT_MAX);
		std::vector<int> from(n, -1);
		std::vector<std::string> piece(n);
		best[0] = 0;
		for (size_t j = 1; j < n; ++j)
		{
			for (size_t i = 0; i < j; ++i)
			{
				if (best[i] == INT_MAX || best[i] + 1 >= best[j])
					continue;
				// The piece without the space after its mark.
				size_t s = cuts[i], e = cuts[j];
				if (j + 1 < n)
					e -= 1;   // the space
				std::string seg = folded.substr(s, e - s);
				// Its closing mark is its own: ',' is cut off, '.' is optional anyway.
				size_t core = seg.size();
				while (core > 0 && seg[core - 1] == ' ')
					--core;
				if (core > 0 && (seg[core - 1] == ',' || seg[core - 1] == ';'))
					--core;
				if (core >= 2 && seg[core - 1] == '.' && seg[core - 2] != '.')
					--core;
				std::string t;
				if (!TranslatePlayerBotI18nWhole(lang, text, folded, s, s + core, t, 0))
				{
					// A smiley the template has not got stays the bot's own: "Expie w Joan :D".
					size_t bare = core;
					if (bare >= 3 && seg[bare - 3] == ' ' &&
							((seg[bare - 2] == ':' || seg[bare - 2] == ';' || seg[bare - 2] == 'x') &&
							strchr("dDpP)(", seg[bare - 1])))
						bare -= 3;
					if (bare == core || bare == 0)
						continue;
					std::string b = seg.substr(0, bare);
					size_t cut = bare;
					if (cut >= 2 && b[cut - 1] == '.' && b[cut - 2] != '.')
						--cut;
					if (!TranslatePlayerBotI18nWhole(lang, text, folded, s, s + cut, t, 0))
						continue;
					core = cut;
				}
				// The mark the Polish piece closed with, unless the translation closes on its own.
				const std::string tail = text.substr(s + core, e - (s + core));
				if (!tail.empty() && !t.empty())
				{
					const char last = t[t.size() - 1];
					if (last == '.' || last == '!' || last == '?')
					{
						if (tail[0] == ',' || tail[0] == ';')
							t.erase(t.size() - 1);
						else if (tail[0] == '.')
							t.erase(t.size() - 1);
					}
				}
				t += tail;
				// A piece the Polish wrote small starts small (the hand's lowercase).
				const unsigned char c0 = (unsigned char)text[s];
				if (c0 >= 'a' && c0 <= 'z' && !t.empty() && t[0] >= 'A' && t[0] <= 'Z' &&
						!(t.size() > 1 && t[1] >= 'A' && t[1] <= 'Z'))
					t[0] = (char)(t[0] - 'A' + 'a');
				best[j] = best[i] + 1;
				from[j] = (int)i;
				piece[j] = t;
			}
		}
		if (best[n - 1] == INT_MAX)
			return false;
		std::vector<std::string> parts;
		for (int j = (int)n - 1; j > 0; j = from[j])
			parts.push_back(piece[j]);
		for (size_t k = parts.size(); k-- > 0; )
		{
			if (!out.empty())
				out += ' ';
			out += parts[k];
		}
		// A line the Polish closed without a full stop closes so in the translation.
		const char lastPl = text[text.size() - 1];
		if (lastPl != '.' && !out.empty() && out[out.size() - 1] == '.' &&
				!(out.size() >= 2 && out[out.size() - 2] == '.'))
			out.erase(out.size() - 1);
		out = TranslatePlayerBotI18nLinks(lang, out);
		return true;
	}

	// ------------------------------------------------------------ languages of people

	struct TPlayerBotI18nDetected
	{
		std::string lang;
		DWORD until;
	};
	std::map<DWORD, TPlayerBotI18nDetected> s_mapPlayerBotI18nDetectedByPID;
	std::map<std::string, TPlayerBotI18nDetected> s_mapPlayerBotI18nByName;   // the last known, for a person of another core

	void NotePlayerBotPersonLanguage(DWORD pid, const char* name, const std::string& lang, bool detected)
	{
		const DWORD until = get_dword_time() + PLAYERBOT_I18N_DETECT_TTL_MS;
		if (detected && pid)
		{
			TPlayerBotI18nDetected& d = s_mapPlayerBotI18nDetectedByPID[pid];
			d.lang = lang;
			d.until = until;
		}
		if (name && *name)
		{
			TPlayerBotI18nDetected& d = s_mapPlayerBotI18nByName[name];
			d.lang = lang;
			d.until = until;
		}
		if (s_mapPlayerBotI18nByName.size() > 8192)
			s_mapPlayerBotI18nByName.clear();
		if (s_mapPlayerBotI18nDetectedByPID.size() > 8192)
			s_mapPlayerBotI18nDetectedByPID.clear();
	}

	// The language a person reads now: what the person last wrote in, when
	// DETECT found it lately, else the client's choice.
	std::string GetPlayerBotPersonLanguage(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
			return "pl";
		std::map<DWORD, TPlayerBotI18nDetected>::iterator it = s_mapPlayerBotI18nDetectedByPID.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotI18nDetectedByPID.end())
		{
			if ((int)(it->second.until - get_dword_time()) > 0)
				return it->second.lang;
			s_mapPlayerBotI18nDetectedByPID.erase(it);
		}
		const char* lang = GetPlayerLanguage(ch);
		const std::string code = lang && *lang ? lang : "pl";
		TPlayerBotI18nDetected& d = s_mapPlayerBotI18nByName[ch->GetName()];
		d.lang = code;
		d.until = get_dword_time() + PLAYERBOT_I18N_DETECT_TTL_MS;
		return code;
	}

	// A person known by name only (another core's): the last known language.
	std::string GetPlayerBotPersonLanguageByName(const char* name)
	{
		if (!name || !*name)
			return "pl";
		if (LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(name))
			return GetPlayerBotPersonLanguage(ch);
		std::map<std::string, TPlayerBotI18nDetected>::const_iterator it = s_mapPlayerBotI18nByName.find(name);
		return it != s_mapPlayerBotI18nByName.end() ? it->second.lang : std::string("pl");
	}

	std::string GetPlayerBotPersonLanguageByPID(DWORD pid)
	{
		if (LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid))
			return GetPlayerBotPersonLanguage(ch);
		std::map<DWORD, TPlayerBotI18nDetected>::const_iterator it = s_mapPlayerBotI18nDetectedByPID.find(pid);
		return it != s_mapPlayerBotI18nDetectedByPID.end() ? it->second.lang : std::string("pl");
	}

	// ------------------------------------------------------------ the API

	// The Polish line for a reader of `lang`: translated, or - FALLBACK 0 -
	// the Polish when the catalog cannot; an empty result means "say nothing".
	// A line marked PLAYERBOT_I18N_DONE is already the reader's: unmarked.
	std::string LocalizePlayerBotLine(const std::string& lang, const char* text)
	{
		if (!text)
			return std::string();
		if (text[0] == PLAYERBOT_I18N_DONE)
			return std::string(text + 1);
		TPlayerBotI18nLang* l = FindPlayerBotI18nLang(lang);
		if (!l)
			return text;
		std::string out;
		if (TranslatePlayerBotI18nLine(*l, text, out))
			return out;
		NotePlayerBotI18nMiss(*l, text);
		return s_PlayerBotI18nConfig.fallback ? std::string() : std::string(text);
	}

	// For the conversation (playerbot_conv_style.h): false when the catalog
	// has no full translation.
	bool TryLocalizePlayerBotLine(const std::string& lang, const std::string& text, std::string& out)
	{
		TPlayerBotI18nLang* l = FindPlayerBotI18nLang(lang);
		if (!l)
			return false;
		if (TranslatePlayerBotI18nLine(*l, text, out))
			return true;
		NotePlayerBotI18nMiss(*l, text);
		return false;
	}

	std::string LocalizePlayerBotLineFor(LPCHARACTER reader, const char* text)
	{
		return LocalizePlayerBotLine(GetPlayerBotPersonLanguage(reader), text);
	}

	// ------------------------------------------------------------ understanding

	// The few Polish words that say a line is Polish (the bots' own lexicon is
	// far richer; this only has to outvote another language's).
	bool IsPlayerBotI18nPolishWord(const std::string& w)
	{
		static const char* const k[] = {
			"jestem", "jestes", "gdzie", "co", "jak", "siema", "czesc", "nie", "tak", "ile", "masz", "robisz", "expisz",
			"czy", "mozesz", "dzieki", "sprzedam", "kupie", "kto", "jaki", "jaka", "jakie", "chodz", "daj", "mi", "ty",
			"ja", "sie", "na", "do", "w", "z", "to", "ze", "juz", "teraz", "elo", "hej", "witam", "pomoz", "pomozesz",
			"potrzebuje", "dobra", "spoko", "moze", "bo", "ale", "poziom", "lvl", "gildia", "gildii", "zaproszenie",
		};
		for (size_t i = 0; i < sizeof(k) / sizeof(k[0]); ++i)
			if (w == k[i])
				return true;
		return false;
	}

	// The language a line is clearly in, or "" when it is not clear.
	std::string DetectPlayerBotLineLanguage(const char* text)
	{
		if (!text || !*text || !s_PlayerBotI18nConfig.detect)
			return std::string();
		RefreshPlayerBotI18n();
		std::string best;
		int bestScore = 0, second = 0, polish = 0;
		size_t words = 0;
		for (std::map<std::string, TPlayerBotI18nLang>::const_iterator it = s_mapPlayerBotI18n.begin();
				it != s_mapPlayerBotI18n.end(); ++it)
		{
			std::vector<std::string> w;
			SplitPlayerBotI18nWords(FoldPlayerBotI18n(text, it->second.page), w);
			words = w.size();
			int score = 0;
			polish = 0;
			for (size_t i = 0; i < w.size(); ++i)
			{
				if (it->second.detectWords.count(w[i]))
					++score;
				if (IsPlayerBotI18nPolishWord(w[i]))
					++polish;
			}
			if (score > bestScore)
			{
				second = bestScore;
				bestScore = score;
				best = it->first;
			}
			else if (score > second)
				second = score;
		}
		if (bestScore == 0)
			return polish > 0 ? std::string("pl") : std::string();
		if (bestScore <= polish || bestScore == second)
			return polish > bestScore ? std::string("pl") : std::string();
		// One word decides a short line ("hello", "where r u"), two a long one.
		if (bestScore >= 2 || words <= 3)
			return best;
		return std::string();
	}

	// A person's line in the bots' Polish: their words for the Polish ones the
	// bots' rules know ("where are you" -> "gdzie jestes"); the rest kept.
	std::string RewritePlayerBotI18nInput(const TPlayerBotI18nLang& lang, const char* text)
	{
		const std::string raw(text);
		const std::string folded = FoldPlayerBotI18n(raw, lang.page);
		// Words with where they are in the line.
		std::vector<std::pair<size_t, size_t> > spans;
		std::vector<std::string> words;
		for (size_t i = 0; i < folded.size(); )
		{
			const unsigned char c = (unsigned char)folded[i];
			const bool wc = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c >= 0x80 || c == '\'';
			if (!wc)
			{
				++i;
				continue;
			}
			size_t j = i;
			while (j < folded.size())
			{
				const unsigned char d = (unsigned char)folded[j];
				if (!((d >= 'a' && d <= 'z') || (d >= '0' && d <= '9') || d >= 0x80 || d == '\''))
					break;
				++j;
			}
			spans.push_back(std::make_pair(i, j - i));
			words.push_back(folded.substr(i, j - i));
			i = j;
		}
		std::string out;
		size_t pos = 0;   // in raw
		for (size_t w = 0; w < words.size(); )
		{
			size_t used = 0;
			const std::string* pl = NULL;
			for (size_t k = 0; k < lang.input.size() && !used; ++k)
			{
				const std::vector<std::string>& phrase = lang.input[k].first;
				if (w + phrase.size() > words.size())
					continue;
				bool ok = true;
				for (size_t q = 0; q < phrase.size() && ok; ++q)
				{
					const std::string& p = phrase[q];
					// "lvl*" - a prefix.
					if (!p.empty() && p[p.size() - 1] == '*')
						ok = words[w + q].compare(0, p.size() - 1, p, 0, p.size() - 1) == 0;
					else
						ok = words[w + q] == p;
				}
				if (ok)
				{
					used = phrase.size();
					pl = &lang.input[k].second;
				}
			}
			if (!used)
			{
				++w;
				continue;
			}
			out += raw.substr(pos, spans[w].first - pos);
			out += *pl;
			const size_t endWord = w + used - 1;
			pos = spans[endWord].first + spans[endWord].second;
			w += used;
		}
		out += raw.substr(pos);
		return out;
	}

	// A person's whisper or chat line, before the bots read it: the person's
	// language noted (DETECT) and the line put into the bots' Polish. Returns
	// the line to read - `text` itself for a Polish one.
	const char* LocalizePlayerBotInput(LPCHARACTER from, DWORD pid, const char* name, const char* text, std::string& buf)
	{
		if (!text || !*text)
			return text;
		RefreshPlayerBotI18n();
		if (!s_PlayerBotI18nConfig.enabled || s_mapPlayerBotI18n.empty())
			return text;
		std::string lang = from ? GetPlayerBotPersonLanguage(from) : GetPlayerBotPersonLanguageByName(name);
		const std::string detected = DetectPlayerBotLineLanguage(text);
		if (!detected.empty() && detected != lang)
		{
			if (detected == "pl")
			{
				// Writes Polish: read in Polish while the client says nothing else.
				if (from)
					s_mapPlayerBotI18nDetectedByPID.erase(from->GetPlayerID());
				const char* chosen = from ? GetPlayerLanguage(from) : "pl";
				lang = chosen && *chosen ? chosen : "pl";
				if (lang != "pl")
				{
					NotePlayerBotPersonLanguage(pid, name, "pl", true);
					lang = "pl";
				}
				else
					NotePlayerBotPersonLanguage(0, name, "pl", false);
			}
			else
			{
				NotePlayerBotPersonLanguage(pid, name, detected, true);
				lang = detected;
				sys_log(0, "PLAYERBOT_I18N: %s writes in %s", name ? name : "?", detected.c_str());
			}
		}
		const TPlayerBotI18nLang* l = FindPlayerBotI18nLang(lang);
		if (!l || l->input.empty())
			return text;
		buf = RewritePlayerBotI18nInput(*l, text);
		return buf.c_str();
	}

	// ------------------------------------------------------------ public channels

	DWORD s_dwPlayerBotI18nCensus = 0;
	std::map<std::string, int> s_mapPlayerBotI18nOnline;   // the languages of the players online, not the world's
	int s_iPlayerBotI18nOnlineForeign = 0;

	void CensusPlayerBotI18nLanguages()
	{
		const DWORD now = get_dword_time();
		if (s_dwPlayerBotI18nCensus != 0 && now - s_dwPlayerBotI18nCensus < 30000)
			return;
		s_dwPlayerBotI18nCensus = now;
		s_mapPlayerBotI18nOnline.clear();
		s_iPlayerBotI18nOnlineForeign = 0;
		const std::string world = Mt2009DefaultLanguage();
		const DESC_MANAGER::DESC_SET& set = DESC_MANAGER::instance().GetClientSet();
		for (DESC_MANAGER::DESC_SET::const_iterator it = set.begin(); it != set.end(); ++it)
		{
			LPDESC d = *it;
			if (!d || d->IsBot() || !d->GetCharacter())
				continue;
			const std::string lang = GetPlayerBotPersonLanguage(d->GetCharacter());
			if (lang == world || (lang != "pl" && s_mapPlayerBotI18n.find(lang) == s_mapPlayerBotI18n.end()))
				continue;
			++s_mapPlayerBotI18nOnline[lang];
			++s_iPlayerBotI18nOnlineForeign;
		}
	}

	// The language a bot speaks on the public channels now: the world's (the
	// server's default language, MT2009_PLUS_LANGUAGE_DEFAULT_V1), or for
	// PUBLIC_FOREIGN_PCT of the bots one of the others.
	std::string GetPlayerBotPublicLanguage(LPCHARACTER bot)
	{
		RefreshPlayerBotI18n();
		const TPlayerBotI18nConfig& c = s_PlayerBotI18nConfig;
		const std::string world = Mt2009DefaultLanguage();
		if (!bot || !c.enabled || c.publicPct <= 0 || s_mapPlayerBotI18n.empty())
			return world;
		// The same bots every time: a bot does not change its tongue mid-sentence.
		const DWORD pid = bot->GetPlayerID();
		const DWORD h = (pid * 2654435761u) ^ 0x5bd1e995u;
		if ((int)(h % 100u) >= c.publicPct)
			return world;
		CensusPlayerBotI18nLanguages();
		const DWORD pick = (h / 100u) * 2246822519u;
		if (s_iPlayerBotI18nOnlineForeign > 0)
		{
			int n = (int)(pick % (DWORD)s_iPlayerBotI18nOnlineForeign);
			for (std::map<std::string, int>::const_iterator it = s_mapPlayerBotI18nOnline.begin();
					it != s_mapPlayerBotI18nOnline.end(); ++it)
			{
				if (n < it->second)
					return it->first;
				n -= it->second;
			}
		}
		if (c.publicNeedPlayers)
			return world;
		// Any other language of the catalogs - Polish (no catalog, the bots' own) among them when the world's is not.
		std::vector<std::string> others;
		if (world != "pl")
			others.push_back("pl");
		for (std::map<std::string, TPlayerBotI18nLang>::const_iterator it = s_mapPlayerBotI18n.begin();
				it != s_mapPlayerBotI18n.end(); ++it)
			if (it->first != world)
				others.push_back(it->first);
		if (others.empty())
			return world;
		return others[pick % (DWORD)others.size()];
	}

	// Who a public line answers, while it is being said: the line is in that
	// person's language rather than the bot's (an answer on the shout).
	std::string s_strPlayerBotI18nPublicFor;

	// A bot's public line in its public language; the Polish when the catalog
	// cannot (a foreign bot that says something only in Polish is a Pole for a moment).
	std::string LocalizePlayerBotPublicLine(LPCHARACTER bot, const char* text)
	{
		if (!text)
			return std::string();
		if (text[0] == PLAYERBOT_I18N_DONE)
			return std::string(text + 1);
		const std::string lang = !s_strPlayerBotI18nPublicFor.empty() ? s_strPlayerBotI18nPublicFor
				: GetPlayerBotPublicLanguage(bot);
		TPlayerBotI18nLang* l = FindPlayerBotI18nLang(lang);
		if (!l)
			return text;
		std::string out;
		if (TranslatePlayerBotI18nLine(*l, text, out))
			return out;
		NotePlayerBotI18nMiss(*l, text);
		return text;
	}

	// "Name : text" of the shout: the text part.
	std::string LocalizePlayerBotShout(const char* msg)
	{
		if (!msg)
			return std::string();
		const char* sep = strstr(msg, " : ");
		if (!sep)
			return msg;
		const std::string name(msg, sep - msg);
		LPCHARACTER bot = CHARACTER_MANAGER::instance().FindPC(name.c_str());
		if (!bot && s_strPlayerBotI18nPublicFor.empty())
			return msg;
		return name + " : " + LocalizePlayerBotPublicLine(bot, sep + 3);
	}

	// A guild's chat: the language most of its players online read (the
	// world's - the server's default - when none is online).
	std::string GetPlayerBotGuildLanguage(CGuild* guild)
	{
		const std::string world = Mt2009DefaultLanguage();
		if (!guild)
			return world;
		RefreshPlayerBotI18n();
		if (!s_PlayerBotI18nConfig.enabled || s_mapPlayerBotI18n.empty())
			return world;
		std::map<std::string, int> count;
		const DESC_MANAGER::DESC_SET& set = DESC_MANAGER::instance().GetClientSet();
		for (DESC_MANAGER::DESC_SET::const_iterator it = set.begin(); it != set.end(); ++it)
		{
			LPDESC d = *it;
			if (!d || d->IsBot() || !d->GetCharacter() || d->GetCharacter()->GetGuild() != guild)
				continue;
			++count[GetPlayerBotPersonLanguage(d->GetCharacter())];
		}
		std::string best = world;
		int most = count[world];
		for (std::map<std::string, int>::const_iterator it = count.begin(); it != count.end(); ++it)
			if (it->second > most)
			{
				most = it->second;
				best = it->first;
			}
		return best;
	}

	void ChatPlayerBotGuild(CGuild* guild, const char* text)
	{
		if (!guild || !text)
			return;
		const std::string lang = GetPlayerBotGuildLanguage(guild);
		TPlayerBotI18nLang* l = FindPlayerBotI18nLang(lang);
		std::string out;
		if (l && !TranslatePlayerBotI18nLine(*l, text, out))
		{
			NotePlayerBotI18nMiss(*l, text);
			out.clear();
		}
		guild->Chat(out.empty() ? text : out.c_str());
	}
}

#endif
