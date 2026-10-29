# dmgprint – Damage Print Improve (unoszące się liczby obrażeń)

Znacznik: `MT2009_PLUS_DAMAGE_PRINT_V1`. Właściciel (29.10.2026): „systemy, które zmieniają grę wizualnie – dodaj do
Yohary”. Paczka „Damage Print Improve v26.0.5” (`cache/yohara/dmgprint-src`, bez readme/autora w paczce).

## Co robi

Liczby obrażeń jak w nowym kliencie: niżej na postaci (¼ wysokości, przy górnej krawędzi ekranu – u stóp), rysowane
po całym świecie bez testu głębokości (nie chowają się za terenem/obiektami), do 11 cyfr, obok liczb na potworze ikona
krytyka / przebicia / obu, na graczu znaki unik / blok / pudło, cios bez obrażeń = „pudło” zamiast niczego. Tekstury i
efekty – nowy folder `d:/ymir work/effect/affect/damagevalue2/` (paczka klienta `dmgprint`, 38 plików = folder
`damagevalue` klienta GF 26.1.11).

## Serwer (3 edycje, `edits.json`)

| Plik | Zmiana |
|---|---|
| `char.h` `(flags)` | `DAMAGE_ATTACKER_PC = 1<<6`, `DAMAGE_MISS = 1<<7` w `enum DamageFlag` (`#error`, gdyby ktoś włączył wilkołaka z `DAMAGE_BLEEDING` = 1<<6) |
| `char_battle.cpp` `(attacker)` | `SendDamagePacket`: cios gracza (także bota) → `flag |= DAMAGE_ATTACKER_PC` |
| `char_battle.cpp` `(miss)` | główne miejsce wysyłki w `Damage()`: `dam <= 0` → sam `DAMAGE_MISS` (reguła paczki) |

**Różnica względem paczki:** paczka dokładała `DWORD dwAttackerVID` do `TPacketGCDamageInfo` (inny rozmiar pakietu =
stary exe rozjeżdża strumień). Tu pakiet zostaje bez zmian (nagłówek 135, ten sam rozmiar) – klient potrzebuje tylko
„czy bił gracz”, więc to bit we fladze. Stary exe ignoruje oba bity (pudło = 0 obrażeń, jak dotąd nic). Bez nowych
nagłówków pakietów, db bez zmian, boty bez zmian (nie czytają tego pakietu).

Linux/VPS: `python3 apply_dmgprint.py <game/src>` (po `superstone`, na końcu listy `yohara-deploy.sh`);
Windows: `Apply-DmgPrintPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Sprawdzone: kompilacja
`char_battle.cpp` na drzewie testowym z łatką (29.10.2026), druga aplikacja = 0 edycji.

## Klient

- exe (`client-patches/exe`, `ENABLE_DAMAGE_PRINT_IMPROVE` w `Locale_inc.h`): `EffectLib/EffectManager.*` (osobny zbiór
  efektów obrażeń, update+render bez Z), `ParticleProperty.*` / `ParticleSystemData.cpp` / `ParticleSystemInstance.h`
  (token `EnableFrustum` w .mse – **brak tokenu = stary test frustum**, paczka wyłączała go wszystkim efektom),
  `InstanceBase.h` / `InstanceBaseEffect.cpp` (nowe `ProcessDamage`; opcja „Pokazuj obrażenia” brak/cel/wszystkie
  i limit kolejki zostają), `PythonApplication.*` (`RenderDamageEffect` na końcu `RenderGame` – root bez zmian),
  `PythonPlayerSettingsModule.cpp` (efekty z `damagevalue2/`), `PythonCharacterManagerModule.cpp`,
  `PythonApplicationModule.cpp` (`app.ENABLE_DAMAGE_PRINT_IMPROVE`).
- paczka: `client-2.0.30/tools/dmgprint` (`build_dmgprint_pack.py`, `verify_dmgprint.py`).
