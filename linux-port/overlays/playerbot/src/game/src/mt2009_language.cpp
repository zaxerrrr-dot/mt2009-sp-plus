// MT2009_PLUS_LANGUAGE_V1: the server's language core - the reader's language, the dictionaries, the chat lines in the
// reader's language, "/lang", the quests' pc.get_language() / mt2009_tr() (server-patches/language/README.md).
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "db.h"
#include "locale.hpp"
#include "locale_service.h"
#include "questmanager.h"
#include "questlua.h"
#include "mt2009_language.h"

#include <dirent.h>
#include <unistd.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <algorithm>

namespace mt2009_language
{
	static const char* const POLISH = "pl";
	static const char* const ENGLISH = "en";

	// Code page tables: the Unicode code point of the bytes 0x80-0xFF (0 - none).
	struct SCodePage
	{
		int cp;
		unsigned short table[128];
	};

	static const SCodePage s_codePages[] =
	{
	{ 1250, {
		0x20AC, 0x0000, 0x201A, 0x0000, 0x201E, 0x2026, 0x2020, 0x2021, 0x0000, 0x2030, 0x0160, 0x2039, 0x015A, 0x0164, 0x017D, 0x0179,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x0000, 0x2122, 0x0161, 0x203A, 0x015B, 0x0165, 0x017E, 0x017A,
		0x00A0, 0x02C7, 0x02D8, 0x0141, 0x00A4, 0x0104, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x015E, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x017B,
		0x00B0, 0x00B1, 0x02DB, 0x0142, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x0105, 0x015F, 0x00BB, 0x013D, 0x02DD, 0x013E, 0x017C,
		0x0154, 0x00C1, 0x00C2, 0x0102, 0x00C4, 0x0139, 0x0106, 0x00C7, 0x010C, 0x00C9, 0x0118, 0x00CB, 0x011A, 0x00CD, 0x00CE, 0x010E,
		0x0110, 0x0143, 0x0147, 0x00D3, 0x00D4, 0x0150, 0x00D6, 0x00D7, 0x0158, 0x016E, 0x00DA, 0x0170, 0x00DC, 0x00DD, 0x0162, 0x00DF,
		0x0155, 0x00E1, 0x00E2, 0x0103, 0x00E4, 0x013A, 0x0107, 0x00E7, 0x010D, 0x00E9, 0x0119, 0x00EB, 0x011B, 0x00ED, 0x00EE, 0x010F,
		0x0111, 0x0144, 0x0148, 0x00F3, 0x00F4, 0x0151, 0x00F6, 0x00F7, 0x0159, 0x016F, 0x00FA, 0x0171, 0x00FC, 0x00FD, 0x0163, 0x02D9,
	} },
	{ 1251, {
		0x0402, 0x0403, 0x201A, 0x0453, 0x201E, 0x2026, 0x2020, 0x2021, 0x20AC, 0x2030, 0x0409, 0x2039, 0x040A, 0x040C, 0x040B, 0x040F,
		0x0452, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x0000, 0x2122, 0x0459, 0x203A, 0x045A, 0x045C, 0x045B, 0x045F,
		0x00A0, 0x040E, 0x045E, 0x0408, 0x00A4, 0x0490, 0x00A6, 0x00A7, 0x0401, 0x00A9, 0x0404, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x0407,
		0x00B0, 0x00B1, 0x0406, 0x0456, 0x0491, 0x00B5, 0x00B6, 0x00B7, 0x0451, 0x2116, 0x0454, 0x00BB, 0x0458, 0x0405, 0x0455, 0x0457,
		0x0410, 0x0411, 0x0412, 0x0413, 0x0414, 0x0415, 0x0416, 0x0417, 0x0418, 0x0419, 0x041A, 0x041B, 0x041C, 0x041D, 0x041E, 0x041F,
		0x0420, 0x0421, 0x0422, 0x0423, 0x0424, 0x0425, 0x0426, 0x0427, 0x0428, 0x0429, 0x042A, 0x042B, 0x042C, 0x042D, 0x042E, 0x042F,
		0x0430, 0x0431, 0x0432, 0x0433, 0x0434, 0x0435, 0x0436, 0x0437, 0x0438, 0x0439, 0x043A, 0x043B, 0x043C, 0x043D, 0x043E, 0x043F,
		0x0440, 0x0441, 0x0442, 0x0443, 0x0444, 0x0445, 0x0446, 0x0447, 0x0448, 0x0449, 0x044A, 0x044B, 0x044C, 0x044D, 0x044E, 0x044F,
	} },
	{ 1252, {
		0x20AC, 0x0000, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x0000, 0x017D, 0x0000,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x0000, 0x017E, 0x0178,
		0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00AA, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF,
		0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C4, 0x00C5, 0x00C6, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x00CC, 0x00CD, 0x00CE, 0x00CF,
		0x00D0, 0x00D1, 0x00D2, 0x00D3, 0x00D4, 0x00D5, 0x00D6, 0x00D7, 0x00D8, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x00DD, 0x00DE, 0x00DF,
		0x00E0, 0x00E1, 0x00E2, 0x00E3, 0x00E4, 0x00E5, 0x00E6, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC, 0x00ED, 0x00EE, 0x00EF,
		0x00F0, 0x00F1, 0x00F2, 0x00F3, 0x00F4, 0x00F5, 0x00F6, 0x00F7, 0x00F8, 0x00F9, 0x00FA, 0x00FB, 0x00FC, 0x00FD, 0x00FE, 0x00FF,
	} },
	{ 1253, {
		0x20AC, 0x0000, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x0000, 0x2030, 0x0000, 0x2039, 0x0000, 0x0000, 0x0000, 0x0000,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x0000, 0x2122, 0x0000, 0x203A, 0x0000, 0x0000, 0x0000, 0x0000,
		0x00A0, 0x0385, 0x0386, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x0000, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x2015,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x0384, 0x00B5, 0x00B6, 0x00B7, 0x0388, 0x0389, 0x038A, 0x00BB, 0x038C, 0x00BD, 0x038E, 0x038F,
		0x0390, 0x0391, 0x0392, 0x0393, 0x0394, 0x0395, 0x0396, 0x0397, 0x0398, 0x0399, 0x039A, 0x039B, 0x039C, 0x039D, 0x039E, 0x039F,
		0x03A0, 0x03A1, 0x0000, 0x03A3, 0x03A4, 0x03A5, 0x03A6, 0x03A7, 0x03A8, 0x03A9, 0x03AA, 0x03AB, 0x03AC, 0x03AD, 0x03AE, 0x03AF,
		0x03B0, 0x03B1, 0x03B2, 0x03B3, 0x03B4, 0x03B5, 0x03B6, 0x03B7, 0x03B8, 0x03B9, 0x03BA, 0x03BB, 0x03BC, 0x03BD, 0x03BE, 0x03BF,
		0x03C0, 0x03C1, 0x03C2, 0x03C3, 0x03C4, 0x03C5, 0x03C6, 0x03C7, 0x03C8, 0x03C9, 0x03CA, 0x03CB, 0x03CC, 0x03CD, 0x03CE, 0x0000,
	} },
	{ 1254, {
		0x20AC, 0x0000, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x0000, 0x0000, 0x0000,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x0000, 0x0000, 0x0178,
		0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00AA, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF,
		0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C4, 0x00C5, 0x00C6, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x00CC, 0x00CD, 0x00CE, 0x00CF,
		0x011E, 0x00D1, 0x00D2, 0x00D3, 0x00D4, 0x00D5, 0x00D6, 0x00D7, 0x00D8, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x0130, 0x015E, 0x00DF,
		0x00E0, 0x00E1, 0x00E2, 0x00E3, 0x00E4, 0x00E5, 0x00E6, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC, 0x00ED, 0x00EE, 0x00EF,
		0x011F, 0x00F1, 0x00F2, 0x00F3, 0x00F4, 0x00F5, 0x00F6, 0x00F7, 0x00F8, 0x00F9, 0x00FA, 0x00FB, 0x00FC, 0x0131, 0x015F, 0x00FF,
	} },
	{ 1255, {
		0x20AC, 0x0000, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0000, 0x2039, 0x0000, 0x0000, 0x0000, 0x0000,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0000, 0x203A, 0x0000, 0x0000, 0x0000, 0x0000,
		0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x20AA, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00D7, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00F7, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF,
		0x05B0, 0x05B1, 0x05B2, 0x05B3, 0x05B4, 0x05B5, 0x05B6, 0x05B7, 0x05B8, 0x05B9, 0x0000, 0x05BB, 0x05BC, 0x05BD, 0x05BE, 0x05BF,
		0x05C0, 0x05C1, 0x05C2, 0x05C3, 0x05F0, 0x05F1, 0x05F2, 0x05F3, 0x05F4, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
		0x05D0, 0x05D1, 0x05D2, 0x05D3, 0x05D4, 0x05D5, 0x05D6, 0x05D7, 0x05D8, 0x05D9, 0x05DA, 0x05DB, 0x05DC, 0x05DD, 0x05DE, 0x05DF,
		0x05E0, 0x05E1, 0x05E2, 0x05E3, 0x05E4, 0x05E5, 0x05E6, 0x05E7, 0x05E8, 0x05E9, 0x05EA, 0x0000, 0x0000, 0x200E, 0x200F, 0x0000,
	} },
	{ 1256, {
		0x20AC, 0x067E, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0679, 0x2039, 0x0152, 0x0686, 0x0698, 0x0688,
		0x06AF, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x06A9, 0x2122, 0x0691, 0x203A, 0x0153, 0x200C, 0x200D, 0x06BA,
		0x00A0, 0x060C, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x06BE, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x061B, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x061F,
		0x06C1, 0x0621, 0x0622, 0x0623, 0x0624, 0x0625, 0x0626, 0x0627, 0x0628, 0x0629, 0x062A, 0x062B, 0x062C, 0x062D, 0x062E, 0x062F,
		0x0630, 0x0631, 0x0632, 0x0633, 0x0634, 0x0635, 0x0636, 0x00D7, 0x0637, 0x0638, 0x0639, 0x063A, 0x0640, 0x0641, 0x0642, 0x0643,
		0x00E0, 0x0644, 0x00E2, 0x0645, 0x0646, 0x0647, 0x0648, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x0649, 0x064A, 0x00EE, 0x00EF,
		0x064B, 0x064C, 0x064D, 0x064E, 0x00F4, 0x064F, 0x0650, 0x00F7, 0x0651, 0x00F9, 0x0652, 0x00FB, 0x00FC, 0x200E, 0x200F, 0x06D2,
	} },
	{ 1257, {
		0x20AC, 0x0000, 0x201A, 0x0000, 0x201E, 0x2026, 0x2020, 0x2021, 0x0000, 0x2030, 0x0000, 0x2039, 0x0000, 0x00A8, 0x02C7, 0x00B8,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x0000, 0x2122, 0x0000, 0x203A, 0x0000, 0x00AF, 0x02DB, 0x0000,
		0x00A0, 0x0000, 0x00A2, 0x00A3, 0x00A4, 0x0000, 0x00A6, 0x00A7, 0x00D8, 0x00A9, 0x0156, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00C6,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00F8, 0x00B9, 0x0157, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00E6,
		0x0104, 0x012E, 0x0100, 0x0106, 0x00C4, 0x00C5, 0x0118, 0x0112, 0x010C, 0x00C9, 0x0179, 0x0116, 0x0122, 0x0136, 0x012A, 0x013B,
		0x0160, 0x0143, 0x0145, 0x00D3, 0x014C, 0x00D5, 0x00D6, 0x00D7, 0x0172, 0x0141, 0x015A, 0x016A, 0x00DC, 0x017B, 0x017D, 0x00DF,
		0x0105, 0x012F, 0x0101, 0x0107, 0x00E4, 0x00E5, 0x0119, 0x0113, 0x010D, 0x00E9, 0x017A, 0x0117, 0x0123, 0x0137, 0x012B, 0x013C,
		0x0161, 0x0144, 0x0146, 0x00F3, 0x014D, 0x00F5, 0x00F6, 0x00F7, 0x0173, 0x0142, 0x015B, 0x016B, 0x00FC, 0x017C, 0x017E, 0x02D9,
	} },
	{ 1258, {
		0x20AC, 0x0000, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0000, 0x2039, 0x0152, 0x0000, 0x0000, 0x0000,
		0x0000, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0000, 0x203A, 0x0153, 0x0000, 0x0000, 0x0178,
		0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00AA, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00AF,
		0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF,
		0x00C0, 0x00C1, 0x00C2, 0x0102, 0x00C4, 0x00C5, 0x00C6, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x0300, 0x00CD, 0x00CE, 0x00CF,
		0x0110, 0x00D1, 0x0309, 0x00D3, 0x00D4, 0x01A0, 0x00D6, 0x00D7, 0x00D8, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x01AF, 0x0303, 0x00DF,
		0x00E0, 0x00E1, 0x00E2, 0x0103, 0x00E4, 0x00E5, 0x00E6, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x0301, 0x00ED, 0x00EE, 0x00EF,
		0x0111, 0x00F1, 0x0323, 0x00F3, 0x00F4, 0x01A1, 0x00F6, 0x00F7, 0x00F8, 0x00F9, 0x00FA, 0x00FB, 0x00FC, 0x01B0, 0x20AB, 0x00FF,
	} },
	};

	static const unsigned short* CodePageTable(int cp)
	{
		for (size_t i = 0; i < sizeof(s_codePages) / sizeof(s_codePages[0]); ++i)
			if (s_codePages[i].cp == cp)
				return s_codePages[i].table;
		return NULL;
	}

	// The client's code page of a language (GF's) when its language.cfg names none.
	static int DefaultCodePage(const std::string& code)
	{
		if (code == "pl" || code == "cz" || code == "hu" || code == "ro" || code == "sk" || code == "hr" || code == "si")
			return 1250;
		if (code == "ru" || code == "bg")
			return 1251;
		if (code == "gr")
			return 1253;
		if (code == "tr")
			return 1254;
		if (code == "ae")
			return 1256;
		return 1252;
	}

	// UTF-8 (the dictionaries) to a code page; a character the page lacks becomes '?'.
	static std::string FromUtf8(const std::string& s, int cp)
	{
		const unsigned short* table = CodePageTable(cp);
		std::string out;
		out.reserve(s.size());
		size_t i = 0;
		while (i < s.size())
		{
			const unsigned char c = (unsigned char) s[i];
			if (c < 0x80)
			{
				out += (char) c;
				++i;
				continue;
			}
			unsigned int u = 0;
			size_t n = 0;
			if ((c & 0xE0) == 0xC0)
			{
				u = c & 0x1F;
				n = 1;
			}
			else if ((c & 0xF0) == 0xE0)
			{
				u = c & 0x0F;
				n = 2;
			}
			else if ((c & 0xF8) == 0xF0)
			{
				u = c & 0x07;
				n = 3;
			}
			else
			{
				out += '?';
				++i;
				continue;
			}
			bool ok = true;
			for (size_t k = 1; k <= n; ++k)
			{
				if (i + k >= s.size() || (((unsigned char) s[i + k]) & 0xC0) != 0x80)
				{
					ok = false;
					break;
				}
				u = (u << 6) | (((unsigned char) s[i + k]) & 0x3F);
			}
			if (!ok)
			{
				out += '?';
				++i;
				continue;
			}
			i += n + 1;
			char b = '?';
			if (table)
			{
				for (int k = 0; k < 128; ++k)
				{
					if (table[k] == u)
					{
						b = (char) (0x80 + k);
						break;
					}
				}
			}
			if (b == '?' && u == 0x00A0)
				b = ' ';
			out += b;
		}
		return out;
	}

	// The conversions of a printf format, a token each ("d;", "ld;", "s;", "?;" for one this code will not hand to
	// vsnprintf: '*', 'n', anything unknown). count gets the number of tokens.
	static std::string Conversions(const std::string& s, int& count)
	{
		std::string sig;
		count = 0;
		for (size_t i = 0; i < s.size(); ++i)
		{
			if (s[i] != '%')
				continue;
			if (i + 1 < s.size() && s[i + 1] == '%')
			{
				++i;
				continue;
			}
			size_t j = i + 1;
			while (j < s.size() && strchr("-+ #0", s[j]) && s[j])
				++j;
			while (j < s.size() && isdigit((unsigned char) s[j]))
				++j;
			if (j < s.size() && s[j] == '.')
			{
				++j;
				while (j < s.size() && isdigit((unsigned char) s[j]))
					++j;
			}
			std::string len;
			while (j < s.size() && s[j] && strchr("hlLqjzt", s[j]))
				len += s[j++];
			++count;
			if (j < s.size() && s[j] && strchr("diouxXeEfgGcs", s[j]))
			{
				sig += len;
				sig += s[j];
				sig += ';';
				i = j;
			}
			else
			{
				sig += "?;";
				if (j > i)
					i = j - 1;
			}
		}
		return sig;
	}

	struct SEntry
	{
		std::string text;
		bool format;		// the same conversions as the Polish: usable as a printf format in its place
	};

	// A Polish format and its translation, cut at their conversions: src[0] v1 src[1] v2 ... src[n].
	struct STemplate
	{
		std::vector<std::string> src;
		std::vector<std::string> dst;
		std::string conv;	// a conversion character per value
		size_t literal;		// the Polish's literal bytes (the more, the earlier it is tried)
	};

	struct SLanguage
	{
		bool loaded;
		int codePage;
		std::string fallback;
		std::unordered_map<std::string, SEntry> exact;
		std::vector<STemplate> templates;
		std::unordered_map<std::string, size_t> templateOf;		// Polish format -> its template
		std::unordered_map<std::string, std::vector<size_t> > buckets;	// the first two bytes of src[0]
		std::vector<size_t> generic;		// src[0] shorter than two bytes
		// Pieces of texts a quest glues together ("Koszt: " .. n .. " Yang"): replaced inside a line nothing else
		// translates (*fragments*.tsv), the longest first.
		std::vector<std::pair<std::string, std::string> > fragments;
		std::unordered_map<std::string, std::vector<size_t> > fragmentBuckets;	// their first two bytes
		std::unordered_map<DWORD, std::string> items;
		std::unordered_map<DWORD, std::string> mobs;
		size_t files;
		size_t texts;
		size_t dropped;

		SLanguage() : loaded(false), codePage(1252), files(0), texts(0), dropped(0) {}
	};

	static std::map<std::string, SLanguage> s_languages;
	static std::vector<std::string> s_available;
	static bool s_scanned = false;
	static std::unordered_map<DWORD, std::string> s_playerLanguage;
	static bool s_dbColumn = true;

	static std::string LanguageDir()
	{
		return LocaleService_GetBasePath() + "/lang";
	}

	static bool IsPolish(const char* lang)
	{
		return !lang || !*lang || !strcmp(lang, POLISH);
	}

	// "cs" -> "cz" and the like; "" for anything that is not 2-4 letters.
	static std::string Normalize(const char* code)
	{
		std::string s;
		for (const char* p = code; p && *p; ++p)
		{
			const char c = (char) tolower((unsigned char) *p);
			if (c < 'a' || c > 'z')
				return "";
			s += c;
		}
		if (s.size() < 2 || s.size() > 4)
			return "";
		if (s == "cs")
			return "cz";
		if (s == "el")
			return "gr";
		if (s == "ar")
			return "ae";
		if (s == "eng" || s == "gb" || s == "us")
			return "en";
		if (s == "pol")
			return "pl";
		if (s == "ger" || s == "deu")
			return "de";
		return s;
	}

	static void Scan()
	{
		if (s_scanned)
			return;
		s_scanned = true;
		s_available.clear();
		DIR* dir = opendir(LanguageDir().c_str());
		if (!dir)
			return;
		while (dirent* de = readdir(dir))
		{
			if (de->d_name[0] == '.')
				continue;
			const std::string code = Normalize(de->d_name);
			if (!code.empty() && code == de->d_name && code != POLISH)
				s_available.push_back(code);
		}
		closedir(dir);
		std::sort(s_available.begin(), s_available.end());
	}

	static std::string Unescape(const std::string& s)
	{
		std::string out;
		out.reserve(s.size());
		for (size_t i = 0; i < s.size(); ++i)
		{
			if (s[i] == '\\' && i + 1 < s.size())
			{
				const char n = s[i + 1];
				if (n == 't')
				{
					out += '\t';
					++i;
					continue;
				}
				if (n == 'n')
				{
					out += '\n';
					++i;
					continue;
				}
				if (n == '\\')
				{
					out += '\\';
					++i;
					continue;
				}
			}
			out += s[i];
		}
		return out;
	}

	static bool ReadLines(const std::string& path, std::vector<std::string>& lines)
	{
		FILE* fp = fopen(path.c_str(), "rb");
		if (!fp)
			return false;
		std::string data;
		char buf[65536];
		size_t n;
		while ((n = fread(buf, 1, sizeof(buf), fp)) > 0)
			data.append(buf, n);
		fclose(fp);
		if (data.size() >= 3 && (unsigned char) data[0] == 0xEF && (unsigned char) data[1] == 0xBB && (unsigned char) data[2] == 0xBF)
			data.erase(0, 3);
		size_t start = 0;
		while (start <= data.size())
		{
			size_t end = data.find('\n', start);
			if (end == std::string::npos)
				end = data.size();
			std::string line = data.substr(start, end - start);
			if (!line.empty() && line[line.size() - 1] == '\r')
				line.erase(line.size() - 1);
			lines.push_back(line);
			start = end + 1;
		}
		return true;
	}

	// The literal pieces of a format (%% as %), or false when two conversions touch (no piece between them).
	static bool Pieces(const std::string& s, std::vector<std::string>& pieces, std::string& conv)
	{
		pieces.clear();
		conv.clear();
		std::string piece;
		for (size_t i = 0; i < s.size(); ++i)
		{
			if (s[i] != '%')
			{
				piece += s[i];
				continue;
			}
			if (i + 1 < s.size() && s[i + 1] == '%')
			{
				piece += '%';
				++i;
				continue;
			}
			size_t j = i + 1;
			while (j < s.size() && strchr("-+ #0", s[j]) && s[j])
				++j;
			while (j < s.size() && isdigit((unsigned char) s[j]))
				++j;
			if (j < s.size() && s[j] == '.')
			{
				++j;
				while (j < s.size() && isdigit((unsigned char) s[j]))
					++j;
			}
			while (j < s.size() && s[j] && strchr("hlLqjzt", s[j]))
				++j;
			if (j >= s.size() || !s[j] || !strchr("diouxXeEfgGcs", s[j]))
				return false;
			if (!pieces.empty() && piece.empty())
				return false;
			pieces.push_back(piece);
			piece.clear();
			conv += s[j];
			i = j;
		}
		pieces.push_back(piece);
		return true;
	}

	static void AddTemplate(SLanguage& lang, const std::string& src, const std::string& dst)
	{
		STemplate t;
		std::string dstConv;
		if (!Pieces(src, t.src, t.conv) || !Pieces(dst, t.dst, dstConv) || t.conv.empty() || t.src.size() != t.dst.size())
			return;
		t.literal = 0;
		for (size_t i = 0; i < t.src.size(); ++i)
			for (size_t k = 0; k < t.src[i].size(); ++k)
				if (!isspace((unsigned char) t.src[i][k]))
					++t.literal;
		// A template of little but values would find any text.
		if (t.literal < 4)
			return;
		std::unordered_map<std::string, size_t>::iterator it = lang.templateOf.find(src);
		if (it != lang.templateOf.end())
		{
			lang.templates[it->second] = t;
			return;
		}
		lang.templateOf[src] = lang.templates.size();
		lang.templates.push_back(t);
	}

	static void AddPair(SLanguage& lang, const std::string& src, const std::string& dst, bool lines)
	{
		if (src.empty() || dst.empty())
			return;
		int nSrc = 0, nDst = 0;
		const std::string sigSrc = Conversions(src, nSrc);
		const std::string sigDst = Conversions(dst, nDst);
		SEntry e;
		e.text = dst;
		e.format = sigSrc == sigDst && sigSrc.find('?') == std::string::npos;
		if (!e.format && nSrc > 0 && sigSrc.find('?') == std::string::npos)
			++lang.dropped;	// a Polish format whose translation has other conversions: a text, never a format
		lang.exact[src] = e;
		++lang.texts;
		if (e.format && nSrc > 0)
			AddTemplate(lang, src, dst);
		// A text of several lines (GF's [ENTER]) also line by line: notice_multiline and say_split hand out lines.
		if (lines && src.find("[ENTER]") != std::string::npos)
		{
			std::vector<std::string> a, b;
			for (int k = 0; k < 2; ++k)
			{
				const std::string& s = k ? dst : src;
				std::vector<std::string>& v = k ? b : a;
				size_t start = 0;
				for (;;)
				{
					const size_t p = s.find("[ENTER]", start);
					v.push_back(s.substr(start, p == std::string::npos ? std::string::npos : p - start));
					if (p == std::string::npos)
						break;
					start = p + 7;
				}
			}
			if (a.size() == b.size())
			{
				for (size_t i = 0; i < a.size(); ++i)
				{
					size_t visible = 0;
					for (size_t k = 0; k < a[i].size(); ++k)
						if (!isspace((unsigned char) a[i][k]))
							++visible;
					if (visible >= 4 && !b[i].empty() && lang.exact.find(a[i]) == lang.exact.end())
						AddPair(lang, a[i], b[i], false);
				}
			}
		}
	}

	static void LoadFile(SLanguage& lang, const std::string& path, const std::string& name)
	{
		std::vector<std::string> lines;
		if (!ReadLines(path, lines))
			return;
		++lang.files;
		const bool items = name == "item_names.tsv";
		const bool mobs = name == "mob_names.tsv";
		const bool fragments = name.find("fragment") != std::string::npos;
		for (size_t i = 0; i < lines.size(); ++i)
		{
			const std::string& line = lines[i];
			if (line.empty() || line[0] == '#')
				continue;
			const size_t tab = line.find('\t');
			if (tab == std::string::npos || tab == 0)
				continue;
			std::string a = line.substr(0, tab);
			std::string b = line.substr(tab + 1);
			if (items || mobs)
			{
				const size_t tab2 = b.find('\t');
				if (tab2 != std::string::npos)
					b.erase(tab2);
				DWORD vnum = 0;
				if (!str_to_number(vnum, a.c_str()) || !vnum || b.empty())
					continue;
				(items ? lang.items : lang.mobs)[vnum] = FromUtf8(Unescape(b), lang.codePage);
				continue;
			}
			if (fragments)
			{
				const std::string src = FromUtf8(Unescape(a), 1250);
				size_t visible = 0;
				for (size_t k = 0; k < src.size(); ++k)
					if (!isspace((unsigned char) src[k]))
						++visible;
				if (visible >= 5 && src.find('%') == std::string::npos)
					lang.fragments.push_back(std::make_pair(src, FromUtf8(Unescape(b), lang.codePage)));
				continue;
			}
			AddPair(lang, FromUtf8(Unescape(a), 1250), FromUtf8(Unescape(b), lang.codePage), true);
		}
	}

	static SLanguage& Get(const std::string& code)
	{
		SLanguage& lang = s_languages[code];
		if (lang.loaded)
			return lang;
		lang.loaded = true;
		lang.codePage = DefaultCodePage(code);
		lang.fallback = code == ENGLISH ? "" : ENGLISH;
		const std::string dir = LanguageDir() + "/" + code;
		std::vector<std::string> cfg;
		if (ReadLines(dir + "/language.cfg", cfg))
		{
			for (size_t i = 0; i < cfg.size(); ++i)
			{
				char key[64] = {0}, value[64] = {0};
				if (sscanf(cfg[i].c_str(), "%63s %63s", key, value) != 2 || key[0] == '#')
					continue;
				if (!strcmp(key, "codepage"))
					str_to_number(lang.codePage, value);
				else if (!strcmp(key, "fallback"))
					lang.fallback = !strcmp(value, "none") || !strcmp(value, POLISH) ? "" : Normalize(value);
			}
		}
		if (lang.fallback == code)
			lang.fallback.clear();
		std::vector<std::string> names;
		if (DIR* d = opendir(dir.c_str()))
		{
			while (dirent* de = readdir(d))
			{
				const std::string n = de->d_name;
				if (n.size() > 4 && n.compare(n.size() - 4, 4, ".tsv") == 0)
					names.push_back(n);
			}
			closedir(d);
		}
		// Sorted: a later file overrides an earlier one (zz_*.tsv for the hand fixes).
		std::sort(names.begin(), names.end());
		for (size_t i = 0; i < names.size(); ++i)
			LoadFile(lang, dir + "/" + names[i], names[i]);
		for (size_t i = 0; i < lang.templates.size(); ++i)
		{
			const std::string& first = lang.templates[i].src[0];
			if (first.size() >= 2)
				lang.buckets[first.substr(0, 2)].push_back(i);
			else
				lang.generic.push_back(i);
		}
		struct FMoreLiteral
		{
			const std::vector<STemplate>* t;
			bool operator()(size_t a, size_t b) const { return (*t)[a].literal > (*t)[b].literal; }
		} more = { &lang.templates };
		for (std::unordered_map<std::string, std::vector<size_t> >::iterator it = lang.buckets.begin(); it != lang.buckets.end(); ++it)
			std::stable_sort(it->second.begin(), it->second.end(), more);
		std::stable_sort(lang.generic.begin(), lang.generic.end(), more);
		for (size_t i = 0; i < lang.fragments.size(); ++i)
			lang.fragmentBuckets[lang.fragments[i].first.substr(0, 2)].push_back(i);
		struct FLonger
		{
			const std::vector<std::pair<std::string, std::string> >* f;
			bool operator()(size_t a, size_t b) const { return (*f)[a].first.size() > (*f)[b].first.size(); }
		} longer = { &lang.fragments };
		for (std::unordered_map<std::string, std::vector<size_t> >::iterator it = lang.fragmentBuckets.begin(); it != lang.fragmentBuckets.end(); ++it)
			std::stable_sort(it->second.begin(), it->second.end(), longer);
		sys_log(0, "MT2009_LANGUAGE: %s - %u file(s), %u text(s), %u template(s), %u fragment(s), %u item and %u monster name(s), "
				"%u format(s) whose translation has other conversions, code page %d, fallback %s",
				code.c_str(), (unsigned) lang.files, (unsigned) lang.exact.size(), (unsigned) lang.templates.size(), (unsigned) lang.fragments.size(),
				(unsigned) lang.items.size(), (unsigned) lang.mobs.size(), (unsigned) lang.dropped, lang.codePage,
				lang.fallback.empty() ? "-" : lang.fallback.c_str());
		return lang;
	}

	static bool ValidValue(char conv, const std::string& v)
	{
		switch (conv)
		{
			case 's':
				return true;
			case 'c':
				return v.size() == 1;
			case 'd':
			case 'i':
			case 'u':
			case 'o':
			{
				if (v.empty())
					return false;
				size_t i = (v[0] == '-' || v[0] == '+') ? 1 : 0;
				if (i >= v.size())
					return false;
				for (; i < v.size(); ++i)
					if (!isdigit((unsigned char) v[i]))
						return false;
				return true;
			}
			case 'x':
			case 'X':
			{
				if (v.empty())
					return false;
				for (size_t i = 0; i < v.size(); ++i)
					if (!isxdigit((unsigned char) v[i]))
						return false;
				return true;
			}
			default:
			{
				if (v.empty())
					return false;
				for (size_t i = 0; i < v.size(); ++i)
					if (!strchr("0123456789+-.eE", v[i]))
						return false;
				return true;
			}
		}
	}

	static bool MatchRest(const STemplate& t, size_t i, const std::string& text, size_t pos, std::vector<std::string>& caps)
	{
		const std::string& lit = t.src[i];
		const char conv = t.conv[i - 1];
		if (i + 1 == t.src.size())
		{
			if (text.size() < pos + lit.size())
				return false;
			const size_t end = text.size() - lit.size();
			if (text.compare(end, lit.size(), lit) != 0)
				return false;
			const std::string v = text.substr(pos, end - pos);
			if (!ValidValue(conv, v))
				return false;
			caps.push_back(v);
			return true;
		}
		size_t from = pos;
		while ((from = text.find(lit, from)) != std::string::npos)
		{
			const std::string v = text.substr(pos, from - pos);
			if (ValidValue(conv, v))
			{
				caps.push_back(v);
				if (MatchRest(t, i + 1, text, from + lit.size(), caps))
					return true;
				caps.pop_back();
			}
			++from;
		}
		return false;
	}

	static bool Match(const STemplate& t, const std::string& text, std::vector<std::string>& caps)
	{
		caps.clear();
		if (text.compare(0, t.src[0].size(), t.src[0]) != 0)
			return false;
		return MatchRest(t, 1, text, t.src[0].size(), caps);
	}

	static bool TryLanguage(SLanguage& lang, const std::string& text, std::string& out, bool templates)
	{
		std::unordered_map<std::string, SEntry>::const_iterator it = lang.exact.find(text);
		if (it != lang.exact.end())
		{
			out = it->second.text;
			return true;
		}
		if (!templates || lang.templates.empty())
			return false;
		std::vector<std::string> caps;
		for (int pass = 0; pass < 2; ++pass)
		{
			const std::vector<size_t>* list = &lang.generic;
			if (pass == 0)
			{
				if (text.size() < 2)
					continue;
				std::unordered_map<std::string, std::vector<size_t> >::const_iterator b = lang.buckets.find(text.substr(0, 2));
				if (b == lang.buckets.end())
					continue;
				list = &b->second;
			}
			for (size_t k = 0; k < list->size(); ++k)
			{
				const STemplate& t = lang.templates[(*list)[k]];
				if (!Match(t, text, caps))
					continue;
				out = t.dst[0];
				for (size_t i = 0; i < caps.size(); ++i)
				{
					// A value that is a text of its own (an empire's, an item's name) in the language too.
					std::unordered_map<std::string, SEntry>::const_iterator v = t.conv[i] == 's' && caps[i].size() >= 2 ? lang.exact.find(caps[i]) : lang.exact.end();
					out += v != lang.exact.end() ? v->second.text : caps[i];
					out += t.dst[i + 1];
				}
				return true;
			}
		}
		return false;
	}

	// The known pieces of a glued line replaced, each where it stands (one pass: a translation is never looked at again).
	static bool TryFragments(SLanguage& lang, const std::string& text, std::string& out)
	{
		if (lang.fragments.empty() || text.size() < 5)
			return false;
		std::string res;
		res.reserve(text.size() + 32);
		bool any = false;
		size_t i = 0;
		while (i < text.size())
		{
			bool hit = false;
			if (i + 1 < text.size())
			{
				std::unordered_map<std::string, std::vector<size_t> >::const_iterator b = lang.fragmentBuckets.find(text.substr(i, 2));
				if (b != lang.fragmentBuckets.end())
				{
					for (size_t k = 0; k < b->second.size(); ++k)
					{
						const std::pair<std::string, std::string>& f = lang.fragments[b->second[k]];
						if (text.compare(i, f.first.size(), f.first) == 0)
						{
							res += f.second;
							i += f.first.size();
							hit = any = true;
							break;
						}
					}
				}
			}
			if (!hit)
				res += text[i++];
		}
		if (any)
			out.swap(res);
		return any;
	}

	static bool Find(const char* code, const std::string& text, std::string& out)
	{
		if (IsPolish(code) || text.empty())
			return false;
		SLanguage& lang = Get(code);
		if (TryLanguage(lang, text, out, true))
			return true;
		SLanguage* fb = lang.fallback.empty() ? NULL : &Get(lang.fallback);
		if (fb && TryLanguage(*fb, text, out, true))
			return true;
		if (TryFragments(lang, text, out))
			return true;
		if (fb && TryFragments(*fb, text, out))
			return true;
		return false;
	}

	// A Polish format's translation usable as a format in its place (the same conversions), or NULL.
	static const char* FindFormat(const char* code, const char* format)
	{
		SLanguage& lang = Get(code);
		std::unordered_map<std::string, SEntry>::const_iterator it = lang.exact.find(format);
		if (it != lang.exact.end())
			return it->second.format ? it->second.text.c_str() : NULL;
		if (!lang.fallback.empty())
		{
			SLanguage& fb = Get(lang.fallback);
			it = fb.exact.find(format);
			if (it != fb.exact.end() && it->second.format)
				return it->second.text.c_str();
		}
		return NULL;
	}

	static bool Translatable(unsigned char type)
	{
		switch (type)
		{
			case CHAT_TYPE_TALKING:
			case CHAT_TYPE_INFO:
			case CHAT_TYPE_NOTICE:
			case CHAT_TYPE_BIG_NOTICE:
#ifdef ENABLE_DICE_SYSTEM
			case CHAT_TYPE_DICE_INFO:
#endif
			case CHAT_TYPE_FANCY_NOTICE:
#ifdef ENABLE_12ZI
			case CHAT_TYPE_MISSION:
			case CHAT_TYPE_SUB_MISSION:
			case CHAT_TYPE_CLEAR_MISSION:
#endif
				return true;
			default:
				return false;
		}
	}

	static const char* NameIn(const char* code, unsigned int vnum, bool items)
	{
		if (IsPolish(code))
			return NULL;
		SLanguage& lang = Get(code);
		std::unordered_map<DWORD, std::string>& names = items ? lang.items : lang.mobs;
		std::unordered_map<DWORD, std::string>::const_iterator it = names.find(vnum);
		if (it != names.end())
			return it->second.c_str();
		if (!lang.fallback.empty())
		{
			SLanguage& fb = Get(lang.fallback);
			std::unordered_map<DWORD, std::string>& fbNames = items ? fb.items : fb.mobs;
			it = fbNames.find(vnum);
			if (it != fbNames.end())
				return it->second.c_str();
		}
		return NULL;
	}

	static std::string AvailableList()
	{
		Scan();
		std::string s = POLISH;
		for (size_t i = 0; i < s_available.size(); ++i)
		{
			s += ' ';
			s += s_available[i];
		}
		return s;
	}
}

using namespace mt2009_language;

const char* GetPlayerLanguage(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return POLISH;
	std::unordered_map<DWORD, std::string>::const_iterator it = s_playerLanguage.find(ch->GetPlayerID());
	return it == s_playerLanguage.end() ? POLISH : it->second.c_str();
}

void SetPlayerLanguage(LPCHARACTER ch, const char* code)
{
	if (!ch || !ch->IsPC())
		return;
	const std::string lang = Normalize(code);
	if (lang.empty())
		return;
	const DWORD pid = ch->GetPlayerID();
	const std::string before = GetPlayerLanguage(ch);
	if (lang == POLISH)
		s_playerLanguage.erase(pid);
	else
		s_playerLanguage[pid] = lang;
	if (before != lang && s_dbColumn)
		DBManager::instance().Query("UPDATE player%s SET language = '%s' WHERE id = %u", get_table_postfix(), lang.c_str(), pid);
}

void Mt2009LanguageOnEnterGame(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot() || !s_dbColumn)
		return;
	const DWORD pid = ch->GetPlayerID();
	std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery("SELECT language FROM player%s WHERE id = %u", get_table_postfix(), pid));
	if (!msg || msg->uiSQLErrno != 0)
	{
		if (msg && msg->uiSQLErrno == 1054)
		{
			// The migration (language.sql) has not run: Polish for all, no more questions.
			s_dbColumn = false;
			sys_err("MT2009_LANGUAGE: player.language is missing (language.sql) - languages are not kept");
		}
		return;
	}
	SQLResult* res = msg->Get();
	MYSQL_ROW row = res && res->uiNumRows > 0 ? mysql_fetch_row(res->pSQLResult) : NULL;
	const std::string lang = row && row[0] ? Normalize(row[0]) : std::string();
	if (lang.empty() || lang == POLISH)
		s_playerLanguage.erase(pid);
	else
		s_playerLanguage[pid] = lang;
}

const char* Mt2009Translate(const char* lang, const char* polish)
{
	static std::string s_out;
	if (!polish || !*polish || IsPolish(lang))
		return polish;
	if (Find(lang, polish, s_out))
		return s_out.c_str();
	return polish;
}

const char* Mt2009TranslateFor(LPCHARACTER ch, const char* polish)
{
	return Mt2009Translate(GetPlayerLanguage(ch), polish);
}

const char* Mt2009LcTextFor(LPCHARACTER ch, const char* key)
{
	return Mt2009TranslateFor(ch, LC_TEXT(key));
}

const char* Mt2009ItemNameIn(const char* lang, unsigned int vnum)
{
	return NameIn(lang, vnum, true);
}

const char* Mt2009MobNameIn(const char* lang, unsigned int vnum)
{
	return NameIn(lang, vnum, false);
}

const char* Mt2009LanguageChatFormat(LPCHARACTER ch, unsigned char type, const char* format)
{
	if (!format || !Translatable(type))
		return format;
	const char* lang = GetPlayerLanguage(ch);
	if (IsPolish(lang) || !strcmp(format, "%s"))
		return format;
	const char* translated = FindFormat(lang, format);
	return translated ? translated : format;
}

int Mt2009LanguageChatResult(LPCHARACTER ch, unsigned char type, bool formatTranslated, char* buf, size_t size, int len)
{
	if (len < 0)
		len = 0;
	if ((size_t) len >= size)
		len = (int) strlen(buf);
	if (formatTranslated || !Translatable(type))
		return len;
	const char* lang = GetPlayerLanguage(ch);
	if (IsPolish(lang) || !len)
		return len;
	std::string out;
	if (!Find(lang, std::string(buf, len), out))
		return len;
	strlcpy(buf, out.c_str(), size);
	return (int) strlen(buf);
}

void Mt2009LanguageCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch)
		return;
	char arg[32];
	one_argument(argument, arg, sizeof(arg));
	if (!*arg)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "lang: %s (%s)", GetPlayerLanguage(ch), AvailableList().c_str());
		return;
	}
	if (!strcmp(arg, "reload") && ch->GetGMLevel() >= GM_IMPLEMENTOR)
	{
		s_languages.clear();
		s_scanned = false;
		ch->ChatPacket(CHAT_TYPE_INFO, "lang: dictionaries reloaded (%s)", AvailableList().c_str());
		return;
	}
	SetPlayerLanguage(ch, arg);
}

namespace quest
{
	// pc.get_language() - the code of the language the quest's character reads ("pl" for nobody).
	static int pc_get_language(lua_State* L)
	{
		lua_pushstring(L, GetPlayerLanguage(CQuestManager::instance().GetCurrentCharacterPtr()));
		return 1;
	}

	// pc.set_language(code)
	static int pc_set_language(lua_State* L)
	{
		if (lua_type(L, 1) == LUA_TSTRING)
			SetPlayerLanguage(CQuestManager::instance().GetCurrentCharacterPtr(), lua_tostring(L, 1));
		return 0;
	}

	// mt2009_tr(text[, code]) - a Polish text in the language of the quest's character (or `code`); anything that is
	// not a string comes back as it is.
	static int mt2009_tr(lua_State* L)
	{
		if (lua_type(L, 1) != LUA_TSTRING)
		{
			lua_pushvalue(L, 1);
			return 1;
		}
		const char* lang = lua_type(L, 2) == LUA_TSTRING ? lua_tostring(L, 2) : GetPlayerLanguage(CQuestManager::instance().GetCurrentCharacterPtr());
		lua_pushstring(L, Mt2009Translate(lang, lua_tostring(L, 1)));
		return 1;
	}

	static int PushName(lua_State* L, bool items)
	{
		const char* lang = lua_type(L, 2) == LUA_TSTRING ? lua_tostring(L, 2) : GetPlayerLanguage(CQuestManager::instance().GetCurrentCharacterPtr());
		const char* name = lua_isnumber(L, 1) ? NameIn(lang, (unsigned int) lua_tonumber(L, 1), items) : NULL;
		if (name)
			lua_pushstring(L, name);
		else
			lua_pushnil(L);
		return 1;
	}

	// mt2009_item_name(vnum[, code]) / mt2009_mob_name(vnum[, code]) - the name in the reader's language, nil without one.
	static int mt2009_item_name(lua_State* L)
	{
		return PushName(L, true);
	}

	static int mt2009_mob_name(lua_State* L)
	{
		return PushName(L, false);
	}

	// mt2009_languages() - { "pl", "de", "en", ... }: Polish and every language with a folder in lang/.
	static int mt2009_languages(lua_State* L)
	{
		Scan();
		lua_newtable(L);
		lua_pushstring(L, POLISH);
		lua_rawseti(L, -2, 1);
		for (size_t i = 0; i < s_available.size(); ++i)
		{
			lua_pushstring(L, s_available[i].c_str());
			lua_rawseti(L, -2, (int) i + 2);
		}
		return 1;
	}

	// questlua.cpp (MT2009_PLUS_LANGUAGE_V1 (lua)), after the pc table is made.
	void RegisterMt2009LanguageFunctions()
	{
		lua_State* L = CQuestManager::instance().GetLuaState();
		lua_getglobal(L, "pc");
		if (lua_istable(L, -1))
		{
			lua_pushstring(L, "get_language");
			lua_pushcfunction(L, pc_get_language);
			lua_rawset(L, -3);
			lua_pushstring(L, "set_language");
			lua_pushcfunction(L, pc_set_language);
			lua_rawset(L, -3);
		}
		else
			sys_err("MT2009_LANGUAGE: the quest table pc does not exist");
		lua_pop(L, 1);
		lua_register(L, "mt2009_tr", mt2009_tr);
		lua_register(L, "mt2009_item_name", mt2009_item_name);
		lua_register(L, "mt2009_mob_name", mt2009_mob_name);
		lua_register(L, "mt2009_languages", mt2009_languages);
	}

	// questlua.cpp (MT2009_PLUS_LANGUAGE_V1 (lua load)): quest/mt2009_language.lua, after locale.lua - the quests' texts
	// in the reader's language (it wraps say, select and the rest). Not there or broken: the quests speak Polish.
	void LoadMt2009LanguageLua(lua_State* L)
	{
		const std::string path = g_stQuestDir + "/mt2009_language.lua";
		if (access(path.c_str(), R_OK) != 0)
		{
			sys_log(0, "MT2009_LANGUAGE: no %s", path.c_str());
			return;
		}
		const int ret = lua_dofile(L, path.c_str());
		if (ret != 0)
			sys_err("MT2009_LANGUAGE: %s returns %d", path.c_str(), ret);
		else
			sys_log(0, "MT2009_LANGUAGE: %s loaded", path.c_str());
	}
}
