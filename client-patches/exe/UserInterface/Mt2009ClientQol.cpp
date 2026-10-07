// ---------------------------------------------------------------------------------------------
// MT2009_PLUS_DIGI_CLIENT_QOL_V1 - "Opcje dodatkowe" (Autor: Digi Rasta; nowy-system 0.19.0 / 0.28,
// his "Biore" small client systems). Our own code: his notes (DOKUMENTACJA/biore.md) say the packages
// behind these ideas (Hide-Objects among them) are GPL, so nothing of theirs is copied - only the
// effect file names (data) and the hooks' places. Python (root/uiopcjedodatkowe.py) checks hasattr:
//   app.SetHideEffects(buff, skill)  hides the shaman's buff effects / the skill auras
//                                     (EffectLib CEffectInstance::OnRender asks Mt2009DigiQol_IsEffectHidden)
//   app.SetChatLog(on)               chat and whispers to logs/czat_YYYY-MM-DD.txt (PythonChat.cpp)
//   chrmgr.SetShopsVisible(on)       player shops hidden/shown: the ikashop entities
//                                     (CPythonIkarusShop::RenderEntities) and shop characters (IsShop)
// ---------------------------------------------------------------------------------------------
#include "StdAfx.h"
#include "../EffectLib/EffectData.h"
#include "PythonCharacterManager.h"
#include "InstanceBase.h"

#include <cctype>
#include <ctime>
#include <map>
#include <string>

namespace
{
	enum { QOL_EFFECT_NONE, QOL_EFFECT_BUFF, QOL_EFFECT_SKILL };

	bool s_bHideBuff = false;
	bool s_bHideSkill = false;
	bool s_bChatLog = false;
	bool s_bShopsHidden = false;

	// effect kind by file name (effect data may be loaded again at another address)
	std::map<std::string, int> s_mapEffectKind;

#ifdef ENABLE_DIGI_CLIENT_QOL
	// The shaman's buffs on a character, and the skill auras of the warrior, sura, ninja and shaman.
	const char* const c_aszBuffEffects[] =
	{
		"pc/shaman/effect/3hosin_loop.mse",
		"pc/shaman/effect/boho_loop.mse",
		"pc/shaman/effect/6gicheon_hand.mse",
		"pc/shaman/effect/jeungryeok_hand.mse",
	};
	const char* const c_aszSkillEffects[] =
	{
		"pc/shaman/effect/10kwaesok_loop.mse",
		"pc/sura/effect/gwigeom_loop.mse",
		"pc/sura/effect/fear_loop.mse",
		"pc/sura/effect/jumagap_loop.mse",
		"pc/sura/effect/muyeong_loop.mse",
		"pc/sura/effect/heuksin_loop.mse",
		"pc/warrior/effect/gyeokgongjang_loop.mse",
		"pc/warrior/effect/geom_sword_loop.mse",
		"pc/assassin/effect/gyeonggong_loop.mse",
	};

	bool HasSuffix(const std::string& s, const char* c_szSuffix)
	{
		const size_t n = strlen(c_szSuffix);
		return s.size() >= n && s.compare(s.size() - n, n, c_szSuffix) == 0;
	}

	bool InList(const std::string& name, const char* const* list, size_t count)
	{
		for (size_t i = 0; i < count; ++i)
			if (HasSuffix(name, list[i]))
				return true;
		return false;
	}

	int EffectKindOf(const CEffectData* c_pData)
	{
		const std::string name = c_pData->GetFileName() ? c_pData->GetFileName() : "";
		std::map<std::string, int>::const_iterator it = s_mapEffectKind.find(name);
		if (it != s_mapEffectKind.end())
			return it->second;

		std::string low(name);
		for (size_t i = 0; i < low.size(); ++i)
			low[i] = low[i] == '\\' ? '/' : (char) tolower((unsigned char) low[i]);

		int kind = QOL_EFFECT_NONE;
		if (InList(low, c_aszBuffEffects, _countof(c_aszBuffEffects)))
			kind = QOL_EFFECT_BUFF;
		else if (InList(low, c_aszSkillEffects, _countof(c_aszSkillEffects)))
			kind = QOL_EFFECT_SKILL;
		s_mapEffectKind[name] = kind;
		return kind;
	}

	// A chat line carries colour and link codes (|cAARRGGBB, |r, |H...|h, |h); the log gets the text.
	std::string PlainChatText(const char* c_szText)
	{
		std::string out;
		const char* p = c_szText;
		while (*p)
		{
			if (p[0] == '|')
			{
				if (p[1] == 'c' && strlen(p) >= 10) { p += 10; continue; }
				if (p[1] == 'r' || p[1] == 'h') { p += 2; continue; }
				if (p[1] == 'H')
				{
					const char* e = strstr(p, "|h");
					p = e ? e + 2 : p + 2;
					continue;
				}
			}
			out += *p++;
		}
		return out;
	}
#endif
}

// EffectLib (CEffectInstance::OnRender) declares this where it calls it; without the define it never hides.
bool Mt2009DigiQol_IsEffectHidden(const CEffectData* c_pData)
{
#ifdef ENABLE_DIGI_CLIENT_QOL
	if (!c_pData || (!s_bHideBuff && !s_bHideSkill))
		return false;
	const int kind = EffectKindOf(c_pData);
	return (kind == QOL_EFFECT_BUFF && s_bHideBuff) || (kind == QOL_EFFECT_SKILL && s_bHideSkill);
#else
	return false;
#endif
}

#ifdef ENABLE_DIGI_CLIENT_QOL
// CPythonIkarusShop::RenderEntities: hidden ikashop entities are drawn as if out of range.
bool Mt2009DigiQol_ShopsHidden()
{
	return s_bShopsHidden;
}

// CPythonChat::AppendChat (name NULL) and AppendWhisper.
void Mt2009DigiQol_OnChat(const char* c_szName, const char* c_szChat)
{
	if (!s_bChatLog || !c_szChat || !*c_szChat)
		return;

	CreateDirectoryA("logs", NULL);
	const time_t now = time(NULL);
	const struct tm lt = *localtime(&now);
	char szFile[64];
	strftime(szFile, sizeof(szFile), "logs/czat_%Y-%m-%d.txt", &lt);
	FILE* fp = fopen(szFile, "ab");
	if (!fp)
		return;
	char szTime[16];
	strftime(szTime, sizeof(szTime), "%H:%M:%S", &lt);
	const std::string text = PlainChatText(c_szChat);
	if (c_szName)
		fprintf(fp, "[%s] [szept: %s] %s\r\n", szTime, c_szName, text.c_str());
	else
		fprintf(fp, "[%s] %s\r\n", szTime, text.c_str());
	fclose(fp);
}

static PyObject* qolAppSetHideEffects(PyObject* poSelf, PyObject* poArgs)
{
	int iBuff, iSkill;
	if (!PyTuple_GetInteger(poArgs, 0, &iBuff) || !PyTuple_GetInteger(poArgs, 1, &iSkill))
		return Py_BuildException();
	s_bHideBuff = iBuff != 0;
	s_bHideSkill = iSkill != 0;
	return Py_BuildNone();
}

static PyObject* qolAppSetChatLog(PyObject* poSelf, PyObject* poArgs)
{
	int iOn;
	if (!PyTuple_GetInteger(poArgs, 0, &iOn))
		return Py_BuildException();
	s_bChatLog = iOn != 0;
	return Py_BuildNone();
}

// Python calls it once a second while the shops are hidden, so shop characters that came into
// view are hidden too; shown again once.
static PyObject* qolChrmgrSetShopsVisible(PyObject* poSelf, PyObject* poArgs)
{
	int iVisible;
	if (!PyTuple_GetInteger(poArgs, 0, &iVisible))
		return Py_BuildException();

	s_bShopsHidden = iVisible == 0;

	CPythonCharacterManager& rkChrMgr = CPythonCharacterManager::Instance();
	CInstanceBase* pkMain = rkChrMgr.GetMainInstancePtr();
	for (CPythonCharacterManager::CharacterIterator it = rkChrMgr.CharacterInstanceBegin(); it != rkChrMgr.CharacterInstanceEnd(); ++it)
	{
		CInstanceBase* pkInst = *it;
		if (!pkInst || pkInst == pkMain || !pkInst->IsShop())
			continue;
		if (iVisible)
			pkInst->Show();
		else
			pkInst->Hide();
	}
	return Py_BuildNone();
}

static void Mt2009DigiQol_AddFunctions(const char* c_szModule, PyMethodDef* pMethods)
{
	PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed; the module's own init adds to it later
	if (!poModule)
		return;
	for (PyMethodDef* p = pMethods; p->ml_name; ++p)
		PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
}

// UserInterface.cpp (RunMainScript's module init) declares this where it calls it.
void Mt2009DigiQol_RegisterPython()
{
	static PyMethodDef s_appMethods[] =
	{
		{ "SetHideEffects",		qolAppSetHideEffects,		METH_VARARGS, NULL },
		{ "SetChatLog",			qolAppSetChatLog,			METH_VARARGS, NULL },
		{ NULL, NULL, 0, NULL },
	};
	static PyMethodDef s_chrmgrMethods[] =
	{
		{ "SetShopsVisible",	qolChrmgrSetShopsVisible,	METH_VARARGS, NULL },
		{ NULL, NULL, 0, NULL },
	};
	Mt2009DigiQol_AddFunctions("app", s_appMethods);
	Mt2009DigiQol_AddFunctions("chrmgr", s_chrmgrMethods);
}
#endif
