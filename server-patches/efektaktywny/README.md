# efektaktywny – „Ten efekt jest już aktywny.” najwyżej raz na minutę (Yohara 3.x)

Znacznik: `MT2009_PLUS_EFFECT_ACTIVE_QUIET_V1` (zgłoszenie właściciela 4.11.2026: czat zalany komunikatem przy
Auto Łowach). Auto Łowy klienta (do łatki klienta: `MT2009_PLUS_AUTOHUNT_SPECIAL_AFFECT_V1` w `uiautohunt.py`) używały
przedmiotu co kilka sekund, mimo że jego efekt trwał; serwer każdą odmowę wypisywał na czacie.

## Haki (2, `char_item.cpp`)
- **nog** – Grzaniec 50216 (`ITEM_NOG_POCKET`) przy trwającym `AFFECT_NOG_ABILITY`: „This effect is already activated.”
- **cz** – Znak Strażnika 72328 (`ENABLE_12ZI`) przy trwającym `AFFECT_CZ_UNLIMIT_ENTER`: „The effect is already active.”

Odmowa zostaje (przedmiot nie znika), tylko komunikat przychodzi najwyżej raz na 60 s na postać (mapa PID → czas).
`gen_edits.py` → `edits.json`, `apply_efektaktywny.py` / `Apply-EfektAktywnyPatch.ps1`. Kolejność: dowolna (na końcu).
