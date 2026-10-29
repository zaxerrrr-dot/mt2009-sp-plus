# ringfx – efekty zakładania pierścieni, medalu, lizaków i amuletów

Znacznik: `MT2009_PLUS_RING_EFFECTS_V1`. Właściciel (30.10.2026): poradnik „efekty na pierścienie/amulety/lizaki”
(`SE_EQUIP_*`, `CItemVnumHelper::Is*`, `EffectPacket` po `IsLovePendant`, `EFFECT_*_EQUIP` w exe, paczka
„offical_ring”).

## Numery (protokół serwer ↔ exe)

Poradnik dopisuje `SE_EQUIP_*` za `SE_EQUIP_LOVE_PENDANT` – u nas to przesunęłoby efekty Zodiaku i błyskawicy rękawic,
więc nowe idą **na koniec** listy, za `SE_ELEC_ATTACK_HIT` (54, `server-patches/elecglove`), w tej samej kolejności po
obu stronach (`static_assert` w `char_item.cpp` i w exe):

| SE | nr | Przedmiot | Efekt (exe) |
|---|---|---|---|
| `SE_EQUIP_WILL_RING` | 55 | 71148 Pierścień Siły Woli | `buff_item5.mse` (GF, paczka etc) |
| `SE_EQUIP_DEADLY_RING` | 56 | 71149 Pierścień Śmierc. Mocy | `deadly_ring.mse` (paczka `ringfx`) |
| `SE_EQUIP_HERO_MEDAL` | 57 | 71158 Medal Bohatera | `buff_symbol1.mse` (GF, etc) |
| `SE_EQUIP_BLUE_CANDY` | 58 | 71180 (niebieski lizak) | `buff_item16.mse` (GF, etc) |
| `SE_EQUIP_GREEN_CANDY` | 59 | 71181 (zielony lizak) | `green_candy.mse` (paczka `ringfx`) |
| `SE_EQUIP_YELLOW_CANDY` | 60 | 71188 Lizak Magii | `buff_item8.mse` (GF, etc) |
| `SE_EQUIP_CHOCOLATE_PENDANT` | 61 | 71199 Czekoladowy Amulet | `buff_item10.mse` (GF, etc) |
| `SE_EQUIP_EVIL_PENDANT` | 62 | 71202 Amulet Nazara | `buff_item13.mse` (GF, etc) |
| `SE_EQUIP_GUARD_PENDANT` | 63 | 72054 (amulet strażnika) | `buff_item14.mse` (GF, etc) |

71180, 71181 i 72054 nie ma w naszym `world.item_proto` – efekt zadziała, gdy zostaną dodane. Reszta to `ITEM_UNIQUE`
(typ 16, `WEARABLE_UNIQUE`) – sloty unikatowe; `EquipItem` gra efekt w każdym slocie, do którego przedmiot pasuje.
Grupy bonusów (`special_item_group.unique_attr.txt`) nie mają pliku efektu, więc gałąź SIG niczego nie traci.

## Serwer

| Plik | Zmiana |
|---|---|
| `common/length.h` | `(SE)`: 9 × `SE_EQUIP_*` (55–63) za `SE_ELEC_ATTACK_HIT` |
| `common/VnumHelper.h` | `(vnum)`: `IsWillRing` … `IsGuardPendant` |
| `char_item.cpp` | `(equip)`: `EffectPacket(SE_EQUIP_*)` po gałęzi `IsLovePendant` (+ `static_assert` 55/63) |

3 edycje (`edits.json`), **ostatnia** w kolejności `yohara-deploy.sh` (za `konie`). Linux/VPS:
`python3 apply_ringfx.py <game/src>`; Windows: `Apply-RingFxPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu).
db bez zmian (ten sam `length.h`, enum tylko dłuższy).

## Klient

- exe (`client-patches/exe`, `ENABLE_MT2009_RING_EFFECTS` w `Locale_inc.h`): `SE_EQUIP_*` w `Server/common/length.h`,
  `CInstanceBase::EFFECT_*_EQUIP` (na końcu, przed `EFFECT_NUM`), rejestracja w `PythonPlayerSettingsModule.cpp` (nasz exe
  rejestruje efekty w C++, nie w root `playersettingmodule.py` – root bez zmian), `case SE_EQUIP_*` w
  `PythonNetworkStreamPhaseGameItem.cpp`, `chrmgr.EFFECT_*_EQUIP`.
- Pliki: 7 efektów to oryginały klienta GF 26.1.11, już w paczce `etc` instalacji (te same bajty; paczka „offical_ring”
  ma je pod innymi nazwami – `will_ring.mse` = `buff_item5.mse`, `blue_candy.dds` = `candy3.dds` itd.). Nowa paczka
  `ringfx` (`client-2.0.30/tools/ringfx`) ma tylko dwa efekty, których GF nie ma: `deadly_ring.mse` + `magic_ring2.dds`,
  `green_candy.mse` + `green_candy.dds` (bajty z „offical_ring”, klucze EterPack standardowe).
- Stary exe dostaje nieznany efekt 55–63: tylko wpis w syserr („is not a special effect number”), gra działa.
