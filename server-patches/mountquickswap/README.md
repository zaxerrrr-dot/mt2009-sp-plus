# Wierzchowiec z pieczęci działa jak koń: szybkie zejście, umiejętność, wejście

Poprawka silnika, znaczniki `MT2009_PLUS_MOUNT_QUICKSWAP_V1` i `MT2009_PLUS_MOUNT_CRASH_FIX_V1`
(każda zmiana ma własny dopisek w nawiasie). Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu); `Apply-MountQuickswapPatch.ps1` i
linuksowy bliźniak `apply_mountquickswap.py` czytają ten sam `edits.json`.

Zgłoszenie właściciela (3 października 2026): „poprawić system mount aby działał jak konie czyli
aby można było szybko zejść, odpalić aurę i wejść – nie czekać aż serwer złapie że się nie
ruszamy”.

## Co było nie tak

Koń: Ctrl+G zsiada (`StopRiding`), koń staje obok, następne Ctrl+G od razu na niego wsiada
(`StartRiding`) – bez sprawdzania walki, ataku ani ruchu (tylko 1 s między dwoma wsiadaniami).

Wierzchowiec z pieczęci: Ctrl+G (`/ride`, `do_ride`) zsiadał przez `do_unmount`, czyli **zdejmował
pieczęć do ekwipunku**. Następne Ctrl+G zakładało ją z powrotem (`UseItem` → `EquipItem`), a
`EquipItem` odmawia założenia czegokolwiek przez 1,5 s po ataku lub umiejętności – komunikat „You
have to stand still to equip the item.” („musisz stać w miejscu”). Zejście, aura, wejście –
i wierzchowiec nie wracał, dopóki nie minęło 1,5 s od aury.

Exe nie ma tu nic do rzeczy: klient przełącza postać na wierzchowca od razu po pakiecie serwera
(`CNetworkActorManager::AppendActor` tworzy postać na nowo, bez odkładania do końca animacji).
Czekanie było po stronie serwera.

## Co robi poprawka

| Dopisek | Plik | Co |
|---|---|---|
| `(dismount)` | `cmd_general.cpp` (`do_ride`) | Ctrl+G na wierzchowcu z założonej pieczęci zsiada jak z konia: pieczęć **zostaje założona**, wierzchowiec staje obok (`CMountSystem::Unmount` – tak samo zsiadają boty). Jak przy koniu (`StopRiding`): nie przy otwartym handlu, sklepie, magazynie (`CANNOT_CONTINUE_WHEN_BUSY`); dodatek do sprawdzania ruchu dla zsiadającego w biegu (`OnStopRiding`). Wierzchowiec z questa (`pc.set_mount`) i stare przedmioty do jazdy zsiadają po staremu. |
| `(mount)` | `cmd_general.cpp` (`do_ride`) | Wsiadanie na założoną pieczęć: jak koń – 1 s między dwoma wsiadaniami (ten sam zegar `ePulse::HorseUse` co koń). Gdy wierzchowca nie ma obok (np. odesłany), Ctrl+G najpierw go przywołuje (`MountSummon`, z jego zakazami: OX, arena), zamiast nic nie robić. |
| `(same keypress)` | `cmd_general.cpp` (`do_ride`) | Ctrl+G z pieczęcią w plecaku: `EquipItem` już wsadza gracza na wierzchowca (`MT2009_PLUS_MOUNT_ON_EQUIP_V1`), drugie `Mount` w tej samej komendzie zsiadało i wsiadało jeszcze raz (dwa razy wysłana postać do wszystkich wokół). |
| `(stand still)` | `char_item.cpp` (`EquipItem`) | Pieczęć wierzchowca (kostium, podtyp mount) zakłada się od razu, także zaraz po ataku czy umiejętności – jak przywołanie konia. 1,5 s zostaje dla broni, zbroi i reszty (przeciw podmianie ekwipunku w walce); licznik zakładania (5 na 500 ms) i `FAST_ITEM_SWAP` działają dalej. |
| `MT2009_PLUS_MOUNT_CRASH_FIX_V1 (unsummon)`, `(summon)`, `(update)` | `MountSystem.cpp` | Autor: Digi Rasta (pakiet v0.23.0, „padanie rdzenia”). Postać wierzchowca zniszczona z zewnątrz zostawała w `CMountActor::m_pkChar`: odwołanie niszczyło ją drugi raz (`Unsummon`), przywołanie wołało `Show()` na zwolnionej pamięci (`Summon`), a `CMountSystem::Update` (kilka razy na sekundę) czytał jej VID ze zwolnionej pamięci. Postać jest „nasza” tylko wtedy, gdy `CHARACTER_MANAGER` wciąż zna ją pod naszym VID. Żadnej z trzech poprawek nie było w silniku MT2009 PLUS. |

## Jak się teraz gra

- **Ctrl+G** – wsiada / zsiada, jak koń. Po zejściu pieczęć zostaje w slocie wierzchowca, a
  wierzchowiec idzie za postacią. Zejście → aura (albo inna umiejętność) → Ctrl+G = od razu w
  siodle. Między dwoma wsiadaniami 1 s, jak przy koniu.
- **Ctrl+J** (`/unmount`) albo klik na pieczęć w ekwipunku – zdejmuje pieczęć do plecaka
  (wierzchowiec znika), jak dotąd.
- Pieczęć w plecaku: klik albo Ctrl+G zakłada ją i od razu wsiada – teraz także zaraz po walce.

Bez zmian w exe, w Pythonie klienta i w protokole.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

- `Apply-MountQuickswapPatch.ps1 -SourceDir <game/src>` – Windows (Apply-MT2009PlusEngine.ps1);
- `apply_mountquickswap.py <game/src>` – to samo na Linuksie/VPS.
