#pragma once

// MT2009_PLUS_ZODIAC_V1 (Autor: Digi Rasta): Swiatynia Zodiaku - GC 220 and the server's Zodiac SE_* ids,
// chrmgr.IsDead / IsPC, the constants of the Zodiac scripts (Mt2009Zodiak.cpp).
void Mt2009Zodiak_RegisterPython();

// SE_* of the special effect packets -> CInstanceBase::EFFECT_*, (DWORD)-1 when it is not a Zodiac effect
DWORD Mt2009Zodiak_EffectFromSE(BYTE bType);
