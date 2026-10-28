# elecglove – efekt błyskawic rękawic (bonus 6/7)

Znacznik: `MT2009_PLUS_ELEC_GLOVE_V1`. Właściciel (28.10.2026): „efekt do bonusu ataku błyskawicami w rękawicach
(6/7)” – poradnik z forum (`ENABLE_GLOVE_ELEC_ATTACK_BONUS`: `APPLY/POINT_HIT_AREA_ELEC_ATTACK`, `SE_ELEC_ATTACK_HIT`,
odnowienie na postać, uderzenie w `battle_hit`).

## Co już było

Bonus działał od `MT2009_PLUS_BONUS67_V1` (`server-patches/bonusy67`): punkt i typ bonusu **`POINT_GLOVE_LIGHTNING`
(242)**, pula rękawic (`bonusy67_wiki.sql`: waga 18, poziomy 1/1/1/1/1, tylko kolumna `glove`), nazwa w dymku
(`root/localeinfo_point.py`: „Atakuj potwory w pobliżu błyskawicami (regeneracja 15 sek.)”), boty (`GLOVE67_WANTED`
w `playerbot_shop_aids.h`). Działanie (`playerbot_bonus67.cpp`, `GloveLightning` z `Bonus67Damage`): zwykły cios gracza
w potwora/NPC – do 8 potworów w promieniu `b67_lightning_range` (6 m, maks. 30 m) dostaje te same obrażenia, raz na
15 s (odnowienie na postać, `TState::dwLightningReady`), bez szansy – jak wiki („obrażenia auto-ataku”, „15 sek.”,
linia bez wartości). Brakowało tylko efektu trafienia – widać było sam lecący pocisk `FLY_CHAIN_LIGHTNING`.

Dlatego **bez nowego APPLY/POINT** (numery poradnika = nasz 242) i bez drugiego uderzenia w `battle_hit`.

## Serwer

| Plik | Zmiana |
|---|---|
| `common/length.h` | `(SE)`: `SE_ELEC_ATTACK_HIT` (**54**, po efektach Zodiaku 39–53) i `#define MT2009_PLUS_ELEC_GLOVE_SE` |
| `playerbot_bonus67.cpp` (overlay) | każdy trafiony potwór: `EffectPacket(SE_ELEC_ATTACK_HIT)` obok `CreateFly(FLY_CHAIN_LIGHTNING)`; `static_assert` 54 |

1 edycja (`edits.json`), **ostatnia** w kolejności `yohara-deploy.sh`. Linux/VPS: `python3 apply_elecglove.py <game/src>`;
Windows: `Apply-ElecGlovePatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). db bez zmian.

## Klient

- exe (`client-patches/exe`, `ENABLE_GLOVE_ELEC_ATTACK_BONUS` w `Locale_inc.h`): `SE_ELEC_ATTACK_HIT` w
  `Server/common/length.h`, `CInstanceBase::EFFECT_ELEC_ATTACK_HIT`, rejestracja w `PythonPlayerSettingsModule.cpp`
  (`d:/ymir work/effect/hit/blow_electric/6th7th_attributes_blow.mse`), `case SE_ELEC_ATTACK_HIT` w
  `PythonNetworkStreamPhaseGameItem.cpp`, `chrmgr.EFFECT_ELEC_ATTACK_HIT`.
- Plik efektu: globalny `6th7th_attributes_blow.mse` (klient GF 26.1.11) + `3.dds` – nowa paczka `elecglove`
  (`client-2.0.30/tools/elecglove`); 4–6.dds są w `hydra_mobs`, `impact3.dds` w `gf_razador`, `smoke_dust.dds` w `az_mobs3`.
- Stary exe dostaje nieznany efekt 54: tylko wpis w syserr („is not a special effect number”), gra działa.
- Okno bonusów (`uiattributelist.py`): punkt 242 ≥ 198 (exe `POINT_MAX_NUM`), serwer go nie wysyła – bez nowej linii.
